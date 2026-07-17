import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from code.src.analysis.regression import (
    fit_linear_regression,
    fit_polynomial_regression,
    compare_models,
    analyze_correlation,
)
from code.src.analysis.anova import (
    run_one_way_anova,
    apply_multiple_comparison_correction,
    run_anova_on_diffusion_by_topology,
)
from code.src.analysis.sensitivity import (
    run_sensitivity_sweep,
    save_sensitivity_results,
    load_simulation_data,
)
from code.src.analysis.plotting import generate_all_figures
from code.src.utils.config import load_config, get_global_config
from code.src.utils.logging import log_run, log_metric, get_run_log
from code.src.utils.reproducibility import ensure_data_directory

# Configure logging for this module
logger = logging.getLogger(__name__)

def setup_logging(log_file: Optional[Path] = None) -> logging.Logger:
    """Configure logging for the analysis pipeline."""
    if log_file is None:
        log_file = Path("data/run_log.json")
    
    ensure_data_directory(log_file.parent)
    
    # Setup basic console logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    
    # Return the module logger
    return logger

def load_results(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Aggregate simulation results from data/analysis/simulation_results.json.
    Handles missing data via mean/median/variance aggregation strategies.
    
    Returns a dictionary containing:
    - simulation_data: DataFrame with all simulation results
    - summary_stats: Dict of aggregated statistics
    """
    sim_results_path = Path(config.get("paths", {}).get("simulation_results", "data/analysis/simulation_results.json"))
    
    if not sim_results_path.exists():
        logger.warning(f"Simulation results file not found: {sim_results_path}")
        return {
            "simulation_data": pd.DataFrame(),
            "summary_stats": {},
            "error": "Simulation results file missing"
        }
    
    try:
        with open(sim_results_path, 'r') as f:
            raw_data = json.load(f)
        
        # Normalize list of results into a DataFrame
        if isinstance(raw_data, list):
            df = pd.DataFrame(raw_data)
        elif isinstance(raw_data, dict) and "results" in raw_data:
            df = pd.DataFrame(raw_data["results"])
        else:
            logger.warning("Unexpected simulation results format, attempting to convert")
            df = pd.DataFrame([raw_data] if isinstance(raw_data, dict) else [])
        
        # Handle missing data
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(df) > 0:
            # Fill missing numeric values with median
            for col in numeric_cols:
                if df[col].isnull().any():
                    median_val = df[col].median()
                    df[col].fillna(median_val, inplace=True)
                    logger.info(f"Filled {df[col].isnull().sum()} missing values in '{col}' with median {median_val}")
        
        # Calculate summary statistics
        summary_stats = {}
        if len(df) > 0:
            summary_stats = {
                "total_records": len(df),
                "topology_counts": df["topology_class"].value_counts().to_dict() if "topology_class" in df.columns else {},
                "diffusion_stats": {},
                "clustering_stats": {}
            }
            
            if "diffusion_rate" in df.columns:
                summary_stats["diffusion_stats"] = {
                    "mean": float(df["diffusion_rate"].mean()),
                    "std": float(df["diffusion_rate"].std()),
                    "median": float(df["diffusion_rate"].median()),
                    "min": float(df["diffusion_rate"].min()),
                    "max": float(df["diffusion_rate"].max())
                }
            
            if "clustering_coefficient" in df.columns:
                summary_stats["clustering_stats"] = {
                    "mean": float(df["clustering_coefficient"].mean()),
                    "std": float(df["clustering_coefficient"].std()),
                    "median": float(df["clustering_coefficient"].median()),
                    "min": float(df["clustering_coefficient"].min()),
                    "max": float(df["clustering_coefficient"].max())
                }
        
        return {
            "simulation_data": df,
            "summary_stats": summary_stats
        }
    except Exception as e:
        logger.error(f"Error loading simulation results: {e}")
        return {
            "simulation_data": pd.DataFrame(),
            "summary_stats": {},
            "error": str(e)
        }

def run_regression_analysis(simulation_data: pd.DataFrame) -> Dict[str, Any]:
    """
    Run regression analysis on simulation data.
    Fits linear and polynomial models to correlate topology metrics with diffusion rates.
    """
    if simulation_data.empty:
        logger.warning("No simulation data available for regression analysis")
        return {"error": "No data", "models": []}
    
    results = {
        "models": [],
        "correlations": [],
        "best_model": None
    }
    
    # Ensure required columns exist
    x_col = "clustering_coefficient"
    y_col = "diffusion_rate"
    
    if x_col not in simulation_data.columns or y_col not in simulation_data.columns:
        # Fallback to available numeric columns
        numeric_cols = simulation_data.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) >= 2:
            x_col, y_col = numeric_cols[0], numeric_cols[1]
            logger.warning(f"Using fallback columns: x={x_col}, y={y_col}")
        else:
            logger.error("Insufficient numeric columns for regression")
            return {"error": "Insufficient data", "models": []}
    
    x = simulation_data[x_col].values
    y = simulation_data[y_col].values
    
    # Linear regression
    try:
        linear_result = fit_linear_regression(x, y)
        results["models"].append({
            "type": "linear",
            "r_squared": float(linear_result.r_squared),
            "p_value": float(linear_result.p_value),
            "coefficients": linear_result.coefficients.tolist()
        })
    except Exception as e:
        logger.warning(f"Linear regression failed: {e}")
    
    # Polynomial regression (degree 2)
    try:
        poly_result = fit_polynomial_regression(x, y, degree=2)
        results["models"].append({
            "type": "polynomial_degree_2",
            "r_squared": float(poly_result.r_squared),
            "p_value": float(poly_result.p_value),
            "coefficients": poly_result.coefficients.tolist()
        })
    except Exception as e:
        logger.warning(f"Polynomial regression failed: {e}")
    
    # Compare models
    if len(results["models"]) >= 2:
        try:
            comparison = compare_models(
                [m for m in results["models"] if m["type"] != "polynomial_degree_2"],
                [m for m in results["models"] if m["type"] == "polynomial_degree_2"]
            )
            results["comparison"] = comparison
            # Determine best model
            if comparison.get("winner"):
                results["best_model"] = comparison["winner"]
        except Exception as e:
            logger.warning(f"Model comparison failed: {e}")
    
    # Correlation analysis
    try:
        corr_result = analyze_correlation(x, y)
        results["correlations"].append({
            "x": x_col,
            "y": y_col,
            "pearson_r": float(corr_result.pearson_r),
            "p_value": float(corr_result.p_value),
            "spearman_r": float(corr_result.spearman_r)
        })
    except Exception as e:
        logger.warning(f"Correlation analysis failed: {e}")
    
    return results

def run_anova_analysis(simulation_data: pd.DataFrame) -> Dict[str, Any]:
    """
    Run ANOVA analysis to test if diffusion rates differ significantly by topology class.
    Applies multiple comparison correction (Bonferroni and Benjamini-Hochberg).
    """
    if simulation_data.empty:
        logger.warning("No simulation data available for ANOVA analysis")
        return {"error": "No data", "anova_results": []}
    
    results = {
        "anova_results": [],
        "corrections": {}
    }
    
    group_col = "topology_class"
    value_col = "diffusion_rate"
    
    if group_col not in simulation_data.columns or value_col not in simulation_data.columns:
        logger.error(f"Missing required columns for ANOVA: {group_col} or {value_col}")
        return {"error": "Missing columns", "anova_results": []}
    
    # Run one-way ANOVA by topology
    try:
        anova_result = run_anova_on_diffusion_by_topology(simulation_data, group_col, value_col)
        results["anova_results"].append(anova_result)
        
        # Extract p-values for correction
        p_values = [res.get("p_value") for res in results["anova_results"] if res.get("p_value") is not None]
        
        if len(p_values) > 0:
            # Apply multiple comparison corrections
            corrections = apply_multiple_comparison_correction(p_values)
            results["corrections"] = {
                "bonferroni": corrections.get("bonferroni", {}),
                "benjamini_hochberg": corrections.get("benjamini_hochberg", {})
            }
    except Exception as e:
        logger.error(f"ANOVA analysis failed: {e}")
        results["error"] = str(e)
    
    return results

def run_sensitivity_analysis(config: Dict[str, Any], simulation_data: pd.DataFrame) -> Dict[str, Any]:
    """
    Run sensitivity sweep for clustering coefficient thresholds.
    """
    if simulation_data.empty:
        logger.warning("No simulation data available for sensitivity analysis")
        return {"error": "No data"}
    
    # Get thresholds from config or use defaults
    thresholds = config.get("sensitivity", {}).get("thresholds", [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7])
    
    try:
        sweep_results = run_sensitivity_sweep(simulation_data, thresholds)
        
        # Save results to file
        output_path = Path(config.get("paths", {}).get("sensitivity_results", "data/analysis/sensitivity_sweep.json"))
        save_sensitivity_results(sweep_results, output_path)
        
        logger.info(f"Sensitivity results saved to {output_path}")
        
        return sweep_results
    except Exception as e:
        logger.error(f"Sensitivity analysis failed: {e}")
        return {"error": str(e)}

def generate_plots(config: Dict[str, Any], simulation_data: pd.DataFrame) -> List[str]:
    """
    Generate all required figures (scatter, heatmaps, etc.) at 300 DPI.
    Returns list of generated file paths.
    """
    if simulation_data.empty:
        logger.warning("No simulation data available for plotting")
        return []
    
    figures_dir = Path(config.get("paths", {}).get("figures", "figures"))
    ensure_data_directory(figures_dir)
    
    try:
        generated_files = generate_all_figures(simulation_data, figures_dir)
        logger.info(f"Generated {len(generated_files)} figures")
        return generated_files
    except Exception as e:
        logger.error(f"Plot generation failed: {e}")
        return []

def aggregate_final_results(
    regression_results: Dict[str, Any],
    anova_results: Dict[str, Any],
    sensitivity_results: Dict[str, Any],
    figures_generated: List[str],
    summary_stats: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Aggregate all analysis results into the final output structure.
    Schema: {regression_results, anova_results, sensitivity_results, figures_generated}
    """
    final_output = {
        "timestamp": datetime.now().isoformat(),
        "status": "complete",
        "summary": summary_stats,
        "regression_results": regression_results,
        "anova_results": anova_results,
        "sensitivity_results": sensitivity_results,
        "figures_generated": figures_generated
    }
    
    return final_output

def main():
    """Main entry point for the analysis pipeline."""
    parser = argparse.ArgumentParser(description="Run full analysis pipeline")
    parser.add_argument("--config", type=str, default="code/config.yaml", help="Path to config file")
    parser.add_argument("--output", type=str, default="data/analysis", help="Output directory")
    args = parser.parse_args()
    
    # Setup logging
    logger = setup_logging()
    
    # Load configuration
    try:
        config = load_config(args.config)
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        sys.exit(1)
    
    # Ensure output directory exists
    output_dir = Path(args.output)
    ensure_data_directory(output_dir)
    
    # Update paths in config
    config.setdefault("paths", {})
    config["paths"]["simulation_results"] = str(output_dir / "simulation_results.json")
    config["paths"]["sensitivity_results"] = str(output_dir / "sensitivity_sweep.json")
    config["paths"]["figures"] = str(output_dir.parent / "figures")
    config["paths"]["final_results"] = str(output_dir / "final_results.json")
    
    logger.info("Starting analysis pipeline...")
    
    # 1. Load and aggregate simulation results
    logger.info("Loading simulation results...")
    data = load_results(config)
    
    if "error" in data:
        logger.error(f"Failed to load simulation data: {data['error']}")
        # Continue with empty data to allow partial results
        simulation_data = pd.DataFrame()
    else:
        simulation_data = data["simulation_data"]
    
    # 2. Run regression analysis
    logger.info("Running regression analysis...")
    regression_results = run_regression_analysis(simulation_data)
    
    # 3. Run ANOVA analysis
    logger.info("Running ANOVA analysis...")
    anova_results = run_anova_analysis(simulation_data)
    
    # 4. Run sensitivity analysis
    logger.info("Running sensitivity analysis...")
    sensitivity_results = run_sensitivity_analysis(config, simulation_data)
    
    # 5. Generate plots
    logger.info("Generating plots...")
    figures = generate_plots(config, simulation_data)
    
    # 6. Aggregate final results
    final_output = aggregate_final_results(
        regression_results,
        anova_results,
        sensitivity_results,
        figures,
        data.get("summary_stats", {})
    )
    
    # 7. Save final results
    final_path = Path(config["paths"]["final_results"])
    try:
        with open(final_path, 'w') as f:
            json.dump(final_output, f, indent=2, default=str)
        logger.info(f"Final results saved to {final_path}")
    except Exception as e:
        logger.error(f"Failed to save final results: {e}")
        sys.exit(1)
    
    # Log completion
    log_metric("analysis_status", "complete")
    log_metric("figures_generated", len(figures))
    
    logger.info("Analysis pipeline completed successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())