"""
NL4KW 校园网登录系统 - Windows 自动账号轮转版

用途：
1. 读取同目录 config_auto.ini 中的多个账号 / 密码 / 运营商组合。
2. 启动后随机打乱账号顺序，逐个向认证网关直接发包。
3. 若当前已经登录则立即退出；若某个账号失败则继续尝试下一个。
4. 多网卡环境下优先选择到认证服务器路由命中的 10.* 地址。

适用环境：Windows + Python，依赖 requests。
"""

import configparser
import json
import os
import random
import re
import socket
import subprocess
import sys
import time
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlencode

import requests


BASE_URL = "http://10.110.6.251"
APP_NAME = "NL4KW 校园网登录系统"
APP_EDITION = "Windows 自动账号轮转版"
AUTH_HOST = "10.110.6.251"
CONFIG_FILE_NAME = "config_auto.ini"


# 首次运行会把这两个账号位写入 config_auto.ini。
# 用户如果保留这些示例值，程序不会把它们视为可用账号。
DEFAULT_ACCOUNT_SLOTS: List[Dict[str, str]] = [
    {"username": "示例账号1", "password": "示例密码1", "operator": "中国联通"},
    {"username": "示例账号2", "password": "示例密码2", "operator": "中国移动"},
]


def print_banner() -> None:
    """统一输出启动横幅，便于四个实现保持同一套系统观感。"""
    print("=" * 56)
    print(f"[系统] {APP_NAME}")
    print(f"[系统] 当前版本：{APP_EDITION}")
    print("=" * 56)


def get_app_dir() -> str:
    """返回脚本或 exe 所在目录，用于读取同目录外置配置文件。"""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


