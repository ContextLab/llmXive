import os
import json
import logging
import subprocess
import tempfile
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd

from config import get_path, get_data_path, get_processed_path, get_results_path, setup_logging

def load_sampled_functions(num_samples: int) -> List[str]:
    """Loads a sample of functions from the codeparrot dataset.
    
    Uses the HuggingFace datasets library to stream a sample of Python code
    from the codeparrot/github-code repository.
    """
    try:
        from datasets import load_dataset
        logging.info(f"Loading {num_samples} functions from codeparrot/github-code...")
        
        # Load dataset with streaming to avoid downloading full dataset
        dataset = load_dataset(
            "codeparrot/github-code",
            split="train",
            streaming=True,
            trust_remote_code=True
        )
        
        # Filter for Python files only and sample
        python_functions = []
        count = 0
        
        for item in dataset:
            if count >= num_samples:
                break
                
            # Check if it's Python code
            if item.get("language") == "python" and item.get("content"):
                content = item["content"]
                # Basic check to ensure it looks like code (has def or class)
                if "def " in content or "class " in content:
                    python_functions.append(content)
                    count += 1
                    
        if count < num_samples:
            logging.warning(f"Only found {count} Python functions, requested {num_samples}")
            
        return python_functions
        
    except Exception as e:
        logging.error(f"Failed to load dataset: {e}")
        raise

def compute_radon_metrics(code: str) -> Tuple[int, float]:
    """Computes LOC and Cyclomatic Complexity using radon."""
    try:
        from radon.complexity import cc_visit
        from radon.raw import analyze
        from io import StringIO

        # Get raw metrics (LOC)
        raw_analysis = analyze(StringIO(code))
        loc = raw_analysis.loc
        
        # Get complexity metrics
        cc_results = cc_visit(StringIO(code))
        cyclomatic_complexity = sum([r.complexity for r in cc_results]) if cc_results else 0
        
        return loc, cyclomatic_complexity
    except Exception as e:
        logging.error(f"Radon error processing code: {e}")
        return 0, 0

def run_pylint_analysis(code: str) -> List[str]:
    """Runs Pylint analysis and returns a list of smell codes."""
    try:
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False, mode="w") as tmp_file:
            tmp_file.write(code)
            tmp_file_path = tmp_file.name

        result = subprocess.run(
            ["pylint", "--disable=all", "--enable=C,R", "--output-format=text", tmp_file_path],
            capture_output=True,
            text=True,
            timeout=30
        )
        output = result.stdout + result.stderr
        
        smell_codes = []
        for line in output.splitlines():
            # Look for Pylint message codes (e.g., C0301, R0915)
            if ":" in line:
                parts = line.split(":")
                if len(parts) >= 2:
                    # Extract potential code from the message part
                    msg_part = parts[-1].strip()
                    # Look for patterns like [C0301] or C0301:
                    import re
                    matches = re.findall(r'\[?([CR]\d{4})\]?', msg_part)
                    smell_codes.extend(matches)

        os.remove(tmp_file_path)
        return list(set(smell_codes))  # Remove duplicates
    except subprocess.TimeoutExpired:
        logging.warning("Pylint timed out on a function")
        return []
    except Exception as e:
        logging.error(f"Pylint error processing code: {e}")
        return []

def normalize_pylint_smells(smell_codes: List[str]) -> List[str]:
    """Normalizes Pylint smell codes to canonical names."""
    normalization_map = {
        # Line length and formatting
        "C0301": "line-too-long",
        "C0302": "too-many-lines",
        "C0303": "trailing-whitespace",
        "C0304": "missing-final-newline",
        "C0321": "multiple-statements",
        
        # Naming conventions
        "C0103": "invalid-name",
        "C0111": "missing-docstring",
        "C0116": "missing-function-docstring",
        "C0114": "missing-module-docstring",
        
        # Complexity and size
        "R0902": "too-many-instance-attributes",
        "R0903": "too-few-public-methods",
        "R0904": "too-many-public-methods",
        "R0911": "too-many-return-statements",
        "R0912": "too-many-branches",
        "R0913": "too-many-arguments",
        "R0914": "too-many-locals",
        "R0915": "too-many-statements",
        
        # Design issues
        "R0901": "too-many-ancestors",
        "R0916": "too-many-boolean-expressions",
        
        # Import issues
        "C0410": "multiple-imports",
        "C0411": "wrong-import-order",
        "C0412": "ungrouped-imports",
    }
    
    normalized = []
    for code in smell_codes:
        if code in normalization_map:
            normalized.append(normalization_map[code])
        else:
            normalized.append(f"pylint-{code}")
            
    return normalized

def process_functions(functions: List[str]) -> List[Dict]:
    """Processes a list of functions and extracts metrics."""
    results = []
    for i, code in enumerate(functions):
        if i % 100 == 0:
            logging.info(f"Processing function {i}/{len(functions)}")
        
        # Compute metrics
        loc, cyclomatic_complexity = compute_radon_metrics(code)
        smell_codes = run_pylint_analysis(code)
        normalized_smells = normalize_pylint_smells(smell_codes)

        results.append({
            "code": code,
            "loc": loc,
            "cyclomatic_complexity": cyclomatic_complexity,
            "static_smell_labels": ",".join(normalized_smells),
        })
    return results

def save_to_csv(data: List[Dict], filepath: str):
    """Saves the processed data to a CSV file."""
    if not data:
        logging.warning("No data to save to CSV")
        return
        
    df = pd.DataFrame(data)
    df.to_csv(filepath, index=False, encoding='utf-8')
    logging.info(f"Saved {len(data)} records to {filepath}")

def validate_output(filepath: str) -> bool:
    try:
        df = pd.read_csv(filepath)
        required_cols = ["code", "loc", "cyclomatic_complexity", "static_smell_labels"]
        
        if df.shape[0] == 0:
            logging.error("CSV file is empty")
            return False
            
        if not all(col in df.columns for col in required_cols):
            missing = [col for col in required_cols if col not in df.columns]
            logging.error(f"Missing required columns: {missing}")
            return False
            
        return True
    except Exception as e:
        logging.error(f"Error validating output file {filepath}: {e}")
        return False

def run_pipeline(num_samples: int, data_path: str):
    """Runs the entire pipeline."""
    setup_logging()
    logging.info(f"Starting pipeline with {num_samples} samples")
    
    functions = load_sampled_functions(num_samples)
    logging.info(f"Loaded {len(functions)} functions")
    
    processed_data = process_functions(functions)
    logging.info(f"Processed {len(processed_data)} functions")
    
    output_filepath = os.path.join(data_path, "static_baseline.csv")
    save_to_csv(processed_data, output_filepath)
    
    if validate_output(output_filepath):
        logging.info(f"Successfully created and validated {output_filepath}")
        return True
    else:
        logging.error(f"Failed to create valid baseline CSV at {output_filepath}")
        return False

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Run code smell detection pipeline")
    parser.add_argument("--num_samples", type=int, default=800, help="Number of functions to sample")
    args = parser.parse_args()
    
    success = run_pipeline(args.num_samples, get_data_path())
    exit(0 if success else 1)