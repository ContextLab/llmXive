import os
import json
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional

from config import get_data_dir
from download import fetch_openml_dataset, fetch_huggingface_dataset

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

EXCLUSION_LOG_PATH = Path("data/processed/exclusion_log.json")

def load_exclusion_log() -> List[Dict[str, Any]]:
    """Load the exclusion log if it exists."""
    if EXCLUSION_LOG_PATH.exists():
        with open(EXCLUSION_LOG_PATH, 'r') as f:
            return json.load(f)
    return []

def save_exclusion_log(log: List[Dict[str, Any]]) -> None:
    """Save the exclusion log to disk."""
    EXCLUSION_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(EXCLUSION_LOG_PATH, 'w') as f:
        json.dump(log, f, indent=2)

def log_exclusion(dataset_id: str, reason: str, details: Optional[Dict] = None) -> None:
    """Log a dataset exclusion."""
    log = load_exclusion_log()
    log.append({
        "dataset_id": dataset_id,
        "status": "excluded",
        "reason": reason,
        "details": details or {},
        "timestamp": pd.Timestamp.now().isoformat()
    })
    save_exclusion_log(log)
    logger.warning(f"Excluded dataset {dataset_id}: {reason}")

def log_inclusion(dataset_id: str, details: Optional[Dict] = None) -> None:
    """Log a dataset inclusion."""
    log = load_exclusion_log()
    log.append({
        "dataset_id": dataset_id,
        "status": "included",
        "reason": None,
        "details": details or {},
        "timestamp": pd.Timestamp.now().isoformat()
    })
    save_exclusion_log(log)
    logger.info(f"Included dataset {dataset_id}")

def check_sequential_stimuli(df: pd.DataFrame, stimulus_col: str = "stimulus_sequence") -> bool:
    """
    Check if the dataset contains sequential stimuli.
    Returns False if the data appears to be random noise or non-sequential.
    
    Heuristics:
    1. The stimulus column must exist.
    2. The stimulus column should have a non-trivial sequence structure.
       We check for transitions. If the column is constant or has no transitions,
       it might not be a valid sequential task.
    3. We assume valid sequential data has at least some variation in transitions.
    """
    if stimulus_col not in df.columns:
        return False

    series = df[stimulus_col]
    if series.isna().all():
        return False

    # Check for constant sequence (no sequence)
    if series.nunique() == 1:
        return False

    # Check for randomness vs structure.
    # A purely random sequence might still be valid, but we need to ensure
    # there is a sequence to analyze.
    # We simply verify that there are transitions (length > 1 and not constant).
    # More advanced: Check autocorrelation? For now, basic sequence check.
    if len(series) < 2:
        return False

    return True

def check_predictability_manipulation(df: pd.DataFrame) -> bool:
    """
    Check if the dataset contains predictability manipulations.
    
    Heuristics:
    1. Look for columns indicating condition, block, or probability.
    2. If the dataset is purely random (no structure), it might not have
       the necessary predictability manipulations for this study.
    3. We check for the presence of columns that typically denote conditions
       (e.g., 'condition', 'block', 'predictability', 'prob').
    """
    # Columns that suggest predictability manipulation
    target_keywords = ['condition', 'block', 'predict', 'prob', 'high', 'low', 'sequence_type']
    
    cols_lower = [str(c).lower() for c in df.columns]
    
    has_structure = any(kw in ' '.join(cols_lower) for kw in target_keywords)
    
    # If we have a stimulus sequence and it's not constant, we assume
    # there is some structure to analyze, but strictly speaking,
    # we want to exclude datasets that are just "random noise" without
    # a designed manipulation (e.g. high vs low probability blocks).
    # Since we don't have a schema for the manipulation itself, we rely on
    # column names or the existence of a sequence column that varies.
    
    # Fallback: If we have a varying sequence, we tentatively include it,
    # assuming the study design implies the manipulation.
    # However, the task asks to exclude "random noise".
    # We will assume if a column named 'condition' or similar exists, it's valid.
    # If not, and it's just a raw sequence, we might need to inspect entropy.
    
    # For this implementation, we require at least one of the structural columns
    # OR a sequence that shows non-random transition patterns (simplified: just varies).
    # To be strict per FR-002: "exclude datasets lacking sequential stimuli or predictability manipulations".
    # If we can't find a 'condition' column, we might be looking at raw noise.
    # Let's enforce the presence of a 'condition' or 'block' column as a proxy for manipulation.
    
    if not has_structure:
        # Check if there is a 'stimulus_sequence' column that is the primary feature
        # If the dataset ONLY has a sequence and no condition labels, it might be
        # a simple reaction time task without the predictive coding manipulation.
        # We will exclude it to be safe, as we need to compare conditions.
        return False

    return True

