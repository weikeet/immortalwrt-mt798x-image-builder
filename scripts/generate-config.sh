#!/usr/bin/env bash
set -euo pipefail

if [ $# -lt 1 ]; then
  echo "Usage: $0 <device> [openwrt_dir] [repo_dir]" >&2
  exit 1
fi

DEVICE="$1"
OPENWRT_DIR="${2:-$(pwd)}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="${3:-$(cd "$SCRIPT_DIR/.." && pwd)}"

case "$DEVICE" in
  cudy-tr3000-112m)
    BASE_DEFCONFIG="defconfig/mt7981-ax3000.config"
    USE_FULL=0
    ;;
  rax3000m-emmc)
    BASE_DEFCONFIG="defconfig/mt7981-ax3000.config"
    USE_FULL=1
    ;;
  netcore-n60-pro-512m)
    BASE_DEFCONFIG="defconfig/mt7986-ax6000.config"
    USE_FULL=1
    ;;
  clx-s20p)
    BASE_DEFCONFIG="defconfig/mt7986-ax6000.config"
    USE_FULL=1
    ;;
  *)
    echo "ERROR: unsupported device '$DEVICE'" >&2
    exit 1
    ;;
esac

DEVICE_CFG="$REPO_DIR/configs/devices/${DEVICE}.config"
COMMON_CFG="$REPO_DIR/configs/common.config"
FULL_CFG="$REPO_DIR/configs/full-features.config"

for f in "$OPENWRT_DIR/$BASE_DEFCONFIG" "$COMMON_CFG" "$DEVICE_CFG"; do
  [ -f "$f" ] || { echo "ERROR: missing config file: $f" >&2; exit 1; }
done
if [ "$USE_FULL" -eq 1 ] && [ ! -f "$FULL_CFG" ]; then
  echo "ERROR: missing full-features config: $FULL_CFG" >&2
  exit 1
fi

cd "$OPENWRT_DIR"

echo ">>> Staging files overlay..."
if [ -d "$REPO_DIR/files" ]; then
  mkdir -p files
  cp -a "$REPO_DIR/files/." files/
fi

echo ">>> Merging configuration layers for $DEVICE..."
grep -Ev \
  '^(# )?CONFIG_(TARGET_MULTI_PROFILE|TARGET_PER_DEVICE_ROOTFS|TARGET_DEVICE_|TARGET_BOARD|TARGET_SUBTARGET|TARGET_PROFILE|TARGET_ROOTFS_INITRAMFS|PACKAGE_luci-theme-argon|PACKAGE_luci-theme-bootstrap|PACKAGE_luci-app-eqos-mtk|PACKAGE_luci-i18n-|PACKAGE_nano|PACKAGE_tcpdump|PACKAGE_htop)' \
  "$BASE_DEFCONFIG" > .config

printf '\n' >> .config
cat "$COMMON_CFG" >> .config

if [ "$USE_FULL" -eq 1 ]; then
  printf '\n' >> .config
  cat "$FULL_CFG" >> .config
fi

printf '\n' >> .config
cat "$DEVICE_CFG" >> .config

echo ">>> Running initial make defconfig..."
make defconfig

echo ">>> Pruning LuCI zh-cn translations with whitelist..."
sed -i '/^CONFIG_LUCI_LANG_zh_Hans=/d; /^# CONFIG_LUCI_LANG_zh_Hans is not set$/d' .config
echo '# CONFIG_LUCI_LANG_zh_Hans is not set' >> .config

sed -i -E 's/^(CONFIG_PACKAGE_luci-i18n-[a-zA-Z0-9_-]+-zh-cn)=(y|m)/# \1 is not set/' .config

KEEP_I18N_REQUIRED="base firewall package-manager ttyd upnp mtwifi-cfg turboacc-mtk honk vantage-theme"
if [ "$USE_FULL" -eq 1 ]; then
  KEEP_I18N_REQUIRED="$KEEP_I18N_REQUIRED tailscale-community bandix lucky"
fi
KEEP_I18N_OPTIONAL="vantage vantage-aps vantage-traffic"

for name in $KEEP_I18N_REQUIRED; do
  sym="CONFIG_PACKAGE_luci-i18n-${name}-zh-cn"
  if ! grep -qE "^(# )?${sym}( is not set|=)" .config; then
    echo "ERROR: required i18n symbol not found in .config: $sym" >&2
    exit 1
  fi
  sed -i -E "s|^# ${sym} is not set$|${sym}=y|" .config
  grep -qE "^${sym}=y$" .config || echo "${sym}=y" >> .config
