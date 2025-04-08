import requests
import datetime

AS_NUMBERS = ["AS4134", "AS4808", "AS4837", "AS9808", "AS4812"]
OUTPUT_FILE = "china_ips.txt"

def get_as_ips(as_number):
    """
    从 ipinfo.io 获取指定 AS 的所有 IP 地址。
    """
    url = f"https://ipinfo.io/{as_number}/cidr"
    try:
        response = requests.get(url)
        response.raise_for_status()  # 抛出 HTTPError for bad responses (4xx or 5xx)
        return response.text.strip().split("\n")
    except requests.exceptions.RequestException as e:
        print(f"Error fetching IPs for {as_number}: {e}")
        return []

def is_china_ip(ip_address):
    """
    判断 IP 地址是否属于中国大陆。这里使用纯真 IP 库 (https://www.ipip.net/) 作为示例。
    **注意：**
    *  纯真 IP 库是商业服务，这里仅为演示目的。实际使用时，请确保你拥有相应的授权。
    *  由于纯真 IP 库更新频率较高，你可能需要定期更新该库。
    *  更推荐的方式是使用专门的 IP 地理位置查询服务（如 MaxMind GeoIP2、IP2Location 等），它们提供更准确和可靠的数据。
    """
    import ipaddress

    try:
        ip = ipaddress.ip_address(ip_address)  # 检查是否为有效的 IP 地址
    except ValueError:
        print(f"Invalid IP address: {ip_address}")
        return False

    try:
        # 注意：这里需要你自己的纯真 IP 库（qqwry.dat）。你需要自行下载并将其放在与 main.py 相同的目录下。
        # 为了简化示例，这里注释掉了，你需要取消注释并替换成你自己的实现。
        #
        # from qqwry import QQwry
        # q = QQwry()
        # q.load_file('qqwry.dat') # 纯真 IP 数据库文件
        # result = q.lookup(ip_address)
        # if result and "中国" in result[0]:
        #    return True
        # else:
        #    return False

        #  由于无法直接提供 qqwry.dat 的下载和使用，这里提供一个简化的占位符实现
        #  请用更可靠和授权的方式来判断 IP 归属地

        # 占位符实现： 模拟判断一些常见网段
        if ip.subnet_of(ipaddress.ip_network('101.0.0.0/8')):
            return True
        elif ip.subnet_of(ipaddress.ip_network('58.0.0.0/8')):
            return True
        else:
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
