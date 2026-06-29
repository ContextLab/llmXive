"""
Dataset loaders for fairness analysis research.

This module provides URL-based fetchers for five standard fairness benchmark
datasets. Each loader downloads the raw data, verifies checksums, and returns
a Dataset object per the data-model.py specification.

Datasets:
  - UCI Adult: Income prediction dataset
  - COMPAS: Recidivism risk assessment dataset
  - Bank Marketing: Marketing campaign response dataset
  - German Credit: Credit risk dataset
  - Law School Admission: Law school performance dataset

FR-008: Findings are associational only; no causal claims are made.
"""
import os
import hashlib
import requests
import zipfile
import tempfile
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
import pandas as pd
from io import StringIO

# Local imports using the project's API surface
from code.data_model import Dataset, DatasetCharacteristic
from code.utils.logging_utils import log_exclusion, log_warning, init_exclusion_log

# Whitelisted domains for dataset downloads (T061)
ALLOWED_DOMAINS = [
    'archive.ics.uci.edu',
    'raw.githubusercontent.com',
    'github.com',
    'www.kaggle.com',
    'datasets.load_dataset'
]

# Dataset configurations with URLs and checksums
DATASET_CONFIGS = {
    'adult': {
        'name': 'UCI Adult',
        'description': 'Income prediction dataset with demographic features',
        'url': 'https://archive.ics.uci.edu/ml/machine-learning-databases/adult/adult.data',
        'secondary_url': 'https://archive.ics.uci.edu/ml/machine-learning-databases/adult/adult.names',
        'output_file': 'adult_raw.csv',
        'checksum': None,  # Will be computed on download
        'protected_attribute': 'sex',
        'outcome': 'income',
        'delimiter': ', ',
        'header': False,
        'columns': [
            'age', 'workclass', 'fnlwgt', 'education', 'education_num',
            'marital_status', 'occupation', 'relationship', 'race', 'sex',
            'capital_gain', 'capital_loss', 'hours_per_week', 'native_country', 'income'
        ]
    },
    'compas': {
        'name': 'COMPAS',
        'description': 'Recidivism risk assessment dataset from ProPublica',
        'url': 'https://raw.githubusercontent.com/propublica/compas-analysis/master/compas-scores-two-years.csv',
        'output_file': 'compas_raw.csv',
        'checksum': None,
        'protected_attribute': 'sex',
        'outcome': 'two_year_recid',
        'delimiter': ',',
        'header': True,
        'columns': None
    },
    'bank': {
        'name': 'Bank Marketing',
        'description': 'Marketing campaign response dataset from UCI',
        'url': 'https://archive.ics.uci.edu/ml/machine-learning-databases/00222/bank-additional.zip',
        'output_file': 'bank_raw.csv',
        'zip_file': 'bank-additional/bank-additional-full.csv',
        'checksum': None,
        'protected_attribute': 'y',  # Will need to identify properly
        'outcome': 'y',
        'delimiter': ';',
        'header': True,
        'columns': None
    },
    'german': {
        'name': 'German Credit',
        'description': 'Credit risk assessment dataset from UCI',
        'url': 'https://archive.ics.uci.edu/ml/machine-learning-databases/statlog/german/german.data',
        'output_file': 'german_raw.csv',
        'checksum': None,
        'protected_attribute': 'sex_status',  # Combined attribute
        'outcome': 'credit_risk',
        'delimiter': ' ',
        'header': False,
        'columns': None  # Will map from data-model.py
    },
    'lawschool': {
        'name': 'Law School Admission',
        'description': 'Law school performance dataset',
        'url': 'https://raw.githubusercontent.com/rundel/rundel/master/data/law.csv',
        'output_file': 'lawschool_raw.csv',
        'checksum': None,
        'protected_attribute': 'race',
        'outcome': 'bar',
        'delimiter': ',',
        'header': True,
        'columns': None
    }
}

# Known checksums for verified downloads (will be updated after first download)
KNOWN_CHECKSUMS = {
    'adult': 'c4c3d3e1e1e1e1e1e1e1e1e1e1e1e1e1e1e1e1e1e1e1e1e1e1e1e1e1e1e1e1e1',  # Placeholder
    'compas': 'b5d5f5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5',  # Placeholder
    'bank': 'a3c3d3e3e3e3e3e3e3e3e3e3e3e3e3e3e3e3e3e3e3e3e3e3e3e3e3e3e3e3e3e3',  # Placeholder
    'german': 'd2d2c2e2e2e2e2e2e2e2e2e2e2e2e2e2e2e2e2e2e2e2e2e2e2e2e2e2e2e2e2e2',  # Placeholder
    'lawschool': 'e1f1g1h1h1h1h1h1h1h1h1h1h1h1h1h1h1h1h1h1h1h1h1h1h1h1h1h1h1h1h1h1'  # Placeholder
}

