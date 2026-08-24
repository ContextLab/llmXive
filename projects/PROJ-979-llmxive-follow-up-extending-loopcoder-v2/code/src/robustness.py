import csv
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import math
import pandas as pd
from scipy.stats import spearmanr

from src.config import load_config, get_config_value
from src.logging_utils import save_results_to_json

logger = logging.getLogger(__name__)

def load_full_splits(path: str = "data/processed/full_splits.json") -> Dict[str, Any]:
    """Load the full splits JSON."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Full splits not found at {path}")
    with open(p, 'r') as f:
        return json.load(f)

def load_strata_log(path: str = "data/processed/strata_log.json") -> Dict[str, Any]:
    """Load the strata log JSON."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Strata log not found at {path}")
    with open(p, 'r') as f:
        return json.load(f)

def load_entropy_results(path: str = "data/processed/entropy_results.csv") -> pd.DataFrame:
    """Load entropy results into a DataFrame."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Entropy results not found at {path}")
    return pd.read_csv(p)

def load_convergence_results(path: str) -> pd.DataFrame:
    """Load convergence results from a CSV file."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Convergence results not found at {path}")
    return pd.read_csv(p)

def get_stratum_for_task(task_id: str, strata_log: Dict[str, Any]) -> Optional[str]:
    """Retrieve the stratum name for a given task_id."""
    # The strata_log structure is expected to have a 'strata' key containing a list of strata definitions
    # Each stratum definition likely has a 'stratum_name' and a list of 'task_ids' or similar.
    # If the structure is different (e.g., a flat map), adjust accordingly.
    # Assuming structure: {'strata': [{'name': 'easy', 'task_ids': [...]}, ...]}
    strata = strata_log.get('strata', [])
    for stratum in strata:
        if 'task_ids' in stratum and task_id in stratum['task_ids']:
            return stratum.get('name') or stratum.get('stratum_name')
        # Fallback check if task_ids are keys in a dict
        if 'tasks' in stratum and task_id in stratum['tasks']:
            return stratum.get('name') or stratum.get('stratum_name')
    return None

