#!/usr/bin/env python3
"""Apply idempotent MeekuWrt source patches to ImmortalWrt MT798x tree."""

from __future__ import annotations

import argparse
import re
import shutil
from pathlib import Path


N60_PRO_512M_IMAGE_DEF = """
define Device/netcore_n60-pro-512m
  DEVICE_VENDOR := Netcore
  DEVICE_MODEL := N60 Pro
  DEVICE_VARIANT := 512M
  DEVICE_DTS := mt7986a-netcore-n60-pro-512m
  DEVICE_DTS_DIR := ../dts-ext
  SUPPORTED_DEVICES += netcore,n60-pro
  UBINIZE_OPTS := -E 5
  BLOCKSIZE := 128k
  PAGESIZE := 2048
  KERNEL_IN_UBI := 1
  UBOOTENV_IN_UBI := 1
  IMAGES := sysupgrade.itb
  KERNEL_INITRAMFS_SUFFIX := -recovery.itb
  KERNEL := kernel-bin | gzip
  KERNEL_INITRAMFS := kernel-bin | lzma | \\
\tfit lzma $$(KDIR)/image-$$(firstword $$(DEVICE_DTS)).dtb with-initrd | pad-to 64k
  IMAGE/sysupgrade.itb := append-kernel | \\
\tfit gzip $$(KDIR)/image-$$(firstword $$(DEVICE_DTS)).dtb external-static-with-rootfs | append-metadata
  DEVICE_PACKAGES := kmod-usb3 automount kmod-usb-ledtrig-usbport
  ARTIFACTS := preloader.bin bl31-uboot.fip
  ARTIFACT/preloader.bin := mt7986-bl2 spim-nand-ddr4
  ARTIFACT/bl31-uboot.fip := mt7986-bl31-uboot netcore_n60-pro
endef
TARGET_DEVICES += netcore_n60-pro-512m
"""


def require_file(path: Path) -> str:
    if not path.is_file():
        raise SystemExit(f"ERROR: expected file not found: {path}")
    return path.read_text(encoding="utf-8")


def insert_after_board_case(path: Path, existing_board: str, new_board: str, min_matches: int) -> None:
    text = require_file(path)
    if new_board in text:
        return
    pattern = re.compile(rf"^([ \t]*){re.escape(existing_board)}\|\\$", re.MULTILINE)
    matches = list(pattern.finditer(text))
    if len(matches) < min_matches:
        raise SystemExit(
            f"ERROR: expected at least {min_matches} '{existing_board}|\\' match(es) in {path}, found {len(matches)}"
        )
    updated = pattern.sub(rf"\1{existing_board}|\\\n\1{new_board}|\\", text)
    path.write_text(updated, encoding="utf-8")


def patch_n60_pro_512m(openwrt: Path, repo: Path) -> None:
    src_dts = repo / "dts" / "mt7986a-netcore-n60-pro-512m.dts"
    if not src_dts.is_file():
        raise SystemExit(f"ERROR: source DTS missing: {src_dts}")
    dst_dts = openwrt / "target/linux/mediatek/dts-ext/mt7986a-netcore-n60-pro-512m.dts"
    dst_dts.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src_dts, dst_dts)

    filogic_ext = openwrt / "target/linux/mediatek/image/filogic-ext.mk"
    mk_text = require_file(filogic_ext)
    if "define Device/netcore_n60-pro-512m" not in mk_text:
        if not mk_text.endswith("\n"):
            mk_text += "\n"
        filogic_ext.write_text(mk_text + N60_PRO_512M_IMAGE_DEF, encoding="utf-8")

    insert_after_board_case(
        openwrt / "target/linux/mediatek/filogic/base-files/etc/board.d/02_network",
        "netcore,n60-pro",
        "netcore,n60-pro-512m",
        min_matches=1,
    )
    insert_after_board_case(
        openwrt / "target/linux/mediatek/filogic/base-files/lib/upgrade/platform.sh",
        "netcore,n60-pro",
        "netcore,n60-pro-512m",
        min_matches=2,
    )
    insert_after_board_case(
        openwrt / "target/linux/mediatek/filogic/base-files/etc/board.d/01_leds",
        "netcore,n60-pro",
        "netcore,n60-pro-512m",
        min_matches=1,
    )

    fix_mac = openwrt / "target/linux/mediatek/filogic/base-files/etc/hotplug.d/net/09-fix-mtwifi-mac"
    if fix_mac.is_file():
        fix_text = fix_mac.read_text(encoding="utf-8")
        if "netcore,n60-pro|\\" in fix_text and "netcore,n60-pro-512m" not in fix_text:
            insert_after_board_case(fix_mac, "netcore,n60-pro", "netcore,n60-pro-512m", min_matches=1)

    uboot_mk = openwrt / "package/boot/uboot-mediatek/Makefile"
    uboot_text = require_file(uboot_mk)
    old_build_dev = "  BUILD_DEVICES:=netcore_n60-pro\n"
    new_build_dev = "  BUILD_DEVICES:=netcore_n60-pro netcore_n60-pro-512m\n"
    if new_build_dev not in uboot_text:
        if old_build_dev not in uboot_text:
            raise SystemExit(f"ERROR: '{old_build_dev.strip()}' not found in {uboot_mk}")
        uboot_mk.write_text(uboot_text.replace(old_build_dev, new_build_dev, 1), encoding="utf-8")


