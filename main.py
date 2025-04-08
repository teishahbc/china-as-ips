# main.py
import datetime
import ipaddress
import csv
import gzip
import sys # Import sys for stderr and exit

# --- Configuration ---
# Define the target ASNs for China mainland providers
# AS4134: China Telecom
# AS4808: China Unicom (formerly CNCGROUP)
# AS4837: China Unicom Backbone
# AS9808: China Mobile
# AS4812: China Telecom Backbone (CN2)
# Add or remove ASNs as needed
AS_NUMBERS = ["AS4134", "AS4808", "AS4837", "AS9808", "AS4812"]

OUTPUT_FILE = "china_ips.txt"
COUNTRY_ASN_FILE = "country_asn.csv.gz" # Input gzipped CSV file from IPinfo
COUNTRY_CODE = "CN" # Target country code
# --- End Configuration ---

def ip_range_to_cidr(start_ip_str, end_ip_str):
    """
    Converts an IP address range to a list of CIDR blocks.
    Includes robust error handling. Handles only IPv4.
    """
    try:
        start_ip = ipaddress.ip_address(start_ip_str)
        end_ip = ipaddress.ip_address(end_ip_str)
        # Ensure IPs are IPv4, as this database primarily deals with IPv4 ranges
        if start_ip.version != 4 or end_ip.version != 4:
             # Silently skip non-IPv4 ranges
             return []

        start_int = int(start_ip)
        end_int = int(end_ip)

        if start_int > end_int:
            # Log warning but don't stop execution for this specific range
            print(f"Warning: Start IP > End IP in range: {start_ip_str} - {end_ip_str}", file=sys.stderr)
            return []

        # Use summarize_address_range for efficient CIDR generation
        return [str(network) for network in ipaddress.summarize_address_range(start_ip, end_ip)]

    except ValueError as e:
        # Log error for invalid IP format or range issues
        print(f"Error converting range to CIDR: {start_ip_str}-{end_ip_str}. Error: {e}", file=sys.stderr)
        return []
    except Exception as e:
        # Catch unexpected errors during conversion
        print(f"Unexpected error in ip_range_to_cidr for {start_ip_str}-{end_ip_str}: {e}", file=sys.stderr)
        return []


def get_ips_from_ipinfo_csv(csv_file_path, target_country, target_asns):
    """
    Reads the IPinfo country_asn gzipped CSV file, filters by country and ASN,
    and returns a sorted list of unique IP addresses/ranges in CIDR format.
    """
    cidrs = set() # Use a set for efficient deduplication during processing
    processed_rows = 0
    matched_rows = 0
    print(f"Processing {csv_file_path} for country {target_country} and ASNs: {', '.join(target_asns)}")

    try:
        with gzip.open(csv_file_path, 'rt', encoding='utf-8', errors='ignore') as f:
            reader = csv.reader(f)
            header = next(reader, None)  # Read header row
            if not header or len(header) < 3: # Basic header validation (start, end, country, asn needed)
                 raise ValueError("CSV file has unexpected header format or too few columns.")
            print(f"CSV Header: {header}") # Log the header for debugging purposes

            # Find column indices dynamically - more robust to column order changes
            try:
                start_ip_idx = header.index('start_ip')
                end_ip_idx = header.index('end_ip')
                country_idx = header.index('country')
                # *** CORRECTED LINE: Use the actual column name 'asn' ***
                asn_idx = header.index('asn')
            except ValueError as e:
                # If essential columns are missing, raise an error to stop processing
                raise ValueError(f"Missing expected column in CSV header: {e}")

            required_indices = [start_ip_idx, end_ip_idx, country_idx, asn_idx]
            max_required_index = max(required_indices)

            for i, row in enumerate(reader):
                processed_rows += 1
                try:
                    # Ensure row has enough columns before accessing by index
                    # Using '<=' because indices are 0-based
                    if len(row) <= max_required_index:
                        # Optionally log skipped rows:
                        # print(f"Skipping row {i+2}: Insufficient columns ({len(row)}). Expected at least {max_required_index + 1}.", file=sys.stderr)
                        continue

                    country = row[country_idx]
                    asn = row[asn_idx] # ASN is usually like "AS12345"

                    # Apply filters: Check country first (usually faster) then ASN
                    if country == target_country and asn in target_asns:
                        matched_rows += 1
                        start_ip = row[start_ip_idx]
                        end_ip = row[end_ip_idx]

                        # Convert range to CIDR and add to set
                        range_cidrs = ip_range_to_cidr(start_ip, end_ip)
                        cidrs.update(range_cidrs) # update is efficient for adding multiple items

                except IndexError:
                     # Should be caught by length check, but as a fallback
                     print(f"Skipping row {i+2}: Index error accessing required columns. Row: {row}", file=sys.stderr)
                     continue
                except Exception as e:
                    # Catch other errors during row processing
                    print(f"Error processing row {i+2}: {row}. Error: {e}", file=sys.stderr)
                    continue # Continue with the next row

                # Optional: Print progress indicator periodically
                if (processed_rows % 500000) == 0: # Adjust frequency as needed
                    print(f"Processed {processed_rows} rows, found {len(cidrs)} unique CIDRs so far...")

    except FileNotFoundError:
        print(f"Error: Input file not found: {csv_file_path}", file=sys.stderr)
        return [] # Return empty list on critical file error
    except gzip.BadGzipFile:
         print(f"Error: Bad Gzip file: {csv_file_path}. Download might be corrupt.", file=sys.stderr)
         return [] # Return empty list
    except ValueError as e: # Catch header validation errors or other ValueErrors during setup
        print(f"Error reading or processing CSV file {csv_file_path}: {e}", file=sys.stderr)
        return [] # Return empty list
    except Exception as e:
        # Catch any other unexpected errors during file opening/reading
        print(f"Unexpected error reading or processing CSV file {csv_file_path}: {e}", file=sys.stderr)
        return [] # Return empty list

    print(f"Finished processing. Total rows processed: {processed_rows}. Rows matched criteria: {matched_rows}.")
    if not cidrs:
        # It's possible no IPs match, but log a warning just in case
        print("Warning: No CIDRs were generated after processing. Check filters or input data.", file=sys.stderr)
        return []

    # Sort the final list of unique CIDRs by network address
    try:
        # Convert set to list and sort using ipaddress objects for correct network sorting
        sorted_cidrs = sorted(list(cidrs), key=ipaddress.ip_network)
        return [str(cidr) for cidr in sorted_cidrs] # Return list of strings
    except Exception as e:
        # If sorting fails for some reason, log error and return unsorted
        print(f"Error sorting CIDRs: {e}", file=sys.stderr)
        # Decide whether to return unsorted or empty list based on requirements
        return list(cidrs) # Return unsorted list as fallback


