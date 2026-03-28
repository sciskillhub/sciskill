---
name: sciskillhub
description: 当你遇到实际专业问题时（生命科学/计算科学/数据查询等等专业问题），来这里查询合适的专业 skill。支持按学科、标签和任务类型筛选，并按需组合或切换不同 skill。
metadata:
    skill-author: sciskillhub
    homepage: https://sciskillhub.org
    subjects: General
    tags: skillhub, discovery
---

# sciskillhub — 技能中心

SciSkillHub 是一个科学技能分发平台。当遇到科研、编程、数据分析等问题时，你可以在这里找到专门的技能（Skill）来帮助解决问题。

每个技能都是一套针对特定任务优化的知识库和操作指南，安装后你的 AI 助手就能获得该领域的专业能力。

---

## 解决问题的完整流程

```
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│  问题   │ → │ 确定学科 │ → │ 查询标签 │ → │ 搜索技能 │ → │ 安装技能 │ → │ 使用技能 │
└─────────┘    └─────────┘    └─────────┘    └─────────┘    └─────────┘    └─────────┘
                                                              ↓
                                                    ┌─────────────────┐
                                                    │ 问题未解决？    │
                                                    │ 换其他技能重试  │
                                                    └─────────────────┘
```

---

## 第一步：确定学科（Subject）

根据问题内容，直接在下面选择最合适的学科即可：

| subject | 说明 | 适用场景 |
|---------|------|----------|
| `life-science` | 生命科学相关技能 | 生物信息学、组学分析、医学、药物发现、实验数据分析 |
| `computer-science` | 计算机科学相关技能 | 编程、软件工程、AI、数据结构、系统与工具开发 |
| `general` | 通用技能 | 写作、效率工具、通用数据分析、跨学科任务 |

**选择建议：**

- 生物、医学、测序、组学、蛋白、分子、实验分析问题，优先选 `life-science`
- 代码、框架、工程、部署、调试、算法问题，优先选 `computer-science`
- 不明显属于某个专业学科，或偏通用方法/流程/写作时，选 `general`
- 如果问题明显跨学科，先选最贴近主要任务目标的学科，再用标签和关键词继续缩小范围

---

## 第二步：查询标签（Tag）

```bash
sciskillhub list tag --subject life-science --json
```

```json
[
  {"name": "bioinformatics", "count": 844},
  {"name": "data-analysis", "count": 687},
  {"name": "genomics", "count": 335},
  {"name": "databases", "count": 136},
  {"name": "Python", "count": 129},
  {"name": "drug discovery", "count": 119},
  {"name": "machine-learning", "count": 110},
  {"name": "pipelines", "count": 103},
  {"name": "single cell", "count": 79},
  {"name": "data-formats", "count": 67}
]
```

---

## 第三步：搜索技能（Search）

```bash
# 按学科和标签搜索
sciskillhub list skill --subject life-science --tag "single cell"

# 按关键词搜索
sciskillhub search "single cell"
```

**输出：**

```
Found 10 skills:

1. alterlab-anndata
   open-source/AlterLab-IEU/AlterLab-Academic-Skills/skills/bioinformatics/alterlab-anndata
   Data structure for annotated matrices in single-cell analysis...

2. alterlab-cellxgene
   open-source/AlterLab-IEU/AlterLab-Academic-Skills/skills/bioinformatics/alterlab-cellxgene
   Query the CELLxGENE Census (61M+ cells) programmatically...

3. alterlab-scanpy
   open-source/AlterLab-IEU/AlterLab-Academic-Skills/skills/bioinformatics/alterlab-scanpy
   Standard single-cell RNA-seq analysis pipeline...

ℹ Install with: sciskillhub install <author>/<path>
ℹ Example: sciskillhub install AlterLab-IEU/AlterLab-Academic-Skills/skills/bioinformatics/alterlab-anndata --platform claude
```

**JSON 格式：**

```bash
sciskillhub search "single cell" --json
```

```json
[
  {
    "id": "open-source/AlterLab-IEU/AlterLab-Academic-Skills/skills/bioinformatics/alterlab-anndata",
    "name": "alterlab-anndata",
    "author": "AlterLab-IEU",
    "description": "Data structure for annotated matrices in single-cell analysis. Use when working with .h5ad files...",
    "tags": ["single cell", "data-formats", "Python"],
    "category": "Life Science"
  }
]
```

---

## 第四步：阅读描述，选择技能

**常用技能说明：**

| 技能 | 说明 | 适用场景 |
|------|------|----------|
| **anndata** | .h5ad 数据结构 | 读取、操作 AnnData 对象 |
| **scanpy** | 单细胞分析流程 | QC、聚类、可视化 |
| **scvi-tools** | 深度学习模型 | 批次校正、整合 |
| **scvelo** | RNA 速度 | 轨迹推断 |
| **cellxgene-census** | 大规模数据查询 | 查询已发表的单细胞数据 |

**技能选择策略：**

- 如果一个问题包含多个阶段或子任务，可以选择多个**互补**技能组合使用
- 例如：一个技能负责预处理，另一个负责建模/统计分析，第三个负责可视化或结果解释
- 如果多个技能功能相近，不要一开始全部安装，先选择当前描述最贴合的一个
- 如果第一个技能运行效果不好、覆盖不全，或不适合当前数据/环境，再尝试其他功能相近的技能
- 优先避免安装大量重复能力的技能，先小步验证，再按需要补充

---

## 第五步：安装技能（Install）

```bash
# 安装到 Claude（全局，推荐）
sciskillhub install <skill> --platform claude -y

# 安装到当前项目
sciskillhub install <skill> --platform claude --project -y
```