def patch_clx_s20p(openwrt: Path) -> None:
    filogic_ext = openwrt / "target/linux/mediatek/image/filogic-ext.mk"
    mk_text = require_file(filogic_ext)
    block_re = re.compile(r"(define Device/clx_s20p\n)(.*?)(^endef)", re.MULTILINE | re.DOTALL)
    match = block_re.search(mk_text)
    if not match:
        raise SystemExit(f"ERROR: Device/clx_s20p block not found in {filogic_ext}")
    body = match.group(2)
    if "supergateway,s20p" in body:
        return
    replacement = match.group(1) + body.rstrip("\n") + "\n  SUPPORTED_DEVICES += supergateway,s20p\n" + match.group(3)
    updated = mk_text[: match.start()] + replacement + mk_text[match.end() :]
    filogic_ext.write_text(updated, encoding="utf-8")


def patch_config_generate(openwrt: Path) -> None:
    cfg = openwrt / "package/base-files/files/bin/config_generate"
    text = require_file(cfg)

    target_ip = 'lan) ipad=${ipaddr:-"192.168.6.1"} ;;'
    old_ip = 'lan) ipad=${ipaddr:-"192.168.1.1"} ;;'
    if target_ip not in text:
        if old_ip not in text:
            raise SystemExit(f"ERROR: default LAN IP anchor not found in {cfg}")
        text = text.replace(old_ip, target_ip, 1)

    target_host = "hostname='MeekuWrt'"
    if target_host not in text:
        replaced = False
        for old_host in ("hostname='ImmortalWrt'", "hostname='OpenWrt'"):
            if old_host in text:
                text = text.replace(old_host, target_host)
                replaced = True
        if not replaced:
            raise SystemExit(f"ERROR: default hostname anchor not found in {cfg}")

    cfg.write_text(text, encoding="utf-8")


def patch_wifi_defaults(openwrt: Path) -> None:
    mtwifi_uc = openwrt / "package/mtk/applications/mtwifi-cfg-ucode/files/lib/wifi/mtwifi.uc"
    uc_text = require_file(mtwifi_uc)

    if '"encryption": "none"' not in uc_text and "'encryption': 'none'" not in uc_text:
        raise SystemExit(f"ERROR: expected unencrypted default in {mtwifi_uc}")

    replacements = [
        ('ssid: "ImmortalWrt-2.4G"', 'ssid: "MeekuWrt"'),
        ('ssid: "ImmortalWrt-5G"', 'ssid: "MeekuWrt-5G"'),
        ('ssid: "ImmortalWrt-6G"', 'ssid: "MeekuWrt-6G"'),
    ]
    for old, new in replacements:
        if new not in uc_text:
            if old not in uc_text:
                raise SystemExit(f"ERROR: WiFi SSID anchor '{old}' not found in {mtwifi_uc}")
            uc_text = uc_text.replace(old, new)
    mtwifi_uc.write_text(uc_text, encoding="utf-8")

    profile_root = openwrt / "package/mtk/drivers/wifi-profile/files"
    if not profile_root.is_dir():
        raise SystemExit(f"ERROR: wifi-profile directory missing: {profile_root}")

    dat_files = sorted(
        list(profile_root.glob("mt7981/*.dat")) + list(profile_root.glob("mt7986*/*.dat"))
    )
    updated_b0 = 0
    updated_b1 = 0
    for dat in dat_files:
        name = dat.name
        if name.endswith(".b0.dat"):
            ssid = "MeekuWrt"
            updated_b0 += 1
        elif name.endswith(".b1.dat"):
            ssid = "MeekuWrt-5G"
            updated_b1 += 1
        else:
            continue

        content = dat.read_text(encoding="utf-8")
        content, ssid_subs = re.subn(r"^([ \t]*)SSID1=.*$", rf"\1SSID1={ssid}", content, flags=re.MULTILINE)
        if ssid_subs == 0:
            raise SystemExit(f"ERROR: SSID1= not found in {dat}")
        content, auth_subs = re.subn(r"^([ \t]*)AuthMode=.*$", r"\1AuthMode=OPEN", content, flags=re.MULTILINE)
        content, enc_subs = re.subn(r"^([ \t]*)EncrypType=.*$", r"\1EncrypType=NONE", content, flags=re.MULTILINE)
        if auth_subs == 0 or enc_subs == 0:
            raise SystemExit(f"ERROR: AuthMode/EncrypType not found in {dat}")
        dat.write_text(content, encoding="utf-8")

    if updated_b0 < 2 or updated_b1 < 2:
        raise SystemExit(
            f"ERROR: expected >=2 b0 and >=2 b1 dat files updated, got b0={updated_b0}, b1={updated_b1}"
        )