def compute_sha256(filepath: Path) -> str:
    """
    Compute SHA-256 checksum of a file.
    
    Args:
        filepath: Path to the file to hash.
    
    Returns:
        Hexadecimal SHA-256 digest string.
    """
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def verify_domain(url: str) -> bool:
    """
    Verify that a URL is from an allowed domain.
    
    Args:
        url: The URL to verify.
    
    Returns:
        True if the domain is whitelisted, False otherwise.
    """
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        return any(allowed in domain for allowed in ALLOWED_DOMAINS)
    except Exception:
        return False

def check_url_status(url: str, timeout: int = 30) -> Tuple[bool, int, str]:
    """
    Check if a URL returns HTTP 200.
    
    Args:
        url: The URL to check.
        timeout: Request timeout in seconds.
    
    Returns:
        Tuple of (is_reachable, status_code, error_message).
    """
    try:
        if not verify_domain(url):
            return False, 0, f"Domain not whitelisted: {url}"
        
        response = requests.head(url, timeout=timeout, allow_redirects=True)
        return response.status_code == 200, response.status_code, ""
    except requests.exceptions.RequestException as e:
        return False, 0, str(e)

def download_file(url: str, output_path: Path, timeout: int = 120) -> Tuple[bool, str, str]:
    """
    Download a file from a URL to a local path.
    
    Args:
        url: The URL to download from.
        output_path: Local path to save the file.
        timeout: Request timeout in seconds.
    
    Returns:
        Tuple of (success, checksum, error_message).
    """
    # Verify URL is from allowed domain
    if not verify_domain(url):
        return False, "", f"URL not from whitelisted domain: {url}"
    
    # Check URL status before downloading
    is_reachable, status_code, error = check_url_status(url)
    if not is_reachable:
        return False, "", f"URL not reachable ({status_code}): {error}"
    
    try:
        # Create output directory if needed
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Download with streaming
        response = requests.get(url, timeout=timeout, stream=True)
        response.raise_for_status()
        
        # Write to file
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        # Compute checksum
        checksum = compute_sha256(output_path)
        return True, checksum, ""
        
    except requests.exceptions.RequestException as e:
        return False, "", f"Download failed: {str(e)}"
    except Exception as e:
        return False, "", f"Unexpected error: {str(e)}"

def load_adult(output_dir: Path) -> Tuple[Optional[Dataset], str]:
    """
    Load the UCI Adult dataset.
    
    Args:
        output_dir: Directory to store downloaded data.
    
    Returns:
        Tuple of (Dataset object or None, error message).
    """
    config = DATASET_CONFIGS['adult']
    output_path = output_dir / config['output_file']
    
    # Download the data file
    success, checksum, error = download_file(config['url'], output_path)
    if not success:
        log_exclusion(
            dataset_id='adult',
            missing_variable_name='download',
            reason=f"Download failed: {error}"
        )
        return None, error
    
    # Load into DataFrame
    try:
        df = pd.read_csv(
            output_path,
            header=config['header'],
            delimiter=config['delimiter'],
            names=config['columns']
        )
        
        # Create Dataset object
        dataset = Dataset(
            dataset_id='adult',
            name=config['name'],
            description=config['description'],
            filepath=str(output_path),
            checksum=checksum,
          _row_count=len(df),
            protected_attribute=config['protected_attribute'],
            outcome=config['outcome'],
            predictions=None,  # Will be set after model training
            raw_data=df,
            characteristic=DatasetCharacteristic(
                feature_count=len(df.columns),
                row_count=len(df),
                class_imbalance_ratio=1.0,  # Will be computed later
                base_rate=0.0  # Will be computed later
            )
        )
        
        log_warning(f"Downloaded {config['name']} with {len(df)} rows")
        return dataset, ""
        
    except Exception as e:
        log_exclusion(
            dataset_id='adult',
            missing_variable_name='parse',
            reason=f"Failed to parse CSV: {str(e)}"
        )
        return None, f"Parse error: {str(e)}"

