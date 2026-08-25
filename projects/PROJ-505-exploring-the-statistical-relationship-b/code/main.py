"""
Main entry point for the Solar Wind Composition and Geomagnetic Indices analysis pipeline.
Aggregates results from ingestion, regression, cross-validation, permutation tests, and sensitivity analysis.
Generates final summary artifacts.
"""
import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config import get_config
from utils.logging import get_logger, setup_logging, PipelineError
from utils.io import save_parquet, load_parquet
from utils.mkdirs import ensure_dirs
from ingestion.align import align_data, main as align_main
from analysis.coupling_functions import compute_all_coupling_functions, main as coupling_main
from analysis.regression import run_regression_analysis, main as regression_main
from analysis.cross_validation import run_cross_validation, main as cv_main
from analysis.permutation_test import run_permutation_tests, main as perm_main
from analysis.sensitivity import run_sensitivity_analysis, main as sens_main
from analysis.integrate_results import integrate_results, main as integrate_main

logger = get_logger(__name__)

def load_results_from_json(file_path: str) -> Dict[str, Any]:
    """Load results from a JSON file."""
    path = Path(file_path)
    if not path.exists():
        logger.warning(f"Results file not found: {file_path}")
        return {}
    with open(path, 'r') as f:
        return json.load(f)

def aggregate_results(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Aggregate results from all analysis stages.
    Returns a summary dictionary containing model metrics, significant predictors, and data source labels.
    """
    processed_dir = Path(config['paths']['processed'])
    artifacts_dir = Path(config['paths']['artifacts'])
    
    # Load regression results
    regression_file = processed_dir / 'regression_results.json'
    regression_results = load_results_from_json(str(regression_file))
    
    # Load cross-validation results
    cv_file = processed_dir / 'cv_results.json'
    cv_results = load_results_from_json(str(cv_file))
    
    # Load permutation test results
    perm_file = processed_dir / 'permutation_results.json'
    perm_results = load_results_from_json(str(perm_file))
    
    # Load sensitivity analysis results
    sens_file = processed_dir / 'sensitivity_results.json'
    sens_results = load_results_from_json(str(sens_file))
    
    # Determine if synthetic data was used
    # Check the aligned data metadata or a specific flag file
    aligned_metadata_file = processed_dir / 'aligned_data_metadata.json'
    is_synthetic = False
    data_source_label = "Real"
    
    if aligned_metadata_file.exists():
        with open(aligned_metadata_file, 'r') as f:
            meta = json.load(f)
            if meta.get('source') == 'synthetic':
                is_synthetic = True
                data_source_label = "Synthetic (Fallback Triggered)"
            elif meta.get('source') == 'real':
                is_synthetic = False
                data_source_label = "Real"
            else:
                # Fallback: check if aligned parquet exists but metadata is missing
                # This is a heuristic; in a robust system, metadata should always be present
                aligned_parquet = processed_dir / 'aligned_data.parquet'
                if not aligned_parquet.exists():
                    is_synthetic = True
                    data_source_label = "Synthetic (Fallback Triggered)"
    else:
        # If metadata is missing, we assume synthetic based on the project's current state
        # as per the critical note in tasks.md about data gaps
        is_synthetic = True
        data_source_label = "Synthetic (Fallback Triggered)"
    
    # Compile summary
    summary = {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "data_source": data_source_label,
            "is_synthetic": is_synthetic,
            "config": {
                "study_start": config.get('study_start'),
                "study_end": config.get('study_end'),
                "random_seed": config.get('random_seed')
            }
        },
        "regression_metrics": {
            "baseline_model": regression_results.get('baseline_metrics', {}),
            "full_model": regression_results.get('full_metrics', {}),
            "delta_r_squared": regression_results.get('delta_r_squared', {}),
            "vif_warnings": regression_results.get('vif_warnings', [])
        },
        "cross_validation": {
            "baseline_cv": cv_results.get('baseline_cv', {}),
            "full_cv": cv_results.get('full_cv', {}),
            "delta_cv_r_squared": cv_results.get('delta_r_squared', {})
        },
        "permutation_tests": {
            "null_distributions": perm_results.get('null_distributions', {}),
            "p_values": perm_results.get('p_values', {}),
            "significance_flags": perm_results.get('significant_predictors', [])
        },
        "sensitivity_analysis": {
            "threshold_sweep": sens_results.get('threshold_sweep', {}),
            "fdr_corrected": sens_results.get('fdr_corrected', {}),
            "stable_predictors": sens_results.get('stable_predictors', [])
        },
        "conclusions": {
            "composition_predictive_power": "Pending expert review",
            "statistical_significance": "Pending expert review",
            "data_quality_note": "Data source is synthetic due to real data unavailability. Results are for pipeline validation only." if is_synthetic else "Real data used."
        }
    }
    
    return summary

def generate_summary_artifacts(summary: Dict[str, Any], config: Dict[str, Any]) -> None:
    """
    Generate final summary artifacts (JSON and CSV) for review.
    """
    artifacts_dir = Path(config['paths']['artifacts'])
    ensure_dirs([artifacts_dir])
    
    # Save full summary as JSON
    summary_json_path = artifacts_dir / 'final_summary.json'
    with open(summary_json_path, 'w') as f:
        json.dump(summary, f, indent=2, default=str)
    logger.info(f"Saved final summary to {summary_json_path}")
    
    # Create a simplified CSV for quick review of key metrics
    # Extract key metrics for CSV
    csv_data = []
    
    # Regression Metrics
    baseline_metrics = summary['regression_metrics']['baseline_model']
    full_metrics = summary['regression_metrics']['full_model']
    delta_r2 = summary['regression_metrics']['delta_r_squared']
    
    csv_data.append({
        'metric': 'Baseline R2',
        'value': baseline_metrics.get('r2', 'N/A'),
        'model': 'Baseline'
    })
    csv_data.append({
        'metric': 'Full R2',
        'value': full_metrics.get('r2', 'N/A'),
        'model': 'Full'
    })
    csv_data.append({
        'metric': 'Delta R2',
        'value': delta_r2.get('dst', 'N/A'),
        'model': 'Delta (Dst)'
    })
    csv_data.append({
        'metric': 'Delta R2',
        'value': delta_r2.get('kp', 'N/A'),
        'model': 'Delta (Kp)'
    })
    
    # Cross-Validation Metrics
    baseline_cv = summary['cross_validation']['baseline_cv']
    full_cv = summary['cross_validation']['full_cv']
    delta_cv = summary['cross_validation']['delta_cv_r_squared']
    
    csv_data.append({
        'metric': 'Baseline CV R2',
        'value': baseline_cv.get('mean_r2', 'N/A'),
        'model': 'Baseline'
    })
    csv_data.append({
        'metric': 'Full CV R2',
        'value': full_cv.get('mean_r2', 'N/A'),
        'model': 'Full'
    })
    csv_data.append({
        'metric': 'Delta CV R2',
        'value': delta_cv.get('mean', 'N/A'),
        'model': 'Delta'
    })
    
    # Significant Predictors from Permutation Tests
    significant_predictors = summary['permutation_tests']['significance_flags']
    for pred in significant_predictors:
        csv_data.append({
            'metric': 'Significant Predictor',
            'value': pred.get('predictor', 'N/A'),
            'model': f"Perm Test ({pred.get('target', 'N/A')})"
        })
    
    # Sensitivity Analysis
    stable_predictors = summary['sensitivity_analysis']['stable_predictors']
    for pred in stable_predictors:
        csv_data.append({
            'metric': 'Stable Predictor',
            'value': pred,
            'model': 'Sensitivity Analysis'
        })
    
    # Add data source info
    csv_data.append({
        'metric': 'Data Source',
        'value': summary['metadata']['data_source'],
        'model': 'Metadata'
    })
    csv_data.append({
        'metric': 'Is Synthetic',
        'value': summary['metadata']['is_synthetic'],
        'model': 'Metadata'
    })
    
    import pandas as pd
    df_summary = pd.DataFrame(csv_data)
    csv_path = artifacts_dir / 'final_summary.csv'
    df_summary.to_csv(csv_path, index=False)
    logger.info(f"Saved summary CSV to {csv_path}")

def main():
    """
    Main entry point for the pipeline.
    Orchestrates the execution of all stages and generates final reports.
    """
    parser = argparse.ArgumentParser(description='Solar Wind Composition and Geomagnetic Indices Analysis Pipeline')
    parser.add_argument('--config', type=str, default='code/config.py', help='Path to config file')
    parser.add_argument('--skip-ingestion', action='store_true', help='Skip data ingestion and alignment')
    parser.add_argument('--skip-analysis', action='store_true', help='Skip analysis stages (regression, CV, etc.)')
    parser.add_argument('--skip-reporting', action='store_true', help='Skip final reporting')
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(level=logging.INFO)
    
    # Load configuration
    try:
        config = get_config()
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        raise PipelineError(f"Configuration error: {e}")
    
    logger.info("Starting Solar Wind Composition and Geomagnetic Indices Analysis Pipeline")
    
    # Stage 1: Data Ingestion and Alignment (if not skipped)
    if not args.skip_ingestion:
        logger.info("Stage 1: Data Ingestion and Alignment")
        try:
            align_main()
        except Exception as e:
            logger.error(f"Ingestion/Alignment failed: {e}")
            # Continue with synthetic data if available, otherwise fail
            if not (Path(config['paths']['processed']) / 'aligned_data.parquet').exists():
                raise PipelineError("Ingestion/Alignment failed and no fallback data available.")
    
    # Stage 2: Coupling Functions (if not skipped)
    if not args.skip_analysis:
        logger.info("Stage 2: Coupling Functions")
        try:
            coupling_main()
        except Exception as e:
            logger.error(f"Coupling functions failed: {e}")
            raise PipelineError("Coupling functions failed.")
    
    # Stage 3: Regression Analysis (if not skipped)
    if not args.skip_analysis:
        logger.info("Stage 3: Regression Analysis")
        try:
            regression_main()
        except Exception as e:
            logger.error(f"Regression analysis failed: {e}")
            raise PipelineError("Regression analysis failed.")
    
    # Stage 4: Cross-Validation (if not skipped)
    if not args.skip_analysis:
        logger.info("Stage 4: Cross-Validation")
        try:
            cv_main()
        except Exception as e:
            logger.error(f"Cross-validation failed: {e}")
            raise PipelineError("Cross-validation failed.")
    
    # Stage 5: Permutation Tests (if not skipped)
    if not args.skip_analysis:
        logger.info("Stage 5: Permutation Tests")
        try:
            perm_main()
        except Exception as e:
            logger.error(f"Permutation tests failed: {e}")
            raise PipelineError("Permutation tests failed.")
    
    # Stage 6: Sensitivity Analysis (if not skipped)
    if not args.skip_analysis:
        logger.info("Stage 6: Sensitivity Analysis")
        try:
            sens_main()
        except Exception as e:
            logger.error(f"Sensitivity analysis failed: {e}")
            raise PipelineError("Sensitivity analysis failed.")
    
    # Stage 7: Final Reporting (if not skipped)
    if not args.skip_reporting:
        logger.info("Stage 7: Final Reporting")
        try:
            summary = aggregate_results(config)
            generate_summary_artifacts(summary, config)
            logger.info("Final reporting complete.")
        except Exception as e:
            logger.error(f"Final reporting failed: {e}")
            raise PipelineError(f"Final reporting failed: {e}")
    
    logger.info("Pipeline execution completed successfully.")

if __name__ == '__main__':
    main()