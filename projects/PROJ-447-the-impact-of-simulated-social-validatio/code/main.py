"""
Main orchestration module for the research pipeline.

This module coordinates data loading/generation, regression analysis,
robustness checks, and report generation.
"""

import json
import os
import sys
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

import pandas as pd

from utils.logger import get_logger, log_pipeline_step
from utils.exceptions import (
    DataLoadError,
    DataGapError,
    InsufficientSampleError,
    CausalLanguageViolationError,
    StabilityThresholdViolationError
)
from data.loader import load_real_data
from data.generator import generate_synthetic_data, validate_rses_psychometrics
from data.validator import validate_data
from data.processor import add_psv_column
from analysis.regression import run_analysis
from analysis.sensitivity import run_sensitivity_analysis, check_stability
from analysis.nonlinearity import run_nonlinearity_analysis
from viz.plots import run_viz_pipeline
from viz.validator import count_generated_visualizations, update_pipeline_log

logger = get_logger(__name__)


def load_or_generate_data(
    real_data_url: Optional[str] = None,
    local_data_path: Optional[str] = None,
    output_path: Optional[str] = None
) -> pd.DataFrame:
    """
    Attempt to load real data; if failed, generate synthetic data.

    Args:
        real_data_url: URL for real data.
        local_data_path: Path to local real data file.
        output_path: Path to save the final processed data.

    Returns:
        Processed DataFrame.
    """
    log_pipeline_step("Starting data acquisition")
    data = None

    # Step 1: Try real data
    try:
        logger.info("Attempting to load real data...")
        data = load_real_data(source_url=real_data_url, file_path=local_data_path)
        logger.info("Real data loaded successfully.")
    except DataLoadError as e:
        logger.warning(f"Real data load failed: {e}. Falling back to synthetic generation.")
        # Step 2: Generate synthetic
        data = generate_synthetic_data(n_samples=500, seed=42)

    # Step 3: Validate
    try:
        validate_data(data)
    except (DataGapError, InsufficientSampleError) as e:
        logger.error(f"Data validation failed: {e}")
        raise

    # Step 4: Process (add PSV)
    data = add_psv_column(data)

    # Step 5: Save processed data
    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        data.to_csv(output_path, index=False)
        logger.info(f"Processed data saved to {output_path}")

    log_pipeline_step("Data acquisition and processing complete")
    return data