def main():
    """
    Main function to orchestrate the IP fetching, comparison, and writing process.
    """
    start_time = datetime.datetime.now()
    print(f"Script started at {start_time.isoformat()}")

    # Step 1: Get filtered IPs from the CSV file
    print(f"Fetching IPs from {COUNTRY_ASN_FILE}...")
    china_ips_list = get_ips_from_ipinfo_csv(COUNTRY_ASN_FILE, COUNTRY_CODE, AS_NUMBERS)

    if not china_ips_list:
        # get_ips_from_ipinfo_csv already printed errors/warnings
        print("No IPs found matching the criteria or a critical error occurred during processing. Aborting update.", file=sys.stderr)
        sys.exit(1) # Exit with error code 1 to signal failure in Actions workflow

    print(f"Successfully retrieved {len(china_ips_list)} unique CIDRs for {COUNTRY_CODE} and specified ASNs.")

    # Step 2: Read existing IPs from the output file to check for changes
    existing_ips = set()
    try:
        # Use utf-8 encoding for reading
        with open(OUTPUT_FILE, "r", encoding='utf-8') as f:
            # Read lines, strip whitespace, and only add non-empty lines to the set
            existing_ips.update(line.strip() for line in f if line.strip())
        print(f"Read {len(existing_ips)} existing CIDRs from {OUTPUT_FILE}.")
    except FileNotFoundError:
        print(f"{OUTPUT_FILE} not found. A new file will be created.")
        # No need to exit, just means we will definitely write a new file
    except Exception as e:
        # Log error reading existing file but proceed to overwrite if necessary
        print(f"Warning: Error reading existing {OUTPUT_FILE}: {e}. Will attempt to overwrite if changes are detected.", file=sys.stderr)

    # Step 3: Compare the newly generated list with the existing list
    new_ips_set = set(china_ips_list)

    if new_ips_set == existing_ips:
        print(f"No changes detected in the IP list. {OUTPUT_FILE} is already up-to-date.")
        # Successful exit, no changes needed
        exit_code = 0
    else:
        added_count = len(new_ips_set - existing_ips)
        removed_count = len(existing_ips - new_ips_set)
        print(f"IP list has changed ({added_count} added, {removed_count} removed).")
        print(f"Writing {len(china_ips_list)} unique CIDRs to {OUTPUT_FILE}...")

        # Step 4: Write the new list to the output file (only if changed)
        try:
            # Use utf-8 encoding for writing
            with open(OUTPUT_FILE, "w", encoding='utf-8') as f:
                # Write the sorted list, each CIDR on a new line, ending with a newline
                f.write("\n".join(china_ips_list) + "\n")
            print(f"Successfully wrote updates to {OUTPUT_FILE}")
            exit_code = 0 # Successful exit after writing changes
        except IOError as e:
             print(f"Error: Failed to write to {OUTPUT_FILE}: {e}", file=sys.stderr)
             exit_code = 1 # Exit with error code 1 if writing fails
        except Exception as e:
             print(f"An unexpected error occurred during file writing: {e}", file=sys.stderr)
             exit_code = 1 # Exit with error code 1

    # Step 5: Log completion time and total duration
    end_time = datetime.datetime.now()
    print(f"Script finished at {end_time.isoformat()}")
    print(f"Total execution time: {end_time - start_time}")

    # Exit with the determined code (0 for success/no change, 1 for error)
    sys.exit(exit_code)

# --- Main execution block ---
if __name__ == "__main__":
    main()
