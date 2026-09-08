"""
Name: nyc_trips_pipeline.py
Description: NYC yellow-taxi ETL pipeline — extract a raw trips file, apply the
    transformations, and load the result into data/processed (optionally
    partitioned). Every path and option is driven by CLI arguments.
Author: Abiodun Akinyemi
Modified by: Tosin Ayodele
Update date: 2026-08-29

Usage:
    # unpartitioned parquet (defaults)
    uv run python -m src.nyc_trips_pipeline

    # partitioned by payment type, written as CSV
    uv run python -m src.nyc_trips_pipeline \
        --as-file-type csv \
        --partition-by payment_type
"""

import argparse
import logging
import pathlib

from src.extract import extract_data_from_file
from src.load import load_data
from src.transform import transform_data

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ROOT = pathlib.Path("demo_data")

DEFAULT_INPUT = ROOT / "data/raw/yellow_taxi_jan2024_sample.csv"
DEFAULT_OUTPUT = ROOT / "data/processed/yellow_taxi_jan2024_processed.parquet"

# The business logic for this pipeline: cast the raw strings to real types,
# then derive the trip duration and tidy up the money/distance columns.
TRANSFORMATIONS = {
    "passenger_count": ("type", "int"),
    "pickup_datetime": ("type", "date", "%Y-%m-%d %H:%M:%S"),
    "dropoff_datetime": ("type", "date", "%Y-%m-%d %H:%M:%S"),
    "payment_type": "lowercase",
    "trip_duration_minutes": (
        "duration",
        "pickup_datetime",
        "dropoff_datetime",
        "minutes",
    ),
    "trip_distance": ("round", 1),
    "total_amount": ("round", 2),
}


def parse_args(argv=None):
    """
    Parses the command line arguments for the pipeline.

    Args:
        argv (list, optional): The arguments to parse. Defaults to None, which
            reads them from sys.argv.

    Returns:
        argparse.Namespace: The parsed arguments.
    """
    parser = argparse.ArgumentParser(
        description="Extract, transform and load the NYC yellow-taxi trips sample."
    )
    parser.add_argument(
        "--input-path",
        type=pathlib.Path,
        default=DEFAULT_INPUT,
        help=f"Path to the raw trips file (default: {DEFAULT_INPUT}).",
    )
    parser.add_argument(
        "--input-file-type",
        choices=["csv", "parquet", "json"],
        default="csv",
        help="Format of the raw file (default: csv).",
    )
    parser.add_argument(
        "--output-path",
        type=pathlib.Path,
        default=DEFAULT_OUTPUT,
        help=(
            "Where to write the processed data. A file when unpartitioned, "
            f"a directory when --partition-by is used (default: {DEFAULT_OUTPUT})."
        ),
    )
    parser.add_argument(
        "--as-file-type",
        choices=["csv", "parquet"],
        default="parquet",
        help="Format to write the processed data in (default: parquet).",
    )
    parser.add_argument(
        "--partition-by",
        nargs="+",
        default=None,
        metavar="COLUMN",
        help=(
            "Column(s) to partition the output by, e.g. --partition-by payment_type. "
            "Omit to write a single unpartitioned output."
        ),
    )
    parser.add_argument(
        "--chunksize",
        type=int,
        default=10000,
        help="Rows per chunk when reading/writing CSV (default: 10000).",
    )

    return parser.parse_args(argv)


def main(argv=None):
    """
    Runs the full extract -> transform -> load pipeline from the command line.

    Args:
        argv (list, optional): The arguments to parse. Defaults to None, which
            reads them from sys.argv.
    """
    args = parse_args(argv)

    logger.info(f"Extracting {args.input_file_type} data from {args.input_path}")
    # chunksize is a write-side concern here — the transformations need the whole
    # frame, so the extract always returns a single DataFrame.
    data = extract_data_from_file(
        args.input_path, file_type=args.input_file_type, chunksize=None
    )

    logger.info(f"Transforming {len(data)} row(s)")
    transformed = transform_data(data, transformations=TRANSFORMATIONS)

    logger.info(f"Loading to {args.output_path} (partition_by={args.partition_by})")
    output = load_data(
        transformed,
        file_path=args.output_path,
        as_file_type=args.as_file_type,
        partition_by=args.partition_by,
        chunksize=args.chunksize,
    )

    logger.info(f"Pipeline complete, output at {output}")


if __name__ == "__main__":
    # argv stays None, so argparse reads sys.argv.
    main()
