import requests
import datetime
import time
import ipaddress
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
    将 IP 地址范围转换为 CIDR 格式（优化版本）。
    """
    try:
        start = int(ipaddress.ip_address(start_ip))
        end = int(ipaddress.ip_address(end_ip))
    except ValueError as e:
        print(f"Invalid IP address format: {e}")
        return []
    if start > end:
        print(f"start_ip > end_ip")
        return []

    cidrs = []
    try:
        network = ipaddress.summarize_address_range(ipaddress.ip_address(start_ip),ipaddress.ip_address(end_ip))
        for n in network:
            cidrs.append(str(n))
    except ValueError as e:
        print(f"Error creating network: {e}")

    return cidrs

def is_valid_asn(as_number:str, asns:list[str]) ->bool:
    if not as_number:
        return False
    for asn in asns:
        if asn in as_number:
            return True
    return False

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
                try:
                    if len(row) < 7:
                        continue
                    start_ip, end_ip, country,_,_,_,asn = row[0], row[1], row[2],row[3],row[4],row[5],row[6]

                    if country == "CN" and is_valid_asn(asn,AS_NUMBERS):
                        #Convert to CIDR
                        cidrs = ip_range_to_cidr(start_ip, end_ip)
                        china_ips.extend(cidrs)
                except Exception as e:
                    print(f"Error processing row: {row}. Error: {e}") # 打印出错的行
                    continue  # 忽略当前行，继续处理下一行
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


    # Remove duplicates and sort
    unique_china_ips = sorted(list(set(all_china_ips)))

    # Write to file
    if unique_china_ips: #只有当列表不为空时，才写入文件，防止文件内容没有改变
        with open(OUTPUT_FILE, "w") as f:
            f.write("\n".join(unique_china_ips))

    print(f"Wrote {len(unique_china_ips)} unique China IPs to {OUTPUT_FILE}")
    print(f"Script finished at {datetime.datetime.now()}")


if __name__ == "__main__":
    main()
