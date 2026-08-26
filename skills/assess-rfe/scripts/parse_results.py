#!/usr/bin/env python3
"""Parse status-aware RFE assessment results and produce a scores CSV."""

import argparse
import csv
import os
import re
import sys


CRITERIA = ["Misclassified", "WHAT", "WHY", "Strategic", "HOW", "Scope"]


def _metadata(text, name):
    match = re.search(
        rf"^(?:\*\*)?{name}(?:\*\*)?:\s*(.+?)\s*$",
        text,
        re.MULTILINE | re.IGNORECASE,
    )
    return match.group(1).strip().strip("*").strip() if match else ""


def _empty_result(status="", outcome="ERROR"):
    return {
        "Status": status,
        **{criterion: None for criterion in CRITERIA},
        "Total": None,
        "Max_Score": None,
        "Outcome": outcome,
    }


def extract_scores(text):
    """Extract status-specific scores and outcome from one result."""
    status = _metadata(text, "STATUS")
    outcome = _metadata(text, "OUTCOME").upper()
    lower_text = text.lower()

    if "data file not found" in lower_text or "unable to assess" in lower_text:
        return _empty_result(status, "ERROR")

    scores = {criterion: None for criterion in CRITERIA}
    total = max_score = None

    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue

        parts = [part.strip() for part in stripped.split("|")]
        if len(parts) < 3:
            continue

        raw_criterion = parts[1]
        criterion = re.sub(r"[*_?]", "", raw_criterion).strip().lower()
        score_cell = parts[2]
        score_match = re.search(r"(\d+)\s*/\s*(\d+)", score_cell)

        if "total" in criterion:
            if score_match:
                total = int(score_match.group(1))
                max_score = int(score_match.group(2))
            continue

        if not score_match:
            score_match = re.fullmatch(r"\s*([0-2])\s*", score_cell)
        if not score_match:
            continue
        score = int(score_match.group(1))

        if criterion.startswith("misclassified"):
            scores["Misclassified"] = score
        elif criterion.startswith("what"):
            scores["WHAT"] = score
        elif criterion.startswith("why"):
            scores["WHY"] = score
        elif criterion.startswith("strategic"):
            scores["Strategic"] = score
        elif "how" in criterion:
            scores["HOW"] = score
        elif "scope" in criterion or criterion.startswith("right"):
            scores["Scope"] = score

    normalized_status = status.strip().lower()
    if not outcome:
        if normalized_status == "backlog" and scores["Misclassified"] == 0:
            outcome = "STOP"
        elif normalized_status in {"backlog", "refinement"}:
            outcome = "GRADED"
        else:
            outcome = "NOT_GRADED"

    required = []
    if outcome == "STOP":
        required = ["Misclassified"]
    elif outcome == "GRADED" and normalized_status == "backlog":
        required = ["Misclassified", "WHAT", "WHY", "Strategic"]
    elif outcome == "GRADED" and normalized_status == "refinement":
        required = ["HOW", "Scope"]

    if required and any(scores[name] is None for name in required):
        return None

    if required and total is None:
        total = sum(scores[name] for name in required)
        max_score = len(required) * 2

    return {
        "Status": status,
        **scores,
        "Total": total,
        "Max_Score": max_score,
        "Outcome": outcome,
    }


def extract_title(text):
    """Extract the RFE title from result text."""
    return _metadata(text, "TITLE")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("result_dir", help="Directory containing .result.md files")
    parser.add_argument(
        "-o",
        "--output",
        default=None,
        help="Output CSV path (default: <result_dir>/scores.csv)",
    )
    args = parser.parse_args()

    result_dir = args.result_dir.rstrip("/")
    result_files = sorted(
        [name for name in os.listdir(result_dir) if name.endswith(".result.md")],
        key=lambda name: int(re.search(r"(\d+)", name).group(1))
        if re.search(r"(\d+)", name)
        else 0,
    )

    if not result_files:
        print(f"No .result.md files found in {result_dir}", file=sys.stderr)
        sys.exit(1)

    output_path = args.output or os.path.join(result_dir, "scores.csv")
    rows = []
    failed_parse = []

    for filename in result_files:
        key = filename.removesuffix(".result.md")
        filepath = os.path.join(result_dir, filename)
        with open(filepath, encoding="utf-8") as result_file:
            text = result_file.read()

        scores = extract_scores(text)
        if scores is None:
            failed_parse.append(key)
            continue
        rows.append({"ID": key, "Title": extract_title(text), **scores})

    fieldnames = [
        "ID",
        "Title",
        "Status",
        *CRITERIA,
        "Total",
        "Max_Score",
        "Outcome",
    ]
    with open(output_path, "w", newline="", encoding="utf-8") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    outcomes = {
        name: sum(1 for row in rows if row["Outcome"] == name)
        for name in ["GRADED", "STOP", "NOT_GRADED", "ERROR"]
    }
    print(f"Parsed {len(rows)} results -> {output_path}", file=sys.stderr)
    print(
        "  " + ", ".join(f"{name}: {count}" for name, count in outcomes.items()),
        file=sys.stderr,
    )
    if failed_parse:
        names = ", ".join(failed_parse[:10])
        print(f"  Could not parse: {len(failed_parse)} files: {names}", file=sys.stderr)


if __name__ == "__main__":
    main()
