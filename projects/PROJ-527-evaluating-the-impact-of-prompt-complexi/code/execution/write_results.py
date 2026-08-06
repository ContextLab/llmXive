"""
Write execution results to CSV.

This script loads generated prompt variants, executes them against HumanEval unit tests,
performs static analysis, and writes the aggregated results to data/results/execution_outcomes.csv.
"""

import os
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

import pandas as pd

from config import Paths
from utils.logger import get_logger
from execution.runner import run_batch_execution, ExecutionError, ExecutionTimeoutError
from execution.static_analysis import analyze_generated_code
from prompts.generator import generate_prompt_variants
from data.fetcher import load_human_eval
from data.storage import save_variants_to_parquet, load_variants_from_parquet

logger = get_logger(__name__)


def load_execution_results_from_parquet() -> pd.DataFrame:
    """
    Load generated prompt variants from parquet file.

    Returns:
        DataFrame with columns: problem_id, prompt, complexity_label, code, etc.
    """
    parquet_path = Paths.PROCESSED_DATA / "prompt_variants.parquet"

    if not parquet_path.exists():
        logger.warning(f"Parquet file not found at {parquet_path}. Generating variants first.")
        # If parquet doesn't exist, we need to generate it first
        # This should normally be done by a separate pipeline step
        raise FileNotFoundError(
            f"Prompt variants parquet file not found at {parquet_path}. "
            "Please run the prompt generation pipeline first."
        )

    df = pd.read_parquet(parquet_path)
    logger.info(f"Loaded {len(df)} prompt variants from {parquet_path}")
    return df


def run_execution_and_analysis(df: pd.DataFrame, sample_size: Optional[int] = None) -> pd.DataFrame:
    """
    Execute generated code and perform static analysis.

    Args:
        df: DataFrame with prompt variants and generated code
        sample_size: Optional limit on number of samples to process

    Returns:
        DataFrame with execution results and static analysis scores
    """
    if sample_size:
        df = df.head(sample_size)
        logger.info(f"Processing sample of {sample_size} variants")

    results = []

    # Group by problem_id to ensure we process all variants for each problem
    grouped = df.groupby('problem_id')

    for problem_id, group in grouped:
        logger.info(f"Processing problem {problem_id} with {len(group)} variants")

        # Load the original HumanEval problem for test execution
        human_eval_data = load_human_eval()
        original_problem = human_eval_data.get(problem_id)

        if not original_problem:
            logger.warning(f"Could not find original problem {problem_id} in HumanEval dataset")
            continue

        test_code = original_problem.get('test', '')

        for _, row in group.iterrows():
            generated_code = row.get('code', '')
            complexity_label = row.get('complexity_label', 'unknown')

            if not generated_code:
                logger.warning(f"No generated code for {problem_id} variant {complexity_label}")
                continue

            # Run execution
            try:
                execution_result = run_batch_execution(
                    code=generated_code,
                    test_code=test_code,
                    timeout_per_test=10
                )

                pass_count = execution_result.get('pass_count', 0)
                fail_count = execution_result.get('fail_count', 0)
                exception_type = execution_result.get('exception_type', None)
                timeout_flag = execution_result.get('timeout_flag', False)

            except ExecutionTimeoutError:
                pass_count = 0
                fail_count = len(original_problem.get('tests', []))
                exception_type = 'TimeoutError'
                timeout_flag = True
            except ExecutionError as e:
                pass_count = 0
                fail_count = len(original_problem.get('tests', []))
                exception_type = str(type(e).__name__)
                timeout_flag = False
            except Exception as e:
                pass_count = 0
                fail_count = len(original_problem.get('tests', []))
                exception_type = str(type(e).__name__)
                timeout_flag = False

            # Run static analysis
            try:
                static_scores = analyze_generated_code(generated_code)
            except Exception as e:
                logger.warning(f"Static analysis failed for {problem_id}: {e}")
                static_scores = {
                    'cyclomatic_complexity': None,
                    'lines_of_code': None,
                    'indentation_consistent': None,
                    'security_vulnerable': None
                }

            result_row = {
                'problem_id': problem_id,
                'complexity_label': complexity_label,
                'pass_count': pass_count,
                'fail_count': fail_count,
                'exception_type': exception_type,
                'timeout_flag': timeout_flag,
                'static_analysis_scores': str(static_scores),
                'timestamp': datetime.now().isoformat()
            }

            results.append(result_row)

    return pd.DataFrame(results)


def write_results_to_csv(results_df: pd.DataFrame, output_path: Optional[Path] = None):
    """
    Write execution results to CSV file.

    Args:
        results_df: DataFrame with execution results
        output_path: Optional output path (defaults to Paths.RESULTS / "execution_outcomes.csv")
    """
    if output_path is None:
        output_path = Paths.RESULTS / "execution_outcomes.csv"

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write to CSV
    results_df.to_csv(output_path, index=False)
    logger.info(f"Wrote {len(results_df)} execution results to {output_path}")

    # Verify file was created
    if output_path.exists():
        logger.info(f"Output file size: {output_path.stat().st_size} bytes")
    else:
        logger.error(f"Failed to create output file at {output_path}")


def main():
    """Main entry point for writing execution results."""
    logger.info("Starting execution results writer")

    try:
        # Load prompt variants
        df = load_execution_results_from_parquet()

        # Execute and analyze
        results_df = run_execution_and_analysis(df)

        # Write results to CSV
        write_results_to_csv(results_df)

        logger.info("Execution results writer completed successfully")

    except FileNotFoundError as e:
        logger.error(f"Required file not found: {e}")
        raise
    except Exception as e:
        logger.error(f"Error during execution results writing: {e}")
        raise


if __name__ == "__main__":
    main()