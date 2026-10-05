import os
import logging
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import numpy as np
from scipy.stats import spearmanr
import pandas as pd

from utils import setup_logger, get_seeded_rng, check_fd, log_exclusion
from models import Subject

def load_metrics_and_behavioral_data(metrics_dir: Path, behavioral_dir: Path) -> Tuple[List[Dict], List[Dict]]:
    """
    Load all metric JSON files and behavioral data.
    Returns lists of dicts with 'subject_id', 'transition_count', 'dsst_score'.
    """
    metrics = []
    if metrics_dir.exists():
        for f in metrics_dir.glob("metrics_*.json"):
            import json
            with open(f, 'r') as fh:
                data = json.load(fh)
                metrics.append({
                    'subject_id': data['subject_id'],
                    'transition_count': data['transition_count']
                })

    behavioral = []
    if behavioral_dir.exists():
        # Assuming a CSV or JSON with subject_id and dsst_score
        # Try CSV first
        csv_path = behavioral_dir / "behavioral_data.csv"
        if csv_path.exists():
            df = pd.read_csv(csv_path)
            for _, row in df.iterrows():
                behavioral.append({
                    'subject_id': str(row['subject_id']),
                    'dsst_score': float(row['dsst_score'])
                })
        else:
            # Fallback to JSON if CSV missing, though spec implies CSV
            json_path = behavioral_dir / "behavioral_data.json"
            if json_path.exists():
                import json
                with open(json_path, 'r') as fh:
                    data = json.load(fh)
                    for item in data:
                        behavioral.append({
                            'subject_id': str(item['subject_id']),
                            'dsst_score': float(item['dsst_score'])
                        })

    return metrics, behavioral

def compute_spearman(x: np.ndarray, y: np.ndarray) -> Tuple[float, float]:
    """Compute Spearman correlation and p-value."""
    if len(x) == 0 or len(y) == 0:
        return 0.0, 1.0
    corr, p_val = spearmanr(x, y)
    if np.isnan(corr):
        return 0.0, 1.0
    return float(corr), float(p_val)

def apply_bonferroni(p_values: List[float], n_tests: int) -> List[float]:
    """Apply Bonferroni correction."""
    if n_tests == 0:
        return [1.0] * len(p_values)
    return [min(p * n_tests, 1.0) for p in p_values]

def compute_cohens_r(r: float) -> float:
    """Compute Cohen's r effect size (equivalent to correlation coefficient)."""
    return float(r)

def handle_extreme_p_values(p_val: float, floor: float = 1e-10, ceiling: float = 1.0) -> float:
    """Handle extreme p-values by flooring/ceiling."""
    return max(floor, min(ceiling, p_val))

def save_aggregated_statistics(metrics: List[Dict], behavioral: List[Dict], output_path: Path) -> None:
    """
    Save Aggregated Statistical Summary to TSV.
    Format: metric_pair, coef, p_val, adj_p, effect_size.
    One row per metric-behavior pair (aggregated), NOT per subject.
    """
    # Merge data by subject_id
    metrics_dict = {m['subject_id']: m['transition_count'] for m in metrics}
    behavioral_dict = {b['subject_id']: b['dsst_score'] for b in behavioral}

    common_ids = set(metrics_dict.keys()) & set(behavioral_dict.keys())
    if not common_ids:
        logging.warning("No common subjects found between metrics and behavioral data.")
        # Create empty file with header
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            f.write("metric_pair\tcoef\tp_val\tadj_p\teffect_size\n")
        return

    transition_counts = [metrics_dict[sid] for sid in common_ids]
    dsst_scores = [behavioral_dict[sid] for sid in common_ids]

    coef, p_val = compute_spearman(np.array(transition_counts), np.array(dsst_scores))
    adj_p = apply_bonferroni([p_val], 1)[0]
    effect_size = compute_cohens_r(coef)
    p_val = handle_extreme_p_values(p_val)

    metric_pair = "transition_count_vs_dsst_score"

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        f.write("metric_pair\tcoef\tp_val\tadj_p\teffect_size\n")
        f.write(f"{metric_pair}\t{coef:.6f}\t{p_val:.6f}\t{adj_p:.6f}\t{effect_size:.6f}\n")

def run_permutation_test(x: np.ndarray, y: np.ndarray, n_shuffles: int = 1000, seed: int = 42) -> float:
    """Run permutation test to get empirical p-value."""
    rng = get_seeded_rng(seed)
    observed_corr, _ = compute_spearman(x, y)
    null_dist = []
    for _ in range(n_shuffles):
        y_perm = rng.permutation(y)
        corr, _ = compute_spearman(x, y_perm)
        null_dist.append(corr)
    
    # Two-tailed p-value
    count = sum(abs(c) >= abs(observed_corr) for c in null_dist)
    return float(count) / n_shuffles

def calculate_permutation_p_value(observed_stat: float, null_dist: List[float]) -> float:
    """Calculate p-value from null distribution."""
    if not null_dist:
        return 1.0
    count = sum(abs(c) >= abs(observed_stat) for c in null_dist)
    return float(count) / len(null_dist)

def main():
    logger = setup_logger()
    logger.info("Starting statistical analysis and aggregation.")
    
    base_dir = Path(__file__).resolve().parent.parent
    metrics_dir = base_dir / "data" / "results"
    behavioral_dir = base_dir / "data" / "raw" # Assuming raw or processed
    output_path = base_dir / "data" / "analysis_results.tsv"

    metrics, behavioral = load_metrics_and_behavioral_data(metrics_dir, behavioral_dir)
    
    save_aggregated_statistics(metrics, behavioral, output_path)
    logger.info(f"Aggregated statistics saved to {output_path}")

if __name__ == "__main__":
    main()