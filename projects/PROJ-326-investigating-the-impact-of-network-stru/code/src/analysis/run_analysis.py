import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from code.src.analysis.regression import fit_linear_regression, fit_polynomial_regression
from code.src.analysis.anova import run_anova_on_diffusion_by_topology, apply_multiple_comparison_correction
from code.src.analysis.sensitivity import run_sensitivity_sweep, save_sensitivity_results
from code.src.analysis.plotting import generate_all_figures, load_simulation_results, load_sensitivity_results
from code.src.utils.config import load_config, get_global_config
from code.src.utils.logging import log_run, log_metric, get_run_log
from code.src.utils.reproducibility import ensure_data_directory, generate_run_id

# Import load_results from the correct location based on the API surface
# The API surface lists it in code.src.simulation.schema
from code.src.simulation.schema import load_results as load_simulation_results_from_schema

logger = logging.getLogger(__name__)

def setup_logging(log_level: int = logging.INFO) -> None:
    """Configure logging for the analysis run."""
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(Path('data/analysis/analysis_run.log'))
        ]
    )

def load_results(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Load simulation results from data/analysis/simulation_results.json.
    Handles missing data and filters out failed runs.
    """
    results_path = Path(config.get('paths', {}).get('analysis_results', 'data/analysis/simulation_results.json'))
    
    if not results_path.exists():
        logger.warning(f"Simulation results file not found at {results_path}. Returning empty list.")
        return []

    try:
        with open(results_path, 'r') as f:
            data = json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        logger.error(f"Failed to load simulation results: {e}")
        return []

    if isinstance(data, list):
        results = data
    elif isinstance(data, dict) and 'results' in data:
        results = data['results']
    else:
        logger.warning("Unexpected format in simulation results. Expected list or dict with 'results' key.")
        return []

    # Filter out failed runs
    excluded_statuses = ['[SIMULATION_DIVERGENCE]', '[DISCONNECTED_NETWORK_FAILURE]', 'FAILED']
    valid_results = []
    excluded_count = 0

    for r in results:
        status = r.get('status', 'UNKNOWN')
        if status in excluded_statuses:
            excluded_count += 1
            logger.debug(f"Excluding run {r.get('network_id', 'unknown')} due to status: {status}")
        else:
            valid_results.append(r)

    if excluded_count > 0:
        logger.info(f"Excluded {excluded_count} runs due to failure status.")
    
    return valid_results, excluded_count

def run_regression_analysis(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Run regression analysis on diffusion rates vs topology metrics.
    """
    if not results:
        logger.warning("No valid results for regression analysis.")
        return {"error": "No data", "coefficients": [], "r_squared": 0.0}

    df = pd.DataFrame(results)
    
    # Ensure required columns exist
    required_cols = ['diffusion_rate', 'clustering_coefficient', 'topology_class']
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        logger.error(f"Missing columns in results: {missing_cols}")
        return {"error": f"Missing columns: {missing_cols}"}

    # Prepare data
    X = df['clustering_coefficient'].values
    y = df['diffusion_rate'].values

    # Filter out NaNs
    valid_mask = ~(np.isnan(X) | np.isnan(y))
    X_clean = X[valid_mask]
    y_clean = y[valid_mask]

    if len(X_clean) < 2:
        logger.warning("Insufficient data points for regression.")
        return {"error": "Insufficient data", "coefficients": [], "r_squared": 0.0}

    # Fit linear regression
    try:
        linear_result = fit_linear_regression(X_clean, y_clean)
    except Exception as e:
        logger.error(f"Linear regression failed: {e}")
        return {"error": str(e)}

    # Fit polynomial regression (degree 2)
    try:
        poly_result = fit_polynomial_regression(X_clean, y_clean, degree=2)
    except Exception as e:
        logger.warning(f"Polynomial regression failed: {e}")
        poly_result = None

    return {
        "linear": {
            "coefficients": linear_result.get('coefficients', []),
            "r_squared": linear_result.get('r_squared', 0.0),
            "p_value": linear_result.get('p_value', 1.0)
        },
        "polynomial": {
            "coefficients": poly_result.get('coefficients', []) if poly_result else None,
            "r_squared": poly_result.get('r_squared', 0.0) if poly_result else None,
            "p_value": poly_result.get('p_value', 1.0) if poly_result else None
        }
    }

def run_anova_analysis(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Run ANOVA analysis on diffusion rates by topology class.
    """
    if not results:
        logger.warning("No valid results for ANOVA analysis.")
        return {"error": "No data"}

    df = pd.DataFrame(results)
    
    if 'diffusion_rate' not in df.columns or 'topology_class' not in df.columns:
        logger.error("Missing required columns for ANOVA.")
        return {"error": "Missing columns"}

    # Group by topology class
    groups = df.groupby('topology_class')['diffusion_rate'].apply(list).to_dict()
    
    if len(groups) < 2:
        logger.warning("Insufficient topology classes for ANOVA.")
        return {"error": "Insufficient groups"}

    try:
        f_stat, p_value = run_anova_on_diffusion_by_topology(groups)
        
        # Apply multiple comparison correction (Bonferroni and BH)
        corrected = apply_multiple_comparison_correction([p_value], method='bonferroni')
        bh_corrected = apply_multiple_comparison_correction([p_value], method='bh')
        
        return {
            "f_statistic": float(f_stat),
            "p_value": float(p_value),
            "groups_analyzed": list(groups.keys()),
            "corrections": {
                "bonferroni": float(corrected[0]) if corrected else None,
                "benjamini_hochberg": float(bh_corrected[0]) if bh_corrected else None
            }
        }
    except Exception as e:
        logger.error(f"ANOVA analysis failed: {e}")
        return {"error": str(e)}

def run_sensitivity_analysis(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run sensitivity sweep on clustering coefficient thresholds.
    """
    try:
        # Run the sweep and save results
        results = run_sensitivity_sweep(config)
        save_sensitivity_results(results, config)
        return results
    except Exception as e:
        logger.error(f"Sensitivity analysis failed: {e}")
        return {"error": str(e)}

def generate_plots(config: Dict[str, Any], results: List[Dict[str, Any]]) -> List[str]:
    """
    Generate all required figures.
    """
    try:
        figures = generate_all_figures(config, results)
        return figures
    except Exception as e:
        logger.error(f"Plot generation failed: {e}")
        return []

def aggregate_final_results(
    regression_results: Dict[str, Any],
    anova_results: Dict[str, Any],
    sensitivity_results: Dict[str, Any],
    figures: List[str],
    excluded_count: int,
    config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Aggregate all results into the final_results.json schema.
    """
    run_id = generate_run_id()
    timestamp = datetime.now().isoformat()

    final_output = {
        "run_id": run_id,
        "timestamp": timestamp,
        "config_summary": {
            "global_seed": config.get('global_seed'),
            "topology_targets": config.get('topology_targets')
        },
        "regression_results": regression_results,
        "anova_results": anova_results,
        "sensitivity_results": sensitivity_results,
        "figures_generated": figures,
        "excluded_runs_count": excluded_count,
        "status": "COMPLETE"
    }

    # Save to disk
    output_path = Path(config.get('paths', {}).get('final_results', 'data/analysis/final_results.json'))
    ensure_data_directory(output_path)
    
    with open(output_path, 'w') as f:
        json.dump(final_output, f, indent=2)
    
    logger.info(f"Final results saved to {output_path}")
    return final_output

def main():
    parser = argparse.ArgumentParser(description='Master analysis script for network topology energy transfer study.')
    parser.add_argument('--config', type=str, default='code/config.yaml', help='Path to config file')
    parser.add_argument('--output', type=str, default='data/analysis', help='Output directory')
    parser.add_argument('--log-level', type=str, default='INFO', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'])
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = getattr(logging, args.log_level.upper())
    setup_logging(log_level)
    
    # Load config
    try:
        config = load_config(args.config)
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        sys.exit(1)
    
    # Ensure output directory exists
    ensure_data_directory(Path(args.output))
    config['paths']['analysis_results'] = str(Path(args.output) / 'simulation_results.json')
    config['paths']['final_results'] = str(Path(args.output) / 'final_results.json')
    config['paths']['sensitivity_results'] = str(Path(args.output) / 'sensitivity_sweep.json')
    config['paths']['figures'] = str(Path(args.output) / 'figures')
    
    logger.info("Starting master analysis pipeline...")
    
    # 1. Load and filter results
    results_data, excluded_count = load_results(config)
    logger.info(f"Loaded {len(results_data)} valid results, excluded {excluded_count} failed runs.")
    
    if not results_data:
        logger.warning("No valid data to analyze. Generating empty final report.")
        final_output = aggregate_final_results(
            {"error": "No data"},
            {"error": "No data"},
            {"error": "No data"},
            [],
            excluded_count,
            config
        )
        return final_output

    # 2. Run Regression Analysis
    logger.info("Running regression analysis...")
    regression_results = run_regression_analysis(results_data)
    
    # 3. Run ANOVA Analysis
    logger.info("Running ANOVA analysis...")
    anova_results = run_anova_analysis(results_data)
    
    # 4. Run Sensitivity Analysis
    logger.info("Running sensitivity analysis...")
    sensitivity_results = run_sensitivity_analysis(config)
    
    # 5. Generate Plots
    logger.info("Generating plots...")
    figures = generate_plots(config, results_data)
    
    # 6. Aggregate and Save Final Results
    logger.info("Aggregating final results...")
    final_output = aggregate_final_results(
        regression_results,
        anova_results,
        sensitivity_results,
        figures,
        excluded_count,
        config
    )
    
    logger.info("Analysis pipeline completed successfully.")
    return final_output

if __name__ == '__main__':
    main()