import os
import json
import logging
import hashlib
from pathlib import Path
from typing import Optional, Dict, Any, Tuple, List

import pandas as pd
import openml
from datasets import load_dataset

from utils import setup_logging, log_info, log_warning, log_error
from config import get_config, ensure_dirs

setup_logging()
logger = logging.getLogger(__name__)

class RealDataFetchFailed(Exception):
    """Raised when all real data sources fail to provide a usable dataset."""
    pass

def get_column_mapping(df: pd.DataFrame) -> Tuple[Dict[str, str], bool]:
    """
    Heuristically map source columns to the target schema.
    Target schema: participant_id, age, stimulus_type, perseverative_errors, categories_completed, mmse_score
    """
    mapping = {}
    cols = df.columns.tolist()
    
    heuristics = {
        "participant_id": ["id", "subj", "participant", "pid"],
        "age": ["age"],
        "stimulus_type": ["condition", "group", "stimulus", "type", "nostalgia"],
        "perseverative_errors": ["persev", "error", "err"],
        "categories_completed": ["cat", "complete", "success"],
        "mmse_score": ["mmse"]
    }
    
    for target, keywords in heuristics.items():
        for col in cols:
            if any(k in col.lower() for k in keywords):
                mapping[target] = col
                break
    
    has_condition_labels = "stimulus_type" in mapping
    return mapping, has_condition_labels

def fetch_data() -> Tuple[pd.DataFrame, str, str]:
    """
    Acquire a real WCST dataset following the deterministic strategy in T101.
    Returns: (DataFrame, source_name, fetch_recipe)
    """
    # (a) OpenML Probe
    try:
        log_info("Probing OpenML for WCST datasets...")
        datasets_df = openml.datasets.list_datasets()
        keywords = ["WCST", "card-sorting", "executive function"]
        
        # Filter by name or description
        mask = datasets_df['name'].str.contains('|'.join(keywords), case=False, na=False) | \
               datasets_df['description'].str.contains('|'.join(keywords), case=False, na=False)
        
        filtered = datasets_df[mask]
        if not filtered.empty:
            # Select largest row count, break ties by lowest ID
            best = filtered.sort_values(by=['numInstances', 'dataset_id'], ascending=[False, True]).iloc[0]
            dataset_id = int(best['dataset_id'])
            log_info(f"Found OpenML dataset ID {dataset_id} ('{best['name']}') with {best['numInstances']} rows.")
            
            dataset = openml.datasets.get_dataset(dataset_id)
            df = dataset.get_data()
            
            recipe = f"openml.datasets.get_dataset({dataset_id}).get_data()"
            return df, f"OpenML ID {dataset_id}", recipe
    except Exception as e:
        log_warning(f"OpenML fetch failed: {e}")

    # (b) HuggingFace Probe
    try:
        log_info("Probing HuggingFace for WCST datasets...")
        # The spec mentions <huggingface-repo> as a placeholder.
        # We attempt a search or a known candidate if available. 
        # Since no specific repo was provided, we try a generic known pattern or common repo.
        # In a real scenario, we'd use a verified repo. Here we implement the logic.
        # We try 'cognitive_flexibility/wcst' as a representative attempt.
        hf_repo = "cognitive_flexibility/wcst" 
        dataset = load_dataset(hf_repo, name="wcst", split="train", streaming=False)
        df = pd.DataFrame(dataset)
        
        recipe = f"datasets.load_dataset('{hf_repo}', name='wcst', split='train')"
        return df, f"HuggingFace {hf_repo}", recipe
    except Exception as e:
        log_warning(f"HuggingFace fetch failed: {e}")

    # Final Failure
    log_error("All real data sources failed.")
    raise RealDataFetchFailed("Could not acquire real WCST data from OpenML or HuggingFace.")

def main():
    """Main entry point for T101: Acquire real WCST dataset."""
    config = get_config()
    ensure_dirs(config)
    
    try:
        df, source, recipe = fetch_data()
    except RealDataFetchFailed as e:
        log_error(str(e))
        raise

    # Write raw CSV
    raw_path = Path(config['paths']['raw']) / 'raw_dataset.csv'
    df.to_csv(raw_path, index=False)
    log_info(f"Raw dataset written to {raw_path}")

    # Compute SHA-256 checksum of the file
    sha256_hash = hashlib.sha256()
    with open(raw_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    checksum = sha256_hash.hexdigest()

    # Determine column mapping and condition labels
    mapping, has_condition_labels = get_column_mapping(df)

    # Write metadata.json
    metadata = {
        "dataset_source": source,
        "fetch_recipe": recipe,
        "simulation_mode": False,
        "has_condition_labels": has_condition_labels,
        "sha256_checksum": checksum,
        "column_mapping": mapping
    }
    
    metadata_path = Path(config['paths']['raw']) / 'metadata.json'
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    log_info(f"Metadata written to {metadata_path}")
    log_info(f"Successfully acquired dataset from {source}. Mapping: {mapping}")

if __name__ == "__main__":
    main()