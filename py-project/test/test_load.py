"""
Name: test_load.py
Description: Unit tests for every functional unit of src/load.py.
Author: Abiodun Akinyemi
Modified by: Tosin Ayodele
Update date: 2026-08-29
"""

import pandas as pd
import pytest
from src.load import (
    load_data,
    normalise_partition_by,
    validate_partition_columns,
    write_partitioned_csv,
)

# ------------------------------------------------------------------- load_data


def test_load_to_csv_no_partition(tmp_path):
    df = pd.DataFrame({"name": ["Abisola", "Segun"], "age": [23, 32]})
    output = tmp_path / "test_load_csv_no_p.csv"
    load_data(df, output)
    assert len(pd.read_csv(output)) == 2


def test_load_to_csv_with_partition(tmp_path, trips_df):
    output = tmp_path / "trips_csv"
    load_data(trips_df, output, as_file_type="csv", partition_by="payment_type")

    assert (output / "payment_type=cash" / "part.csv").exists()
    assert (output / "payment_type=credit_card" / "part.csv").exists()

    cash = pd.read_csv(output / "payment_type=cash" / "part.csv")
    assert len(cash) == 2
    # The partition value lives in the directory name, not inside the file.
    assert "payment_type" not in cash.columns


def test_load_to_parquet_no_partition(tmp_path, trips_df):
    output = tmp_path / "trips.parquet"
    load_data(trips_df, output, as_file_type="parquet")
    assert len(pd.read_parquet(output)) == len(trips_df)


def test_load_to_parquet_with_partition(tmp_path, trips_df):
    output = tmp_path / "trips_parquet"
    load_data(trips_df, output, as_file_type="parquet", partition_by="payment_type")

    assert (output / "payment_type=cash").is_dir()
    assert (output / "payment_type=credit_card").is_dir()
    assert len(pd.read_parquet(output)) == len(trips_df)


def test_load_with_multiple_partition_columns(tmp_path, trips_df):
    output = tmp_path / "trips_multi"
    load_data(
        trips_df,
        output,
        as_file_type="csv",
        partition_by=["payment_type", "vendor_id"],
    )
    assert (output / "payment_type=cash" / "vendor_id=1" / "part.csv").exists()
    assert (output / "payment_type=credit_card" / "vendor_id=2" / "part.csv").exists()


def test_load_creates_missing_parent_directories(tmp_path):
    df = pd.DataFrame({"name": ["Abisola"]})
    output = tmp_path / "deeply" / "nested" / "out.csv"
    load_data(df, output)
    assert output.exists()


def test_load_returns_the_output_path(tmp_path):
    df = pd.DataFrame({"name": ["Abisola"]})
    output = tmp_path / "out.csv"
    assert load_data(df, output) == output


def test_load_honours_chunksize(tmp_path, trips_df):
    output = tmp_path / "chunked.csv"
    load_data(trips_df, output, as_file_type="csv", chunksize=2)
    assert len(pd.read_csv(output)) == len(trips_df)


def test_load_rejects_unsupported_file_type(tmp_path):
    df = pd.DataFrame({"name": ["Abisola"]})
    with pytest.raises(ValueError, match="Unsupported file type"):
        load_data(df, tmp_path / "out.txt", as_file_type="txt")


def test_load_rejects_unknown_partition_column(tmp_path, trips_df):
    with pytest.raises(ValueError, match="Partition column"):
        load_data(trips_df, tmp_path / "out", partition_by="does_not_exist")


# -------------------------------------------------------- normalise_partition_by


def test_normalise_partition_by_none():
    assert normalise_partition_by(None) == []


def test_normalise_partition_by_empty_string():
    assert normalise_partition_by("") == []


def test_normalise_partition_by_single_string():
    assert normalise_partition_by("payment_type") == ["payment_type"]


def test_normalise_partition_by_list():
    assert normalise_partition_by(["payment_type", "vendor_id"]) == [
        "payment_type",
        "vendor_id",
    ]


# ---------------------------------------------------- validate_partition_columns


def test_validate_partition_columns_passes_for_known_columns(trips_df):
    assert validate_partition_columns(trips_df, ["payment_type"]) is None


def test_validate_partition_columns_raises_for_unknown_columns(trips_df):
    with pytest.raises(ValueError, match=r"\['nope'\]"):
        validate_partition_columns(trips_df, ["payment_type", "nope"])


# ------------------------------------------------------------ write_partitioned_csv


def test_write_partitioned_csv_returns_one_path_per_partition(tmp_path, trips_df):
    written = write_partitioned_csv(trips_df, tmp_path / "out", ["payment_type"])
    assert len(written) == 2
    assert all(path.exists() for path in written)


def test_write_partitioned_csv_keeps_every_row(tmp_path, trips_df):
    root = tmp_path / "out"
    write_partitioned_csv(trips_df, root, ["payment_type"])
    total = sum(len(pd.read_csv(path)) for path in root.rglob("part.csv"))
    assert total == len(trips_df)
