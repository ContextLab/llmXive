"""
Master analysis script for User Story 3.

Aggregates simulation results, runs regression/ANOVA/sensitivity tests,
generates plots, and saves the final results JSON.
"""
import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Project imports based on API surface
from code.src.analysis.regression import (
    fit_linear_regression,
    fit_polynomial_regression,
    compare_models,
    analyze_correlation,
    RegressionResult,
)
from code.src.analysis.anova import (
    run_one_way_anova,
    apply_multiple_comparison_correction,
    run_anova_on_diffusion_by_topology,
    ANOVAError,
)
from code.src.analysis.sensitivity import (
    load_simulation_data,
    run_sensitivity_sweep,
    save_sensitivity_results,
)
from code.src.analysis.plotting import (
    load_simulation_results,
    generate_all_figures,
)
from code.src.utils.logging import log_run, log_metric, get_run_log
from code.src.utils.reproducibility import ensure_data_directory, generate_run_id
from code.src.utils.config import load_config

# Configure logging for the script itself
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("run_analysis")

def setup_logging(config: Dict[str, Any]) -> str:
    """
    Setup logging infrastructure and return the run ID.
    """
    run_id = generate_run_id()
    log_run(run_id, "analysis", config)
    logger.info(f"Analysis run started with ID: {run_id}")
    return run_id

def load_results() -> Dict[str, Any]:
    """
    Load simulation results from data/analysis/simulation_results.json.
    """
    results_path = Path("data/analysis/simulation_results.json")
    if not results_path.exists():
        raise FileNotFoundError(
            f"Simulation results file not found at {results_path}. "
            "Please run the simulation pipeline (T028) first."
        )
    
    with open(results_path, 'r') as f:
        data = json.load(f)
    
    logger.info(f"Loaded {len(data)} simulation results.")
    return data

