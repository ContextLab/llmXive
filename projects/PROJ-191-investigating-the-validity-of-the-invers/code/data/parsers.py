"""
Data parsing module.
Parses raw CSV files extracted from arXiv tarballs into intermediate HarmonizedDataset objects.
"""
import pandas as pd
import numpy as np
from pathlib import Path
import re
import logging
from typing import List, Dict, Any, Optional

from config import get_logger
from data.models import HarmonizedDataset

logger = get_logger(__name__)

def parse_raw_data(file_path: Path) -> pd.DataFrame:
    """
    Parse a raw CSV file.
    Attempts to identify columns for separation, force, and uncertainty.

    Args:
        file_path: Path to the CSV file.

    Returns:
        DataFrame with standardized columns.
    """
    try:
        df = pd.read_csv(file_path)
        logger.debug(f"Parsed {file_path}: {df.shape}")
    except Exception as e:
        logger.error(f"Failed to parse {file_path}: {e}")
        raise

    # Heuristic column mapping
    sep_col = None
    force_col = None
    unc_col = None

    cols_lower = {c.lower(): c for c in df.columns}

    # Search for separation
    for pattern in ['separation', 'distance', 'gap', 'r_um', 'r_\\mu m', 'separation_um']:
        if re.search(pattern, str(cols_lower.keys()), re.IGNORECASE):
            # Find the key in original case
            for k, v in cols_lower.items():
                if pattern in k:
                    sep_col = v
                    break
        if sep_col: break
    
    # Fallback if regex failed, try common names
    if not sep_col:
        if 'separation_um' in cols_lower: sep_col = cols_lower['separation_um']
        elif 'separation' in cols_lower: sep_col = cols_lower['separation']
        elif 'distance_um' in cols_lower: sep_col = cols_lower['distance_um']

    # Search for force
    for pattern in ['force', 'f_n', 'force_n', 'force_dyne']:
        if re.search(pattern, str(cols_lower.keys()), re.IGNORECASE):
            for k, v in cols_lower.items():
                if pattern in k:
                    force_col = v
                    break
        if force_col: break

    if not force_col:
        if 'force_n' in cols_lower: force_col = cols_lower['force_n']
        elif 'force_dyne' in cols_lower: force_col = cols_lower['force_dyne']
        elif 'force' in cols_lower: force_col = cols_lower['force']

    # Search for uncertainty
    for pattern in ['uncertainty', 'error', 'sigma', 'unc', 'err']:
        if re.search(pattern, str(cols_lower.keys()), re.IGNORECASE):
            for k, v in cols_lower.items():
                if pattern in k:
                    unc_col = v
                    break
        if unc_col: break

    if not unc_col:
        if 'uncertainty_dyne' in cols_lower: unc_col = cols_lower['uncertainty_dyne']
        elif 'uncertainty_n' in cols_lower: unc_col = cols_lower['uncertainty_n']
        elif 'error' in cols_lower: unc_col = cols_lower['error']

    # Construct output
    output_data = {}
    if sep_col and sep_col in df.columns:
        output_data['separation_um'] = df[sep_col]
    else:
        logger.warning(f"Could not find separation column in {file_path}")
        # Create dummy if missing? No, raise or skip. Let's skip row if critical.
        # For now, assume valid data structure as per spec
        return pd.DataFrame() 

    if force_col and force_col in df.columns:
        output_data['force_dyne'] = df[force_col]
    else:
        logger.warning(f"Could not find force column in {file_path}")
        return pd.DataFrame()

    if unc_col and unc_col in df.columns:
        output_data['uncertainty_dyne'] = df[unc_col]
    else:
        # If no uncertainty, estimate or leave for harmonize to handle
        logger.info(f"No uncertainty column found in {file_path}, will estimate later.")
        output_data['uncertainty_dyne'] = np.nan

    # Add experiment ID from filename if possible
    exp_id = file_path.stem
    output_data['experiment_id'] = exp_id

    return pd.DataFrame(output_data)

def parse_arxiv_2106_08611(raw_dir: Path) -> List[pd.DataFrame]:
    """
    Parse all relevant CSVs from arXiv:2106.08611.
    """
    files = list(raw_dir.glob("*2106*") / "**" / "*.csv")
    # If glob didn't work recursively, try flat
    if not files:
       files = list(raw_dir.glob("*.csv"))
    
    dfs = []
    for f in files:
        if "_run" in f.name.lower() or "calib" in f.name.lower():
            df = parse_raw_data(f)
            if not df.empty:
                dfs.append(df)
    return dfs

def parse_arxiv_2305_06325(raw_dir: Path) -> List[pd.DataFrame]:
    """
    Parse all relevant CSVs from arXiv:2305.06325.
    """
    files = list(raw_dir.glob("*2305*") / "**" / "*.csv")
    if not files:
       files = list(raw_dir.glob("*.csv"))
    
    dfs = []
    for f in files:
        if "_run" in f.name.lower() or "calib" in f.name.lower():
            df = parse_raw_data(f)
            if not df.empty:
                dfs.append(df)
    return dfs

def main():
    """CLI entry point for parsing."""
    # This is typically called by download.py or harmonize.py
    # For testing, we can run it if data exists
    raw_dir = Path("data/raw/extracted")
    if not raw_dir.exists():
        logger.warning("Raw data directory not found. Run download.py first.")
        return 1
    
    dfs_2106 = parse_arxiv_2106_08611(raw_dir)
    dfs_2305 = parse_arxiv_2305_06325(raw_dir)
    
    logger.info(f"Parsed {len(dfs_2106)} files from 2106.08611")
    logger.info(f"Parsed {len(dfs_2305)} files from 2305.06325")
    return 0

if __name__ == "__main__":
    exit(main())
