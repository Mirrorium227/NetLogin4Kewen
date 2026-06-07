"""
NL4KWTC 校园网登录系统 - Windows 教师网自动账号轮转版

用途：
1. 读取同目录 config_tc_auto.ini 中的多个教师网账号。
2. 启动后随机打乱账号顺序，逐个向教师网认证接口直接发包。
3. 教师网没有运营商选项，因此配置文件只需要 username/password。
4. 附带 logout 参数时，按 HAR 中的教师网注销接口注销。
"""

import configparser
import os
import random
import sys
import time
from typing import Dict, List, Optional
from urllib.parse import urlencode

import requests

from NL4KWTC_Win import BASE_URL, TeacherNetLogin, get_app_dir, mask_username


APP_NAME = "NL4KWTC 校园网登录系统"
APP_EDITION = "Windows 教师网自动账号轮转版"
CONFIG_FILE_NAME = "config_tc_auto.ini"


DEFAULT_ACCOUNT_SLOTS: List[Dict[str, str]] = [
    {"username": "示例账号1", "password": "示例密码1"},
    {"username": "示例账号2", "password": "示例密码2"},
]


def print_banner() -> None:
    print("=" * 56)
    print(f"[系统] {APP_NAME}")
    print(f"[系统] 当前版本：{APP_EDITION}")
    print("=" * 56)


class TeacherNetAutoLogin(TeacherNetLogin):
    def __init__(self) -> None:
        super().__init__()
        self.config_path = os.path.join(get_app_dir(), CONFIG_FILE_NAME)

    def build_account_pool(self) -> List[Dict[str, str]]:
        """读取外置配置，过滤空账号/默认示例账号，并随机打乱顺序。"""
        config = self.load_auto_config()
        if config is None:
            return []

        accounts = []
        for section in config.sections():
            if not section.upper().startswith("ACCOUNT_"):
                continue

            username = config.get(section, "username", fallback="").strip()
            password = config.get(section, "password", fallback="").strip()
            if self.is_default_or_empty_account(username, password):
                print(f"[提示] 已跳过未填写或保持示例值的账号位: {section}")
                continue

            accounts.append({"username": username, "password": password})

        random.shuffle(accounts)
        return accounts

    def load_auto_config(self) -> Optional[configparser.ConfigParser]:
        """首次运行时创建两个账号位；之后读取用户填写的账号池。"""
        config = configparser.ConfigParser()
        if not os.path.exists(self.config_path):
            self.create_default_config(config)
            print(f"[配置] 已创建教师网自动轮转配置文件: {self.config_path}")
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
        for index, account in enumerate(DEFAULT_ACCOUNT_SLOTS, start=1):
            config[f"ACCOUNT_{index}"] = {
                "username": account["username"],
                "password": account["password"],
            }

        with open(self.config_path, "w", encoding="utf-8") as file:
            config.write(file)

    @staticmethod
    def is_default_or_empty_account(username: str, password: str) -> bool:
        """只要账号或密码为空，或任一字段仍为示例值，就不作为可用账号。"""
        if not username or not password:
            return True

        default_usernames = {account["username"] for account in DEFAULT_ACCOUNT_SLOTS}
        default_passwords = {account["password"] for account in DEFAULT_ACCOUNT_SLOTS}
        default_usernames.update({"YOUR_USERNAME", "2024000001", "2024000002"})
        default_passwords.update({"YOUR_PASSWORD", "password_1", "password_2"})
        return username in default_usernames or password in default_passwords

    def login_once(self, account: Dict[str, str], ip_address: str) -> bool:
        """教师网单账号登录：不追加任何运营商后缀。"""
        query_params = {
            "c": "Portal",
            "a": "login",
            "callback": "dr1003",
            "login_method": "1",
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

        print(f"[尝试] 账号 {mask_username(account['username'])} | IP {ip_address}")
        try:
            response = self.session.get(login_url, timeout=10)
            response.raise_for_status()
        except requests.RequestException as exc:
            print(f"[失败] 请求异常: {exc}")
            return False

        if '"result":"1"' in response.text or self.parse_jsonp_result(response.text) == "1":
            print(f"[成功] 登录成功: {mask_username(account['username'])}")
            return True

        print(f"[失败] 登录失败: {mask_username(account['username'])} | 响应预览: {response.text[:160]}")
        return False

    def login(self) -> bool:
        accounts = self.build_account_pool()
        if not accounts:
            print(f"[错误] 没有可用账号，请先在 {CONFIG_FILE_NAME} 中填写账号信息")
            return False

        ip_address = self.choose_login_ip()
        if not ip_address:
            print("[错误] 未检测到 10.xxx.xxx.xxx 网卡地址，无法发送登录请求")
            return False

        if self.check_status():
            print("[信息] 当前网络已经登录，程序退出")
            return True

        print(f"[信息] 本次将按随机顺序尝试 {len(accounts)} 个账号")
        for account in accounts:
            if self.login_once(account, ip_address):
                return True

        print("[失败] 所有账号均尝试失败，程序退出")
        return False


def main() -> int:
    print_banner()
    client = TeacherNetAutoLogin()
    if len(sys.argv) > 1 and sys.argv[1].lower() == "logout":
        return 0 if client.logout() else 1
    return 0 if client.login() else 1


if __name__ == "__main__":
    sys.exit(main())