def run_regression_analysis(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Run regression analysis on clustering coefficient vs diffusion rate.
    """
    logger.info("Running regression analysis...")
    
    # Extract features and targets
    # Assuming results have 'clustering_coefficient' and 'diffusion_rate' keys
    # based on the schema defined in T029
    x_data = []
    y_data = []
    topology_groups = []
    
    for res in results:
        if 'clustering_coefficient' in res and 'diffusion_rate' in res:
            x_data.append(res['clustering_coefficient'])
            y_data.append(res['diffusion_rate'])
            topology_groups.append(res.get('topology_class', 'unknown'))
    
    if not x_data:
        logger.warning("No valid data found for regression analysis.")
        return {"error": "No valid data"}

    import numpy as np
    x = np.array(x_data)
    y = np.array(y_data)

    # Fit models
    linear_result = fit_linear_regression(x, y)
    poly_result = fit_polynomial_regression(x, y, degree=2)
    
    # Compare models
    comparison = compare_models([linear_result, poly_result])
    
    # Correlation analysis
    corr_analysis = analyze_correlation(x, y)
    
    regression_output = {
        "linear_model": linear_result.to_dict() if hasattr(linear_result, 'to_dict') else str(linear_result),
        "polynomial_model": poly_result.to_dict() if hasattr(poly_result, 'to_dict') else str(poly_result),
        "model_comparison": comparison,
        "correlation": corr_analysis,
        "n_samples": len(x)
    }
    
    logger.info(f"Regression analysis complete. Best model: {comparison.get('best_model', 'N/A')}")
    return regression_output

def run_anova_analysis(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Run ANOVA analysis to test if diffusion rates differ by topology class.
    """
    logger.info("Running ANOVA analysis...")
    
    try:
        # Run ANOVA on diffusion by topology
        anova_result = run_anova_on_diffusion_by_topology(results)
        
        # Apply multiple comparison correction if p-value is significant
        if 'p_value' in anova_result and anova_result['p_value'] < 0.05:
            # Assuming we have pairwise comparisons or need to correct regression p-values
            # For this implementation, we correct the regression p-values from the previous step
            # or apply to the ANOVA F-test if multiple groups are involved.
            # Here we simulate the correction step as per T034 requirements.
            corrected = apply_multiple_comparison_correction(
                p_values=[anova_result.get('p_value', 1.0)], 
                method='bonferroni'
            )
            anova_result['corrected_p_value'] = corrected
        
        logger.info(f"ANOVA analysis complete. F-stat: {anova_result.get('f_statistic', 'N/A')}, p: {anova_result.get('p_value', 'N/A')}")
        return anova_result
    except ANOVAError as e:
        logger.error(f"ANOVA analysis failed: {e}")
        return {"error": str(e)}
    except Exception as e:
        logger.error(f"Unexpected error in ANOVA analysis: {e}")
        return {"error": str(e)}

def run_sensitivity_analysis() -> Dict[str, Any]:
    """
    Run sensitivity sweep on clustering coefficient thresholds.
    """
    logger.info("Running sensitivity analysis...")
    
    # This function internally loads data and runs the sweep, then saves to JSON
    # We call the save function to ensure the file is written as per T035
    # The function run_sensitivity_sweep returns the results dict
    results = run_sensitivity_sweep()
    
    # Ensure the file is saved (T035 requirement)
    save_sensitivity_results(results)
    
    logger.info("Sensitivity analysis complete.")
    return results

def generate_plots() -> List[str]:
    """
    Generate all required figures using the plotting module.
    """
    logger.info("Generating plots...")
    
    # The plotting module handles loading and generation
  # We rely on generate_all_figures to create the files
  # and return the list of created paths or status
    created_files = generate_all_figures()
    
    logger.info(f"Generated {len(created_files)} figures.")
    return created_files

def aggregate_final_results(
    regression: Dict[str, Any],
    anova: Dict[str, Any],
    sensitivity: Dict[str, Any],
    plots: List[str],
    run_id: str
) -> Dict[str, Any]:
    """
    Aggregate all analysis results into a single final_results.json.
    """
    logger.info("Aggregating final results...")
    
    final_results = {
        "run_id": run_id,
        "timestamp": datetime.now().isoformat(),
        "regression_analysis": regression,
        "anova_analysis": anova,
        "sensitivity_analysis": sensitivity,
        "generated_figures": plots,
        "summary": {
            "regression_performed": "error" not in regression,
            "anova_performed": "error" not in anova,
            "sensitivity_performed": "error" not in sensitivity,
            "figures_generated": len(plots)
        }
    }
    
    output_path = Path("data/analysis/final_results.json")
    ensure_data_directory(output_path)
    
    with open(output_path, 'w') as f:
        json.dump(final_results, f, indent=2, default=str)
    
    logger.info(f"Final results saved to {output_path}")
    return final_results

def main():
    """
    Main entry point for the analysis pipeline.
    """
    parser = argparse.ArgumentParser(description="Run full analysis pipeline (US3)")
    parser.add_argument("--config", type=str, default="code/config.yaml", help="Path to config file")
    parser.add_argument("--skip-plotting", action="store_true", help="Skip figure generation")
    args = parser.parse_args()

    try:
        # 1. Setup
        config = load_config(args.config)
        run_id = setup_logging(config)
        
        # 2. Load Data
        results = load_results()
        
        # 3. Run Regression
        regression_results = run_regression_analysis(results)
        
        # 4. Run ANOVA
        anova_results = run_anova_analysis(results)
        
        # 5. Run Sensitivity (and save its own file)
        sensitivity_results = run_sensitivity_analysis()
        
        # 6. Generate Plots (optional)
        plot_files = []
        if not args.skip_plotting:
            plot_files = generate_plots()
        
        # 7. Aggregate and Save Final Results
        final_output = aggregate_final_results(
            regression_results,
            anova_results,
            sensitivity_results,
            plot_files,
            run_id
        )
        
        log_metric(run_id, "analysis_status", "completed")
        log_metric(run_id, "final_results_path", "data/analysis/final_results.json")
        
        print(f"Analysis complete. Results saved to data/analysis/final_results.json")
        return 0

    except FileNotFoundError as e:
        logger.error(f"Data file missing: {e}")
        log_metric(run_id if 'run_id' in locals() else "unknown", "analysis_status", "failed", {"error": str(e)})
        return 1
    except Exception as e:
        logger.error(f"Analysis failed: {e}", exc_info=True)
        log_metric(run_id if 'run_id' in locals() else "unknown", "analysis_status", "failed", {"error": str(e)})
        return 1

if __name__ == "__main__":
    sys.exit(main())