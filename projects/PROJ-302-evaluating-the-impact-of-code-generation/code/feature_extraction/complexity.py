import os
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import traceback

try:
    from radon.complexity import cc_visit
    from radon.raw import analyze as radon_raw_analyze
except ImportError:
    raise ImportError(
        "The 'radon' package is required for complexity analysis. "
        "Please install it via: pip install radon"
    )

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def calculate_snippet_complexity(snippet_code: str, snippet_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Calculate cyclomatic complexity and raw metrics for a code snippet.
    
    Args:
        snippet_code: The source code string to analyze.
        snippet_id: Optional identifier for logging purposes.
        
    Returns:
        Dictionary containing complexity metrics:
            - cyclomatic_complexity: Sum of cyclomatic complexities of all functions/classes
            - max_cc: Maximum cyclomatic complexity of any single block
            - loc: Lines of code
            - blanks: Blank lines
            - comments: Comment lines
            - success: Boolean indicating if analysis succeeded
            - error_message: Error string if analysis failed, None otherwise
    """
    result = {
        'cyclomatic_complexity': 0,
        'max_cc': 0,
        'loc': 0,
        'blanks': 0,
        'comments': 0,
        'success': False,
        'error_message': None
    }

    if not snippet_code or not snippet_code.strip():
        result['error_message'] = "Empty code snippet"
        return result

    try:
        # Calculate Cyclomatic Complexity
        complexity_results = cc_visit(snippet_code)
        if complexity_results:
            result['cyclomatic_complexity'] = sum(block.cc for block in complexity_results)
            result['max_cc'] = max(block.cc for block in complexity_results)
        else:
            # If no functions/classes found, basic complexity is 1 (the module itself)
            result['cyclomatic_complexity'] = 1
            result['max_cc'] = 1

        # Calculate Raw Metrics (LOC, blanks, comments)
        raw_metrics = radon_raw_analyze(snippet_code)
        result['loc'] = raw_metrics.loc
        result['blanks'] = raw_metrics.blank
        result['comments'] = raw_metrics.comments

        result['success'] = True

    except SyntaxError as e:
        msg = f"Syntax error in code snippet {snippet_id}: {str(e)}"
        logger.warning(msg)
        result['error_message'] = msg
        # Return partial metrics if possible, or defaults
        result['cyclomatic_complexity'] = -1
        result['max_cc'] = -1
        result['loc'] = len(snippet_code.splitlines())
        
    except Exception as e:
        msg = f"Unexpected error analyzing snippet {snippet_id}: {str(e)}"
        logger.error(msg)
        logger.debug(traceback.format_exc())
        result['error_message'] = msg
        result['cyclomatic_complexity'] = -1
        result['max_cc'] = -1
        result['loc'] = len(snippet_code.splitlines())

    return result

def process_dataset(input_path: str, output_path: str, id_column: str = 'snippet_id', code_column: str = 'code') -> Tuple[int, int]:
    """
    Process a dataset of code snippets, calculating complexity metrics for each.
    
    Handles radon failures gracefully:
    - Logs a warning for each failure.
    - Marks the row with error details.
    - Continues processing the rest of the dataset.
    
    Args:
        input_path: Path to input parquet/CSV file.
        output_path: Path to output parquet file.
        id_column: Name of the column containing snippet IDs.
        code_column: Name of the column containing source code.
        
    Returns:
        Tuple of (successful_count, failed_count)
    """
    logger.info(f"Starting complexity extraction for: {input_path}")
    
    # Determine file type and read
    input_p = Path(input_path)
    if input_p.suffix == '.parquet':
        df = pd.read_parquet(input_path)
    elif input_p.suffix == '.csv':
        df = pd.read_csv(input_path)
    else:
        raise ValueError(f"Unsupported file format: {input_p.suffix}")

    if code_column not in df.columns:
        raise ValueError(f"Input file missing required column: {code_column}")
    if id_column not in df.columns:
        raise ValueError(f"Input file missing required column: {id_column}")

    results = []
    success_count = 0
    fail_count = 0

    for idx, row in df.iterrows():
        snippet_id = row.get(id_column, f"row_{idx}")
        code = row.get(code_column, "")
        
        metrics = calculate_snippet_complexity(code, snippet_id)
        
        # Merge original row with metrics
        new_row = row.to_dict()
        new_row.update(metrics)
        results.append(new_row)
        
        if metrics['success']:
            success_count += 1
        else:
            fail_count += 1

    # Create output DataFrame
    output_df = pd.DataFrame(results)
    
    # Ensure output directory exists
    output_p = Path(output_path)
    output_p.parent.mkdir(parents=True, exist_ok=True)
    
    # Write output
    if output_p.suffix == '.parquet':
        output_df.to_parquet(output_path, index=False)
    elif output_p.suffix == '.csv':
        output_df.to_csv(output_path, index=False)
    else:
        # Default to parquet if extension is missing or unknown
        output_df.to_parquet(str(output_p.with_suffix('.parquet')), index=False)
        logger.info(f"Saved output as parquet: {output_p.with_suffix('.parquet')}")

    logger.info(f"Processing complete. Success: {success_count}, Failed: {fail_count}")
    return success_count, fail_count

def main():
    """Main entry point for running complexity extraction from command line."""
    import argparse

    parser = argparse.ArgumentParser(description="Extract complexity metrics from code snippets.")
    parser.add_argument("--input", type=str, required=True, help="Path to input dataset (parquet or csv)")
    parser.add_argument("--output", type=str, required=True, help="Path to output dataset (parquet or csv)")
    parser.add_argument("--id-col", type=str, default="snippet_id", help="Column name for snippet ID")
    parser.add_argument("--code-col", type=str, default="code", help="Column name for source code")
    
    args = parser.parse_args()

    try:
        success, failed = process_dataset(args.input, args.output, args.id_col, args.code_col)
        if failed > 0:
            logger.warning(f"Completed with {failed} failures. Check logs for details.")
            sys.exit(0) # Exit 0 as the task completed, even with skips
        sys.exit(0)
    except Exception as e:
        logger.critical(f"Fatal error in main: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()