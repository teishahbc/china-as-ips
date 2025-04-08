import datetime
import ipaddress
import csv
import os

AS_NUMBERS = ["AS4134", "AS4808", "AS4837", "AS9808", "AS4812"]
OUTPUT_FILE = "china_ips.txt"
IP2LOCATION_DB_PATH = "IP2LOCATION-LITE-DB1.IPV4.CSV"

def get_as_ips(as_number):
    """
    从 IP2Location 数据库中查找属于指定 AS 的 IP 地址范围。
    注意：此实现需要你手动创建 AS 到 IP 地址范围的映射。
    由于 IP2Location 数据库不直接包含 AS 信息，你需要自己维护一个映射表，
    或者使用其他方法将 IP 地址范围映射到 AS 编号。

    **重要：** 这个函数是一个占位符实现，你需要替换它，或者额外建立IP和AS的对应关系。
    """

    print(f"Fetching IPs for {as_number} using IP2Location - Placeholder implementation, replace with your logic!")
    return [] # 你需要实现从 IP2Location 数据中获取与AS number 对应的IP段

def is_china_ip(ip_address):
    """
    使用 IP2Location LITE 数据库判断 IP 地址是否属于中国大陆。
    """
    try:
        ip_num = int(ipaddress.ip_address(ip_address))  # 将 IP 地址转换为整数
    except ValueError:
        print(f"Invalid IP address: {ip_address}")
        return False

    try:
        if not os.path.exists(IP2LOCATION_DB_PATH):
            print(f"IP2Location database file not found at {IP2LOCATION_DB_PATH}. Using placeholder China IP check.")
            ip = ipaddress.ip_address(ip_address)
            #  提供一个简化的占位符实现
            #  请用更可靠和授权的方式来判断 IP 归属地
            if ip.subnet_of(ipaddress.ip_network('101.0.0.0/8')):
                return True
            elif ip.subnet_of(ipaddress.ip_network('58.0.0.0/8')):
                return True
            else:
                return False


        with open(IP2LOCATION_DB_PATH, 'r') as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                try:
                    ip_from = int(row[0])
                    ip_to = int(row[1])
                    country_code = row[2]

                    if ip_from <= ip_num <= ip_to:
                        print(f"IP {ip_address} found in range {ip_from} - {ip_to}, country code: {country_code}")
                        return country_code == "CN" # CN 是中国的 ISO 国家代码

                except ValueError:
                   continue # 忽略格式错误的行

        print(f"IP {ip_address} not found in IP2Location database.")
        return False

    except Exception as e:
        print(f"Error looking up IP {ip_address}: {e}")
        return False


def main():
    all_china_ips = []
    for as_number in AS_NUMBERS:
        print(f"Fetching IPs for {as_number}...")
        ips = get_as_ips(as_number)
        print(f"Found {len(ips)} IPs for {as_number}.")

        china_ips = [ip for ip in ips if is_china_ip(ip)]
        print(f"Found {len(china_ips)} China IPs for {as_number}.")
        all_china_ips.extend(china_ips)

    # Remove duplicates and sort
    unique_china_ips = sorted(list(set(all_china_ips)))

    # Write to file
    with open(OUTPUT_FILE, "w") as f:
        f.write("\n".join(unique_china_ips))

    print(f"Wrote {len(unique_china_ips)} unique China IPs to {OUTPUT_FILE}")
    print(f"Script finished at {datetime.datetime.now()}")


if __name__ == "__main__":
    main()
