import datetime
import ipaddress
import csv
import os
import gzip

AS_NUMBERS = ["AS4134", "AS4808", "AS4837", "AS9808", "AS4812"]
OUTPUT_FILE = "china_ips.txt"
IPINFO_DB_PATH = "country_asn.csv.gz"  # 恢复为 country_asn.csv.gz

def get_as_ips_from_db(as_number, ip_country_asn_data):
    """
    从 IPinfo 数据库中查找指定 AS 编号的所有 IP 地址。
    """
    as_ips = []
    for record in ip_country_asn_data:
        if record["asn"] == as_number:
            as_ips.append(record["start_ip"] + '-' + record["end_ip"]) #  返回 "start_ip-end_ip" 格式
    return as_ips


def is_china_ip(ip_address, ip_country_asn_data):
    """
    使用 IPinfo 数据库判断 IP 地址是否属于中国大陆。
    """
    try:
        ip_num = int(ipaddress.ip_address(ip_address)) #将 IP 地址转换为整数
    except ValueError:
        print(f"Invalid IP address: {ip_address}")
        return False

    for record in ip_country_asn_data:
      try:
        start_ip_num = int(ipaddress.ip_address(record["start_ip"]))
        end_ip_num = int(ipaddress.ip_address(record["end_ip"]))
        if start_ip_num <= ip_num <= end_ip_num:
           return record["country"] == "CN" #CN 是中国的 ISO 国家代码

      except ValueError:
          print(f"Invalid IP Range: {record['start_ip']} - {record['end_ip']}")
          continue # skip to the next record
      except Exception as e:
          print(f"Unexpected Error checking IP {ip_address} in Range {record['start_ip']} - {record['end_ip']}: {e}")
          return False
    print(f"No matching IP Range found in database for IP {ip_address}")
    return False



def load_ip_country_asn_data(db_path):
    """
    加载 IPinfo 的国家和 ASN 数据。
    """
    ip_country_asn_data = []

    try:
        with gzip.open(db_path, 'rt', encoding='utf-8') as csvfile:  # 使用 gzip 打开 .gz 文件
            reader = csv.DictReader(csvfile, fieldnames=["start_ip", "end_ip", "country", "country_name", "continent", "continent_name", "asn", "as_name", "as_domain"])

            next(reader)  # 跳过标题行

            for row in reader:
                ip_country_asn_data.append({
                    "start_ip": row["start_ip"],
                    "end_ip": row["end_ip"],
                    "country": row["country"],
                    "asn": row["asn"],
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
        print(f"Found {len(ips)} IP Ranges for {as_number}.")

        # 检查IP 范围
        china_ips = []
        for ip_range_str in ips:
            try:
                start_ip, end_ip = ip_range_str.split('-')  # 分割 "start_ip-end_ip" 字符串
                start_ip = start_ip.strip()
                end_ip = end_ip.strip()

                start_ip_num = int(ipaddress.ip_address(start_ip))
                end_ip_num = int(ipaddress.ip_address(end_ip))

                #展开 IP 范围，并检查每个 IP 地址是否属于中国
                for ip_int in range(start_ip_num, end_ip_num + 1):
                  ip_address = str(ipaddress.ip_address(ip_int))
                  if is_china_ip(ip_address, ip_country_asn_data):
                     china_ips.append(ip_address)


            except ValueError as e:
                print(f"Error processing IP Range {ip_range_str}: {e}")
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
