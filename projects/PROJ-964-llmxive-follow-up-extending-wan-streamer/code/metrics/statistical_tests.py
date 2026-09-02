"""
T086: Reconcile run-book vs implementation for statistical_tests.py

This script serves as the canonical entry point for statistical analysis.
It wraps the logic from:
- T045 (analyze_latency_bias)
- T071 (Propensity Score Matching)
- T049 (TOST Equivalence Test)

It reads the hybrid output and baseline metrics, performs propensity score matching
to create a balanced dataset, runs the TOST equivalence test on FID degradation,
and writes the results to data/metrics/statistical_tests_results.json.
"""
import os
import sys
import json
import argparse
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import pandas as pd
import numpy as np
from scipy import stats
from sklearn.linear_model import LogisticRegression
from sklearn.neighbors import NearestNeighbors

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from data.preprocess import load_config
from inference.analyze_latency_bias import load_hybrid_output, propensity_score_matching, stratified_bootstrap
from metrics.tost_equivalence import load_hybrid_output as load_hybrid_for_tost, load_baseline_metrics, perform_tost_test

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(PROJECT_ROOT / "data" / "logs" / "statistical_tests.log")
    ]
)
logger = logging.getLogger(__name__)


def load_hybrid_metrics_for_matching(hybrid_output_path: Path, baseline_metrics_path: Path) -> pd.DataFrame:
    """
    Load hybrid output and baseline metrics, merge them, and prepare for propensity matching.
    """
    logger.info(f"Loading hybrid output from {hybrid_output_path}")
    if not hybrid_output_path.exists():
        raise FileNotFoundError(f"Hybrid output not found: {hybrid_output_path}")
    
    hybrid_df = pd.read_parquet(hybrid_output_path)
    
    logger.info(f"Loading baseline metrics from {baseline_metrics_path}")
    if not baseline_metrics_path.exists():
        raise FileNotFoundError(f"Baseline metrics not found: {baseline_metrics_path}")
    
    baseline_df = pd.read_parquet(baseline_metrics_path)
    
    # Merge on frame_id or segment_id
    if 'frame_id' in hybrid_df.columns and 'frame_id' in baseline_df.columns:
        merged_df = pd.merge(hybrid_df, baseline_df, on='frame_id', how='inner')
    elif 'segment_id' in hybrid_df.columns and 'segment_id' in baseline_df.columns:
        merged_df = pd.merge(hybrid_df, baseline_df, on='segment_id', how='inner')
    else:
        # Fallback: assume they are aligned row-wise if no common key
        logger.warning("No common key found. Assuming row-wise alignment.")
        if len(hybrid_df) != len(baseline_df):
            raise ValueError("Hybrid and baseline datasets have different lengths and no common key.")
        merged_df = pd.concat([hybrid_df, baseline_df], axis=1)
    
    # Ensure we have the necessary columns
    required_cols = ['latency', 'fid_degradation', 'frame_complexity']
    missing_cols = [c for c in required_cols if c not in merged_df.columns]
    if missing_cols:
        # Try to derive or find alternatives
        if 'latency' not in merged_df.columns and 'latency_reduction' in merged_df.columns:
            merged_df['latency'] = merged_df['latency_reduction'] # Assuming reduction is stored
        if 'fid_degradation' not in merged_df.columns and 'fid' in merged_df.columns:
            # If we have raw FID, we might need to compute degradation, but for now assume column exists
            pass
        
        missing_cols = [c for c in required_cols if c not in merged_df.columns]
        if missing_cols:
            raise ValueError(f"Missing required columns for matching: {missing_cols}")
    
    # Create a binary treatment column: 1 if skipped (latency reduced significantly), 0 otherwise
    # Heuristic: if latency is below a certain threshold or latency_reduction is high
    # For simplicity, assume 'latency_reduction' or 'latency' indicates treatment
    if 'latency_reduction' in merged_df.columns:
        # Treatment = 1 if latency_reduction > 0 (meaning we saved time)
        merged_df['treatment'] = (merged_df['latency_reduction'] > 0).astype(int)
    elif 'latency' in merged_df.columns:
        # If we have absolute latency, treat as 1 if it's lower than a baseline average
        baseline_latency = merged_df['latency'].mean()
        merged_df['treatment'] = (merged_df['latency'] < baseline_latency * 0.8).astype(int) # Arbitrary threshold
    else:
        raise ValueError("Cannot determine treatment status from available columns.")
    
    return merged_df


