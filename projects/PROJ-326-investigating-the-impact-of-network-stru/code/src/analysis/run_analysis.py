"""
Master analysis script for User Story 3.

This script aggregates simulation results, runs statistical tests (regression, ANOVA,
sensitivity sweep), generates visualizations, and saves the final results.
"""

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add project root to path for imports if running as script
if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from code.src.analysis.regression import (
    fit_linear_regression,
    fit_polynomial_regression,
    compare_models,
    analyze_correlation,
)
from code.src.analysis.anova import (
    run_anova_on_diffusion_by_topology,
    apply_multiple_comparison_correction,
)
from code.src.analysis.sensitivity import run_sensitivity_sweep, load_simulation_data
from code.src.analysis.plotting import generate_all_figures, load_simulation_results
from code.src.utils.config import load_config
from code.src.utils.reproducibility import ensure_data_directory, generate_run_id


def setup_logging(log_path: Optional[Path] = None) -> logging.Logger:
    """Configure logging for the analysis run."""
    logger = logging.getLogger("analysis_master")
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
        )
        logger.addHandler(handler)

        if log_path:
            file_handler = logging.FileHandler(log_path)
            file_handler.setFormatter(
                logging.Formatter(
                    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                )
            )
            logger.addHandler(file_handler)

    return logger


def load_results(data_dir: Path) -> List[Dict[str, Any]]:
    """Load simulation results from the analysis directory."""
    results_path = data_dir / "simulation_results.json"
    if not results_path.exists():
        raise FileNotFoundError(
            f"Simulation results not found at {results_path}. "
            "Please run T028 (run_simulation) first."
        )

    with open(results_path, "r") as f:
        data = json.load(f)

    # Handle both list and dict with 'results' key
    if isinstance(data, dict) and "results" in data:
        return data["results"]
    elif isinstance(data, list):
        return data
    else:
        raise ValueError("Unexpected format in simulation_results.json")


def run_regression_analysis(
    results: List[Dict[str, Any]], logger: logging.Logger
) -> Dict[str, Any]:
    """Run regression analysis on simulation results."""
    logger.info("Running regression analysis...")

    # Extract features and target
    # Assuming results have 'clustering_coefficient' and 'diffusion_rate'
    try:
        df_data = []
        for r in results:
            if "clustering_coefficient" in r and "diffusion_rate" in r:
                df_data.append({
                    "clustering": r["clustering_coefficient"],
                    "diffusion": r["diffusion_rate"],
                    "topology": r.get("topology_class", "unknown")
                })

        if not df_data:
            logger.warning("No valid data points found for regression.")
            return {"error": "No valid data points"}

        import pandas as pd
        df = pd.DataFrame(df_data)

        # Linear Regression
        linear_result = fit_linear_regression(
            df["clustering"].values,
            df["diffusion"].values
        )

        # Polynomial Regression
        poly_result = fit_polynomial_regression(
            df["clustering"].values,
            df["diffusion"].values,
            degree=2
        )

        # Compare models
        comparison = compare_models([linear_result, poly_result])

        # Correlation analysis
        correlation = analyze_correlation(
            df["clustering"].values,
            df["diffusion"].values
        )

        return {
            "linear": {
                "slope": float(linear_result.slope),
                "intercept": float(linear_result.intercept),
                "r_squared": float(linear_result.r_squared),
                "p_value": float(linear_result.p_value)
            },
            "polynomial": {
                "degree": 2,
                "coefficients": [float(c) for c in poly_result.coefficients],
                "r_squared": float(poly_result.r_squared),
                "p_value": float(poly_result.p_value)
            },
            "comparison": comparison,
            "correlation": {
                "r": float(correlation.r),
                "p_value": float(correlation.p_value)
            }
        }

    except Exception as e:
        logger.error(f"Regression analysis failed: {e}")
        return {"error": str(e)}


def run_anova_analysis(
    results: List[Dict[str, Any]], logger: logging.Logger
) -> Dict[str, Any]:
    """Run ANOVA analysis on simulation results."""
    logger.info("Running ANOVA analysis...")

    try:
        # Run ANOVA on diffusion by topology class
        anova_result = run_anova_on_diffusion_by_topology(results)

        if "error" in anova_result:
            return anova_result

        # Apply multiple comparison correction
        corrected = apply_multiple_comparison_correction(
            anova_result.get("p_values", []),
            method="bonferroni"
        )

        return {
            "anova": anova_result,
            "corrected_p_values": corrected
        }

    except Exception as e:
        logger.error(f"ANOVA analysis failed: {e}")
        return {"error": str(e)}


