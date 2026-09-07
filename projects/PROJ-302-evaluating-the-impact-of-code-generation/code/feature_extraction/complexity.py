import os
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import pandas as pd
from radon.complexity import cc_visit
from radon.raw import analyze as raw_analyze

# Ensure project root is in path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from utils.config import get_config, ensure_directories
from utils.models import CodeSnippet

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def calculate_snippet_complexity(snippet: CodeSnippet) -> Dict[str, Any]:
    """
    Calculate cyclomatic complexity and raw metrics for a single code snippet.
    
    Args:
        snippet: A CodeSnippet object containing the source code.
        
    Returns:
        A dictionary containing:
            - 'cyclomatic_complexity': int (sum of complexities)
            - 'lines_of_code': int
            - 'blank_lines': int
            - 'comments': int
            - 'statements': int
            - 'error': str (if radon fails, otherwise None)
    """
    code_content = snippet.code_content
    
    result = {
        'cyclomatic_complexity': 0,
        'lines_of_code': 0,
        'blank_lines': 0,
        'comments': 0,
        'statements': 0,
        'error': None
    }

    if not code_content or not isinstance(code_content, str):
        result['error'] = "Invalid or empty code content"
        logger.warning(f"Skipping snippet {snippet.snippet_id} due to invalid content: {result['error']}")
        return result

    try:
        # Calculate Cyclomatic Complexity
        # cc_visit returns a list of complexity results for each function/class
        complexity_results = cc_visit(code_content)
        total_cc = sum(block.complexity for block in complexity_results)
        result['cyclomatic_complexity'] = total_cc

        # Calculate Raw Metrics
        raw_metrics = raw_analyze(code_content)
        result['lines_of_code'] = raw_metrics.loc
        result['blank_lines'] = raw_metrics.blank
        result['comments'] = raw_metrics.comments
        result['statements'] = raw_metrics.stmt

    except Exception as e:
        # ERROR HANDLING: Catch radon failures, log warning, and exclude from dataset
        error_msg = str(e)
        result['error'] = f"Radon analysis failed: {error_msg}"
        logger.warning(
            f"Skipping snippet {snippet.snippet_id} due to radon failure: {error_msg}. "
            f"This snippet will be excluded from the final dataset."
        )
        # We return the result with error flag set, but 0 for metrics.
        # The caller (process_dataset) should filter out rows where 'error' is not None.
    
    return result

def process_dataset(input_path: str, output_path: str) -> Tuple[int, int]:
    """
    Process a dataset of code snippets, calculating complexity metrics.
    Handles radon failures by logging warnings and excluding invalid rows.
    
    Args:
        input_path: Path to input parquet file containing CodeSnippet data.
        output_path: Path to output parquet file for processed metrics.
        
    Returns:
        A tuple (processed_count, excluded_count)
    """
    config = get_config()
    ensure_directories()
    
    input_file = Path(input_path)
    output_file = Path(output_path)
    
    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_file}")
    
    logger.info(f"Loading dataset from {input_file}")
    df = pd.read_parquet(input_file)
    
    processed_rows = []
    excluded_count = 0
    
    logger.info(f"Processing {len(df)} snippets...")
    
    for idx, row in df.iterrows():
        # Reconstruct CodeSnippet object or use raw data directly
        # Assuming the parquet contains columns matching CodeSnippet fields
        try:
            snippet = CodeSnippet(
                snippet_id=row.get('snippet_id'),
                source_commit=row.get('source_commit'),
                generation_source=row.get('generation_source'),
                code_content=row.get('code_content'), # Assuming this column exists
                complexity_metrics=None,
                semantic_similarity_score=row.get('semantic_similarity_score')
            )
        except Exception as e:
            logger.warning(f"Skipping row {idx} due to reconstruction error: {e}")
            excluded_count += 1
            continue

        metrics = calculate_snippet_complexity(snippet)
        
        if metrics['error']:
            excluded_count += 1
            continue
        
        # Add metrics to the row
        row_dict = row.to_dict() if hasattr(row, 'to_dict') else dict(row)
        row_dict.update({
            'cyclomatic_complexity': metrics['cyclomatic_complexity'],
            'lines_of_code': metrics['lines_of_code'],
            'blank_lines': metrics['blank_lines'],
            'comments': metrics['comments'],
            'statements': metrics['statements']
        })
        processed_rows.append(row_dict)
    
    if not processed_rows:
        logger.error("No valid rows processed. All snippets were excluded.")
        # Create empty output with correct schema if needed, or just exit
        pd.DataFrame().to_parquet(output_file)
        return 0, excluded_count
        
    result_df = pd.DataFrame(processed_rows)
    
    logger.info(f"Writing {len(result_df)} processed snippets to {output_file}")
    result_df.to_parquet(output_file, index=False)
    
    logger.info(f"Processing complete. Included: {len(result_df)}, Excluded: {excluded_count}")
    return len(result_df), excluded_count

def main():
    """Main entry point for running the complexity extraction pipeline."""
    config = get_config()
    
    # Default paths can be overridden by config or CLI args
    input_path = config.get('paths', {}).get('classified_snippets', 'data/processed/classified_snippets.parquet')
    output_path = config.get('paths', {}).get('complexity_metrics', 'data/processed/complexity_metrics.parquet')
    
    # Ensure output directory exists
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        processed, excluded = process_dataset(input_path, output_path)
        print(f"Successfully processed {processed} snippets. Excluded {excluded} due to errors.")
    except Exception as e:
        logger.critical(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()