def run_propensity_score_matching(df: pd.DataFrame, covariates: List[str]) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Perform propensity score matching to balance covariates between treatment and control groups.
    """
    logger.info("Running propensity score matching...")
    
    # Filter out rows with missing covariates
    df_clean = df.dropna(subset=covariates + ['treatment'])
    
    if len(df_clean) < 10:
        logger.warning("Not enough data for matching. Returning original data.")
        return df_clean, {"status": "insufficient_data", "matched_count": len(df_clean)}
    
    # Fit propensity score model
    X = df_clean[covariates].values
    y = df_clean['treatment'].values
    
    try:
        model = LogisticRegression()
        model.fit(X, y)
        propensity_scores = model.predict_proba(X)[:, 1]
        df_clean['propensity_score'] = propensity_scores
    except Exception as e:
        logger.error(f"Propensity score model failed: {e}")
        return df_clean, {"status": "model_failed", "matched_count": len(df_clean)}
    
    # Simple nearest neighbor matching
    treated = df_clean[df_clean['treatment'] == 1].copy()
    control = df_clean[df_clean['treatment'] == 0].copy()
    
    if len(treated) == 0 or len(control) == 0:
        logger.warning("No treated or control group found.")
        return df_clean, {"status": "no_groups", "matched_count": 0}
    
    # Match each treated unit to the closest control unit
    treated_scores = treated['propensity_score'].values.reshape(-1, 1)
    control_scores = control['propensity_score'].values.reshape(-1, 1)
    
    nbrs = NearestNeighbors(n_neighbors=1)
    nbrs.fit(control_scores)
    distances, indices = nbrs.kneighbors(treated_scores)
    
    matched_control_indices = indices.flatten()
    matched_control = control.iloc[matched_control_indices].reset_index(drop=True)
    matched_treated = treated.reset_index(drop=True)
    
    matched_df = pd.concat([matched_treated, matched_control], ignore_index=True)
    matched_df['matched'] = True
    
    # Diagnostics
    diagnostics = {
        "status": "success",
        "matched_count": len(matched_df),
        "treated_count": len(treated),
        "control_count": len(control),
        "covariate_balance": {}
    }
    
    for col in covariates:
        treated_mean = matched_treated[col].mean()
        control_mean = matched_control[col].mean()
        std_diff = (treated_mean - control_mean) / np.sqrt((matched_treated[col].var() + matched_control[col].var()) / 2)
        diagnostics["covariate_balance"][col] = {
            "treated_mean": float(treated_mean),
            "control_mean": float(control_mean),
            "standardized_diff": float(std_diff)
        }
    
    return matched_df, diagnostics


def run_tost_on_matched_data(df: pd.DataFrame, result_path: Path):
    """
    Run TOST equivalence test on the matched dataset.
    """
    logger.info("Running TOST equivalence test on matched data...")
    
    if 'fid_degradation' not in df.columns:
        logger.error("fid_degradation column not found in matched data.")
        return None
    
    # We want to test if the mean difference in FID degradation between treatment and control is within [-0.05, 0.05]
    # But since we are looking at the effect of skipping, we might test if the mean degradation is close to 0.
    # For TOST, we compare two groups. Here, we can compare the FID degradation of skipped vs non-skipped frames.
    # However, the matched_df contains both. We need to split by treatment.
    
    if 'treatment' not in df.columns:
        logger.error("treatment column not found in matched data.")
        return None
    
    skipped_fid = df[df['treatment'] == 1]['fid_degradation'].dropna()
    non_skipped_fid = df[df['treatment'] == 0]['fid_degradation'].dropna()
    
    if len(skipped_fid) < 2 or len(non_skipped_fid) < 2:
        logger.warning("Not enough data for TOST test.")
        return None
    
    # Perform TOST
    # Equivalence margin
    epsilon = 0.05
    
    # Calculate mean difference and standard error
    mean_diff = skipped_fid.mean() - non_skipped_fid.mean()
    var_diff = skipped_fid.var() / len(skipped_fid) + non_skipped_fid.var() / len(non_skipped_fid)
    se_diff = np.sqrt(var_diff)
    
    # TOST: Two one-sided tests
    # H0: mean_diff <= -epsilon OR mean_diff >= epsilon
    # H1: -epsilon < mean_diff < epsilon
    
    t1 = (mean_diff - (-epsilon)) / se_diff
    t2 = (mean_diff - epsilon) / se_diff
    
    df_tost = len(skipped_fid) + len(non_skipped_fid) - 2
    p1 = 1 - stats.t.cdf(t1, df_tost) # P(T > t1)
    p2 = stats.t.cdf(t2, df_tost)     # P(T < t2)
    
    # For equivalence, we need both p-values to be small (e.g., < 0.05)
    # Actually, the standard TOST p-value is max(p1, p2) if we are testing against the bounds.
    # But typically, we reject the null if both one-sided tests are significant.
    # Here, we report the p-values for each one-sided test.
    
    tost_results = {
        "equivalence_margin": epsilon,
        "mean_difference": float(mean_diff),
        "standard_error": float(se_diff),
        "t_statistic_lower": float(t1),
        "p_value_lower": float(p1),
        "t_statistic_upper": float(t2),
        "p_value_upper": float(p2),
        "equivalence_concluded": (p1 < 0.05) and (p2 < 0.05),
        "skipped_count": len(skipped_fid),
        "non_skipped_count": len(non_skipped_fid)
    }
    
    # Write results
    with open(result_path, 'w') as f:
        json.dump(tost_results, f, indent=2)
    
    logger.info(f"TOST results written to {result_path}")
    return tost_results


def main():
    parser = argparse.ArgumentParser(description="Run statistical tests for hybrid inference evaluation.")
    parser.add_argument("--hybrid_output", type=str, default="data/processed/hybrid_output.parquet",
                        help="Path to hybrid output parquet file.")
    parser.add_argument("--baseline_metrics", type=str, default="data/processed/baseline_metrics.parquet",
                        help="Path to baseline metrics parquet file.")
    parser.add_argument("--output", type=str, default="data/metrics/statistical_tests_results.json",
                        help="Path to output JSON file for results.")
    args = parser.parse_args()
    
    logger.info("Starting statistical tests...")
    
    hybrid_path = Path(args.hybrid_output)
    baseline_path = Path(args.baseline_metrics)
    output_path = Path(args.output)
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        # 1. Load and prepare data
        df = load_hybrid_metrics_for_matching(hybrid_path, baseline_path)
        logger.info(f"Loaded {len(df)} rows for analysis.")
        
        # 2. Propensity Score Matching
        covariates = ['frame_complexity'] # As per FR-005, use independent covariates
        matched_df, matching_diagnostics = run_propensity_score_matching(df, covariates)
        logger.info(f"Matching completed. Matched count: {len(matched_df)}")
        
        # 3. TOST Equivalence Test
        tost_results = run_tost_on_matched_data(matched_df, output_path)
        
        # 4. Compile final results
        final_results = {
            "matching_diagnostics": matching_diagnostics,
            "tost_results": tost_results,
            "status": "completed" if tost_results else "failed"
        }
        
        # Write final summary
        summary_path = output_path.parent / "statistical_tests_summary.json"
        with open(summary_path, 'w') as f:
            json.dump(final_results, f, indent=2)
        
        logger.info(f"Statistical tests completed. Summary written to {summary_path}")
        
    except Exception as e:
        logger.error(f"Statistical tests failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()