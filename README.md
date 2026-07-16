# Paper Citation Researcher

面向科研评价、成果申报和学术影响力调查的高价值引用检索 Skill。它不会把普通引用作者全部堆进表格，而是重点识别并核验：

- 图灵奖及同等级国际大奖得主
- 中国科学院、中国工程院及各国科学院/工程院院士
- IEEE Fellow、ACM Fellow、AAAI Fellow、IAPR Fellow 等高等级会士
- Google/DeepMind、NVIDIA、Microsoft、Adobe、Amazon、Meta、IBM、Intel 等头部企业研究人员
- 引文正文中对目标论文给出明确正面评价或实际采用的方法作者

输出采用“一篇目标论文一组工作表”的结构，记录学者姓名、完整头衔、机构、具体引用论文、引用评价、主页、证据链接与可信度，避免同名误配、头衔夸大和“见PDF”式占位。

## 特点

- 合并 Google Scholar、Semantic Scholar、OpenAlex 与用户提供的引用 PDF/Markdown。
- 优先保留有正文证据的正面评价，并区分正面评价、方法采用/比较和普通提及。
- 使用作者ID、机构、研究方向、论文署名和官方主页进行保守身份解析。
- 逐条核验院士、Fellow、奖项和企业归属，无法唯一对应时不纳入核心结果。
- 自动生成 `citation_report.xlsx` 和可浏览的 HTML 调查面板。
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
  --browser edge `
  --scholar-locale zh-CN
```

分阶段运行：

```powershell
python scripts/paper_citation_researcher.py find --paper "<论文题名或 DOI>" --output ".\out"
python scripts/paper_citation_researcher.py authors --output ".\out"
python scripts/paper_citation_researcher.py download --output ".\out"
python scripts/paper_citation_researcher.py analyze --output ".\out"
python scripts/paper_citation_researcher.py dashboard --output ".\out"
```

Google Scholar 出现验证码时，默认保留浏览器窗口等待人工验证。若任务要求 Google Scholar 必须成功，增加 `--require-google-scholar`。

## 输入材料

- 论文题名、DOI 或论文清单工作簿
- 用户已有的引用 PDF、Markdown 或历史调查表
- 可选的人工核验结果；人工材料应单独标注来源，不重复验证或覆盖

## 主要输出

- `citation_report.xlsx`：引用论文、作者、荣誉、企业、可信度、主页和正文引用位置
- `citation_dashboard.html`：可视化浏览与核验面板
- `pdfs/`：按需下载的高价值引用论文全文
- `manual_download_todo`：无法自动获取全文时的人工补充清单

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
- Edge、Chrome 或 Firefox 浏览器
- 可访问 Google Scholar、Semantic Scholar、OpenAlex、出版社和机构官网的网络环境
- Python依赖见 `requirements.txt`

更详细的工作表字段定义见 `references/output-schema.md`。
