"""
Name: load.py
Description: This module contains functions for loading data into various destinations.
Author: Abiodun Akinyemi
Modified by: Tosin Ayodele
Update date: 2026-08-29
"""

import logging
import pathlib

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SUPPORTED_FILE_TYPES = ("csv", "parquet")


def write_partitioned_csv(data, dir_path, partition_columns, chunksize=None):
    """
    Writes a DataFrame to Hive-style partitioned CSV files.

    Args:
        data (pd.DataFrame): The data to write.
        dir_path (str or pathlib.Path): The dataset directory itself, not its
            parent. It is created if it does not exist, and one
            `<column>=<value>` sub-directory per partition is written inside it.
        partition_columns (list): The columns to partition by. Their values
            become the sub-directory names and are dropped from the CSVs.
        chunksize (int, optional): Rows per write chunk. Defaults to None.

    Returns:
        int: The number of partition files written.

    Example:
        A frame with payment_type in {cash, credit_card} and vendor_id in {1, 2}::

            write_partitioned_csv(
                trips, "demo_data/data/processed/trips_csv",
                ["payment_type", "vendor_id"],
            )

        writes four files and returns 4::

            demo_data/data/processed/trips_csv/   <- dir_path
            |-- payment_type=cash/
            |   |-- vendor_id=1/part.csv
            |   `-- vendor_id=2/part.csv
            `-- payment_type=credit_card/
                |-- vendor_id=1/part.csv
                `-- vendor_id=2/part.csv
    """
    root = pathlib.Path(dir_path)
    # Only the count is needed downstream, so the paths are not accumulated.
    written = 0

    # group_keys is a scalar for a single partition column and a tuple for many,
    # so normalise it to a tuple before building the directory name.
    for group_keys, group in data.groupby(
        partition_columns, dropna=False, observed=True
    ):
        if not isinstance(group_keys, tuple):
            group_keys = (group_keys,)

        partition_dir = root.joinpath(
            *(
                f"{column}={value}"
                for column, value in zip(partition_columns, group_keys)
            )
        )
        partition_dir.mkdir(parents=True, exist_ok=True)

        part_file = partition_dir / "part.csv"
        # The partition values live in the directory names, so drop the columns
        # from the file itself, which is what parquet partitioning does too.
        group.drop(columns=partition_columns).to_csv(
            part_file, index=False, encoding="utf-8", chunksize=chunksize
        )
        written += 1

    logger.info(f"Wrote {written} CSV partition(s) under {root}")
    return written


def load_data(data, file_path, as_file_type="csv", partition_by=None, chunksize=None):
    """
    Loads data into a CSV or parquet destination.

    Args:
        data (pd.DataFrame): The data to load.
        file_path (str or pathlib.Path): The output path. When `partition_by` is
            given this is a directory; otherwise it is a single file.
        as_file_type (str, optional): "csv" or "parquet". Defaults to "csv".
        partition_by (str or list, optional): The column(s) to partition by.
            Accepts a single column name ("payment_type"), a list of them
            (["payment_type", "vendor_id"]), or None/[] for no partitioning.
            Defaults to None. Every name given must exist in `data`.
        chunksize (int, optional): The number of rows to include in each chunk.
            Defaults to None.

    Returns:
        pathlib.Path: The file or directory that was written.

    Raises:
        ValueError: If `as_file_type` is unsupported, a partition column is not
            in `data`, or `file_path` is the wrong kind of path for the write.
    """

    if as_file_type not in SUPPORTED_FILE_TYPES:
        raise ValueError("Unsupported file type. Use 'csv' or 'parquet'.")

    # Callers pass one column name, several, or nothing. Normalise all three
    # to a list so the rest of the function has a single shape to work with.
    if not partition_by:
        partition_columns = []
    elif isinstance(partition_by, str):
        partition_columns = [partition_by]
    else:
        partition_columns = list(partition_by)

    missing = [column for column in partition_columns if column not in data.columns]
    if missing:
        raise ValueError(f"Partition column(s) {missing} not found in data")

    output_path = pathlib.Path(file_path)

    # A partitioned write needs a directory and an unpartitioned one needs a
    # file, so reject a path that is already the other kind rather than letting
    # mkdir or the writer fail further down with a less obvious error.
    if partition_columns and output_path.is_file():
        raise ValueError(
            f"{output_path} is an existing file, but partitioning by "
            f"{partition_columns} writes a directory"
        )
    if not partition_columns and output_path.is_dir():
        raise ValueError(
            f"{output_path} is a directory, but an unpartitioned write needs a "
            f"file path, e.g. {output_path / f'data.{as_file_type}'}"
        )

    # Partitioned writes create the output directory itself; unpartitioned ones
    # only need the parent directory to exist.
    parent = output_path if partition_columns else output_path.parent
    parent.mkdir(parents=True, exist_ok=True)

    if as_file_type == "csv":
        if partition_columns:
            write_partitioned_csv(data, output_path, partition_columns, chunksize)
        else:
            data.to_csv(output_path, index=False, encoding="utf-8", chunksize=chunksize)
    elif as_file_type == "parquet":
        if partition_columns:
            data.to_parquet(output_path, index=False, partition_cols=partition_columns)
        else:
            data.to_parquet(output_path, index=False)

    logger.info(f"Loaded {len(data)} row(s) to {output_path} as {as_file_type}")
    return output_path
