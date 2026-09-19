import os
import sys
import time
import signal
import logging
import json
from pathlib import Path
from typing import List, Dict, Any, Optional

import pandas as pd
from datasets import load_dataset

# Import project utilities based on API surface
from config import load_config
from utils.logger import setup_logging, log_missing_data
from utils.data_loader import fetch_nist_data, fetch_pubchem_data, fetch_mtr_data

# Define custom exceptions
class TimeoutError(Exception):
    pass

class MemoryLimitError(Exception):
    pass

# Global timeout handler for signal
_timeout_handler = None

def timeout_handler(signum, frame):
    raise TimeoutError("TIMEOUT: Graph construction exceeded 5 minutes")

def setup_timeout_handler(timeout_seconds: int):
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(timeout_seconds)

def cancel_timeout_handler():
    signal.alarm(0)

def compute_molecular_descriptors(df: pd.DataFrame) -> pd.DataFrame:
    """
    Parse SMILES to Mol using RDKit and compute descriptors.
    """
    try:
        from rdkit import Chem
        from rdkit.Chem import Descriptors
    except ImportError:
        raise ImportError("RDKit is required for molecular descriptor computation. Install via: pip install rdkit")

    def get_mol(smiles):
        try:
            return Chem.MolFromSmiles(smiles)
        except Exception:
            return None

    def calc_props(mol):
        if mol is None:
            return None, None, None, None
        return (
            Descriptors.MolWt(mol),
            Descriptors.MolLogP(mol),
            Descriptors.TPSA(mol),
            Descriptors.NumRotatableBonds(mol)
        )

    df['mol'] = df['smiles'].apply(get_mol)
    props = df['mol'].apply(calc_props)
    
    # Unpack properties into separate columns
    df['MW'] = props.apply(lambda x: x[0])
    df['logP'] = props.apply(lambda x: x[1])
    df['PSA'] = props.apply(lambda x: x[2])
    df['rotatable_bonds'] = props.apply(lambda x: x[3])

    return df

def ingest_nist_data() -> pd.DataFrame:
    """Fetch NIST dataset."""
    return fetch_nist_data()

def ingest_pubchem_data() -> pd.DataFrame:
    """Fetch PubChem dataset."""
    return fetch_pubchem_data()

def ingest_mtr_data() -> pd.DataFrame:
    """Fetch MTR dataset."""
    return fetch_mtr_data()

def deduplicate_smiles(df: pd.DataFrame) -> pd.DataFrame:
    """
    Handle duplicate SMILES by aggregating targets using mean function.
    Returns deduplicated dataframe.
    """
    if df.empty:
        return df

    # Group by smiles and aggregate
    grouped = df.groupby('smiles').agg({
        'target': ['mean', 'count'],
        'source_id': lambda x: list(set(x))  # Aggregate source IDs
    }).reset_index()
    
    grouped.columns = ['smiles', 'target_mean', 'count', 'source_ids']
    return grouped

def merge_sources(df_nist: pd.DataFrame, df_pubchem: pd.DataFrame, df_mtr: pd.DataFrame) -> pd.DataFrame:
    """Merge NIST, PubChem, and MTR datasets into a single dataframe."""
    return pd.concat([df_nist, df_pubchem, df_mtr], ignore_index=True)

