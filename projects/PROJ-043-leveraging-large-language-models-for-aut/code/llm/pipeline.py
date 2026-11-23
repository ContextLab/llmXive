"""
Orchestration pipeline for User Story 2: Refactoring, Baseline, and Quality Measurement.

This module coordinates the execution of:
1. Loading processed data from US1 (raw_metrics.json)
2. Generating null baselines (identity transformation)
3. Invoking LLM for zero-shot refactoring
4. Calculating quality metrics and deltas
5. Saving results to data/processed/refactoring_results.json

It handles syntax errors in LLM output by marking them as "Refactoring Failed"
and logs total execution time to satisfy SC-003 efficiency requirements.
"""

import json
import logging
import sys
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

from config import Config, get_secret
from utils.logging import get_logger, LLMRefactoringError
from models.entities import FunctionSample, MetricDelta
from llm.refactoring import refactor_batch
from llm.baseline import generate_identity_baseline
from llm.quality import calculate_metrics, compute_deltas

logger = get_logger(__name__)


def load_processed_data(input_path: Path) -> List[Dict[str, Any]]:
    """
    Load the processed raw metrics from US1.

    Args:
        input_path: Path to data/processed/raw_metrics.json

    Returns:
        List of function samples with structural metrics.

    Raises:
        FileNotFoundError: If input file does not exist.
        json.JSONDecodeError: If file is not valid JSON.
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    logger.info(f"Loading processed data from {input_path}")
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError(f"Expected list of samples, got {type(data)}")

    logger.info(f"Loaded {len(data)} function samples")
    return data


def process_refactoring_batch(
    samples: List[Dict[str, Any]],
    batch_size: int = 10
) -> List[Dict[str, Any]]:
    """
    Process a batch of function samples through the refactoring pipeline.

    For each sample:
    1. Generate identity baseline
    2. Attempt LLM refactoring (handles syntax errors)
    3. Calculate quality metrics for original, refactored, and baseline
    4. Compute deltas

    Args:
        samples: List of function samples from US1.
        batch_size: Maximum number of samples to process in one batch.

    Returns:
        List of results with refactored code, baselines, and deltas.
    """
    results = []
    total_samples = len(samples)
    processed = 0

    logger.info(f"Starting refactoring pipeline for {total_samples} samples")

    for i, sample in enumerate(samples):
        processed += 1
        function_code = sample.get('code', '')
        function_hash = sample.get('hash', '')
        
        if not function_code:
            logger.warning(f"Skipping sample {i} with empty code (hash: {function_hash})")
            results.append({
                'hash': function_hash,
                'status': 'Skipped',
                'reason': 'Empty code',
                'original_metrics': None,
                'refactored_metrics': None,
                'baseline_metrics': None,
                'deltas': None
            })
            continue

        try:
            # Step 1: Generate identity baseline
            logger.debug(f"Generating baseline for hash {function_hash}")
            baseline_code = generate_identity_baseline([{'code': function_code}])[0]['code']
            
            # Validate baseline is identical (log warning if not, per T021)
            if baseline_code != function_code:
                logger.warning(f"Baseline mismatch for hash {function_hash}: delta detected")

            # Step 2: Attempt refactoring
            logger.debug(f"Refactoring function {i+1}/{total_samples} (hash: {function_hash})")
            refactored_code = None
            refactoring_status = "Success"
            
            try:
                # refactor_batch expects list of dicts with 'code' key
                batch_input = [{'code': function_code, 'hash': function_hash}]
                refactored_results = refactor_batch(batch_input)
                
                if refactored_results and len(refactored_results) > 0:
                    refactored_code = refactored_results[0].get('refactored_code')
                    if not refactored_code:
                        refactoring_status = "Refactoring Failed"
                        logger.warning(f"LLM returned empty refactored code for {function_hash}")
                else:
                    refactoring_status = "Refactoring Failed"
                    logger.warning(f"Refactoring returned no results for {function_hash}")
                    
            except SyntaxError as e:
                refactoring_status = "Refactoring Failed"
                logger.error(f"Syntax error in LLM output for {function_hash}: {e}")
            except Exception as e:
                refactoring_status = "Refactoring Failed"
                logger.error(f"Refactoring error for {function_hash}: {e}")

            # Step 3: Calculate metrics
            # Original metrics
            original_metrics = calculate_metrics(function_code)
            
            # Baseline metrics
            baseline_metrics = calculate_metrics(baseline_code)
            
            # Refactored metrics (if successful)
            refactored_metrics = None
            if refactored_code and refactoring_status == "Success":
                try:
                    refactored_metrics = calculate_metrics(refactored_code)
                except Exception as e:
                    logger.error(f"Error calculating metrics for refactored code {function_hash}: {e}")
                    refactoring_status = "Refactoring Failed"
                    refactored_metrics = None
            else:
                refactored_metrics = None

            # Step 4: Compute deltas
            deltas = None
            if original_metrics and baseline_metrics:
                deltas = compute_deltas(original_metrics, baseline_metrics, refactored_metrics)
            else:
                logger.warning(f"Cannot compute deltas for {function_hash} due to missing metrics")

            result = {
                'hash': function_hash,
                'original_code': function_code,
                'baseline_code': baseline_code,
                'refactored_code': refactored_code,
                'status': refactoring_status,
                'original_metrics': original_metrics,
                'baseline_metrics': baseline_metrics,
                'refactored_metrics': refactored_metrics,
                'deltas': deltas
            }
            results.append(result)

        except Exception as e:
            logger.exception(f"Unexpected error processing sample {i} (hash: {function_hash}): {e}")
            results.append({
                'hash': function_hash,
                'status': 'Error',
                'reason': str(e),
                'original_metrics': None,
                'refactored_metrics': None,
                'baseline_metrics': None,
                'deltas': None
            })

        # Progress logging
        if processed % 10 == 0 or processed == total_samples:
            logger.info(f"Progress: {processed}/{total_samples} samples processed")

    return results


def save_results(results: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Save the refactoring results to JSON.

    Args:
        results: List of processing results.
        output_path: Path to save the JSON file.
    """
    if not output_path.parent.exists():
        output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Saving results to {output_path}")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, default=str)

    logger.info(f"Saved {len(results)} results to {output_path}")


