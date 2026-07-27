"""
Fallback logic for data availability handling.

Implements automatic switching to bootstrap resampling if fewer than
three independent runs are detected in the harmonized dataset.
Otherwise, proceeds with normal leave-one-out cross-validation path.
"""
import logging
import numpy as np
import pandas as pd
from typing import List, Tuple, Optional
from pathlib import Path

from data.loaders import HarmonizedDataset
from config import get_logger

logger = get_logger(__name__)


def detect_independent_runs(dataset: HarmonizedDataset) -> List[str]:
    """
    Detect the number of independent experimental runs in the dataset.

    Args:
        dataset: The HarmonizedDataset object containing the data.

    Returns:
        List of unique run identifiers found in the dataset.
    """
    if dataset.metadata is None or 'run_ids' not in dataset.metadata:
        # Fallback: try to infer from dataframe columns if metadata missing
        if hasattr(dataset, 'data') and isinstance(dataset.data, pd.DataFrame):
            if 'run_id' in dataset.data.columns:
                return dataset.data['run_id'].unique().tolist()
        return []

    return dataset.metadata.get('run_ids', [])


def bootstrap_resample_dataset(
    dataset: HarmonizedDataset,
    n_bootstrap: int = 1000,
    random_state: Optional[int] = None
) -> Tuple[List[HarmonizedDataset], dict]:
    """
    Generate bootstrap resamples of the available runs.

    Args:
        dataset: The HarmonizedDataset to resample.
        n_bootstrap: Number of bootstrap iterations.
        random_state: Random seed for reproducibility.

    Returns:
        Tuple of (list of resampled datasets, metadata dict with stats).
    """
    rng = np.random.default_rng(random_state)
    runs = detect_independent_runs(dataset)
    n_runs = len(runs)

    if n_runs == 0:
        raise ValueError("No independent runs detected for bootstrap resampling.")

    logger.info(f"Performing bootstrap resampling with {n_bootstrap} iterations "
                f"from {n_runs} available run(s).")

    resampled_datasets = []
    bootstrap_stats = {
        'n_bootstrap': n_bootstrap,
        'n_original_runs': n_runs,
        'method': 'bootstrap'
    }

    # If we have actual data in the dataset, resample indices
    if hasattr(dataset, 'data') and isinstance(dataset.data, pd.DataFrame):
        data_df = dataset.data
        n_rows = len(data_df)

        for i in range(n_bootstrap):
            # Resample rows with replacement
            indices = rng.choice(n_rows, size=n_rows, replace=True)
            resampled_df = data_df.iloc[indices].copy()
            resampled_df = resampled_df.sort_values('separation_m').reset_index(drop=True)

            # Create new dataset with resampled data
            # Preserve metadata but update run_ids to indicate bootstrap
            new_metadata = dataset.metadata.copy() if dataset.metadata else {}
            new_metadata['bootstrap_iteration'] = i
            new_metadata['method'] = 'bootstrap'

            new_dataset = HarmonizedDataset(
                data=resampled_df,
                covariance=dataset.covariance,
                metadata=new_metadata,
                grid_info=dataset.grid_info
            )
            resampled_datasets.append(new_dataset)

    else:
        # If no dataframe available, create placeholder datasets
        # This handles edge cases where only metadata is present
        for i in range(n_bootstrap):
            new_metadata = dataset.metadata.copy() if dataset.metadata else {}
            new_metadata['bootstrap_iteration'] = i
            new_metadata['method'] = 'bootstrap'

            # Create a minimal dataset (will fail gracefully if actual data needed)
            new_dataset = HarmonizedDataset(
                data=dataset.data if hasattr(dataset, 'data') else None,
                covariance=dataset.covariance,
                metadata=new_metadata,
                grid_info=dataset.grid_info
            )
            resampled_datasets.append(new_dataset)

    logger.info(f"Generated {len(resampled_datasets)} bootstrap resamples.")
    return resampled_datasets, bootstrap_stats


