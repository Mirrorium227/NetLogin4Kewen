#!/bin/sh

# NL4KWTC 校园网登录系统 - Linux/OpenWrt 教师网端
#
# 教师网逻辑来自 KWXY/10.110.6.251.har：
# 1. 状态检查：/drcom/chkstatus
# 2. 登录接口：:801/eportal/?c=Portal&a=login
# 3. 注销接口：:801/eportal/?c=Portal&a=logout
#
# 教师网没有运营商选项，user_account 固定为 ",0,账号"。
#
# 使用方式：
# - 登录：sh NL4KWTC_Linux.sh
# - 注销：sh NL4KWTC_Linux.sh logout

BASE_URL="http://10.110.6.251"
APP_NAME="NL4KWTC 校园网登录系统"
APP_EDITION="Linux/OpenWrt 教师网端"

# ======== 在此处写死教师网账号与密码 ========
USERNAME="YOUR_USERNAME"
PASSWORD="YOUR_PASSWORD"
# ==========================================

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

get_local_ip() {
  # 获取访问认证服务器时使用的本机 IPv4 地址。
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
  V=$(( ( $(date +%s) * 1000 ) % 10000 ))
  RESP=$(http_get "${BASE_URL}/drcom/chkstatus?callback=dr1002&v=${V}" 2>/dev/null || true)
  echo "$RESP" | grep -q '"result"[[:space:]]*:[[:space:]]*1'
}

login() {
  IP_ADDR="$1"
  if [ -z "$USERNAME" ] || [ -z "$PASSWORD" ] || [ "$USERNAME" = "YOUR_USERNAME" ] || [ "$PASSWORD" = "YOUR_PASSWORD" ]; then
    echo "[错误] 请先在脚本顶部填写教师网账号和密码"
    return 1
  fi

  echo "[系统] 正在构建教师网认证数据包..."

  # 教师网没有运营商后缀，HAR 中 user_account 等价于 %2C0%2C账号。
  USER_ACCOUNT="%2C0%2C${USERNAME}"
  V=$(( ( $(date +%s) * 1000 ) % 10000 ))

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

  echo "[系统] 正在发送教师网认证请求..."
  RESP=$(http_get "$LOGIN_URL" 2>/dev/null || true)
  echo "[调试] 响应预览: $(printf '%s' "$RESP" | head -c 200)"

  echo "$RESP" | grep -q 'dr1003({"result":"1"' && return 0
  echo "$RESP" | grep -q '"result":"1"' && return 0
  return 1
}

logout() {
  IP_ADDR="$1"
  V=$(( ( $(date +%s) * 1000 ) % 10000 ))

  LOGOUT_URL="${BASE_URL}:801/eportal/?c=Portal&a=logout&callback=dr1004&login_method=1\
&user_account=drcom\
&user_password=123\
&ac_logout=0\
&register_mode=0\
&wlan_user_ip=${IP_ADDR}\
&wlan_user_ipv6=\
&wlan_vlan_id=0\
&wlan_user_mac=000000000000\
&wlan_ac_ip=\
&wlan_ac_name=\
&jsVersion=3.3.2\
&v=${V}"

  echo "[系统] 正在发送教师网注销请求..."
  RESP=$(http_get "$LOGOUT_URL" 2>/dev/null || true)
  echo "[调试] 响应预览: $(printf '%s' "$RESP" | head -c 200)"

  echo "$RESP" | grep -q 'dr1004({"result":"1"' && return 0
  echo "$RESP" | grep -q '"result":"1"' && return 0
  return 1
}

print_banner

IP_ADDR=$(get_local_ip)
echo "[信息] 本机IP：$IP_ADDR"

if [ "$1" = "logout" ]; then
  if logout "$IP_ADDR"; then
    echo "[成功] 注销成功"
    exit 0
  fi
  echo "[失败] 注销未通过"
  exit 1
fi

if check_status; then
  echo "[信息] 已经处于登录状态"
  exit 0
fi

if login "$IP_ADDR"; then
  MASKED_USERNAME=$(mask_username "$USERNAME")
  echo "[成功] 网络认证成功"
  echo "[信息] 用户名: $MASKED_USERNAME"
  exit 0
fi

echo "[失败] 认证未通过，请检查账号/密码或网络连通性"
exit 1
