import csv
import json
import logging
import os
import pickle
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import math

import numpy as np
from scipy.stats import spearmanr

# Importing from sibling modules based on API surface
# Note: log_exclusions is imported from logging_utils in other contexts,
# but here we read the exclusion log directly as JSON to filter data.
from src.logging_utils import log_exclusions

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_entropy_results(input_path: str) -> List[Dict[str, Any]]:
    """
    Load entropy results from a CSV file.
    Expected columns: task_id, entropy, cluster_count, excluded (optional)
    """
    results = []
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Entropy results not found at {input_path}")

    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Parse numeric fields
            try:
                row['entropy'] = float(row['entropy'])
                row['cluster_count'] = int(row.get('cluster_count', 0))
            except (ValueError, TypeError) as e:
                logger.warning(f"Skipping row due to parsing error: {row} - {e}")
                continue
            results.append(row)
    return results


def load_convergence_results(input_path: str) -> List[Dict[str, Any]]:
    """
    Load convergence results from a CSV file.
    Expected columns: task_id, k, converged, step, timestamp
    We need to map task_id to the first correct step (convergence step).
    If not converged, we might need to handle it (e.g., assign a max step or exclude).
    """
    results = {}
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Convergence results not found at {input_path}")

    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            task_id = row['task_id']
            try:
                k = int(row['k'])
                converged = row['converged'].lower() == 'true'
                step = int(row['step']) if row['step'] else None
            except (ValueError, TypeError) as e:
                logger.warning(f"Skipping row due to parsing error: {row} - {e}")
                continue

            # We want the first correct step.
            # If converged is True, step is the first correct step.
            # If converged is False, step might be the last attempted or None.
            # For correlation, we typically want the step where it converged.
            # If it never converged, we might exclude it or use a sentinel.
            # Let's assume for T015 we only consider converged cases or handle non-converged specifically.
            # The task says "convergence step", implying we need the step index.
            # If not converged, we can't define a "convergence step" in the standard sense.
            # We will filter for converged=True later.

            if task_id not in results:
                results[task_id] = []
            results[task_id].append({
                'k': k,
                'converged': converged,
                'step': step
            })
    return results


def load_exclusion_log(input_path: str) -> Dict[str, Any]:
    """
    Load the exclusion log to identify excluded task_ids.
    Expected schema: {excluded_count: int, excluded_rate: float, reasons: [str], excluded_task_ids: [str]}
    """
    path = Path(input_path)
    if not path.exists():
        logger.warning(f"Exclusion log not found at {input_path}. Proceeding without exclusion filtering.")
        return {'excluded_task_ids': []}

    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        return data


def load_strata_log(input_path: str) -> Dict[str, Any]:
    """
    Load the strata log to identify underpowered strata.
    Expected schema: {strata: [{name: str, count: int, underpowered: bool}]}
    """
    path = Path(input_path)
    if not path.exists():
        logger.warning(f"Strata log not found at {input_path}. Proceeding without strata filtering.")
        return {'strata': []}

    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        return data


def load_filtered_splits(input_path: str) -> List[Dict[str, Any]]:
    """
    Load filtered splits to determine which task_ids are valid (not underpowered).
    Expected schema: {train: [...], test: [...]} or just a list of task_ids.
    The schema in T004d says: {train: [{task_id: str, ...}], test: [{task_id: str, ...}]}
    """
    path = Path(input_path)
    if not path.exists():
        logger.warning(f"Filtered splits not found at {input_path}. Proceeding without strata filtering.")
        return []

    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        valid_task_ids = set()
        for split_name in ['train', 'test']:
            if split_name in data:
                for item in data[split_name]:
                    if 'task_id' in item:
                        valid_task_ids.add(item['task_id'])
        return list(valid_task_ids)


def compute_spearman_correlation(entropy_data: List[Dict], convergence_data: List[Dict]) -> Tuple[float, float]:
    """
    Compute Spearman correlation between entropy and convergence step.
    Returns (rho, p_value).
    """
    entropies = []
    steps = []

    for ent in entropy_data:
        task_id = ent['task_id']
        if task_id in convergence_data:
            conv_entry = convergence_data[task_id]
            # We need the step where it converged.
            # Filter for converged=True and take the minimum step?
            # Or if there's only one converged entry per task_id.
            converged_entries = [c for c in conv_entry if c['converged']]
            if not converged_entries:
                continue  # Skip if never converged

            # Assume the first converged entry is the one we care about, or min step
            # Let's take the minimum step among converged entries
            min_step = min(c['step'] for c in converged_entries)
            entropies.append(ent['entropy'])
            steps.append(min_step)

    if len(entropies) < 2:
        logger.warning("Not enough data points to compute correlation.")
        return 0.0, 1.0

    rho, p_value = spearmanr(entropies, steps)
    return rho, p_value