done

for name in $KEEP_I18N_OPTIONAL; do
  sym="CONFIG_PACKAGE_luci-i18n-${name}-zh-cn"
  if grep -qE "^(# )?${sym}( is not set|=)" .config; then
    sed -i -E "s|^# ${sym} is not set$|${sym}=y|" .config
    grep -qE "^${sym}=y$" .config || echo "${sym}=y" >> .config
  fi
done

echo ">>> Re-running make defconfig to settle dependencies..."
make defconfig

KEEP_ALL="$KEEP_I18N_REQUIRED $KEEP_I18N_OPTIONAL"
KEEP_RE="$(echo "$KEEP_ALL" | tr ' ' '|')"
BAD_I18N="$(grep -E '^CONFIG_PACKAGE_luci-i18n-[a-zA-Z0-9_-]+-zh-cn=(y|m)' .config \
  | grep -vE "luci-i18n-(${KEEP_RE})-zh-cn=" || true)"
if [ -n "$BAD_I18N" ]; then
  echo "ERROR: non-whitelisted zh-cn translations enabled:" >&2
  echo "$BAD_I18N" >&2
  exit 1
fi

echo ">>> Verifying critical config assertions..."
require_enabled() {
  local sym="$1"
  if ! grep -qx "${sym}=y" .config; then
    echo "ERROR: expected ${sym}=y in .config" >&2
    exit 1
  fi
}

require_disabled() {
  local sym="$1"
  if grep -qE "^${sym}=(y|m)$" .config; then
    echo "ERROR: expected ${sym} to be disabled, but found enabled in .config" >&2
    exit 1
  fi
}

# 通用关键开关
require_enabled CONFIG_USE_APK
require_enabled CONFIG_KERNEL_DEBUG_INFO_BTF
require_enabled CONFIG_PACKAGE_honk
require_enabled CONFIG_PACKAGE_luci-app-honk
require_enabled CONFIG_PACKAGE_luci-theme-vantage
require_enabled CONFIG_PACKAGE_luci-app-ttyd
require_enabled CONFIG_PACKAGE_luci-app-upnp
require_enabled CONFIG_PACKAGE_luci-app-mtwifi-cfg
require_enabled CONFIG_PACKAGE_luci-app-turboacc-mtk
require_enabled CONFIG_PACKAGE_kmod-mt_wifi

# 明确禁用项
require_disabled CONFIG_CCACHE
require_disabled CONFIG_RUBY_ENABLE_YJIT
require_disabled CONFIG_PACKAGE_luci-theme-argon
require_disabled CONFIG_PACKAGE_luci-theme-bootstrap
require_disabled CONFIG_PACKAGE_dockerd
require_disabled CONFIG_PACKAGE_luci-app-dockerman
require_disabled CONFIG_PACKAGE_luci-app-samba4
require_disabled CONFIG_PACKAGE_luci-app-ksmbd

if [ "$USE_FULL" -eq 1 ]; then
  require_enabled CONFIG_PACKAGE_luci-app-openclash
  require_enabled CONFIG_LUCI_APP_OPENCLASH_INCLUDE_CORE
  require_enabled CONFIG_PACKAGE_luci-app-tailscale-community
  require_enabled CONFIG_PACKAGE_luci-app-bandix
  require_enabled CONFIG_PACKAGE_luci-app-lucky
  require_disabled CONFIG_PACKAGE_luci-app-fm350
else
  require_disabled CONFIG_PACKAGE_luci-app-openclash
  require_enabled CONFIG_PACKAGE_luci-app-fm350
  require_enabled CONFIG_PACKAGE_kmod-usb-serial-option
  require_enabled CONFIG_PACKAGE_kmod-usb-net-rndis
  require_enabled CONFIG_PACKAGE_kmod-usb-net-qmi-wwan
  require_enabled CONFIG_PACKAGE_luci-proto-qmi
fi

if [ "$DEVICE" = "netcore-n60-pro-512m" ]; then
  require_enabled CONFIG_PACKAGE_u-boot-mt7986_netcore_n60-pro
  require_enabled CONFIG_PACKAGE_trusted-firmware-a-mt7986-spim-nand-ddr4
fi

echo ">>> Configuration for $DEVICE generated and verified successfully."