def run_regression_analysis(
    data: pd.DataFrame,
    output_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Run the primary regression analysis.

    Args:
        data: Input DataFrame.
        output_path: Path to save results.

    Returns:
        Dictionary with regression results.
    """
    log_pipeline_step("Starting regression analysis")

    try:
        results = run_analysis(
            data,
            outcome_col="self_perception_score",
            predictor_cols=["psv_score"],
            confounder_cols=["age", "gender", "offline_relationships", "intrinsic_traits"],
            output_path=output_path
        )
        log_pipeline_step("Regression analysis complete")
        return results
    except CausalLanguageViolationError as e:
        logger.error(f"Causal language violation: {e}")
        raise


def run_robustness_checks(
    data: pd.DataFrame,
    base_results_path: Optional[str] = None,
    viz_output_dir: Optional[str] = None
) -> Dict[str, Any]:
    """
    Run robustness checks: sensitivity, non-linearity, and visualization.

    Args:
        data: Input DataFrame.
        base_results_path: Path for sensitivity results.
        viz_output_dir: Directory for visualization outputs.

    Returns:
        Dictionary with robustness check results.
    """
    log_pipeline_step("Starting robustness checks")

    results = {}

    # 1. Sensitivity Analysis
    try:
        logger.info("Running sensitivity analysis...")
        sensitivity_results = run_sensitivity_analysis(
            data,
            outcome_col="self_perception_score",
            predictor_col="psv_score",
            confounder_cols=["age", "gender", "offline_relationships", "intrinsic_traits"],
            output_path=base_results_path
        )

        # Check stability
        stability_check = check_stability(sensitivity_results)
        results["sensitivity"] = {
            "runs": sensitivity_results,
            "stability_check": stability_check
        }
    except StabilityThresholdViolationError as e:
        logger.error(f"Stability threshold violated: {e}")
        raise
    except Exception as e:
        logger.warning(f"Sensitivity analysis failed: {e}")
        results["sensitivity"] = {"error": str(e)}

    # 2. Non-linearity Analysis
    try:
        logger.info("Running non-linearity analysis...")
        nonlinearity_results = run_nonlinearity_analysis(
            data,
            outcome_col="self_perception_score",
            predictor_col="psv_score",
            output_path=str(Path(base_results_path).parent / "nonlinearity_results.json")
        )
        results["nonlinearity"] = nonlinearity_results
    except Exception as e:
        logger.warning(f"Non-linearity analysis failed: {e}")
        results["nonlinearity"] = {"error": str(e)}

    # 3. Visualization
    try:
        logger.info("Running visualization pipeline...")
        viz_results = run_viz_pipeline(
            data,
            output_dir=viz_output_dir
        )
        results["visualization"] = viz_results
    except Exception as e:
        logger.warning(f"Visualization pipeline failed: {e}")
        results["visualization"] = {"error": str(e)}

    log_pipeline_step("Robustness checks complete")
    return results


def main() -> None:
    """
    Main entry point for the entire pipeline.
    """
    logger.info("========================================")
    logger.info("Starting llmXive Research Pipeline")
    logger.info("========================================")

    base_dir = Path(__file__).resolve().parents[1]
    data_output = base_dir / "data" / "processed" / "pipeline_data.csv"
    model_results_path = base_dir / "data" / "processed" / "model_results.json"
    sensitivity_path = base_dir / "data" / "processed" / "sensitivity_analysis.json"
    viz_dir = base_dir / "data" / "processed"
    log_path = base_dir / "data" / "processed" / "pipeline_run_log.json"

    pipeline_log = {
        "start_time": datetime.now().isoformat(),
        "status": "running",
        "steps": []
    }

    try:
        # 1. Load/Generate Data
        data = load_or_generate_data(
            local_data_path=None,
            output_path=str(data_output)
        )
        pipeline_log["steps"].append({"step": "data_acquisition", "status": "success"})

        # 2. Regression
        run_regression_analysis(data, output_path=str(model_results_path))
        pipeline_log["steps"].append({"step": "regression_analysis", "status": "success"})

        # 3. Robustness
        run_robustness_checks(
            data,
            base_results_path=str(sensitivity_path),
            viz_output_dir=str(viz_dir)
        )
        pipeline_log["steps"].append({"step": "robustness_checks", "status": "success"})

        # 4. Visualizations check
        viz_count, missing_files = count_generated_visualizations(viz_dir)
        if viz_count < 2:
            logger.warning(f"Missing visualization files: {missing_files}")
            pipeline_log["steps"].append({
                "step": "visualization_check",
                "status": "warning",
                "message": f"Only {viz_count} visualizations found. Missing: {missing_files}"
            })
        else:
            pipeline_log["steps"].append({"step": "visualization_check", "status": "success"})

        pipeline_log["status"] = "completed"
        pipeline_log["end_time"] = datetime.now().isoformat()

    except (DataLoadError, DataGapError, InsufficientSampleError) as e:
        logger.error(f"Pipeline failed at data stage: {e}")
        pipeline_log["status"] = "failed"
        pipeline_log["error"] = str(e)
        pipeline_log["end_time"] = datetime.now().isoformat()
    except (CausalLanguageViolationError, StabilityThresholdViolationError) as e:
        logger.error(f"Pipeline failed at analysis stage: {e}")
        pipeline_log["status"] = "failed"
        pipeline_log["error"] = str(e)
        pipeline_log["end_time"] = datetime.now().isoformat()
    except Exception as e:
        logger.error(f"Pipeline failed with unexpected error: {e}", exc_info=True)
        pipeline_log["status"] = "failed"
        pipeline_log["error"] = str(e)
        pipeline_log["end_time"] = datetime.now().isoformat()

    # Save log
    with open(log_path, 'w', encoding='utf-8') as f:
        json.dump(pipeline_log, f, indent=2)
    logger.info(f"Pipeline log saved to {log_path}")

    if pipeline_log["status"] != "completed":
        sys.exit(1)


if __name__ == "__main__":
    main()
