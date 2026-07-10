"""
Data Ingestion Module for Electrolyte Decomposition Prediction.

Fetches DFT data from HuggingFace, filters for target electrolytes (EC, DMC, LiPF6),
and handles fallback to local data if the remote source is unavailable.
"""
import os
import hashlib
import json
import pandas as pd
from pathlib import Path
from typing import Optional, List, Dict, Any
import sys

# Add project root to path if running as script
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent))

from config import get_data_dir, get_dataset_url, get_fallback_path, get_project_root


def fetch_dataset_data(url: Optional[str] = None) -> Optional[pd.DataFrame]:
    """
    Attempt to fetch the DFT dataset from HuggingFace or a remote URL.
    
    Args:
        url: Optional override for the dataset URL.
        
    Returns:
        DataFrame if successful, None otherwise.
    """
    if url is None:
        url = get_dataset_url()
        
    try:
        # Attempt to import datasets library
        try:
            from datasets import load_dataset
        except ImportError:
            raise ImportError("The 'datasets' package is required. Install via: pip install datasets")
        
        # Check if the URL is a HuggingFace dataset ID
        if "huggingface.co/datasets" in url or "/" in url and not url.startswith("http"):
            ds = load_dataset(url)
            # Assuming split is 'train' or 'default'
            if 'train' in ds:
                return ds['train'].to_pandas()
            elif 'default' in ds:
                return ds['default'].to_pandas()
            else:
                # Fallback to first available split
                first_split = list(ds.keys())[0]
                return ds[first_split].to_pandas()
        else:
            # Assume it's a direct CSV/Parquet URL
            if url.endswith('.csv'):
                return pd.read_csv(url)
            elif url.endswith('.parquet'):
                return pd.read_parquet(url)
            else:
                raise ValueError(f"Unsupported file format for URL: {url}")
                
    except Exception as e:
        print(f"Failed to fetch dataset from {url}: {e}")
        return None


def load_fallback_data(fallback_path: Optional[str] = None) -> pd.DataFrame:
    """
    Load data from a local fallback CSV file.
    
    Args:
        fallback_path: Optional override for the fallback file path.
        
    Returns:
        DataFrame containing the fallback data.
        
    Raises:
        FileNotFoundError: If the fallback file does not exist.
    """
    if fallback_path is None:
        fallback_path = get_fallback_path()
        
    fallback_file = Path(fallback_path)
    
    if not fallback_file.exists():
        raise FileNotFoundError(f"Fallback data file not found at {fallback_file}")
        
    return pd.read_csv(fallback_file)


def filter_electrolytes(df: pd.DataFrame, target_molecules: List[str]) -> pd.DataFrame:
    """
    Filter the dataset to include only specified electrolyte molecules.
    
    Args:
        df: Input DataFrame.
        target_molecules: List of molecule identifiers (e.g., ['EC', 'DMC', 'LiPF6']).
        
    Returns:
        Filtered DataFrame.
    """
    # Normalize column names for robustness
    df = df.rename(columns=str.strip)
    
    # Identify the molecule column (common names: 'molecule_id', 'name', 'species')
    molecule_col = None
    candidates = ['molecule_id', 'name', 'species', 'molecule']
    for cand in candidates:
        if cand in df.columns:
            molecule_col = cand
            break
    
    if molecule_col is None:
        # If no obvious column found, return empty or raise warning
        print("Warning: Could not identify molecule column. Returning empty DataFrame.")
        return df.iloc[0:0]
        
    # Filter rows where the molecule column matches any target
    # Ensure the column is string type for comparison
    mask = df[molecule_col].astype(str).isin(target_molecules)
    return df[mask].reset_index(drop=True)


def deduplicate_by_id_potential(df: pd.DataFrame) -> pd.DataFrame:
    """
    Remove duplicate entries based on molecule_id and potential.
    
    Args:
        df: Input DataFrame.
        
    Returns:
        Deduplicated DataFrame.
    """
    df = df.rename(columns=str.strip)
    
    # Identify columns
    id_col = 'molecule_id' if 'molecule_id' in df.columns else None
    pot_col = 'potential_v' if 'potential_v' in df.columns else None
    
    if id_col is None or pot_col is None:
        # Try to infer from common names
        if 'id' in df.columns: id_col = 'id'
        if 'potential' in df.columns: pot_col = 'potential'
        
    if id_col is not None and pot_col is not None:
        # Drop duplicates keeping the first occurrence
        df = df.drop_duplicates(subset=[id_col, pot_col], keep='first')
        
    return df.reset_index(drop=True)


def run_ingestion_pipeline(output_dir: Optional[str] = None) -> pd.DataFrame:
    """
    Execute the full ingestion pipeline: fetch/filter/deduplicate.
    
    Args:
        output_dir: Directory to save the intermediate raw data (optional).
        
    Returns:
        Processed DataFrame ready for descriptor extraction.
    """
    project_root = get_project_root()
    data_dir = get_data_dir()
    
    if output_dir is None:
        output_dir = data_dir / "raw"
    else:
        output_dir = Path(output_dir)
        
    output_dir.mkdir(parents=True, exist_ok=True)
    
    target_molecules = ["EC", "DMC", "LiPF6"]
    raw_file = output_dir / "electrolytes_raw.csv"
    
    # 1. Fetch
    print("Attempting to fetch dataset...")
    df = fetch_dataset_data()
    
    # 2. Fallback
    if df is None or df.empty:
        print("Remote fetch failed. Loading fallback data...")
        try:
            df = load_fallback_data()
        except FileNotFoundError as e:
            print(f"FATAL: No data source available. {e}")
            # Return empty with expected schema if possible, or exit
            return pd.DataFrame(columns=["molecule_id", "potential_v", "smiles", "homo", "lumo"])
    
    # 3. Filter
    print(f"Filtering for molecules: {target_molecules}")
    df = filter_electrolytes(df, target_molecules)
    
    if df.empty:
        print("Warning: No matching molecules found in the dataset.")
        return df
        
    # 4. Deduplicate
    print("Deduplicating entries...")
    df = deduplicate_by_id_potential(df)
    
    # 5. Save
    print(f"Saving raw data to {raw_file}")
    df.to_csv(raw_file, index=False)
    
    # Compute checksum for validation
    checksum = hashlib.sha256(raw_file.read_bytes()).hexdigest()
    checksum_file = output_dir / "electrolytes_raw.sha256"
    checksum_file.write_text(f"{checksum}  {raw_file.name}\n")
    
    print(f"Ingestion complete. Rows: {len(df)}, Checksum: {checksum}")
    return df


if __name__ == "__main__":
    run_ingestion_pipeline()
