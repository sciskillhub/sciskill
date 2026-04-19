# Open Source Skills

Collected GitHub repositories that provide reusable skills, workflows, or domain-specific agent capabilities.

Total repositories: **70**

### [24111999/claude-skills](https://github.com/24111999/claude-skills)

Create and modify PowerPoint presentations (PPTX) through direct XML manipulation. Use this skill when: (1) Creating presentations from scratch, (2) Adding/editing/deleting slides, (3) Inserting images or custom shapes, (4) Applying POTX templates for consistent branding, (5) Editing existing PPTX files, (6) Working with slide layouts and placeholders, (7) User asks to make a "presentation", "slides", "deck", or mentions ".pptx". Supports all 11 standard Office slide layouts.

Example skill path: `slide-studio/SKILL.md`

### [Agents365-ai/ccc-skill](https://github.com/Agents365-ai/ccc-skill)

Domain expertise for cell-cell communication (CCC) analysis. Intent-to-tool routing, workflow patterns, code templates, and pitfall warnings for LIANA+, CellPhoneDB, CellChat, NicheNet, COMMOT, Squidpy, MEBOCOST, DIALOGUE, and 10+ additional tools across scRNA-seq and spatial transcriptomics data.

Example skill path: `SKILL.md`

### [Agents365-ai/seurat-skill](https://github.com/Agents365-ai/seurat-skill)

Comprehensive Seurat v5 (R) guide for single-cell RNA-seq and multimodal analysis. Covers installation, standard workflows (Normalize/SCTransform), clustering, integration (CCA/RPCA/Harmony), differential expression (FindMarkers/FindAllMarkers), visualization (DimPlot/FeaturePlot/VlnPlot/DoHeatmap), spatial transcriptomics (Visium/Visium HD/MERFISH/Slide-seq), CITE-seq, ATAC-seq, WNN, cell cycle regression, hashing/demultiplexing, sketch analysis, BPCells on-disk, pseudobulk, and format conversion. Use this skill whenever writing, debugging, or reviewing Seurat R code, building scRNA-seq pipelines, or looking up Seurat syntax, even for simple questions.

Example skill path: `SKILL.md`

### [aipoch/medical-research-skills](https://github.com/aipoch/medical-research-skills)

Turns reviewer comments into structured, professional point-by-point responses linked to manuscript revisions, clarifications, rebuttals, and additional analyses.

Example skill path: `awesome-med-research-skills/Academic Writing/author-response-builder/SKILL.md`

### [aksh-3141/claude-toolshed](https://github.com/aksh-3141/claude-toolshed)

Generate dev server lifecycle scripts (start/stop/status/ports) from detected project structure

Example skill path: `plugins/dev-setup/skills/dev-setup/SKILL.md`

### [ALMAZENY1/order-hub](https://github.com/ALMAZENY1/order-hub)

Use when building Laravel 10+ applications requiring Eloquent ORM, API resources, or queue systems. Invoke for Laravel models, Livewire components, Sanctum authentication, Horizon queues.

Example skill path: `auth-service/.ai/skills/laravel-specialist/SKILL.md`

### [AlterLab-IEU/AlterLab-Academic-Skills](https://github.com/AlterLab-IEU/AlterLab-Academic-Skills)

Data structure for annotated matrices in single-cell analysis. Use when working with .h5ad files or integrating with the scverse ecosystem. This is the data format skill—for analysis workflows use scanpy; for probabilistic models use scvi-tools; for population-scale queries use cellxgene-census. Part of the AlterLab Academic Skills suite.

Example skill path: `skills/bioinformatics/alterlab-anndata/SKILL.md`

### [ammawla/encode-toolkit](https://github.com/ammawla/encode-toolkit)

