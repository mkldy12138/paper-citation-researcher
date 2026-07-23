# Paper Citation Researcher

面向科研评价、成果申报和学术影响力调查的高价值引用检索 Skill。它不会把普通引用作者全部堆进表格，而是重点识别并核验：

- 图灵奖及同等级国际大奖得主
- 中国科学院、中国工程院及各国科学院/工程院院士
- IEEE Fellow、ACM Fellow、AAAI Fellow、IAPR Fellow 等高等级会士
- Google/DeepMind、NVIDIA、Microsoft、Adobe、Amazon、Meta、IBM、Intel 等头部企业研究人员
- 引文正文中对目标论文给出明确正面评价或实际采用的方法作者

输出采用“一篇目标论文一组工作表”的结构，记录学者姓名、完整头衔、机构、具体引用论文、引用评价、主页、证据链接与可信度，避免同名误配、头衔夸大和“见PDF”式占位；也可以生成与 `b-DARTS_高价值引用影响调查报告.pdf` 同类的正式中文PDF报告。

## 特点

- 默认合并 Semantic Scholar、OpenAlex、OpenCitations/Crossref 与用户提供的引用 PDF/Markdown；Google Scholar 改为显式启用。
- 默认要求至少两个引用数据库成功，并覆盖最多1000名引用作者；不会只核验高引用论文的前几十名作者。
- 执行两轮以上候选核验和名册反向匹配，直到最后一轮不再发现新的高价值作者。
- 输出覆盖率、作者展开率、全文获取率、正文评价率、主页率和未解决候选，避免用“查到多少算多少”冒充完整调查。
- 使用有上限的分阶段并发：三个默认来源同时检索，Crossref元数据、作者画像、主页、PDF下载和正文分析分别并发；每阶段结束后统一汇总再进入下一阶段。
- 来源遇到429、临时5xx或超时时立即隔离；若同一目标存在近期成功快照，则以 `cached_fallback` 明示回退，避免坏网络覆盖好结果。
- 优先保留有正文证据的正面评价，并区分正面评价、方法采用/比较和普通提及。
- 使用作者ID、机构、研究方向、论文署名和官方主页进行保守身份解析。
- 对带 DOI 的引文作者表默认进行 Crossref 校正；仅在题名、作者总数、作者顺序和其余合作者共同支持时修复硬冲突，并完整保留原始姓名、原始来源 ID、校正类型、证据链接和置信度。缩写、重音、空格、连字符等规范写法差异保留作者 ID；硬冲突校正自动进入 DBLP 精确姓名+机构消歧、官方主页/Biography、荣誉和画像核验队列。Semantic Scholar 姓名检索若没有严格等价结果则明确拒绝，不再取“最高引用的近似姓名”。
- 保留 OpenAlex 的逐作者机构并与 Semantic Scholar 作者ID合并；同一引用记录中的 NVIDIA、Google/DeepMind、Microsoft、TikTok/ByteDance 等机构直接形成企业署名证据。
- 对优先作者并发执行定向 Deep Search：姓名+机构、IEEE/ACM/AAAI Fellow、各国科学院/Royal Society，以及学校或个人主页。
- 逐条核验院士、Fellow、奖项和企业归属，无法唯一对应时不纳入核心结果。
- 自动生成 `citation_report.xlsx` 和可浏览的 HTML 调查面板，作为可审计的数据底稿。
- 每次面向用户的正式调查都必须从经过验证的JSON生成中文PDF报告，包含总览表、逐人证据、企业作者、检索范围、限制和排除项；只有 Excel、HTML 或 JSON 时不算完成。
- 正式报告坚持“一人一节、一篇引文一条证据”，同时呈现引用原文、方法/背景/基线/数据集类型和中文技术说明。
- 支持多篇论文，每篇论文独立分表，不把所有姓名混在同一张表中。

## 安装

将整个 `paper-citation-researcher` 文件夹放入 Codex Skills 目录：

```powershell
Copy-Item -Recurse .\paper-citation-researcher "$HOME\.codex\skills\paper-citation-researcher"
python -m pip install -r "$HOME\.codex\skills\paper-citation-researcher\requirements.txt"
```

也可以直接在 Codex 中提出类似请求，触发 `$paper-citation-researcher`：

```text
调查论文 “Point Transformer V3” 的高价值引用，重点查找院士、IEEE Fellow、
图灵奖得主和国际头部企业作者。优先提取正面评价，输出可信度、主页、具体引用论文和证据。
```

## 命令行用法

完整运行：

```powershell
python scripts/paper_citation_researcher.py run `
  --paper "Point Transformer V3: Simpler, Faster, Stronger" `
  --output ".\citation-output" `
  --max-papers 1000 `
  --find-workers 3 `
  --metadata-workers 12 `
  --metadata-rps 5 `
  --author-workers 8 `
  --wiki-workers 4 `
  --download-workers 8 `
  --analyze-workers 4
```

分阶段运行：

```powershell
python scripts/paper_citation_researcher.py find --paper "<论文题名或 DOI>" --output ".\out"
python scripts/paper_citation_researcher.py authors --output ".\out"
python scripts/paper_citation_researcher.py download --output ".\out"
python scripts/paper_citation_researcher.py analyze --output ".\out"
python scripts/paper_citation_researcher.py dashboard --output ".\out"
python scripts/paper_citation_researcher.py report --output ".\out" --strict-report
```

作者校正默认并发执行，可按来源限流情况调整：

```powershell
python scripts/paper_citation_researcher.py authors --output ".\out" `
  --canonical-author-workers 8 --canonical-author-rps 5
