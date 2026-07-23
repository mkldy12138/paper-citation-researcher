import json
import os
import sys
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether

def first_existing(paths):
    for path in paths:
        if path and Path(path).is_file():
            return Path(path)
    return None


FONT = first_existing([
    os.environ.get("CITATION_REPORT_FONT"),
    r"C:\Windows\Fonts\msyh.ttc",
    r"C:\Windows\Fonts\simhei.ttf",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc",
    "/System/Library/Fonts/PingFang.ttc",
])
BOLD = first_existing([
    os.environ.get("CITATION_REPORT_BOLD_FONT"),
    r"C:\Windows\Fonts\msyhbd.ttc",
    r"C:\Windows\Fonts\simhei.ttf",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
    "/System/Library/Fonts/PingFang.ttc",
]) or FONT
if FONT is None:
    raise RuntimeError(
        "No Chinese font found. Set CITATION_REPORT_FONT and "
        "CITATION_REPORT_BOLD_FONT to installed TTF/TTC font files."
    )
pdfmetrics.registerFont(TTFont("CN", str(FONT), subfontIndex=0))
pdfmetrics.registerFont(TTFont("CN-Bold", str(BOLD), subfontIndex=0))

def esc(v):
    value = "" if v is None else str(v)
    return value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def build(data, output):
    styles = getSampleStyleSheet()
    body = ParagraphStyle("BodyCN", parent=styles["BodyText"], fontName="CN", fontSize=8.2, leading=13, textColor=colors.HexColor("#263238"))
    small = ParagraphStyle("SmallCN", parent=body, fontSize=7, leading=10)
    table_header = ParagraphStyle("TableHeaderCN", parent=small, fontName="CN-Bold", textColor=colors.white)
    h1 = ParagraphStyle("H1CN", parent=styles["Title"], fontName="CN-Bold", fontSize=20, leading=28, textColor=colors.HexColor("#123B56"), alignment=TA_CENTER)
    h2 = ParagraphStyle("H2CN", parent=styles["Heading2"], fontName="CN-Bold", fontSize=13, leading=18, textColor=colors.HexColor("#0B6E69"), spaceBefore=8, spaceAfter=6)
    h3 = ParagraphStyle("H3CN", parent=h2, fontSize=10.5, leading=15, textColor=colors.HexColor("#123B56"))
    quote = ParagraphStyle("QuoteCN", parent=body, fontSize=7.7, leading=12, leftIndent=4*mm, rightIndent=3*mm, borderColor=colors.HexColor("#AAB7B8"), borderWidth=0.5, borderPadding=5, backColor=colors.HexColor("#F4F7F7"), spaceBefore=2, spaceAfter=3)
    doc = SimpleDocTemplate(str(output), pagesize=A4, rightMargin=13*mm, leftMargin=13*mm, topMargin=15*mm, bottomMargin=15*mm, title=data["target"]["title"])
    story = [Spacer(1, 20*mm), Paragraph("高价值引用影响调查报告", h1), Spacer(1, 8*mm), Paragraph(esc(data["target"]["title"]), ParagraphStyle("T", parent=h2, alignment=TA_CENTER, fontSize=15, leading=22)), Spacer(1, 15*mm)]
    t = data["target"]
    meta = [["作者", t.get("authors", "")], ["年份 / 期刊", f"{t.get('year','')} / {t.get('venue','')}"], ["DOI", t.get("doi", "")], ["检索日期", t.get("retrieved_at", "")], ["本次检索被引数", t.get("citation_count", "")]]
    table = Table([[Paragraph(esc(a), body), Paragraph(esc(b), body)] for a,b in meta], colWidths=[34*mm, 135*mm])
    table.setStyle(TableStyle([("BACKGROUND",(0,0),(0,-1),colors.HexColor("#E7F1F0")),("FONTNAME",(0,0),(-1,-1),"CN"),("GRID",(0,0),(-1,-1),0.35,colors.HexColor("#AAB7B8")),("VALIGN",(0,0),(-1,-1),"TOP"),("PADDING",(0,0),(-1,-1),6)]))
    story += [table, Spacer(1, 6*mm)]
    if t.get("abstract"):
        story += [Paragraph("论文摘要", h3), Paragraph(esc(t.get("abstract")), body), Spacer(1, 4*mm)]
    coverage = data.get("coverage") or {}
    if coverage:
        coverage_rows = [
            ["发现引用论文", coverage.get("discovered_unique_citing_papers", "")],
            ["成功数据源", coverage.get("source_success_count", "")],
            ["展开作者数", coverage.get("unique_citing_authors", "")],
            ["核验候选数", coverage.get("high_value_candidates_reviewed", "")],
            ["正文语境已核验", coverage.get("retained_with_verified_context", "")],
            ["最终轮新增", coverage.get("new_verified_people_last_pass", "")],
        ]
        coverage_table = Table(
            [[Paragraph(esc(a), small), Paragraph(esc(b), small)] for a, b in coverage_rows],
            colWidths=[42*mm, 30*mm],
        )
        coverage_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#E7F1F0")),
            ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#AAB7B8")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("PADDING", (0, 0), (-1, -1), 4),
        ]))
        story += [Paragraph("检索覆盖", h3), coverage_table, Spacer(1, 5*mm)]
    story += [Paragraph("结论只收录身份能够可靠对应的高价值作者。中可信记录表示论文署名机构明确，但缺少独立个人履历佐证；低可信候选不进入主表。", body), PageBreak()]

    def summary(rows, scholar=True):
        headers = ["姓名", "荣誉/企业", "机构", "引用论文", "可信度", "主页"]
        vals = [headers]
        for r in rows:
            vals.append([r["name"], r.get("honor") or r.get("company"), r.get("affiliation") or r.get("raw_affiliation"), "；".join(p["title"] for p in r["citing_papers"]), r["confidence"].upper(), r.get("homepage") or "未找到可核验主页"])
        rendered = [[Paragraph(esc(x), table_header if row_index == 0 else small) for x in row] for row_index, row in enumerate(vals)]
        tab = Table(rendered, repeatRows=1, colWidths=[19*mm,25*mm,31*mm,54*mm,17*mm,32*mm])
        tab.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.HexColor("#123B56")),("TEXTCOLOR",(0,0),(-1,0),colors.white),("FONTNAME",(0,0),(-1,0),"CN-Bold"),("GRID",(0,0),(-1,-1),0.3,colors.HexColor("#AAB7B8")),("VALIGN",(0,0),(-1,-1),"TOP"),("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white,colors.HexColor("#F4F7F7")]),("PADDING",(0,0),(-1,-1),4)]))
        return tab

    story += [Paragraph("一、重点学者引用总览", h2)]
    story += [summary(data.get("scholars", [])) if data.get("scholars") else Paragraph("本次检索未发现可验证的重点学者引用。", body), Spacer(1, 7*mm), Paragraph("二、国际头部企业引用总览", h2)]
    story += [summary(data.get("companies", []), False) if data.get("companies") else Paragraph("本次检索未发现可验证的头部企业作者引用。", body), PageBreak()]

    def detail(rows, kind):
        out = []
        for idx,r in enumerate(rows,1):
            block = []
            label = r.get("honor") or r.get("company")
            block += [Paragraph(f"{idx}. {esc(r['name'])} - {esc(label)}", h3)]
            metrics = []
            if r.get("h_index") not in (None, ""):
                metrics.append(f"h指数 {r.get('h_index')}")
            if r.get("personal_citation_count") not in (None, ""):
                metrics.append(f"个人引用 {r.get('personal_citation_count')}")
            verdicts = r.get("claim_verdicts") or {}
            verdict_text = "；".join(f"{k}={v}" for k, v in verdicts.items())
            fields = [("机构/署名", r.get("affiliation") or r.get("raw_affiliation"))]
            if metrics:
                fields.append(("学术指标", "；".join(metrics)))
            fields.extend([("可信度", f"{r['confidence'].upper()}：{r['confidence_reason']}"), ("五项核验", verdict_text or "未单独记录"), ("主页", r.get("homepage") or "未找到可核验主页"), ("证据", "<br/>".join(r.get("honor_evidence") or r.get("affiliation_evidence") or []))])
            for k,v in fields: block.append(Paragraph(f"<b>{esc(k)}：</b>{esc(v) if k != '证据' else v}", body))
            for p in r["citing_papers"]:
                block.append(Paragraph(f"<b>具体引用论文：</b>{esc(p['title'])} ({esc(p.get('year'))}, {esc(p.get('venue'))})", body))
                paper_metrics = []
                if p.get("citation_count") not in (None, ""):
                    paper_metrics.append(f"引文自身被引 {p.get('citation_count')} 次")
                if p.get("target_citation_frequency") not in (None, ""):
                    paper_metrics.append(f"该作者引用目标论文 {p.get('target_citation_frequency')} 次")
                if paper_metrics:
                    block.append(Paragraph(f"<b>引文指标：</b>{esc('；'.join(paper_metrics))}", body))
                block.append(Paragraph(f"<b>论文链接：</b>{esc(p.get('url'))}", small))
                if p.get("evidence_pdf"):
                    location = f"第 {p.get('page')} 页" if p.get("page") else "页码未记录"
                    block.append(Paragraph(f"<b>正文证据：</b>{esc(location)}；{esc(p.get('evidence_pdf'))}", small))
                status = {"verified":"正文引文已核验","reference-list-only":"仅参考文献表已核验","not-accessible":"全文未获取"}[p["context_status"]]
                if p["context_status"] == "verified":
                    role = {"method":"方法引用","background":"背景/相关工作引用","baseline":"基线/比较引用","dataset":"数据集引用"}.get(p.get("citation_role"), "未分类")
                    if p.get("positive_assessment"):
                        sentiment = "正面技术表述"
                    elif "critical" in str(p.get("assessment_type") or ""):
                        sentiment = "批评性比较"
                    else:
                        sentiment = "中性引用"
                    block.append(Paragraph(f"<b>证据状态：</b>{status}；{role}；{sentiment}", body))
                else:
                    block.append(Paragraph(f"<b>证据状态：</b>{status}", body))
                if p.get("context_original") and p["context_status"] == "verified":
                    block.append(Paragraph(f"<b>引用原文：</b>{esc(p.get('context_original'))}", quote))
                if p.get("assessment_zh") and p["context_status"] == "verified":
                    block.append(Paragraph(f"<b>中文说明：</b>{esc(p.get('assessment_zh'))}", body))
            block.append(Spacer(1, 4*mm))
            if kind == "scholar":
                out.append(KeepTogether(block))
            else:
                out.extend(block)
        return out

    scholars = data.get("scholars", [])
    companies = data.get("companies", [])
    if scholars:
        story += [Paragraph("三、重点学者逐人证据", h2)] + detail(scholars, "scholar")
        if companies:
            story.append(PageBreak())
    if companies:
        story += [Paragraph("四、企业作者逐人证据", h2)] + detail(companies, "company")
    d = data.get("diagnostics", {})
    story += [PageBreak(), Paragraph("五、检索范围与限制", h2)]
    for s in t.get("sources", []): story.append(Paragraph(f"<b>{esc(s['name'])}：</b>{esc(s.get('coverage'))}；{esc(s.get('url'))}", body))
    if d.get("zero_categories"): story.append(Paragraph("<b>未发现的类别：</b>" + esc("、".join(d["zero_categories"])), body))
    for x in d.get("limitations", []): story.append(Paragraph("• " + esc(x), body))
    if d.get("excluded_candidates"):
        story.append(Paragraph("排除的歧义候选", h3))
        for x in d["excluded_candidates"]: story.append(Paragraph(f"• {esc(x['name'])}：{esc(x['reason'])}", body))

    def footer(canvas, doc):
        canvas.saveState(); canvas.setFont("CN", 7); canvas.setFillColor(colors.HexColor("#607D8B")); canvas.drawCentredString(A4[0]/2, 8*mm, f"高价值引用影响调查 | 第 {doc.page} 页"); canvas.restoreState()
    doc.build(story, onFirstPage=footer, onLaterPages=footer)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("Usage: render_report.py INPUT.json OUTPUT.pdf")
    data = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    output = Path(sys.argv[2])
    output.parent.mkdir(parents=True, exist_ok=True)
    build(data, output)
