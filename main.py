import requests
import datetime
import time
import ipaddress
import geoip2.database
import os
import csv  # 导入csv 模块
import gzip # 导入 gzip 模块

AS_NUMBERS = ["AS4134", "AS4808", "AS4837", "AS9808", "AS4812"]
OUTPUT_FILE = "china_ips.txt"
COUNTRY_ASN_FILE = "country_asn.csv.gz"  # 修改为 CSV 文件名
MAX_RETRIES = 3
RETRY_DELAY = 5

def ip_range_to_cidr(start_ip, end_ip):
    """
    将 IP 地址范围转换为 CIDR 格式。
    """
    start = int(ipaddress.ip_address(start_ip))
    end = int(ipaddress.ip_address(end_ip))

    cidrs = []
    while start <= end:
        # 计算最大的可以合并的 prefixlen
        prefixlen = 32
        while prefixlen > 0:
            try:
                network = ipaddress.ip_network((start, prefixlen), strict=False)
                if int(network.network_address) != start or int(network.broadcast_address) > end:
                    prefixlen -= 1
                    break
                else:
                    break
            except ValueError:
                prefixlen -= 1
                break
        cidrs.append(str(ipaddress.ip_network((start, prefixlen), strict=False)))
        start += 2 ** (32 - prefixlen)
    return cidrs


def get_china_ips_from_csv(csv_file):
    """
    从 CSV 文件中读取 IP 地址范围，并转换为 CIDR 格式。
    """
    china_ips = []
    try:
        with gzip.open(csv_file, 'rt', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader, None)  # Skip header row
            for row in reader:
                if len(row) < 3:
                    continue
                start_ip, end_ip, country = row[0], row[1], row[2]
                if country == "CN":
                    #Convert to CIDR
                    cidrs = ip_range_to_cidr(start_ip, end_ip)
                    china_ips.extend(cidrs)
    except Exception as e:
        print(f"Error reading CSV file: {e}")
    return china_ips



def main():
    all_china_ips = []

    # 直接从 CSV 文件中获取中国 IP 地址
    print(f"Fetching China IPs from {COUNTRY_ASN_FILE}...")
    china_ips = get_china_ips_from_csv(COUNTRY_ASN_FILE)
    print(f"Found {len(china_ips)} China IPs.")
    all_china_ips.extend(china_ips)


    # Filter IPs by AS numbers (如果需要，可以添加AS 过滤，但这可能和直接使用 CSV 文件冲突)
    # filtered_china_ips = []
    # for ip in all_china_ips:
    #     if is_ip_in_as(ip, AS_NUMBERS):
    #         filtered_china_ips.append(ip)
    # all_china_ips = filtered_china_ips


    # Remove duplicates and sort
    unique_china_ips = sorted(list(set(all_china_ips)))

    # Write to file
    with open(OUTPUT_FILE, "w") as f:
        f.write("\n".join(unique_china_ips))

    print(f"Wrote {len(unique_china_ips)} unique China IPs to {OUTPUT_FILE}")
    print(f"Script finished at {datetime.datetime.now()}")


if __name__ == "__main__":
    main()
