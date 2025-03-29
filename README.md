# 江苏师范大学潘安湖校区(科文学院)校园网登录器
本项目使用Python构建，主要通过模拟HTTP请求实现校园网认证过程，以下是其核心原理和实现方式：

## 基本原理
1. **认证机制**：程序通过向校园网认证服务器(10.110.6.251)发送特定格式的HTTP请求，模拟用户在Web页面上的登录操作。
2. **运营商区分**：通过在用户名后添加特定后缀(@cmcc/@unicom/@telecom)来区分不同运营商的认证通道。
3. **会话维持**：使用requests.Session对象保持HTTP会话状态，便于后续状态检查。
4. **自动重连**：定期检测网络连接状态，在断网时自动重新发起认证请求。

## 技术实现
1. **配置管理**：
   - 使用configparser库读写INI格式的配置文件
   - 支持首次运行自动创建配置模板
   - 实现账号密码和运营商信息的持久化存储
1. **网络操作**：
   - 使用socket库获取本机IP地址
   - 通过requests库构造并发送HTTP认证请求
   - 解析JSON格式的服务器响应判断认证结果
1. **WiFi检测**：
   - 利用pywifi库获取当前连接的WiFi网络名称
   - 判断是否连接到指定的校园网WiFi(KWXY_Stu)
1. **用户界面**：
   - 使用win32gui/win32api实现窗口置顶和大小控制
   - 通过ctypes设置控制台窗口标题
   - 实现账号信息脱敏显示保护隐私
1. **异常处理**：
   - 完善的异常捕获机制确保程序稳定运行
   - 网络错误、解析错误等情况下的友好提示
   - 支持多次重试提高认证成功率
1. **跨平台兼容**：
   - 针对Windows/Unix系统实现不同的输入检测方法
   - 兼容Python脚本和打包后的exe运行环境
这个程序本质上是通过分析校园网认证系统的通信协议，然后使用编程方式自动完成认证过程，避免了手动登录的繁琐，并通过定时检测确保网络连接的持续可用。


## 如何使用？
1. 确保已安装Python 3.6+
2. 安装依赖库：
```bash
pip install requests pywifi pywin32
```
3. 首次运行会自动创建`config.ini`配置文件
4. 用记事本打开`config.ini`填写以下信息：
```ini
[LOGIN]
username = 您的校园网账号
password = 您的校园网密码
operator = 中国联通
```

```
"中国联通"这里可选：校园网/中国移动/中国联通/中国电信
```

5. 运行程序：
```bash
python netlogin4kewen_Net.py
```

## 打包为EXE
使用PyInstaller打包：
```bash
pip install pyinstaller
pyinstaller --onefile --windowed netlogin4kewen_Net.py
```

## 注意事项
1. 请确保连接到校园网WiFi（KWXY_Stu）
2. 运营商选择必须与账号类型匹配
3. 程序需要管理员权限获取网络信息
4. 密码以明文存储在config.ini中，请注意保护

## 常见问题
Q: 登录失败怎么办？
A: 请检查：
- 是否连接到校园网WiFi
- 账号密码是否正确
- 运营商选择是否匹配账号类型

Q: 窗口无法置顶？
A: 请以管理员身份运行程序