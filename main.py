import datetime
import ipaddress
import csv
import os
import gzip
import bisect

AS_NUMBERS = ["AS4134", "AS4808", "AS4837", "AS9808", "AS4812"]
OUTPUT_FILE = "china_ips.txt"
IPINFO_DB_PATH = "country_asn.csv.gz"

def get_as_ips_from_db(as_number, ip_country_asn_data):
    """
    从 IPinfo 数据库中查找指定 AS 编号的所有 IP 地址范围。
    """
    as_ips = []
    for record in ip_country_asn_data:
        if record["asn"] == as_number:
            as_ips.append((record["start_ip"], record["end_ip"]))
    return as_ips


def is_china_ip(ip_address, ip_ranges):
    """
    判断 IP 地址是否属于中国大陆，使用预处理后的数据和二分查找。
    """
    try:
        ip_num = int(ipaddress.ip_address(ip_address))  # 将 IP 地址转换为整数
    except ValueError:
        print(f"Invalid IP address: {ip_address}")
        return False

    # 使用二分查找找到包含 ip_num 的 IP 范围
    index = bisect.bisect_left(ip_ranges, (ip_num,))

    if index > 0 and index <= len(ip_ranges):
        start_ip_num, end_ip_num, country = ip_ranges[index-1]
        if start_ip_num <= ip_num <= end_ip_num:
           return country == "CN"

    return False


def load_ip_country_asn_data(db_path):
    """
    加载 IPinfo 的国家和 ASN 数据，并预处理数据。
    """
    ip_country_asn_data = []

    try:
        with gzip.open(db_path, 'rt', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile, fieldnames=["start_ip", "end_ip", "country", "country_name", "continent", "continent_name", "asn", "as_name", "as_domain"])

            next(reader)  # 跳过标题行

            for row in reader:
                try:
                    start_ip = row["start_ip"]
                    end_ip = row["end_ip"]
                    country = row["country"]
                    asn = row["asn"]
                    start_ip_num = int(ipaddress.ip_address(start_ip))
                    end_ip_num = int(ipaddress.ip_address(end_ip))


                    # 添加验证：检查 end_ip_num >= start_ip_num
                    if end_ip_num < start_ip_num:
                        print(f"Warning: Invalid IP range {start_ip} - {end_ip}, skipping.")
                        continue

                    ip_country_asn_data.append((start_ip_num, end_ip_num, country))  # 存储为元组
                except ValueError as e:
                    print(f"Invalid IP address  {start_ip} or  {end_ip}: {e}")
                    continue

    except FileNotFoundError:
        print(f"Error: Database file '{db_path}' not found.")
        return None
    except Exception as e:
        print(f"Error loading data from '{db_path}': {e}")
        return None

    ip_country_asn_data.sort(key=lambda x: x[0])  # 按照 start_ip 排序

    return ip_country_asn_data


def main():
    start_time = datetime.datetime.now()
    print(f"Script started at {start_time}")

    # 加载数据库
    print("Loading IP database...")
    ip_country_asn_data = load_ip_country_asn_data(IPINFO_DB_PATH)
    if ip_country_asn_data is None:
        print("Failed to load IP database. Exiting.")
        return
    print("Loaded IP database...")

    all_china_ips = []
    for as_number in AS_NUMBERS:
        print(f"Fetching IPs for AS {as_number}...")
        ips = get_as_ips_from_db(as_number, ip_country_asn_data)
        print(f"Found {len(ips)} IP Ranges for AS {as_number}.")

        china_ips = []
        for start_ip, end_ip in ips:
          start_ip_num = int(ipaddress.ip_address(start_ip))
          end_ip_num = int(ipaddress.ip_address(end_ip))
          # 添加验证：检查 end_ip_num >= start_ip_num
          if end_ip_num < start_ip_num:
            print(f"Warning: Invalid IP range {start_ip} - {end_ip}, skipping.")
            continue
          network = ipaddress.ip_network(start_ip+'/'+'24', strict=False)

          if is_china_ip(start_ip, ip_country_asn_data) :  #使用范围查找
            china_ips.append(str(network.network_address)) # 添加网络地址

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
