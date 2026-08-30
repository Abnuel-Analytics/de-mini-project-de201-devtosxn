"""
Name: transform.py
Description: This module contains functions for transforming data.
Author: Abiodun Akinyemi
Modified by: Tosin Ayodele
Update date: 2026-08-29
"""

import logging

import pandas as pd

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Number of seconds in one unit of elapsed time, used by the "duration"
# transformation to convert a Timedelta into a plain number.
_DURATION_UNITS = {
    "seconds": 1,
    "minutes": 60,
    "hours": 3600,
    "days": 86400,
}

# Transformations that derive a brand new column from other columns, so the
# target column is not required to already exist on the DataFrame.
_DERIVING_TRANSFORMATIONS = ("age", "duration")


def to_datetime(series, date_format=None):
    """
    Parses a column into datetimes.

    Args:
        series (pd.Series): The column to parse.
        date_format (str, optional): The strftime format the values are in
            (e.g. "%Y-%m-%d"). Defaults to None, which lets pandas infer it.

    Returns:
        pd.Series: The parsed datetimes. Values that cannot be parsed become NaT
            rather than raising, so one bad row does not fail the whole pipeline.
    """
    parsed = pd.to_datetime(series, format=date_format, errors="coerce")

    unparsed = int(parsed.isna().sum() - pd.isna(series).sum())
    if unparsed > 0:
        logger.warning(
            f"{unparsed} value(s) could not be parsed as dates "
            f"(format={date_format!r}) and were set to NaT"
        )

    return parsed


def calculate_age(series, as_of=None):
    """
    Calculates whole years elapsed between a date column and a reference date.

    Args:
        series (pd.Series): The column of dates (e.g. dates of birth).
        as_of (str or datetime, optional): The date to measure age at.
            Defaults to None, which uses today's date.

    Returns:
        pd.Series: The age in completed years, as a nullable integer.
    """
    reference = (
        pd.Timestamp.today().normalize() if as_of is None else pd.Timestamp(as_of)
    )
    dates = to_datetime(series)

    # A birthday has been reached this year once the reference month/day is on
    # or after the source month/day — otherwise the person is a year younger.
    had_birthday = (reference.month > dates.dt.month) | (
        (reference.month == dates.dt.month) & (reference.day >= dates.dt.day)
    )

    age = (reference.year - dates.dt.year) - (~had_birthday).astype("int64")

    return age.where(dates.notna()).astype("Int64")


def calculate_duration(start_series, end_series, unit="minutes"):
    """
    Calculates the elapsed time between two datetime columns.

    Args:
        start_series (pd.Series): The column holding the start timestamps.
        end_series (pd.Series): The column holding the end timestamps.
        unit (str, optional): One of "seconds", "minutes", "hours" or "days".
            Defaults to "minutes".

    Returns:
        pd.Series: The elapsed time expressed in `unit`, as a float.
    """
    if unit not in _DURATION_UNITS:
        raise ValueError(
            f"Unsupported duration unit '{unit}'. Use one of {sorted(_DURATION_UNITS)}."
        )

    elapsed = to_datetime(end_series) - to_datetime(start_series)

    return elapsed.dt.total_seconds() / _DURATION_UNITS[unit]


def round_values(series, ndigits=2):
    """
    Rounds a numeric column to a fixed number of decimal places.

    Args:
        series (pd.Series): The column to round.
        ndigits (int, optional): The number of decimal places. Defaults to 2.

    Returns:
        pd.Series: The rounded values.
    """
    return pd.to_numeric(series, errors="coerce").round(ndigits)


def transform_data(data, transformations):
    """
    Transforms the data based on the specified transformations.

    Args:
        data (pd.DataFrame): The data to transform.
        transformations (dict): A mapping of column name to transformation.
            A transformation is either a plain string:

                "uppercase" | "lowercase" | "strip"

            or a tuple whose first element names the operation:

                ("type", "int")
                ("type", "float")
                ("type", "date")                    # format inferred
                ("type", "date", "%Y-%m-%d")        # explicit format
                ("age", "date_of_birth")            # age today, in whole years
                ("age", "date_of_birth", "2026-01-01")
                ("duration", "start_col", "end_col")            # minutes
                ("duration", "start_col", "end_col", "hours")
                ("round", 2)

            "age" and "duration" derive a new column, so their target column
            does not need to exist yet; every other transformation is applied
            in place to an existing column.

    Returns:
        pd.DataFrame: The transformed data.
    """
    for column, transformation in transformations.items():
        operation = (
            transformation[0] if isinstance(transformation, tuple) else transformation
        )

        if operation not in _DERIVING_TRANSFORMATIONS and column not in data.columns:
            logger.warning(f"Column '{column}' not found in data — skipping")
            continue

        if transformation == "uppercase":
            data[column] = data[column].str.upper()
        elif transformation == "lowercase":
            data[column] = data[column].str.lower()
        elif transformation == "strip":
            data[column] = data[column].str.strip()
        # conversion of types (values will be tuples)
        elif operation == "type":
            if transformation[1] == "int":
                # Convert column to integer
                data[column] = data[column].astype(int)
            elif transformation[1] == "float":
                # convert to float
                data[column] = data[column].astype(float)
            elif transformation[1] == "date":
                # Convert column to datetime. The format is optional — when it
                # is omitted pandas infers it, and unparseable values become
                # NaT instead of raising.
                date_format = transformation[2] if len(transformation) > 2 else None
                data[column] = to_datetime(data[column], date_format)
            else:
                logger.warning(f"Unsupported target type '{transformation[1]}'")
        # ---------------------------------------------------- custom transforms
        elif operation == "age":
            source = transformation[1]
            if source not in data.columns:
                logger.warning(
                    f"Column '{source}' not found in data — skipping '{column}'"
                )
                continue
            as_of = transformation[2] if len(transformation) > 2 else None
            data[column] = calculate_age(data[source], as_of)
        elif operation == "duration":
            start, end = transformation[1], transformation[2]
            missing = [col for col in (start, end) if col not in data.columns]
            if missing:
                logger.warning(
                    f"Column(s) {missing} not found in data — skipping '{column}'"
                )
                continue
            unit = transformation[3] if len(transformation) > 3 else "minutes"
            data[column] = calculate_duration(data[start], data[end], unit)
        elif operation == "round":
            ndigits = transformation[1] if len(transformation) > 1 else 2
            data[column] = round_values(data[column], ndigits)
        else:
            logger.warning(f"Unsupported transformation '{transformation}'")

    return data
