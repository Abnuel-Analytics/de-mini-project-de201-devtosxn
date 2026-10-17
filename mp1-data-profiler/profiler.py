"""Profile a raw CSV: per-column quality metrics for the Chicago Food Inspections data."""

import pandas as pd


def load_csv(path):
    """Read every cell as text so nothing is coerced before it is measured.

    Empty and whitespace-only cells become null; all other cells are kept as-is.
    """
    df = pd.read_csv(path, dtype=str, keep_default_na=False)
    return df.mask(df.apply(lambda col: col.str.strip() == ""))
