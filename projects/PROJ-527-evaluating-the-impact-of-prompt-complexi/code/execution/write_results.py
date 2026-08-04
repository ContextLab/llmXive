"""
Execution Results Writer Module (T030)

Implements the writing of execution results to data/results/execution_outcomes.csv
with pass/fail counts, exception types, and static analysis scores.

This module integrates execution outcomes from runner.py with static analysis
metrics from static_analysis.py to produce a comprehensive results CSV.
"""

import os
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

import pandas as pd

from config import Paths
from execution.runner import run_batch_execution, execute_sample, ExecutionError, ExecutionTimeoutError
from execution.static_analysis import analyze_generated_code
from data.storage import load_variants_from_parquet
from utils.logger import get_logger

logger = get_logger(__name__)


def load_execution_results_from_parquet() -> pd.DataFrame:
    """
    Load generated prompt variants and code samples from the parquet file.

    Returns:
        DataFrame containing all prompt variants with generated code metadata.
    """
    variants_path = Paths.PROCESSED_DIR / "prompt_variants.parquet"
    if not variants_path.exists():
        logger.error(f"Parquet file not found: {variants_path}")
        raise FileNotFoundError(f"Prompt variants file not found: {variants_path}")

    logger.info(f"Loading prompt variants from {variants_path}")
    df = pd.read_parquet(variants_path)
    logger.info(f"Loaded {len(df)} prompt variants")
    return df