def patch_default_theme(openwrt: Path) -> None:
    luci_light = openwrt / "feeds/luci/collections/luci-light/Makefile"
    text = require_file(luci_light)
    if "+luci-theme-vantage" not in text:
        if "+luci-theme-bootstrap" not in text:
            raise SystemExit(f"ERROR: +luci-theme-bootstrap not found in {luci_light}")
        text = text.replace("+luci-theme-bootstrap", "+luci-theme-vantage")
        text = text.replace("default Bootstrap theme", "Vantage theme")
        luci_light.write_text(text, encoding="utf-8")


def patch_ruby_yjit(openwrt: Path) -> None:
    ruby_mk = openwrt / "feeds/packages/lang/ruby/Makefile"
    text = require_file(ruby_mk)
    block_re = re.compile(
        r"(config RUBY_ENABLE_YJIT\b.*?)(^\s*(?:help|endef|endif)\b)",
        re.MULTILINE | re.DOTALL,
    )
    match = block_re.search(text)
    if not match:
        raise SystemExit(f"ERROR: config RUBY_ENABLE_YJIT block not found in {ruby_mk}")
    block = match.group(1)
    patched_block = re.sub(r"^([ \t]*)default[ \t]+y\b.*$", r"\1default n", block, flags=re.MULTILINE)
    if re.search(r"^[ \t]*default[ \t]+y\b", patched_block, flags=re.MULTILINE):
        raise SystemExit(f"ERROR: failed to disable default y in RUBY_ENABLE_YJIT block of {ruby_mk}")
    updated = text[: match.start(1)] + patched_block + text[match.end(1) :]
    ruby_mk.write_text(updated, encoding="utf-8")


def patch_build_hardening(openwrt: Path) -> None:
    xcrypt_mk = openwrt / "feeds/packages/libs/libxcrypt/Makefile"
    if xcrypt_mk.is_file():
        text = xcrypt_mk.read_text(encoding="utf-8")
        if "--disable-werror" not in text:
            text = re.sub(
                r"(CONFIGURE_ARGS[ \t]*\+=[ \t]*)",
                r"\1--disable-werror ",
                text,
            )
        if "-fcommon" not in text:
            text = re.sub(
                r"(TARGET_CFLAGS[ \t]*\+=[ \t]*)",
                r"\1-fcommon ",
                text,
            )
        xcrypt_mk.write_text(text, encoding="utf-8")

    rust_mk = openwrt / "feeds/packages/lang/rust/Makefile"
    if rust_mk.is_file():
        text = rust_mk.read_text(encoding="utf-8")
        if "download-ci-llvm=true" in text:
            rust_mk.write_text(
                text.replace("download-ci-llvm=true", "download-ci-llvm=false"),
                encoding="utf-8",
            )


def patch_openclash_core_makefile(openwrt: Path) -> None:
    """Fix double-expanded $$CORE_ARCH in OpenClash Build/Compile recipe."""
    oc_mk = openwrt / "package/custom/luci-app-openclash/Makefile"
    if not oc_mk.is_file():
        return
    text = oc_mk.read_text(encoding="utf-8")
    # Build/Compile is evaluated twice inside OpenWrt's Build/DefaultTargets,
    # so $$CORE_ARCH turns into ORE_ARCH unless escaped as $$$$CORE_ARCH.
    updated = re.sub(r"(?<!\$)\$\$CORE_ARCH", "$$$$CORE_ARCH", text)
    if updated != text:
        oc_mk.write_text(updated, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Apply MeekuWrt source patches.")
    parser.add_argument("--openwrt-dir", required=True, type=Path, help="Path to OpenWrt source tree")
    parser.add_argument("--repo-dir", required=True, type=Path, help="Path to MeekuWrt builder repository")
    args = parser.parse_args()

    openwrt = args.openwrt_dir.resolve()
    repo = args.repo_dir.resolve()

    patch_n60_pro_512m(openwrt, repo)
    patch_clx_s20p(openwrt)
    patch_config_generate(openwrt)
    patch_wifi_defaults(openwrt)
    patch_default_theme(openwrt)
    patch_ruby_yjit(openwrt)
    patch_build_hardening(openwrt)
    patch_openclash_core_makefile(openwrt)

    print("All MeekuWrt source patches applied successfully.")


if __name__ == "__main__":
    main()
