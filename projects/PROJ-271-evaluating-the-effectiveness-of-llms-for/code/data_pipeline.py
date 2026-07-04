import os
import json
import logging
import subprocess
import tempfile
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np
from radon.complexity import cc_visit
from radon.raw import analyze
from datasets import load_dataset
from pylint.lint import Run
from pylint.reporters.text import TextReporter
from io import StringIO

from config import get_data_path, get_path
from monitoring import get_ram_usage_mb, get_cpu_utilization

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
REQUIRED_COLUMNS = ['code', 'loc', 'cyclomatic_complexity', 'static_smell_labels']
COMPLETENESS_THRESHOLD = 0.95

def load_sampled_functions(sample_size: int = 800) -> List[Dict[str, Any]]:
    """Load a sampled subset of functions from codeparrot/github-code."""
    try:
        logger.info(f"Loading {sample_size} functions from codeparrot/github-code...")
        dataset = load_dataset("codeparrot/github-code", split="train", streaming=True)
        functions = []
        count = 0
        for item in dataset:
            if count >= sample_size:
                break
            # Filter for Python code
            if item['language'] == 'python' and 'content' in item:
                functions.append({
                    'id': item.get('repo', 'unknown') + '_' + str(count),
                    'code': item['content'],
                    'repo': item.get('repo', 'unknown')
                })
                count += 1
        logger.info(f"Successfully loaded {len(functions)} Python functions.")
        return functions
    except Exception as e:
        logger.error(f"Failed to load dataset: {e}")
        raise

def compute_radon_metrics(code: str) -> Tuple[int, float]:
    """Compute LOC and Cyclomatic Complexity using radon."""
    try:
        raw_analysis = analyze(code)
        loc = raw_analysis.loc
        complexity = cc_visit(code)
        cc_sum = sum(func.cc for func in complexity)
        return loc, cc_sum
    except Exception as e:
        logger.warning(f"Radon parsing error: {e}")
        raise

def run_pylint_analysis(code: str) -> str:
    """Run Pylint on the code and return the output."""
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            f.flush()
            temp_path = f.name

        output = StringIO()
        reporter = TextReporter(output)
        try:
            Run([temp_path, '--disable=all', '--enable=E,W', '--output-format=text'],
                reporter=reporter, exit=False)
        finally:
            os.unlink(temp_path)

        return output.getvalue()
    except Exception as e:
        logger.error(f"Pylint execution error: {e}")
        return ""

def normalize_pylint_smells(pylint_output: str) -> List[str]:
    """Normalize raw Pylint codes to canonical smell names."""
    smell_mapping = {
        'C0114': 'missing_module_docstring',
        'C0116': 'missing_function_docstring',
        'R0903': 'too_few_public_methods',
        'R0904': 'too_many_public_methods',
        'R0902': 'too_many_instance_attributes',
        'R0913': 'too_many_arguments',
        'R0914': 'too_many_local_variables',
        'R0915': 'too_many_statements',
        'R0912': 'too_many_branches',
        'R0911': 'too_many_returns',
        'C0301': 'line_too_long',
        'C0302': 'too_many_lines',
        'E1101': 'no_member',
        'W0613': 'unused_argument',
        'W0612': 'unused_variable'
    }

    smells = []
    for msg_code, smell_name in smell_mapping.items():
        if msg_code in pylint_output:
            smells.append(smell_name)
    return smells

def process_functions(functions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Process each function to compute metrics and smell labels."""
    results = []
    for func in functions:
        try:
            code = func['code']
            loc, cc = compute_radon_metrics(code)
            pylint_output = run_pylint_analysis(code)
            smells = normalize_pylint_smells(pylint_output)

            results.append({
                'id': func['id'],
                'code': code,
                'loc': loc,
                'cyclomatic_complexity': cc,
                'static_smell_labels': json.dumps(smells)
            })
        except Exception as e:
            logger.warning(f"Skipping function {func['id']} due to error: {e}")
            continue
    return results

def save_to_csv(data: List[Dict[str, Any]], filepath: str) -> None:
    """Save processed data to CSV."""
    df = pd.DataFrame(data)
    df.to_csv(filepath, index=False)
    logger.info(f"Saved {len(data)} records to {filepath}")

def validate_output(filepath: str, required_columns: List[str] = None, threshold: float = 0.95) -> bool:
    """
    Validate that the output CSV contains >= 95% of sampled functions 
    with all required columns.
    
    Returns True if validation passes, False otherwise.
    """
    if required_columns is None:
        required_columns = REQUIRED_COLUMNS

    try:
        df = pd.read_csv(filepath)
        total_rows = len(df)
        
        if total_rows == 0:
            logger.error(f"Validation failed: {filepath} is empty.")
            return False

        # Check for required columns
        missing_cols = [col for col in required_columns if col not in df.columns]
        if missing_cols:
            logger.error(f"Validation failed: Missing required columns: {missing_cols}")
            return False

        # Check for non-null values in required columns
        complete_rows = 0
        for _, row in df.iterrows():
            is_complete = all(pd.notna(row[col]) for col in required_columns)
            if is_complete:
                complete_rows += 1

        completeness_ratio = complete_rows / total_rows
        logger.info(f"Validation: {complete_rows}/{total_rows} rows ({completeness_ratio:.2%}) have all required columns.")

        if completeness_ratio >= threshold:
            logger.info(f"Validation PASSED: Completeness ratio ({completeness_ratio:.2%}) >= threshold ({threshold:.2%})")
            return True
        else:
            logger.error(f"Validation FAILED: Completeness ratio ({completeness_ratio:.2%}) < threshold ({threshold:.2%})")
            return False

    except FileNotFoundError:
        logger.error(f"Validation failed: File not found - {filepath}")
        return False
    except Exception as e:
        logger.error(f"Validation failed with error: {e}")
        return False

def run_pipeline(sample_size: int = 800) -> bool:
    """Run the full data pipeline and validate the output."""
    output_path = get_data_path("static_baseline.csv")
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Load data
    functions = load_sampled_functions(sample_size)
    
    if not functions:
        logger.error("No functions loaded. Pipeline aborted.")
        return False

    # Process functions
    processed_data = process_functions(functions)
    
    if not processed_data:
        logger.error("No data processed. Pipeline aborted.")
        return False

    # Save to CSV
    save_to_csv(processed_data, output_path)
    
    # Validate output
    is_valid = validate_output(output_path, REQUIRED_COLUMNS, COMPLETENESS_THRESHOLD)
    
    return is_valid

if __name__ == "__main__":
    success = run_pipeline()
    if not success:
        exit(1)
    logger.info("Pipeline completed successfully.")
