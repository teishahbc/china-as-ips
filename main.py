import datetime
import ipaddress
import csv
import gzip
import sys # Import sys for stderr

# Define the target ASNs for China mainland providers
# AS4134: China Telecom
# AS4808: China Unicom (formerly CNCGROUP) - Note: CNCGROUP merged into Unicom
# AS4837: China Unicom Backbone (AS4837 is often associated with premium CN routes)
# AS9808: China Mobile
# AS4812: China Telecom Backbone (often associated with CN2 routes)
# Consider adding other relevant ASNs if needed (e.g., regional providers, education networks like AS4538 CERNET)
AS_NUMBERS = ["AS4134", "AS4808", "AS4837", "AS9808", "AS4812"]

OUTPUT_FILE = "china_ips.txt"
COUNTRY_ASN_FILE = "country_asn.csv.gz"
COUNTRY_CODE = "CN" # Target country code

def ip_range_to_cidr(start_ip_str, end_ip_str):
    """
    Converts an IP address range to a list of CIDR blocks.
    Includes robust error handling.
    """
    try:
        start_ip = ipaddress.ip_address(start_ip_str)
        end_ip = ipaddress.ip_address(end_ip_str)
        # Ensure IPs are IPv4 as this database primarily deals with IPv4 ranges for ASN mapping
        if start_ip.version != 4 or end_ip.version != 4:
             # print(f"Skipping non-IPv4 range: {start_ip_str} - {end_ip_str}", file=sys.stderr)
             return []

        start_int = int(start_ip)
        end_int = int(end_ip)

        if start_int > end_int:
            print(f"Warning: Start IP > End IP in range: {start_ip_str} - {end_ip_str}", file=sys.stderr)
            return []

        # Use summarize_address_range for efficient CIDR generation
        return [str(network) for network in ipaddress.summarize_address_range(start_ip, end_ip)]

    except ValueError as e:
        print(f"Error converting range to CIDR: {start_ip_str}-{end_ip_str}. Error: {e}", file=sys.stderr)
        return []
    except Exception as e:
        print(f"Unexpected error in ip_range_to_cidr for {start_ip_str}-{end_ip_str}: {e}", file=sys.stderr)
        return []


def get_ips_from_ipinfo_csv(csv_file_path, target_country, target_asns):
    """
    Reads the IPinfo country_asn gzipped CSV file, filters by country and ASN,
    and returns a list of IP addresses/ranges in CIDR format.
    """
    cidrs = set() # Use a set for efficient deduplication during processing
    processed_rows = 0
    matched_rows = 0
    print(f"Processing {csv_file_path} for country {target_country} and ASNs: {', '.join(target_asns)}")

    try:
        with gzip.open(csv_file_path, 'rt', encoding='utf-8', errors='ignore') as f:
            reader = csv.reader(f)
            header = next(reader, None)  # Read header row
            if not header or len(header) < 4:
                 raise ValueError("CSV file has unexpected header format or too few columns.")
            print(f"CSV Header: {header}") # Print header for verification

            # Find column indices dynamically (more robust)
            try:
                start_ip_idx = header.index('start_ip')
                end_ip_idx = header.index('end_ip')
                country_idx = header.index('country')
                asn_idx = header.index('asn_number') # Assuming column name is 'asn_number'
            except ValueError as e:
                raise ValueError(f"Missing expected column in CSV header: {e}")

            for i, row in enumerate(reader):
                processed_rows += 1
                try:
                    if len(row) < max(start_ip_idx, end_ip_idx, country_idx, asn_idx) + 1:
                        # print(f"Skipping row {i+2}: Insufficient columns ({len(row)}). Row: {row}", file=sys.stderr)
                        continue # Skip rows that don't have enough columns

                    country = row[country_idx]
                    asn = row[asn_idx] # ASN is usually like "AS12345"

                    # Filter by country and ASN
                    if country == target_country and asn in target_asns:
                        matched_rows += 1
                        start_ip = row[start_ip_idx]
                        end_ip = row[end_ip_idx]

                        # Convert range to CIDR
                        range_cidrs = ip_range_to_cidr(start_ip, end_ip)
                        cidrs.update(range_cidrs) # Add CIDRs to the set

                except IndexError:
                     # This shouldn't happen with the length check, but as a safeguard
                     print(f"Skipping row {i+2}: Index error. Row: {row}", file=sys.stderr)
                     continue
                except Exception as e:
                    print(f"Error processing row {i+2}: {row}. Error: {e}", file=sys.stderr)
                    continue # Ignore problematic rows

                # Optional: Print progress periodically
                if (i + 1) % 100000 == 0:
                    print(f"Processed {processed_rows} rows, found {len(cidrs)} unique CIDRs so far...")

    except FileNotFoundError:
        print(f"Error: File not found: {csv_file_path}", file=sys.stderr)
        return []
    except gzip.BadGzipFile:
         print(f"Error: Bad Gzip file: {csv_file_path}. Download might be corrupt.", file=sys.stderr)
         return []
    except Exception as e:
        print(f"Error reading or processing CSV file {csv_file_path}: {e}", file=sys.stderr)
        return []

    print(f"Finished processing. Total rows processed: {processed_rows}. Rows matched criteria: {matched_rows}.")
    # Sort the final list of unique CIDRs by network address
    # Convert back to list and sort using ipaddress objects for correct sorting
    sorted_cidrs = sorted(list(cidrs), key=ipaddress.ip_network)
    return [str(cidr) for cidr in sorted_cidrs] # Return as strings


def main():
    start_time = datetime.datetime.now()
    print(f"Script started at {start_time}")

    # Get filtered IPs from the local IPinfo CSV file
    print(f"Fetching IPs from {COUNTRY_ASN_FILE}...")
    china_ips = get_ips_from_ipinfo_csv(COUNTRY_ASN_FILE, COUNTRY_CODE, AS_NUMBERS)

    if not china_ips:
        print("No IPs found matching the criteria or error occurred during processing. Not updating the output file.")
        # Exit with an error code if no IPs were found, maybe indicating a problem upstream
        sys.exit(1) # Exit with error

    print(f"Found {len(china_ips)} unique CIDRs for {COUNTRY_CODE} and specified ASNs.")

    # --- Read existing IPs to see if update is needed ---
    existing_ips = set()
    try:
        with open(OUTPUT_FILE, "r") as f:
            existing_ips.update(line.strip() for line in f if line.strip())
    except FileNotFoundError:
        print(f"{OUTPUT_FILE} not found. Creating a new one.")
    except Exception as e:
        print(f"Error reading existing {OUTPUT_FILE}: {e}. Will overwrite.", file=sys.stderr)


    # --- Compare and Write if Changed ---
    new_ips_set = set(china_ips)
    if new_ips_set == existing_ips:
        print(f"No changes detected in the IP list. {OUTPUT_FILE} remains unchanged.")
    else:
        print(f"IP list has changed. Writing {len(china_ips)} unique CIDRs to {OUTPUT_FILE}...")
        try:
            with open(OUTPUT_FILE, "w") as f:
                for ip in china_ips: # Use the sorted list
                    f.write(ip + "\n")
            print(f"Successfully wrote updates to {OUTPUT_FILE}")
        except Exception as e:
             print(f"Error writing to {OUTPUT_FILE}: {e}", file=sys.stderr)
             sys.exit(1) # Exit with error if writing fails


    end_time = datetime.datetime.now()
    print(f"Script finished at {end_time}")
    print(f"Total execution time: {end_time - start_time}")


if __name__ == "__main__":
    main()
