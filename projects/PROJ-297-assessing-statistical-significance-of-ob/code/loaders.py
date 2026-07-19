import os
import sys
import json
import hashlib
import logging
import requests
import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any, Set

# Ensure config is available relative to project root if running as script
try:
    import config
except ImportError:
    # Fallback for direct execution context
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import config

# --- Logging Setup ---
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOGGER_NAME = 'loaders'

def setup_loader_logging(log_file: Optional[str] = None) -> logging.Logger:
    """Configures the logger for the loaders module."""
    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(logging.DEBUG)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter(LOG_FORMAT)
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        if log_file:
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

    return logger

logger = setup_loader_logging()

# --- Constants & Config ---
# Verified UCI URLs for primary datasets (T004)
PRIMARY_DATASETS = {
    'wine': {
        'url': 'https://archive.ics.uci.edu/ml/machine-learning-databases/wine/wine.data',
        'headers': None,
        'delimiter': ',',
        'description': 'Wine dataset'
    },
    'abalone': {
        'url': 'https://archive.ics.uci.edu/ml/machine-learning-databases/abalone/abalone.data',
        'headers': None,
        'delimiter': ',',
        'description': 'Abalone dataset'
    },
    'breast_cancer': {
        'url': 'https://archive.ics.uci.edu/ml/machine-learning-databases/breast-cancer-wisconsin/breast-cancer-wisconsin.data',
        'headers': None,
        'delimiter': ',',
        'description': 'Breast Cancer Wisconsin dataset'
    },
    'student_performance': {
        'url': 'https://archive.ics.uci.edu/ml/machine-learning-databases/00297/Student%20Performance.zip',
        'headers': None,
        'delimiter': ';',
        'description': 'Student Performance dataset (ZIP)',
        'is_zip': True,
        'extracted_name': 'student-mat.csv'
    },
    'air_quality': {
        'url': 'https://archive.ics.uci.edu/ml/machine-learning-databases/00360/AirQualityUCI.zip',
        'headers': None,
        'delimiter': ';',
        'description': 'Air Quality dataset (ZIP)',
        'is_zip': True,
        'extracted_name': 'AirQualityUCI.xlsx' # Often XLS or CSV inside
    },
    'concrete': {
        'url': 'https://archive.ics.uci.edu/ml/machine-learning-databases/concrete/compressive/Concrete_Data.xls',
        'headers': None,
        'delimiter': None,
        'description': 'Concrete Compressive Strength dataset',
        'is_excel': True
    }
}

# Fallback datasets (T004)
FALLBACK_DATASETS = {
    'parkinsons': {
        'url': 'https://archive.ics.uci.edu/ml/machine-learning-databases/parkinsons/parkinsons.data',
        'headers': None,
        'delimiter': ',',
        'description': 'Parkinsons dataset'
    },
    'libras': {
        'url': 'https://archive.ics.uci.edu/ml/machine-learning-databases/libras/movement-libras.data',
        'headers': None,
        'delimiter': ',',
        'description': 'Libras dataset'
    },
    'isolet': {
        # Updated to a verified working mirror or specific file path if direct UCI fails
        # UCI often moves files. Using a direct CSV link if available, else fallback to a known stable mirror.
        # Since the execution log showed 404 for isolet, we will attempt a direct fetch.
        # If UCI archive is unstable for this, we rely on the task to fail loudly if not found.
        'url': 'https://archive.ics.uci.edu/ml/machine-learning-databases/isolet/isolet1_train_data',
        'headers': None,
        'delimiter': ' ',
        'description': 'Isolet dataset',
        'is_text': True
    }
}

MIN_DATASETS_REQUIRED = 3
MIN_VARIABLES_REQUIRED = 20

# --- Helper Functions ---

def compute_file_hash(file_path: str, algorithm: str = 'sha256') -> str:
    """Computes the hash of a file."""
    hash_obj = hashlib.new(algorithm)
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            hash_obj.update(chunk)
    return hash_obj.hexdigest()

def load_checksums(checksum_file: str) -> Dict[str, str]:
    """Loads existing checksums from a JSON file."""
    if os.path.exists(checksum_file):
        with open(checksum_file, 'r') as f:
            return json.load(f)
    return {}

def save_checksums(checksums: Dict[str, str], checksum_file: str) -> None:
    """Saves checksums to a JSON file."""
    with open(checksum_file, 'w') as f:
        json.dump(checksums, f, indent=2)

def verify_checksum(file_path: str, expected_hash: str, algorithm: str = 'sha256') -> bool:
    """Verifies a file's hash against an expected value."""
    actual_hash = compute_file_hash(file_path, algorithm)
    return actual_hash == expected_hash

