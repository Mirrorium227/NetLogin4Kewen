"""
NL4KW 校园网登录系统 - Windows 手动模拟版

用途：
1. 首次运行时记录浏览器页面中账号框、密码框、运营商选项、登录按钮坐标。
2. 后续运行时用 pyautogui 模拟鼠标和键盘完成网页登录。
3. 登录后通过 ping 检查公网连通性。

适用环境：Windows + Python，依赖 pyautogui / keyboard / pywin32。
"""

import pyautogui
import json
import webbrowser
import time
from pathlib import Path
import win32gui
import win32con
import sys
import ctypes
import keyboard
import win32api
import subprocess


APP_NAME = "NL4KW 校园网登录系统"
APP_EDITION = "Windows 手动模拟版"
BASE_URL = "http://10.110.6.251"


def print_banner():
    """统一输出启动横幅，便于四个实现保持同一套系统观感。"""
    print("=" * 56)
    print(f"[系统] {APP_NAME}")
    print(f"[系统] 当前版本：{APP_EDITION}")
    print("=" * 56)


def mask_username(username):
    """日志中只展示账号首尾，避免控制台泄露完整账号。"""
    if len(username) <= 4:
        return "*" * len(username)
    return username[:2] + "*" * (len(username) - 4) + username[-2:]


def get_app_dir():
    """返回脚本或 exe 所在目录，用于持久保存配置文件。"""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).parent


class CampusNetLogin:
    def __init__(self):
        # 坐标和账号信息保存在同目录配置文件，避免每次都重新标定页面位置。
        self.config_file = get_app_dir() / "login_config.json"
        self.positions = {}
        self.credentials = {}
        self.keep_window_on_top()
        
    def keep_window_on_top(self):
        """保持终端窗口在最顶层并设置位置"""
        if sys.stdout.isatty():
            hwnd = win32gui.GetForegroundWindow()
            
            # 使用 win32api 获取屏幕分辨率
            screen_width = win32api.GetSystemMetrics(win32con.SM_CXSCREEN)
            screen_height = win32api.GetSystemMetrics(win32con.SM_CYSCREEN)
            
            # 设置窗口大小为屏幕的1/4
            window_width = screen_width // 2
            window_height = screen_height // 2
            x_position = 0  # 左上角
            y_position = 0  # 左上角
            
            # 设置窗口位置和大小
            win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, 
                                x_position, y_position, 
                                window_width, window_height, 
                                win32con.SWP_SHOWWINDOW)
            
            # 设置窗口标题
            ctypes.windll.kernel32.SetConsoleTitleW(f"{APP_NAME} - {APP_EDITION}")
            
    def wait_for_alt(self, message):
        """等待用户按下Alt键"""
        print(message)
        print("[提示] 请点击相应位置后按下 Alt 键继续...")
        keyboard.wait('alt')
        time.sleep(0.5)  # 等待按键释放
        
    def first_time_setup(self):
        """首次运行时的设置向导"""
        print("[配置] 首次运行，进入坐标标定向导")
        print("[提示] 请按照提示点击相应位置，点击后按 Alt 键继续")
        
        # 收集网页元素坐标。模拟版依赖这些坐标完成后续自动点击。
        positions = {}
        
        self.wait_for_alt("[配置] 请点击账号输入框位置...")
        time.sleep(0.5)  # 给用户一点时间确保鼠标位置正确
        positions['username_field'] = pyautogui.position()
        
        self.wait_for_alt("[配置] 请点击密码输入框位置...")
        time.sleep(0.5)
        positions['password_field'] = pyautogui.position()
        
        self.wait_for_alt("[配置] 请点击'登录选项'按钮...")
        time.sleep(0.5)
        positions['login_options'] = pyautogui.position()
        
        self.wait_for_alt("[配置] 请点击具体的登录选项...")
        time.sleep(0.5)
        positions['specific_option'] = pyautogui.position()
        
        self.wait_for_alt("[配置] 请点击登录按钮...")
        time.sleep(0.5)
        positions['login_button'] = pyautogui.position()
        
        # 获取账号密码
        username = input("[配置] 请输入您的学号：")
        password = input("[配置] 请输入您的密码：")
        
        # 保存配置。position 对象会被 json 转为坐标列表，pyautogui.click 可直接使用。
        config = {
            'positions': positions,
            'credentials': {
                'username': username,
                'password': password
            }
        }
        
        with open(self.config_file, 'w') as f:
            json.dump(config, f)
        print(f"[配置] 坐标和账号配置已保存: {self.config_file}")
            
    def load_config(self):
        """加载配置文件"""
        with open(self.config_file, 'r') as f:
            config = json.load(f)
            self.positions = config['positions']
            self.credentials = config['credentials']
        print(f"[信息] 已读取配置: 用户名={mask_username(self.credentials.get('username', ''))}")
            
    def check_internet_connection(self):
        """检查网络连接"""
        try:
            # 用 ping 公网域名判断认证完成后是否已经具备 Internet 访问能力。
            result = subprocess.run(['ping', 'www.baidu.com', '-n', '1'], 
                                 capture_output=True, 
                                 text=True)
            return result.returncode == 0
        except Exception as e:
            print(f"[错误] 检测网络连接时出错: {e}")
            return False

    def perform_login(self):
        """执行登录操作"""
        # 打开浏览器访问登录页面
        print("[系统] 正在打开浏览器并访问登录页面...")
        webbrowser.open(BASE_URL)
        time.sleep(3)  # 等待页面加载
        
        # 输入账号
        print("[信息] 正在输入账号...")
        pyautogui.click(self.positions['username_field'])
        pyautogui.write(self.credentials['username'])
        
        # 输入密码
        print("[信息] 正在输入密码...")
        pyautogui.click(self.positions['password_field'])
        pyautogui.write(self.credentials['password'])
        
        # 点击登录选项
        print("[信息] 正在选择认证通道...")
        pyautogui.click(self.positions['login_options'])
        time.sleep(1)
        
        # 选择具体选项
        pyautogui.click(self.positions['specific_option'])
        
        # 点击登录
        print("[系统] 正在点击登录按钮...")
        pyautogui.click(self.positions['login_button'])
        
        # 立即输出检测网络连接的状态
        print("[检测] 正在检测是否连接到 Internet...")
        
        # 等待一段时间让登录完成
        time.sleep(3)
        
        # 开始检测网络连接
        if self.check_internet_connection():
            print("[成功] 认证成功")
        else:
            print("[失败] 联网可能未成功，请检查登录状态")
        
        # 等待3秒后关闭
        print("\n[系统] 程序将在3秒后自动关闭...")
        time.sleep(3)
        sys.exit(0)

    def run(self):
        """主运行函数"""
        print_banner()
        if not self.config_file.exists():
            self.first_time_setup()
        
        self.load_config()
        self.perform_login()

if __name__ == "__main__":
    login_bot = CampusNetLogin()
    login_bot.run()
