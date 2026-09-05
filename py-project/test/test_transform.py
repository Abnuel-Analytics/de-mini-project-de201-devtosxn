"""
Name: test_transform.py
Description: Unit tests for every functional unit of src/transform.py.
Author: Abiodun Akinyemi
Modified by: Tosin Ayodele
Update date: 2026-08-29
"""

import pandas as pd
import pytest
from src.transform import (
    calculate_age,
    calculate_duration,
    round_values,
    to_datetime,
    transform_data,
)

# ---------------------------------------------------------------- transform_data


def test_tranform_logic_uppercase():
    df = pd.DataFrame({"name": ["Abisola", "Segun"], "age": [23, 32]})
    tf_df = transform_data(df, transformations={"name": "uppercase"})
    assert all(name.isupper() for name in tf_df["name"].values)


def test_tranform_logic_lowercase():
    df = pd.DataFrame({"name": ["ABISOLA", "SEGUN"], "age": [23, 32]})
    tf_df = transform_data(df, transformations={"name": "lowercase"})
    assert all(name.islower() for name in tf_df["name"].values)


def test_tranform_logic_strip():
    df = pd.DataFrame({"name": ["  Abisola  ", "\tSegun\n"], "age": [23, 32]})
    tf_df = transform_data(df, transformations={"name": "strip"})
    assert tf_df["name"].tolist() == ["Abisola", "Segun"]


def test_tranform_logic_int_type():
    df = pd.DataFrame({"name": ["Abisola", "Segun"], "age": ["23", "32"]})
    tf_df = transform_data(df, transformations={"age": ("type", "int")})
    assert tf_df["age"].dtype.kind == "i"
    assert tf_df["age"].tolist() == [23, 32]


def test_tranform_logic_float_type():
    df = pd.DataFrame({"name": ["Abisola", "Segun"], "age": ["23", "32"]})
    tf_df = transform_data(df, transformations={"age": ("type", "float")})
    assert tf_df["age"].dtype.kind == "f"
    assert tf_df["age"].tolist() == [23.0, 32.0]


def test_tranform_logic_date_type():
    """The date transformation works when no format is supplied (the bug fix)."""
    df = pd.DataFrame({"date": ["2015-01-13", "2010-01-13"]})
    tf_df = transform_data(df, transformations={"date": ("type", "date")})
    assert tf_df["date"].dtype.kind == "M"
    assert tf_df["date"].tolist() == [
        pd.Timestamp("2015-01-13"),
        pd.Timestamp("2010-01-13"),
    ]


def test_tranform_logic_date_type_with_explicit_format():
    df = pd.DataFrame({"date": ["13/01/2015", "13/01/2010"]})
    tf_df = transform_data(df, transformations={"date": ("type", "date", "%d/%m/%Y")})
    assert tf_df["date"].tolist() == [
        pd.Timestamp("2015-01-13"),
        pd.Timestamp("2010-01-13"),
    ]


def test_tranform_logic_date_type_bad_value_becomes_nat():
    """An unparseable value is coerced to NaT instead of failing the pipeline."""
    df = pd.DataFrame({"date": ["2015-01-13", "not-a-date"]})
    tf_df = transform_data(df, transformations={"date": ("type", "date")})
    assert tf_df["date"].iloc[0] == pd.Timestamp("2015-01-13")
    assert pd.isna(tf_df["date"].iloc[1])


def test_tranform_logic_unsupported_transformation_is_skipped(caplog):
    df = pd.DataFrame({"name": ["Abisola"]})
    tf_df = transform_data(df, transformations={"name": "reverse"})
    assert tf_df["name"].tolist() == ["Abisola"]
    assert "Unsupported transformation" in caplog.text


def test_tranform_logic_missing_column_is_skipped(caplog):
    df = pd.DataFrame({"name": ["Abisola"]})
    tf_df = transform_data(df, transformations={"nickname": "uppercase"})
    assert list(tf_df.columns) == ["name"]
    assert "not found in data" in caplog.text


