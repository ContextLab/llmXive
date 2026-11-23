import json
import os
import sys
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

# Add the project root to the path so imports work when running from code/
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.logger import get_logger, log_pipeline_step, log_model_fit_start, log_model_fit_success, log_model_fit_error
from utils.constants import get_min_sample_size, get_significance_level
from utils.exceptions import (
    DataLoadError,
    DataGapError,
    InsufficientSampleError,
    CausalLanguageViolationError,
    StabilityThresholdViolationError,
    LongitudinalMismatchError
)

# Import data pipeline modules
from data.loader import load_real_data
from data.generator import generate_synthetic_data, verify_association_recovery, validate_rses_psychometrics
from data.validator import validate_data
from data.processor import add_psv_column

# Import analysis modules
from analysis.regression import fit_multiple_linear_regression, calculate_vif, check_vif_results, generate_associational_report, run_analysis
from analysis.sensitivity import run_sensitivity_analysis, check_stability
from analysis.nonlinearity import run_nonlinearity_analysis

# Import viz modules
from viz.plots import run_viz_pipeline
from viz.validator import count_generated_visualizations, validate_visualization_count

logger = get_logger(__name__)

def load_or_generate_data(stage: Optional[str] = None) -> Any:
    """
    Orchestrates the data loading and generation process.
    Tries to load real data first. If that fails, generates synthetic data.
    Validates the data and ensures required columns are present.
    """
    log_pipeline_step(logger, "Starting data acquisition stage")
    
    data = None
    source = None
    
    # 1. Attempt to load real data
    try:
        log_pipeline_step(logger, "Attempting to load real dataset...")
        data = load_real_data()
        source = "real"
    except DataLoadError as e:
        log_pipeline_step(logger, f"Real data load failed: {e}. Switching to synthetic generation.")
        data = None
    
    # 2. Generate synthetic data if real data failed
    if data is None:
        log_pipeline_step(logger, "Generating synthetic data using SEM model...")
        try:
            df = generate_synthetic_data(n_samples=1000) # Default sample size
            
            # Verify psychometric properties (RSES)
            validate_rses_psychometrics(df)
            
            # Verify association recovery
            # Note: This is a validation step, not a causal claim
            verify_association_recovery(df)
            
            data = df
            source = "synthetic"
        except Exception as e:
            log_model_fit_error(logger, f"Synthetic data generation failed: {e}")
            raise RuntimeError(f"Failed to generate synthetic data: {e}")
    
    # 3. Validate the data
    log_pipeline_step(logger, "Validating data structure and content...")
    try:
        validate_data(data)
    except (DataGapError, InsufficientSampleError, LongitudinalMismatchError) as e:
        log_model_fit_error(logger, f"Data validation failed: {e}")
        raise e
    
    # 4. Calculate Perceived Social Validation (PSV)
    log_pipeline_step(logger, "Calculating Perceived Social Validation (PSV) metric...")
    data = add_psv_column(data)
    
    log_pipeline_step(logger, f"Data acquisition complete. Source: {source}, N={len(data)}")
    return data, source

def run_regression_analysis(data: Any, source: str) -> Dict[str, Any]:
    """
    Runs the multiple linear regression analysis.
    Calculates VIF, fits the model, and checks for causal language violations.
    Saves results to versioned JSON files.
    """
    log_pipeline_step(logger, "Starting regression analysis stage")
    
    results = {}
    
    # 1. Calculate VIF
    log_pipeline_step(logger, "Calculating Variance Inflation Factors (VIF)...")
    vif_results = calculate_vif(data)
    
    # 2. Check VIF against threshold
    log_pipeline_step(logger, "Checking VIF results against threshold...")
    vif_status = check_vif_results(vif_results)
    
    # 3. Fit the regression model
    log_model_fit_start(logger, "Fitting multiple linear regression model...")
    try:
        model_results = fit_multiple_linear_regression(data)
        log_model_fit_success(logger, "Regression model fitted successfully.")
    except Exception as e:
        log_model_fit_error(logger, f"Regression model fitting failed: {e}")
        raise e
    
    # 4. Generate associational report (checks for causal language)
    log_pipeline_step(logger, "Generating associational report and checking for causal language...")
    try:
        report_buffer = generate_associational_report(model_results)
        # The report generation itself checks for causal language and raises if found
        # If we are here, no causal language was found in the report buffer
    except CausalLanguageViolationError as e:
        log_model_fit_error(logger, f"Causal language violation detected: {e}")
        raise e
    
    # 5. Prepare results for saving
    results['vif_results'] = {
        'values': vif_results,
        'threshold': 5.0, # Default threshold, could be dynamic
        'status': vif_status
    }
    
    # Extract regression results
    results['regression_results'] = {
        'coefficients': model_results['coefficients'],
        'p_values': model_results['p_values'],
        'ci_lower': model_results['ci_lower'],
        'ci_upper': model_results['ci_upper'],
        'r_squared': model_results['r_squared'],
        'adj_r_squared': model_results['adj_r_squared']
    }
    
    # 6. Save results to versioned file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = project_root / "data" / "processed" / f"model_results_v{timestamp}.json"
    
    # Ensure directory exists
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    log_pipeline_step(logger, f"Regression results saved to {output_file}")
    
    return results, output_file

