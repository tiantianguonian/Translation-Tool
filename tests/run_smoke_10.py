#!/usr/bin/env python3
"""
run_smoke_10.py — Execute the Smoke-10 test suite.
Loads 10 samples, runs translation with all features ON, validates structure safety, generates report.
"""

import json
import os
import sys
import time
import argparse

# Project root
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "src"))

from translate_multi_language import (
    translate, CONFIG
)

sys.path.insert(0, os.path.join(PROJECT_ROOT, "tests"))
from acceptance_check import run_all_checks as structure_checks


def load_smoke_samples(path: str) -> list[dict]:
    """Load smoke test samples from JSONL file."""
    samples = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                try:
                    samples.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return samples


def run_smoke_10(samples_path: str, output_dir: str):
    """Run Smoke-10 test and generate report."""
    samples = load_smoke_samples(samples_path)
    if len(samples) < 10:
        print(f"WARNING: Only {len(samples)} samples loaded (expected 10)")

    # Enable all features
    CONFIG["ENABLE_TEXT_CLASSIFIER"] = True
    CONFIG["ENABLE_REVIEWER"] = True
    CONFIG["ENABLE_TERM_CHECK"] = True
    CONFIG["DEBUG_TOP_N"] = 0

    results = []
    pass_count = 0
    fail_count = 0
    fail_reasons = {
        "placeholder_break": 0,
        "newline_break": 0,
        "pipe_field_break": 0,
        "term_miss": 0,
        "unit_talk_break": 0,
    }

    print(f"Running Smoke-10 on {len(samples)} samples...")
    for i, sample in enumerate(samples):
        sample_id = sample.get("sample_id", f"smoke_{i}")
        source = sample.get("source_text", "")
        expected_type = sample.get("text_type", "normal")

        result = translate(source, sample_id=sample_id)

        # Run structure safety
        translation = result.get("translation", "")
        struct = structure_checks(source, translation)

        sample_result = {
            "sample_id": sample_id,
            "text_type": result.get("text_type", "unknown"),
            "expected_type": expected_type,
            "source": source,
            "translation": translation,
            "structure_pass": struct["all_pass"],
            "structure_failures": struct["failures"],
            "scores": result.get("scores", {}),
            "reviewer_used": result.get("reviewer_used", False),
            "review_rounds": result.get("review_rounds", 0),
        }

        # Track failures
        if not struct["all_pass"]:
            fail_count += 1
            for failure in struct["failures"]:
                check = failure.get("check", "")
                if "placeholder" in check:
                    fail_reasons["placeholder_break"] += 1
                elif "newline" in check:
                    fail_reasons["newline_break"] += 1
                elif "pipe" in check:
                    fail_reasons["pipe_field_break"] += 1
                elif "unit_talk" in check:
                    fail_reasons["unit_talk_break"] += 1
        else:
            pass_count += 1

        # Track term misses
        if result.get("scores", {}).get("issue_tags"):
            for tag in result["scores"]["issue_tags"]:
                if "term_miss" in tag:
                    fail_reasons["term_miss"] += 1

        results.append(sample_result)
        status = "PASS" if struct["all_pass"] else "FAIL"
        print(f"  [{i+1}/{len(samples)}] {sample_id}: {status} (type={result.get('text_type', '?')}, score={result.get('scores', {}).get('final_score', 0):.3f})")

    # Write quality log
    log_dir = os.path.join(PROJECT_ROOT, "production", "quality_logs")
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, "smoke_10.jsonl")
    with open(log_path, "w", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps({
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "sample_id": r["sample_id"],
                "text_type": r["text_type"],
                "source_text": r["source"],
                "translated_text": r["translation"],
                "format_score": r["scores"].get("format_score", 0),
                "term_consistency": r["scores"].get("term_consistency", 0),
                "fluency": r["scores"].get("fluency", 0),
                "completeness": r["scores"].get("completeness", 0),
                "style_match": r["scores"].get("style_match", 0),
                "final_score": r["scores"].get("final_score", 0),
                "verdict": r["scores"].get("verdict", "UNKNOWN"),
                "reviewer_used": r["reviewer_used"],
                "review_rounds": r["review_rounds"],
                "structure_pass": r["structure_pass"],
                "issue_tags": r["scores"].get("issue_tags", []),
            }, ensure_ascii=False) + "\n")

    # Generate report
    report_path = os.path.join(PROJECT_ROOT, "production", "reports", "smoke_10_report.md")
    os.makedirs(os.path.dirname(report_path), exist_ok=True)

    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# Smoke-10 Report\n\n")
        f.write(f"**Date**: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**Total Samples**: {len(samples)}\n\n")

        f.write("## Summary\n\n")
        f.write(f"- **Pass count**: {pass_count}\n")
        f.write(f"- **Fail count**: {fail_count}\n")
        f.write(f"- **Pass rate**: {pass_count}/{len(samples)} ({pass_count/len(samples)*100:.1f}%)\n\n")

        f.write("## Fail Reasons (top)\n\n")
        for reason, count in sorted(fail_reasons.items(), key=lambda x: -x[1]):
            if count > 0:
                f.write(f"- **{reason}**: {count}\n")
        f.write("\n")

        f.write("## Samples Detail\n\n")
        for r in results:
            f.write(f"### {r['sample_id']}\n\n")
            f.write(f"- **Type**: {r['text_type']} (expected: {r['expected_type']})\n")
            f.write(f"- **Structure**: {'PASS' if r['structure_pass'] else 'FAIL'}\n")
            if r["structure_failures"]:
                f.write(f"- **Failures**: {r['structure_failures']}\n")
            scores = r["scores"]
            f.write(f"- **Scores**: format={scores.get('format_score', 0)}, term={scores.get('term_consistency', 0):.2f}, fluency={scores.get('fluency', 0):.2f}, completeness={scores.get('completeness', 0):.2f}, style={scores.get('style_match', 0):.2f} → final={scores.get('final_score', 0):.3f} ({scores.get('verdict', '?')})\n")
            if scores.get("issue_tags"):
                f.write(f"- **Issues**: {', '.join(scores['issue_tags'])}\n")
            f.write(f"- **Reviewer**: {'used' if r['reviewer_used'] else 'not used'} (rounds: {r['review_rounds']})\n")
            f.write(f"- **Source**: `{r['source'][:100]}`\n")
            f.write(f"- **Translation**: `{r['translation'][:100]}`\n\n")

    print(f"\nSmoke-10 Complete: {pass_count} pass, {fail_count} fail")
    print(f"Report: {report_path}")
    print(f"Quality log: {log_path}")

    return pass_count == len(samples)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Smoke-10 test suite")
    parser.add_argument("--samples", default=None, help="Path to smoke_10.jsonl")
    parser.add_argument("--output-dir", default=None, help="Output directory override")
    args = parser.parse_args()

    samples_path = args.samples or os.path.join(PROJECT_ROOT, "tests", "smoke_10.jsonl")
    output_dir = args.output_dir or os.path.join(PROJECT_ROOT, "production")

    success = run_smoke_10(samples_path, output_dir)
    sys.exit(0 if success else 1)
