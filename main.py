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
    china_ipv4_ranges = []

    try:
        with gzip.open(db_path, 'rt', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile, fieldnames=["start_ip", "end_ip", "country", "country_name", "continent", "continent_name", "asn", "as_name", "as_domain"])

            next(reader)  # 跳过标题行

            for row in reader:
                # 忽略IPv6地址
                if ":" in row["start_ip"] or ":" in row["end_ip"]:
                    continue
                #  必须是中国的IP地址
                if row["country"] != "CN":
                    continue

                try:
                    start_ip = row["start_ip"]
                    end_ip = row["end_ip"]
                    asn = row["asn"]

                    start_ip_num = int(ipaddress.ip_address(start_ip))
                    end_ip_num = int(ipaddress.ip_address(end_ip))
                    china_ipv4_ranges.append({
                        "start_ip": start_ip,
                        "end_ip": end_ip,
                        "asn": asn,
                    })
                except ValueError as e:
                    print(f"Invalid IP Address: {row['start_ip']} {row['end_ip']}")
                    continue



    except FileNotFoundError:
        print(f"Error: Database file '{db_path}' not found.")
        return None
    except Exception as e:
        print(f"Error loading data from '{db_path}': {e}")
        return None
    print(f"Loaded {len(china_ipv4_ranges)} china_ipv4_ranges data")
    return china_ipv4_ranges


def get_china_ips_for_as(as_number, china_ipv4_ranges):
    """
    从中国的 IPv4 地址范围中，筛选出属于指定 AS 编号的 IP 地址范围。
    """
    as_ips = []
    for record in china_ipv4_ranges:
        if record["asn"] == as_number:
            as_ips.append((record["start_ip"], record["end_ip"]))  # 存储 (start_ip, end_ip) 元组
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
        ips = get_china_ips_for_as(as_number, china_ipv4_ranges)
        print(f"Found {len(ips)} IP Ranges for AS {as_number}.")

        china_ips = []
        for start_ip, end_ip in ips:
           try:
             network = ipaddress.ip_network(start_ip + '/' + '24', strict=False)  # 创建网络对象
             china_ips.append(str(network.network_address))  # 获取网络地址并添加到列表
           except ValueError as e:
               print(f"error ipaddress.ip_network: {e}")
               continue

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