def main() -> int:
    """
    Main entry point for the refactoring pipeline.

    Returns:
        0 on success, 1 on failure.
    """
    start_time = time.time()
    
    # Configuration
    config = Config()
    input_path = Path(config.DATA_DIR) / "processed" / "raw_metrics.json"
    output_path = Path(config.DATA_DIR) / "processed" / "refactoring_results.json"
    
    logger.info("Starting LLM Refactoring Pipeline (T022)")
    logger.info(f"Input: {input_path}")
    logger.info(f"Output: {output_path}")

    try:
        # Step 1: Load data
        samples = load_processed_data(input_path)
        
        if not samples:
            logger.error("No samples found in input file. Halting.")
            return 1

        # Step 2: Process refactoring batch
        results = process_refactoring_batch(samples, batch_size=config.BATCH_SIZE)

        # Step 3: Save results
        save_results(results, output_path)

        # Efficiency metrics
        elapsed_time = time.time() - start_time
        success_count = sum(1 for r in results if r.get('status') == 'Success')
        failed_count = sum(1 for r in results if r.get('status') in ['Refactoring Failed', 'Error', 'Skipped'])

        logger.info("=" * 50)
        logger.info("Pipeline Execution Summary")
        logger.info(f"Total samples: {len(results)}")
        logger.info(f"Successful refactoring: {success_count}")
        logger.info(f"Failed/Skipped: {failed_count}")
        logger.info(f"Total execution time: {elapsed_time:.2f} seconds")
        logger.info(f"Average time per sample: {elapsed_time / len(results):.2f} seconds")
        logger.info("=" * 50)

        return 0

    except FileNotFoundError as e:
        logger.error(f"Input file not found: {e}")
        return 1
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in input file: {e}")
        return 1
    except Exception as e:
        logger.exception(f"Pipeline failed with unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())