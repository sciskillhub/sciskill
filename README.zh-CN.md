# sciskill

English version: [README.md](README.md)

`sciskill` 是 `sciskillhub` 下的一个独立仓库，用于收集公开 GitHub 仓库中符合要求的 `SKILL.md`。当前仓库保存收录元数据以及已收录 GitHub 仓库的 Markdown 索引。

### 仓库结构

- [`open-source-skills.md`](/data20T/dev/agenticbioinfo/sciskillhub/sciskill/open-source-skills.md)：已收录 GitHub 仓库的 Markdown 索引
- [`community/`](/data20T/dev/agenticbioinfo/sciskillhub/sciskill/community)：预留目录，目前未使用

### 这个仓库记录什么

- 基于基础查询以及“领域 topic × 限制 topic”的组合搜索 GitHub 仓库
- 扫描候选仓库中的 `SKILL.md`
- 校验其中的 YAML front matter
- 将新命中的仓库写入 `skill-manifest.json`
- 重建 `open-source-skills.md`
- 生成结构化 JSON 报告

当前校验规则要求：

- `SKILL.md` 包含可解析的 YAML front matter
- `name` 非空，且匹配 `[a-z0-9-]+`
- `description` 非空，且长度不少于 10 个字符

### 自动化

GitHub Actions 工作流 [`.github/workflows/collect-skills.yml`](/data20T/dev/agenticbioinfo/sciskillhub/sciskill/.github/workflows/collect-skills.yml)：

- 支持手动触发
- 每天 `07:10 UTC` 定时运行
- 使用 `secrets.SKILL_COLLECTOR_TOKEN`
- 自动更新 `skill-manifest.json` 和 `open-source-skills.md`

### 维护说明

- 收集器现在使用双 topic AND 语义：一个领域 topic 加一个 skill / agent 限制 topic
- 实际查询会按 `M × N` 笛卡尔积生成，例如：
  - `archived:false is:public topic:clinical-research topic:ai-agents`
- 已存在于 [`skill-manifest.json`](/data20T/dev/agenticbioinfo/sciskillhub/sciskill/skill-manifest.json) 的仓库会被跳过
- 这个仓库的定位是记录已收录的 GitHub 仓库及其元数据
