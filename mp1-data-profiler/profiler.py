"""Profile a raw CSV: per-column quality metrics for the Chicago Food Inspections data."""

import json
import sys
from pathlib import Path

import pandas as pd


def load_csv(path):
    """Read every cell as text so nothing is coerced before it is measured.

    Empty and whitespace-only cells become null; all other cells are kept as-is.
    """
    df = pd.read_csv(path, dtype=str, keep_default_na=False)
    return df.mask(df.apply(lambda col: col.str.strip() == ""))


DATE_PATTERN = (
    r"\d{1,2}/\d{1,2}/\d{4}|\d{4}-\d{2}-\d{2}([ T]\d{2}:\d{2}(:\d{2}(\.\d+)?)?)?"
)


def infer_type(values):
    """Classify non-null text values as empty, integer, float, date, mixed or string.

    The first rule that matches wins. "mixed" means some values look numeric or
    date-like and others do not, which is the shape of a column that needs cleaning.
    """
    if values.empty:
        return "empty"
    is_integer = values.str.fullmatch(r"[+-]?\d+")
    is_number = pd.to_numeric(values, errors="coerce").notna()
    is_date = values.str.fullmatch(DATE_PATTERN)
    if is_integer.all():
        return "integer"
    if is_number.all():
        return "float"
    if is_date.all():
        return "date"
    if (is_number | is_date).any():
        return "mixed"
    return "string"


def profile_column(series):
    """Return quality metrics for one column; percentages are 0 to 100.

    distinct_pct is relative to the non-null values, so 100 means every value is unique.
    """
    values = series.dropna()
    rows = max(len(series), 1)  # guards the empty frame
    non_null = max(len(values), 1)  # guards the all-null column
    nulls = len(series) - len(values)
    distinct = values.nunique()
    kind = infer_type(values)
    stats = {}
    if kind in ("integer", "float"):
        numbers = pd.to_numeric(values)
        stats = {
            "min": float(numbers.min()),
            "max": float(numbers.max()),
            "mean": round(float(numbers.mean()), 4),
            "median": float(numbers.median()),
        }
    elif kind != "empty":
        lengths = values.str.len()
        stats = {
            "min_length": int(lengths.min()),
            "max_length": int(lengths.max()),
            "avg_length": round(float(lengths.mean()), 2),
        }
    return {
        "type": kind,
        **stats,
        "null_count": nulls,
        "null_pct": round(100 * nulls / rows, 2),
        "high_null": nulls / rows > 0.5,
        "distinct_count": distinct,
        "distinct_pct": round(100 * distinct / non_null, 2),
        "top_values": values.value_counts().head(10).to_dict(),
    }


def main(path, out="output/profile_results.json"):
    """Profile the CSV at path, print a summary and write the full results as JSON."""
    df = load_csv(path)
    result = {
        "file_size_bytes": Path(path).stat().st_size,
        "row_count": len(df),
        "column_count": len(df.columns),
        "duplicate_rows": int(df.duplicated().sum()),
        "columns": {name: profile_column(df[name]) for name in df},
    }
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_text(json.dumps(result, indent=2) + "\n")

    print(
        f"{result['row_count']} rows, {result['column_count']} columns, {result['duplicate_rows']} duplicate rows"
    )
    for name, col in result["columns"].items():
        flag = "  HIGH NULL" if col["high_null"] else ""
        print(
            f"{name:<22}{col['type']:<9}nulls {col['null_pct']:>6}%  distinct {col['distinct_count']}{flag}"
        )


if __name__ == "__main__":
    main(sys.argv[1])
