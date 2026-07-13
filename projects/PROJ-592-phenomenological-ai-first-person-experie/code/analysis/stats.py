"""
Statistical Analysis Module.

Orchestrates metric aggregation, normality checks, and statistical testing.
Writes validity_scores.csv to data/processed/.
"""
import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import pandas as pd
from scipy import stats
from datetime import datetime

# Local imports
from config import get_config
from utils.logging import get_logger, log_operation
from utils.io import safe_write_json, safe_write_csv, load_json

logger = get_logger("stats_analysis")

class StatsAnalysisError(Exception):
    """Custom exception for statistical analysis errors."""
    pass

def load_aggregated_scores(input_dir: str) -> pd.DataFrame:
    """
    Load and aggregate scores from analysis outputs.
    
    Args:
        input_dir: Directory containing analysis outputs
    
    Returns:
        Aggregated DataFrame with all metrics
    """
    input_path = Path(input_dir)
    scores = []
    
    # Load consistency scores
    consistency_file = input_path / "consistency_scores.json"
    if consistency_file.exists():
        data = load_json(consistency_file)
        for item in data:
            scores.append({"condition": item.get("condition"), "consistency": item.get("score")})
    
    # Load stability scores
    stability_file = input_path / "stability_scores.json"
    if stability_file.exists():
        data = load_json(stability_file)
        for item in data:
            # Merge or append
            scores.append({"condition": item.get("condition"), "stability": item.get("score")})
    
    # Load marker scores
    marker_file = input_path / "marker_scores.json"
    if marker_file.exists():
        data = load_json(marker_file)
        for item in data:
            scores.append({"condition": item.get("condition"), "markers": item.get("score")})
    
    if not scores:
        raise StatsAnalysisError("No score data found in input directory")
    
    df = pd.DataFrame(scores)
    return df

def check_normality(data: np.ndarray) -> Tuple[bool, float]:
    """
    Check normality assumption using Shapiro-Wilk test.
    
    Args:
        data: Array of values
    
    Returns:
        Tuple of (is_normal, p_value)
    """
    if len(data) < 3:
        return True, 1.0  # Not enough data to test
    
    stat, p_value = stats.shapiro(data)
    return p_value >= 0.05, p_value

def check_homogeneity(groups: List[np.ndarray]) -> Tuple[bool, float]:
    """
    Check homogeneity of variance using Levene test.
    
    Args:
        groups: List of arrays for each group
    
    Returns:
        Tuple of (is_homogeneous, p_value)
    """
    if len(groups) < 2:
        return True, 1.0  # Not enough groups to test
    
    stat, p_value = stats.levene(*groups)
    return p_value >= 0.05, p_value

def run_anova(data: Dict[str, np.ndarray]) -> Dict[str, Any]:
    """
    Run one-way ANOVA.
    
    Args:
        data: Dictionary of group_name -> values
    
    Returns:
        ANOVA results
    """
    groups = list(data.values())
    stat, p_value = stats.f_oneway(*groups)
    return {
        "test": "ANOVA",
        "statistic": float(stat),
        "p_value": float(p_value),
        "significant": p_value < 0.05
    }

def run_kruskal(data: Dict[str, np.ndarray]) -> Dict[str, Any]:
    """
    Run Kruskal-Wallis H test (non-parametric alternative to ANOVA).
    
    Args:
        data: Dictionary of group_name -> values
    
    Returns:
        Kruskal-Wallis results
    """
    groups = list(data.values())
    stat, p_value = stats.kruskal(*groups)
    return {
        "test": "Kruskal-Wallis",
        "statistic": float(stat),
        "p_value": float(p_value),
        "significant": p_value < 0.05
    }

def orchestrate_analysis(
    input_dir: str,
    output_dir: str
) -> Dict[str, Any]:
    """
    Orchestrate the full statistical analysis pipeline.
    
    This function:
    1. Loads aggregated scores
    2. Checks normality and homogeneity assumptions
    3. Runs appropriate statistical tests (ANOVA or Kruskal-Wallis)
    4. Writes validity_scores.csv to output_dir
    
    Args:
        input_dir: Directory containing analysis outputs
        output_dir: Directory to write results
    
    Returns:
        Analysis summary
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    logger.log("orchestrate_start", input_dir=input_dir, output_dir=output_dir)
    
    # Load data
    df = load_aggregated_scores(input_dir)
    
    # Prepare data for analysis
    # Group by condition and extract metrics
    results = {
        "assumptions": {},
        "tests": {},
        "scores_summary": {},
        "timestamp": datetime.utcnow().isoformat()
    }
    
    # Check assumptions for each metric
    for metric in ["consistency", "stability", "markers"]:
        if metric not in df.columns:
            continue
        
        # Group by condition
        groups = df.groupby("condition")[metric].apply(lambda x: x.dropna().values).to_dict()
        
        if len(groups) < 2:
            continue
        
        # Check normality
        normality_results = {}
        group_arrays = []
        for name, values in groups.items():
          is_normal, p = check_normality(values)
          normality_results[name] = {"is_normal": is_normal, "p_value": p}
          group_arrays.append(values)
        
        # Check homogeneity
        is_homogeneous, p_hom = check_homogeneity(group_arrays)
        
        results["assumptions"][metric] = {
            "normality": normality_results,
            "homogeneity": {"is_homogeneous": is_homogeneous, "p_value": p_hom}
        }
        
        # Run appropriate test
        if all(r["is_normal"] for r in normality_results.values()) and is_homogeneous:
            test_result = run_anova(groups)
        else:
            test_result = run_kruskal(groups)
        
        results["tests"][metric] = test_result
    
    # Aggregate scores for CSV output
    # Create a summary row per condition
    summary_rows = []
    for condition in df["condition"].unique():
        row = {"condition": condition}
        for metric in ["consistency", "stability", "markers"]:
            if metric in df.columns:
                values = df[df["condition"] == condition][metric].dropna()
                if len(values) > 0:
                    row[f"{metric}_mean"] = float(values.mean())
                    row[f"{metric}_std"] = float(values.std())
                    row[f"{metric}_n"] = int(len(values))
        summary_rows.append(row)
    
    # Write validity_scores.csv
    if summary_rows:
        csv_path = output_path / "validity_scores.csv"
        safe_write_csv(csv_path, summary_rows)
        logger.log("validity_scores_written", path=str(csv_path))
    else:
        logger.log("warning", message="No valid scores to write to CSV")
    
    # Save full results
    json_path = output_path / "analysis_results.json"
    safe_write_json(json_path, results)
    
    logger.log("orchestrate_complete", results=results)
    return results

def main():
    """CLI entry point for statistical analysis."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Statistical Analysis Orchestrator")
    parser.add_argument(
        "--input-dir",
        type=str,
        default="data/processed",
        help="Input directory with analysis outputs"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/processed",
        help="Output directory for results"
    )
    
    args = parser.parse_args()
    
    try:
        results = orchestrate_analysis(
            input_dir=args.input_dir,
            output_dir=args.output_dir
        )
        
        print(json.dumps(results, indent=2, default=str))
        logger.log("main_success")
        
    except Exception as e:
        logger.log("main_error", error=str(e))
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