Build comprehensive chromatin accessibility maps by aggregating ATAC-seq and DNase-seq narrowPeak data across multiple ENCODE experiments, donors, and labs. Use when the user wants to answer "where is chromatin accessible in my tissue?" by combining peak calls into a union peak set. Handles cross-lab variation, ATAC vs DNase platform differences, and ENCODE blocklist filtering.

Example skill path: `plugin/skills/accessibility-aggregation/SKILL.md`

### [ankitgupta9525/VMware-Monitor](https://github.com/ankitgupta9525/VMware-Monitor)

VMware vCenter/ESXi read-only monitoring. Code-level enforced safety — no destructive operations exist in this codebase. Use when monitoring VMware infrastructure via natural language: querying inventory, checking health/alarms/logs, viewing VM info and snapshots, and scheduled log scanning. NO power, create, delete, snapshot, clone, or migrate.

Example skill path: `codex-skill/SKILL.md`

### [anthropics/life-sciences](https://github.com/anthropics/life-sciences)

Generate clinical trial protocols for medical devices or drugs. This skill should be used when users say "Create a clinical trial protocol", "Generate protocol for [device/drug]", "Help me design a clinical study", "Research similar trials for [intervention]", or when developing FDA submission documentation for investigational products.

Example skill path: `clinical-trial-protocol-skill/SKILL.md`

### [anubhavsingh-0218/uncodixify-skill](https://github.com/anubhavsingh-0218/uncodixify-skill)

Use when building or refactoring React and Tailwind UI that keeps drifting into generic AI-dashboard styling and needs a repeatable visual audit loop.

Example skill path: `SKILL.md`

### [AsadJaved66/Web-Skills-Protocol](https://github.com/AsadJaved66/Web-Skills-Protocol)

Place orders on Bob's Online Store. Use when the user wants to add items to a cart, apply coupons, choose shipping, and complete checkout via API. Handles the full purchase workflow from cart to confirmation. Requires a Bearer token (user must be logged in). Do NOT use for product search or browsing.

Example skill path: `examples/bobs-store/skills/order/SKILL.md`

### [bio-xyz/BioAgents](https://github.com/bio-xyz/BioAgents)

This skill should be used when users explicitly request academic papers, recent research, most cited research, or scholarly articles about longevity, aging, lifespan extension, or related topics. Triggers on phrases like "find papers on", "latest research about", "most cited studies on", or "academic literature about" in the context of longevity.

Example skill path: `.claude/skills/longevity-scholar/SKILL.md`

### [bloody2634/claud-skills](https://github.com/bloody2634/claud-skills)

Comprehensive document creation, editing, and analysis with support for tracked changes, comments, formatting preservation, and text extraction. When Claude needs to work with professional documents (.docx files) for: (1) Creating new documents, (2) Modifying or editing content, (3) Working with tracked changes, (4) Adding comments, or any other document tasks

Example skill path: `.claude/skills/document-skills/docx/SKILL.md`

### [Boom5426/Nature-Paper-Skills](https://github.com/Boom5426/Nature-Paper-Skills)

Use when checking manuscript citations, bibliography hygiene, DOI or PMID completeness, placeholder references, or BibTeX consistency before submission or revision.

Example skill path: `skills/core/citation-verifier/SKILL.md`

### [Chandrikakt/earl](https://github.com/Chandrikakt/earl)

Use recall.ai to record video meetings, retrieve transcripts, and access recordings. Use when the user wants to record a meeting, get a transcript, summarize a call, or access meeting audio/video.

Example skill path: `skills/3p/recall_ai/SKILL.md`

### [ClawBio/ClawBio](https://github.com/ClawBio/ClawBio)

Genomic coordinates of introgressed segments

Example skill path: `skills/archaic-introgression/SKILL.md`

### [cyanheads/pubmed-mcp-server](https://github.com/cyanheads/pubmed-mcp-server)

Scaffold an MCP App tool + UI resource pair. Use when the user asks to add a tool with interactive UI, create an MCP App, or build a visual/interactive tool.

