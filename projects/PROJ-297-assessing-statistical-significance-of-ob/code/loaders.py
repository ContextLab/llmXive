import os
import json
import hashlib
import logging
import requests
import pandas as pd
import zipfile
import io
import tempfile
import openml
from typing import Optional, List, Dict, Tuple, Any

from config import get_dataset_registry

# Setup logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def setup_loader_logging():
    """Configure logging for the loader module."""
    # Logging is already configured at import time.
    pass

def get_logger():
    """Return the module logger."""
    return logger

def compute_file_hash(filepath: str, algorithm: str = 'sha256') -> str:
    """Compute the hash of a file."""
    hasher = hashlib.new(algorithm)
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hasher.update(chunk)
    return hasher.hexdigest()

def load_checksums(filepath: str) -> Dict[str, str]:
    """Load checksums from a JSON file."""
    if not os.path.exists(filepath):
        return {}
    with open(filepath, 'r') as f:
        return json.load(f)

def save_checksums(checksums: Dict[str, str], filepath: str):
    """Save checksums to a JSON file."""
    with open(filepath, 'w') as f:
        json.dump(checksums, f, indent=2)

def verify_checksum(filepath: str, expected_hash: str, algorithm: str = 'sha256') -> bool:
    """Verify the checksum of a file."""
    actual_hash = compute_file_hash(filepath, algorithm)
    return actual_hash == expected_hash

def fetch_file(url: str) -> bytes:
    """Download a file from a URL and return its raw bytes."""
    logger.info(f"Downloading from {url}")
    response = requests.get(url, timeout=60)
    response.raise_for_status()
    return response.content

def load_csv_from_bytes(content: bytes, delimiter: str = ',', header: bool = True) -> pd.DataFrame:
    """Load a CSV from raw bytes."""
    header_row = 0 if header else None
    return pd.read_csv(io.BytesIO(content), delimiter=delimiter,
                       header=header_row)

def load_excel_from_bytes(content: bytes) -> pd.DataFrame:
    """Load an Excel file from raw bytes."""
    return pd.read_excel(io.BytesIO(content))

def load_zip_and_extract(url: str, files: List[str]) -> List[pd.DataFrame]:
    """
    Download a zip archive, extract listed CSV files, and return them as DataFrames.
    Assumes all listed files are CSVs.
    """
    zip_bytes = fetch_file(url)
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as z:
        dataframes = []
        for fname in files:
            with z.open(fname) as f:
                df = pd.read_csv(f)
                dataframes.append(df)
        return dataframes

