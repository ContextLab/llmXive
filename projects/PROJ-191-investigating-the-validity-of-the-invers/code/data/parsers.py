import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict, Any
import logging

from config import get_logger
from data.loaders import HarmonizedDataset

logger = get_logger(__name__)

def parse_arxiv_2106_08611(raw_path: Path) -> pd.DataFrame:
    """
    Parse the raw CSV from arXiv:2106.08611.
    
    Expected columns: separation (microns), force (dynes), stat_err, sys_err (or similar).
    This function maps them to a standard internal format.
    """
    logger.info(f"Parsing {raw_path}")
    
    # Attempt to read
    try:
        df = pd.read_csv(raw_path)
    except Exception as e:
        logger.error(f"Failed to read CSV {raw_path}: {e}")
        raise
    
    # Normalize column names to lowercase
    df.columns = [c.lower().strip() for c in df.columns]
    
    # Map columns
    # Heuristic: find columns containing 'sep', 'force', 'err'
    sep_col = None
    force_col = None
    stat_col = None
    sys_col = None
    
    for col in df.columns:
        if 'sep' in col or 'dist' in col:
            sep_col = col
        elif 'force' in col:
            force_col = col
        elif 'stat' in col and 'err' in col:
            stat_col = col
        elif 'sys' in col and 'err' in col:
            sys_col = col
        elif 'uncertainty' in col:
            # Fallback for uncertainty
            if stat_col is None: stat_col = col
    
    if sep_col is None or force_col is None:
        raise ValueError(f"Could not identify separation or force columns in {raw_path}. Columns: {df.columns.tolist()}")
    
    # Standardize
    result = pd.DataFrame()
    result['separation_microns'] = df[sep_col].values
    result['force_dynes'] = df[force_col].values
    
    if stat_col:
        result['stat_err'] = df[stat_col].values
    else:
        result['stat_err'] = np.zeros(len(df))
        logger.warning(f"No statistical error column found in {raw_path}. Setting to zero.")
        
    if sys_col:
        result['sys_err'] = df[sys_col].values
    else:
        result['sys_err'] = np.zeros(len(df))
        logger.warning(f"No systematic error column found in {raw_path}. Setting to zero.")
    
    result['source'] = '2106.08611'
    
    return result

def parse_arxiv_2305_06325(raw_path: Path) -> pd.DataFrame:
    """
    Parse the raw CSV from arXiv:2305.06325.
    Similar logic, potentially different column names.
    """
    logger.info(f"Parsing {raw_path}")
    
    try:
        df = pd.read_csv(raw_path)
    except Exception as e:
        logger.error(f"Failed to read CSV {raw_path}: {e}")
        raise
    
    df.columns = [c.lower().strip() for c in df.columns]
    
    sep_col = None
    force_col = None
    stat_col = None
    sys_col = None
    
    for col in df.columns:
        if 'sep' in col or 'dist' in col:
            sep_col = col
        elif 'force' in col:
            force_col = col
        elif 'stat' in col and 'err' in col:
            stat_col = col
        elif 'sys' in col and 'err' in col:
            sys_col = col
        elif 'uncertainty' in col:
            if stat_col is None: stat_col = col
    
    if sep_col is None or force_col is None:
        raise ValueError(f"Could not identify separation or force columns in {raw_path}. Columns: {df.columns.tolist()}")
    
    result = pd.DataFrame()
    result['separation_microns'] = df[sep_col].values
    result['force_dynes'] = df[force_col].values
    
    if stat_col:
        result['stat_err'] = df[stat_col].values
    else:
        result['stat_err'] = np.zeros(len(df))
        
    if sys_col:
        result['sys_err'] = df[sys_col].values
    else:
        result['sys_err'] = np.zeros(len(df))
    
    result['source'] = '2305.06325'
    
    return result

def parse_raw_data(data_paths: List[Path]) -> List[pd.DataFrame]:
    """
    Dispatch to appropriate parser based on file path or content.
    """
    dfs = []
    for p in data_paths:
        if '2106.08611' in p.name:
            dfs.append(parse_arxiv_2106_08611(p))
        elif '2305.06325' in p.name:
            dfs.append(parse_arxiv_2305_06325(p))
        else:
            # Fallback: try generic parse
            logger.warning(f"Unknown data source {p}. Attempting generic parse.")
            try:
                df = pd.read_csv(p)
                df.columns = [c.lower().strip() for c in df.columns]
                # Try to infer
                sep_col = next((c for c in df.columns if 'sep' in c or 'dist' in c), None)
                force_col = next((c for c in df.columns if 'force' in c), None)
                if sep_col and force_col:
                    result = pd.DataFrame()
                    result['separation_microns'] = df[sep_col]
                    result['force_dynes'] = df[force_col]
                    result['stat_err'] = np.zeros(len(df))
                    result['sys_err'] = np.zeros(len(df))
                    result['source'] = p.stem
                    dfs.append(result)
                else:
                    raise ValueError("Generic parse failed: missing columns")
            except Exception as e:
                logger.error(f"Failed to parse {p}: {e}")
                raise
    return dfs

def main():
    logger.info("parsers module loaded.")

if __name__ == "__main__":
    main()