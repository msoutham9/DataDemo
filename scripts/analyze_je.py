"""Generate basic summary outputs for the JE Excel sample."""

from __future__ import annotations

import json
import math
from pathlib import Path

import pandas as pd


OUTPUT_DIR = Path("outputs")
INPUT_FILE = Path("je_samples.xlsx")


def _infer_date_columns(df: pd.DataFrame) -> dict[str, dict[str, str | int]]:
    date_columns: dict[str, dict[str, str | int]] = {}
    for column in df.columns:
        series = df[column]
        if pd.api.types.is_datetime64_any_dtype(series):
            parsed = series
        else:
            parsed = pd.to_datetime(series, errors="coerce", infer_datetime_format=True)
        non_null = parsed.notna().sum()
        if non_null == 0:
            continue
        min_date = parsed.min()
        max_date = parsed.max()
        date_columns[column] = {
            "non_null": int(non_null),
            "min": min_date.strftime("%Y-%m-%d"),
            "max": max_date.strftime("%Y-%m-%d"),
        }
    return date_columns


def _numeric_summary(df: pd.DataFrame) -> dict[str, dict[str, float | int]]:
    numeric_df = df.select_dtypes(include="number")
    if numeric_df.empty:
        return {}
    summary = numeric_df.describe().to_dict()
    formatted: dict[str, dict[str, float | int]] = {}
    for column, stats in summary.items():
        formatted[column] = {
            metric: float(value) for metric, value in stats.items() if value is not None
        }
    return formatted


def _first_digit(value: float) -> int | None:
    if value == 0 or math.isnan(value):
        return None
    value = abs(value)
    while value < 1:
        value *= 10
    while value >= 10:
        value /= 10
    return int(value)


def _benford_analysis(df: pd.DataFrame) -> dict[str, dict[str, float | int | dict[str, int]]]:
    numeric_df = df.select_dtypes(include="number")
    if numeric_df.empty:
        return {}

    expected_proportions = {digit: math.log10(1 + 1 / digit) for digit in range(1, 10)}
    results: dict[str, dict[str, float | int | dict[str, int]]] = {}

    for column in numeric_df.columns:
        series = pd.to_numeric(numeric_df[column], errors="coerce").dropna()
        digits = [
            digit
            for value in series
            if (digit := _first_digit(float(value))) is not None
        ]
        total = len(digits)
        if total == 0:
            continue
        counts = {digit: digits.count(digit) for digit in range(1, 10)}
        chi_square = 0.0
        max_deviation = 0.0
        for digit, expected in expected_proportions.items():
            expected_count = expected * total
            observed = counts[digit]
            chi_square += ((observed - expected_count) ** 2) / expected_count
            deviation = abs((observed / total) - expected)
            max_deviation = max(max_deviation, deviation)

        results[column] = {
            "sample_size": total,
            "chi_square": chi_square,
            "max_deviation": max_deviation,
            "observed_counts": counts,
        }

    return results


def main() -> None:
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Expected {INPUT_FILE} in repository root. Found: {INPUT_FILE.resolve()}"
        )

    df = pd.read_excel(INPUT_FILE)
    OUTPUT_DIR.mkdir(exist_ok=True)

    summary = {
        "file": INPUT_FILE.name,
        "row_count": int(df.shape[0]),
        "column_count": int(df.shape[1]),
        "columns": [
            {
                "name": column,
                "dtype": str(df[column].dtype),
                "null_count": int(df[column].isna().sum()),
            }
            for column in df.columns
        ],
        "date_ranges": _infer_date_columns(df),
        "numeric_summary": _numeric_summary(df),
        "benford_analysis": _benford_analysis(df),
    }

    summary_path = OUTPUT_DIR / "summary.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    lines = ["# JE Sample Summary", "", f"- Rows: {summary['row_count']}"]
    lines.append(f"- Columns: {summary['column_count']}")
    lines.append("")
    lines.append("## Columns")
    lines.append("| Name | Dtype | Nulls |")
    lines.append("| --- | --- | --- |")
    for column in summary["columns"]:
        lines.append(
            f"| {column['name']} | {column['dtype']} | {column['null_count']} |"
        )

    if summary["date_ranges"]:
        lines.append("")
        lines.append("## Date Ranges")
        lines.append("| Column | Non-null | Min | Max |")
        lines.append("| --- | --- | --- | --- |")
        for column, stats in summary["date_ranges"].items():
            lines.append(
                f"| {column} | {stats['non_null']} | {stats['min']} | {stats['max']} |"
            )

    if summary["numeric_summary"]:
        lines.append("")
        lines.append("## Numeric Summary")
        for column, stats in summary["numeric_summary"].items():
            lines.append("")
            lines.append(f"### {column}")
            lines.append("| Metric | Value |")
            lines.append("| --- | --- |")
            for metric, value in stats.items():
                lines.append(f"| {metric} | {value:.2f} |")

    if summary["benford_analysis"]:
        lines.append("")
        lines.append("## Benford's Law Analysis")
        lines.append(
            "Chi-square values compare observed first-digit frequencies to Benford's expected distribution."
        )
        for column, stats in summary["benford_analysis"].items():
            lines.append("")
            lines.append(f"### {column}")
            lines.append(f"- Sample size: {stats['sample_size']}")
            lines.append(f"- Chi-square: {stats['chi_square']:.2f}")
            lines.append(f"- Max deviation: {stats['max_deviation']:.4f}")
            lines.append("")
            lines.append("| First Digit | Observed Count | Expected % |")
            lines.append("| --- | --- | --- |")
            for digit in range(1, 10):
                expected_pct = math.log10(1 + 1 / digit) * 100
                observed = stats["observed_counts"][digit]
                lines.append(f"| {digit} | {observed} | {expected_pct:.2f}% |")

    (OUTPUT_DIR / "summary.md").write_text("\n".join(lines), encoding="utf-8")

    print(f"Wrote outputs to {OUTPUT_DIR.resolve()}")


if __name__ == "__main__":
    main()
