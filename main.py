import datetime
import time
import ipaddress
import geoip2.database
import os

AS_NUMBERS = ["AS4134", "AS4808", "AS4837", "AS9808", "AS4812"]
OUTPUT_FILE = "china_ips.txt"
GEOIP2_DB_PATH = "GeoLite2-Country.mmdb"  # 数据库文件需要放在相同目录下

def get_as_ips(as_number):
    """
    获取指定 AS 的所有 IP 地址。
    这个函数现在**必须**返回该AS的IP地址列表，否则后续流程会出错。
    如果无法获取，应该记录错误并返回一个空列表。
    **你需要替换这个函数的实现，使用其他数据源来获取 AS 的 IP 地址。**
    """
    #  示例： 占位符实现，你需要替换它
    print(f"Fetching IPs for {as_number} - Placeholder implementation, replace with your data source!")
    return [] # 返回一个空列表，你需要替换它

def is_china_ip(ip_address):
    """
    使用 MaxMind GeoIP2 数据库判断 IP 地址是否属于中国大陆。
    """
    try:
        ip = ipaddress.ip_address(ip_address)
    except ValueError:
        print(f"Invalid IP address: {ip_address}")
        return False

    try:
        # 检查数据库文件是否存在
        if not os.path.exists(GEOIP2_DB_PATH):
            print(f"GeoIP2 database file not found at {GEOIP2_DB_PATH}. Using placeholder China IP check.")
            #  提供一个简化的占位符实现
            #  请用更可靠和授权的方式来判断 IP 归属地
            if ip.subnet_of(ipaddress.ip_network('101.0.0.0/8')):
                return True
            elif ip.subnet_of(ipaddress.ip_network('58.0.0.0/8')):
                return True
            else:
                return False

        with geoip2.database.Reader(GEOIP2_DB_PATH) as reader:
            response = reader.country(ip_address)
            country_code = response.country.iso_code
            print(f"IP {ip_address} country code: {country_code}")  # 增加日志输出
            return country_code == "CN"  # CN 是中国的 ISO 国家代码
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
