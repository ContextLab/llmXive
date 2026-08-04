"""
Fallback logic for data analysis:
- Detect number of independent runs in the harmonized dataset.
- If fewer than 3 runs are detected, switch to bootstrap resampling.
- Otherwise, proceed with normal leave-one-out path (handled in T030).
"""
import logging
import numpy as np
import pandas as pd
from typing import List, Tuple, Optional
from pathlib import Path
from data.loaders import HarmonizedDataset

logger = logging.getLogger(__name__)

def detect_independent_runs(dataset: HarmonizedDataset) -> int:
    """
    Detect the number of independent experimental runs in the dataset.
    
    Args:
        dataset: The HarmonizedDataset object containing the data.
        
    Returns:
        The number of independent runs detected.
    """
    if dataset.run_metadata is None or len(dataset.run_metadata) == 0:
        logger.warning("No run metadata found. Assuming single run.")
        return 1
    
    # Count unique run identifiers from metadata
    # Assuming run_metadata is a list of dicts or a DataFrame with 'run_id'
    if isinstance(dataset.run_metadata, list):
        unique_runs = set()
        for run in dataset.run_metadata:
            if isinstance(run, dict) and 'run_id' in run:
                unique_runs.add(run['run_id'])
            else:
                # If metadata is just a list of strings or lacks run_id, count items
                unique_runs.add(str(run))
        return len(unique_runs)
    elif isinstance(dataset.run_metadata, pd.DataFrame):
        if 'run_id' in dataset.run_metadata.columns:
            return dataset.run_metadata['run_id'].nunique()
        elif 'experiment_id' in dataset.run_metadata.columns:
            return dataset.run_metadata['experiment_id'].nunique()
        else:
            # Fallback: count rows if no ID column
            return len(dataset.run_metadata)
    else:
        logger.warning(f"Unexpected run_metadata type: {type(dataset.run_metadata)}. Assuming single run.")
        return 1

def bootstrap_resample_dataset(dataset: HarmonizedDataset, n_bootstrap: int = 1000, random_state: Optional[int] = None) -> List[HarmonizedDataset]:
    """
    Generate bootstrap resamples of the dataset for statistical analysis.
    
    Args:
        dataset: The original HarmonizedDataset.
        n_bootstrap: Number of bootstrap samples to generate.
        random_state: Random seed for reproducibility.
        
    Returns:
        A list of HarmonizedDataset objects, each being a bootstrap resample.
    """
    if random_state is not None:
        np.random.seed(random_state)
    
    if dataset.separation is None or dataset.force is None:
        raise ValueError("Cannot bootstrap: dataset has no separation or force data.")
    
    n_points = len(dataset.separation)
    if n_points == 0:
        raise ValueError("Cannot bootstrap: dataset is empty.")
    
    resampled_datasets = []
    
    for i in range(n_bootstrap):
        # Generate indices with replacement
        indices = np.random.choice(n_points, size=n_points, replace=True)
        
        # Create resampled arrays
        sep_resampled = dataset.separation[indices]
        force_resampled = dataset.force[indices]
        
        # Sort by separation to maintain physical order
        sort_idx = np.argsort(sep_resampled)
        sep_resampled = sep_resampled[sort_idx]
        force_resampled = force_resampled[sort_idx]
        
        # Reconstruct covariance if available
        cov_resampled = None
        if dataset.covariance_matrix is not None:
            # For bootstrap, we typically resample the data points and their associated errors.
            # A simple approximation is to take the diagonal elements (variances) and resample them,
            # then reconstruct a diagonal covariance. More complex methods exist but this is a baseline.
            diag = np.diag(dataset.covariance_matrix)
            diag_resampled = diag[indices]
            cov_resampled = np.diag(diag_resampled)
        
        # Create new dataset object
        resampled_dataset = HarmonizedDataset(
            separation=sep_resampled,
            force=force_resampled,
            covariance_matrix=cov_resampled,
            run_metadata=dataset.run_metadata, # Keep original metadata for context
            source_files=dataset.source_files
        )
        resampled_datasets.append(resampled_dataset)
        
    return resampled_datasets

def prepare_analysis_dataset(dataset: HarmonizedDataset, min_runs_required: int = 3) -> Tuple[HarmonizedDataset, bool]:
    """
    Prepare the dataset for analysis, applying fallback logic if necessary.
    
    Args:
        dataset: The input HarmonizedDataset.
        min_runs_required: The minimum number of independent runs required for leave-one-out.
        
    Returns:
        A tuple (dataset_to_use, is_bootstrap).
        - dataset_to_use: The dataset ready for analysis (original or resampled context).
        - is_bootstrap: True if bootstrap resampling was triggered, False otherwise.
    """
    n_runs = detect_independent_runs(dataset)
    logger.info(f"Detected {n_runs} independent runs.")
    
    if n_runs < min_runs_required:
        logger.warning(f"Fewer than {min_runs_required} independent runs detected ({n_runs}). "
                     f"Switching to bootstrap resampling for robustness analysis.")
        # In the context of T016, we return the original dataset but flag that bootstrap is needed.
        # The actual resampling happens in the robustness module (T030) or here if called directly.
        # For T016's specific role, we prepare the state and flag.
        return dataset, True
    else:
        logger.info(f"Sufficient runs ({n_runs}) detected. Proceeding with leave-one-out path (T030).")
        return dataset, False

def main():
    """
    Main entry point for testing fallback logic.
    This function demonstrates the logic but expects a real dataset to be passed in a real pipeline.
    """
    logging.basicConfig(level=logging.INFO)
    
    # This is a placeholder for integration. In a real run, this would be called by the pipeline
    # after T013-VAL and before T030.
    logger.info("Fallback logic module loaded. Ready to detect runs and switch strategies.")
    logger.info("Usage: Import detect_independent_runs, prepare_analysis_dataset, and bootstrap_resample_dataset.")

if __name__ == "__main__":
    main()
