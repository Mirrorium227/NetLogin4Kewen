#!/bin/sh

# NL4KW 校园网登录系统 - Linux 端
#
# 用途：
# 1. 在脚本内维护单个账号 / 密码 / 运营商组合。
# 2. 自动获取到认证服务器时使用的本机 IPv4 地址。
# 3. 通过校园网认证接口直接发包登录。
#
# 适用环境：Linux / OpenWrt，依赖 curl、wget 或 uclient-fetch 之一，以及 ip/awk/grep。
# 使用方式：编辑下方 USERNAME/PASSWORD/OPERATOR_NAME 后执行：sh NL4KW_Linux.sh

BASE_URL="http://10.110.6.251"
APP_NAME="NL4KW 校园网登录系统"
APP_EDITION="Linux 端"

# ======== 在此处写死账号、密码与运营商 ========
# OPERATOR_NAME 可选值：校园网 / 中国移动 / 中国联通 / 中国电信
USERNAME="YOUR_USERNAME"
PASSWORD="YOUR_PASSWORD"
OPERATOR_NAME="中国联通"
# ============================================

print_banner() {
  echo "========================================================"
  echo "[系统] $APP_NAME"
  echo "[系统] 当前版本：$APP_EDITION"
  echo "========================================================"
}

mask_username() {
  NAME="$1"
  LEN=$(printf '%s\n' "$NAME" | awk '{print length; exit}')
  if [ "$LEN" -le 4 ]; then
    printf '%s' "$NAME" | sed 's/./*/g'
    return
  fi

  PREFIX=$(printf '%s' "$NAME" | cut -c 1-2)
  SUFFIX=$(printf '%s' "$NAME" | sed 's/^.*\(..\)$/\1/')
  STARS=$(awk "BEGIN{for(i=0;i<${LEN}-4;i++) printf \"*\"}")
  printf '%s%s%s' "$PREFIX" "$STARS" "$SUFFIX"
}

# 将运营商名称映射为 user_account 里的后缀（URL 编码后的 @ 符号）
case "$OPERATOR_NAME" in
  "校园网") OP_SUFFIX="" ;;
  "中国移动") OP_SUFFIX="%40cmcc" ;;
  "中国联通") OP_SUFFIX="%40unicom" ;;
  "中国电信") OP_SUFFIX="%40telecom" ;;
  *) echo "[错误] 无效的运营商：$OPERATOR_NAME" >&2; exit 1 ;;
esac

# 选择可用的 HTTP 客户端
http_get() {
  URL="$1"
  if command -v curl >/dev/null 2>&1; then
    curl -sL --connect-timeout 10 -H "User-Agent: Mozilla/5.0" "$URL"
  elif command -v wget >/dev/null 2>&1; then
    wget -q -T 10 -O - --header="User-Agent: Mozilla/5.0" "$URL"
  elif command -v uclient-fetch >/dev/null 2>&1; then
    uclient-fetch -q -T 10 -O - "$URL"
  else
    echo "[错误] 缺少 curl/wget/uclient-fetch，请安装其一" >&2
    return 127
  fi
}

# 带 HTTP 状态码的 GET（优先使用 curl）
http_get_with_status() {
  URL="$1"
  if command -v curl >/dev/null 2>&1; then
    OUT=$(curl -sL --connect-timeout 10 -H "User-Agent: Mozilla/5.0" -w '\nHTTP_CODE:%{http_code}\n' "$URL")
    LAST_HTTP_STATUS=$(printf '%s' "$OUT" | awk -F 'HTTP_CODE:' 'END{print $2+0}')
    printf '%s' "$OUT" | sed '$d'
  elif command -v wget >/dev/null 2>&1; then
    LAST_HTTP_STATUS="NA"
    wget -q -T 10 -O - --header="User-Agent: Mozilla/5.0" "$URL"
  elif command -v uclient-fetch >/dev/null 2>&1; then
    LAST_HTTP_STATUS="NA"
    uclient-fetch -q -T 10 -O - "$URL"
  else
    echo "[错误] 缺少 curl/wget/uclient-fetch，请安装其一" >&2
    return 127
  fi
}

