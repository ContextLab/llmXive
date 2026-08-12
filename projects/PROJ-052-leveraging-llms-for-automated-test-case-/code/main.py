import os
import sys
import time
import logging
import argparse
from pathlib import Path
from typing import List, Optional, Dict, Any

# Import from project modules (API surface)
from config import (
    init_runtime_tracker,
    check_runtime_limit,
    get_sample_limit,
    get_runtime_limit,
    get_data_dir,
    get_output_dir,
    ensure_directories
)
from data_loader import (
    load_state,
    save_state,
    ensure_data_loaded_and_integrity_recorded,
    load_defects4j_data
)
from llm_generator import generate_test_code
from test_executor import execute_test_suite, generate_coverage_csv
from analyzer import run_statistical_test, calculate_effect_size
from report_generator import generate_final_report
from validate_schemas import validate_all_artifacts

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(os.path.join(get_data_dir(), 'pipeline.log'))
    ]
)
logger = logging.getLogger(__name__)

def run_pipeline(args: Optional[argparse.Namespace] = None) -> int:
    """
    Main orchestration logic for the LLM test generation pipeline.
    
    Implements:
    - Hard stop when runtime exceeds configured limit (T011a)
    - Hard stop when sample count reaches configured limit (T011b, FR-007)
    - Full pipeline execution: Data -> Generation -> Execution -> Analysis -> Report
    
    Args:
        args: Command line arguments (optional, for testing)
        
    Returns:
        0 on success, 1 on failure
    """
    # Initialize directories
    ensure_directories()
    
    # Initialize runtime tracker (T011a)
    init_runtime_tracker()
    
    # Parse arguments if not provided
    if args is None:
        parser = argparse.ArgumentParser(description='LLM Test Generation Pipeline')
        parser.add_argument('--limit', type=int, help='Override sample count limit')
        parser.add_argument('--no-verify', action='store_true', help='Skip data integrity verification')
        args = parser.parse_args()
    
    # Get configuration limits
    sample_limit = args.limit if args.limit is not None else get_sample_limit()
    runtime_limit = get_runtime_limit()
    
    logger.info(f"Pipeline starting with sample limit: {sample_limit}, runtime limit: {runtime_limit}s")
    
    # Step 1: Ensure data is loaded and integrity is recorded
    try:
        if not args.no_verify:
            ensure_data_loaded_and_integrity_recorded()
        else:
            logger.warning("Skipping data integrity verification as requested")
            load_defects4j_data()
    except Exception as e:
        logger.error(f"Failed to load or verify data: {e}")
        return 1
    
    # Step 2: Load the dataset
    try:
        data = load_defects4j_data()
        if data is None or len(data) == 0:
            logger.error("No data loaded from Defects4J")
            return 1
    except Exception as e:
        logger.error(f"Failed to load Defects4J data: {e}")
        return 1
    
    # Apply sample limit (FR-007)
    if len(data) > sample_limit:
        logger.info(f"Truncating dataset from {len(data)} to {sample_limit} samples per FR-007")
        data = data[:sample_limit]
    
    logger.info(f"Processing {len(data)} bug fix descriptions")
    
    # Step 3: Generate test code for each sample
    generated_tests = []
    processed_count = 0
    
    for idx, bug in enumerate(data):
        # Check runtime limit before processing each item
        if not check_runtime_limit():
            logger.error(f"Runtime limit exceeded after processing {processed_count} samples. Stopping.")
            break
        
        # Check sample count limit (FR-007)
        if processed_count >= sample_limit:
            logger.info(f"Sample count limit ({sample_limit}) reached. Stopping generation.")
            break
        
        try:
            logger.info(f"Processing sample {idx + 1}/{len(data)}: {bug.get('project_id', 'unknown')}")
            
            # Generate test code
            test_code = generate_test_code(bug)
            
            if test_code:
                generated_tests.append({
                    'project_id': bug.get('project_id'),
                    'test_code': test_code,
                    'status': 'generated'
                })
                processed_count += 1
                logger.info(f"Successfully generated test for {bug.get('project_id')}")
            else:
                logger.warning(f"Failed to generate test for {bug.get('project_id')}")
                
        except Exception as e:
            logger.error(f"Error generating test for {bug.get('project_id')}: {e}")
            continue
    
    # Step 4: Execute tests and calculate coverage
    if not generated_tests:
        logger.warning("No tests generated. Skipping execution phase.")
        return 0
    
    try:
        execution_results = execute_test_suite(generated_tests)
    except Exception as e:
        logger.error(f"Error executing tests: {e}")
        execution_results = []
    
    # Step 5: Generate coverage CSV
    try:
        generate_coverage_csv(execution_results)
        logger.info("Coverage metrics CSV generated successfully")
    except Exception as e:
        logger.error(f"Error generating coverage CSV: {e}")
    
    # Step 6: Perform statistical analysis
    try:
        analysis_results = run_statistical_test(execution_results)
        if analysis_results:
            effect_size = calculate_effect_size(analysis_results)
            analysis_results['effect_size'] = effect_size
            logger.info("Statistical analysis completed")
    except Exception as e:
        logger.error(f"Error performing statistical analysis: {e}")
        analysis_results = None
    
    # Step 7: Generate final report
    try:
        generate_final_report(
            generated_tests=generated_tests,
            execution_results=execution_results,
            analysis_results=analysis_results
        )
        logger.info("Final report generated successfully")
    except Exception as e:
        logger.error(f"Error generating final report: {e}")
    
    # Step 8: Validate all output artifacts
    try:
        if not validate_all_artifacts():
            logger.warning("Some artifacts failed schema validation")
        else:
            logger.info("All artifacts validated successfully")
    except Exception as e:
        logger.error(f"Error validating artifacts: {e}")
    
    logger.info("Pipeline completed successfully")
    return 0

def main():
    """Entry point for the pipeline."""
    try:
        exit_code = run_pipeline()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("Pipeline interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Unhandled exception in pipeline: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()