def prepare_analysis_dataset(
    dataset: HarmonizedDataset,
    fallback_to_bootstrap: bool = True,
    n_bootstrap: int = 1000,
    random_state: Optional[int] = None
) -> Tuple[List[HarmonizedDataset], str, dict]:
    """
    Prepare the dataset(s) for analysis, applying fallback logic if needed.

    This function implements the core requirement for T016:
    - If fewer than 3 independent runs are detected:
      -> Switch to bootstrap resampling
    - Otherwise:
      -> Return the original dataset for leave-one-out (handled in T030)

    Args:
        dataset: The HarmonizedDataset to process.
        fallback_to_bootstrap: Whether to enable bootstrap fallback.
        n_bootstrap: Number of bootstrap iterations if fallback is triggered.
        random_state: Random seed for bootstrap.

    Returns:
        Tuple of (list of datasets to use, method name, metadata dict).
    """
    runs = detect_independent_runs(dataset)
    n_runs = len(runs)

    logger.info(f"Detected {n_runs} independent run(s): {runs}")

    if n_runs < 3 and fallback_to_bootstrap:
        logger.warning(f"Only {n_runs} run(s) detected (< 3). "
                     f"Switching to bootstrap resampling method.")

        resampled_datasets, stats = bootstrap_resample_dataset(
            dataset,
            n_bootstrap=n_bootstrap,
            random_state=random_state
        )

        return resampled_datasets, 'bootstrap', stats

    else:
        logger.info(f"Found {n_runs} run(s) (>= 3). Proceeding with "
                   f"leave-one-out cross-validation (T030).")

        # Return single dataset for LOO processing
        return [dataset], 'leave_one_out', {
            'n_runs': n_runs,
            'method': 'leave_one_out'
        }


def main():
    """
    Main entry point for fallback logic demonstration/testing.

    This script:
    1. Loads a harmonized dataset (or creates one if none exists)
    2. Detects the number of independent runs
    3. Applies fallback logic (bootstrap vs leave-one-out)
    4. Outputs the result to data/results/fallback_decision.json
    """
    from utils.versioning import create_state_manager
    import json

    # Setup paths
    project_root = Path(__file__).parent.parent.parent
    data_results_dir = project_root / 'data' / 'results'
    data_results_dir.mkdir(parents=True, exist_ok=True)

    # Try to load an existing harmonized dataset
    # In a real pipeline, this would be the output of harmonize.py
    harmonized_path = project_root / 'data' / 'processed' / 'harmonized_dataset.csv'

    if harmonized_path.exists():
        logger.info(f"Loading existing harmonized dataset from {harmonized_path}")
        df = pd.read_csv(harmonized_path)

        # Create a minimal HarmonizedDataset
        dataset = HarmonizedDataset(
            data=df,
            covariance=None,  # Would be loaded separately in real pipeline
            metadata={'run_ids': df['run_id'].unique().tolist() if 'run_id' in df.columns else []},
            grid_info=None
        )
    else:
        logger.warning(f"No harmonized dataset found at {harmonized_path}. "
                     "Creating a minimal test dataset for demonstration.")

        # Create a minimal test dataset with 2 runs (triggers bootstrap)
        test_data = pd.DataFrame({
            'separation_m': [1e-5, 2e-5, 3e-5, 4e-5, 5e-5],
            'force_n': [1e-12, 2e-12, 3e-12, 4e-12, 5e-12],
            'run_id': ['run_A'] * 3 + ['run_B'] * 2  # Only 2 runs -> triggers bootstrap
        })

        dataset = HarmonizedDataset(
            data=test_data,
            covariance=None,
            metadata={'run_ids': ['run_A', 'run_B']},
            grid_info=None
        )

    # Apply fallback logic
    datasets, method, stats = prepare_analysis_dataset(
        dataset,
        fallback_to_bootstrap=True,
        n_bootstrap=100,  # Small number for demo
        random_state=42
    )

    # Prepare output
    output = {
        'method_selected': method,
        'detection_stats': stats,
        'num_datasets_generated': len(datasets),
        'timestamp': str(pd.Timestamp.now())
    }

    # Write output
    output_path = data_results_dir / 'fallback_decision.json'
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2)

    logger.info(f"Fallback decision written to {output_path}")
    logger.info(f"Selected method: {method}")
    logger.info(f"Number of datasets generated: {len(datasets)}")

    return output


if __name__ == '__main__':
    main()