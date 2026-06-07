# NL4KW 校园网登录系统 v2026.06

本次发布包含学生网和教师网 Windows 可执行文件，以及 Linux/OpenWrt 脚本。学生网版本使用 `NL4KW` 前缀，教师网版本使用 `NL4KWTC` 前缀。

## Release 附件

建议将以下文件作为 Release 附件上传：

| 文件 | 说明 | 大小 | SHA256 |
| --- | --- | ---: | --- |
| `NL4KW_Win.exe` | 学生网 Windows 普通版 | 10.42 MB | `FD9B811D1052B6740DE84A5FF5E7E62ABB61E5CA94D350BFFEC4783C8EA3FAF5` |
| `NL4KW_Win_auto.exe` | 学生网 Windows 自动账号轮转版 | 9.87 MB | `11F887AB4B7451200A409CCB93FEE603B307B3A509E67AB331A5F5DFEE50ABBF` |
| `NL4KW_Win_Emulator.exe` | 学生网 Windows 手动模拟版 | 13.38 MB | `BD6E08ADE24C543490ED330FFB242CCFE74EBA4B2C4B467A84974AD709BF0A4F` |
| `NL4KWTC_Win.exe` | 教师网 Windows 普通版 | 9.86 MB | `EB888A693532A03CB37C4D271096CE9A0B4C3F58CBBC5C4341C940ECD0291351` |
| `NL4KWTC_Win_auto.exe` | 教师网 Windows 自动账号轮转版 | 9.86 MB | `77CEC898129A3EF5EA0949743B832FAB1D7868BF11D7B46613D46876F98AE27A` |
| `NL4KWTC_Win_Emulator.exe` | 教师网 Windows 手动模拟版 | 13.38 MB | `6306709C000C2E576362F690BA6304BAB91D28268809BDD08F1557F50C79F189` |

Linux/OpenWrt 端随源码提供：`NL4KW_Linux.sh`、`NL4KWTC_Linux.sh`。

## 版本选择

| 场景 | 推荐文件 |
| --- | --- |
| 学生网，Windows 单账号直接发包 | `NL4KW_Win.exe` |
| 学生网，Windows 多账号轮转 | `NL4KW_Win_auto.exe` |
| 学生网，Windows 模拟网页登录 | `NL4KW_Win_Emulator.exe` |
| 学生网，Linux/OpenWrt | `NL4KW_Linux.sh` |
| 教师网，Windows 单账号直接发包 | `NL4KWTC_Win.exe` |
| 教师网，Windows 多账号轮转 | `NL4KWTC_Win_auto.exe` |
| 教师网，Windows 模拟网页登录 | `NL4KWTC_Win_Emulator.exe` |
| 教师网，Linux/OpenWrt | `NL4KWTC_Linux.sh` |

## 使用提示

学生网版本需要填写运营商配置。可选值为 `校园网`、`中国移动`、`中国联通`、`中国电信`。

教师网版本没有运营商选项，只需要账号和密码。

普通版首次运行会创建单账号配置文件。自动账号轮转版首次运行会创建两个账号位，空账号位和默认示例账号位不会被计入可用账号。

手动模拟版首次运行需要标定网页中的输入框和登录按钮位置。浏览器缩放、窗口位置、显示器分辨率或网页布局变化后，删除对应配置文件即可重新标定。

教师网直接发包版本支持注销参数：

```powershell
python .\NL4KWTC_Win.py logout
python .\NL4KWTC_Win_auto.py logout
```

```sh
sh NL4KWTC_Linux.sh logout
```

## 校验方法

Windows PowerShell：

```powershell
Get-FileHash -Algorithm SHA256 .\NL4KW_Win.exe
Get-FileHash -Algorithm SHA256 .\NL4KW_Win_auto.exe
Get-FileHash -Algorithm SHA256 .\NL4KW_Win_Emulator.exe
Get-FileHash -Algorithm SHA256 .\NL4KWTC_Win.exe
Get-FileHash -Algorithm SHA256 .\NL4KWTC_Win_auto.exe
Get-FileHash -Algorithm SHA256 .\NL4KWTC_Win_Emulator.exe
```

输出的 SHA256 应与上方表格一致。

## 本次更新

- 新增教师网适配，文件统一使用 `NL4KWTC` 前缀。
- 新增教师网 Windows exe：普通版、自动账号轮转版、手动模拟版。
- 教师网直接发包版本支持登录和注销。
- 学生网自动账号轮转版改为外置配置文件，不再把账号密码写入 exe。
- README 已调整为公开仓库视角，移除本地路径和本地抓包文件信息。

## 注意事项

请只在你有权限使用的校园网环境中运行本工具。

Windows 安全软件可能会对 PyInstaller 打包程序、键盘监听或鼠标模拟行为给出提示。普通版和自动账号轮转版不使用键鼠模拟；手动模拟版需要使用鼠标点击和按键检测完成网页登录流程。

自动账号轮转版会随机尝试配置中的有效账号。请确保账号来源、使用方式和学校网络管理要求一致。
