import argparse
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

import pandas as pd


SCRIPT = Path(__file__).with_name("paper_citation_researcher.py")


def run_find(paper, output, platforms, max_papers, concurrent, scholar_target_url=""):
    if output.exists():
        shutil.rmtree(output)
    command = [
        sys.executable,
        str(SCRIPT),
        "find",
        "--paper",
        paper,
        "--output",
        str(output),
        "--platforms",
        platforms,
        "--max-papers",
        str(max_papers),
        "--minimum-source-success",
        "1",
        "--source-failure-policy",
        "skip",
        "--no-source-cache",
        "--scholar-captcha-action",
        "fail",
    ]
    if scholar_target_url:
        command.extend(["--scholar-target-url", scholar_target_url])
    if concurrent:
        command.extend([
            "--find-workers", "4",
            "--metadata-workers", "12",
            "--async-http",
        ])
    else:
        command.extend([
            "--find-workers", "1",
            "--metadata-workers", "1",
            "--no-async-http",
        ])
    started = time.monotonic()
    completed = subprocess.run(command, text=True, capture_output=True, encoding="utf-8")
    elapsed = time.monotonic() - started
    if completed.returncode != 0:
        raise RuntimeError(
            f"benchmark command failed ({completed.returncode}):\n{completed.stdout}\n{completed.stderr}"
        )
    workbook = output / "citation_report.xlsx"
    papers = pd.read_excel(workbook, sheet_name="papers").fillna("")
    keys = set(papers["dedupe_key"].astype(str))
    author_coverage = float(papers["citing_authors"].astype(str).str.strip().ne("").mean()) if len(papers) else 0.0
    notes = pd.read_excel(workbook, sheet_name="run_notes").fillna("")
    note_values = {}
    for _, row in notes.iterrows():
        key = str(row.iloc[0]).split(" ", 2)[-1]
        note_values[key] = row.iloc[1]
    source_counts = json.loads(str(note_values.get("find.platform_record_counts_json") or "{}"))
    successful_sources = sorted(source for source, count in source_counts.items() if int(count or 0) > 0)
    return {
        "elapsed_seconds": round(elapsed, 3),
        "rows": len(papers),
        "keys": keys,
        "author_coverage": author_coverage,
        "successful_sources": successful_sources,
        "stdout": completed.stdout,
    }


def main():
    parser = argparse.ArgumentParser(description="Measure quality-preserving concurrency speedup")
    parser.add_argument("--paper", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--platforms", default="opencitations")
    parser.add_argument("--max-papers", type=int, default=100)
    parser.add_argument("--scholar-target-url", default="")
    args = parser.parse_args()

    root = Path(args.output)
    root.mkdir(parents=True, exist_ok=True)
    serial = run_find(args.paper, root / "serial", args.platforms, args.max_papers, False, args.scholar_target_url)
    concurrent = run_find(args.paper, root / "concurrent", args.platforms, args.max_papers, True, args.scholar_target_url)

    union = serial["keys"] | concurrent["keys"]
    intersection = serial["keys"] & concurrent["keys"]
    jaccard = len(intersection) / len(union) if union else 1.0
    author_ratio = (
        concurrent["author_coverage"] / serial["author_coverage"]
        if serial["author_coverage"]
        else 1.0
    )
    nonempty = bool(serial["keys"] and concurrent["keys"])
    same_sources = serial["successful_sources"] == concurrent["successful_sources"]
    quality_gate = nonempty and same_sources and jaccard >= 0.99 and author_ratio >= 0.99
    raw_speedup = serial["elapsed_seconds"] / concurrent["elapsed_seconds"]
    qps = raw_speedup if quality_gate else 0.0
    report = {
        "metric": "Quality-Preserving Speedup (QPS)",
        "formula": "serial_wall_time / concurrent_wall_time when quality_gate passes; otherwise 0",
        "paper": args.paper,
        "platforms": args.platforms,
        "serial": {k: v for k, v in serial.items() if k not in {"keys", "stdout"}},
        "concurrent": {k: v for k, v in concurrent.items() if k not in {"keys", "stdout"}},
        "dedupe_key_jaccard": round(jaccard, 6),
        "author_coverage_ratio": round(author_ratio, 6),
        "nonempty_results": nonempty,
        "successful_source_sets_match": same_sources,
        "quality_gate_passed": quality_gate,
        "raw_speedup": round(raw_speedup, 3),
        "qps": round(qps, 3),
    }
    report_path = root / "benchmark.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print(f"Saved benchmark: {report_path}")
    return 0 if quality_gate else 2


if __name__ == "__main__":
    raise SystemExit(main())
