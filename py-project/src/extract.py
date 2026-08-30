"""
Name: extract.py
Description: This module contains functions for extracting data from various sources.
Author: Abiodun Akinyemi
Modified by: Abiodun Akinyemi
Update date: 2026-08-22
"""

import logging

import pandas as pd
import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def extract_data_from_file(file_path, file_type, chunksize=None):
    """
    Extracts data from a CSV file or parquet or JSON file.

    Args:
        file_path (str): The path to the file.
        file_type (str): The type of the file (csv, parquet, json).
    Returns:
        pd.DataFrame: The extracted data.
    """
    if file_type == "csv":
        return pd.read_csv(file_path, encoding="utf-8", chunksize=chunksize)
    elif file_type == "parquet":
        return pd.read_parquet(file_path)
    elif file_type == "json":
        return pd.read_json(file_path, orient="records")
    else:
        raise ValueError("Unsupported file type")


# Include page number for pagination
def extract_data_from_api(api_url, params=None, page_number=None):
    """
    Extracts data from an API endpoint.

    Args:
        api_url (str): The URL of the API endpoint.
        params (dict, optional): The parameters to send with the request. Defaults to None.

    Returns:
        dict: The extracted data.
    """
    try:
        response = requests.get(api_url, params=params)
        response.raise_for_status()  # Raise an error for bad responses
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching data from API: {e}")
        raise
