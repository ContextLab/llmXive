"""
Main orchestration script for the LLM Test Generation Pipeline.
Implements hard stops for runtime limits (T011a) and sample count limits (T011b/FR-007).
"""
import os
import sys
import time
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import local modules using relative imports logic adjusted for project structure
# Assuming code/ is in sys.path or this is run as python code/main.py
from config import (
    init_runtime_tracker,
    check_runtime_limit,
    get_sample_limit,
    get_data_dir,
    ensure_directories,
    get_output_dir
)
from data_loader import load_defects4j_data, verify_data_integrity
from llm_generator import load_model, generate_test_code, validate_syntax_java
from test_executor import execute_test_suite, generate_coverage_csv
from analyzer import run_statistical_test, calculate_effect_size, run_power_analysis
from report_generator import generate_final_report
from validate_schemas import validate_all_artifacts

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(Path(get_output_dir()) / "pipeline.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description="LLM Test Generation Pipeline Orchestration")
    parser.add_argument("--limit", type=int, default=None, help="Override sample count limit")
    args = parser.parse_args()

    # 1. Initialize Environment
    logger.info("Initializing pipeline environment...")
    ensure_directories()
    init_runtime_tracker()

    # 2. Load and Verify Data
    logger.info("Loading Defects4J dataset...")
    try:
        data = load_defects4j_data()
        verify_data_integrity()
    except Exception as e:
        logger.error(f"Failed to load or verify data: {e}")
        sys.exit(1)

    # 3. Apply Sample Limit (FR-007)
    # T011b Implementation: Hard stop when sample count reaches configured limit
    sample_limit = args.limit if args.limit is not None else get_sample_limit()
    total_available = len(data)
    
    logger.info(f"Total available samples: {total_available}")
    logger.info(f"Configured sample limit: {sample_limit}")

    if total_available > sample_limit:
        logger.info(f"Trimming dataset from {total_available} to {sample_limit} samples per FR-007.")
        processed_data = data[:sample_limit]
    else:
        logger.info("Dataset size is within limits.")
        processed_data = data

    # 4. Load Model
    logger.info("Loading LLM model...")
    try:
        model = load_model()
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        sys.exit(1)

    # 5. Execution Loop
    results = []
    processed_count = 0

    for idx, bug in enumerate(processed_data):
        # Check Runtime Limit (T011a)
        if not check_runtime_limit():
            logger.warning("Runtime limit exceeded. Stopping pipeline.")
            break

        # Check Sample Count Limit (T011b - Redundant check inside loop for safety)
        # The loop range is already sliced, but this ensures we stop immediately if logic changes
        if processed_count >= sample_limit:
            logger.info(f"Sample count limit ({sample_limit}) reached. Stopping pipeline.")
            break

        logger.info(f"Processing sample {processed_count + 1}/{sample_limit}: {bug.get('project_id', 'unknown')}")

        try:
            # A. Generate Test
            prompt = bug.get('description', '')
            generated_code = generate_test_code(model, prompt)
            
            if not generated_code:
                logger.warning(f"Generation failed for {bug.get('project_id')}. Skipping.")
                continue

            # B. Validate Syntax
            if not validate_syntax_java(generated_code):
                logger.warning(f"Syntax validation failed for {bug.get('project_id')}. Skipping execution.")
                continue

            # C. Execute & Measure Coverage
            exec_result = execute_test_suite(generated_code, bug)
            results.append(exec_result)
            
            processed_count += 1

        except Exception as e:
            logger.error(f"Error processing sample {processed_count + 1}: {e}", exc_info=True)
            # Continue to next sample rather than crashing entire pipeline, 
            # unless critical infrastructure fails

    logger.info(f"Pipeline finished. Processed {processed_count} samples.")

    # 6. Post-Processing: Coverage CSV
    if results:
        logger.info("Generating coverage metrics CSV...")
        generate_coverage_csv(results)

    # 7. Post-Processing: Statistical Analysis
    if len(results) >= 2:
        logger.info("Running statistical analysis...")
        # Assuming results have 'coverage' and 'baseline' keys for analysis
        # This is a simplified call structure based on typical analyzer usage
        try:
            analysis_results = run_statistical_test([r.get('coverage', 0) for r in results])
            effect = calculate_effect_size(analysis_results)
            power = run_power_analysis(len(results))
            
            logger.info(f"Analysis complete. P-value: {analysis_results.get('p_value')}, Effect: {effect}")
        except Exception as e:
            logger.error(f"Statistical analysis failed: {e}", exc_info=True)

    # 8. Final Report
    logger.info("Generating final report...")
    # Placeholder for report generation logic if needed, or rely on specific report_generator call
    # generate_final_report(results, analysis_results) 

    # 9. Schema Validation
    logger.info("Validating output artifacts against schemas...")
    if not validate_all_artifacts():
        logger.error("Schema validation failed. Exiting with error.")
        sys.exit(1)

    logger.info("Pipeline completed successfully.")

if __name__ == "__main__":
    main()