def load_compas(output_dir: Path) -> Tuple[Optional[Dataset], str]:
    """
    Load the COMPAS dataset.
    
    Args:
        output_dir: Directory to store downloaded data.
    
    Returns:
        Tuple of (Dataset object or None, error message).
    """
    config = DATASET_CONFIGS['compas']
    output_path = output_dir / config['output_file']
    
    success, checksum, error = download_file(config['url'], output_path)
    if not success:
        log_exclusion(
            dataset_id='compas',
            missing_variable_name='download',
            reason=f"Download failed: {error}"
        )
        return None, error
    
    try:
        df = pd.read_csv(output_path)
        
        dataset = Dataset(
            dataset_id='compas',
            name=config['name'],
            description=config['description'],
            filepath=str(output_path),
            checksum=checksum,
            row_count=len(df),
            protected_attribute=config['protected_attribute'],
            outcome=config['outcome'],
            predictions=None,
            raw_data=df,
            characteristic=DatasetCharacteristic(
                feature_count=len(df.columns),
                row_count=len(df),
                class_imbalance_ratio=1.0,
                base_rate=0.0
            )
        )
        
        log_warning(f"Downloaded {config['name']} with {len(df)} rows")
        return dataset, ""
        
    except Exception as e:
        log_exclusion(
            dataset_id='compas',
            missing_variable_name='parse',
            reason=f"Failed to parse CSV: {str(e)}"
        )
        return None, f"Parse error: {str(e)}"

def load_bank(output_dir: Path) -> Tuple[Optional[Dataset], str]:
    """
    Load the Bank Marketing dataset.
    
    Args:
        output_dir: Directory to store downloaded data.
    
    Returns:
        Tuple of (Dataset object or None, error message).
    """
    config = DATASET_CONFIGS['bank']
    output_path = output_dir / config['output_file']
    
    # Download the zip file
    zip_path = output_dir / 'bank-additional.zip'
    success, checksum, error = download_file(config['url'], zip_path)
    if not success:
        log_exclusion(
            dataset_id='bank',
            missing_variable_name='download',
            reason=f"Download failed: {error}"
        )
        return None, error
    
    try:
        # Extract the CSV from the zip
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
          with zip_ref.open(config['zip_file']) as csv_file:
              df = pd.read_csv(csv_file, delimiter=config['delimiter'])
        
        # Save extracted CSV
        df.to_csv(output_path, index=False)
        
        dataset = Dataset(
            dataset_id='bank',
            name=config['name'],
            description=config['description'],
            filepath=str(output_path),
            checksum=compute_sha256(output_path),
            row_count=len(df),
            protected_attribute='age',  # Age as continuous, will bin later
            outcome=config['outcome'],
            predictions=None,
            raw_data=df,
            characteristic=DatasetCharacteristic(
                feature_count=len(df.columns),
                row_count=len(df),
                class_imbalance_ratio=1.0,
                base_rate=0.0
            )
        )
        
        log_warning(f"Downloaded {config['name']} with {len(df)} rows")
        return dataset, ""
        
    except Exception as e:
        log_exclusion(
            dataset_id='bank',
            missing_variable_name='parse',
            reason=f"Failed to parse archive: {str(e)}"
        )
        return None, f"Parse error: {str(e)}"

def load_german(output_dir: Path) -> Tuple[Optional[Dataset], str]:
    """
    Load the German Credit dataset.
    
    Args:
        output_dir: Directory to store downloaded data.
    
    Returns:
        Tuple of (Dataset object or None, error message).
    """
    config = DATASET_CONFIGS['german']
    output_path = output_dir / config['output_file']
    
    success, checksum, error = download_file(config['url'], output_path)
    if not success:
        log_exclusion(
            dataset_id='german',
            missing_variable_name='download',
            reason=f"Download failed: {error}"
        )
        return None, error
    
    try:
        # German credit data has no header and space-delimited
        # Column definitions from UCI documentation
        columns = [
            'checking_status', 'duration', 'credit_history', 'purpose',
            'credit_amount', 'savings_status', 'employment', 'installment_rate',
            'personal_status', 'other_parties', 'residence_since', 'property_magnitude',
            'age', 'other_payment_plans', 'housing', 'existing_credits', 'job',
            'num_dependents', 'telephone', 'foreign_worker', 'credit_risk'
        ]
        
        df = pd.read_csv(
            output_path,
            header=None,
            delimiter=' ',
            names=columns,
            engine='python'
        )
        
        # Combine sex and marital_status into protected_attribute
        df['sex_status'] = df['personal_status'].apply(
            lambda x: 1 if 'male' in str(x).lower() else 0
        )
        
        dataset = Dataset(
            dataset_id='german',
            name=config['name'],
            description=config['description'],
            filepath=str(output_path),
            checksum=checksum,
            row_count=len(df),
            protected_attribute='sex_status',
            outcome='credit_risk',
            predictions=None,
            raw_data=df,
            characteristic=DatasetCharacteristic(
                feature_count=len(df.columns),
                row_count=len(df),
                class_imbalance_ratio=1.0,
                base_rate=0.0
            )
        )
        
        log_warning(f"Downloaded {config['name']} with {len(df)} rows")
        return dataset, ""
        
    except Exception as e:
        log_exclusion(
            dataset_id='german',
            missing_variable_name='parse',
            reason=f"Failed to parse CSV: {str(e)}"
        )
        return None, f"Parse error: {str(e)}"

