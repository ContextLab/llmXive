"""
Main orchestration script for the automated test generation pipeline.
Coordinates data loading, test generation, execution, and analysis.
"""
import os
import sys
import time
import logging
import argparse
import json
from pathlib import Path

from config import (
    init_runtime_tracker,
    check_runtime_limit,
    get_sample_limit,
    get_runtime_limit,
    get_data_dir,
    get_output_dir,
    get_model_path,
)
from data_loader import (
    load_state,
    save_state,
    ensure_data_loaded_and_integrity_recorded,
    load_defects4j_data,
    extract_bug_fix_description,
    extract_changed_lines,
)
from llm_generator import load_model, generate_test_code, validate_syntax_java
from test_executor import execute_test_suite, generate_coverage_csv
from analyzer import run_statistical_test, calculate_effect_size, run_power_analysis
from report_generator import generate_final_report
from validate_schemas import validate_all_artifacts

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

class RuntimeLimitExceeded(Exception):
    """Raised when the execution time exceeds the configured limit."""
    pass

class SampleLimitExceeded(Exception):
    """Raised when the number of processed samples exceeds the configured limit."""
    pass

def check_sample_limit(processed_count: int) -> bool:
    """
    Checks if the processed count exceeds the configured sample limit.
    
    Args:
        processed_count: The number of samples processed so far.
        
    Returns:
        True if the limit has not been exceeded, False otherwise.
        
    Raises:
        SampleLimitExceeded: If processed_count >= configured limit.
    """
    sample_limit = get_sample_limit()
    if sample_limit is not None and processed_count >= sample_limit:
        raise SampleLimitExceeded(
            f"Sample limit of {sample_limit} reached. Stopping pipeline."
        )
    return True

def run_pipeline(args):
    """
    Executes the full pipeline: data loading, test generation, execution, and analysis.
    """
    logger.info("Starting pipeline execution...")
    
    # Initialize runtime tracker
    init_runtime_tracker()
    
    # Load or initialize project state
    state = load_state()
    
    try:
        # Ensure data is loaded and integrity is recorded
        logger.info("Ensuring data is loaded and integrity is recorded...")
        ensure_data_loaded_and_integrity_recorded()
        
        # Load Defects4J data
        logger.info("Loading Defects4J data...")
        data = load_defects4j_data()
        
        # Extract changed lines (prerequisite for coverage calculation)
        logger.info("Extracting changed lines...")
        extract_changed_lines(data)
        
        # Get limits
        sample_limit = get_sample_limit()
        runtime_limit = get_runtime_limit()
        
        processed_count = 0
        results = []
        
        # Process samples
        for sample in data:
            # Check runtime limit
            if not check_runtime_limit():
                raise RuntimeLimitExceeded(
                    f"Runtime limit of {runtime_limit} seconds exceeded."
                )
            
            # Check sample limit
            check_sample_limit(processed_count)
            
            # Extract bug fix description
            prompt = extract_bug_fix_description(sample)
            
            # Generate test code
            test_code = generate_test_code(prompt)
            
            # Validate syntax
            is_valid = validate_syntax_java(test_code)
            
            if is_valid:
                # Execute test and get coverage
                coverage_result = execute_test_suite(sample, test_code)
                results.append(coverage_result)
            
            processed_count += 1
            state["processed_samples"] = processed_count
            save_state(state)
        
        # Generate coverage CSV
        logger.info("Generating coverage metrics CSV...")
        generate_coverage_csv(results)
        
        # Run statistical analysis
        logger.info("Running statistical analysis...")
        analysis_results = run_statistical_test("data/coverage_metrics.csv")
        effect_size = calculate_effect_size(analysis_results)
        power_analysis = run_power_analysis(analysis_results)
        
        # Generate final report
        logger.info("Generating final report...")
        generate_final_report(analysis_results, effect_size, power_analysis)
        
        # Validate all artifacts
        logger.info("Validating artifacts...")
        validate_all_artifacts()
        
        logger.info("Pipeline completed successfully.")
        
    except (RuntimeLimitExceeded, SampleLimitExceeded) as e:
        logger.error(f"Pipeline stopped due to limit: {e}")
        raise
    except Exception as e:
        logger.error(f"Pipeline failed with error: {e}")
        raise

def main():
    """Entry point for the pipeline."""
    parser = argparse.ArgumentParser(description="Automated Test Generation Pipeline")
    parser.add_argument(
        "--sample-limit",
        type=int,
        default=None,
        help="Maximum number of samples to process",
    )
    parser.add_argument(
        "--runtime-limit",
        type=int,
        default=None,
        help="Maximum runtime in seconds",
    )
    args = parser.parse_args()
    
    try:
        run_pipeline(args)
    except (RuntimeLimitExceeded, SampleLimitExceeded) as e:
        logger.info(f"Pipeline terminated: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()