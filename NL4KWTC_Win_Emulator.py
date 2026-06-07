"""
NL4KWTC 校园网登录系统 - Windows 教师网手动模拟版

用途：
1. 打开教师网登录页 http://10.110.6.251。
2. 首次运行时记录账号框、密码框、登录按钮坐标。
3. 后续运行时用 pyautogui 模拟鼠标和键盘完成网页登录。

教师网页面没有运营商选项，因此本版本不记录运营商选择坐标。
"""

import ctypes
import json
import subprocess
import sys
import time
import webbrowser
from pathlib import Path

import keyboard
import pyautogui
import win32api
import win32con
import win32gui


APP_NAME = "NL4KWTC 校园网登录系统"
APP_EDITION = "Windows 教师网手动模拟版"
BASE_URL = "http://10.110.6.251"
CONFIG_FILE_NAME = "login_config_tc.json"


def print_banner() -> None:
    print("=" * 56)
    print(f"[系统] {APP_NAME}")
    print(f"[系统] 当前版本：{APP_EDITION}")
    print("=" * 56)


def get_app_dir() -> Path:
    """返回脚本或 exe 所在目录，坐标配置文件也保存在这里。"""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).parent


def mask_username(username: str) -> str:
    if len(username) <= 4:
        return "*" * len(username)
    return f"{username[:2]}{'*' * (len(username) - 4)}{username[-2:]}"


class TeacherCampusNetEmulator:
    def __init__(self) -> None:
        self.config_file = get_app_dir() / CONFIG_FILE_NAME
        self.positions = {}
        self.credentials = {}
        self.keep_window_on_top()

    def keep_window_on_top(self) -> None:
        """把控制台固定到左上角，标定坐标时更容易看提示。"""
        if sys.stdout.isatty():
            hwnd = win32gui.GetForegroundWindow()
            screen_width = win32api.GetSystemMetrics(win32con.SM_CXSCREEN)
            screen_height = win32api.GetSystemMetrics(win32con.SM_CYSCREEN)
            win32gui.SetWindowPos(
                hwnd,
                win32con.HWND_TOPMOST,
                0,
                0,
                screen_width // 2,
                screen_height // 2,
                win32con.SWP_SHOWWINDOW,
            )
            ctypes.windll.kernel32.SetConsoleTitleW(f"{APP_NAME} - {APP_EDITION}")

    def wait_for_alt(self, message: str) -> None:
        print(message)
        print("[提示] 请点击相应位置后按下 Alt 键继续...")
        keyboard.wait("alt")
        time.sleep(0.5)

    def first_time_setup(self) -> None:
        """首次运行时记录教师网登录页面的三个关键坐标。"""
        print("[配置] 首次运行，进入教师网坐标标定向导")
        print("[提示] 教师网没有运营商选项，只需标定账号、密码和登录按钮")

        positions = {}
        self.wait_for_alt("[配置] 请点击账号输入框位置...")
        positions["username_field"] = pyautogui.position()

        self.wait_for_alt("[配置] 请点击密码输入框位置...")
        positions["password_field"] = pyautogui.position()

        self.wait_for_alt("[配置] 请点击登录按钮...")
        positions["login_button"] = pyautogui.position()

        username = input("[配置] 请输入教师网账号：").strip()
        password = input("[配置] 请输入教师网密码：").strip()

        config = {
            "positions": positions,
            "credentials": {
                "username": username,
                "password": password,
            },
        }

        with open(self.config_file, "w", encoding="utf-8") as file:
            json.dump(config, file, ensure_ascii=False, indent=2)
        print(f"[配置] 坐标和账号配置已保存: {self.config_file}")

    def load_config(self) -> None:
        with open(self.config_file, "r", encoding="utf-8") as file:
            config = json.load(file)
        self.positions = config["positions"]
        self.credentials = config["credentials"]
        print(f"[信息] 已读取配置: 用户名={mask_username(self.credentials.get('username', ''))}")

    @staticmethod
    def check_internet_connection() -> bool:
        """用 ping 公网域名判断网页登录后是否具备 Internet 访问能力。"""
        try:
            result = subprocess.run(
                ["ping", "www.baidu.com", "-n", "1"],
                capture_output=True,
                text=True,
                check=False,
            )
            return result.returncode == 0
        except Exception as exc:
            print(f"[错误] 检测网络连接时出错: {exc}")
            return False

    def perform_login(self) -> None:
        print("[系统] 正在打开浏览器并访问教师网登录页面...")
        webbrowser.open(BASE_URL)
        time.sleep(3)

        print("[信息] 正在输入账号...")
        pyautogui.click(self.positions["username_field"])
        pyautogui.write(self.credentials["username"])

        print("[信息] 正在输入密码...")
        pyautogui.click(self.positions["password_field"])
        pyautogui.write(self.credentials["password"])

        print("[系统] 正在点击登录按钮...")
        pyautogui.click(self.positions["login_button"])

        print("[检测] 正在检测是否连接到 Internet...")
        time.sleep(3)
        if self.check_internet_connection():
            print("[成功] 认证成功")
        else:
            print("[失败] 联网可能未成功，请检查登录状态")

        print("\n[系统] 程序将在3秒后自动关闭...")
        time.sleep(3)

    def run(self) -> int:
        print_banner()
        if not self.config_file.exists():
            self.first_time_setup()

        self.load_config()
        self.perform_login()
        return 0


def main() -> int:
    return TeacherCampusNetEmulator().run()


if __name__ == "__main__":
    sys.exit(main())
