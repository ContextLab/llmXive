import os
import hashlib
import requests
import zipfile
import tempfile
import pandas as pd
from pathlib import Path
from typing import Dict, Optional, Tuple
from utils.logging_utils import log_warning

# Whitelist of allowed domains
ALLOWED_DOMAINS = [
    "archive.ics.uci.edu",
    "raw.githubusercontent.com",
    "github.com",
    "www.kaggle.com",
    "datahub.io"
]

def verify_domain(url: str) -> bool:
    """Verify that the URL domain is in the whitelist."""
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        return any(domain in parsed.netloc for domain in ALLOWED_DOMAINS)
    except Exception:
        return False

def check_url_status(url: str) -> Tuple[bool, int]:
    """Check if URL returns HTTP 200."""
    try:
        response = requests.head(url, timeout=10, allow_redirects=True)
        return response.status_code == 200, response.status_code
    except Exception as e:
        log_warning(f"URL check failed for {url}: {str(e)}")
        return False, 0

def download_file(url: str, destination: Path) -> bool:
    """Download a file from URL to destination path."""
    if not verify_domain(url):
        raise ValueError(f"Domain not allowed: {url}")
    
    is_available, status = check_url_status(url)
    if not is_available:
        raise ConnectionError(f"URL not available (status {status}): {url}")
    
    try:
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()
        
        with open(destination, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        return True
    except Exception as e:
        log_warning(f"Download failed for {url}: {str(e)}")
        return False

def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def get_dataset_info(dataset_name: str) -> Dict:
    """Get metadata for a dataset including URL and expected characteristics."""
    # Note: Checksums are calculated dynamically, not hardcoded
    info = {
        "adult": {
            "name": "UCI Adult",
            "url": "https://archive.ics.uci.edu/ml/machine-learning-databases/adult/adult.data",
            "description": "Income prediction dataset",
            "protected_attr": "sex",
            "outcome": "income"
        },
        "compas": {
            "name": "COMPAS",
            "url": "https://raw.githubusercontent.com/propublica/compas-analysis/master/compas-scores-two-years.csv",
            "description": "Recidivism prediction dataset",
            "protected_attr": "race",
            "outcome": "two_year_recid"
        },
        "bank": {
            "name": "Bank Marketing",
            "url": "https://archive.ics.uci.edu/ml/machine-learning-databases/datasets/bank/bank-full.csv",
            "description": "Bank marketing campaign dataset",
            "protected_attr": "age", 
            "outcome": "y"
        },
        "german": {
            "name": "German Credit",
            "url": "https://archive.ics.uci.edu/ml/machine-learning-databases/statlog/german/german.data",
            "description": "Credit risk dataset",
            "protected_attr": "sex",
            "outcome": "class"
        },
        "lawschool": {
            "name": "Law School Admission",
            "url": "https://raw.githubusercontent.com/richie0866/lawschool/main/gss_data.csv",
            "description": "Law school performance dataset",
            "protected_attr": "race",
            "outcome": "grad"
        }
    }
    return info.get(dataset_name, {})

def load_adult() -> Optional[pd.DataFrame]:
    """Load UCI Adult dataset."""
    try:
        url = "https://archive.ics.uci.edu/ml/machine-learning-databases/adult/adult.data"
        df = pd.read_csv(url, header=None, names=[
            'age', 'workclass', 'fnlwgt', 'education', 'education-num',
            'marital-status', 'occupation', 'relationship', 'race', 'sex',
            'capital-gain', 'capital-loss', 'hours-per-week', 'native-country', 'income'
        ], sep=', ', skipinitialspace=True)
        return df
    except Exception as e:
        log_warning(f"Failed to load Adult dataset: {str(e)}")
        return None

def load_compas() -> Optional[pd.DataFrame]:
    """Load COMPAS dataset."""
    try:
        url = "https://raw.githubusercontent.com/propublica/compas-analysis/master/compas-scores-two-years.csv"
        df = pd.read_csv(url)
        return df
    except Exception as e:
        log_warning(f"Failed to load COMPAS dataset: {str(e)}")
        return None

def load_bank() -> Optional[pd.DataFrame]:
    """Load Bank Marketing dataset."""
    try:
        url = "https://archive.ics.uci.edu/ml/machine-learning-databases/datasets/bank/bank-full.csv"
        df = pd.read_csv(url, sep=';')
        return df
    except Exception as e:
        log_warning(f"Failed to load Bank dataset: {str(e)}")
        return None

def load_german() -> Optional[pd.DataFrame]:
    """Load German Credit dataset."""
    try:
        url = "https://archive.ics.uci.edu/ml/machine-learning-databases/statlog/german/german.data"
        # German credit data has no header
        df = pd.read_csv(url, delim_whitespace=True, header=None)
        # Assign generic column names
        df.columns = [f'col_{i}' for i in range(len(df.columns))]
        return df
    except Exception as e:
        log_warning(f"Failed to load German Credit dataset: {str(e)}")
        return None

def load_lawschool() -> Optional[pd.DataFrame]:
    """Load Law School Admission dataset."""
    try:
        url = "https://raw.githubusercontent.com/richie0866/lawschool/main/gss_data.csv"
        df = pd.read_csv(url)
        return df
    except Exception as e:
        log_warning(f"Failed to load Law School dataset: {str(e)}")
        return None

def load_all_datasets() -> Dict[str, pd.DataFrame]:
    """Load all datasets and return as a dictionary."""
    datasets = {}
    for name in ["adult", "compas", "bank", "german", "lawschool"]:
        loader_map = {
            "adult": load_adult,
            "compas": load_compas,
            "bank": load_bank,
            "german": load_german,
            "lawschool": load_lawschool
        }
        df = loader_map[name]()
        if df is not None:
            datasets[name] = df
        else:
            log_warning(f"Skipping {name} due to load failure")
    return datasets
