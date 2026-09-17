import os
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
from radon.complexity import cc_visit
from radon.raw import analyze as raw_analyze
import ast

# Ensure logging is configured to write to the specific file
def _setup_radon_logging():
    """Configure logging specifically for radon errors."""
    log_path = Path("logs")
    log_path.mkdir(exist_ok=True)
    log_file = log_path / "radon_errors.log"

    # Create a dedicated logger for radon errors if not exists
    logger = logging.getLogger("radon_errors")
    logger.setLevel(logging.WARNING)

    # Remove existing handlers to avoid duplicates if called multiple times
    logger.handlers = []

    # File handler for radon errors
    fh = logging.FileHandler(log_file)
    fh.setLevel(logging.WARNING)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    return logger

_radon_logger = _setup_radon_logging()

def calculate_snippet_complexity(snippet_code: str, file_path: str = "unknown") -> Dict[str, Any]:
    """
    Calculate complexity metrics for a given code snippet using radon.
    
    Args:
        snippet_code: The source code string to analyze.
        file_path: Identifier for the source file (for logging purposes).
        
    Returns:
        Dictionary containing complexity metrics:
            - cyclomatic_complexity: Maximum CC value in the snippet
            - avg_complexity: Average CC value
            - loc: Lines of code
            - blank: Blank lines
            - comments: Comment lines
            - statements: Number of statements
            
    Raises:
        Exception: If radon fails to parse the code (handled upstream).
    """
    try:
        # Parse AST to check validity first (optional but good practice)
        try:
            ast.parse(snippet_code)
        except SyntaxError as e:
            # Radon might handle this, but we log it if we catch it early
            # However, per task, we handle radon failure specifically.
            # If radon fails on this, it will be caught in the try/except below.
            pass

        # Raw analysis
        raw = raw_analyze(snippet_code)
        
        # Cyclomatic complexity analysis
        complexities = cc_visit(snippet_code)
        
        if not complexities:
            # If no functions/classes found, treat as a simple block with CC=1
            max_cc = 1
            avg_cc = 1.0
        else:
            cc_values = [c.complexity for c in complexities]
            max_cc = max(cc_values)
            avg_cc = sum(cc_values) / len(cc_values)
        
        return {
            "cyclomatic_complexity": max_cc,
            "avg_complexity": round(avg_cc, 2),
            "loc": raw.loc,
            "blank": raw.blank,
            "comments": raw.comments,
            "statements": raw.statements
        }
        
    except Exception as e:
        # LOG THE ERROR TO logs/radon_errors.log
        _radon_logger.warning(f"Radon failed for {file_path}: {e}")
        
        # Re-raise so the caller knows to drop the row
        raise

def process_dataset(input_path: str, output_path: str) -> pd.DataFrame:
    """
    Process a dataset of code snippets, calculating complexity for each.
    Rows where radon fails are dropped, and errors are logged.
    
    Args:
        input_path: Path to the input Parquet/CSV file containing snippets.
        output_path: Path to save the processed DataFrame.
        
    Returns:
        Processed DataFrame with complexity columns added.
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    # Load data
    if input_path.endswith('.parquet'):
        df = pd.read_parquet(input_path)
    elif input_path.endswith('.csv'):
        df = pd.read_csv(input_path)
    else:
        raise ValueError("Input file must be .parquet or .csv")
    
    required_cols = ['snippet_code', 'file_path']
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Input data missing required columns: {missing_cols}")
    
    results = []
    dropped_count = 0
    
    for idx, row in df.iterrows():
        try:
            code = row['snippet_code']
            f_path = row.get('file_path', f"row_{idx}")
            
            metrics = calculate_snippet_complexity(code, f_path)
            
            # Merge metrics into the row
            new_row = row.to_dict()
            new_row.update(metrics)
            results.append(new_row)
            
        except Exception:
            # Error already logged in calculate_snippet_complexity
            # Drop the row (do not append to results)
            dropped_count += 1
            continue
    
    if dropped_count > 0:
        logging.warning(f"Dropped {dropped_count} rows due to radon failures.")
    
    processed_df = pd.DataFrame(results)
    
    # Ensure output directory exists
    out_dir = Path(output_path).parent
    out_dir.mkdir(parents=True, exist_ok=True)
    
    if output_path.endswith('.parquet'):
        processed_df.to_parquet(output_path, index=False)
    elif output_path.endswith('.csv'):
        processed_df.to_csv(output_path, index=False)
    else:
        # Default to parquet
        processed_df.to_parquet(output_path, index=False)
        
    return processed_df

def main():
    """Entry point for running complexity extraction."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Default paths (can be overridden by args in a real CLI)
    input_file = "data/processed/classified_snippets.parquet"
    output_file = "data/processed/complexity_features.parquet"
    
    if not os.path.exists(input_file):
        logging.error(f"Input file {input_file} not found. Cannot proceed.")
        sys.exit(1)
        
    logging.info(f"Starting complexity extraction from {input_file}")
    try:
        df = process_dataset(input_file, output_file)
        logging.info(f"Successfully processed {len(df)} rows. Output saved to {output_file}")
    except Exception as e:
        logging.error(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()