def run_execution_and_analysis(
    df: pd.DataFrame,
    timeout_seconds: int = 30,
    sample_limit: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Execute code samples and run static analysis on each.

    Args:
        df: DataFrame containing prompt variants with generated code.
        timeout_seconds: Timeout for code execution in seconds.
        sample_limit: Optional limit on number of samples to process.

    Returns:
        List of dictionaries containing execution results and analysis scores.
    """
    results = []

    # Apply sample limit if specified
    if sample_limit is not None and sample_limit < len(df):
        logger.info(f"Limiting execution to {sample_limit} samples")
        df = df.head(sample_limit)

    total = len(df)
    logger.info(f"Starting execution and analysis for {total} samples")

    for idx, row in df.iterrows():
        problem_id = row['problem_id']
        complexity_label = row['complexity_label']
        generated_code = row['generated_code']
        variant_id = row.get('variant_id', f"{problem_id}_{complexity_label}")

        logger.debug(f"Processing {variant_id} ({idx+1}/{total})")

        result_entry = {
            'variant_id': variant_id,
            'problem_id': problem_id,
            'complexity_label': complexity_label,
            'timestamp': datetime.now().isoformat(),
            'execution_status': None,
            'pass_count': 0,
            'fail_count': 0,
            'timeout_count': 0,
            'exception_type': None,
            'exception_message': None,
            'cyclomatic_complexity': None,
            'lines_of_code': None,
            'indentation_consistency': None,
            'security_vulnerabilities': None,
            'ruff_warnings': None
        }

        try:
            # Execute the generated code
            exec_result = execute_sample(
                generated_code=generated_code,
                test_code=row.get('test_code', ''),
                timeout_seconds=timeout_seconds
            )

            result_entry['execution_status'] = exec_result['status']
            result_entry['pass_count'] = exec_result['pass_count']
            result_entry['fail_count'] = exec_result['fail_count']
            result_entry['timeout_count'] = exec_result['timeout_count']

            if exec_result['status'] == 'error':
                result_entry['exception_type'] = exec_result.get('exception_type', 'Unknown')
                result_entry['exception_message'] = exec_result.get('exception_message', '')

        except ExecutionTimeoutError as e:
            result_entry['execution_status'] = 'timeout'
            result_entry['timeout_count'] = 1
            result_entry['exception_type'] = 'TimeoutError'
            result_entry['exception_message'] = str(e)
            logger.warning(f"Timeout for {variant_id}: {e}")

        except ExecutionError as e:
            result_entry['execution_status'] = 'error'
            result_entry['exception_type'] = e.exception_type
            result_entry['exception_message'] = str(e)
            logger.warning(f"Execution error for {variant_id}: {e}")

        except Exception as e:
            result_entry['execution_status'] = 'error'
            result_entry['exception_type'] = type(e).__name__
            result_entry['exception_message'] = str(e)
            logger.error(f"Unexpected error for {variant_id}: {e}", exc_info=True)

        # Run static analysis on the generated code
        try:
            analysis_result = analyze_generated_code(generated_code)

            result_entry['cyclomatic_complexity'] = analysis_result.get('cyclomatic_complexity')
            result_entry['lines_of_code'] = analysis_result.get('lines_of_code')
            result_entry['indentation_consistency'] = analysis_result.get('indentation_consistency')
            result_entry['security_vulnerabilities'] = analysis_result.get('security_vulnerabilities', [])
            result_entry['ruff_warnings'] = analysis_result.get('ruff_warnings', [])

        except Exception as e:
            logger.warning(f"Static analysis failed for {variant_id}: {e}")
            result_entry['cyclomatic_complexity'] = None
            result_entry['lines_of_code'] = None
            result_entry['indentation_consistency'] = None
            result_entry['security_vulnerabilities'] = []
            result_entry['ruff_warnings'] = []

        results.append(result_entry)

        # Log progress every 10 samples
        if (idx + 1) % 10 == 0:
            logger.info(f"Processed {idx+1}/{total} samples")

    return results


def write_results_to_csv(results: List[Dict[str, Any]], output_path: Optional[Path] = None) -> Path:
    """
    Write execution results to a CSV file.

    Args:
        results: List of result dictionaries from run_execution_and_analysis.
        output_path: Optional custom output path. Defaults to data/results/execution_outcomes.csv.

    Returns:
        Path to the written CSV file.
    """
    if output_path is None:
        output_path = Paths.RESULTS_DIR / "execution_outcomes.csv"

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Writing {len(results)} results to {output_path}")

    # Define column order for consistent output
    columns = [
        'variant_id',
        'problem_id',
        'complexity_label',
        'timestamp',
        'execution_status',
        'pass_count',
        'fail_count',
        'timeout_count',
        'exception_type',
        'exception_message',
        'cyclomatic_complexity',
        'lines_of_code',
        'indentation_consistency',
        'security_vulnerabilities',
        'ruff_warnings'
    ]

    # Flatten list fields for CSV compatibility
    flattened_results = []
    for result in results:
        flat_result = result.copy()
        # Convert lists to semicolon-separated strings for CSV
        if isinstance(flat_result.get('security_vulnerabilities'), list):
            flat_result['security_vulnerabilities'] = ';'.join(flat_result['security_vulnerabilities'])
        if isinstance(flat_result.get('ruff_warnings'), list):
            flat_result['ruff_warnings'] = ';'.join(map(str, flat_result['ruff_warnings']))
        flattened_results.append(flat_result)

    # Write to CSV
    with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=columns, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(flattened_results)

    logger.info(f"Successfully wrote {len(flattened_results)} rows to {output_path}")
    return output_path


def main():
    """
    Main entry point for execution results writer.

    This function orchestrates the full pipeline:
    1. Load prompt variants from parquet
    2. Execute code samples and run static analysis
    3. Write results to CSV
    """
    logger.info("Starting execution results writer (T030)")

    try:
        # Load data
        df = load_execution_results_from_parquet()

        # Run execution and analysis
        results = run_execution_and_analysis(
            df=df,
            timeout_seconds=30,
            sample_limit=None  # Process all samples
        )

        # Write results
        output_path = write_results_to_csv(results)

        # Summary statistics
        total = len(results)
        passed = sum(1 for r in results if r['execution_status'] == 'success' and r['pass_count'] > 0)
        failed = sum(1 for r in results if r['execution_status'] in ['error', 'timeout'])

        logger.info(f"Execution complete: {total} total, {passed} passed, {failed} failed")
        logger.info(f"Results written to: {output_path}")

        return output_path

    except Exception as e:
        logger.error(f"Execution results writer failed: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()