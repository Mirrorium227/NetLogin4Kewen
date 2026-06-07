"""
NL4KWTC 校园网登录系统 - Windows 教师网普通版

教师网逻辑来自 KWXY/10.110.6.251.har：
1. 状态检查：GET http://10.110.6.251/drcom/chkstatus
2. 登录接口：GET http://10.110.6.251:801/eportal/?c=Portal&a=login
3. 注销接口：GET http://10.110.6.251:801/eportal/?c=Portal&a=logout

教师网与学生网的核心差异：
- 教师网没有运营商选项。
- 登录时 user_account 固定为 ",0,账号"，不追加 @cmcc/@unicom/@telecom 等后缀。

使用方式：
- 直接运行：登录
- 运行时附带 logout 参数：注销，例如 python NL4KWTC_Win.py logout
"""

import configparser
import json
import os
import re
import socket
import subprocess
import sys
import time
from typing import Dict, Optional
from urllib.parse import urlencode

import requests


APP_NAME = "NL4KWTC 校园网登录系统"
APP_EDITION = "Windows 教师网普通版"
BASE_URL = "http://10.110.6.251"
AUTH_HOST = "10.110.6.251"
CONFIG_FILE_NAME = "config_tc.ini"
DEFAULT_USERNAME = "YOUR_USERNAME"
DEFAULT_PASSWORD = "YOUR_PASSWORD"


def print_banner() -> None:
    print("=" * 56)
    print(f"[系统] {APP_NAME}")
    print(f"[系统] 当前版本：{APP_EDITION}")
    print("=" * 56)


def get_app_dir() -> str:
    """返回脚本或 exe 所在目录，配置文件也保存在这里。"""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def mask_username(username: str) -> str:
    """控制台日志只显示脱敏账号。"""
    if len(username) <= 4:
        return "*" * len(username)
    return f"{username[:2]}{'*' * (len(username) - 4)}{username[-2:]}"


