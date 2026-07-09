import os
import logging
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import numpy as np
from scipy.stats import spearmanr

from models import Subject
from utils import setup_logger, log_exclusion

# Ensure logger is configured (T004 dependency)
logger = setup_logger()

def load_metrics_and_behavioral_data(subjects: List[Subject]) -> Tuple[List[Subject], List[float], List[float]]:
    """
    Load metrics and behavioral data for valid subjects.
    
    Returns:
        Tuple of (valid_subjects, transition_counts, dsst_scores)
    """
    valid_subjects = []
    transition_counts = []
    dsst_scores = []

    for subject in subjects:
        # T025b: Filter out subjects where has_valid_data() is False
        if not subject.has_valid_data():
            log_exclusion(reason="Missing fMRI_path or DSST_score", subject_id=subject.id)
            continue
        
        valid_subjects.append(subject)
        
        # Load metrics from JSON (assuming structure from T020)
        metrics_path = Path("data/results") / f"metrics_{subject.id}.json"
        if not metrics_path.exists():
            log_exclusion(reason="Metrics file missing", subject_id=subject.id)
            continue
        
        import json
        with open(metrics_path, 'r') as f:
            metrics_data = json.load(f)
        
        transition_counts.append(metrics_data['transition_count'])
        dsst_scores.append(subject.DSST_score)
    
    return valid_subjects, transition_counts, dsst_scores

def compute_spearman(transition_counts: List[float], dsst_scores: List[float]) -> Tuple[float, float]:
    """
    Compute Spearman rank correlation between transition counts and DSST scores.
    
    Args:
        transition_counts: List of network reconfigurability metrics
        dsst_scores: List of DSST behavioral scores
        
    Returns:
        Tuple of (correlation_coefficient, p_value)
    """
    if len(transition_counts) < 3:
        logger.warning("Insufficient data points for correlation analysis")
        return 0.0, 1.0
    
    coef, p_val = spearmanr(transition_counts, dsst_scores)
    return float(coef), float(p_val)

def apply_bonferroni(p_values: List[float], alpha: float = 0.05) -> List[float]:
    """
    Apply Bonferroni correction for multiple comparisons.
    
    Args:
        p_values: List of raw p-values
        alpha: Significance threshold (not directly used in calculation but kept for API consistency)
        
    Returns:
        List of adjusted p-values
    """
    n_tests = len(p_values)
    if n_tests == 0:
        return []
    
    # Bonferroni correction: multiply p-value by number of tests, cap at 1.0
    adjusted = [min(p * n_tests, 1.0) for p in p_values]
    return adjusted

def compute_cohens_r(r: float, n: int) -> float:
    """
    Compute Cohen's r effect size from Pearson/Spearman correlation coefficient.
    
    Args:
        r: Correlation coefficient
        n: Sample size
        
    Returns:
        Cohen's r effect size
    """
    # For Spearman, we can use the same formula as Pearson for effect size
    return r

def main():
    """
    Main entry point for statistical analysis pipeline.
    
    T025b Implementation: Filters subjects based on data validity before analysis.
    T026 Implementation: Applies Bonferroni correction to p-values.
    """
    logger.info("Starting statistical analysis pipeline")
    
    # Load subject data (in a real implementation, this would come from data/raw or data/processed)
    # For this implementation, we assume subjects are loaded from a manifest or directory scan
    subjects = []
    data_dir = Path("data/processed")
    if data_dir.exists():
        # Example: Load subjects from processed data directory
        # In a real scenario, this would parse actual subject manifests
        pass
    
    # T025b: Filter subjects and log exclusions
    valid_subjects, transition_counts, dsst_scores = load_metrics_and_behavioral_data(subjects)
    
    excluded_count = len(subjects) - len(valid_subjects)
    logger.info(f"Subject filtering complete: {excluded_count} subjects excluded, {len(valid_subjects)} remaining")
    
    if len(valid_subjects) < 3:
        logger.warning("Insufficient valid subjects for analysis. Exiting.")
        return
    
    # Compute correlation
    coef, p_val = compute_spearman(transition_counts, dsst_scores)
    logger.info(f"Spearman correlation: r={coef:.4f}, p={p_val:.4f}")
    
    # T026: Apply Bonferroni correction
    adj_p = apply_bonferroni([p_val])[0]
    logger.info(f"Bonferroni adjusted p-value: {adj_p:.4f}")
    
    # Compute effect size
    effect_size = compute_cohens_r(coef, len(valid_subjects))
    logger.info(f"Effect size (Cohen's r): {effect_size:.4f}")
    
    # Save results (T028)
    results_dir = Path("data/analysis_results")
    results_dir.mkdir(parents=True, exist_ok=True)
    
    import csv
    results_file = results_dir / "analysis_summary.tsv"
    with open(results_file, 'w', newline='') as f:
        writer = csv.writer(f, delimiter='\t')
        writer.writerow(['metric_pair', 'coef', 'p_val', 'adj_p', 'effect_size'])
        writer.writerow(['transition_count_vs_DSST', f"{coef:.6f}", f"{p_val:.6f}", f"{adj_p:.6f}", f"{effect_size:.6f}"])
    
    logger.info(f"Results saved to {results_file}")

if __name__ == "__main__":
    main()