**输出：**

```
📦 alterlab-scanpy
   open-source/AlterLab-IEU/AlterLab-Academic-Skills/skills/bioinformatics/alterlab-scanpy

- Downloading skill content...
- Extracting skill files...

✓ Installed alterlab-scanpy to Claude Code

  Location: /home/shuang/.claude/skills/alterlab-scanpy
  File:     SKILL.md

╭─ ✓ Installed ─────────────────────────╮
│ The skill is now available globally. │
│ Restart your agent to use it.        │
╰──────────────────────────────────────╯
```

**安装格式支持多种写法：**

```bash
# 只用技能名称（最简单）
sciskillhub install anndata --platform claude -y

# 用作者/路径
sciskillhub install AlterLab-IEU/AlterLab-Academic-Skills/skills/bioinformatics/anndata --platform claude -y

# 完整 slug
sciskillhub install open-source/AlterLab-IEU/AlterLab-Academic-Skills/skills/bioinformatics/anndata --platform claude -y
```

---

## 第六步：使用技能解决问题

安装完成后，直接向 AI 提问：

```
"帮我分析这个 h5ad 文件的结构"
"用 scanpy 对我的单细胞数据做 QC 和聚类"
"用 scvi-tools 进行批次校正"
```

---

## 第七步：问题没解决？换一个技能

```bash
# 1. 搜索其他相关技能
sciskillhub search "trajectory"

# 2. 查看同标签下的其他技能
sciskillhub list skill --subject life-science --tag "其他标签"

# 3. 安装新技能重试
sciskillhub install <新技能> --platform claude -y
```

---

## 常用命令速查

| 命令 | 说明 |
|------|------|
| `sciskillhub list subject` | 列出所有学科 |
| `sciskillhub list tag --subject <学科>` | 列出标签 |
| `sciskillhub list skill --subject <学科> --tag <标签>` | 按标签筛选 |
| `sciskillhub search <关键词>` | 搜索技能 |
| `sciskillhub install <技能> --platform claude -y` | 安装 |
| `sciskillhub --help` | 查看帮助 |

---

## 支持的平台

| 平台 | 参数 | 安装路径 |
|------|------|----------|
| Claude Code | `claude` | `~/.claude/skills/` |
| Cursor | `cursor` | `~/.cursor/skills/` |
| Codex CLI | `codex` | `~/.codex/skills/` |
| Gemini CLI | `gemini` | `~/.gemini/skills/` |
| Windsurf | `windsurf` | `~/.windsurf/skills/` |
| Cline | `cline` | `~/.cline/skills/` |

上表列的是 SciSkillHub CLI 常见平台参数，不代表所有 AI Client 都已经被 `--platform` 直接支持。
如果你的平台暂时不在支持列表里，或者当前平台的安装方式还未适配，可以直接下载 skill 的 `.zip` 文件，手动安装到对应的 `skills` 目录。

### 平台暂未支持时：手动安装 zip skill

1. 在 SciSkillHub 页面下载对应 skill 的 `.zip` 文件
2. 解压 zip，确认解压后的目录中包含 `SKILL.md`
3. 确定你的 `skills` 基础路径
4. 把整个 skill 目录移动到对应的 `skills` 目录下
5. 重启 AI Client，或重新打开当前会话

**目录结构要点：**

- 最终应当是 `<skills基础路径>/<skill-name>/SKILL.md`
- 不要多套一层目录，例如 `<skills基础路径>/<skill-name>/<skill-name>/SKILL.md`
- 如果不确定路径是否生效，优先重启客户端或新开会话再测试

### 你的 skills 路径

⚠️ **此处容易犯错，请先确定清楚“你的 skills 路径”后再下一步，从 system prompt 中获取 workspace、user、project 级 skills 路径信息，择其一作为 skills 基础路径。**

- OpenClaw 安装到你的 workspace skills 目录
- OpenClaw 变体（NanoBot、PicoClaw、memUBot、MaxClaw、CoPaw、AutoClaw、KimiClaw、QClaw、EasyClaw、workbuddy 等），通常会有类似 workspace、project、user 级 skills 目录

常用 AI Client 的 skills 路径如下：

- Claude Code: `~/.claude/skills/`
- Cursor: `~/.cursor/skills/`
- Windsurf: `~/.codeium/windsurf/skills/` 或项目下的 `.windsurf/skills/`
- Codex: `~/.codex/skills/` 或项目下的 `.agents/skills/`
- Google Antigravity: `~/.gemini/antigravity/skills/`
- Gemini CLI: `~/.gemini/skills/`

**手动安装示意：**

```bash
# 1. 下载 zip
## https://sciskillhub.org/skill/open-source/jackspace/ClaudeSkillz/skills/scientific-pkg-reportlab.zip
wget "https://sciskillhub.org/api/download/<skill-id>.zip" -O skill.zip

# 2. 解压
unzip skill.zip -d /tmp/sciskillhub-skill

# 3. 移动到你的 skills 目录
mv /tmp/sciskillhub-skill/<skill-name> ~/.claude/skills/
```

---

## 常见问题

### Q: 安装同名技能会怎样？

CLI 会提示你选择：覆盖现有技能或取消安装。

### Q: 如何查看已安装的技能？

```bash
ls ~/.claude/skills/  # Claude Code
ls ~/.cursor/skills/  # Cursor
```

### Q: 如何卸载技能？

```bash
rm -rf ~/.claude/skills/<skill-name>
```

---

## 获取帮助

- **网站**: https://sciskillhub.org
- **GitHub**: https://github.com/sciskillhub/typescript-cli
- **命令行**: `sciskillhub --help`
