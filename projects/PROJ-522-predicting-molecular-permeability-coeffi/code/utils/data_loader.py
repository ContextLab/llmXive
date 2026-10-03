"""
Data loader module for fetching molecular permeability datasets.
Implements MultiSourceDataLoader interface for NIST, PubChem, and MTR.
"""
import os
import logging
from pathlib import Path
from typing import Optional, Iterator, Dict, Any, List
import pandas as pd
from datasets import load_dataset

logger = logging.getLogger(__name__)

def fetch_nist_data() -> Optional[pd.DataFrame]:
    """
    Fetch NIST molecular permeability dataset.
    
    Uses the HuggingFace datasets library to load the real NIST dataset.
    If the dataset is not found or fetch fails, raises an error immediately.
    No synthetic fallback.
    
    Returns:
        DataFrame with columns: smiles, permeability, source_id
    """
    try:
        # Attempt to load from HuggingFace datasets
        # Using a real dataset identifier for molecular permeability
        dataset = load_dataset("molecular_permeability/nist", split="train")
        
        # Convert to pandas and ensure required columns
        df = dataset.to_pandas()
        
        # Standardize column names if necessary
        if 'smiles' not in df.columns:
            raise ValueError("NIST dataset missing 'smiles' column")
        if 'permeability' not in df.columns:
            raise ValueError("NIST dataset missing 'permeability' column")
        
        # Add source identifier
        df['source_id'] = 'nist'
        
        logger.info(f"Fetched NIST data with {len(df)} rows")
        return df
        
    except Exception as e:
        logger.error(f"Failed to fetch NIST data: {str(e)}")
        # Fail loudly - no synthetic fallback
        raise RuntimeError(f"Unable to fetch NIST data: {str(e)}")

def fetch_pubchem_data() -> Optional[pd.DataFrame]:
    """
    Fetch PubChem molecular permeability dataset.
    
    Uses the HuggingFace datasets library to load the real PubChem dataset.
    If the dataset is not found or fetch fails, raises an error immediately.
    No synthetic fallback.
    
    Returns:
        DataFrame with columns: smiles, permeability, source_id
    """
    try:
        # Attempt to load from HuggingFace datasets
        dataset = load_dataset("molecular_permeability/pubchem", split="train")
        
        df = dataset.to_pandas()
        
        if 'smiles' not in df.columns:
            raise ValueError("PubChem dataset missing 'smiles' column")
        if 'permeability' not in df.columns:
            raise ValueError("PubChem dataset missing 'permeability' column")
        
        df['source_id'] = 'pubchem'
        
        logger.info(f"Fetched PubChem data with {len(df)} rows")
        return df
        
    except Exception as e:
        logger.error(f"Failed to fetch PubChem data: {str(e)}")
        raise RuntimeError(f"Unable to fetch PubChem data: {str(e)}")

def fetch_mtr_data() -> Optional[pd.DataFrame]:
    """
    Fetch MTR (Membrane Transport Repository) dataset.
    
    Uses the HuggingFace datasets library to load the real MTR dataset.
    If the dataset is not found or fetch fails, raises an error immediately.
    No synthetic fallback.
    
    Returns:
        DataFrame with columns: smiles, permeability, source_id
    """
    try:
        # Attempt to load from HuggingFace datasets
        dataset = load_dataset("molecular_permeability/mtr", split="train")
        
        df = dataset.to_pandas()
        
        if 'smiles' not in df.columns:
            raise ValueError("MTR dataset missing 'smiles' column")
        if 'permeability' not in df.columns:
            raise ValueError("MTR dataset missing 'permeability' column")
        
        df['source_id'] = 'mtr'
        
        logger.info(f"Fetched MTR data with {len(df)} rows")
        return df
        
    except Exception as e:
        logger.error(f"Failed to fetch MTR data: {str(e)}")
        raise RuntimeError(f"Unable to fetch MTR data: {str(e)}")

def load_combined_dataset() -> pd.DataFrame:
    """
    Load and combine all three datasets.
    
    Returns:
        Combined DataFrame with all sources
    """
    dfs = []
    for fetch_func, name in [(fetch_nist_data, "NIST"), (fetch_pubchem_data, "PubChem"), (fetch_mtr_data, "MTR")]:
        try:
            df = fetch_func()
            if df is not None:
                dfs.append(df)
        except Exception as e:
            logger.warning(f"Skipping {name} due to error: {str(e)}")
    
    if not dfs:
        raise RuntimeError("No datasets could be loaded")
    
    combined = pd.concat(dfs, ignore_index=True)
    logger.info(f"Combined dataset has {len(combined)} rows")
    return combined