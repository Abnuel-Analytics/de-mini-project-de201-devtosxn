"""Profile a raw CSV: per-column quality metrics for the Chicago Food Inspections data."""

import pandas as pd


def load_csv(path):
    """Read every cell as text so nothing is coerced before it is measured.

    Empty and whitespace-only cells become null; all other cells are kept as-is.
    """
    df = pd.read_csv(path, dtype=str, keep_default_na=False)
    return df.mask(df.apply(lambda col: col.str.strip() == ""))


def profile_column(series):
    """Return quality metrics for one column; percentages are 0 to 100.

    distinct_pct is relative to the non-null values, so 100 means every value is unique.
    """
    values = series.dropna()
    rows = max(len(series), 1)  # guards the empty frame
    non_null = max(len(values), 1)  # guards the all-null column
    nulls = len(series) - len(values)
    distinct = values.nunique()
    return {
        "null_count": nulls,
        "null_pct": round(100 * nulls / rows, 2),
        "high_null": nulls / rows > 0.5,
        "distinct_count": distinct,
        "distinct_pct": round(100 * distinct / non_null, 2),
        "top_values": values.value_counts().head(10).to_dict(),
    }