# 获取到认证服务器时将使用的本机 IPv4 地址
get_local_ip() {
  IP_ADDR=$(ip route get 10.110.6.251 2>/dev/null | awk '{for(i=1;i<=NF;i++){if($i=="src"){print $(i+1); exit}}}')
  if [ -z "$IP_ADDR" ]; then
    DEV=$(ip route | awk '/default/ {print $5; exit}')
    if [ -n "$DEV" ]; then
      IP_ADDR=$(ip -4 addr show "$DEV" 2>/dev/null | awk '/inet /{print $2}' | cut -d/ -f1 | head -n1)
    fi
  fi
  [ -z "$IP_ADDR" ] && IP_ADDR="0.0.0.0"
  echo "$IP_ADDR"
}

check_status() {
  # Python 版检查同一个 chkstatus 接口，result=1 表示当前已经认证在线。
  RESP=$(http_get "${BASE_URL}/drcom/chkstatus" 2>/dev/null || true)
  echo "$RESP" | grep -q '"result"[[:space:]]*:[[:space:]]*1'
}

login() {
  IP_ADDR="$1"
  echo "[系统] 正在构建认证数据包..."

  # Python 版里通过 urlencode 编码，此处手工对 ",0," 和 "@" 做等价编码。
  USER_ACCOUNT="%2C0%2C${USERNAME}${OP_SUFFIX}"

  # v 参数取当前毫秒时间的低 4 位（近似，秒*1000 再取模）
  V=$(( ( $(date +%s) * 1000 ) % 10000 ))

  # 与 Windows 普通版保持同一套认证参数，差异只在 Shell 中手工拼接 URL。
  LOGIN_URL="${BASE_URL}:801/eportal/?c=Portal&a=login&callback=dr1003&login_method=1\
&user_account=${USER_ACCOUNT}\
&user_password=${PASSWORD}\
&wlan_user_ip=${IP_ADDR}\
&wlan_user_ipv6=\
&wlan_user_mac=000000000000\
&wlan_ac_ip=\
&wlan_ac_name=\
&jsVersion=3.3.2\
&v=${V}"

  # 打印掩码后的URL，避免明文泄露
  MASKED_URL=$(printf '%s' "$LOGIN_URL" | sed -e 's/\(user_password=\)[^&]*/\1*** /' -e 's/\(user_account=\)[^&]*/\1*** /')
  echo "[调试] 登录URL(掩码): $MASKED_URL"

  echo "[系统] 正在发送认证请求..."
  RESP=$(http_get_with_status "$LOGIN_URL" 2>/dev/null || true)

  # HTTP 状态与响应预览
  echo "[调试] HTTP状态: ${LAST_HTTP_STATUS:-NA}"
  echo "[调试] 响应预览: $(printf '%s' "$RESP" | head -c 200)"

  # 提取 ret_code 与 msg 以便定位问题
  RET_CODE=$(printf '%s' "$RESP" | grep -o 'ret_code"[[:space:]]*:[[:space:]]*[-0-9]*' | grep -o '[-0-9]*' | head -n1)
  MSG=$(printf '%s' "$RESP" | sed -n 's/.*msg":"\([^"]*\)".*/\1/p' | head -n1)

  # 将完整响应写到临时文件，便于进一步分析
  printf '%s' "$RESP" > /tmp/netlogin_last_response.txt 2>/dev/null || true
  echo "[调试] 完整响应保存在: /tmp/netlogin_last_response.txt"

  echo "$RESP" | grep -q 'dr1003({"result":"1"' && return 0
  echo "$RESP" | grep -q 'ret_code":2' && {
    echo "[提示] 您已经登录，无需重复登录"
    return 0
  }

  # 失败时输出更多上下文
  [ -n "$RET_CODE" ] && echo "[调试] ret_code: $RET_CODE"
  [ -n "$MSG" ] && echo "[调试] msg: $MSG"
  return 1
}

print_banner

IP_ADDR=$(get_local_ip)
echo "[信息] 本机IP：$IP_ADDR"

if check_status; then
  echo "[信息] 已经处于登录状态"
  exit 0
fi

if login "$IP_ADDR"; then
  MASKED_USERNAME=$(mask_username "$USERNAME")
  echo "[成功] 网络认证成功"
  echo "[信息] 运营商: $OPERATOR_NAME"
  echo "[信息] 用户名: $MASKED_USERNAME"
  exit 0
else
  echo "[失败] 认证未通过，请检查账号/密码/运营商或网络连通性"
  exit 1
fi
