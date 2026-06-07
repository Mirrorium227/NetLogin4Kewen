# NL4KW 校园网登录系统

NL4KW 是一套用于校园网认证的多端脚本集合，覆盖学生网和教师网两类认证场景。

学生网版本使用 `NL4KW` 前缀，支持运营商选项；教师网版本使用 `NL4KWTC` 前缀，教师网登录不需要运营商选项。

## 版本选择

| 使用场景 | 推荐文件 |
| --- | --- |
| Windows 学生网，单账号直接发包登录 | `NL4KW_Win.py` 或 `dist_exe/NL4KW_Win.exe` |
| Windows 学生网，多账号自动轮转 | `NL4KW_Win_auto.py` 或 `dist_exe/NL4KW_Win_auto.exe` |
| Windows 学生网，模拟网页登录 | `NL4KW_Win_Emulator.py` 或 `dist_exe/NL4KW_Win_Emulator.exe` |
| Linux/OpenWrt 学生网 | `NL4KW_Linux.sh` |
| Windows 教师网，单账号直接发包登录 | `NL4KWTC_Win.py` |
| Windows 教师网，多账号自动轮转 | `NL4KWTC_Win_auto.py` |
| Windows 教师网，模拟网页登录 | `NL4KWTC_Win_Emulator.py` |
| Linux/OpenWrt 教师网 | `NL4KWTC_Linux.sh` |

## 文件结构

| 路径 | 说明 |
| --- | --- |
| `dist_exe/` | Windows 可执行文件，适合直接下载运行。 |
| `spec/` | PyInstaller 打包配置，便于复现构建。 |
| `NL4KW_Win.py` | 学生网 Windows 普通版。 |
| `NL4KW_Win_auto.py` | 学生网 Windows 自动账号轮转版。 |
| `NL4KW_Win_Emulator.py` | 学生网 Windows 手动模拟版。 |
| `NL4KW_Linux.sh` | 学生网 Linux/OpenWrt 版。 |
| `NL4KWTC_Win.py` | 教师网 Windows 普通版。 |
| `NL4KWTC_Win_auto.py` | 教师网 Windows 自动账号轮转版。 |
| `NL4KWTC_Win_Emulator.py` | 教师网 Windows 手动模拟版。 |
| `NL4KWTC_Linux.sh` | 教师网 Linux/OpenWrt 版。 |
| `RELEASE.md` | Release 发布说明模板。 |

## 学生网与教师网

学生网登录时需要选择运营商，脚本会根据配置为账号追加对应后缀。

| 配置值 | 账号后缀 |
| --- | --- |
| `校园网` | 不追加后缀 |
| `中国移动` | `@cmcc` |
| `中国联通` | `@unicom` |
| `中国电信` | `@telecom` |

教师网没有运营商选项，登录时只提交账号和密码，不追加运营商后缀。

## Windows 可执行文件

`dist_exe/` 中提供学生网 Windows 端 exe：

| 文件 | 说明 |
| --- | --- |
| `NL4KW_Win.exe` | 学生网普通版，单账号配置。 |
| `NL4KW_Win_auto.exe` | 学生网自动账号轮转版，多账号配置。 |
| `NL4KW_Win_Emulator.exe` | 学生网手动模拟版，适合只能通过网页登录的情况。 |

教师网 Windows 端目前提供源码脚本，可直接用 Python 运行；需要 exe 时可按 `spec/` 中的现有打包方式扩展生成。

## 配置说明

### 学生网普通版

运行 `NL4KW_Win.py` 或 `NL4KW_Win.exe`。首次运行会生成 `config.ini`，填写后再次运行。

```ini
[LOGIN]
username = 你的账号
password = 你的密码
operator = 中国联通
```

### 学生网自动账号轮转版

运行 `NL4KW_Win_auto.py` 或 `NL4KW_Win_auto.exe`。首次运行会生成 `config_auto.ini`，默认自带两个账号位。

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

账号或密码为空，或仍保持默认示例值时，该账号位不会被计入可用账号。需要更多账号时，可继续添加 `[ACCOUNT_3]`、`[ACCOUNT_4]`。

### 学生网手动模拟版

运行 `NL4KW_Win_Emulator.py` 或 `NL4KW_Win_Emulator.exe`。首次运行会进入坐标标定流程，按提示记录账号框、密码框、运营商选项和登录按钮位置。

坐标配置保存在 `login_config.json`。如果浏览器缩放、窗口位置、显示器分辨率或网页布局发生变化，删除该文件后重新标定。

### 教师网普通版

运行 `NL4KWTC_Win.py`。首次运行会生成 `config_tc.ini`，填写后再次运行。

```ini
[LOGIN]
username = 你的教师网账号
password = 你的教师网密码
```

### 教师网自动账号轮转版

运行 `NL4KWTC_Win_auto.py`。首次运行会生成 `config_tc_auto.ini`，默认自带两个账号位。

```ini
[ACCOUNT_1]
username = 示例账号1
password = 示例密码1

[ACCOUNT_2]
username = 示例账号2
password = 示例密码2
```

教师网自动轮转版同样会跳过空账号位和默认示例账号位。

### 教师网手动模拟版

运行 `NL4KWTC_Win_Emulator.py`。首次运行会标定账号框、密码框和登录按钮位置。

教师网页面没有运营商选项，因此不需要标定运营商选择位置。坐标配置保存在 `login_config_tc.json`。

## Linux/OpenWrt

学生网：

```sh
sh NL4KW_Linux.sh
```

教师网：

```sh
sh NL4KWTC_Linux.sh
```

Linux/OpenWrt 脚本需要先编辑脚本顶部的账号配置。学生网脚本还需要填写运营商；教师网脚本只需要填写账号和密码。

## 注销

教师网直接发包版本支持注销参数：

```powershell
python .\NL4KWTC_Win.py logout
python .\NL4KWTC_Win_auto.py logout
```

```sh
sh NL4KWTC_Linux.sh logout
```

学生网 Linux 端和教师网端的注销逻辑都在对应脚本中保留；Windows 学生网普通版主要面向登录和自动重连。

## 发布

Release 页面正文可参考 `RELEASE.md`。发布时建议上传 `dist_exe/` 中的 exe，并在 Release 说明中附带 SHA256 校验值。

## 注意事项

请只在你有权限使用的校园网环境中运行本项目。

Windows 安全软件可能会对 PyInstaller 打包程序、键盘监听或鼠标模拟行为给出提示。普通版和自动轮转版不需要键鼠模拟；手动模拟版会使用鼠标点击和按键检测来完成网页登录流程。

自动账号轮转版会随机尝试配置中的有效账号。请确保账号来源、使用方式和学校网络管理要求一致。
