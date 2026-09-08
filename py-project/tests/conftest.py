"""
Name: conftest.py
Description: Shared pytest fixtures for the ETL unit tests.
Author: Tosin Ayodele
Update date: 2026-08-29
"""

import pathlib

import pandas as pd
import pytest

# Anchored on this file rather than the working directory, so `pytest` behaves
# the same from the repository root and from py-project/.
TEST_DATA_DIR = pathlib.Path(__file__).resolve().parent.parent / "test_data"


@pytest.fixture(scope="session")
def test_data_dir():
    """The directory holding the small fixture files used by the extract tests."""
    TEST_DATA_DIR.mkdir(parents=True, exist_ok=True)

    # test_data.parquet is covered by the repository's `*.parquet` gitignore rule,
    # so it is regenerated from the committed CSV whenever it is missing.
    parquet_file = TEST_DATA_DIR / "test_data.parquet"
    if not parquet_file.exists():
        pd.read_csv(TEST_DATA_DIR / "test_data.csv").to_parquet(
            parquet_file, index=False
        )

    return TEST_DATA_DIR


@pytest.fixture
def people_df():
    """A small people DataFrame — string, numeric and date columns."""
    return pd.DataFrame(
        {
            "name": ["  Abisola ", "Segun"],
            "age": ["23", "32"],
            "city": ["New York", "Lagos"],
            "date_of_birth": ["1990-05-20", "2000-01-01"],
            "score": [12.3456, 78.9012],
        }
    )


@pytest.fixture
def string_ages_df():
    """A frame whose numeric column is still text, for the type transformations."""
    return pd.DataFrame({"name": ["Abisola", "Segun"], "age": ["23", "32"]})


@pytest.fixture
def name_only_df():
    """A single-column frame, for the transformations that should be skipped."""
    return pd.DataFrame({"name": ["Abisola"]})


@pytest.fixture
def two_hour_span():
    """A start and an end timestamp exactly two hours apart."""
    return (
        pd.Series(["2024-01-01 10:00:00"]),
        pd.Series(["2024-01-01 12:00:00"]),
    )


@pytest.fixture
def trips_df():
    """A small trips DataFrame with two partition-friendly, low-cardinality columns."""
    return pd.DataFrame(
        {
            "trip_id": [1, 2, 3, 4],
            "vendor_id": [1, 2, 1, 2],
            "payment_type": ["cash", "credit_card", "cash", "credit_card"],
            "pickup_datetime": [
                "2024-01-01 10:00:00",
                "2024-01-01 11:00:00",
                "2024-01-02 09:15:00",
                "2024-01-02 22:40:00",
            ],
            "dropoff_datetime": [
                "2024-01-01 10:30:00",
                "2024-01-01 12:00:00",
                "2024-01-02 09:45:00",
                "2024-01-02 23:10:00",
            ],
            "total_amount": [10.555, 20.123, 30.987, 40.001],
        }
    )
