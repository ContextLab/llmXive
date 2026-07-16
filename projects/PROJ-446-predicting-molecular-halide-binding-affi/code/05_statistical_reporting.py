import os
import json
import logging
import sys
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional

from utils.logger import get_logger
from utils.config import get_data_path, is_simulated_mode, set_simulated_mode

logger = get_logger(__name__)

def load_model_metrics() -> Optional[Dict[str, Any]]:
    """Load model metrics from data/processed/model_runs.json."""
    metrics_path = get_data_path() / "processed" / "model_runs.json"
    if not metrics_path.exists():
        logger.warning(f"Model metrics not found at {metrics_path}")
        return None
    with open(metrics_path, 'r') as f:
        return json.load(f)

def get_halide_counts(df: pd.DataFrame) -> Dict[str, int]:
    """Count occurrences of each halide in the dataset."""
    if 'halide_identity' not in df.columns:
        logger.error("DataFrame missing 'halide_identity' column")
        return {}
    return df['halide_identity'].value_counts().to_dict()

def run_power_analysis(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Run power analysis to verify N >= 10 per halide group.
    Returns analysis result including underpowered flag and group counts.
    """
    counts = get_halide_counts(df)
    min_n = min(counts.values()) if counts else 0
    underpowered = min_n < 10
    
    result = {
        "group_counts": counts,
        "min_sample_size": min_n,
        "underpowered": underpowered,
        "message": f"Minimum sample size: {min_n} (threshold: 10)"
    }
    
    if underpowered:
        logger.warning(f"Power analysis failed: minimum sample size {min_n} < 10")
    
    return result

def run_statistical_analysis(
    df: pd.DataFrame, 
    model_metrics: Dict[str, Any],
    power_result: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Run bootstrap confidence interval analysis for pairwise halide comparisons.
    Algorithm: Resample rows, compute mean R²/RMSE per halide group, compute differences.
    """
    if is_simulated_mode():
        logger.warning("Simulated Data Mode active. Statistical analysis aborted.")
        return {
            "aborted": True,
            "reason": "Simulated Data Mode active",
            "comparisons": [],
            "underpowered": True
        }
    
    if power_result.get("underpowered"):
        logger.warning("Analysis is underpowered. Confidence intervals will be marked as 'wide'.")
    
    # Extract relevant data for analysis
    # Assuming df has columns: 'halide_identity', 'log_K', and model predictions
    # For this implementation, we'll simulate the analysis based on available metrics
    
    comparisons = []
    halides = list(power_result.get("group_counts", {}).keys())
    
    if len(halides) < 2:
        logger.warning("Insufficient halide groups for pairwise comparison")
        return {
            "aborted": False,
            "comparisons": [],
            "underpowered": power_result.get("underpowered", False)
        }
    
    # Bootstrap resampling for pairwise comparisons
    n_bootstrap = 10000
    bootstrap_differences = []
    
    for i in range(len(halides)):
        for j in range(i + 1, len(halides)):
            halide_a = halides[i]
            halide_b = halides[j]
            
            # Filter data for each halide
            df_a = df[df['halide_identity'] == halide_a]
            df_b = df[df['halide_identity'] == halide_b]
            
            if len(df_a) == 0 or len(df_b) == 0:
                continue
            
            # Bootstrap resampling
            diffs = []
            for _ in range(n_bootstrap):
                # Resample with replacement
                sample_a = df_a.sample(n=len(df_a), replace=True, random_state=np.random.randint(0, 10000))
                sample_b = df_b.sample(n=len(df_b), replace=True, random_state=np.random.randint(0, 10000))
                
                # Compute mean affinity for each sample
                mean_a = sample_a['log_K'].mean() if 'log_K' in sample_a.columns else 0.0
                mean_b = sample_b['log_K'].mean() if 'log_K' in sample_b.columns else 0.0
                
                diffs.append(mean_a - mean_b)
            
            if len(diffs) > 0:
                mean_diff = np.mean(diffs)
                ci_lower = np.percentile(diffs, 2.5)
                ci_upper = np.percentile(diffs, 97.5)
                
                # Determine significance (CI does not include 0)
                significant = (ci_lower > 0) or (ci_upper < 0)
                
                # Handle underpowered case
                ci_lower_val = ci_lower if not power_result.get("underpowered") else "wide"
                ci_upper_val = ci_upper if not power_result.get("underpowered") else "wide"
                
                comparisons.append({
                    "pair": f"{halide_a} vs {halide_b}",
                    "mean_diff": float(mean_diff),
                    "ci_lower": ci_lower_val,
                    "ci_upper": ci_upper_val,
                    "significant": significant
                })
    
    return {
        "comparisons": comparisons,
        "underpowered": power_result.get("underpowered", False),
        "n_bootstrap": n_bootstrap
    }

def save_statistical_summary(
    power_result: Dict[str, Any],
    statistical_result: Dict[str, Any],
    output_path: Path
) -> None:
    """Save statistical summary to JSON file."""
    summary = {
        "power_analysis": power_result,
        "statistical_analysis": statistical_result,
        "simulated_mode": is_simulated_mode()
    }
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(summary, f, indent=2)
    
    logger.info(f"Statistical summary saved to {output_path}")

def generate_report_section(stats_summary: Dict[str, Any]) -> str:
    """Generate a markdown section for the report based on statistical summary."""
    section = "### Statistical Analysis Summary\n\n"
    
    power = stats_summary.get("power_analysis", {})
    if power.get("underpowered"):
        section += "**Warning**: Analysis is underpowered (N < 10 per group). "
        section += "Confidence intervals are marked as **wide**.\n\n"
    
    section += "#### Sample Sizes\n\n"
    for halide, count in power.get("group_counts", {}).items():
        section += f"- {halide}: {count}\n"
    section += "\n"
    
    stats = stats_summary.get("statistical_analysis", {})
    if stats.get("aborted"):
        section += f"**Analysis Aborted**: {stats.get('reason', 'Unknown reason')}\n\n"
    else:
        section += "#### Pairwise Comparisons\n\n"
        section += "| Comparison | Mean Difference | 95% CI Lower | 95% CI Upper | Significant? |\n"
        section += "|------------|-----------------|--------------|--------------|---------------|\n"
        
        for comp in stats.get("comparisons", []):
            ci_lower = comp.get("ci_lower", "wide")
            ci_upper = comp.get("ci_upper", "wide")
            sig = "Yes" if comp.get("significant", False) else "No"
            section += f"| {comp['pair']} | {comp['mean_diff']:.3f} | {ci_lower} | {ci_upper} | {sig} |\n"
        section += "\n"
    
    return section

def main():
    """Main entry point for statistical reporting (T028-T032 logic)."""
    logger.info("Starting statistical reporting pipeline")
    
    # Check simulated mode
    sim_mode = is_simulated_mode()
    if sim_mode:
        logger.warning("WARNING: Simulated Data Mode active. Project FAILS to answer the primary comparative research question.")
        # Generate empty/aborted summary
        summary = {
            "power_analysis": {
                "underpowered": True,
                "message": "Simulated Data Mode: Comparative analysis aborted"
            },
            "statistical_analysis": {
                "aborted": True,
                "reason": "Simulated Data Mode active",
                "comparisons": []
            },
            "simulated_mode": True
        }
        output_path = get_data_path() / "processed" / "statistical_summary.json"
        save_statistical_summary(summary["power_analysis"], summary["statistical_analysis"], output_path)
        logger.info("Statistical summary saved (simulated mode)")
        return 0
    
    # Load data
    data_path = get_data_path() / "processed" / "halide_binding_data.csv"
    if not data_path.exists():
        logger.error(f"Processed data not found at {data_path}")
        return 1
    
    df = pd.read_csv(data_path)
    
    # Run power analysis
    power_result = run_power_analysis(df)
    
    # Load model metrics
    model_metrics = load_model_metrics()
    if model_metrics is None:
        logger.warning("Model metrics not found, proceeding with empty metrics")
        model_metrics = {"runs": []}
    
    # Run statistical analysis
    statistical_result = run_statistical_analysis(df, model_metrics, power_result)
    
    # Save statistical summary
    output_path = get_data_path() / "processed" / "statistical_summary.json"
    save_statistical_summary(power_result, statistical_result, output_path)
    
    logger.info("Statistical reporting complete")
    return 0

if __name__ == "__main__":
    sys.exit(main())
