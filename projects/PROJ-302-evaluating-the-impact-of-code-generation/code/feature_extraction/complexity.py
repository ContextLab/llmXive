import os
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd

try:
    from radon.complexity import cc_visit
    from radon.raw import analyze
except ImportError:
    raise ImportError(
        "radon is required for complexity analysis. "
        "Please install it via: pip install radon"
    )

logger = logging.getLogger(__name__)

def calculate_snippet_complexity(code_block: str) -> Dict[str, Any]:
    """
    Calculate cyclomatic complexity and raw metrics for a code block.
    
    Handles radon failures gracefully by logging a warning and returning
    a dictionary with None values for the failed metrics.
    
    Args:
        code_block: The source code string to analyze.
        
    Returns:
        Dictionary containing:
            - cyclomatic_complexity: Sum of CC for all functions/classes
            - raw_metrics: Dict with 'loc', 'logical_lines', 'comments', etc.
            - error: None if successful, error message string if radon failed
    """
    if not code_block or not code_block.strip():
        return {
            "cyclomatic_complexity": None,
            "raw_metrics": {
                "loc": 0,
                "logical_lines": 0,
                "comments": 0,
                "blank": 0,
                "multi": 0
            },
            "error": "Empty code block provided"
        }

    try:
        # Analyze cyclomatic complexity
        cc_results = cc_visit(code_block)
        total_cc = sum(block.cc for block in cc_results) if cc_results else 0
        
        # Analyze raw metrics
        raw_analysis = analyze(code_block)
        
        return {
            "cyclomatic_complexity": total_cc,
            "raw_metrics": {
                "loc": raw_analysis.loc,
                "logical_lines": raw_analysis.logical_lines,
                "comments": raw_analysis.comments,
                "blank": raw_analysis.blank,
                "multi": raw_analysis.multi
            },
            "error": None
        }
    except Exception as e:
        # Log the failure as a warning and return None metrics
        logger.warning(
            f"radon analysis failed for code snippet: {str(e)[:200]}... "
            "Skipping complexity metrics for this snippet."
        )
        return {
            "cyclomatic_complexity": None,
            "raw_metrics": {
                "loc": None,
                "logical_lines": None,
                "comments": None,
                "blank": None,
                "multi": None
            },
            "error": str(e)
        }

def process_dataset(
    input_path: str,
    output_path: str,
    code_column: str = "code",
    id_column: str = "snippet_id"
) -> None:
    """
    Process a dataset of code snippets, calculating complexity metrics.
    
    Skips rows where radon fails, logs warnings, and excludes those rows
    from the final output dataset.
    
    Args:
        input_path: Path to input parquet/CSV file containing code snippets.
        output_path: Path to write the processed parquet file.
        code_column: Name of the column containing the code string.
        id_column: Name of the column containing the unique identifier.
    """
    input_file = Path(input_path)
    output_file = Path(output_path)
    
    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    # Determine file format and load
    if input_file.suffix == '.csv':
        df = pd.read_csv(input_path)
    elif input_file.suffix == '.parquet':
        df = pd.read_parquet(input_path)
    else:
        raise ValueError(f"Unsupported file format: {input_file.suffix}")
    
    if code_column not in df.columns:
        raise ValueError(f"Code column '{code_column}' not found in dataset.")
    
    results = []
    skipped_count = 0
    total_count = len(df)
    
    for idx, row in df.iterrows():
        snippet_id = row.get(id_column, f"unknown_{idx}")
        code = str(row[code_column]) if pd.notna(row[code_column]) else ""
        
        metrics = calculate_snippet_complexity(code)
        
        if metrics["error"] is not None:
            # Skip this row as per requirements
            logger.warning(
                f"Skipping snippet {snippet_id} due to radon failure: "
                f"{metrics['error']}"
            )
            skipped_count += 1
            continue
        
        # Flatten metrics for the result row
        result_row = {id_column: snippet_id}
        result_row["cyclomatic_complexity"] = metrics["cyclomatic_complexity"]
        
        for metric_name, metric_value in metrics["raw_metrics"].items():
            result_row[f"raw_{metric_name}"] = metric_value
        
        results.append(result_row)
    
    if not results:
        logger.warning("No valid complexity metrics could be calculated. "
                     "Output file will be empty.")
        # Create an empty dataframe with expected schema
        result_df = pd.DataFrame(columns=[
            id_column, "cyclomatic_complexity",
            "raw_loc", "raw_logical_lines", "raw_comments",
            "raw_blank", "raw_multi"
        ])
    else:
        result_df = pd.DataFrame(results)
    
    # Ensure output directory exists
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Write output
    if output_file.suffix == '.csv':
        result_df.to_csv(output_path, index=False)
    else:
        result_df.to_parquet(output_path, index=False)
    
    logger.info(
        f"Complexity extraction complete. "
        f"Processed: {total_count}, "
        f"Success: {len(results)}, "
        f"Skipped (radon failure): {skipped_count}"
    )

def main():
    """Entry point for running complexity extraction from command line."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Extract code complexity metrics from a dataset."
    )
    parser.add_argument(
        "--input", "-i",
        required=True,
        help="Path to input dataset (parquet or csv)"
    )
    parser.add_argument(
        "--output", "-o",
        required=True,
        help="Path to output dataset"
    )
    parser.add_argument(
        "--code-column", "-c",
        default="code",
        help="Name of the column containing code (default: code)"
    )
    parser.add_argument(
        "--id-column", "-id",
        default="snippet_id",
        help="Name of the column containing snippet ID (default: snippet_id)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.basicConfig(
            level=logging.DEBUG,
            format="%(asctime)s - %(levelname)s - %(message)s"
        )
    else:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s"
        )
    
    process_dataset(
        input_path=args.input,
        output_path=args.output,
        code_column=args.code_column,
        id_column=args.id_column
    )

if __name__ == "__main__":
    main()