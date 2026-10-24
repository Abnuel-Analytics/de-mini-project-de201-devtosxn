"""Profile a CSV file and report on the quality of each column.

How the code flows:
    main()            runs the steps below, then prints a summary and saves a JSON file
      load_csv()        reads the file as text
      profile_column()  measures one column (called once per column)
        infer_type()      works out what kind of data the column holds
        percent()         turns a count into a percentage

Run it with:  python profiler.py data/food-inspections.csv
"""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd


def load_csv(path):
    """Read a CSV file with every value kept as text.

    We keep everything as text on purpose. If pandas guessed the types for us,
    a zip code like "007" would silently become the number 7 and we would never
    see the problem. Blank cells (including cells with only spaces) become null.
    """
    df = pd.read_csv(path, dtype=str, keep_default_na=False)
    is_blank = df.apply(lambda column: column.str.strip() == "")
    return df.mask(is_blank)


def percent(part, whole):
    """Return part as a percentage of whole, rounded to 2 places (0 if whole is 0)."""
    if whole == 0:
        return 0.0
    return round(100 * part / whole, 2)


def infer_type(values):
    """Guess what kind of data a column holds, from its non-null text values.

    Returns one of these, checking in this order:
        "empty"    there are no values at all
        "integer"  every value is a number with no fractional part, like 60614 or 23.0
        "float"    every value is a number, like 41.89
        "date"     every value parses as a real date, in any common format
        "mixed"    some values look like numbers or dates and some do not
        "string"   anything else (plain text)

    "mixed" is the interesting one: it usually means the column needs cleaning.
    """
    if values.empty:
        return "empty"

    numbers = pd.to_numeric(values, errors="coerce")
    looks_like_number = numbers.notna() & np.isfinite(numbers)
    looks_like_date = pd.to_datetime(values, errors="coerce", format="mixed").notna()

    if looks_like_number.all():
        return "integer" if (numbers % 1 == 0).all() else "float"
    if looks_like_date.all():
        return "date"
    if (looks_like_number | looks_like_date).any():
        return "mixed"
    return "string"


def profile_column(series):
    """Measure one column and return the results as a dictionary.

    `series` is the whole column. `values` is the same column with the blanks
    removed, because most measurements only make sense on real values.

    The dictionary holds:
        type, then either min/max/mean/median (numbers)
                or min_length/max_length/avg_length (text and dates),
        null_count, null_pct, high_null (True if more than half is blank),
        distinct_count, distinct_pct (relative to non-blank values),
        top_values (the 10 most common values and how often each appears).
    """
    values = series.dropna()
    null_count = len(series) - len(values)
    distinct_count = values.nunique()
    column_type = infer_type(values)

    profile = {"type": column_type}

    if column_type in ("integer", "float"):
        numbers = pd.to_numeric(values)
        profile["min"] = float(numbers.min())
        profile["max"] = float(numbers.max())
        profile["mean"] = round(float(numbers.mean()), 4)
        profile["median"] = float(numbers.median())
    elif column_type != "empty":
        lengths = values.str.len()
        profile["min_length"] = int(lengths.min())
        profile["max_length"] = int(lengths.max())
        profile["avg_length"] = round(float(lengths.mean()), 2)

    profile["null_count"] = null_count
    profile["null_pct"] = percent(null_count, len(series))
    profile["high_null"] = null_count > len(series) / 2
    profile["distinct_count"] = distinct_count
    profile["distinct_pct"] = percent(distinct_count, len(values))
    profile["top_values"] = values.value_counts().head(10).to_dict()
    return profile


def main(path, out="output/profile_results.json"):
    """Profile every column in the CSV at `path`.

    Prints a short summary to the screen and saves the full results to `out`
    as JSON, so the numbers can be checked later.
    """
    df = load_csv(path)

    results = {
        "file_size_bytes": Path(path).stat().st_size,
        "row_count": len(df),
        "column_count": len(df.columns),
        "duplicate_rows": int(
            df.duplicated().sum()
        ),  # rows identical to an earlier row
        "columns": {name: profile_column(df[name]) for name in df},
    }

    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_text(json.dumps(results, indent=2) + "\n")

    print(
        f"{results['row_count']} rows, {results['column_count']} columns, "
        f"{results['duplicate_rows']} duplicate rows"
    )
    for name, column in results["columns"].items():
        high_null_flag = "  HIGH NULL" if column["high_null"] else ""
        print(
            f"{name:<22}{column['type']:<9}"
            f"nulls {column['null_pct']:>6}%  distinct {column['distinct_count']}"
            f"{high_null_flag}"
        )


if __name__ == "__main__":
    main(sys.argv[1])
