# NL4KW 校园网登录系统

NL4KW 是同一套校园网登录逻辑的多端实现，面向 Windows 普通使用、Windows 自动账号轮转、Windows 手动模拟登录，以及 Linux/OpenWrt 直接发包登录。

认证网关默认地址为 `http://10.110.6.251`。Windows 端 exe 已放在 `dist_exe` 目录，可直接作为 Release 附件发布。

教师网适配版本使用 `NL4KWTC` 前缀。教师网没有运营商选项，登录时不会给账号追加运营商后缀。

## 文件说明

| 文件 | 对应版本 | 说明 |
| --- | --- | --- |
| `NL4KW_Win.py` | Windows 普通版 | 读取 `config.ini` 中的单个账号，通过认证接口直接发包登录，并支持 WiFi 检查和自动重连监控。 |
| `NL4KW_Win_auto.py` | Windows 自动账号轮转版 | 读取 `config_auto.ini` 中的多个账号、密码、运营商组合，启动后随机轮转尝试登录。 |
| `NL4KW_Win_Emulator.py` | Windows 手动模拟版 | 记录网页元素坐标，使用鼠标和键盘模拟网页登录流程。 |
| `NL4KW_Linux.sh` | Linux/OpenWrt 端 | 在脚本内配置账号，通过 `curl`、`wget` 或 `uclient-fetch` 直接发包认证。 |
| `dist_exe/` | Windows exe 成品 | 已打包好的三个 Windows 可执行文件。 |
| `spec/` | PyInstaller 配置 | 记录三个 Windows exe 的打包参数，便于后续复现构建。 |
| `RELEASE.md` | 发布说明 | 可作为 Release 页面正文使用。 |

## 教师网适配

教师网逻辑来自 `KWXY/10.110.6.251.har`。HAR 中的关键请求如下：

| 流程 | 接口 | 关键差异 |
| --- | --- | --- |
| 状态检查 | `GET /drcom/chkstatus` | `result=1` 表示已在线，`result=0` 表示未登录。 |
| 登录 | `GET :801/eportal/?c=Portal&a=login` | `user_account` 为 `,0,账号`，不带运营商后缀。 |
| 注销 | `GET :801/eportal/?c=Portal&a=logout` | 使用 HAR 中的 `drcom/123` 占位参数注销。 |

教师网脚本文件：

| 文件 | 对应版本 | 配置文件 |
| --- | --- | --- |
| `NL4KWTC_Win.py` | Windows 教师网普通版 | `config_tc.ini` |
| `NL4KWTC_Win_auto.py` | Windows 教师网自动账号轮转版 | `config_tc_auto.ini` |
| `NL4KWTC_Win_Emulator.py` | Windows 教师网手动模拟版 | `login_config_tc.json` |
| `NL4KWTC_Linux.sh` | Linux/OpenWrt 教师网端 | 直接编辑脚本顶部账号密码 |

教师网直接运行脚本时执行登录；附带 `logout` 参数时执行注销，例如：

```powershell
python .\NL4KWTC_Win.py logout
python .\NL4KWTC_Win_auto.py logout
```

```sh
sh NL4KWTC_Linux.sh logout
```

## Windows exe

| exe | 对应功能 | 大小 |
| --- | --- | --- |
| `dist_exe/NL4KW_Win.exe` | Windows 普通版 | 10.42 MB |
| `dist_exe/NL4KW_Win_auto.exe` | Windows 自动账号轮转版 | 9.87 MB |
| `dist_exe/NL4KW_Win_Emulator.exe` | Windows 手动模拟版 | 13.38 MB |

### NL4KW_Win.exe

普通版适合单用户、单账号场景。

首次运行时，如果 exe 同目录不存在 `config.ini`，程序会自动创建配置模板并退出。填写后再次运行即可登录。

`config.ini` 示例：

```ini
[LOGIN]
username = 你的账号
password = 你的密码
operator = 中国联通
```

`operator` 可选值：

| 名称 | 说明 |
| --- | --- |
| `校园网` | 不追加运营商后缀 |
| `中国移动` | 追加 `@cmcc` |
| `中国联通` | 追加 `@unicom` |
| `中国电信` | 追加 `@telecom` |

### NL4KW_Win_auto.exe

自动账号轮转版适合多账号备用登录场景。

首次运行时，如果 exe 同目录不存在 `config_auto.ini`，程序会自动创建两个账号位模板并退出。填写后再次运行，程序会随机打乱有效账号顺序并逐个尝试登录。

`config_auto.ini` 示例：

```ini
[ACCOUNT_1]
username = 示例账号1
password = 示例密码1
operator = 中国联通

[ACCOUNT_2]
username = 示例账号2
password = 示例密码2
operator = 中国移动
```

如果某个账号位的账号或密码为空，或仍保持 `示例账号1`、`示例密码1`、`示例账号2`、`示例密码2` 这类默认示例值，程序不会把它计入可用账号。需要更多账号时，可以继续添加 `[ACCOUNT_3]`、`[ACCOUNT_4]`。

### NL4KW_Win_Emulator.exe

手动模拟版适合直接发包不可用、需要模拟网页登录页面的场景。

首次运行会进入坐标标定流程，按提示点击账号框、密码框、运营商选项和登录按钮后按 `Alt` 记录坐标。配置会保存到 exe 同目录的 `login_config.json`。

页面布局、浏览器缩放、显示器分辨率变化后，原坐标可能失效。删除 `login_config.json` 后再次运行即可重新标定。

## Linux/OpenWrt 端

编辑 `NL4KW_Linux.sh` 顶部的账号配置：

```sh
USERNAME="YOUR_USERNAME"
PASSWORD="YOUR_PASSWORD"
OPERATOR_NAME="中国联通"
```

运行：

```sh
sh NL4KW_Linux.sh
```

脚本会自动判断到认证服务器时使用的本机 IPv4 地址，并用同一套认证参数直接发包。

## 打包说明

三个 Windows exe 使用 PyInstaller `onefile + console` 打包。为了控制体积，打包时排除了 `numpy`、`pandas`、`matplotlib`、`scipy`、`PyQt/PySide` 等无关模块；模拟版额外排除了 `cv2`，避免被 `pyautogui` 的可选截图链路拉大体积。

当前构建环境：

| 项目 | 值 |
| --- | --- |
| Python | `E:\Python312\python.exe` |
| PyInstaller | `6.16.0` |
| 系统 | Windows 11 64-bit |

## 注意事项

请只在你有权限使用的校园网环境中运行本项目。

Windows 安全软件可能会对 PyInstaller onefile 程序、键盘监听或鼠标模拟能力给出提示。普通版和自动轮转版不需要键鼠模拟；手动模拟版会使用 `pyautogui` 和 `keyboard` 完成点击与按键检测。

Release 发布时建议同时上传三个 exe，并把 `RELEASE.md` 中的 SHA256 校验值放入发布说明，便于下载后核对文件完整性。