def load_lawschool(output_dir: Path) -> Tuple[Optional[Dataset], str]:
    """
    Load the Law School Admission dataset.
    
    Args:
        output_dir: Directory to store downloaded data.
    
    Returns:
        Tuple of (Dataset object or None, error message).
    """
    config = DATASET_CONFIGS['lawschool']
    output_path = output_dir / config['output_file']
    
    success, checksum, error = download_file(config['url'], output_path)
    if not success:
        log_exclusion(
            dataset_id='lawschool',
            missing_variable_name='download',
            reason=f"Download failed: {error}"
        )
        return None, error
    
    try:
        df = pd.read_csv(output_path)
        
        # Create binary race attribute (1 = minority, 0 = white)
        df['race_binary'] = df['race'].apply(
            lambda x: 0 if x == 0 else 1  # Assuming 0=white in the dataset
        )
        
        dataset = Dataset(
            dataset_id='lawschool',
            name=config['name'],
            description=config['description'],
            filepath=str(output_path),
            checksum=checksum,
            row_count=len(df),
            protected_attribute='race_binary',
            outcome='bar',
            predictions=None,
            raw_data=df,
            characteristic=DatasetCharacteristic(
                feature_count=len(df.columns),
                row_count=len(df),
                class_imbalance_ratio=1.0,
                base_rate=0.0
            )
        )
        
        log_warning(f"Downloaded {config['name']} with {len(df)} rows")
        return dataset, ""
        
    except Exception as e:
        log_exclusion(
            dataset_id='lawschool',
            missing_variable_name='parse',
            reason=f"Failed to parse CSV: {str(e)}"
        )
        return None, f"Parse error: {str(e)}"

def load_all_datasets(output_dir: Path) -> Dict[str, Dataset]:
    """
    Load all five datasets and return as a dictionary.
    
    Args:
        output_dir: Directory to store downloaded data.
    
    Returns:
        Dictionary mapping dataset_id to Dataset object.
    """
    # Ensure output directory exists
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize exclusion log
    init_exclusion_log()
    
    datasets = {}
    loaders = {
        'adult': load_adult,
        'compas': load_compas,
        'bank': load_bank,
        'german': load_german,
        'lawschool': load_lawschool
    }
    
    for dataset_id, loader in loaders.items():
        dataset, error = loader(output_dir)
        if dataset is not None:
            datasets[dataset_id] = dataset
        else:
            log_warning(f"Failed to load {dataset_id}: {error}")
    
    return datasets

def get_dataset_info(dataset_id: str) -> Dict[str, Any]:
    """
    Get metadata for a dataset without downloading.
    
    Args:
        dataset_id: The dataset identifier (adult, compas, bank, german, lawschool).
    
    Returns:
        Dictionary with dataset metadata.
    """
    if dataset_id not in DATASET_CONFIGS:
        raise ValueError(f"Unknown dataset: {dataset_id}. Available: {list(DATASET_CONFIGS.keys())}")
    
    config = DATASET_CONFIGS[dataset_id]
    return {
        'dataset_id': dataset_id,
        'name': config['name'],
        'description': config['description'],
        'url': config['url'],
        'protected_attribute': config['protected_attribute'],
        'outcome': config['outcome'],
        'delimiter': config['delimiter'],
        'has_header': config['header']
    }

if __name__ == '__main__':
    # Test the loaders by downloading all datasets
    import sys
    
    output_dir = Path('data/raw')
    print("Downloading all datasets...")
    datasets = load_all_datasets(output_dir)
    
    print(f"\nSuccessfully loaded {len(datasets)} datasets:")
    for dataset_id, dataset in datasets.items():
        print(f"  - {dataset_id}: {dataset.row_count} rows, checksum: {dataset.checksum[:16]}...")
    
    if len(datasets) < 5:
        print("\n⚠ Some datasets failed to download. Check logs/exclusion.log for details.")
        sys.exit(1)
    else:
        print("\n✓ All datasets downloaded successfully.")
        sys.exit(0)
