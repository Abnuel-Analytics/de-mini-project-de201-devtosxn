"""
Name: test_extract.py
Description: Unit tests for src/extract.py.
Author: Abiodun Akinyemi
Modified by: Tosin Ayodele
Update date: 2026-08-29
"""

import pytest
from src.extract import extract_data_from_file


def test_extract_data_from_csv(test_data_dir):
    # Test extracting data from a CSV file
    data = extract_data_from_file(test_data_dir / "test_data.csv", "csv")
    assert not data.empty, "Data extracted from CSV should not be empty"


def test_extract_data_from_parquet(test_data_dir):
    # Test extracting data from a parquet file
    data = extract_data_from_file(test_data_dir / "test_data.parquet", "parquet")
    assert not data.empty, "Data extracted from parquet should not be empty"


def test_extract_data_from_json(test_data_dir):
    # Test extracting data from a JSON file
    data = extract_data_from_file(test_data_dir / "test_data.json", "json")
    assert not data.empty, "Data extracted from JSON should not be empty"


def test_extract_data_rejects_unsupported_file_type(test_data_dir):
    with pytest.raises(ValueError, match="Unsupported file type"):
        extract_data_from_file(test_data_dir / "test_data.csv", "xlsx")
