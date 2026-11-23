"""
Track intermediate caches and derived steps for the synthetic logical dataset construction.

This module logs all derived intermediate steps and caches generated during the
conversion of GSM8K to pseudo-code format to `data/processed/intermediate_caches.json`.

It ensures that:
1. Every intermediate step derived from the original GSM8K problem is recorded.
2. The dependency graph structure is preserved in the cache log.
3. The output is a valid JSON file that can be used for overlap checking and validation.
"""

import json
import sys
import argparse
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import shared utilities
from utils.common import get_logger, ensure_dir, read_json, write_json, DataLoadError

# Import data conversion functions from existing modules
from data.convert_to_pseudo_code import convert_gsm8k_to_pseudo_code, extract_steps_from_gsm8k_question
from data.download_gsm8k import download_gsm8k

# Constants
DEFAULT_OUTPUT_PATH = "data/processed/intermediate_caches.json"
DEFAULT_RAW_DATA_PATH = "data/raw/gsm8k/train.jsonl"

logger = get_logger(__name__)


def process_single_example(
    example: Dict[str, Any], 
    problem_id: str,
    pseudo_code_output: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Process a single GSM8K example and extract intermediate steps for caching.
    
    Args:
        example: The raw GSM8K example dictionary containing 'question' and 'answer'.
        problem_id: Unique identifier for this problem.
        pseudo_code_output: Optional pre-computed pseudo-code output to avoid re-processing.
        
    Returns:
        A dictionary containing the cached intermediate steps and metadata.
    """
    cache_entry = {
        "problem_id": problem_id,
        "original_question": example.get("question", ""),
        "original_answer": example.get("answer", ""),
        "intermediate_steps": [],
        "dependency_edges": [],
        "pseudo_code_blocks": [],
        "processing_metadata": {
            "source": "gsm8k",
            "processed": True,
            "error": None
        }
    }
    
    try:
        # Extract steps if pseudo_code_output is not provided
        if pseudo_code_output is None:
            pseudo_code_output = convert_gsm8k_to_pseudo_code(example)
        
        # Extract intermediate steps from the pseudo-code output
        if "steps" in pseudo_code_output:
            for i, step in enumerate(pseudo_code_output["steps"]):
                step_entry = {
                    "step_id": f"{problem_id}_step_{i}",
                    "step_code": step.get("code", ""),
                    "derived_fact": step.get("fact", ""),
                    "dependencies": step.get("dependencies", []),
                    "is_leaf": len(step.get("dependencies", [])) == 0
                }
                cache_entry["intermediate_steps"].append(step_entry)
                
                # Add dependency edges for graph representation
                for dep in step.get("dependencies", []):
                    cache_entry["dependency_edges"].append({
                        "from": dep,
                        "to": step_entry["step_id"]
                    })
        
        # Store pseudo-code blocks
        if "pseudo_code" in pseudo_code_output:
            cache_entry["pseudo_code_blocks"] = pseudo_code_output["pseudo_code"]
            
        # Validate that we have at least one step
        if not cache_entry["intermediate_steps"]:
            logger.warning(f"No intermediate steps found for problem {problem_id}")
            cache_entry["processing_metadata"]["error"] = "No intermediate steps extracted"
            
    except Exception as e:
        logger.error(f"Error processing problem {problem_id}: {str(e)}")
        cache_entry["processing_metadata"]["error"] = str(e)
        cache_entry["processing_metadata"]["processed"] = False
        
    return cache_entry


def track_all_caches(
    raw_data_path: str,
    output_path: str,
    max_examples: Optional[int] = None
) -> Dict[str, Any]:
    """
    Process all examples from the raw GSM8K dataset and track intermediate caches.
    
    Args:
        raw_data_path: Path to the raw GSM8K dataset (JSONL format).
        output_path: Path where the intermediate caches JSON file will be saved.
        max_examples: Optional limit on the number of examples to process.
        
    Returns:
        A summary dictionary with processing statistics.
    """
    logger.info(f"Loading raw data from {raw_data_path}")
    
    # Load raw data
    try:
        raw_data = read_json(raw_data_path)
    except FileNotFoundError:
        # Try to download if file doesn't exist
        logger.info(f"Raw data not found at {raw_data_path}, attempting download...")
        download_gsm8k(raw_data_path)
        raw_data = read_json(raw_data_path)
    except Exception as e:
        raise DataLoadError(f"Failed to load raw data: {str(e)}")
    
    if not isinstance(raw_data, list):
        # If it's a single JSON object with a 'data' key, extract the list
        if isinstance(raw_data, dict) and "data" in raw_data:
            raw_data = raw_data["data"]
        else:
            raise DataLoadError("Expected raw data to be a list of examples")
    
    # Limit examples if specified
    if max_examples is not None:
        raw_data = raw_data[:max_examples]
        logger.info(f"Processing {len(raw_data)} examples (limited to {max_examples})")
    else:
        logger.info(f"Processing {len(raw_data)} examples")
    
    # Process each example
    all_caches = []
    success_count = 0
    error_count = 0
    
    for i, example in enumerate(raw_data):
        problem_id = f"gsm8k_{i}"
        
        try:
            cache_entry = process_single_example(example, problem_id)
            all_caches.append(cache_entry)
            
            if cache_entry["processing_metadata"]["processed"]:
                success_count += 1
            else:
                error_count += 1
                
        except Exception as e:
            logger.error(f"Critical error processing example {i}: {str(e)}")
            error_count += 1
            
        # Log progress every 100 examples
        if (i + 1) % 100 == 0:
            logger.info(f"Processed {i + 1}/{len(raw_data)} examples")
    
    # Prepare summary
    summary = {
        "total_examples": len(raw_data),
        "successful_processes": success_count,
        "failed_processes": error_count,
        "success_rate": success_count / len(raw_data) if raw_data else 0.0,
        "output_file": output_path,
        "cache_entries_count": len(all_caches)
    }
    
    # Write output
    ensure_dir(output_path)
    output_data = {
        "metadata": summary,
        "caches": all_caches
    }
    
    write_json(output_path, output_data)
    logger.info(f"Successfully wrote intermediate caches to {output_path}")
    logger.info(f"Summary: {summary['successful_processes']}/{summary['total_examples']} examples processed successfully")
    
    return summary


def main():
    """Main entry point for the cache tracking script."""
    parser = argparse.ArgumentParser(
        description="Track intermediate caches from GSM8K to pseudo-code conversion"
    )
    parser.add_argument(
        "--input", 
        type=str, 
        default=DEFAULT_RAW_DATA_PATH,
        help=f"Path to raw GSM8K data (default: {DEFAULT_RAW_DATA_PATH})"
    )
    parser.add_argument(
        "--output", 
        type=str, 
        default=DEFAULT_OUTPUT_PATH,
        help=f"Path for output intermediate caches JSON (default: {DEFAULT_OUTPUT_PATH})"
    )
    parser.add_argument(
        "--max-examples", 
        type=int, 
        default=None,
        help="Maximum number of examples to process (optional)"
    )
    parser.add_argument(
        "--log-level", 
        type=str, 
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level (default: INFO)"
    )
    
    args = parser.parse_args()
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    try:
        summary = track_all_caches(
            raw_data_path=args.input,
            output_path=args.output,
            max_examples=args.max_examples
        )
        
        # Print summary
        print("\n=== Cache Tracking Summary ===")
        print(f"Total examples: {summary['total_examples']}")
        print(f"Successful: {summary['successful_processes']}")
        print(f"Failed: {summary['failed_processes']}")
        print(f"Success rate: {summary['success_rate']:.2%}")
        print(f"Output file: {summary['output_file']}")
        
        # Exit with error if success rate is 0
        if summary['success_rate'] == 0.0:
            logger.error("No examples were successfully processed!")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Fatal error in cache tracking: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
