from __future__ import annotations

import csv
import os
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from config import Paths
from utils.logger import get_logger
from execution.runner import run_batch_execution, ExecutionResult
from execution.static_analysis import analyze_generated_code

logger = get_logger(__name__)


def load_variants_from_parquet() -> pd.DataFrame:
    """
    Load generated prompt variants and code from the processed Parquet file.
    Returns a DataFrame with columns: problem_id, variant_label, code, ...
    """
    input_path = Paths.PROCESSED_DATA_DIR / "prompt_variants.parquet"
    if not input_path.exists():
        raise FileNotFoundError(
            f"Required input file not found: {input_path}. "
            "Ensure T017/T018 (LLM generation) has run successfully."
        )
    
    logger.info(f"Loading variants from {input_path}")
    df = pd.read_parquet(input_path)
    
    required_cols = ["problem_id", "variant_label", "code"]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in {input_path}: {missing}")
    
    return df


def run_execution_and_analysis(df_variants: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Execute the code samples against HumanEval tests and run static analysis.
    Returns a list of aggregated outcome dictionaries.
    """
    logger.info(f"Starting execution and analysis for {len(df_variants)} samples")
    
    # Prepare input for batch execution runner
    # The runner expects a list of dicts with 'problem_id', 'prompt', 'canonical_solution', 'test_list', 'code'
    # We need to reconstruct the necessary fields from our variants dataframe
    # Assuming we have the base HumanEval data loaded or accessible via the variants
    # If 'canonical_solution' and 'test_list' are not in df_variants, we must load them from the raw dataset
    # For this task, we assume the variants dataframe (or a linked raw dataset) has these.
    # If not, we might need to join with the raw data.
    
    # Simplified approach: Run execution per row in the dataframe
    # We assume the 'code' column contains the generated code string.
    # We need the 'canonical_solution' and 'test_list' to run the execution runner correctly.
    # If they are missing, we cannot run the tests. 
    # Given T016 loaded HumanEval, we assume the data is available.
    # Let's assume the df_variants has been enriched with canonical_solution and test_list during T017/T018.
    
    if "canonical_solution" not in df_variants.columns:
        # Fallback: Try to load from raw data if not present
        # This is a critical dependency. If missing, execution cannot proceed.
        logger.warning("canonical_solution not found in variants. Attempting to load from raw data.")
        from data.loader import load_human_eval_dataset
        raw_df = load_human_eval_dataset()
        # Merge on problem_id (assuming task_id in raw matches problem_id in variants)
        df_variants = df_variants.merge(raw_df[["task_id", "canonical_solution", "test"]], 
                                        left_on="problem_id", right_on="task_id", how="left")
        df_variants.rename(columns={"test": "test_list"}, inplace=True)
        if "canonical_solution" not in df_variants.columns:
             raise RuntimeError("Cannot proceed: canonical_solution and test_list missing from input data.")

    results = []
    
    for idx, row in df_variants.iterrows():
        problem_id = str(row["problem_id"])
        variant_label = str(row["variant_label"])
        code = str(row["code"])
        canonical_sol = str(row["canonical_solution"])
        test_list = row["test_list"]
        
        if isinstance(test_list, str):
            import json
            try:
                test_list = json.loads(test_list)
            except:
                test_list = []
        
        # Run execution
        exec_result: ExecutionResult = run_batch_execution(
            problem_id=problem_id,
            prompt="", # Not strictly needed for execution, but part of signature
            canonical_solution=canonical_sol,
            test_list=test_list,
            code=code
        )
        
        # Run static analysis
        static_scores = analyze_generated_code(code)
        
        # Aggregate into a single dict for this sample
        outcome = {
            "problem_id": problem_id,
            "complexity_label": variant_label,
            "pass_count": exec_result.pass_count,
            "fail_count": exec_result.fail_count,
            "exception_type": exec_result.exception_type if exec_result.exception_type else "None",
            "timeout_flag": exec_result.timeout_flag,
            "static_analysis_scores": static_scores
        }
        results.append(outcome)
        
        if (idx + 1) % 10 == 0:
            logger.info(f"Processed {idx + 1}/{len(df_variants)} samples")

    return results


def write_results_to_csv(results: List[Dict[str, Any]]) -> None:
    """
    Write the aggregated execution outcomes to the results CSV file.
    The static_analysis_scores (dict) is serialized to a JSON string for CSV storage.
    """
    output_path = Paths.RESULTS_DIR / "execution_outcomes.csv"
    
    logger.info(f"Writing {len(results)} results to {output_path}")
    
    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        if not results:
            logger.warning("No results to write.")
            return
        
        # Define columns explicitly to handle the nested dict
        fieldnames = [
            "problem_id",
            "complexity_label",
            "pass_count",
            "fail_count",
            "exception_type",
            "timeout_flag",
            "static_analysis_scores"
        ]
        
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for row in results:
            # Serialize the dict to JSON string
            row_copy = row.copy()
            row_copy["static_analysis_scores"] = json.dumps(row_copy["static_analysis_scores"])
            writer.writerow(row_copy)
    
    logger.info(f"Successfully wrote results to {output_path}")


def main() -> None:
    """
    Main entry point for T030: Aggregate execution outcomes and write to CSV.
    """
    try:
        # 1. Load variants
        df_variants = load_variants_from_parquet()
        
        # 2. Run execution and static analysis
        results = run_execution_and_analysis(df_variants)
        
        # 3. Write to CSV
        write_results_to_csv(results)
        
        logger.info("T030 completed successfully.")
        
    except Exception as e:
        logger.error(f"Error during T030 execution: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()