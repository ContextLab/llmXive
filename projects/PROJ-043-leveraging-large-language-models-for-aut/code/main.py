"""
Main orchestrator for the modeling pipeline (User Story 3).
Implements T033: Cross-validation, OLS fitting, Paired T-Test, and validation.
"""
import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

from utils.logging import get_logger, ValidationFailedError
from models.regression import run_regression_analysis
from models.stats import run_statistical_tests
from utils.schema_validation import validate_output

logger = get_logger(__name__)

# Paths
DATA_DIR = Path(__file__).parent.parent / "data"
PROCESSED_DIR = DATA_DIR / "processed"
RESULTS_DIR = DATA_DIR / "results"
INPUT_FILE = PROCESSED_DIR / "refactoring_results.json"
OUTPUT_FILE = RESULTS_DIR / "model_summary.json"

def load_processed_data(input_path: Path) -> List[Dict[str, Any]]:
    """Load the processed refactoring results from JSON."""
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    with open(input_path, 'r') as f:
        data = json.load(f)
    
    logger.info(f"Loaded {len(data)} samples from {input_path}")
    return data

def run_cross_validation(data: List[Dict[str, Any]], k: int = 5) -> Dict[str, Any]:
    """
    Run k-fold cross-validation on the regression model.
    Returns mean coefficients across all folds.
    """
    # This is a simplified version that calls the regression module
    # The actual cross-validation logic is implemented in run_regression_analysis
    # which returns the cross-validation mean coefficients.
    return {}

def run_t_tests(data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Run paired t-tests on the delta distributions.
    Returns the t-test results for each metric.
    """
    # This is handled by run_statistical_tests
    return {}

def validate_and_save(result: Dict[str, Any], output_path: Path) -> None:
    """
    Validate the result against the output schema and save to disk.
    Raises ValidationFailedError if validation fails.
    """
    try:
        validate_output(result)
        logger.info("Output validation passed")
    except Exception as e:
        logger.error(f"Output validation failed: {str(e)}")
        raise ValidationFailedError(f"Validation failed: {str(e)}")
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)
    
    logger.info(f"Model summary saved to {output_path}")

def main():
    """
    Main entry point for the modeling pipeline.
    Executes the full workflow: load data, run regression, run stats, validate, save.
    """
    start_time = time.time()
    
    try:
        # 1. Load processed data
        if not INPUT_FILE.exists():
            logger.error(f"Input file not found: {INPUT_FILE}")
            sys.exit(1)
        
        data = load_processed_data(INPUT_FILE)
        
        if len(data) == 0:
            logger.error("No data found in input file")
            sys.exit(1)
        
        # 2. Run regression analysis (VIF filtering + OLS + Cross-validation)
        logger.info("Running regression analysis...")
        regression_results = run_regression_analysis(
            data, 
            output_path=RESULTS_DIR / "regression_results.json"
        )
        
        # 3. Run statistical tests (Paired T-Test)
        logger.info("Running statistical tests...")
        stats_results = run_statistical_tests(
            data,
            output_path=RESULTS_DIR / "stats_results.json"
        )
        
        # 4. Combine results into summary
        execution_time = time.time() - start_time
        
        summary = {
            "metadata": {
                "timestamp": datetime.utcnow().isoformat(),
                "version": "1.0.0",
                "input_file": str(INPUT_FILE),
                "sample_count": len(data),
                "execution_time_seconds": execution_time
            },
            "model_results": regression_results.get("model_results", {}),
            "statistical_tests": stats_results.get("statistical_tests", {}),
            "cross_validation_mean_coefficients": regression_results.get("cross_validation_mean_coefficients", {}),
            "adjusted_r_squared": regression_results.get("adjusted_r_squared", 0.0),
            "vif_filtered_predictors": regression_results.get("vif_filtered_predictors", []),
            "execution_time_seconds": execution_time
        }
        
        # 5. Validate and save
        logger.info("Validating output...")
        validate_and_save(summary, OUTPUT_FILE)
        
        logger.info(f"Modeling pipeline completed successfully in {execution_time:.2f} seconds")
        return 0
        
    except Exception as e:
        logger.error(f"Modeling pipeline failed: {str(e)}")
        raise

if __name__ == "__main__":
    sys.exit(main() if main() else 0)
