#!/usr/bin/env bash
set -euo pipefail

OPENWRT_DIR="${1:-$(pwd)}"
HONK_CORE_BIN="${2:-}"

if [ ! -d "$OPENWRT_DIR" ]; then
  echo "ERROR: OPENWRT_DIR does not exist: $OPENWRT_DIR" >&2
  exit 1
fi

cd "$OPENWRT_DIR"

echo ">>> Updating upstream feeds..."
./scripts/feeds update -a

echo ">>> Cleaning conflicting feed packages and custom directory..."
rm -rf \
  feeds/luci/themes/luci-theme-vantage \
  feeds/luci/applications/luci-app-vantage \
  feeds/luci/applications/luci-app-vantage-aps \
  feeds/luci/applications/luci-app-vantage-traffic \
  feeds/luci/applications/luci-app-openclash \
  feeds/luci/applications/luci-app-honk \
  feeds/packages/net/honk \
  feeds/luci/applications/luci-app-fm350 \
  feeds/luci/applications/luci-app-bandix \
  feeds/packages/net/bandix \
  feeds/packages/net/openwrt-bandix \
  feeds/luci/applications/luci-app-lucky \
  feeds/packages/net/lucky \
  package/custom

mkdir -p package/custom

echo ">>> Cloning anothaDev/luci-theme-vantage..."
git clone --depth=1 -b main https://github.com/anothaDev/luci-theme-vantage.git package/custom/luci-theme-vantage

echo ">>> Cloning QiuSimons/luci-app-honk..."
git clone --depth=1 https://github.com/QiuSimons/luci-app-honk.git package/custom/luci-app-honk
if [ -n "$HONK_CORE_BIN" ]; then
  if [ ! -f "$HONK_CORE_BIN" ]; then
    echo "ERROR: HONK_CORE_BIN provided but not found: $HONK_CORE_BIN" >&2
    exit 1
  fi
  mkdir -p package/custom/luci-app-honk/honk/files
  cp -f "$HONK_CORE_BIN" package/custom/luci-app-honk/honk/files/honk-core.bin
  chmod +x package/custom/luci-app-honk/honk/files/honk-core.bin
  rm -f package/custom/luci-app-honk/honk/files/honk-core.bin.stamp
  echo ">>> Prebuilt honk-core.bin staged into package/custom/luci-app-honk/honk/files/"
fi

echo ">>> Cloning vernesong/OpenClash (dev branch)..."
OPENCLASH_TMP="$(mktemp -d)"
trap 'rm -rf "$OPENCLASH_TMP"' EXIT
git clone --depth=1 -b dev https://github.com/vernesong/OpenClash.git "$OPENCLASH_TMP"
cp -a "$OPENCLASH_TMP/luci-app-openclash" package/custom/luci-app-openclash

echo ">>> Cloning Bandix, Lucky, and FM350..."
git clone --depth=1 -b main https://github.com/timsaya/openwrt-bandix.git package/custom/openwrt-bandix
git clone --depth=1 -b main https://github.com/timsaya/luci-app-bandix.git package/custom/luci-app-bandix
git clone --depth=1 -b main https://github.com/gdy666/luci-app-lucky.git package/custom/luci-app-lucky
git clone --depth=1 -b main https://github.com/LianXia233/luci-app-fm350.git package/custom/luci-app-fm350
rm -rf package/custom/luci-app-fm350/f22-atproxy

echo ">>> Installing feeds..."
./scripts/feeds install -a

echo ">>> Feeds and custom packages prepared successfully."
