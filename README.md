# MeekuWrt — ImmortalWrt 25.12 MT798x 云编译项目

基于 GitHub Actions 的 MediaTek MT798x (Filogic) 路由器 **ImmortalWrt 25.12** 固件自动编译仓库，采用 [chasey-dev/immortalwrt-mt798x-rebase](https://github.com/chasey-dev/immortalwrt-mt798x-rebase) `25.12` 分支（Linux 6.12 + APK 包管理 + MTK 闭源 `mt_wifi` 驱动与 HNAT 硬件加速）。

---

## 一、默认系统信息

| 项目 | 默认值 |
| --- | --- |
| 管理地址 | `192.168.6.1` |
| 主机名 | `MeekuWrt` |
| Root 密码 | 空（直接登录，建议首次登录后自行设置） |
| 默认 WiFi | 2.4G：`MeekuWrt` / 5G：`MeekuWrt-5G`（默认不加密） |
| 默认主题与语言 | Vantage (`luci-theme-vantage`) + 简体中文（按已装插件白名单保留中文包，候选主题与切换说明见 [docs/themes.md](docs/themes.md)） |
| 包管理器 | `apk`（25.12 新包格式，安装未签名本地包使用 `apk add --allow-untrusted <pkg>.apk`） |

---

## 二、支持设备与 U-Boot / 分区布局对照

| 机型代号 | 设备型号 | 硬件规格 | 推荐 U-Boot / 分区方案 | 核心产物文件 |
| --- | --- | --- | --- | --- |
| `cudy-tr3000-112m` | **Cudy TR3000** | MT7981B<br>512MB RAM / 128MB Flash | 三分区 DHCP U-Boot 112M 布局（NMBM） | `*cudy_tr3000-v1-mtkuboot-squashfs-sysupgrade.bin` |
| `rax3000m-emmc` | **CMCC RAX3000M eMMC** | MT7981B<br>512MB RAM / 64GB eMMC | **官方 25.12 统一布局**（`.itb` + `rootfs=512M`） | `*cmcc_rax3000m-squashfs-sysupgrade.itb`<br>`*initramfs-recovery.itb`<br>`*emmc-gpt.bin` / `emmc-preloader.bin` / `emmc-bl31-uboot.fip` |
| `netcore-n60-pro-512m` | **磊科 N60 Pro (硬改)** | MT7986A<br>2GB RAM / 512MB SPI-NAND | **U-Boot2025-WildEdition (移除 NMBM)** + 506.5MB 全量 UBI | `*netcore_n60-pro-512m-squashfs-sysupgrade.itb`<br>`*initramfs-recovery.itb`<br>`*preloader.bin` / `bl31-uboot.fip` |
| `clx-s20p` | **超级路由 CLX-S20P** | MT7986A<br>2GB RAM / 128GB eMMC | eMMC GPT 布局（`rootfs=512M`，兼容 `supergateway,s20p`） | `*clx_s20p-squashfs-sysupgrade.bin`<br>`*clx_s20p-initramfs-kernel.bin` |

### 各机型刷机重点提醒

1. **Cudy TR3000 (`112M`)**
   - 直接使用 `*cudy_tr3000-v1-mtkuboot-squashfs-sysupgrade.bin` 在当前三分区 DHCP 112M U-Boot 或现有 112M 系统下刷写/升级。
   - 内置 [LianXia233/luci-app-fm350](https://github.com/LianXia233/luci-app-fm350) 管理插件（入口：`网络 -> Mobile Network -> FM350-GL`，默认 AT 串口 `/dev/ttyUSB1`，首次开机自动创建 `fm350` / `fm350v6` 接口）。
2. **CMCC RAX3000M eMMC**
   - 如果机内当前是旧版传统 Kwrt/hanwckf eMMC 布局（旧 GPT + `.bin` 固件），**切勿直接跨布局硬刷 `.itb`**。
   - 切换为官方 25.12 统一布局的标准步骤：备份 `factory` 分区 → 在 U-Boot 或已进入的 recovery 环境中依次更新产物里的 `emmc-gpt.bin`、`emmc-preloader.bin`、`emmc-bl31-uboot.fip` → 重启进入新版 U-Boot 刷入 `*initramfs-recovery.itb` → 进系统后升级 `*squashfs-sysupgrade.itb`。**注意不要误刷原厂仓库中的 NAND 固件。**
3. **磊科 N60 Pro 硬改版 (2GB RAM / 512MB Flash)**
   - 参考恩山论坛硬改方案（`thread-8429618` / `thread-8457733`），推荐刷入 `U-Boot2025-WildEdition` 并在 U-Boot 中选择 **“移除 NMBM”** 与最大 UBI 分区（对应本固件 DTS `ubi` = `0x1fa80000`，即 506.5MB 全量 UBI）。
   - 若升级了 4K+256 大页闪存（如凯侠 TC58CVG2S0HRAIG/J），请务必确认烧录到芯片的 **BL2** 为对应的 4K+256 专版（`.itb` FIT-in-UBI 系统镜像本身可同时兼容 2K+128 与 4K+256 颗粒）。
   - 刷机前务必备份原机 `factory` 分区。
4. **超级路由 CLX-S20P**
   - 已在固件中同时声明兼容 `clx,s20p` 与厂商标识 `supergateway,s20p`，可直接兼容升级。

---

## 三、内置软件包矩阵

| 功能类别 | `cudy-tr3000-112m` | `rax3000m-emmc` / `netcore-n60-pro-512m` / `clx-s20p` |
| --- | :---: | :---: |
| **Honk** (`luci-app-honk` + 内核 BTF/eBPF) | ✅ | ✅ |
| **OpenClash** (`luci-app-openclash` 内置 Mihomo 核心) | ❌ | ✅ |
| **MTK WiFi 管理与 HNAT 加速** (`mtwifi-cfg` / `turboacc-mtk`) | ✅ | ✅ |
| **TTYD 网页终端 & UPnP** | ✅ | ✅ |
| **Tailscale** (`luci-app-tailscale-community`) | ❌ | ✅ |
| **Bandix 流量监控** (`luci-app-bandix`) | ❌ | ✅ |
| **Lucky** (`luci-app-lucky`) | ❌ | ✅ |
| **USB 4G/5G 模组驱动与 FM350-GL 管理** (`luci-app-fm350` + `RNDIS`/`QMI`/`NCM`/`MBIM`/`3G`) | ✅ | ❌ |
| **Docker / Samba / KSMBD** | ❌ | ❌ |

### OpenClash 与 Honk 共存提示
- 3 款高容量机型同时预装了 **Honk** 与 **OpenClash**，但运行时**请只启用其中之一**，避免同时劫持 DNS 与流量规则产生冲突。
- 若使用基于 eBPF/TPROXY 的透明代理时遇到加速异常或规则绕过，可在 **网络 → Turbo ACC** 中按需关闭或调整 MTK HNAT 硬件加速模式。

---

## 四、GitHub Actions 云编译说明

1. 进入仓库 **Actions → Build MeekuWrt 25.12 MT798x → Run workflow**。
2. 参数说明：
   - `device`：选择 `all`（并行编译全部 4 台）或指定单台设备。
   - `publish_release`：默认开启，编译成功后按 `<device>-<YYYYMMDD-HHMM>` 标签分别发布 GitHub Release，并自动清理旧 Release，**每台设备仅保留最新 5 个版本**（不会删除工具链缓存 `toolchain-cache`）。
3. 仓库通过 `prepare-honk` 与 `prepare-toolchain` 两个前置任务分别缓存 `honk-core` 与 Filogic 交叉编译工具链，多机型并行构建时可直接复用。