def validate_dataset(df: pd.DataFrame, min_unique: int = 500) -> Dict[str, Any]:
    """
    Validate dataset size and log exclusion reasons.
    """
    unique_count = df['smiles'].nunique()
    status = "PASS" if unique_count >= min_unique else "FAIL"
    
    report = {
        "unique_compounds": unique_count,
        "min_required": min_unique,
        "status": status,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    if status == "FAIL":
        raise ValueError(f"Dataset validation failed: {unique_count} unique compounds < {min_unique} required.")
    
    return report

def exclude_missing_permeability(df: pd.DataFrame, output_dir: str = "data/processed") -> Dict[str, Any]:
    """
    Exclude rows with missing permeability values and log specific reasons.
    Also calculates and logs exclusion rate statistics.
    
    Returns statistics dictionary:
    {
        "total_rows": int,
        "excluded_rows": int,
        "rate": float,
        "reasons": List[str]
    }
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    logger = logging.getLogger(__name__)
    
    total_rows = len(df)
    excluded_rows = 0
    exclusion_reasons = []
    exclusion_log_entries = []

    # Identify missing permeability (target)
    missing_mask = df['target'].isna()
    missing_count = missing_mask.sum()
    
    if missing_count > 0:
        logger.warning(f"Found {missing_count} rows with missing permeability values.")
        excluded_rows += missing_count
        exclusion_reasons.append("Missing target variable")
        
        # Log specific exclusions
        missing_indices = df[missing_mask].index
        for idx in missing_indices:
            smiles = df.loc[idx, 'smiles']
            exclusion_log_entries.append({
                "smiles": str(smiles),
                "reason": "Missing target variable"
            })
            
        # Log to exclusion log file
        exclusion_log_path = output_path / "exclusion_log.json"
        if exclusion_log_path.exists():
            with open(exclusion_log_path, 'r') as f:
                existing_logs = json.load(f)
            existing_logs.extend(exclusion_log_entries)
        else:
            existing_logs = exclusion_log_entries
            
        with open(exclusion_log_path, 'w') as f:
            json.dump(existing_logs, f, indent=2)
        
        # Log via utility
        for entry in exclusion_log_entries[:10]: # Log first 10 as sample
            log_missing_data(f"Missing target: {entry['smiles']}")

    # Filter out missing rows
    df_clean = df.dropna(subset=['target']).reset_index(drop=True)
    
    # Calculate statistics
    rate = excluded_rows / total_rows if total_rows > 0 else 0.0
    
    stats = {
        "total_rows": total_rows,
        "excluded_rows": excluded_rows,
        "rate": rate,
        "reasons": list(set(exclusion_reasons)),
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    # Write exclusion stats to JSON
    stats_path = output_path / "exclusion_stats.json"
    with open(stats_path, 'w') as f:
        json.dump(stats, f, indent=2)
        
    logger.info(f"Exclusion stats written to {stats_path}")
    logger.info(f"Exclusion rate: {rate:.4f} ({excluded_rows}/{total_rows})")
    
    return stats

def main():
    """
    Main entry point for ingestion pipeline.
    Orchestrates fetching, merging, validating, and excluding missing data.
    """
    # Setup logging
    config = load_config()
    setup_logging(config.get('logging', {}))
    logger = logging.getLogger(__name__)
    
    # Setup timeout
    timeout_seconds = config.get('TIMEOUT_GRAPHS', 300)
    setup_timeout_handler(timeout_seconds)
    
    try:
        logger.info("Starting data ingestion pipeline...")
        
        # Fetch data
        logger.info("Fetching NIST data...")
        df_nist = ingest_nist_data()
        
        logger.info("Fetching PubChem data...")
        df_pubchem = ingest_pubchem_data()
        
        logger.info("Fetching MTR data...")
        df_mtr = ingest_mtr_data()
        
        # Merge sources
        logger.info("Merging datasets...")
        df_merged = merge_sources(df_nist, df_pubchem, df_mtr)
        df_merged.to_csv("data/processed/merged_dataset.csv", index=False)
        
        # Exclude missing permeability (T014 & T016)
        logger.info("Excluding rows with missing permeability...")
        stats = exclude_missing_permeability(df_merged, output_dir="data/processed")
        
        # Filtered dataframe for further processing
        df_clean = df_merged.dropna(subset=['target']).reset_index(drop=True)
        
        # Compute descriptors
        logger.info("Computing molecular descriptors...")
        df_descriptors = compute_molecular_descriptors(df_clean)
        
        # Deduplicate
        logger.info("Deduplicating SMILES...")
        df_dedup = deduplicate_smiles(df_descriptors)
        df_dedup.to_csv("data/processed/deduplicated.csv", index=False)
        
        # Validate
        logger.info("Validating dataset size...")
        validation_report = validate_dataset(df_dedup, min_unique=500)
        
        with open("data/processed/validation_report.json", 'w') as f:
            json.dump(validation_report, f, indent=2)
            
        logger.info(f"Ingestion complete. Unique compounds: {validation_report['unique_compounds']}")
        
    except TimeoutError as e:
        logger.error(str(e))
        raise
    finally:
        cancel_timeout_handler()

if __name__ == "__main__":
    main()