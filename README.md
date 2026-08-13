# 投资组合监控看板（云端版）

多端可访问的投资组合监控看板。基金净值与金价**每日自动抓取**，估值指标每月手动更新，每月 1 号通过**微信**提醒查看。

## 功能

| 数据 | 来源 | 更新方式 |
|---|---|---|
| 基金最新净值（5 只） | 东方财富 | ✅ 每日自动（GitHub Actions） |
| COMEX 黄金价 | 新浪 | ✅ 每日自动 |
| PB 分位 / 股息率 / 国债收益率 / 黄金占比 / 技术指标 | 你手动填 | ✍️ 每月手动（localStorage 持久化） |

- 三 tab：黄金 / 债基 / 红利低波，规则与信号自动计算
- 手动值保存在浏览器 localStorage，换设备可用「导出/导入手动值」迁移
- 每月 1 号微信推送提醒（Server酱）

## 本地预览

```bash
cd investment-dashboard-cloud
python3 -m http.server 8000
# 浏览器打开 http://localhost:8000/
```

> 直接双击 index.html 会因浏览器安全策略无法读取 data/auto.json，请用本地服务器或部署后的网址打开。

## 部署到 GitHub Pages（约 10 分钟）

### 1. 建仓库并推送

在 GitHub 新建一个**公开**仓库（如 `invest-dashboard`），把本目录内容推上去：

```bash
cd investment-dashboard-cloud
git init
git add .
git commit -m "init: 投资看板云端版"
git remote add origin https://github.com/<你的用户名>/invest-dashboard.git
git branch -M main
git push -u origin main
```

### 2. 开启 Pages（GitHub Actions 模式）

仓库 → **Settings → Pages → Build and deployment → Source** 选 **GitHub Actions**。

### 3. 开启 Actions

仓库 → **Actions** 标签，若显示 "workflows are disabled" 点 **Enable**。
首次可手动跑一次：Actions → 选 `更新投资看板数据并部署` → **Run workflow**，验证部署成功。

### 4. 配置微信推送（Server酱）

1. 打开 https://sct.ftqq.com/ 用微信扫码登录，拿到 **SendKey**（新版，36 位）或旧版 **SCKEY**。
2. 仓库 → **Settings → Secrets and variables → Actions → New repository secret**
3. Name 填 `SCKEY`，Value 填你的 Key，保存。

> 工作流会自动识别新旧 Key：长度 >30 用新接口（sctapi.ftqq.com），否则用旧接口（sc.ftqq.com）。

### 5. 访问

部署完成后，看板地址：`https://<用户名>.github.io/invest-dashboard/`

## 定时说明

| 时间（北京时间） | 动作 |
|---|---|
| 每日 23:30 | 抓取净值/金价 → 部署 Pages |
| 每月 1 日 09:00 | 抓取 + 部署 + 微信推送提醒 |

可在 `.github/workflows/update.yml` 的 `schedule` 调整。手动点 Actions 的 **Run workflow** 可随时强制刷新。

## 迭代看板规则

规则与阈值都在 `index.html` 的 JS 里（`calcGold` / `calcBond` / `calcDividend`）。改完 `git push` 即生效，无需改工作流。

## 数据接口说明

- 基金净值：`https://api.fund.eastmoney.com/f10/lsjz`（东方财富，需 Referer）
- 黄金：`https://hq.sinajs.cn/list=hf_GC`（新浪，需 Referer）
- 新浪对部分债基（`fu_` 代码）返回空，故统一用东方财富拿全部基金净值。

## 注意事项

- 本看板仅作参考，不构成投资建议。
- 自动抓取依赖第三方公开接口，若失效需维护 `scripts/fetch_data.py`。
- 手动值存在浏览器本地，清缓存会丢失，重要时请用导出按钮备份。
