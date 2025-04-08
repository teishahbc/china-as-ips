import datetime
import ipaddress
import csv
import os
import gzip

AS_NUMBERS = ["AS4134", "AS4808", "AS4837", "AS9808", "AS4812"]
OUTPUT_FILE = "china_ips.txt"
IPINFO_DB_PATH = "country_asn.csv.gz"

def load_ip_data(db_path):
    """加载 IPinfo 数据库， 过滤 IPv6 和非法地址."""
    valid_ip_data = []
    discarded_ipv6 = 0
    discarded_invalid_ip = 0

    try:
        with gzip.open(db_path, 'rt', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile, fieldnames=["ip_prefix", "country", "country_name", "continent", "continent_code", "asn", "as_name", "as_domain"])
            next(reader)  # Skip header row
            for row in reader:
                # 忽略IPv6地址
                if ":" in row["ip_prefix"]:
                    discarded_ipv6 += 1
                    continue

                try:
                    ipaddress.ip_network(row["ip_prefix"])
                    valid_ip_data.append(row)  # 添加原始数据
                except ValueError as e:
                    discarded_invalid_ip += 1
                    continue


    except FileNotFoundError:
        print(f"Error: Database file '{db_path}' not found.")
        return None,0,0 #返回0,0
    except Exception as e:
        print(f"Error loading data from '{db_path}': {e}")
        return None,0,0

    print(f"load_ip_data: Discarded IPV6 Record {discarded_ipv6}")
    print(f"load_ip_data: Discarded Invalid IP Record {discarded_invalid_ip}")
    print(f"load_ip_data: Loaded {len(valid_ip_data)} records.")
    return valid_ip_data, discarded_ipv6, discarded_invalid_ip

def get_china_ips_for_as(as_number, ip_data):
    """从有效的IP 数据中筛选指定AS号码的中国IP地址"""
    china_ips = []
    for record in ip_data:
        if record["country"] == "CN" and record["asn"] == as_number:
            china_ips.append(record["ip_prefix"]) #只需要网络地址
    return china_ips


def main():
    start_time = datetime.datetime.now()
    print(f"Script started at {start_time}")

    # Load IP data and process in memory
    print("Loading IP database...")
    ip_data, discarded_ipv6, discarded_invalid_ip = load_ip_data(IPINFO_DB_PATH)

    if ip_data is None:
        print("Failed to load IP database. Exiting.")
        return

    print(f"Loaded database from {IPINFO_DB_PATH} ,found  IPV6 {discarded_ipv6}, found  Invalid IP {discarded_invalid_ip} and Effective Record Count {len(ip_data)}")


    all_china_ips = []
    for as_number in AS_NUMBERS:
        print(f"Fetching IPs for AS {as_number}...")
        china_ips = get_china_ips_for_as(as_number, ip_data)
        print(f"Found {len(china_ips)} China IPs for AS {as_number}.")
        all_china_ips.extend(china_ips)

    # Remove duplicates and sort
    unique_china_ips = sorted(list(set(all_china_ips)))

    # Write to file
    with open(OUTPUT_FILE, "w") as f:
        f.write("\n".join(unique_china_ips))

    print(f"Wrote {len(unique_china_ips)} unique China IPs to {OUTPUT_FILE}")
    end_time = datetime.datetime.now()
    print(f"Script finished at {end_time}, total runtime {end_time - start_time}")


if __name__ == "__main__":
    main()
