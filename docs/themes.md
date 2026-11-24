# LuCI 候选主题与默认主题说明

本文档记录项目调研并筛选出的几款适用于 **OpenWrt 25.12（ucode LuCI / APK）** 的现代 LuCI 主题。当前固件已将默认主题由 Argon 切换为 **`luci-theme-vantage`**。

---

## 一、候选主题一览

| 主题名称 | GitHub 仓库 | OpenWrt 包名 | 开源协议 | `mediaurlbase` 路径 | 兼容范围 | 核心风格与特点 |
| --- | --- | --- | --- | --- | --- | --- |
| **Vantage** *(当前默认)* | [anothaDev/luci-theme-vantage](https://github.com/anothaDev/luci-theme-vantage) | `luci-theme-vantage` | GPL-3.0-or-later | `/luci-static/vantage` | 25.12 (`apk`) / 24.10 (`opkg`) | 控制台风格主题：左侧图标栏 + 弹出子菜单、面包屑、页面标签页、`Ctrl+K` 命令面板、深/浅色模式，不依赖外部字体或 CDN |
| **7Dollar** | [itsmaiGe/luci-theme-7dollar](https://github.com/itsmaiGe/luci-theme-7dollar) | `luci-theme-7dollar` | Apache-2.0 | `/luci-static/7dollar` | 23.05 / 24.10 / 25.12 (ucode LuCI) | 轻量卡片式设计（约 53 KB），按使用场景重组菜单、5 套配色（含深/浅色）、`⌘K` / `Ctrl+K` 搜索、可选首页应用卡片（OpenClash 等） |
| **Mono** | [wizcheu/luci-theme-mono](https://github.com/wizcheu/luci-theme-mono) | `luci-theme-mono` | Apache-2.0 | `/luci-static/mono` | ucode LuCI（源码/SDK 构建 `apk` 或脚本构建 `ipk`） | 参考 shadcn/ui neutral dashboard 的黑白极简主题，白底浅灰侧栏、细边框、可收起侧栏、菜单搜索（`⌘K` / `Ctrl+K`）与移动端抽屉导航 |
| **Aeris** | [wizcheu/luci-theme-aeris](https://github.com/wizcheu/luci-theme-aeris) | `luci-theme-aeris` | Apache-2.0 | `/luci-static/aeris` | 24.10 (`ipk`) / 25.12 (`apk`)，ucode LuCI | 参考 Ecme 设计规范的响应式主题，支持浅/深色切换、可收起侧栏、菜单搜索、移动端导航及只读 RPC 网络概览 |

---

## 二、各主题详细信息

### 1. Vantage（当前固件默认）

- **仓库地址**：https://github.com/anothaDev/luci-theme-vantage
- **默认分支**：`main`
- **包构成**（仓库根目录包含多个 OpenWrt 软件包，可单独或组合使用）：
  - `luci-theme-vantage`：主题本体（CSS、图标、登录页、壳层交互及 `/etc/config/vantage_theme` 外观配置）；简体中文语言包为 `luci-i18n-vantage-theme-zh-cn`。
  - `luci-app-vantage` *(可选)*：Vantage 实时仪表盘（`admin/dashboard`），包含 6 项健康检查、实时网络拓扑路径、客户端详情、吞吐量图表、网口与交换机端口统计、防火墙概览等；支持 MTK `mtwifi` 无线配置读取（无 `/etc/config/wireless` 密钥泄露）；简体中文语言包为 `luci-i18n-vantage-zh-cn`。
  - `luci-app-vantage-aps` *(可选)*：通过 SSH 配对在路由器仪表盘汇总展示其他 OpenWrt AP 的 SSID 与客户端（中文包 `luci-i18n-vantage-aps-zh-cn`）。
  - `luci-app-vantage-traffic` *(可选/实验性)*：基于内核 `nf_conntrack` 统计同一端口下设备的独立流量（中文包 `luci-i18n-vantage-traffic-zh-cn`）。
- **构建与运行要求**：
  - 主题本体仅依赖 `luci-base`；已设置 `LUCI_MINIFY_CSS:=0`（保留现代 CSS 特性如 `:has()`、`color-mix()`、container queries）。
  - 浏览器建议 Chrome / Edge 117+、Firefox 121+、Safari 16.2+。

### 2. 7Dollar

- **仓库地址**：https://github.com/itsmaiGe/luci-theme-7dollar
- **默认分支**：`main`
- **包结构**：仓库根目录即 `luci-theme-7dollar` 单个 OpenWrt 包，依赖 `luci-base`。
- **特性摘要**：
  - 面向日常管理优化：将菜单重新组织为「总览 / 设备 / Wi-Fi / 上网 / 安全 / 应用 / 系统」，并将 MAC/BSSID 等进阶信息折叠到「详情」中。
  - 提供陶土、青瓷、雾蓝、暮紫、石墨 5 套配色，支持浅色/深色/跟随系统。
  - 内置中文、英文、俄语界面，无外部字体与远程请求。
  - `Makefile` 已设置 `LUCI_MINIFY_CSS:=0` 与 `LUCI_MINIFY_JS:=0`，可直接放入 OpenWrt 源码树的 `package/custom/` 编译。

### 3. Mono

- **仓库地址**：https://github.com/wizcheu/luci-theme-mono
- **默认分支**：`main`
- **包结构**：仓库根目录即 `luci-theme-mono` 单个 OpenWrt 包，依赖 `luci-base` 与 `rpcd-mod-luci`。
- **特性摘要**：
  - 黑白极简高对比度界面（shadcn/ui Neutral 风格），保留 LuCI 原生页面、ACL 菜单、保存/应用与提交回滚逻辑。
  - 支持本地浅/深色切换、侧栏收起、`⌘K` / `Ctrl+K` 菜单搜索和移动端抽屉导航。
  - 仓库自带脚本主要生成 `ipk`；用于 25.12 `apk` 固件时需将其加入 OpenWrt 源码树或 SDK 中编译。

### 4. Aeris

- **仓库地址**：https://github.com/wizcheu/luci-theme-aeris
- **默认分支**：`main`
- **包结构**：仓库根目录即 `luci-theme-aeris` 单个 OpenWrt 包，依赖 `luci-base` 与 `rpcd-mod-luci`。
- **特性摘要**：
  - 参考 Ecme 风格设计的响应式主题，支持浅/深色模式、可收起侧栏、菜单搜索和移动端导航。
  - 自带只读 RPC 网络概览（展示 WAN 流量、内存、接口、设备信息与 IPv4 DHCP 租约），不修改路由器底层网络设置。
  - `Makefile` 已设置 `LUCI_MINIFY_JS:=0` 与 `LUCI_MINIFY_CSS:=0`，安装包安装时仅注册 `luci.themes.Aeris`，不会强行覆盖现有主题。

---

## 三、本仓库默认主题集成方式

当前固件已通过以下位置将默认主题配置为 **`luci-theme-vantage`**：

1. [scripts/prepare-feeds.sh](../scripts/prepare-feeds.sh)：清理可能冲突的 feed 目录后，将 `anothaDev/luci-theme-vantage` 克隆到 `package/custom/luci-theme-vantage`。
2. [scripts/patch-source.py](../scripts/patch-source.py)：在 `patch_default_theme()` 中将 `feeds/luci/collections/luci-light/Makefile` 的默认依赖从 `+luci-theme-bootstrap` 替换为 `+luci-theme-vantage`，避免 `luci` 强制拉回 `luci-theme-bootstrap`。
3. [configs/common.config](../configs/common.config)：启用 `CONFIG_PACKAGE_luci-theme-vantage=y`，并显式禁用 `luci-theme-argon`、`luci-theme-bootstrap`、`luci-theme-bootstrap-mod`。
4. [scripts/generate-config.sh](../scripts/generate-config.sh)：剥离上游 defconfig 自带的 `luci-theme-argon` / `luci-theme-bootstrap`，在中文语言包白名单中强制保留 `vantage-theme`（即 `luci-i18n-vantage-theme-zh-cn`），并将 `vantage`、`vantage-aps`、`vantage-traffic` 列入可选保留项，最后校验主题启用与禁用断言。
5. [files/etc/uci-defaults/99-meekuwrt-defaults](../files/etc/uci-defaults/99-meekuwrt-defaults)：首次开机脚本强制设置 `luci.main.lang='zh_cn'` 与 `luci.main.mediaurlbase='/luci-static/vantage'`。

> **扩展提示**：如需同时把 Vantage 实时仪表盘也打进固件，只需在 [configs/common.config](../configs/common.config) 追加 `CONFIG_PACKAGE_luci-app-vantage=y`（对应的中文包 `luci-i18n-vantage-zh-cn` 已被 `generate-config.sh` 自动纳入可选保留白名单）。

### 如需切换到其他候选主题

1. 将 [scripts/prepare-feeds.sh](../scripts/prepare-feeds.sh) 中克隆的仓库替换为目标主题仓库。
2. 同步修改 [scripts/patch-source.py](../scripts/patch-source.py)、[configs/common.config](../configs/common.config)、[scripts/generate-config.sh](../scripts/generate-config.sh) 中的包名（`luci-theme-7dollar` / `luci-theme-mono` / `luci-theme-aeris`）及中文包白名单（如使用无独立语言包的主题可移除对应项）。
3. 更新 [files/etc/uci-defaults/99-meekuwrt-defaults](../files/etc/uci-defaults/99-meekuwrt-defaults) 中的 `luci.main.mediaurlbase` 为上表对应的路径。