def save_correlation_results(output_path: str, rho: float, p_value: float, filtered_count: int, total_count: int):
    """
    Save correlation results to a JSON file.
    """
    results = {
        'spearman_rho': rho,
        'p_value': p_value,
        'filtered_count': filtered_count,
        'total_count': total_count,
        'significant': p_value < 0.05
    }
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Correlation results saved to {output_path}")


def run_analysis(entropy_path: str, convergence_path: str, output_path: str,
                 exclusion_log_path: Optional[str] = None,
                 strata_log_path: Optional[str] = None,
                 filtered_splits_path: Optional[str] = None):
    """
    Main analysis function to compute Spearman correlation with filtering.
    """
    logger.info(f"Loading entropy results from {entropy_path}")
    entropy_data = load_entropy_results(entropy_path)
    logger.info(f"Loaded {len(entropy_data)} entropy records.")

    logger.info(f"Loading convergence results from {convergence_path}")
    raw_convergence = load_convergence_results(convergence_path)
    # Convert list of lists to dict for easier lookup
    convergence_data = {k: v for k, v in raw_convergence.items()}
    logger.info(f"Loaded convergence data for {len(convergence_data)} unique task_ids.")

    # Get excluded task_ids
    excluded_task_ids = set()
    if exclusion_log_path:
        exclusion_log = load_exclusion_log(exclusion_log_path)
        excluded_task_ids = set(exclusion_log.get('excluded_task_ids', []))
        logger.info(f"Excluded {len(excluded_task_ids)} task_ids based on exclusion log.")

    # Get valid task_ids from filtered splits (to exclude underpowered strata)
    valid_task_ids = set()
    if filtered_splits_path:
        valid_task_ids = set(load_filtered_splits(filtered_splits_path))
        logger.info(f"Found {len(valid_task_ids)} valid task_ids from filtered splits.")

    # Filter entropy data
    filtered_entropy = []
    for ent in entropy_data:
        task_id = ent['task_id']
        # Exclude if in exclusion log
        if task_id in excluded_task_ids:
            continue
        # Exclude if not in valid task_ids (underpowered strata)
        if filtered_splits_path and task_id not in valid_task_ids:
            continue
        filtered_entropy.append(ent)

    logger.info(f"Filtered entropy data: {len(filtered_entropy)} records remaining.")

    # Filter convergence data to match filtered entropy task_ids
    filtered_convergence = {}
    for task_id, conv_entries in convergence_data.items():
        if task_id in [e['task_id'] for e in filtered_entropy]:
            filtered_convergence[task_id] = conv_entries

    # Compute correlation
    rho, p_value = compute_spearman_correlation(filtered_entropy, filtered_convergence)
    logger.info(f"Spearman correlation: rho={rho}, p_value={p_value}")

    # Save results
    save_correlation_results(output_path, rho, p_value, len(filtered_entropy), len(entropy_data))

    return rho, p_value


def train_logistic_router(entropy_data: List[Dict], convergence_data: List[Dict], output_model_path: str):
    """
    Train a logistic regression router to predict optimal loop count.
    This is a placeholder for T019, but included here for completeness if analysis.py is used for US2.
    """
    # Implementation would go here for T019
    pass


def save_router_model(model, output_path: str):
    """
    Save the trained router model.
    """
    with open(output_path, 'wb') as f:
        pickle.dump(model, f)


def generate_significance_flag(p_value: float, threshold: float = 0.05) -> bool:
    """
    Generate a significance flag based on p-value.
    """
    return p_value < threshold


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Run correlation analysis between entropy and convergence.")
    parser.add_argument('--entropy', type=str, required=True, help="Path to entropy results CSV")
    parser.add_argument('--convergence', type=str, required=True, help="Path to convergence results CSV")
    parser.add_argument('--output', type=str, required=True, help="Path to output JSON file")
    parser.add_argument('--exclusion-log', type=str, default=None, help="Path to exclusion log JSON")
    parser.add_argument('--strata-log', type=str, default=None, help="Path to strata log JSON")
    parser.add_argument('--filtered-splits', type=str, default=None, help="Path to filtered splits JSON")

    args = parser.parse_args()

    run_analysis(
        entropy_path=args.entropy,
        convergence_path=args.convergence,
        output_path=args.output,
        exclusion_log_path=args.exclusion_log,
        strata_log_path=args.strata_log,
        filtered_splits_path=args.filtered_splits
    )


if __name__ == "__main__":
    main()