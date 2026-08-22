# Skills — 投资看板配套技能

本目录存放投资看板（`index.html`）配套的 AI 工作技能。每个 skill 是纯文本文档，可被任意能联网+看图的 AI 模型读取使用。

## bond-diagnose — 债基体检截图识别

从债基截图（天天基金/季报）识别穿透字段（信用等级/久期/占比/规模/杠杆/前五大重仓），输出 `bonds.json` 供看板自动加载。

**文件**：
- [`bond-diagnose/SKILL.md`](bond-diagnose/SKILL.md) — 主流程指令
- [`bond-diagnose/references/fields.md`](bond-diagnose/references/fields.md) — 字段清单与判读规则

## 如何使用（换模型时）

把下面的 raw 链接发给任意 AI 模型，让它读完后识别你的债基截图：

```
https://raw.githubusercontent.com/WayneYannn/invest-dashboard/main/skill/bond-diagnose/SKILL.md
```

提示词示例：
> 读这个文档：https://raw.githubusercontent.com/WayneYannn/invest-dashboard/main/skill/bond-diagnose/SKILL.md
> 然后按它的流程，识别我这张债基截图，输出 bonds.json。

**要求**：模型需支持联网读 URL + 多模态看图（Claude/GPT-4/Gemini 等均可）。

## 在 SmartWork 内使用

若用 SmartWork，本 skill 已安装到 `$CODEX_HOME/skills/bond-diagnose/`，直接说"体检债基"即自动触发，无需手动给链接。