```

如需复现实验而完全禁用 DOI 作者元数据校正，可显式添加 `--no-canonical-author-metadata`。

Google Scholar 默认关闭。确需使用时显式加入来源；用户给出了论文详情页时，可同时指定它以避免同题版本匹配失败：

```powershell
python scripts/paper_citation_researcher.py find `
  --paper "<论文题名>" --output ".\out" `
  --platforms "google-scholar,semantic-scholar,openalex,opencitations" `
  --scholar-target-url "https://scholar.google.com/citations?...&citation_for_view=..."
```

完整运行默认自动生成 `report.json` 和正式中文PDF；已有工作簿可单独重建：

```powershell
python scripts/paper_citation_researcher.py report `
  --output .\output `
  --report-pdf .\output\pdf\高价值引用影响调查报告.pdf `
  --strict-report
```

PDF输入JSON格式见 `references/report-data-schema.md`。生成后必须使用 Poppler 等工具渲染为PNG，逐页检查表格裁切、文字重叠、中文字体和链接可读性。最终答复必须直接给出PDF文件的绝对可点击路径，并同时说明页数和逐页检查结果；不得只交付 Excel、HTML、JSON、命令或生成说明。

需要达到详细 AMiner 报告的信息量时，使用默认的三源检索与高覆盖参数，并遵循 `references/quality-and-coverage-standard.md`。信息量对齐的是检索深度和逐人证据密度，不会用仅有高 h 指数、但不属于院士/Fellow/顶级奖项/头部企业类别的普通作者凑数。

作者 Google Scholar 画像也默认关闭；需要时添加 `--google-scholar-authors`。若任务要求 Google Scholar 引用发现必须成功，添加 `--require-google-scholar`，该参数会自动启用来源。

并发架构、阶段屏障和限流调参见 `references/concurrency-model.md`。Excel、JSON、HTML和PDF始终在汇总阶段单线程写入，避免文件竞争。

测试并发是否真正提速且不丢结果：

```powershell
python scripts/benchmark_concurrency.py `
  --paper "<论文标题或DOI>" `
  --output .\benchmark `
  --platforms opencitations
```

输出的 `QPS` 是质量保持加速比；基准会禁用缓存，且只有串并发结果均非空、成功来源集合一致、引用集合 Jaccard 与作者元数据覆盖率均达到 0.99 时才计分，否则自动记为0。

需要达到 MotionGPT 基准报告的人数和逐人证据密度时，参照 `references/motiongpt-benchmark-lessons.md`。默认 `--author-quality-scope high-impact` 会同时输出严格高价值作者、直接证实的头部企业作者和身份核验后的高影响力补充层；三类必须保留各自标签，不能混称院士或 Fellow。默认完整运行只下载入选重点作者对应的引文PDF，并在逐人部分展示具体引文、引用原文、引用类型和中文说明。严格模式要求至少两轮身份补全、末轮新增为0，并要求至少一半入选人物具有正文语境证据。

用 MotionGPT 参考集测量作者发现覆盖：

```powershell
python scripts/benchmark_author_coverage.py `
  --workbook .\motiongpt-output\citation_report.xlsx `
  --gold references\benchmarks\motiongpt-authors.json `
  --output .\motiongpt-output\author_coverage_benchmark.json
```

`VHAR` 只在姓名/机构身份匹配、具体引用论文、非 `unverified` 质量分层以及主页或企业署名证据同时存在时计为命中。该参考集用于测覆盖，不代替独立头衔核验。

## 输入材料

- 论文题名、DOI 或论文清单工作簿
- 用户已有的引用 PDF、Markdown 或历史调查表
- 可选的人工核验结果；人工材料应单独标注来源，不重复验证或覆盖

## 主要输出

- `高价值引用影响调查报告.pdf`：必须直接交付给用户的中文正式报告，完成逐页渲染检查后才能作为最终结果
- `citation_report.xlsx`：引用论文、作者、荣誉、企业、可信度、主页和正文引用位置
- `citation_dashboard.html`：可视化浏览与核验面板
- `pdfs/`：按需下载的高价值引用论文全文
- `manual_download_todo`：无法自动获取全文时的人工补充清单
- `report.json`：正式PDF的可审计结构化数据源

多篇目标论文的最终汇总表应为每篇论文分别设置“高价值学者”和“企业引用”工作表，并只保留一个最终工作簿。

## 证据与姓名规则

- 中国科学院、中国工程院院士使用中文名。
- 美国及其他国家院士、海外 Fellow 使用权威英文名，即使存在中文名。
- 企业身份必须与具体引用论文共享同一条署名机构证据，不能仅凭个人履历推断。
- 没有可靠全文时只确认引用关系，不编造评价语句。
- 图灵奖得主未核实时明确报告为0，不以“同等级大咖”替代。
- 每条结果必须给出可信度、判断理由和可追溯证据。

## 环境要求

- Python 3.10+
- 可访问 Semantic Scholar、OpenAlex、OpenCitations、出版社和机构官网的网络环境
- 仅在显式启用 Google Scholar 时需要 Edge、Chrome 或 Firefox 浏览器
- Python依赖见 `requirements.txt`
- Linux或macOS需要安装 Noto CJK/PingFang 等中文字体；也可通过 `CITATION_REPORT_FONT` 和 `CITATION_REPORT_BOLD_FONT` 指定字体文件。
- OpenAlex当前可能要求可用额度；通过 `OPENALEX_API_KEY` 提供密钥。无额度时会明确记录平台失败并继续其他来源，不会报告为0条引用。

更详细的工作表字段定义见 `references/output-schema.md`。
