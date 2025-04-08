import datetime
import ipaddress
import csv
import os
import gzip

AS_NUMBERS = ["AS4134", "AS4808", "AS4837", "AS9808", "AS4812"]
OUTPUT_FILE = "china_ips.txt"
IPINFO_DB_PATH = "ipinfo-country-asn.csv.gz" # 修改成你下载的数据库文件名

def get_as_ips_from_db(as_number, ip_country_asn_data):
    """
    从 IPinfo 数据库中查找指定 AS 编号的所有 IP 地址。
    """
    as_ips = []
    for record in ip_country_asn_data:
        if record["asn"] == as_number:
            as_ips.append(record["ip_prefix"])
    return as_ips


def is_china_ip(ip_address, ip_country_asn_data):
    """
    使用 IPinfo 数据库判断 IP 地址是否属于中国大陆。
    """
    try:
        ip_addr = ipaddress.ip_address(ip_address)
    except ValueError:
        print(f"Invalid IP address: {ip_address}")
        return False

    for record in ip_country_asn_data:
        try:
            network = ipaddress.ip_network(record["ip_prefix"])
            if ip_addr in network:
                return record["country_code"] == "CN"
        except ValueError:
            print(f"Invalid IP Prefix: {record['ip_prefix']}")
            continue  # skip to the next record
        except Exception as e:
            print(f"Unexpected Error checking IP {ip_address} in Prefix {record['ip_prefix']}: {e}")
            return False

    print(f"No matching IP Prefix found in database for IP {ip_address}")
    return False


def load_ip_country_asn_data(db_path):
     """
     加载 IPinfo 的国家和 ASN 数据。
     """
     ip_country_asn_data = []

     try:
         with gzip.open(db_path, 'rt', encoding='utf-8') as csvfile:  # 使用 gzip 打开 .gz 文件
             reader = csv.DictReader(csvfile, fieldnames=["ip_prefix", "country_code", "asn", "organization"])

             next(reader) # 跳过标题行

             for row in reader:
                 ip_country_asn_data.append({
                     "ip_prefix": row["ip_prefix"],
                     "country_code": row["country_code"],
                     "asn": row["asn"],
                     "organization": row["organization"]
                 })
     except FileNotFoundError:
         print(f"Error: Database file '{db_path}' not found.")
         return None
     except Exception as e:
         print(f"Error loading data from '{db_path}': {e}")
         return None

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

    all_china_ips = []
    for as_number in AS_NUMBERS:
        print(f"Fetching IPs for {as_number}...")
        ips = get_as_ips_from_db(as_number, ip_country_asn_data)
        print(f"Found {len(ips)} IP Prefixes for {as_number}.")

        #  展开 CIDR 前缀并检查 IP 地址
        china_ips = []
        for prefix in ips:
             try:
                network = ipaddress.ip_network(prefix, strict=False) # strict=False 处理一些边界情况
                for ip_int in range(int(network.network_address), int(network.broadcast_address) + 1): # 遍历网段中的所有IP
                    ip_address = str(ipaddress.ip_address(ip_int))
                    if is_china_ip(ip_address, ip_country_asn_data):
                        china_ips.append(ip_address)
             except ValueError as e:
                 print(f"Error processing IP Prefix {prefix}: {e}")
                 continue

        print(f"Found {len(china_ips)} China IPs for {as_number}.")
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