class NetAutoLogin:
    def __init__(self) -> None:
        # 运营商后缀必须与认证服务端要求一致，拼接到 user_account 字段后。
        self.operator_map = {
            "校园网": "",
            "中国移动": "@cmcc",
            "中国联通": "@unicom",
            "中国电信": "@telecom",
        }

        # 模拟浏览器请求头，避免认证网关拒绝非浏览器请求。
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept": "*/*",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Referer": f"{BASE_URL}/",
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self.config_path = os.path.join(get_app_dir(), CONFIG_FILE_NAME)

    def get_candidate_ips(self) -> List[str]:
        """从 Windows ipconfig 输出中收集所有 10.* IPv4 地址。"""
        try:
            completed = subprocess.run(
                ["ipconfig"],
                capture_output=True,
                text=True,
                encoding="gbk",
                errors="ignore",
                check=False,
            )
        except Exception as exc:
            print(f"[错误] 读取网卡信息失败: {exc}")
            return []

        ips = []
        for ip in re.findall(r"\b10(?:\.\d{1,3}){3}\b", completed.stdout):
            if ip not in ips:
                ips.append(ip)
        return ips

    def choose_login_ip(self) -> Optional[str]:
        """选择用于 wlan_user_ip 的本机地址，优先使用系统路由命中的地址。"""
        ips = self.get_candidate_ips()
        if not ips:
            return None

        routed_ip = self.get_routed_ip()
        if routed_ip and routed_ip in ips:
            print(f"[信息] 已根据路由自动选中网卡地址: {routed_ip}")
            return routed_ip

        if len(ips) > 1:
            print(f"[信息] 检测到多个 10.* 网卡地址: {', '.join(ips)}")
        else:
            print(f"[信息] 检测到登录网卡地址: {ips[0]}")
        return ips[0]

    def get_routed_ip(self) -> Optional[str]:
        """用 UDP connect 让系统判断访问认证网关时会使用哪个本地 IP。"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.connect((AUTH_HOST, 80))
            local_ip = sock.getsockname()[0]
            sock.close()
            if local_ip.startswith("10."):
                return local_ip
        except OSError:
            return None
        return None

    def check_status(self) -> bool:
        """检查认证网关返回的在线状态，result=1 表示已登录。"""
        url = f"{BASE_URL}/drcom/chkstatus"
        try:
            response = self.session.get(url, timeout=5)
            response.raise_for_status()
            try:
                data = response.json()
            except ValueError:
                match = re.search(r'"result"\s*:\s*(\d+)', response.text)
                return bool(match and match.group(1) == "1")
            return data.get("result") == 1
        except requests.RequestException as exc:
            print(f"[提示] 当前无法确认登录状态，将继续尝试登录: {exc}")
            return False

    def parse_login_response(self, text: str) -> Dict[str, object]:
        """解析 dr1003(JSON) 形式的认证响应，并提取成功/已登录状态。"""
        payload = {}
        match = re.search(r"dr1003\((.*)\)\s*$", text)
        if match:
            try:
                payload = json.loads(match.group(1))
            except json.JSONDecodeError:
                payload = {}

        result = str(payload.get("result", ""))
        ret_code = payload.get("ret_code")
        msg = str(payload.get("msg", ""))

        success = result == "1" or '"result":"1"' in text
        already_logged = ret_code == 2 or '"ret_code":2' in text or "您已经登录" in text

        return {
            "success": success,
            "already_logged": already_logged,
            "ret_code": ret_code,
            "msg": msg,
            "raw": text[:300],
        }

    def login_once(self, account: Dict[str, str], ip_address: str) -> Tuple[bool, bool]:
        """使用单个账号发起一次认证请求。返回值为 (登录成功, 已经登录)。"""
        username = account["username"].strip()
        password = account["password"].strip()
        operator_name = account["operator"].strip()
        operator_suffix = self.operator_map.get(operator_name)

        if operator_suffix is None:
            print(f"[提示] 跳过账号 {self.mask_username(username)}，运营商无效: {operator_name}")
            return False, False

        # 与 Windows 普通版保持同一套认证参数；这里通过 urlencode 自动转义特殊字符。
        query_params = {
            "c": "Portal",
            "a": "login",
            "callback": "dr1003",
            "login_method": "1",
            "user_account": f",0,{username}{operator_suffix}",
            "user_password": password,
            "wlan_user_ip": ip_address,
            "wlan_user_ipv6": "",
            "wlan_user_mac": "000000000000",
            "wlan_ac_ip": "",
            "wlan_ac_name": "",
            "jsVersion": "3.3.2",
            "v": str(int(time.time() * 1000) % 10000),
        }
        login_url = f"{BASE_URL}:801/eportal/?{urlencode(query_params)}"

        print(
            f"[尝试] 账号 {self.mask_username(username)} | "
            f"运营商 {operator_name} | IP {ip_address}"
        )

        try:
            response = self.session.get(login_url, timeout=10)
            response.raise_for_status()
        except requests.RequestException as exc:
            print(f"[失败] 请求异常: {exc}")
            return False, False

        parsed = self.parse_login_response(response.text)
        if parsed["success"]:
            print(f"[成功] 登录成功: {self.mask_username(username)}")
            return True, False

        if parsed["already_logged"]:
            print("[信息] 服务器返回已登录状态，程序退出")
            return False, True

        print(
            f"[失败] 登录失败: {self.mask_username(username)} | "
            f"ret_code={parsed['ret_code']} | msg={parsed['msg'] or '无'}"
        )
        return False, False

    @staticmethod
    def mask_username(username: str) -> str:
        if len(username) <= 4:
            return "*" * len(username)
        return f"{username[:2]}{'*' * (len(username) - 4)}{username[-2:]}"

    def build_account_pool(self) -> List[Dict[str, str]]:
        """读取外置配置，过滤无效账号，并随机打乱顺序。"""
        config = self.load_config()
        if config is None:
            return []

        valid_accounts = []
        for section in config.sections():
            if not section.upper().startswith("ACCOUNT_"):
                continue

            username = config.get(section, "username", fallback="").strip()
            password = config.get(section, "password", fallback="").strip()
            operator = config.get(section, "operator", fallback="").strip()

            if self.is_default_or_empty_account(username, password):
                print(f"[提示] 已跳过未填写或保持示例值的账号位: {section}")
                continue

            if username and password and operator:
                valid_accounts.append(
                    {
                        "username": username,
                        "password": password,
                        "operator": operator,
                    }
                )
            else:
                print(f"[提示] 已跳过配置不完整的账号位: {section}")

        random.shuffle(valid_accounts)
        return valid_accounts

    def load_config(self) -> Optional[configparser.ConfigParser]:
        """加载 config_auto.ini；首次运行时创建带两个账号位的模板。"""
        config = configparser.ConfigParser()

        if not os.path.exists(self.config_path):
            self.create_default_config(config)
            print(f"[配置] 已创建自动轮转配置文件: {self.config_path}")
            print("[提示] 请填写账号位后重新运行程序")
            return None

        try:
            config.read(self.config_path, encoding="utf-8")
        except Exception as exc:
            print(f"[错误] 读取配置文件失败: {exc}")
            return None

        if not any(section.upper().startswith("ACCOUNT_") for section in config.sections()):
            print("[错误] 配置文件中未找到 ACCOUNT_ 开头的账号位")
            return None

        print(f"[信息] 已读取自动轮转配置: {self.config_path}")
        return config

    def create_default_config(self, config: configparser.ConfigParser) -> None:
        """创建两个默认账号位，方便用户直接按模板继续扩展。"""
        for index, account in enumerate(DEFAULT_ACCOUNT_SLOTS, start=1):
            config[f"ACCOUNT_{index}"] = {
                "username": account["username"],
                "password": account["password"],
                "operator": account["operator"],
            }

        with open(self.config_path, "w", encoding="utf-8") as file:
            config.write(file)

    @staticmethod
    def is_default_or_empty_account(username: str, password: str) -> bool:
        """账号或密码为空，或仍是模板示例值时，不计入账号池。"""
        if not username or not password:
            return True

        default_usernames = {account["username"] for account in DEFAULT_ACCOUNT_SLOTS}
        default_passwords = {account["password"] for account in DEFAULT_ACCOUNT_SLOTS}
        default_usernames.update({"YOUR_USERNAME", "2024000001", "2024000002"})
        default_passwords.update({"YOUR_PASSWORD", "password_1", "password_2"})
        return username in default_usernames or password in default_passwords

    def run(self) -> int:
        print_banner()

        account_pool = self.build_account_pool()
        if not account_pool:
            print(f"[错误] 没有可用账号，请先在 {CONFIG_FILE_NAME} 中填写账号信息")
            return 1

        ip_address = self.choose_login_ip()
        if not ip_address:
            print("[错误] 未检测到 10.xxx.xxx.xxx 网卡地址，无法发送登录请求")
            return 1

        if self.check_status():
            print("[信息] 当前网络已经登录，程序退出")
            return 0

        print(f"[信息] 本次将按随机顺序尝试 {len(account_pool)} 个账号")
        for account in account_pool:
            success, already_logged = self.login_once(account, ip_address)
            if success:
                return 0
            if already_logged:
                return 0

        print("[失败] 所有账号均尝试失败，程序退出")
        return 1


def main() -> int:
    auto_login = NetAutoLogin()
    return auto_login.run()


if __name__ == "__main__":
    sys.exit(main())
