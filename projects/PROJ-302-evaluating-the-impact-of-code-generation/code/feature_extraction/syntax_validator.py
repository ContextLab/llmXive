"""
Syntax validation for generated code snippets.

This module validates that generated code snippets (from T014b) are syntactically valid.
It performs a >=95% success rate check as required by SC-007.

Dependencies:
- T014b: synthetic_generator.py (must have generated data/processed/generated_snippets.parquet)
"""
import os
import sys
import ast
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from utils.config import get_config, ensure_directories

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
INPUT_FILE = "data/processed/generated_snippets.parquet"
OUTPUT_FILE = "data/processed/syntax_validation_results.parquet"
SUCCESS_RATE_THRESHOLD = 0.95  # 95%

def validate_snippet_syntax(code_snippet: str) -> Tuple[bool, Optional[str]]:
    """
    Validate if a code snippet is syntactically valid Python.
    
    Args:
        code_snippet: The code snippet to validate
        
    Returns:
        Tuple of (is_valid, error_message)
        - is_valid: True if syntax is valid, False otherwise
        - error_message: None if valid, otherwise the error description
    """
    if not isinstance(code_snippet, str):
        return False, f"Invalid type: expected str, got {type(code_snippet)}"
    
    if not code_snippet.strip():
        return False, "Empty snippet"
    
    try:
        ast.parse(code_snippet)
        return True, None
    except SyntaxError as e:
        error_msg = f"SyntaxError at line {e.lineno}: {e.msg}"
        return False, error_msg
    except Exception as e:
        error_msg = f"Unexpected error: {type(e).__name__}: {str(e)}"
        return False, error_msg

def validate_dataset(input_path: Path) -> pd.DataFrame:
    """
    Validate syntax for all snippets in the dataset.
    
    Args:
        input_path: Path to the input parquet file
        
    Returns:
        DataFrame with validation results
    """
    logger.info(f"Loading dataset from {input_path}")
    
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    df = pd.read_parquet(input_path)
    
    logger.info(f"Loaded {len(df)} snippets. Validating syntax...")
    
    results = []
    valid_count = 0
    invalid_count = 0
    
    for idx, row in df.iterrows():
        # Try to get the code snippet column (common names)
        code_snippet = None
        for col in ['code', 'snippet', 'code_content', 'generated_code']:
            if col in row.index:
                code_snippet = row[col]
                break
        
        if code_snippet is None:
            logger.warning(f"Row {idx}: No code snippet found. Available columns: {list(row.index)}")
            is_valid = False
            error_msg = "No code snippet column found"
        else:
            is_valid, error_msg = validate_snippet_syntax(code_snippet)
        
        if is_valid:
            valid_count += 1
        else:
            invalid_count += 1
        
        results.append({
            'snippet_id': row.get('snippet_id', idx),
            'is_valid': is_valid,
            'error_message': error_msg,
            'original_index': idx
        })
        
        # Log progress
        if (idx + 1) % 100 == 0:
            logger.info(f"Processed {idx + 1}/{len(df)} snippets")
    
    validation_df = pd.DataFrame(results)
    
    total = len(validation_df)
    success_rate = valid_count / total if total > 0 else 0.0
    
    logger.info(f"Validation complete:")
    logger.info(f"  Total snippets: {total}")
    logger.info(f"  Valid: {valid_count} ({success_rate:.2%})")
    logger.info(f"  Invalid: {invalid_count} ({1 - success_rate:.2%})")
    logger.info(f"  Success rate threshold: {SUCCESS_RATE_THRESHOLD:.2%}")
    
    if success_rate >= SUCCESS_RATE_THRESHOLD:
        logger.info(f"✓ PASS: Success rate ({success_rate:.2%}) meets threshold ({SUCCESS_RATE_THRESHOLD:.2%})")
    else:
        logger.error(f"✗ FAIL: Success rate ({success_rate:.2%}) below threshold ({SUCCESS_RATE_THRESHOLD:.2%})")
    
    validation_df['success_rate_threshold_met'] = success_rate >= SUCCESS_RATE_THRESHOLD
    validation_df['overall_success_rate'] = success_rate
    
    return validation_df

def main():
    """Main entry point for syntax validation."""
    logger.info("Starting syntax validation for generated snippets (Task T019)")
    
    config = get_config()
    ensure_directories()
    
    input_path = PROJECT_ROOT / INPUT_FILE
    output_path = PROJECT_ROOT / OUTPUT_FILE
    
    try:
        # Validate dataset
        validation_results = validate_dataset(input_path)
        
        # Save results
        output_path.parent.mkdir(parents=True, exist_ok=True)
        validation_results.to_parquet(output_path, index=False)
        logger.info(f"Validation results saved to {output_path}")
        
        # Check if threshold is met
        success_rate = validation_results['overall_success_rate'].iloc[0]
        threshold_met = validation_results['success_rate_threshold_met'].iloc[0]
        
        if threshold_met:
            logger.info(f"SUCCESS: Syntax validation passed with {success_rate:.2%} success rate")
            return 0
        else:
            logger.error(f"FAILURE: Syntax validation failed. Success rate {success_rate:.2%} < {SUCCESS_RATE_THRESHOLD:.2%}")
            return 1
            
    except FileNotFoundError as e:
        logger.error(f"Input file not found: {e}")
        logger.error("Make sure T014b (synthetic_generator.py) has been run successfully first.")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error during validation: {e}")
        raise

if __name__ == "__main__":
    sys.exit(main())