Example skill path: `.agents/skills/add-app-tool/SKILL.md`

### [d-oit/web-doc-resolver](https://github.com/d-oit/web-doc-resolver)

Browser automation CLI for AI agents. Use when the user needs to interact with websites, including navigating pages, filling forms, clicking buttons, taking screenshots, extracting data, testing web apps, or automating any browser task. Triggers include requests to "open a website", "fill out a form", "click a button", "take a screenshot", "scrape data from a page", "test this web app", "login to a site", "automate browser actions", or any task requiring programmatic web interaction.

Example skill path: `.agents/skills/agent-browser/SKILL.md`

### [donbr/lifesciences-research](https://github.com/donbr/lifesciences-research)

Queries clinical databases (Open Targets, ClinicalTrials.gov) via curl for target-disease associations, target tractability assessment, and clinical trial discovery. This skill should be used when the user asks to \"validate drug targets\", \"find clinical trials\", \"assess target tractability\", \"discover disease associations\", or mentions Open Targets scores, NCT identifiers, target-disease evidence, druggability assessment, or translational research workflows.

Example skill path: `.claude/skills/lifesciences-clinical/SKILL.md`

### [droftgamer-wq/researcher-skill](https://github.com/droftgamer-wq/researcher-skill)

Runs multi-source investigations using a structured evidence-mapping cycle. Routes between business research, academic research, and claim verification. Triggers on: "research", "investigate", "verify", "compare", "analyze", "look into", "dig into", "fact check", "due diligence", "deep dive", "what is really happening", "how do real practitioners see this", "is this true", "is this legit", "what's the real story", "market landscape", "state of the art", "literature review", "competitive analysis", "opportunity scan", "risk assessment", "研究", "调研", "调查", "分析", "验证", "核实", "深挖", "摸底", "行业分析", "市场调研", "竞品分析", "尽调", "尽职调查", "这个靠谱吗", "真实情况是什么", "帮我查查", "帮我看看", "有没有前景", "值不值得", "到底怎么样", "是真的吗", "论文调研", "文献综述", "技术选型", "机会分析".

Example skill path: `researcher/SKILL.md`

### [DrugClaw/DrugClaw](https://github.com/DrugClaw/DrugClaw)

Query and manage Apple Calendar on macOS via `icalBuddy` (read) and AppleScript (`osascript`) for event creation. Use when users ask about upcoming events or adding calendar events.

Example skill path: `skills/built-in/apple-calendar/SKILL.md`

### [eamag/papers2dataset](https://github.com/eamag/papers2dataset)

Build structured datasets from academic papers. Use when the user wants to extract structured data from scientific literature, traverse citation graphs, search OpenAlex for papers, or create datasets from PDFs for research purposes.

Example skill path: `skill/SKILL.md`

### [Elfredaaroused655/claude-skills](https://github.com/Elfredaaroused655/claude-skills)

4 business growth agent skills and plugins for Claude Code, Codex, Gemini CLI, Cursor, OpenClaw. Customer success (health scoring, churn), sales engineer (RFP), revenue operations (pipeline, GTM), contract & proposal writer. Python tools (stdlib-only).

Example skill path: `business-growth/SKILL.md`

### [felipemsilva/PowerSkills](https://github.com/felipemsilva/PowerSkills)

Windows automation toolkit for AI agents. Provides Outlook email/calendar, Edge browser (CDP), desktop screenshots/window management, and shell commands via PowerShell. Install this for the full suite, or install individual sub-skills (powerskills-outlook, powerskills-browser, powerskills-desktop, powerskills-system) separately.

Example skill path: `SKILL.md`

### [fmschulz/omics-skills](https://github.com/fmschulz/omics-skills)

Add "Open in molab" badge(s) linking to marimo notebooks. Works with READMEs, docs, websites, or any markdown/HTML target.

Example skill path: `skills/add-molab-badge/SKILL.md`

