import requests
import json
import time
import configparser
import os
import socket
from urllib.parse import urlencode
import win32gui
import win32con
import win32api
import ctypes
import sys
import pywifi
from pywifi import const

class NetLogin:
    def __init__(self):
        self.base_url = "http://10.110.6.251"
        # 添加运营商映射字典
        self.operator_map = {
            "校园网": "",
            "中国移动": "@cmcc",
            "中国联通": "@unicom",
            "中国电信": "@telecom"
        }
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "*/*",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Referer": "http://10.110.6.251/",
        }
        self.config = self.load_config()
        self.session = requests.Session()
        self.ip_address = self.get_local_ip()
        self.keep_window_on_top()  # 添加窗口控制
    
    def keep_window_on_top(self):
        """保持终端窗口在最顶层并设置位置"""
        if sys.stdout.isatty():
            hwnd = win32gui.GetForegroundWindow()
            
            # 获取屏幕分辨率
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
            ctypes.windll.kernel32.SetConsoleTitleW("校园网自动登录程序")

    def get_local_ip(self):
        """获取本机IP地址"""
        try:
            # 创建一个UDP套接字
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            # 连接到一个外部服务器（实际不会建立连接）
            s.connect(("10.110.6.251", 80))
            # 获取本地IP地址
            ip = s.getsockname()[0]
            s.close()
            print(f"获取到本机IP: {ip}")
            return ip
        except Exception as e:
            print(f"获取IP地址失败: {str(e)}")
            return "0.0.0.0"

    def load_config(self):
        """加载或创建配置文件"""
        config = configparser.ConfigParser()
        
        # 获取程序所在目录（兼容打包后的情况）
        if getattr(sys, 'frozen', False):
            # 如果是打包后的exe
            current_dir = os.path.dirname(sys.executable)
        else:
            # 如果是python脚本
            current_dir = os.path.dirname(os.path.abspath(__file__))
        
        config_path = os.path.join(current_dir, "config.ini")
        
        print(f"[系统] 尝试读取配置文件: {config_path}")
        
        try:
            if not os.path.exists(config_path):
                print(f"\n[系统] 首次运行，正在创建配置文件: {config_path}")
                config["LOGIN"] = {
                    "username": "",
                    "password": "",
                    "operator": "中国联通"
                }
                with open(config_path, "w", encoding="utf-8") as f:
                    config.write(f)
                print("\n[配置] 配置文件创建成功！请按以下说明行设置：")
                print("=" * 50)
                print("[说明] 请使用记事本打开config.ini文件，填写以下信息：")
                print("1. username = 您的校园网账号")
                print("2. password = 您的校园网密码")
                print("3. operator = 您的运营商，可选值：")
                print("   - 校园网")
                print("   - 中国移动")
                print("   - 中国联通")
                print("   - 中国电信")
                print("=" * 50)
                print("\n[提示] 填写完成后保存文件并重新运行本程序")
                input("\n[系统] 按回车键退出...")
                exit()
            
            config.read(config_path, encoding="utf-8")
            
            if not config.has_section("LOGIN"):
                print("[错误] 配置文件缺少 [LOGIN] 部分")
                return None
            
            if not all(key in config["LOGIN"] for key in ["username", "password", "operator"]):
                print("[错误] 配置文件缺少必要的配置项")
                return None
            
            username = config["LOGIN"]["username"]
            password = config["LOGIN"]["password"]
            operator = config["LOGIN"]["operator"]
            
            # 只显示用户名的前两位和后两位，中间用星号代替
            masked_username = username[:2] + '*' * (len(username)-4) + username[-2:]
            print(f"[信息] 读取到配置: 用户名={masked_username}, 运营商={operator}")
            
            if not username.strip() or not password.strip():
                print("[错误] 配置文件中的用户名或密码为空")
                return None
            
            return config
            
        except Exception as e:
            print(f"[错误] 读取配置文件出错: {str(e)}")
            return None

    def get_challenge(self):
        """获取登录前的challenge参数"""
        try:
            url = f"{self.base_url}:801/eportal/?c=ACSetting&a=checkScanIP"
            response = self.session.get(url, headers=self.headers)
            
            print(f"状态检查响应: {response.text[:200]}")
            return {"result": 0}  # 返回默认值
        except Exception as e:
            print(f"获取challenge失败: {str(e)}")
            return {"result": 0}

    def login(self, max_retries=3):
        for attempt in range(max_retries):
            try:
                print("\n[系统] 正在初始化登录模块...")
                start_time = time.time()  # 记录开始时间
                
                if self.config is None:
                    print("[错误] 配置加载失败，请检查config.ini文件")
                    return False
                    
                username = self.config["LOGIN"]["username"].strip()
                password = self.config["LOGIN"]["password"].strip()
                operator_name = self.config["LOGIN"]["operator"].strip()
                operator = self.operator_map.get(operator_name)
                
                if operator is None:
                    print(f"[错误] 无效的运营商设置 '{operator_name}'")
                    print(f"[提示] 可用的运营商选项: {', '.join(self.operator_map.keys())}")
                    return False
                
                print(f"[信息] 当前使用运营商: {operator_name} ({operator})")
                print(f"[信息] 本机IP地址: {self.ip_address}")
                
                if not username or not password:
                    print("[错误] 请在config.ini中填写账号密码")
                    return False
                    
                print(f"[系统] 正在构建认证数据包...")
                
                # 构造登录URL和参数
                login_url = f"{self.base_url}:801/eportal/"
                query_params = {
                    "c": "Portal",
                    "a": "login",
                    "callback": "dr1003",
                    "login_method": "1",
                    "user_account": f",0,{username}{operator}",
                    "user_password": password,
                    "wlan_user_ip": self.ip_address,
                    "wlan_user_ipv6": "",
                    "wlan_user_mac": "000000000000",
                    "wlan_ac_ip": "",
                    "wlan_ac_name": "",
                    "jsVersion": "3.3.2",
                    "v": str(int(time.time() * 1000) % 10000)
                }
                
                login_url = f"{login_url}?{urlencode(query_params)}"
                
                print("[系统] 正在发送认证请求...")
                response = self.session.get(
                    login_url, 
                    headers=self.headers,
                    timeout=10
                )
                
                end_time = time.time()  # 记录结束时间
                elapsed_time = round((end_time - start_time) * 1000)  # 计算用时（毫秒）
                
                if response.status_code == 200:
                    print(f"\n[调试] 服务器响应内容: {response.text[:200]}")
                    print(f"[系统] 认证请求处理完成 (用时: {elapsed_time}ms)")
                    
                    if "dr1003({\"result\":\"1\"" in response.text:
                        print(f"\n[成功] 网络认证成功！")
                        print(f"[信息] 运营商: {operator_name}")
                        print(f"[信息] 用户名: {username[:2]}{'*' * (len(username)-4)}{username[-2:]}")
                        return True
                    else:
                        print("\n[失败] 认证未通过")
                        if "ret_code\":1" in response.text:
                            print("[错误] 账号或密码错误，请检查配置文件中的账号密码")
                        elif "ret_code\":2" in response.text:
                            print("[提示] 您已经登录，无需重复登录")
                        else:
                            print("[错误] 登录失败，请检查账号密码是否正确，或尝试切换其他运营商")
                        return False
                print(f"\n[重试] 第 {attempt + 1} 次登录失败，准备重试...")
                time.sleep(2)  # 重试前等待
            except requests.exceptions.RequestException as e:
                print(f"\n[网络错误] 连接服务器失败: {str(e)}")
                return False
            except json.JSONDecodeError as e:
                print(f"\n[解析错误] 服务器响应格式异常: {str(e)}")
                return False
            except Exception as e:
                print(f"\n[系统错误] 未知异常: {str(e)}")
                return False
        return False

    def check_status(self):
        """检查当前登录状态"""
        try:
            url = f"{self.base_url}/drcom/chkstatus"
            response = self.session.get(url, headers=self.headers)
            result = response.json()
            return result.get("result") == 1
        except:
            return False

    def check_network(self):
        """检查基本网络连接"""
        try:
            requests.get(self.base_url, timeout=5)
            return True
        except:
            print("[错误] 无法连接到认证服务器，请检查网络连接")
            return False

    def check_wifi_ssid(self):
        """
        检查当前连接的WiFi SSID
        :return: (is_target_network, ssid)
        """
        try:
            wifi = pywifi.PyWiFi()
            iface = wifi.interfaces()[0]  # 获取第一个无线网卡
            
            if iface.status() == const.IFACE_CONNECTED:
                ssid = iface.scan_results()[0].ssid.strip()
                is_target = ssid == "KWXY_Stu"
                return is_target, ssid
            return False, "未连接到任何WiFi"
        except Exception as e:
            print(f"[错误] 获取WiFi信息失败: {str(e)}")
            return False, "获取WiFi信息失败"

    def auto_reconnect(self, check_interval=60):
        """
        自动重连功能
        :param check_interval: 检查间隔（秒）
        """
        print("[系统] 启动自动重连监控...")
        while True:
            try:
                # 先检查WiFi连接
                is_target_wifi, current_ssid = self.check_wifi_ssid()
                if not is_target_wifi:
                    print(f"\n[警告] WiFi已切换: {current_ssid}")
                    print("[系统] 等待重新连接到校园网...")
                    time.sleep(check_interval)
                    continue
                    
                if not self.check_status():
                    print("[检测] 网络已断开，尝试重新登录...")
                    self.login()
                time.sleep(check_interval)
            except KeyboardInterrupt:
                print("\n[系统] 自动重连监控已停止")
                break
            except Exception as e:
                print(f"[错误] 重连过程发生异常: {str(e)}")
                time.sleep(5)

