import os
import sys
import logging
import pandas as pd
import numpy as np
from pathlib import Path

def load_gss_data_subset(url: str, output_path: str) -> None:
    """Downloads GSS data from a URL and saves it to a CSV file.

    Args:
        url (str): The URL of the GSS data.
        output_path (str): The path to save the downloaded data.
    """
    try:
        df = pd.read_csv(url)
        df.to_csv(output_path, index=False)
        logging.info(f"Successfully downloaded and saved GSS data to {output_path}")
    except Exception as e:
        logging.error(f"Error downloading or saving GSS data: {e}")
        raise

def ensure_design_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Checks for the presence of 'weight', 'psu', and 'strata' columns in a DataFrame.

    Args:
        df (pd.DataFrame): The input DataFrame.

    Returns:
        pd.DataFrame: The DataFrame if all required columns are present.  Raises an error otherwise.
    """
    required_columns = ['weight', 'psu', 'strata']
    missing_columns = [col for col in required_columns if col not in df.columns]

    if missing_columns:
        raise ValueError(f"Required columns are missing: {missing_columns}")

    return df

def detect_missingness(df: pd.DataFrame, threshold: float = 0.3) -> List[str]:
    """Detects variables with a high percentage of missing values.

    Args:
        df (pd.DataFrame): The input DataFrame.
        threshold (float): The maximum allowed proportion of missing values.

    Returns:
        List[str]: A list of variable names with more than the threshold of missing values.
    """
    missing_variables = []
    for col in df.columns:
        if df[col].isnull().sum() / len(df) > threshold:
            missing_variables.append(col)
    return missing_variables

def ingest_and_save(url: str, output_path: str) -> None:
    """Downloads data, ensures required columns exist, and saves the data to a file."""
    try:
        df = load_gss_data_subset(url, output_path)
        df = ensure_design_columns(df)
        logging.info("Data ingestion successful.")

    except Exception as e:
        logging.error(f"Data ingestion failed: {e}")
        raise

def main():
    """Main function to run the data ingestion process."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    gss_url = "https://raw.githubusercontent.com/gdellavedova/llmXive/main/data/raw/gss2018_subset.csv" # Replace with the actual URL
    output_path = "data/raw/gss_2018_subset.csv"

    try:
        ingest_and_save(gss_url, output_path)
    except Exception as e:
        logging.error(f"Data ingestion failed: {e}")
        sys.exit(1)  # Exit with an error code


if __name__ == "__main__":
    main()