### [foryourhealth111-pixel/Vibe-Skills](https://github.com/foryourhealth111-pixel/Vibe-Skills)

Vibe Code Orchestrator (VCO) is a governed runtime entry that freezes requirements, plans XL-first execution, and enforces verification and phase cleanup.

Example skill path: `SKILL.md`

### [FreedomIntelligence/OpenClaw-Medical-Skills](https://github.com/FreedomIntelligence/OpenClaw-Medical-Skills)

Cloud laboratory platform for automated protein testing and validation. Use when designing proteins and needing experimental validation including binding assays, expression testing, thermostability measurements, enzyme activity assays, or protein sequence optimization. Also use for submitting experiments via API, tracking experiment status, downloading results, optimizing protein sequences for better expression using computational tools (NetSolP, SoluProt, SolubleMPNN, ESM), or managing protein design workflows with wet-lab validation.

Example skill path: `skills/adaptyv/SKILL.md`

### [genepattern/module-toolkit](https://github.com/genepattern/module-toolkit)

Build AI agents with Pydantic AI — tools, capabilities, structured output, streaming, testing, and multi-agent patterns. Use when the user mentions Pydantic AI, imports pydantic_ai, or asks to build an AI agent, add tools/capabilities, stream output, define agents from YAML, or test agent behavior.

Example skill path: `.github/skills/building-pydantic-ai-agents/SKILL.md`

### [GPTomics/bioSkills](https://github.com/GPTomics/bioSkills)

Read, write, and convert multiple sequence alignment files using Biopython Bio.AlignIO. Supports Clustal, PHYLIP, Stockholm, FASTA, Nexus, and other alignment formats for phylogenetics and conservation analysis. Use when reading, writing, or converting alignment file formats.

Example skill path: `alignment/alignment-io/SKILL.md`

### [GusWan58/dataclaw](https://github.com/GusWan58/dataclaw)

Export Claude Code, Codex, Gemini CLI, OpenCode, and OpenClaw conversation history to Hugging Face. Use when the user asks about exporting conversations, uploading to Hugging Face, configuring DataClaw, reviewing PII/secrets in exports, or managing their dataset.

Example skill path: `docs/SKILL.md`

### [jackspace/ClaudeSkillz](https://github.com/jackspace/ClaudeSkillz)

This skill provides production-ready AI chat UI components built on shadcn/ui for conversational AI interfaces. Use when building ChatGPT-style chat interfaces with streaming responses, tool/function call displays, reasoning visualization, or source citations. Provides 30+ components including Message, Conversation, Response, CodeBlock, Reasoning, Tool, Actions, Sources optimized for Vercel AI SDK v5. Prevents common setup errors with Next.js App Router, Tailwind v4, shadcn/ui integration, AI SDK v5 migration, component composition patterns, voice input browser compatibility, responsive design issues, and streaming optimization. Keywords: ai-elements, vercel-ai-sdk, shadcn, chatbot, conversational-ai, streaming-ui, chat-interface, ai-chat, message-components, conversation-ui, tool-calling, reasoning-display, source-citations, markdown-streaming, function-calling, ai-responses, prompt-input, code-highlighting, web-preview, branch-navigation, thinking-display, perplexity-style, claude-artifacts

Example skill path: `skills/ai-elements-chatbot/SKILL.md`

### [javidmardanov/paper-banana-skill](https://github.com/javidmardanov/paper-banana-skill)

>-

Example skill path: `skills/paper-banana/SKILL.md`

### [JiahaoZhang-Public/ProtClaw](https://github.com/JiahaoZhang-Public/ProtClaw)

Add /compact command for manual context compaction. Solves context rot in long sessions by forwarding the SDK's built-in /compact slash command. Main-group or trusted sender only.

Example skill path: `apps/orchestrator/.claude/skills/add-compact/SKILL.md`

### [JimLiu/baoyu-skills](https://github.com/JimLiu/baoyu-skills)

