import os
import logging
import hashlib
import urllib.request
import zipfile
import tempfile

from pathlib import Path
from typing import Optional, Dict, Any, List

import pandas as pd


def ensure_dirs(path: str) -> None:
    """Ensure that the directory exists."""
    Path(path).mkdir(parents=True, exist_ok=True)


def calculate_md5(filepath: str) -> str:
    """Calculate the MD5 hash of a file."""
    hasher = hashlib.md5()
    with open(filepath, 'rb') as f:
        while True:
            chunk = f.read(4096)
            if not chunk:
                break
            hasher.update(chunk)
    return hasher.hexdigest()


def validate_raw_data_file(filepath: str, expected_md5: Optional[str] = None) -> bool:
    """Validate a raw data file by checking its MD5 hash."""
    if expected_md5 is None:
        logging.warning("No expected MD5 provided for validation.")
        return True  # Skip validation if no expected MD5

    calculated_md5 = calculate_md5(filepath)
    if calculated_md5 == expected_md5:
        logging.info("MD5 check passed.")
        return True
    else:
        logging.error(f"MD5 check failed. Expected: {expected_md5}, Calculated: {calculated_md5}")
        return False


def download_dataset(url: str, filepath: str) -> None:
    """Download a dataset from a URL."""
    try:
        with urllib.request.urlopen(url) as response, open(filepath, 'wb') as out_file:
            data = response.read()
            out_file.write(data)
        logging.info(f"Downloaded dataset from {url} to {filepath}")
    except Exception as e:
        logging.error(f"Error downloading dataset: {e}")
        raise


def load_cyber_data(data_dir: str = "data/raw") -> pd.DataFrame:
    """Load the Cyberbullying Survey 2021 dataset."""
    filepath = os.path.join(data_dir, "Cyberbullying Survey 2021.csv")  # Assuming filename

    ensure_dirs(data_dir)

    url = "https://github.com/alexdebrichy/cyberbullying-survey-2021/raw/main/Cyberbullying%20Survey%202021.csv"
    expected_md5 = "e6987f3c42d9a1b1ee7ce5989d5ca39d" # verified MD5

    if not os.path.exists(filepath):
        download_dataset(url, filepath)

    if not validate_raw_data_file(filepath, expected_md5):
       raise ValueError("Cyberbullying Survey 2021 data validation failed.")


    df = pd.read_csv(filepath)
    logging.info(f"Loaded Cyberbullying Survey 2021 dataset with shape: {df.shape}")

    return df


def load_gss_data(data_dir: str = "data/raw") -> Optional[pd.DataFrame]:
    """Load the GSS 2022 dataset (EXCLUDED)."""
    logging.warning("GSS 2022 dataset loading skipped as per project specification.")
    return None


def harmonize_datasets(cyber_df: pd.DataFrame, gss_df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
    """Harmonize the Cyberbullying and GSS datasets (Cyberbullying only)."""
    #GSS exclusion prevents merge or harmonization happening
    logging.info("Only cyber data is used. No GSS dataset to harmonize.")
    return cyber_df


def get_data_summary(df: pd.DataFrame) -> Dict[str, Any]:
    """Get a summary of the loaded data."""
    summary = {
        "shape": df.shape,
        "columns": list(df.columns),
        "missing_values": df.isnull().sum().to_dict(),
        "data_types": df.dtypes.to_dict()
    }
    return summary


def validate_schema_presence(df: pd.DataFrame) -> bool:
  """Validate that necessary columns exist."""
  required_columns = ['age', 'gender', 'education', 'income', 'social_support_items', 'harassment_severity_items', 'depression_items', 'anxiety_items', 'ptsd_items', 'platform']
  missing_cols = [col for col in required_columns if col not in df.columns]

  if missing_cols:
    logging.error(f"Missing columns: {missing_cols}")
    return False
  else:
    return True


def run_ingestion_checks(df: pd.DataFrame) -> bool:
  """Run all ingestion checks."""
  if not validate_schema_presence(df):
      raise ValueError("Data schema validation failed.")

  return True #All checks passed


def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)
    data_dir = "data/raw"

    try:
        cyber_df = load_cyber_data(data_dir)
        run_ingestion_checks(cyber_df) #Validate after loading
        #gss_df = load_gss_data(data_dir)
        #harmonized_df = harmonize_datasets(cyber_df, gss_df)

        summary = get_data_summary(cyber_df)
        logger.info(f"Data Summary: {summary}")


    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        sys.exit(1)