def compute_per_stratum_correlation(
    entropy_df: pd.DataFrame,
    convergence_df: pd.DataFrame,
    strata_log: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """Compute Spearman correlation per stratum."""
    merged = pd.merge(entropy_df, convergence_df, on='task_id', how='inner')
    results = []

    strata = strata_log.get('strata', [])
    for stratum in strata:
        stratum_name = stratum.get('name') or stratum.get('stratum_name')
        stratum_tasks = set(stratum.get('task_ids', []) or stratum.get('tasks', []))

        # Filter merged data for this stratum
        stratum_data = merged[merged['task_id'].isin(stratum_tasks)]

        if len(stratum_data) < 2:
            logger.warning(f"Stratum {stratum_name} has fewer than 2 samples. Skipping correlation.")
            results.append({
                'stratum': stratum_name,
                'n_samples': len(stratum_data),
                'rho': None,
                'p_value': None,
                'status': 'insufficient_samples'
            })
            continue

        # Compute Spearman correlation between entropy and first_correct_step (or time_to_event)
        # Assuming 'entropy' and 'first_correct_step' columns exist
        if 'entropy' not in stratum_data.columns or 'first_correct_step' not in stratum_data.columns:
            logger.error(f"Required columns missing in stratum data for {stratum_name}")
            continue

        rho, p_value = spearmanr(stratum_data['entropy'], stratum_data['first_correct_step'])
        results.append({
            'stratum': stratum_name,
            'n_samples': len(stratum_data),
            'rho': float(rho) if not math.isnan(rho) else None,
            'p_value': float(p_value) if not math.isnan(p_value) else None,
            'status': 'computed'
        })

    return results

def merge_convergence_results(
    core_path: str = "data/processed/convergence_results_core.csv",
    sensitivity_path: str = "data/processed/convergence_results_sensitivity.csv",
    output_path: str = "data/processed/convergence_results_merged.csv"
) -> pd.DataFrame:
    """Merge core and sensitivity convergence results."""
    core_path = Path(core_path)
    sensitivity_path = Path(sensitivity_path)
    output_path = Path(output_path)

    if not core_path.exists():
        raise FileNotFoundError(f"Core convergence results not found at {core_path}")
    if not sensitivity_path.exists():
        raise FileNotFoundError(f"Sensitivity convergence results not found at {sensitivity_path}")

    df_core = pd.read_csv(core_path)
    df_sens = pd.read_csv(sensitivity_path)

    # Concatenate and drop duplicates if any (based on task_id and k)
    merged = pd.concat([df_core, df_sens], ignore_index=True)
    merged = merged.drop_duplicates(subset=['task_id', 'k'], keep='first')

    merged.to_csv(output_path, index=False)
    logger.info(f"Merged convergence results saved to {output_path}")
    return merged

def run_sensitivity_sweep(
    merged_convergence_path: str = "data/processed/convergence_results_merged.csv",
    output_path: str = "data/processed/sensitivity_sweep.json"
) -> Dict[str, Any]:
    """
    Perform sensitivity sweep: compute Spearman rho for thresholds k in {2, 3, 4}.
    Compare against baseline (k={1, 2, 3}) and output results.
    """
    merged_df = pd.read_csv(merged_convergence_path)

    if 'first_correct_step' not in merged_df.columns:
        raise ValueError("Column 'first_correct_step' not found in merged convergence results.")

    # Define thresholds
    thresholds = [2, 3, 4]
    baseline_thresholds = [1, 2, 3]

    results = {
        'baseline': {},
        'sweep': {}
    }

    # Compute baseline correlation (using all rows where first_correct_step <= 3)
    # For baseline, we consider the standard convergence metric
    baseline_data = merged_df[merged_df['first_correct_step'] <= 3].copy()
    # If we need to adjust 'first_correct_step' for baseline (e.g., treat >3 as censored),
    # but the task implies comparing correlation at different cutoffs.
    # Let's assume we compute correlation on the subset of data that converges within the threshold.
    # However, the task says "compute Spearman ρ for thresholds k ∈ {2,3,4}".
    # This likely means: for each threshold K, consider only problems that converge by K,
    # and compute correlation between entropy and first_correct_step.

    # Baseline: K=3 (standard)
    baseline_subset = merged_df[merged_df['first_correct_step'] <= 3]
    if len(baseline_subset) > 1:
        rho_base, p_base = spearmanr(baseline_subset['entropy'], baseline_subset['first_correct_step'])
        results['baseline'] = {
            'threshold': 3,
            'n_samples': len(baseline_subset),
            'rho': float(rho_base) if not math.isnan(rho_base) else None,
            'p_value': float(p_base) if not math.isnan(p_base) else None
        }
    else:
        results['baseline'] = {
            'threshold': 3,
            'n_samples': len(baseline_subset),
            'rho': None,
            'p_value': None,
            'note': 'Insufficient samples for baseline'
        }

    # Sweep for K in {2, 3, 4}
    for k in thresholds:
        subset = merged_df[merged_df['first_correct_step'] <= k]
        if len(subset) > 1:
            rho, p_val = spearmanr(subset['entropy'], subset['first_correct_step'])
            results['sweep'][k] = {
                'n_samples': len(subset),
                'rho': float(rho) if not math.isnan(rho) else None,
                'p_value': float(p_val) if not math.isnan(p_val) else None
            }
        else:
            results['sweep'][k] = {
                'n_samples': len(subset),
                'rho': None,
                'p_value': None,
                'note': 'Insufficient samples'
            }

    # Save results
    save_results_to_json(results, output_path)
    logger.info(f"Sensitivity sweep results saved to {output_path}")
    return results

def main():
    """Main entry point for the robustness analysis, specifically the sensitivity sweep."""
    logging.basicConfig(level=logging.INFO)

    # Load data
    try:
        # Ensure merged file exists (T025c dependency)
        merged_path = "data/processed/convergence_results_merged.csv"
        if not Path(merged_path).exists():
            # Attempt to merge if not exists (should be done by T025c, but safety check)
            merge_convergence_results(
                core_path="data/processed/convergence_results_core.csv",
                sensitivity_path="data/processed/convergence_results_sensitivity.csv",
                output_path=merged_path
            )

        # Run sensitivity sweep
        output_json = "data/processed/sensitivity_sweep.json"
        run_sensitivity_sweep(
            merged_convergence_path=merged_path,
            output_path=output_json
        )
        logger.info("Sensitivity sweep completed successfully.")

    except Exception as e:
        logger.error(f"Error during sensitivity sweep: {e}")
        raise

if __name__ == "__main__":
    main()