Universal release workflow. Auto-detects version files and changelogs. Supports Node.js, Python, Rust, Claude Plugin, and generic projects. Use when user says "release", "发布", "new version", "bump version", "push", "推送".

Example skill path: `.claude/skills/release-skills/SKILL.md`

### [K-Dense-AI/scientific-agent-skills](https://github.com/K-Dense-AI/scientific-agent-skills)

How to use the Adaptyv Bio Foundry API and Python SDK for protein experiment design, submission, and results retrieval. Use this skill whenever the user mentions Adaptyv, Foundry API, protein binding assays, protein screening experiments, BLI/SPR assays, thermostability assays, or wants to submit protein sequences for experimental characterization. Also trigger when code imports `adaptyv`, `adaptyv_sdk`, or `FoundryClient`, or references `foundry-api-public.adaptyvbio.com`.

Example skill path: `scientific-skills/adaptyv/SKILL.md`

### [Kayunangka/claude-skill](https://github.com/Kayunangka/claude-skill)

Guide for writing ast-grep rules to perform structural code search and analysis. Use when users need to search codebases using Abstract Syntax Tree (AST) patterns, find specific code structures, or perform complex code queries that go beyond simple text search. This skill should be used when users ask to search for code patterns, find specific language constructs, or locate code with particular structural characteristics.

Example skill path: `ast-grep/skills/ast-grep/SKILL.md`

### [kimimgo/viznoir](https://github.com/kimimgo/viznoir)

>-

Example skill path: `.claude-plugin/skills/cae-postprocess/SKILL.md`

### [ma-compbio-lab/SkillFoundry](https://github.com/ma-compbio-lab/SkillFoundry)

Use this skill to search the current ClinicalTrials.gov v2 API for condition or keyword matches when you need official clinical-study metadata. Do not use it for legacy API URLs or offline work.

Example skill path: `skills/clinical-biomedical-data-science/clinicaltrials-study-search/SKILL.md`

### [Marshanda14816/agent-skills](https://github.com/Marshanda14816/agent-skills)

Builds React Native Nitro Modules from scratch in a monorepo. Scaffolds with Nitrogen, authors HybridObject TypeScript specs, generates native boilerplate, implements in C++/Swift/Kotlin, wires an example app, and prepares for npm publishing. Use when creating a new Nitro Module, implementing native functionality via HybridObjects, or setting up the nitrogen codegen pipeline.

Example skill path: `skills/build-nitro-modules/SKILL.md`

### [mateooo24/timework-skill](https://github.com/mateooo24/timework-skill)

>-

Example skill path: `SKILL.md`

### [megana05082003/review-analyzer-skill](https://github.com/megana05082003/review-analyzer-skill)

AI驱动的电商评论深度分析工具，支持22维度智能标签、用户画像识别、VOC洞察和可视化看板生成。 当用户需要以下功能时触发： - 分析电商产品评论（Amazon/eBay/AliExpress等平台） - 从评论中提取用户画像、痛点和VOC（客户之声） - 生成产品洞察报告和机会点分析 - 创建专业的可视化分析看板 - 进行竞品分析和市场定位研究 触发关键词：电商评论分析、评论分析、竞品分析、用户洞察、VOC分析、产品优化、市场调研、评论数据挖掘 AI Agent 约束：必须通过 AskUserQuestion 收集分析数量、AI引擎选择、报告署名后再执行分析

Example skill path: `SKILL.md`

### [mnfst/manifest](https://github.com/mnfst/manifest)

Collected GitHub skill repository.

### [mzoryy/hwpxskill](https://github.com/mzoryy/hwpxskill)

한글(HWPX) 문서 생성/읽기/편집 스킬. .hwpx 파일, 한글 문서, Hancom, OWPML 관련 요청 시 사용.

Example skill path: `SKILL.md`

### [naity/FM4Life](https://github.com/naity/FM4Life)