def main():
    """主函数"""
    print("校园网自动登录程序启动...")
    
    login_client = NetLogin()
    
    # 首先检查WiFi连接
    is_target_wifi, current_ssid = login_client.check_wifi_ssid()
    if not is_target_wifi:
        print(f"\n[警告] 当前连接的WiFi不是校园网(KWXY_Stu)")
        print(f"[信息] 当前WiFi: {current_ssid}")
        choice = input("是否继续运行程序？(y/n): ")
        if choice.lower() != 'y':
            print("[系统] 程序已终止")
            return
    
    # 检查当前是否已登录
    if login_client.check_status():
        print("已经处于登录状态！")
        try:
            # 已登录状态直接进入自动重连监控
            print("\n[系统] 正在启动自动重连监控...")
            login_client.auto_reconnect()
        except KeyboardInterrupt:
            print("\n[系统] 程序已终止")
        return
    else:
        # 未登录时才需要进行登录操作
        login_client.login()
        
        # 修改自动重连提示
        print("\n[提示] 按回车键开始自动重连监控，3秒内无操作自动退出程序...")
        
        # 使用select模块实现带超时的输入
        import select
        import sys
        
        # 在Windows系统下，我们需要使用不同的方法
        if sys.platform == 'win32':
            import msvcrt
            import time
            
            start_time = time.time()
            while time.time() - start_time < 3:  # 3秒超时
                if msvcrt.kbhit():  # 检查是否有按键
                    if msvcrt.getch() in [b'\r', b'\n']:  # 检查是否是回车键
                        try:
                            login_client.auto_reconnect()
                        except KeyboardInterrupt:
                            print("\n[系统] 程序已终止")
                        return
                time.sleep(0.1)
        else:
            # Unix系统使用select
            rlist, _, _ = select.select([sys.stdin], [], [], 3)
            if rlist:
                sys.stdin.readline()
                try:
                    login_client.auto_reconnect()
                except KeyboardInterrupt:
                    print("\n[系统] 程序已终止")
                return
        
        print("\n[系统] 无操作，程序自动退出")

if __name__ == "__main__":
    main()