"""Generate basic summary outputs for the JE Excel sample."""

from __future__ import annotations

import json
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

    (OUTPUT_DIR / "summary.md").write_text("\n".join(lines), encoding="utf-8")

    print(f"Wrote outputs to {OUTPUT_DIR.resolve()}")


if __name__ == "__main__":
    main()