Skill for protein structure prediction and analysis with AlphaFold. Use this skill whenever a user wants to predict or fetch a protein 3D structure, download structures from the AlphaFold Database (AFDB), run ColabFold for novel proteins, parse pLDDT confidence scores or PAE (predicted aligned error) from AlphaFold outputs, predict structures of protein complexes or multimers, or work with AlphaFold3 for proteins with DNA/RNA/small molecules. Also trigger when the user mentions AlphaFold, AF2, AF3, AFDB, ColabFold, pLDDT, PAE, predicted aligned error, protein folding, or structure prediction from sequence.

Example skill path: `skills/alphafold/SKILL.md`

### [nandodeejay/appstore-review-skill](https://github.com/nandodeejay/appstore-review-skill)

Checks an iOS/iPadOS/macOS app project against Apple's App Store Review Guidelines before submission. Works with native (Swift/Obj-C), Flutter, React Native, Expo, Kotlin Multiplatform, .NET MAUI, Cordova, Ionic, and Unity projects. Use when the user wants to verify their app complies with App Store rules, or when they mention 'app review', 'app store guidelines', 'submission check', or 'review rejection'.

Example skill path: `skills/appstore-review/SKILL.md`

### [Nonsteroidevangel872/research-writing-skill](https://github.com/Nonsteroidevangel872/research-writing-skill)

科研论文写作助手，提供 30 个 Prompt 模板覆盖论文写作全流程。 当用户提到：论文写作、润色、翻译、文献综述、摘要、引言、方法章节、回复审稿人、基金申请、研究计划、学术演讲 PPT、LaTeX 编辑、学术图表、实验结果分析、模拟审稿、去 AI 味、文献对比、找研究空白、论文大纲时使用。

Example skill path: `SKILL.md`

### [openags/OpenAGS](https://github.com/openags/OpenAGS)

Dynamic research workflow management with self-reflection and backtracking

Example skill path: `skills/research-workflow/SKILL.md`

### [OpenRaiser/NanoResearch](https://github.com/OpenRaiser/NanoResearch)

Generate a Python code skeleton from an experiment blueprint

Example skill path: `skills/nanoresearch-experiment/SKILL.md`

### [Pavel-Kravchenko/Bioinformatics](https://github.com/Pavel-Kravchenko/Bioinformatics)

Tries, Aho-Corasick multi-pattern matching, suffix arrays with LCP, and suffix trees for genome indexing

Example skill path: `Skills/advanced-string-structures/SKILL.md`

### [Runchuan-BU/BioClaw](https://github.com/Runchuan-BU/BioClaw)

Add a Python-only figure reference skill to a BioClaw installation. Use when the user wants publication-quality plotting guidance inside agent containers without adding source-code features. Creates `container/skills/figure/` with a Python-only `SKILL.md` and a root-level `seaborn_reference.md`.

Example skill path: `.claude/skills/add-figure/SKILL.md`

### [Samuelkebede24/skill-conductor](https://github.com/Samuelkebede24/skill-conductor)

Create, edit, evaluate, and package agent skills. Use when building a new skill from scratch, improving an existing skill, running evals to test a skill, benchmarking skill performance, optimizing a skill's description for better triggering, reviewing third-party skills for quality, or packaging skills for distribution. Not for using skills or general coding tasks.

Example skill path: `skills/skill-conductor/SKILL.md`

### [Sapiens-ostracism678/finance-skills](https://github.com/Sapiens-ostracism678/finance-skills)

Read Discord for financial research using the discord-cli tool (read-only). Use this skill whenever the user wants to read Discord channels, search for messages in trading servers, view guild/channel info, monitor crypto or market discussion groups, or gather financial sentiment from Discord. Triggers include: "check my Discord", "search Discord for", "read Discord messages", "what's happening in the trading Discord", "show Discord channels", "list my servers", "Discord sentiment on BTC", "what are people saying in Discord about AAPL", "monitor crypto Discord", "export Discord messages", any mention of Discord in context of reading financial news, market research, or trading community discussions. This skill is READ-ONLY — it does NOT support sending messages, reacting, or any write operations.

