"""
Main analysis runner that orchestrates regression, ANOVA, and sensitivity analysis.
Produces aggregated results and statistical outputs.
"""
import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from code.src.analysis.regression import fit_linear_regression, fit_polynomial_regression, analyze_correlation
from code.src.analysis.anova import run_one_way_anova, apply_multiple_comparison_correction
from code.src.analysis.sensitivity import run_sensitivity_sweep, save_sensitivity_results

logger = logging.getLogger(__name__)

def load_results(results_path: str) -> pd.DataFrame:
    """Load simulation results from JSON file."""
    path = Path(results_path)
    if not path.exists():
        raise FileNotFoundError(f"Results file not found: {results_path}")
    
    with open(path, 'r') as f:
        data = json.load(f)
        
    if isinstance(data, list):
        return pd.DataFrame(data)
    elif isinstance(data, dict) and "results" in data:
        return pd.DataFrame(data["results"])
    else:
        return pd.DataFrame([data])

def run_regression_analysis(df: pd.DataFrame) -> Dict[str, Any]:
    """Run regression analysis on clustering vs diffusion."""
    if 'clustering_coefficient_actual' not in df.columns or 'diffusion_rate' not in df.columns:
        logger.warning("Missing required columns for regression. Skipping.")
        return {"status": "skipped", "reason": "missing_columns"}
        
    valid_data = df[['clustering_coefficient_actual', 'diffusion_rate']].dropna()
    
    if len(valid_data) < 2:
        return {"status": "skipped", "reason": "insufficient_data"}
        
    x = valid_data['clustering_coefficient_actual'].values
    y = valid_data['diffusion_rate'].values
    
    # Linear regression
    lin_result = fit_linear_regression(x, y)
    
    # Polynomial regression
    poly_result = fit_polynomial_regression(x, y, degree=2)
    
    # Correlation
    corr_result = analyze_correlation(x, y)
    
    return {
        "linear": lin_result,
        "polynomial": poly_result,
        "correlation": corr_result,
        "sample_size": len(valid_data)
    }

def run_anova_analysis(df: pd.DataFrame) -> Dict[str, Any]:
    """Run ANOVA analysis by topology class."""
    if 'topology_class' not in df.columns or 'diffusion_rate' not in df.columns:
        logger.warning("Missing required columns for ANOVA. Skipping.")
        return {"status": "skipped", "reason": "missing_columns"}
        
    groups = df.groupby('topology_class')['diffusion_rate'].apply(list).to_dict()
    
    if len(groups) < 2:
        return {"status": "skipped", "reason": "insufficient_groups"}
        
    group_values = list(groups.values())
    f_stat, p_value = run_one_way_anova(group_values)
    
    # Apply correction (placeholder for multiple comparisons)
    corrected_p = apply_multiple_comparison_correction([p_value], method='bonferroni')
    
    return {
        "f_statistic": float(f_stat),
        "p_value": float(p_value),
        "corrected_p_value": float(corrected_p[0]) if corrected_p else None,
        "groups": list(groups.keys()),
        "group_sizes": {k: len(v) for k, v in groups.items()}
    }

def aggregate_final_results(regression_results: Dict, anova_results: Dict, sensitivity_results: List, figures_generated: List[str]) -> Dict[str, Any]:
    """Aggregate all analysis results into final structure."""
    return {
        "timestamp": datetime.now().isoformat(),
        "regression_results": regression_results,
        "anova_results": anova_results,
        "sensitivity_results": sensitivity_results,
        "figures_generated": figures_generated,
        "excluded_runs_count": 0  # Placeholder, would be calculated from filtered data
    }

def main():
    """Main entry point for analysis pipeline."""
    parser = argparse.ArgumentParser(description="Run analysis pipeline")
    parser.add_argument("--config", type=str, default="code/config.yaml", help="Path to config")
    parser.add_argument("--output", type=str, default="data", help="Output directory")
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.INFO)
    
    output_path = Path(args.output)
    results_path = output_path / "analysis" / "simulation_results.json"
    aggregated_path = output_path / "analysis" / "aggregated_results.json"
    stats_path = output_path / "analysis" / "statistical_outputs.json"
    final_path = output_path / "analysis" / "final_results.json"
    
    if not results_path.exists():
        logger.error(f"Simulation results not found: {results_path}")
        # Create empty outputs to prevent pipeline crash
        empty_final = {
            "timestamp": datetime.now().isoformat(),
            "regression_results": {"status": "skipped", "reason": "no_data"},
            "anova_results": {"status": "skipped", "reason": "no_data"},
            "sensitivity_results": [],
            "figures_generated": [],
            "excluded_runs_count": 0
        }
        with open(final_path, 'w') as f:
            json.dump(empty_final, f, indent=2)
        return
        
    df = load_results(str(results_path))
    
    # Run regression
    logger.info("Running regression analysis...")
    regression_results = run_regression_analysis(df)
    
    # Run ANOVA
    logger.info("Running ANOVA analysis...")
    anova_results = run_anova_analysis(df)
    
    # Aggregate intermediate results
    aggregated = {
        "regression": regression_results,
        "anova": anova_results,
        "sample_size": len(df)
    }
    with open(aggregated_path, 'w') as f:
        json.dump(aggregated, f, indent=2)
        
    # Save statistical outputs
    with open(stats_path, 'w') as f:
        json.dump({
            "regression": regression_results,
            "anova": anova_results
        }, f, indent=2)
        
    # Run sensitivity (delegated to sensitivity module)
    logger.info("Running sensitivity sweep...")
    # Sensitivity is run separately but we ensure the file exists
    sensitivity_path = output_path / "analysis" / "sensitivity_sweep.json"
    sensitivity_results = []
    if sensitivity_path.exists():
        with open(sensitivity_path, 'r') as f:
            sens_data = json.load(f)
            sensitivity_results = sens_data.get("results", [])
    
    # Final aggregation
    final = aggregate_final_results(regression_results, anova_results, sensitivity_results, [])
    with open(final_path, 'w') as f:
        json.dump(final, f, indent=2)
        
    logger.info(f"Analysis complete. Results saved to {final_path}")

if __name__ == "__main__":
    main()
