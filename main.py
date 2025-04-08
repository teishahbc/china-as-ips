import datetime
import ipaddress
import csv
import os
import gzip

AS_NUMBERS = ["AS4134", "AS4808", "AS4837", "AS9808", "AS4812"]
OUTPUT_FILE = "china_ips.txt"
IPINFO_DB_PATH = "country_asn.csv.gz"

def load_china_ipv4_ranges(db_path):
    """
    加载 IPinfo 数据库中所有中国的 IPv4 地址范围。
    忽略 IPv6 地址和不合法的IP地址
    """
    ip_country_asn_data = []

    try:
        with gzip.open(db_path, 'rt', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile, fieldnames=["ip_prefix", "country", "country_name", "continent", "continent_code", "asn", "as_name", "as_domain"])

            next(reader)  # 跳过标题行

            for row in reader:
                # 忽略IPv6地址
                if ":" in row["ip_prefix"] or row["country"] != "CN":
                    continue

                try:
                   ipaddress.ip_network(row["ip_prefix"])
                   ip_country_asn_data.append({
                       "ip_prefix": row["ip_prefix"],
                       "country": row["country"],
                       "asn": row["asn"]
                   })
                except ValueError as e:
                    print(f"Invalid IP Address: {row['ip_prefix']} {row['country']} 跳过")
                    continue


    except FileNotFoundError:
        print(f"Error: Database file '{db_path}' not found.")
        return None
    except Exception as e:
        print(f"Error loading data from '{db_path}': {e}")
        return None
    print(f"Loaded {len(ip_country_asn_data)} china_ipv4_ranges data")
    return ip_country_asn_data


def get_as_ips_from_db(as_number, ip_country_asn_data):
    """
    从 IPinfo 数据库中查找指定 AS 编号的所有 IP 地址范围。
    """
    as_ips = []
    for record in ip_country_asn_data:
        if record["asn"] == as_number:
            as_ips.append(record["ip_prefix"]) # 直接返回 ip_prefix
    return as_ips


def main():
    start_time = datetime.datetime.now()
    print(f"Script started at {start_time}")

    # 加载数据库
    print("Loading IP database...")
    china_ipv4_ranges = load_china_ipv4_ranges(IPINFO_DB_PATH)
    if china_ipv4_ranges is None:
        print("Failed to load IP database. Exiting.")
        return

    all_china_ips = []
    for as_number in AS_NUMBERS:
        print(f"Fetching IPs for AS {as_number}...")
        ips = get_as_ips_from_db(as_number, china_ipv4_ranges)
        print(f"Found {len(ips)} IP Prefixes for AS {as_number}.")

        # 直接将ip 组地址添加进去
        china_ips = [ip for ip in ips]

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