class TeacherNetLogin:
    def __init__(self) -> None:
        self.config_path = os.path.join(get_app_dir(), CONFIG_FILE_NAME)
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
                "Accept": "*/*",
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                "Referer": f"{BASE_URL}/",
            }
        )

    def load_config(self) -> Optional[Dict[str, str]]:
        """读取单账号配置；首次运行时创建模板并退出。"""
        config = configparser.ConfigParser()
        if not os.path.exists(self.config_path):
            config["LOGIN"] = {
                "username": DEFAULT_USERNAME,
                "password": DEFAULT_PASSWORD,
            }
            with open(self.config_path, "w", encoding="utf-8") as file:
                config.write(file)
            print(f"[配置] 已创建教师网配置文件: {self.config_path}")
            print("[提示] 请填写 username/password 后重新运行程序")
            return None

        config.read(self.config_path, encoding="utf-8")
        if not config.has_section("LOGIN"):
            print("[错误] 配置文件缺少 [LOGIN] 部分")
            return None

        username = config.get("LOGIN", "username", fallback="").strip()
        password = config.get("LOGIN", "password", fallback="").strip()
        if self.is_default_or_empty(username, password):
            print("[错误] 配置文件中的账号或密码为空，或仍保持默认示例值")
            return None

        print(f"[信息] 已读取配置: 用户名={mask_username(username)}")
        return {"username": username, "password": password}

    @staticmethod
    def is_default_or_empty(username: str, password: str) -> bool:
        return (
            not username
            or not password
            or username == DEFAULT_USERNAME
            or password == DEFAULT_PASSWORD
        )

    def choose_login_ip(self) -> Optional[str]:
        """优先选择到认证服务器的路由 IP，再回退到 ipconfig 中第一个 10.* 地址。"""
        routed_ip = self.get_routed_ip()
        if routed_ip:
            print(f"[信息] 已根据路由自动选中网卡地址: {routed_ip}")
            return routed_ip

        ips = self.get_candidate_ips()
        if ips:
            print(f"[信息] 已从网卡列表选中地址: {ips[0]}")
            return ips[0]
        return None

    def get_routed_ip(self) -> Optional[str]:
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

    @staticmethod
    def get_candidate_ips() -> list[str]:
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

    def check_status(self) -> bool:
        """教师网 HAR 中 result=1 表示已在线，result=0 表示未登录。"""
        params = {"callback": "dr1002", "v": str(int(time.time() * 1000) % 10000)}
        url = f"{BASE_URL}/drcom/chkstatus?{urlencode(params)}"
        try:
            response = self.session.get(url, timeout=5)
            response.raise_for_status()
        except requests.RequestException as exc:
            print(f"[提示] 当前无法确认登录状态，将继续执行: {exc}")
            return False

        return self.parse_jsonp_result(response.text) == "1"

    @staticmethod
    def parse_jsonp_result(text: str) -> str:
        match = re.search(r"\((\{.*\})\)\s*$", text)
        if match:
            try:
                return str(json.loads(match.group(1)).get("result", ""))
            except json.JSONDecodeError:
                pass

        match = re.search(r'"result"\s*:\s*"?([^",}]+)"?', text)
        return match.group(1) if match else ""

    def login(self) -> bool:
        account = self.load_config()
        if account is None:
            return False

        ip_address = self.choose_login_ip()
        if not ip_address:
            print("[错误] 未检测到 10.xxx.xxx.xxx 网卡地址，无法发送登录请求")
            return False

        if self.check_status():
            print("[信息] 当前网络已经登录，程序退出")
            return True

        query_params = {
            "c": "Portal",
            "a": "login",
            "callback": "dr1003",
            "login_method": "1",
            # 教师网没有运营商后缀，HAR 中为 user_account=%2C0%2Cfh-sc。
            "user_account": f",0,{account['username']}",
            "user_password": account["password"],
            "wlan_user_ip": ip_address,
            "wlan_user_ipv6": "",
            "wlan_user_mac": "000000000000",
            "wlan_ac_ip": "",
            "wlan_ac_name": "",
            "jsVersion": "3.3.2",
            "v": str(int(time.time() * 1000) % 10000),
        }
        login_url = f"{BASE_URL}:801/eportal/?{urlencode(query_params)}"

        print(f"[系统] 正在发送教师网认证请求: {mask_username(account['username'])}")
        try:
            response = self.session.get(login_url, timeout=10)
            response.raise_for_status()
        except requests.RequestException as exc:
            print(f"[失败] 请求异常: {exc}")
            return False

        if '"result":"1"' in response.text or self.parse_jsonp_result(response.text) == "1":
            print("[成功] 网络认证成功")
            return True

        print(f"[失败] 认证未通过，响应预览: {response.text[:200]}")
        return False

    def logout(self) -> bool:
        ip_address = self.choose_login_ip()
        if not ip_address:
            print("[错误] 未检测到 10.xxx.xxx.xxx 网卡地址，无法发送注销请求")
            return False

        query_params = {
            "c": "Portal",
            "a": "logout",
            "callback": "dr1004",
            "login_method": "1",
            # HAR 中注销接口使用固定占位账号密码。
            "user_account": "drcom",
            "user_password": "123",
            "ac_logout": "0",
            "register_mode": "0",
            "wlan_user_ip": ip_address,
            "wlan_user_ipv6": "",
            "wlan_vlan_id": "0",
            "wlan_user_mac": "000000000000",
            "wlan_ac_ip": "",
            "wlan_ac_name": "",
            "jsVersion": "3.3.2",
            "v": str(int(time.time() * 1000) % 10000),
        }
        logout_url = f"{BASE_URL}:801/eportal/?{urlencode(query_params)}"

        print("[系统] 正在发送教师网注销请求")
        try:
            response = self.session.get(logout_url, timeout=10)
            response.raise_for_status()
        except requests.RequestException as exc:
            print(f"[失败] 请求异常: {exc}")
            return False

        if '"result":"1"' in response.text or self.parse_jsonp_result(response.text) == "1":
            print("[成功] 注销成功")
            return True

        print(f"[失败] 注销未通过，响应预览: {response.text[:200]}")
        return False


def main() -> int:
    print_banner()
    client = TeacherNetLogin()
    if len(sys.argv) > 1 and sys.argv[1].lower() == "logout":
        return 0 if client.logout() else 1
    return 0 if client.login() else 1


if __name__ == "__main__":
    sys.exit(main())
