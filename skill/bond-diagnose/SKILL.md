---
name: bond-diagnose
description: 从债基截图（天天基金/季报）识别穿透字段，输出 bonds.json 供投资看板自动加载。用户说"体检债基""债基截图""穿透数据""生成bonds.json""更新债基持仓""季报截图"时使用。也用于读取用户粘贴的基金详情页文字、识别信用等级/久期/占比/规模/杠杆/前五大重仓。
---

# 债基体检截图识别

> 本文档可被任意 AI 模型读取使用。如果你是 AI 助手，用户发来债基截图并让你"按这个文档识别"——请读完全文后，按步骤识别截图字段并输出 bonds.json。

## 核心流程

用户发来债基截图（或粘贴基金详情页文字）→ 识别穿透字段 → 输出 `bonds.json` 片段。

## 步骤

1. **读取截图/文字**：确认基金代码（6位）、名称、以下字段
2. **字段识别**：按 `references/fields.md` 的字段清单与判读规则识别每个字段
   - 若通过 GitHub raw 链接访问，读取：`https://raw.githubusercontent.com/WayneYannn/invest-dashboard/main/skill/bond-diagnose/references/fields.md`
3. **缺失字段处理**：截图里没有的字段标 `null`，不要臆造；明确告知用户哪些字段缺失
4. **信用等级/久期判读**：若截图没直接给，按重仓券性质推断（国债国开为主→rate；企业债中票为主且评级高→mid），并说明推断依据
5. **输出 JSON**：生成完整 bonds.json 结构（含合并逻辑）
6. **给用户操作指引**：告诉用户把文件放到看板的 `data/bonds.json`，push 后看板自动加载

## 字段识别要点

完整字段清单、截图定位、判读规则见 `references/fields.md`（同目录）。识别前先读该文件。

关键字段优先级（必须有）：
- 基金代码、名称（定位用）
- duration（久期类型）— 看板判断核心
- credit（信用等级）— 看板判断核心
- rate_ratio / credit_ratio（利率债/信用债占比）— 定量穿透

可选字段（有就填，没有标 null）：
- aa_plus_ratio、scale、leverage、top5、report_date

## 输出格式

输出合法 JSON，结构见 `references/fields.md` 末尾示例。输出后附一段说明：
- 识别出的字段清单
- 缺失字段（标 null 的）
- 判读依据（尤其 credit/duration 若是推断的）
- 放置路径：看板工程 `data/bonds.json`（本仓库 `data/bonds.json`）

## 多只基金合并

用户一次发多只基金截图时，合并到同一个 bonds.json 的 `bonds` 对象里，每个基金一个键（代码）。

## 诚实点

- 截图不清晰或字段缺失时，明确说"无法识别"，不要猜数字
- 信用等级若靠推断（非截图直接显示评级分布），标注"依据重仓券性质推断"
- 季报日期用用户提供的为准；若截图无法判断季度，标 `null` 并提示用户补填

## 看板集成说明（给模型上下文）

输出的 `bonds.json` 会被投资看板（本仓库 `index.html`）的 `loadBonds()` 函数读取：
- 文件路径：`data/bonds.json`
- 加载时机：页面打开时自动 fetch
- 失败降级：文件不存在则静默降级到手填模式，不报错
- 体检卡逻辑：识别出的 AA+占比/规模/杠杆等定量字段，会直接增强体检卡的"可买/谨慎/不可买"判断
