"""
Main orchestrator for LLM-driven code simplification.

This script processes the validated functions from the data pipeline,
applies the simplification model, and outputs the simplified functions.

Input: data/processed/validated_functions.jsonl
Output: data/processed/simplified_functions.jsonl
"""

import json
import sys
import time
from pathlib import Path

# Project imports based on provided API surface
from utils.logger import (
    get_logger, 
    log_stage_start, 
    log_stage_complete, 
    log_stage_error,
    log_stage_exclusion
)
from models.simplify import run_simplification_pipeline, SimplificationError
from data.sample import load_validated_functions

# Configuration
INPUT_FILE = Path("data/processed/validated_functions.jsonl")
OUTPUT_FILE = Path("data/processed/simplified_functions.jsonl")
LOG_FILE = Path("results/simplification_execution.log")

# Ensure output directories exist
OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

logger = get_logger("main_simplify", log_file=str(LOG_FILE))

def main():
    """Execute the full simplification pipeline."""
    
    log_stage_start(logger, "simplification_pipeline", "Starting LLM simplification process")
    
    # Verify input file exists
    if not INPUT_FILE.exists():
        log_stage_error(logger, "simplification_pipeline", f"Input file not found: {INPUT_FILE}")
        print(f"ERROR: Input file {INPUT_FILE} does not exist. Run data pipeline first.")
        sys.exit(1)
    
    # Load validated functions
    logger.info(f"Loading validated functions from {INPUT_FILE}")
    try:
        functions = load_validated_functions(INPUT_FILE)
        total_count = len(functions)
        logger.info(f"Loaded {total_count} validated functions")
        
        if total_count == 0:
            log_stage_error(logger, "simplification_pipeline", "No functions loaded from input file")
            print("ERROR: No functions found in input file.")
            sys.exit(1)
            
    except Exception as e:
        log_stage_error(logger, "simplification_pipeline", f"Failed to load functions: {str(e)}")
        print(f"ERROR: Failed to load functions: {e}")
        sys.exit(1)
    
    # Process each function
    simplified_functions = []
    success_count = 0
    failure_count = 0
    start_time = time.time()
    
    logger.info(f"Beginning simplification of {total_count} functions...")
    
    for idx, func_data in enumerate(functions):
        func_id = func_data.get("id", f"func_{idx}")
        original_code = func_data.get("code", "")
        
        try:
            logger.debug(f"Processing function {idx+1}/{total_count}: {func_id}")
            
            # Run simplification pipeline
            simplified_code, metadata = run_simplification_pipeline(
                original_code=original_code,
                function_id=func_id
            )
            
            # Create output record
            result_record = {
                "id": func_id,
                "original_code": original_code,
                "simplified_code": simplified_code,
                "metadata": metadata,
                "stratum": func_data.get("stratum", "unknown")
            }
            
            simplified_functions.append(result_record)
            success_count += 1
            
            logger.info(f"Successfully simplified {func_id} (iteration {idx+1}/{total_count})")
            
        except SimplificationError as e:
            failure_count += 1
            log_stage_exclusion(
                logger, 
                "simplification_pipeline", 
                func_id, 
                "simplification_failed", 
                str(e)
            )
            logger.warning(f"Failed to simplify {func_id}: {str(e)}")
            
        except Exception as e:
            failure_count += 1
            log_stage_error(
                logger, 
                "simplification_pipeline", 
                f"Unexpected error processing {func_id}: {str(e)}"
            )
            logger.error(f"Unexpected error for {func_id}: {str(e)}", exc_info=True)
            
        # Progress logging every 10%
        if (idx + 1) % max(1, total_count // 10) == 0:
            progress = (idx + 1) / total_count * 100
            logger.info(f"Progress: {progress:.1f}% ({idx+1}/{total_count})")
    
    # Calculate statistics
    end_time = time.time()
    duration = end_time - start_time
    avg_time_per_func = duration / max(1, total_count)
    
    # Write output file
    logger.info(f"Writing {len(simplified_functions)} simplified functions to {OUTPUT_FILE}")
    try:
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            for record in simplified_functions:
                f.write(json.dumps(record, ensure_ascii=False) + '\n')
        
        logger.info(f"Successfully wrote {len(simplified_functions)} records to {OUTPUT_FILE}")
        
    except Exception as e:
        log_stage_error(logger, "simplification_pipeline", f"Failed to write output file: {str(e)}")
        print(f"ERROR: Failed to write output file: {e}")
        sys.exit(1)
    
    # Final summary
    log_stage_complete(logger, "simplification_pipeline", {
        "total_input": total_count,
        "successful": success_count,
        "failed": failure_count,
        "success_rate": success_count / max(1, total_count) * 100,
        "total_duration_seconds": duration,
        "avg_time_per_function_seconds": avg_time_per_func,
        "output_file": str(OUTPUT_FILE)
    })
    
    print(f"\n=== Simplification Complete ===")
    print(f"Input functions: {total_count}")
    print(f"Successful: {success_count}")
    print(f"Failed: {failure_count}")
    print(f"Success rate: {success_count / max(1, total_count) * 100:.1f}%")
    print(f"Total duration: {duration:.2f}s")
    print(f"Average time per function: {avg_time_per_func:.2f}s")
    print(f"Output file: {OUTPUT_FILE}")
    
    return 0 if failure_count == 0 else 1

if __name__ == "__main__":
    sys.exit(main())