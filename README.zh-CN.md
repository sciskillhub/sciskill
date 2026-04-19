# sciskill

English version: [README.md](README.md)

`sciskill` 是 `sciskillhub` 下的一个独立仓库，用于收集公开 GitHub 仓库中符合要求的 `SKILL.md`。当前仓库只保存收录元数据；实时同步下来的仓库内容放在仓库外的 `../data/open-source` 中，同时输出结构化报告和一个 Markdown 索引文档。

核心收集脚本是 [`scripts/collect_skills.py`](/data20T/dev/agenticbioinfo/sciskillhub/sciskill/scripts/collect_skills.py)，自动化流程定义在 [`.github/workflows/collect-skills.yml`](/data20T/dev/agenticbioinfo/sciskillhub/sciskill/.github/workflows/collect-skills.yml)。

### 仓库结构

- [`scripts/collect_skills.py`](/data20T/dev/agenticbioinfo/sciskillhub/sciskill/scripts/collect_skills.py)：发现并校验技能仓库的收集脚本
- [`config/domain_topics.txt`](/data20T/dev/agenticbioinfo/sciskillhub/sciskill/config/domain_topics.txt)：领域 topic，例如 `clinical-research`
- [`config/qualifier_topics.txt`](/data20T/dev/agenticbioinfo/sciskillhub/sciskill/config/qualifier_topics.txt)：skill / agent 限制 topic，例如 `ai-agents`
- [`open-source-skills.md`](/data20T/dev/agenticbioinfo/sciskillhub/sciskill/open-source-skills.md)：已收录 GitHub 仓库的 Markdown 索引
- [`skill_report.json`](/data20T/dev/agenticbioinfo/sciskillhub/sciskill/skill_report.json)：最近一次收集结果报告
- [`requirements.txt`](/data20T/dev/agenticbioinfo/sciskillhub/sciskill/requirements.txt)：Python 依赖
- [`community/`](/data20T/dev/agenticbioinfo/sciskillhub/sciskill/community)：预留目录，目前未使用
- `../data/open-source/`：实时同步仓库内容的外部缓存目录

### 收集器做什么

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

### 环境要求

- `python3`
- `git`
- 可用于 GitHub API 的 token
- 可选使用 [`scripts/sync_skill_repos.py`](/data20T/dev/agenticbioinfo/sciskillhub/sciskill/scripts/sync_skill_repos.py) 同步外部缓存

### 自动化

GitHub Actions 工作流 [`.github/workflows/collect-skills.yml`](/data20T/dev/agenticbioinfo/sciskillhub/sciskill/.github/workflows/collect-skills.yml)：

- 支持手动触发
- 每天 `07:10 UTC` 定时运行
- 使用 `secrets.SKILL_COLLECTOR_TOKEN`
- 自动更新 `skill_report.json`、`skill-manifest.json` 和 `open-source-skills.md`

### 维护说明

- 收集器现在使用双 topic AND 语义：
  - 从 [`config/domain_topics.txt`](/data20T/dev/agenticbioinfo/sciskillhub/sciskill/config/domain_topics.txt) 里取一个领域 topic
  - 从 [`config/qualifier_topics.txt`](/data20T/dev/agenticbioinfo/sciskillhub/sciskill/config/qualifier_topics.txt) 里取一个 skill / agent 限制 topic
- 实际查询会按 `M × N` 笛卡尔积生成，例如：
  - `archived:false is:public topic:clinical-research topic:ai-agents`
- 两个配置文件都采用“每行一个 topic”；空行和 `#` 注释会被忽略
- 已存在于 [`skill-manifest.json`](/data20T/dev/agenticbioinfo/sciskillhub/sciskill/skill-manifest.json) 的仓库会被跳过
- [`skill_report.json`](/data20T/dev/agenticbioinfo/sciskillhub/sciskill/skill_report.json) 保存汇总信息和逐仓库状态
- 实时仓库内容应同步到 `../data/open-source`，不再提交到本仓库