Example skill path: `skills/discord-reader/SKILL.md`

### [sethikasithum/skill-generator](https://github.com/sethikasithum/skill-generator)

Tạo AI Skill mới từ ý tưởng hoặc quy trình công việc. Kết hợp phỏng vấn thông minh, pattern detection, và quantitative evaluation để tạo skill chất lượng production. Dùng khi user nói "tạo skill", "biến quy trình thành skill", "make a new skill", "tự động hóa công việc này", hoặc mô tả quy trình lặp lại mà họ muốn AI tự làm. Cũng dùng khi user muốn cải thiện, test, hoặc optimize skill hiện có.

Example skill path: `SKILL.md`

### [Shroomfaerie/veriglow-agent-map-skill](https://github.com/Shroomfaerie/veriglow-agent-map-skill)

Look up VeriGlow Agent Map for any website URL to discover its data functions, internal APIs, browser automation recipes, and agent reliability reports. Use when you need to extract structured data from a website, call a website's hidden API, or automate browser interactions with a web page.

Example skill path: `plugins/veriglow-agent-map/skills/veriglow-agent-map/SKILL.md`

### [Sibyl-Research-Team/AutoResearch-SibylSystem](https://github.com/Sibyl-Research-Team/AutoResearch-SibylSystem)

Sibyl Codex 独立第三方审查 - 使用 OpenAI Codex 提供不同 AI 视角的评审

Example skill path: `.claude/skills/sibyl-codex-reviewer/SKILL.md`

### [SURFLIN2030/swing-skills](https://github.com/SURFLIN2030/swing-skills)

Prevents premature execution on ambiguous requests. Analyzes request clarity using 5W1H decomposition, surfaces hidden assumptions, and generates structured clarifying questions before work begins. Use at the start of any non-trivial task, or when a request could be interpreted multiple ways. Triggers on "뭘 원하는건지", "요구사항 정리", "clarify", "what exactly", "scope", "requirements", "정확히 뭘", "before we start".

Example skill path: `skills/swing-clarify/SKILL.md`

### [Taison472/codex-skills](https://github.com/Taison472/codex-skills)

Prepare and execute safe two-step Git commits in Codex by drafting a commit message, requesting explicit user approval, and only then committing. Use when the user asks to prepare a commit message, perform a commit, or run a two-step commit workflow. Do not use Claude slash commands or Claude CLI for this workflow.

Example skill path: `skills/commit-workflow/SKILL.md`

### [teixasalone/UnrealEngine5-Skills](https://github.com/teixasalone/UnrealEngine5-Skills)

UE5.6/UE5.7 architecture planning and module boundary design for Unreal projects. Use when requests involve module layout, Build.cs dependencies, reflection exposure strategy, Public/Private API boundaries, naming conventions, and preventing circular dependencies.

Example skill path: `skills/ue5-architecture/SKILL.md`

### [TenureAI/PhD-Zero](https://github.com/TenureAI/PhD-Zero)

|-

Example skill path: `.agents/skills/deep-research/SKILL.md`

### [th3vib3coder/vibe-science-codex](https://github.com/th3vib3coder/vibe-science-codex)

Scientific research engine with adversarial review, tree search over hypotheses, and serendipity detection. Turns a coding agent into a rigorous research partner that hunts for artifacts, confounders, and unexpected discoveries. Use this skill whenever the user mentions research, hypotheses, scientific analysis, experimental design, literature review, data validation, quality gates, claim verification, reproducibility, or any task where correctness matters more than speed. Also use when the user wants to explore a dataset scientifically, validate findings against literature, run computational experiments with adversarial review, or hunt for unexpected patterns. Do NOT use for simple Q&A, code editing without research context, or non-scientific tasks.

