"""
Performance validation module for the molecular complexity degradation pipeline.

This module validates the pipeline execution time against a defined operational threshold.
It reads the timing results from the pipeline runner and compares them against the
configured threshold to determine if the pipeline meets performance requirements.
"""

import os
import sys
import time
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# Import from local modules using the provided API surface
from logging_config import setup_logging, get_logger, log_pipeline_start, log_pipeline_complete, log_pipeline_failure
from config import get_config, ensure_directories

# Operational threshold constants
DEFAULT_EXECUTION_THRESHOLD_SECONDS = 300.0  # 5 minutes
PERFORMANCE_LOG_FILE = "data/output/performance_validation.json"

def setup_performance_logging():
    """Setup dedicated logging for performance validation."""
    return setup_logging(log_file="data/output/performance_validation.log", 
                       name="performance_validator")

def load_pipeline_timing_results(timing_file: str) -> Dict[str, Any]:
    """
    Load pipeline execution timing results from the pipeline runner.
    
    Args:
        timing_file: Path to the timing results JSON file
        
    Returns:
        Dictionary containing timing results
        
    Raises:
        FileNotFoundError: If timing file doesn't exist
        json.JSONDecodeError: If timing file is invalid JSON
    """
    path = Path(timing_file)
    if not path.exists():
        raise FileNotFoundError(f"Pipeline timing results not found: {timing_file}")
    
    with open(path, 'r') as f:
        return json.load(f)

def validate_pipeline_performance(timing_results: Dict[str, Any], 
                                threshold_seconds: float = None) -> Dict[str, Any]:
    """
    Validate pipeline execution time against operational threshold.
    
    Args:
        timing_results: Dictionary containing pipeline execution timing data
        threshold_seconds: Maximum allowed execution time in seconds
        
    Returns:
        Dictionary containing validation results
    """
    if threshold_seconds is None:
        threshold_seconds = DEFAULT_EXECUTION_THRESHOLD_SECONDS
    
    logger = get_logger("performance_validator")
    
    total_time = timing_results.get('total_execution_time_seconds', 0.0)
    stage_times = timing_results.get('stage_times', {})
    
    # Determine pass/fail status
    passed = total_time <= threshold_seconds
    
    # Build validation result
    validation_result = {
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'threshold_seconds': threshold_seconds,
        'actual_execution_time_seconds': total_time,
        'passed': passed,
        'margin_seconds': threshold_seconds - total_time,
        'stage_breakdown': stage_times,
        'details': {
            'status': 'PASS' if passed else 'FAIL',
            'message': f"Pipeline executed in {total_time:.2f}s (threshold: {threshold_seconds}s)"
        }
    }
    
    if passed:
        logger.info(f"Performance validation PASSED: {total_time:.2f}s <= {threshold_seconds}s")
    else:
        logger.warning(f"Performance validation FAILED: {total_time:.2f}s > {threshold_seconds}s")
    
    return validation_result

def save_validation_results(validation_result: Dict[str, Any], 
                          output_file: str = None) -> None:
    """
    Save validation results to a JSON file.
    
    Args:
        validation_result: Dictionary containing validation results
        output_file: Path to output file
    """
    if output_file is None:
        output_file = PERFORMANCE_LOG_FILE
    
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(validation_result, f, indent=2)
    
    logging.getLogger("performance_validator").info(f"Validation results saved to {output_file}")

def main():
    """
    Main entry point for performance validation.
    
    This function:
    1. Loads pipeline timing results from the pipeline runner
    2. Validates execution time against threshold
    3. Saves validation results
    4. Returns exit code based on validation status
    """
    logger = setup_performance_logging()
    logger.info("Starting pipeline performance validation")
    
    try:
        # Load configuration
        config = get_config()
        threshold = config.get('performance', {}).get('execution_threshold_seconds', 
                                                    DEFAULT_EXECUTION_THRESHOLD_SECONDS)
        
        # Determine timing results file path
        timing_file = config.get('paths', {}).get('timing_results', 
                                                 'data/output/pipeline_timing.json')
        
        # Load timing results
        logger.info(f"Loading timing results from {timing_file}")
        timing_results = load_pipeline_timing_results(timing_file)
        
        # Validate performance
        logger.info(f"Validating against threshold: {threshold}s")
        validation_result = validate_pipeline_performance(timing_results, threshold)
        
        # Save results
        output_file = config.get('paths', {}).get('performance_validation', 
                                                 'data/output/performance_validation.json')
        save_validation_results(validation_result, output_file)
        
        # Log summary
        logger.info("="*60)
        logger.info("PERFORMANCE VALIDATION SUMMARY")
        logger.info("="*60)
        logger.info(f"Threshold: {threshold}s")
        logger.info(f"Actual Time: {validation_result['actual_execution_time_seconds']:.2f}s")
        logger.info(f"Status: {validation_result['details']['status']}")
        logger.info(f"Message: {validation_result['details']['message']}")
        logger.info("="*60)
        
        # Return appropriate exit code
        if validation_result['passed']:
            logger.info("Performance validation completed successfully")
            return 0
        else:
            logger.warning("Performance validation failed - pipeline too slow")
            return 1
            
    except FileNotFoundError as e:
        logger.error(f"Timing results file not found: {e}")
        logger.error("Please run the pipeline first to generate timing results")
        return 2
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in timing results file: {e}")
        return 3
    except Exception as e:
        logger.error(f"Unexpected error during performance validation: {e}")
        log_pipeline_failure("performance_validation", str(e))
        return 4

if __name__ == "__main__":
    sys.exit(main())