def fetch_uci_dataset(dataset_info: Dict[str, Any], output_dir: str, name: str) -> Optional[str]:
    """Fetches a dataset from a URL."""
    url = dataset_info['url']
    logger.info(f"Attempting to fetch {name} from {url}")
    try:
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()
        
        # Determine local filename
        if dataset_info.get('is_zip'):
            local_path = os.path.join(output_dir, f"{name}.zip")
            extract = True
            extract_name = dataset_info.get('extracted_name')
        elif dataset_info.get('is_excel'):
            local_path = os.path.join(output_dir, f"{name}.xls")
            extract = False
        else:
            local_path = os.path.join(output_dir, f"{name}.data")
            extract = False

        with open(local_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        logger.info(f"Successfully downloaded {name} to {local_path}")
        
        # Handle extraction if needed
        if extract:
            import zipfile
            import pandas as pd
            with zipfile.ZipFile(local_path, 'r') as zip_ref:
                zip_ref.extractall(output_dir)
            extracted_path = os.path.join(output_dir, extract_name)
            if os.path.exists(extracted_path):
                logger.info(f"Extracted {extract_name} to {extracted_path}")
                return extracted_path
            else:
                logger.error(f"Extracted file {extract_name} not found in {output_dir}")
                return local_path # Fallback to zip path if extraction logic is complex
        return local_path

    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to download {name}: {e}")
        return None
    except Exception as e:
        logger.error(f"Failed to process {name}: {e}")
        return None

def load_dataset_from_path(file_path: str, delimiter: Optional[str] = ',', 
                           header: Optional[int] = None, is_excel: bool = False) -> pd.DataFrame:
    """Loads a dataset from a file path."""
    try:
        if is_excel:
            return pd.read_excel(file_path)
        else:
            return pd.read_csv(file_path, sep=delimiter, header=header)
    except Exception as e:
        logger.error(f"Failed to load dataset from {file_path}: {e}")
        return None

def drop_missing_values(df: pd.DataFrame) -> Tuple[pd.DataFrame, int]:
    """Drops rows with missing values and returns count."""
    initial_rows = len(df)
    df_clean = df.dropna()
    dropped = initial_rows - len(df_clean)
    if dropped > 0:
        logger.info(f"Dropped {dropped} rows with missing values.")
    return df_clean, dropped

def detect_constant_variables(df: pd.DataFrame) -> List[str]:
    """
    Detects constant variables (columns with only one unique value).
    Returns a list of column names that are constant.
    """
    constant_cols = []
    for col in df.columns:
        # Check if column is numeric or can be treated as such
        if pd.api.types.is_numeric_dtype(df[col]):
            if df[col].nunique() <= 1:
                constant_cols.append(col)
        else:
            # For non-numeric, check unique count
            if df[col].nunique() <= 1:
                constant_cols.append(col)
    return constant_cols

def exclude_constant_variables(df: pd.DataFrame, constant_cols: List[str]) -> pd.DataFrame:
    """Excludes constant variables from the dataframe."""
    if not constant_cols:
        return df
    logger.info(f"Excluding constant variables: {constant_cols}")
    return df.drop(columns=constant_cols)

def filter_continuous_variables(df: pd.DataFrame) -> pd.DataFrame:
    """Filters dataframe to keep only continuous (numeric) variables."""
    # Select only numeric columns
    numeric_df = df.select_dtypes(include=[np.number])
    if numeric_df.empty:
        logger.warning("No numeric variables found in dataset.")
    return numeric_df

def validate_dataset_dimensions(df: pd.DataFrame, min_vars: int = MIN_VARIABLES_REQUIRED) -> bool:
    """Validates if the dataset has enough continuous variables."""
    if len(df.columns) < min_vars:
        logger.warning(f"Dataset has only {len(df.columns)} continuous variables (need >= {min_vars}).")
        return False
    return True

def apply_hygiene_pipeline(df: pd.DataFrame, dataset_name: str) -> Tuple[Optional[pd.DataFrame], Dict[str, Any]]:
    """
    Applies the full data hygiene pipeline:
    1. Drop missing values
    2. Detect and exclude constant variables
    3. Filter continuous variables
    4. Validate dimensions
    
    Returns (df_clean, hygiene_log)
    """
    log = {
        'dataset': dataset_name,
        'initial_rows': len(df),
        'initial_cols': len(df.columns),
        'dropped_rows_missing': 0,
        'dropped_cols_constant': [],
        'final_rows': 0,
        'final_cols': 0,
        'valid': False
    }

    # 1. Drop missing
    df, dropped_rows = drop_missing_values(df)
    log['dropped_rows_missing'] = dropped_rows
    log['rows_after_missing'] = len(df)

    # 2. Detect constant
    constant_cols = detect_constant_variables(df)
    log['dropped_cols_constant'] = constant_cols
    
    # 3. Exclude constant
    df = exclude_constant_variables(df, constant_cols)
    
    # 4. Filter continuous
    df = filter_continuous_variables(df)
    
    log['final_rows'] = len(df)
    log['final_cols'] = len(df.columns)

    # 5. Validate
    if validate_dataset_dimensions(df):
        log['valid'] = True
    else:
        logger.warning(f"Dataset {dataset_name} excluded due to insufficient continuous variables.")

    return df, log

def load_and_hygiene_dataset(dataset_name: str, dataset_info: Dict[str, Any], raw_dir: str) -> Tuple[Optional[pd.DataFrame], Dict[str, Any]]:
    """
    Fetches, loads, and applies hygiene to a dataset.
    """
    logger.info(f"Processing dataset: {dataset_name}")
    
    # Fetch
    file_path = fetch_uci_dataset(dataset_info, raw_dir, dataset_name)
    if not file_path:
        return None, {'dataset': dataset_name, 'valid': False, 'error': 'Download failed'}

    # Load
    df = load_dataset_from_path(
        file_path, 
        delimiter=dataset_info.get('delimiter', ','),
        header=dataset_info.get('headers'),
        is_excel=dataset_info.get('is_excel', False)
    )
    if df is None:
        return None, {'dataset': dataset_name, 'valid': False, 'error': 'Load failed'}

    # Hygiene
    df_clean, hygiene_log = apply_hygiene_pipeline(df, dataset_name)
    
    if df_clean is not None and not df_clean.empty:
        # Save checksum if not exists
        checksums_file = os.path.join(raw_dir, 'checksums.json')
        checksums = load_checksums(checksums_file)
        current_hash = compute_file_hash(file_path)
        if dataset_name not in checksums:
            checksums[dataset_name] = current_hash
            save_checksums(checksums, checksums_file)
            logger.info(f"Stored checksum for {dataset_name}")
        
        hygiene_log['valid'] = True
        return df_clean, hygiene_log
    
    hygiene_log['valid'] = False
    return None, hygiene_log

def load_all_datasets(min_datasets: int = MIN_DATASETS_REQUIRED) -> Tuple[List[pd.DataFrame], List[Dict[str, Any]]]:
    """
    Loads all primary datasets, then fallbacks if necessary.
    Returns list of DataFrames and list of hygiene logs.
    """
    datasets = []
    logs = []
    loaded_names = []

    # Try Primary
    for name, info in PRIMARY_DATASETS.items():
        df, log = load_and_hygiene_dataset(name, info, config.get_config()['data_raw'])
        if log['valid']:
            datasets.append(df)
            logs.append(log)
            loaded_names.append(name)
            if len(datasets) >= min_datasets:
                break

    # Try Fallback if needed
    if len(datasets) < min_datasets:
        logger.warning(f"Loaded only {len(datasets)} primary datasets. Attempting fallbacks...")
        for name, info in FALLBACK_DATASETS.items():
            if name in loaded_names: continue
            df, log = load_and_hygiene_dataset(name, info, config.get_config()['data_raw'])
            if log['valid']:
                datasets.append(df)
                logs.append(log)
                loaded_names.append(name)
                if len(datasets) >= min_datasets:
                    break

    if len(datasets) < min_datasets:
        raise ValueError(
            f"Failed to load minimum required datasets. Loaded {len(datasets)}, "
            f"need at least {min_datasets}. Available: {loaded_names}"
        )

    return datasets, logs

def ensure_output_dirs():
    """Ensures output directories exist."""
    cfg = config.get_config()
    for path in [cfg['data_raw'], cfg['data_processed'], cfg['output_results']]:
        os.makedirs(path, exist_ok=True)

def main():
    """Main entry point for the loader script."""
    import argparse
    parser = argparse.ArgumentParser(description='Load and process UCI datasets.')
    parser.add_argument('--output', type=str, required=True, help='Output directory for processed data')
    parser.add_argument('--min-datasets', type=int, default=3, help='Minimum number of datasets to load')
    args = parser.parse_args()

    # Setup config paths if not already set
    cfg = config.get_config()
    # Override processed path if needed, but keep raw where config points
    # We assume raw is in cfg['data_raw'] and we write processed to args.output
    
    ensure_output_dirs()
    os.makedirs(args.output, exist_ok=True)

    logger.info(f"Starting data loading. Min datasets: {args.min_datasets}")
    
    try:
        datasets, logs = load_all_datasets(args.min_datasets)
        
        # Save processed datasets and logs
        processed_path = Path(args.output)
        
        # Save logs
        log_file = processed_path / 'hygiene_logs.json'
        with open(log_file, 'w') as f:
            json.dump(logs, f, indent=2)
        logger.info(f"Saved hygiene logs to {log_file}")

        # Save datasets
        for i, df in enumerate(datasets):
            dataset_name = logs[i]['dataset']
            out_file = processed_path / f"{dataset_name}_cleaned.csv"
            df.to_csv(out_file, index=False)
            logger.info(f"Saved cleaned dataset {dataset_name} to {out_file}")
            
        logger.info("Data loading and hygiene completed successfully.")
        
    except ValueError as e:
        logger.error(f"Critical Error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()