Example skill path: `SKILL.md`

### [toohamster/sftp-cc](https://github.com/toohamster/sftp-cc)

通用 SFTP 上传工具，通过自然语言触发，将本地项目文件上传到远程服务器。支持增量上传、私钥自动绑定与权限修正。

Example skill path: `skills/sftp-cc/SKILL.md`

### [unexplained-familyephedraceae871/openclaw-skill](https://github.com/unexplained-familyephedraceae871/openclaw-skill)

OpenClaw development assistant, built by Michel Costa, co-founder of Brabaflow — AI-Native Agency (brabaflow.ai). Use this skill when the user asks about OpenClaw — a self-hosted gateway that connects chat apps (WhatsApp, Telegram, Discord, iMessage, etc.) to AI coding agents. Covers configuration, channels, providers, tools, plugins, deployment, CLI commands, and all aspects of OpenClaw development. 333 pages of verbatim official documentation from docs.openclaw.ai.

Example skill path: `skills/openclaw/SKILL.md`

### [wenmin-wu/ds-skills](https://github.com/wenmin-wu/ds-skills)

Converts a pretrained 2D CNN into a 3D CNN by recursively replacing Conv2d/BN2d/Pool2d layers and inflating kernel weights along the depth axis.

Example skill path: `skills/cv/2d-to-3d-model-conversion/SKILL.md`

### [wtfhanin/Enhance-Prompt](https://github.com/wtfhanin/Enhance-Prompt)

Transform raw prompts into professional-grade, codebase-aware instructions. Use when improving vague/incomplete prompts, adding codebase context to requests, rewriting instructions with structured sections, or crafting detailed prompts like a professional prompt engineer. Supports auto-category detection, prompt chain decomposition, iterative refinement, multilingual handling, monorepo detection, and includes 13 professional templates.

Example skill path: `skills/enhance-prompt/SKILL.md`

### [YTItsfrost/cypress-agent-skill](https://github.com/YTItsfrost/cypress-agent-skill)

Production-grade Cypress E2E and component testing — selectors, network stubbing, auth, CI parallelization, flake elimination, Page Object Model, and TypeScript support. The complete Cypress skill for AI agents.

Example skill path: `SKILL.md`

### [zacklecon/claude-skills](https://github.com/zacklecon/claude-skills)

Use when building Angular 17+ applications with standalone components or signals. Invoke for enterprise apps, RxJS patterns, NgRx state management, performance optimization, advanced routing.

Example skill path: `skills/angular-architect/SKILL.md`

### [zarazhangrui/frontend-slides](https://github.com/zarazhangrui/frontend-slides)

Create stunning, animation-rich HTML presentations from scratch or by converting PowerPoint files. Use when the user wants to build a presentation, convert a PPT/PPTX to web, or create slides for a talk/pitch. Helps non-designers discover their aesthetic through visual exploration rather than abstract choices.

Example skill path: `SKILL.md`

### [zinxj/uikit-expert-skill](https://github.com/zinxj/uikit-expert-skill)

Write, review, or improve UIKit code following best practices for view controller lifecycle, Auto Layout, collection views, navigation, animation, memory management, and modern iOS 18–26 APIs. Use when building new UIKit features, refactoring existing views or view controllers, reviewing code quality, adopting modern UIKit patterns (diffable data sources, compositional layout, cell configuration), or bridging UIKit with SwiftUI. Does not cover SwiftUI-only code.

Example skill path: `uikit-expert/SKILL.md`

### [zongtingwei/Bioclaw_Skills_Hub](https://github.com/zongtingwei/Bioclaw_Skills_Hub)

Workflow for read alignment, sorting, indexing, mapping statistics, and downstream-ready alignment artifacts.

Example skill path: `skills/core-bioinformatics/alignment-and-mapping/SKILL.md`
