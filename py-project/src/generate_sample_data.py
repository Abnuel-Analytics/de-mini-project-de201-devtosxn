"""
Name: generate_sample_data.py
Description: Generates the synthetic NYC yellow-taxi sample that the pipeline
    reads. `data/` is gitignored, so this seeds a local copy on demand — it is
    the same generation logic (and seed) as Section 3 of dev-notebook.ipynb.
Author: Abiodun Akinyemi
Modified by: Tosin Ayodele
Update date: 2026-08-29

Usage:
    uv run python -m src.generate_sample_data
"""

import argparse
import csv
import logging
import pathlib
import random

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ROOT = pathlib.Path("demo_data")
DEFAULT_OUTPUT = ROOT / "data/raw/yellow_taxi_jan2024_sample.csv"

ZONES = {1: "JFK Airport", 132: "LaGuardia", 161: "Midtown", 230: "Times Square"}
ZONE_IDS = list(ZONES.keys())
PAYMENT = ["credit_card", "cash", "no_charge", "dispute"]


def build_rows(n_rows=10_000, seed=42):
    """
    Builds the synthetic trip records.

    Args:
        n_rows (int, optional): How many trips to generate. Defaults to 10000.
        seed (int, optional): Random seed, so runs are reproducible. Defaults to 42.

    Returns:
        list: One dict per trip.
    """
    random.seed(seed)

    rows = []
    for i in range(n_rows):
        dist = round(random.uniform(0.5, 25.0), 2)
        fare = round(max(2.50, 2.50 + dist * 2.50 + random.gauss(0, 3)), 2)
        tip = round(fare * random.uniform(0, 0.25), 2) if random.random() > 0.3 else 0.0
        hr = random.randint(0, 23)
        day = random.randint(1, 28)
        rows.append(
            {
                "trip_id": i + 1,
                "vendor_id": random.choice([1, 2]),
                "pickup_datetime": f"2024-01-{day:02d} {hr:02d}:{random.randint(0, 59):02d}:00",
                "dropoff_datetime": (
                    f"2024-01-{day:02d} "
                    f"{(hr + random.randint(0, 2)) % 24:02d}:{random.randint(0, 59):02d}:00"
                ),
                "pickup_zone_id": random.choice(ZONE_IDS),
                "dropoff_zone_id": random.choice(ZONE_IDS),
                "passenger_count": random.randint(1, 4),
                "trip_distance": dist,
                "fare_amount": fare,
                "tip_amount": tip,
                "total_amount": round(fare + tip + 0.50, 2),
                "payment_type": random.choice(PAYMENT),
            }
        )

    return rows


def write_rows(rows, output_path):
    """
    Writes the generated rows to a CSV file, creating parent directories.

    Args:
        rows (list): The trip records to write.
        output_path (str or pathlib.Path): The CSV file to write.

    Returns:
        pathlib.Path: The file that was written.
    """
    output_path = pathlib.Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    return output_path


def main(argv=None):
    """CLI entry point — generates the raw sample dataset."""
    parser = argparse.ArgumentParser(
        description="Generate the synthetic NYC taxi sample."
    )
    parser.add_argument("--output-path", type=pathlib.Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--rows", type=int, default=10_000)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args(argv)

    written = write_rows(build_rows(args.rows, args.seed), args.output_path)
    logger.info(f"Dataset written: {written} ({args.rows:,} rows)")
    return written


if __name__ == "__main__":
    main()