def test_tranform_logic_applies_multiple_transformations(people_df):
    tf_df = transform_data(
        people_df,
        transformations={
            "name": "strip",
            "age": ("type", "int"),
            "city": "uppercase",
            "score": ("round", 2),
        },
    )
    assert tf_df["name"].tolist() == ["Abisola", "Segun"]
    assert tf_df["age"].tolist() == [23, 32]
    assert tf_df["city"].tolist() == ["NEW YORK", "LAGOS"]
    assert tf_df["score"].tolist() == [12.35, 78.9]


# ------------------------------------------------------ custom transformation 1: age


def test_tranform_logic_age():
    df = pd.DataFrame({"date_of_birth": ["1990-05-20", "2000-01-01"]})
    tf_df = transform_data(
        df, transformations={"age": ("age", "date_of_birth", "2026-08-29")}
    )
    assert tf_df["age"].tolist() == [36, 26]


def test_calculate_age_before_and_after_birthday():
    """A birthday that has not happened yet this year counts as a year younger."""
    dates = pd.Series(["2000-08-30", "2000-08-29", "2000-08-28"])
    assert calculate_age(dates, as_of="2026-08-29").tolist() == [25, 26, 26]


def test_calculate_age_defaults_to_today():
    born_today = pd.Timestamp.today().normalize()
    assert calculate_age(pd.Series([born_today])).tolist() == [0]


def test_calculate_age_missing_date_is_null():
    assert pd.isna(calculate_age(pd.Series([None]), as_of="2026-08-29").iloc[0])


# ------------------------------------------------- custom transformation 2: duration


def test_tranform_logic_duration(trips_df):
    tf_df = transform_data(
        trips_df,
        transformations={
            "trip_duration_minutes": (
                "duration",
                "pickup_datetime",
                "dropoff_datetime",
            )
        },
    )
    assert tf_df["trip_duration_minutes"].tolist() == [30.0, 60.0, 30.0, 30.0]


def test_calculate_duration_units():
    start = pd.Series(["2024-01-01 10:00:00"])
    end = pd.Series(["2024-01-01 12:00:00"])
    assert calculate_duration(start, end, "seconds").tolist() == [7200.0]
    assert calculate_duration(start, end, "minutes").tolist() == [120.0]
    assert calculate_duration(start, end, "hours").tolist() == [2.0]
    assert calculate_duration(start, end, "days").tolist() == [2 / 24]


def test_calculate_duration_rejects_unknown_unit():
    start = pd.Series(["2024-01-01 10:00:00"])
    end = pd.Series(["2024-01-01 12:00:00"])
    with pytest.raises(ValueError, match="Unsupported duration unit"):
        calculate_duration(start, end, "fortnights")


# ---------------------------------------------------- custom transformation 3: round


def test_tranform_logic_round():
    df = pd.DataFrame({"total_amount": [10.555, 20.123]})
    tf_df = transform_data(df, transformations={"total_amount": ("round", 2)})
    assert tf_df["total_amount"].tolist() == [10.56, 20.12]


def test_round_values_defaults_to_two_decimals():
    assert round_values(pd.Series([1.23456])).tolist() == [1.23]


def test_round_values_coerces_strings():
    assert round_values(pd.Series(["1.987", "abc"]), 1).tolist()[0] == 2.0
    assert pd.isna(round_values(pd.Series(["1.987", "abc"]), 1).iloc[1])


# ----------------------------------------------------------------- to_datetime


def test_to_datetime_infers_format():
    parsed = to_datetime(pd.Series(["2015-01-13"]))
    assert parsed.iloc[0] == pd.Timestamp("2015-01-13")


def test_to_datetime_with_explicit_format():
    parsed = to_datetime(pd.Series(["13-01-2015"]), "%d-%m-%Y")
    assert parsed.iloc[0] == pd.Timestamp("2015-01-13")


def test_to_datetime_logs_unparseable_values(caplog):
    parsed = to_datetime(pd.Series(["2015-01-13", "nonsense"]))
    assert pd.isna(parsed.iloc[1])
    assert "could not be parsed as dates" in caplog.text