def run_sensitivity_analysis(
    results: List[Dict[str, Any]],
    data_dir: Path,
    logger: logging.Logger
) -> Dict[str, Any]:
    """Run sensitivity sweep analysis."""
    logger.info("Running sensitivity analysis...")

    try:
        # Run sensitivity sweep
        sweep_results = run_sensitivity_sweep(
            results,
            output_path=data_dir / "sensitivity_sweep.json"
        )

        return {
            "status": "completed",
            "num_thresholds": len(sweep_results.get("thresholds", [])),
            "results_summary": {
                "min_diffusion": float(sweep_results.get("min_diffusion", 0)),
                "max_diffusion": float(sweep_results.get("max_diffusion", 0)),
                "mean_diffusion": float(sweep_results.get("mean_diffusion", 0))
            }
        }

    except Exception as e:
        logger.error(f"Sensitivity analysis failed: {e}")
        return {"error": str(e)}


def generate_plots(
    data_dir: Path,
    logger: logging.Logger
) -> Dict[str, Any]:
    """Generate all visualization figures."""
    logger.info("Generating plots...")

    try:
        figures_generated = generate_all_figures(data_dir)
        return {
            "status": "completed",
            "figures": figures_generated
        }
    except Exception as e:
        logger.error(f"Plot generation failed: {e}")
        return {"error": str(e)}


def aggregate_final_results(
    regression_results: Dict[str, Any],
    anova_results: Dict[str, Any],
    sensitivity_results: Dict[str, Any],
    plot_results: Dict[str, Any],
    run_id: str,
    timestamp: str
) -> Dict[str, Any]:
    """Aggregate all analysis results into final output."""
    return {
        "run_id": run_id,
        "timestamp": timestamp,
        "status": "completed",
        "regression_analysis": regression_results,
        "anova_analysis": anova_results,
        "sensitivity_analysis": sensitivity_results,
        "visualization": plot_results,
        "summary": {
            "regression_completed": "error" not in regression_results,
            "anova_completed": "error" not in anova_results,
            "sensitivity_completed": "error" not in sensitivity_results,
            "plots_generated": "error" not in plot_results
        }
    }


def main(args: Optional[List[str]] = None) -> int:
    """Main entry point for the analysis script."""
    parser = argparse.ArgumentParser(
        description="Run master analysis pipeline for User Story 3"
    )
    parser.add_argument(
        "--config",
        type=str,
        default="code/config.yaml",
        help="Path to configuration file"
    )
    parser.add_argument(
        "--data-dir",
        type=str,
        default="data/analysis",
        help="Path to data directory"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/analysis/final_results.json",
        help="Path for final results output"
    )
    parser.add_argument(
        "--log",
        type=str,
        default="data/analysis/analysis_run.log",
        help="Path for log file"
    )

    parsed_args = parser.parse_args(args)

    # Setup paths
    data_dir = Path(parsed_args.data_dir)
    output_path = Path(parsed_args.output)
    log_path = Path(parsed_args.log)

    ensure_data_directory(data_dir)
    ensure_data_directory(output_path.parent)

    # Setup logging
    logger = setup_logging(log_path)
    logger.info("Starting master analysis pipeline...")

    # Generate run ID
    run_id = generate_run_id()

    try:
        # 1. Load simulation results
        logger.info(f"Loading simulation results from {data_dir}")
        results = load_results(data_dir)
        logger.info(f"Loaded {len(results)} simulation results")

        # 2. Run Regression Analysis (T033)
        regression_results = run_regression_analysis(results, logger)

        # 3. Run ANOVA Analysis (T034)
        anova_results = run_anova_analysis(results, logger)

        # 4. Run Sensitivity Sweep (T035)
        sensitivity_results = run_sensitivity_analysis(results, data_dir, logger)

        # 5. Generate Plots (T036)
        plot_results = generate_plots(data_dir, logger)

        # 6. Aggregate Final Results
        final_results = aggregate_final_results(
            regression_results,
            anova_results,
            sensitivity_results,
            plot_results,
            run_id,
            datetime.now().isoformat()
        )

        # 7. Save Final Results
        with open(output_path, "w") as f:
            json.dump(final_results, f, indent=2)

        logger.info(f"Final results saved to {output_path}")
        logger.info("Master analysis pipeline completed successfully.")

        return 0

    except Exception as e:
        logger.error(f"Analysis pipeline failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return 1


if __name__ == "__main__":
    sys.exit(main())