def run_robustness_checks(data: Any, model_results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Runs sensitivity analysis and non-linearity checks.
    Checks for stability violations and saves results.
    """
    log_pipeline_step(logger, "Starting robustness checks stage")
    
    robustness_results = {}
    
    # 1. Run Sensitivity Analysis
    log_pipeline_step(logger, "Running sensitivity analysis...")
    try:
        sensitivity_results = run_sensitivity_analysis(data)
        robustness_results['sensitivity'] = sensitivity_results
        
        # Check stability (this raises StabilityThresholdViolationError if unstable)
        check_stability(sensitivity_results)
        log_pipeline_step(logger, "Stability check passed.")
    except StabilityThresholdViolationError as e:
        log_model_fit_error(logger, f"Stability threshold violated: {e}")
        raise e
    except Exception as e:
        log_model_fit_error(logger, f"Sensitivity analysis failed: {e}")
        raise e
    
    # 2. Run Non-linearity Check
    log_pipeline_step(logger, "Running non-linearity analysis...")
    try:
        nonlinearity_results = run_nonlinearity_analysis(data)
        robustness_results['nonlinearity'] = nonlinearity_results
    except Exception as e:
        log_model_fit_error(logger, f"Non-linearity analysis failed: {e}")
        raise e
    
    # 3. Save sensitivity results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    sensitivity_file = project_root / "data" / "processed" / f"sensitivity_analysis_v{timestamp}.json"
    sensitivity_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(sensitivity_file, 'w') as f:
        json.dump(robustness_results['sensitivity'], f, indent=2)
    
    log_pipeline_step(logger, f"Sensitivity results saved to {sensitivity_file}")
    
    return robustness_results

def run_viz_stage(data: Any) -> Dict[str, Any]:
    """
    Runs the visualization pipeline.
    Generates plots and validates that required visualizations were created.
    """
    log_pipeline_step(logger, "Starting visualization stage")
    
    viz_results = {}
    
    # 1. Generate Plots
    log_pipeline_step(logger, "Generating diagnostic plots...")
    try:
        plot_files = run_viz_pipeline(data)
        viz_results['generated_files'] = plot_files
    except Exception as e:
        log_model_fit_error(logger, f"Visualization generation failed: {e}")
        raise e
    
    # 2. Validate Visualization Count
    log_pipeline_step(logger, "Validating visualization count...")
    try:
        count, missing = count_generated_visualizations()
        validate_visualization_count(count, missing)
        log_pipeline_step(logger, f"Visualization validation passed. Count: {count}")
    except InsufficientSampleError as e:
        log_model_fit_error(logger, f"Insufficient visualizations generated: {e}")
        raise e
    
    return viz_results

def main():
    """
    Main entry point for the pipeline.
    Supports stage-based execution via command line arguments.
    """
    # Parse arguments
    stage = None
    if len(sys.argv) > 1:
        stage = sys.argv[1].lower()
    
    try:
        if stage in [None, 'data', 'full']:
            # Data Stage
            data, source = load_or_generate_data(stage)
            
            if stage == 'data':
                log_pipeline_step(logger, "Data stage complete.")
                return

        if stage in [None, 'analysis', 'full']:
            # Analysis Stage
            if stage == 'analysis':
                # If running analysis only, we assume data is already processed or re-load it
                # For simplicity, we re-run the data stage or load from disk if needed
                # In a real system, we'd load the processed data file
                data, source = load_or_generate_data() 
            
            results, output_file = run_regression_analysis(data, source)
            
            if stage == 'analysis':
                log_pipeline_step(logger, "Analysis stage complete.")
                return

        if stage in [None, 'robustness', 'full']:
            # Robustness Stage (requires analysis results)
            # Re-load data and run analysis if not already done in this run
            if stage == 'robustness':
                data, source = load_or_generate_data()
                results, _ = run_regression_analysis(data, source)
            
            robustness_results = run_robustness_checks(data, results)
            
            if stage == 'robustness':
                log_pipeline_step(logger, "Robustness stage complete.")
                return

        if stage in [None, 'viz', 'full']:
            # Viz Stage
            if stage == 'viz':
                data, source = load_or_generate_data()
            
            viz_results = run_viz_stage(data)
            
            if stage == 'viz':
                log_pipeline_step(logger, "Visualization stage complete.")
                return

        if stage == 'full' or stage is None:
            log_pipeline_step(logger, "Pipeline execution complete.")

    except (DataLoadError, DataGapError, InsufficientSampleError, 
            CausalLanguageViolationError, StabilityThresholdViolationError,
            LongitudinalMismatchError) as e:
        log_model_fit_error(logger, f"Pipeline failed with expected error: {e}")
        sys.exit(1)
    except Exception as e:
        log_model_fit_error(logger, f"Pipeline failed with unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()