def filter_datasets(dataset_ids: List[str]) -> Dict[str, Any]:
    """
    Filter datasets based on sequential stimuli and predictability manipulations.
    
    Args:
        dataset_ids: List of dataset IDs to check.
        
    Returns:
        Dictionary with 'included' and 'excluded' lists of dataset IDs.
    """
    results = {
        "included": [],
        "excluded": [],
        "details": {}
    }

    for ds_id in dataset_ids:
        try:
            # Attempt to fetch a small sample to inspect structure
            # We use a chunked approach or just load a few rows if possible
            # For OpenML/HF, we might need to load metadata or a sample.
            # Assuming fetch functions can return a sample or we load locally if cached.
            
            # Strategy: Try to load the dataset (or a sample) to check columns.
            # Since we don't have the full file yet, we might need to fetch metadata.
            # For this task, we assume the dataset is already downloaded or we fetch a sample.
            # Let's try to fetch a sample.
            
            # Note: In a real pipeline, T012 would have downloaded these.
            # We assume they are in data/raw or we fetch a sample.
            # For robustness, we try to fetch a sample of 100 rows.
            
            df_sample = None
            source = None
            
            # Try OpenML
            try:
                df_sample, source = fetch_openml_dataset(ds_id, sample_size=100)
            except Exception as e_openml:
                try:
                    df_sample, source = fetch_huggingface_dataset(ds_id, sample_size=100)
                except Exception as e_hf:
                    logger.error(f"Failed to fetch {ds_id} from any source: {e_openml}, {e_hf}")
                    log_exclusion(ds_id, "fetch_failed", {"error": str(e_openml)})
                    results["excluded"].append(ds_id)
                    results["details"][ds_id] = {"reason": "fetch_failed"}
                    continue

            if df_sample is None:
                log_exclusion(ds_id, "empty_dataset")
                results["excluded"].append(ds_id)
                results["details"][ds_id] = {"reason": "empty_dataset"}
                continue

            # Check Sequential Stimuli
            if not check_sequential_stimuli(df_sample):
                log_exclusion(ds_id, "non_sequential_stimuli")
                results["excluded"].append(ds_id)
                results["details"][ds_id] = {"reason": "non_sequential_stimuli"}
                continue

            # Check Predictability Manipulation
            if not check_predictability_manipulation(df_sample):
                log_exclusion(ds_id, "no_predictability_manipulation")
                results["excluded"].append(ds_id)
                results["details"][ds_id] = {"reason": "no_predictability_manipulation"}
                continue

            # If passed
            log_inclusion(ds_id)
            results["included"].append(ds_id)
            results["details"][ds_id] = {"reason": "passed_filters"}

        except Exception as e:
            logger.error(f"Error processing dataset {ds_id}: {e}")
            log_exclusion(ds_id, "processing_error", {"error": str(e)})
            results["excluded"].append(ds_id)
            results["details"][ds_id] = {"reason": "processing_error"}

    return results

def run_filtering_pipeline() -> Dict[str, Any]:
    """
    Main entry point for the filtering pipeline.
    Reads dataset IDs from data/README.md (via download module logic or direct parsing)
    and filters them.
    """
    # We need to get the list of dataset IDs.
    # The download.py module has parse_readme_datasets.
    # We import it here to reuse.
    from download import parse_readme_datasets
    
    readme_path = Path("data/README.md")
    if not readme_path.exists():
        logger.error("data/README.md not found. Cannot proceed.")
        return {"included": [], "excluded": [], "error": "README not found"}

    datasets_info = parse_readme_datasets(readme_path)
    dataset_ids = [d['id'] for d in datasets_info]
    
    logger.info(f"Found {len(dataset_ids)} datasets to filter.")
    
    results = filter_datasets(dataset_ids)
    
    logger.info(f"Filtering complete. Included: {len(results['included'])}, Excluded: {len(results['excluded'])}")
    
    return results

if __name__ == "__main__":
    run_filtering_pipeline()
