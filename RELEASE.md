# NL4KW 校园网登录系统 v2026.05.12

本次发布包含三个 Windows 端可执行文件，分别对应普通版、自动账号轮转版和手动模拟版。Linux/OpenWrt 端仍以 `NL4KW_Linux.sh` 脚本形式提供。

## 发布文件

| 文件 | 版本 | 大小 | SHA256 |
| --- | --- | ---: | --- |
| `NL4KW_Win.exe` | Windows 普通版 | 10.42 MB | `FD9B811D1052B6740DE84A5FF5E7E62ABB61E5CA94D350BFFEC4783C8EA3FAF5` |
| `NL4KW_Win_auto.exe` | Windows 自动账号轮转版 | 9.87 MB | `11F887AB4B7451200A409CCB93FEE603B307B3A509E67AB331A5F5DFEE50ABBF` |
| `NL4KW_Win_Emulator.exe` | Windows 手动模拟版 | 13.38 MB | `BD6E08ADE24C543490ED330FFB242CCFE74EBA4B2C4B467A84974AD709BF0A4F` |

## 版本选择

| 场景 | 推荐文件 |
| --- | --- |
| 单账号、常规校园网认证 | `NL4KW_Win.exe` |
| 多账号备用、失败后自动换号 | `NL4KW_Win_auto.exe` |
| 只能通过网页登录页面完成认证 | `NL4KW_Win_Emulator.exe` |
| OpenWrt 或 Linux 环境 | 使用源码包内的 `NL4KW_Linux.sh` |

## 使用说明

### Windows 普通版

运行 `NL4KW_Win.exe`。首次运行会在 exe 同目录生成 `config.ini` 模板，填写账号、密码和运营商后再次运行。

运营商可选值：

| 值 | 含义 |
| --- | --- |
| `校园网` | 不追加运营商后缀 |
| `中国移动` | 使用 `@cmcc` |
| `中国联通` | 使用 `@unicom` |
| `中国电信` | 使用 `@telecom` |

### Windows 自动账号轮转版

运行 `NL4KW_Win_auto.exe`。首次运行会在 exe 同目录生成 `config_auto.ini`，文件内自带两个账号位：

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

填写账号、密码和运营商后再次运行。程序会检查是否已登录；未登录时按随机顺序尝试有效账号。

如果某个账号位的账号或密码为空，或仍保持默认示例账号/密码，程序不会把它视为可用账号。需要更多账号时，可以继续添加 `[ACCOUNT_3]`、`[ACCOUNT_4]`。

### Windows 手动模拟版

运行 `NL4KW_Win_Emulator.exe`。首次运行需要按提示标定账号框、密码框、运营商选项和登录按钮位置，配置会保存到 exe 同目录的 `login_config.json`。

如果浏览器缩放、窗口位置、显示器分辨率或网页布局变化导致点击位置不准，删除 `login_config.json` 后重新标定。

## 本次整理内容

- 统一三个 Windows 端和 Linux 端的系统名称、文件头说明、注释风格和控制台输出格式。
- 为三个 Windows 脚本封装 onefile exe，保留控制台窗口便于查看认证日志。
- 控制 exe 体积，排除常见大型无关模块；手动模拟版已排除 `cv2/numpy` 可选链路。
- 修正手动模拟版 exe 下 `login_config.json` 的保存位置，使配置稳定保存在 exe 同目录。
- 自动账号轮转版改为读取同目录 `config_auto.ini`，不再把账号密码硬编码进 exe。
- 保留 `spec/` 目录，便于后续复现 PyInstaller 打包。

## 校验方法

Windows PowerShell：

```powershell
Get-FileHash -Algorithm SHA256 .\NL4KW_Win.exe
Get-FileHash -Algorithm SHA256 .\NL4KW_Win_auto.exe
Get-FileHash -Algorithm SHA256 .\NL4KW_Win_Emulator.exe
```

输出的 SHA256 应与上方表格一致。

## 注意事项

请只在你有权限使用的校园网环境中运行本工具。

由于 exe 使用 PyInstaller 打包，部分安全软件可能提示未知程序或键鼠自动化行为。普通版和自动账号轮转版不使用键鼠模拟；手动模拟版需要使用鼠标点击和键盘监听来完成网页登录流程。