def process_registry_entry(entry: Dict[str, Any]) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Load a dataset defined in the config registry, apply hygiene, and return the
    cleaned DataFrame together with metadata.
    """
    name = entry.get('name', 'unknown')
    url = entry['url']
    fmt = entry.get('format', 'csv')
    delimiter = entry.get('delimiter', ',')
    has_header = entry.get('has_header', True)

    # Load raw DataFrame according to format
    if fmt == 'csv':
        content = fetch_file(url)
        df = load_csv_from_bytes(content, delimiter=delimiter, header=has_header)
    elif fmt == 'excel':
        content = fetch_file(url)
        df = load_excel_from_bytes(content)
    elif fmt == 'zip':
        # Expect a list of files and optional merge flag
        files = entry.get('files', [])
        merge = entry.get('merge', False)
        dfs = load_zip_and_extract(url, files)
        if merge:
            # Concatenate row‑wise; assume identical columns
            df = pd.concat(dfs, ignore_index=True)
        else:
            # If not merging, just take the first file
            df = dfs[0]
    else:
        raise ValueError(f"Unsupported dataset format: {fmt}")

    # Apply hygiene pipeline (drop missing, constant vars, keep numeric)
    df_clean, metadata = apply_hygiene_pipeline(df)

    # Build full metadata record
    full_meta = {
        'dataset_name': name,
        'original_feature_names': list(df.columns),
        'continuous_feature_names': [c for c in df_clean.columns
                                     if pd.api.types.is_numeric_dtype(df_clean[c])],
        'num_samples': df_clean.shape[0],
        'num_continuous_features': df_clean.shape[1],
        'source_repository': 'UCI Machine Learning Repository',
        'download_method': f'URL: {url}'
    }
    # Merge with hygiene metadata for completeness
    full_meta.update(metadata)

    return df_clean, full_meta

def fallback_openml_datasets(existing_names: List[str],
                            needed: int) -> List[Tuple[pd.DataFrame, Dict[str, Any]]]:
    """
    Query OpenML for additional multivariate datasets with >=20 continuous variables.
    Returns a list of (DataFrame, metadata) tuples until the required number of
    additional datasets is reached or the OpenML catalog is exhausted.
    """
    logger.info("Starting fallback search on OpenML...")
    candidates = openml.datasets.list_datasets(output_format='dataframe')
    # Shuffle to avoid bias; deterministic order by dataset ID for reproducibility
    candidates = candidates.sort_values('did')

    results = []
    for _, row in candidates.iterrows():
        ds_id = int(row['did'])
        try:
            dataset = openml.datasets.get_dataset(ds_id)
            X, y, _, _ = dataset.get_data(dataset_format='dataframe')
            if y is not None:
                if isinstance(y, pd.Series):
                    df = pd.concat([X, y], axis=1)
                else:
                    df = X
            else:
                df = X

            # Count continuous columns
            continuous_cols = [c for c in df.columns
                                if pd.api.types.is_numeric_dtype(df[c])]
            if len(continuous_cols) < 20:
                continue

            # Apply hygiene pipeline
            df_clean, meta = apply_hygiene_pipeline(df)

            # Avoid duplicates by name
            ds_name = dataset.name
            if ds_name in existing_names:
                continue

            full_meta = {
                'dataset_name': ds_name,
                'original_feature_names': list(df.columns),
                'continuous_feature_names': [c for c in df_clean.columns
                                             if pd.api.types.is_numeric_dtype(df_clean[c])],
                'num_samples': df_clean.shape[0],
                'num_continuous_features': df_clean.shape[1],
                'source_repository': 'OpenML',
                'download_method': f'openml.datasets.get_dataset({ds_id})'
            }
            full_meta.update(meta)

            results.append((df_clean, full_meta))
            existing_names.append(ds_name)

            if len(results) >= needed:
                break
        except Exception as e:
            logger.warning(f"OpenML fallback dataset {ds_id} failed: {e}")
            continue

    return results

def ensure_output_dirs(output_path: str):
    """Ensure output directories exist."""
    os.makedirs(output_path, exist_ok=True)

def load_all_datasets(config: Dict[str, Any], output_dir: str) -> List[pd.DataFrame]:
    """
    Load all datasets defined in the config registry. If fewer than three
    valid datasets (>=20 continuous variables) are obtained, automatically
    query OpenML for additional suitable datasets until at least three are
    available or the source is exhausted.
    """
    registry = get_dataset_registry()
    valid_datasets = []
    used_names = []

    logger.info("Loading primary UCI datasets from registry...")
    for entry in registry:
        try:
            df_clean, meta = process_registry_entry(entry)
            # Save to disk
            safe_name = meta['dataset_name'].replace(' ', '_')
            csv_path = os.path.join(output_dir,
                                    f"dataset_{len(valid_datasets)+1}_{safe_name}.csv")
            df_clean.to_csv(csv_path, index=False)
            meta_path = os.path.join(output_dir,
                                     f"dataset_{len(valid_datasets)+1}_{safe_name}_metadata.json")
            with open(meta_path, 'w') as f:
                json.dump(meta, f, indent=2)

            logger.info(f"Saved dataset '{meta['dataset_name']}' to {csv_path}")
            valid_datasets.append(df_clean)
            used_names.append(meta['dataset_name'])
        except Exception as e:
            logger.warning(f"Dataset '{entry.get('name')}' excluded: {e}")

    # Fallback if needed
    if len(valid_datasets) < 3:
        needed = 3 - len(valid_datasets)
        fallback_results = fallback_openml_datasets(used_names, needed)
        for df_fallback, meta_fallback in fallback_results:
            safe_name = meta_fallback['dataset_name'].replace(' ', '_')
            csv_path = os.path.join(output_dir,
                                    f"dataset_{len(valid_datasets)+1}_{safe_name}.csv")
            df_fallback.to_csv(csv_path, index=False)
            meta_path = os.path.join(output_dir,
                                     f"dataset_{len(valid_datasets)+1}_{safe_name}_metadata.json")
            with open(meta_path, 'w') as f:
                json.dump(meta_fallback, f, indent=2)

            logger.info(f"Saved fallback dataset '{meta_fallback['dataset_name']}' to {csv_path}")
            valid_datasets.append(df_fallback)

    if len(valid_datasets) == 0:
        raise RuntimeError("No valid datasets were loaded after applying fallback logic.")

    logger.info(f"Total valid datasets loaded: {len(valid_datasets)}")
    return valid_datasets

def main():
    """Main entry point for the loader script."""
    import argparse
    parser = argparse.ArgumentParser(description="Load and process datasets.")
    parser.add_argument('--output', type=str, default='data/processed/',
                        help='Output directory')
    args = parser.parse_args()

    ensure_output_dirs(args.output)

    # Load datasets using the current configuration (paths are not needed here)
    datasets = load_all_datasets({}, args.output)
    logger.info(f"Successfully loaded {len(datasets)} datasets.")

if __name__ == "__main__":
    main()
