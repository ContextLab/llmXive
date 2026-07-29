"""
Task T030: Write execution results to data/results/execution_outcomes.csv

This module aggregates execution outcomes from the runner and static analysis
and writes them to a CSV file in the results directory.
"""

import os
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

import pandas as pd

from config import Paths
from execution.runner import run_batch_execution, execute_sample
from execution.static_analysis import analyze_generated_code
from data.storage import load_variants_from_parquet
from utils.logger import get_logger

logger = get_logger(__name__)


def load_execution_results_from_parquet() -> pd.DataFrame:
    """
    Load generated code variants from the processed parquet file.
    Returns a DataFrame containing prompt variants and generated code.
    """
    variants_path = Paths.PROCESSED_DIR / "prompt_variants.parquet"
    if not variants_path.exists():
        raise FileNotFoundError(
            f"Required data file not found: {variants_path}. "
            "Please run the generation pipeline (T017/T018) first."
        )
    return load_variants_from_parquet()


def run_execution_and_analysis(df: pd.DataFrame) -> pd.DataFrame:
    """
    Run execution tests and static analysis on all variants.
    
    Args:
        df: DataFrame with generated code variants (from load_execution_results_from_parquet)
        
    Returns:
        DataFrame with added execution results and static analysis scores
    """
    logger.info(f"Processing {len(df)} variants for execution and analysis")
    
    results = []
    
    for idx, row in df.iterrows():
        problem_id = row.get('problem_id')
        variant_label = row.get('complexity_label')
        generated_code = row.get('generated_code')
        
        if not generated_code:
            logger.warning(f"Skipping row {idx}: No generated code found")
            continue
        
        # Execute code and capture results
        try:
            exec_result = execute_sample(generated_code, problem_id)
            pass_count = exec_result.get('pass_count', 0)
            total_tests = exec_result.get('total_tests', 0)
            status = exec_result.get('status', 'unknown')
            exception_type = exec_result.get('exception_type', None)
            timeout = exec_result.get('timeout', False)
        except Exception as e:
            logger.error(f"Execution failed for {problem_id}/{variant_label}: {e}")
            pass_count = 0
            total_tests = 0
            status = 'error'
            exception_type = type(e).__name__
            timeout = False
        
        # Run static analysis
        try:
            static_result = analyze_generated_code(generated_code)
            cyclomatic_complexity = static_result.get('cyclomatic_complexity', 0)
            lines_of_code = static_result.get('lines_of_code', 0)
            indentation_issues = static_result.get('indentation_issues', 0)
            security_issues = static_result.get('security_issues', 0)
        except Exception as e:
            logger.error(f"Static analysis failed for {problem_id}/{variant_label}: {e}")
            cyclomatic_complexity = 0
            lines_of_code = 0
            indentation_issues = 0
            security_issues = 0
        
        # Compile result row
        result_row = {
            'problem_id': problem_id,
            'complexity_label': variant_label,
            'pass_count': pass_count,
            'total_tests': total_tests,
            'pass_rate': pass_count / total_tests if total_tests > 0 else 0.0,
            'status': status,
            'exception_type': exception_type,
            'timeout': timeout,
            'cyclomatic_complexity': cyclomatic_complexity,
            'lines_of_code': lines_of_code,
            'indentation_issues': indentation_issues,
            'security_issues': security_issues,
            'timestamp': datetime.now().isoformat()
        }
        
        results.append(result_row)
    
    return pd.DataFrame(results)


def write_results_to_csv(results_df: pd.DataFrame, output_path: Optional[Path] = None) -> Path:
    """
    Write execution results to CSV file.
    
    Args:
        results_df: DataFrame with execution results
        output_path: Optional custom output path (defaults to Paths.RESULTS_DIR / 'execution_outcomes.csv')
        
    Returns:
        Path to the written CSV file
    """
    if output_path is None:
        output_path = Paths.RESULTS_DIR / "execution_outcomes.csv"
    
    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write to CSV
    results_df.to_csv(output_path, index=False)
    logger.info(f"Execution results written to {output_path}")
    
    return output_path


def main():
    """Main entry point for T030."""
    logger.info("Starting T030: Write execution results to CSV")
    
    try:
        # Load data
        logger.info("Loading generated variants from parquet...")
        df = load_execution_results_from_parquet()
        logger.info(f"Loaded {len(df)} variants")
        
        # Run execution and analysis
        logger.info("Running execution tests and static analysis...")
        results_df = run_execution_and_analysis(df)
        logger.info(f"Processed {len(results_df)} results")
        
        # Write results
        output_path = write_results_to_csv(results_df)
        
        # Log summary
        logger.info("Execution results summary:")
        logger.info(f"  Total samples: {len(results_df)}")
        logger.info(f"  Passed: {results_df['status'].value_counts().get('passed', 0)}")
        logger.info(f"  Failed: {results_df['status'].value_counts().get('failed', 0)}")
        logger.info(f"  Errors: {results_df['status'].value_counts().get('error', 0)}")
        logger.info(f"  Timeouts: {results_df['timeout'].sum()}")
        
        logger.info("T030 completed successfully")
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"Data file missing: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error during T030: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit(main())
