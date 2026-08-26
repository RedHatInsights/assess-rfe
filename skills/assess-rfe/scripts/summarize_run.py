#!/usr/bin/env python3
"""Summarize a status-aware assessment run from scores.csv."""

import argparse
import csv
import os
import sys
from collections import Counter


CRITERIA = ["Misclassified", "WHAT", "WHY", "Strategic", "HOW", "Scope"]


def load_scores(path):
    """Load scores from a CSV file or directory containing scores.csv."""
    if os.path.isdir(path):
        path = os.path.join(path, "scores.csv")
    if not os.path.exists(path):
        print(f"ERROR: {path} not found", file=sys.stderr)
        sys.exit(1)

    rows = []
    with open(path, encoding="utf-8") as scores_file:
        reader = csv.DictReader(scores_file)
        for row in reader:
            for column in [*CRITERIA, "Total", "Max_Score"]:
                value = row.get(column, "").strip()
                row[column] = int(value) if value else None
            rows.append(row)
    return rows


def _print_distribution(title, rows, maximum):
    print(f"### {title}")
    print()
    if not rows:
        print("No graded issues.")
        print()
        return

    distribution = Counter(row["Total"] for row in rows)
    print("| Score | Count | Bar |")
    print("|-------|-------|-----|")
    for score in range(maximum + 1):
        count = distribution.get(score, 0)
        if count:
            print(f"| {score}/{maximum} | {count} | {'#' * count} |")
    print()


def summarize(rows):
    """Print summary analysis without combining workflow-stage scores."""
    if not rows:
        print("No results to summarize.")
        return

    graded = [row for row in rows if row["Outcome"] == "GRADED"]
    stopped = [row for row in rows if row["Outcome"] == "STOP"]
    not_graded = [row for row in rows if row["Outcome"] == "NOT_GRADED"]
    errors = [row for row in rows if row["Outcome"] == "ERROR"]
    backlog = [
        row for row in graded if row["Status"].strip().lower() == "backlog"
    ]
    refinement = [
        row for row in graded if row["Status"].strip().lower() == "refinement"
    ]

    print("## Assessment Summary")
    print()
    print(f"- **Total results:** {len(rows)}")
    print(f"- **Backlog graded:** {len(backlog)}")
    print(f"- **Refinement graded:** {len(refinement)}")
    print(f"- **Stopped as misclassified:** {len(stopped)}")
    print(f"- **Not graded (other status):** {len(not_graded)}")
    if errors:
        print(f"- **Errors:** {len(errors)}")
    print()

    _print_distribution("Backlog Score Distribution", backlog, 8)
    _print_distribution("Refinement Score Distribution", refinement, 4)

    print("### Criterion Results")
    print()
    print("Averages include only issues for which the criterion was graded.")
    print()
    print("| Criterion | Graded | Average | Zeros |")
    print("|-----------|--------|---------|-------|")
    for criterion in CRITERIA:
        values = [row[criterion] for row in rows if row[criterion] is not None]
        average = sum(values) / len(values) if values else 0
        zeros = sum(value == 0 for value in values)
        print(f"| {criterion} | {len(values)} | {average:.2f} | {zeros} |")
    print()

    if stopped:
        print("### Reclassification Required")
        print()
        print("| ID | Title | Status |")
        print("|----|-------|--------|")
        for row in stopped[:15]:
            title = row["Title"][:70].replace("|", "\\|")
            print(f"| {row['ID']} | {title} | {row['Status']} |")
        if len(stopped) > 15:
            print(f"| ... | ({len(stopped) - 15} more) | |")
        print()

    if not_graded:
        status_counts = Counter(row["Status"] or "Missing" for row in not_graded)
        print("### Not Graded by Status")
        print()
        print("| Status | Count |")
        print("|--------|-------|")
        for status, count in sorted(status_counts.items()):
            print(f"| {status} | {count} |")
        print()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", help="Run directory or scores.csv path")
    args = parser.parse_args()
    summarize(load_scores(args.path))


if __name__ == "__main__":
    main()
