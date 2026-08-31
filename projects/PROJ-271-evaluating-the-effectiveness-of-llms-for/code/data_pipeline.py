"""Data pipeline for ingesting code samples and computing static metrics."""
import os
import json
import logging
import subprocess
import tempfile
from typing import List, Dict, Any, Optional, Tuple

import pandas as pd
from datasets import load_dataset
from radon.raw import analyze as radon_analyze
from radon.complexity import cc_visit
from radon.visitors import ComplexityVisitor

from config import get_data_path, get_processed_path, setup_logging, RANDOM_SEED

logger = setup_logging(__name__)


def load_sampled_functions(
    target_sample_size: int = 800,
    max_runtime_hours: float = 5.5,
) -> List[Dict[str, Any]]:
    """Load a sampled subset of functions from codeparrot/github-code.

    Uses streaming to handle large datasets and dynamically adjusts sample size
    based on estimated processing time.

    Args:
        target_sample_size: Initial target number of functions.
        max_runtime_hours: Maximum allowed runtime in hours.

    Returns:
        List of dictionaries containing function code and metadata.
    """
    logger.info(f"Loading sampled functions (target: {target_sample_size})...")

    # Load dataset with streaming
    dataset = load_dataset(
        "codeparrot/github-code",
        split="train",
        streaming=True,
        trust_remote_code=True,
    )

    # Filter for Python files
    python_dataset = dataset.filter(lambda x: x["language"] == "python")

    functions = []
    estimated_time_per_function = 0.0
    count = 0

    # Dynamic sampling loop
    for item in python_dataset:
        code = item.get("code", "")
        if not code or len(code.strip()) == 0:
            continue

        # Estimate time for first few items
        if count < 10 and estimated_time_per_function == 0.0:
            import time
            start = time.time()
            # Simulate minimal processing to estimate time
            _ = radon_analyze(code)
            elapsed = time.time() - start
            estimated_time_per_function = elapsed

        functions.append({"code": code, "id": f"func_{count}"})
        count += 1

        # Calculate max sample limit
        if estimated_time_per_function > 0:
            max_samples = int((max_runtime_hours * 3600) / estimated_time_per_function)
            if count >= max_samples:
                logger.warning(f"Target sample size {target_sample_size} exceeds runtime limit. Reducing to {max_samples}.")
                break

        if len(functions) >= target_sample_size:
            break

    if len(functions) < 100:
        raise ValueError(f"Insufficient functions collected: {len(functions)} < 100")

    logger.info(f"Successfully loaded {len(functions)} functions.")
    return functions


def compute_radon_metrics(code: str) -> Dict[str, Any]:
    """Compute structural metrics using radon.

    Args:
        code: The source code string.

    Returns:
        Dictionary with loc, cyclomatic_complexity, and max_nesting_depth.
    """
    try:
        raw = radon_analyze(code)
        loc = raw.loc

        # Cyclomatic complexity
        cc_list = cc_visit(code)
        cyclomatic_complexity = sum(c.complexity for c in cc_list) if cc_list else 0

        # Nesting depth
        # radon doesn't have a direct "max nesting depth" in raw, so we calculate from visitors
        # or use a heuristic. For simplicity, we use the max complexity as a proxy or calculate manually.
        # A more robust way is to visit the AST.
        max_nesting = 0
        lines = code.split('\n')
        indent_counts = []
        for line in lines:
            if line.strip():
                # Count leading spaces
                stripped = line.lstrip()
                indent = len(line) - len(stripped)
                indent_counts.append(indent)

        if indent_counts:
            # Heuristic: assume 4 spaces per level
            max_indent = max(indent_counts)
            max_nesting = max_indent // 4

        return {
            "loc": loc,
            "cyclomatic_complexity": cyclomatic_complexity,
            "max_nesting_depth": max_nesting,
        }
    except Exception as e:
        logger.error(f"Error computing radon metrics: {e}")
        return {"loc": 0, "cyclomatic_complexity": 0, "max_nesting_depth": 0}


def run_pylint_analysis(code: str) -> List[str]:
    """Run Pylint on the code and return raw message codes.

    Args:
        code: The source code string.

    Returns:
        List of raw Pylint message codes (e.g., ['C0103', 'R0912']).
    """
    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            temp_path = f.name

        # Run pylint with specific output format
        result = subprocess.run(
            ["pylint", "--output-format=json", temp_path],
            capture_output=True,
            text=True,
            timeout=30,
        )

        os.unlink(temp_path)

        if result.returncode == 0 or result.returncode == 1: # 1 means no code analyzed or convention errors
            messages = json.loads(result.stdout)
            codes = [msg["symbol"] for msg in messages]
            return codes
        else:
            logger.warning(f"Pylint failed for code snippet: {result.stderr}")
            return []
    except subprocess.TimeoutExpired:
        logger.warning("Pylint timed out.")
        return []
    except Exception as e:
        logger.error(f"Error running pylint: {e}")
        return []


def normalize_pylint_smells(raw_codes: List[str], mapping: Dict[str, str]) -> List[str]:
    """Normalize raw Pylint codes to canonical smell names.

    Args:
        raw_codes: List of raw Pylint codes.
        mapping: Dictionary mapping raw codes to canonical names.

    Returns:
        List of canonical smell names.
    """
    normalized = []
    for code in raw_codes:
        if code in mapping:
            normalized.append(mapping[code])
        else:
            # Fallback or skip? Let's keep the raw code if no mapping found
            normalized.append(code)
    return normalized


def process_functions(
    functions: List[Dict[str, Any]],
    smell_mapping: Dict[str, str],
) -> List[Dict[str, Any]]:
    """Process a list of functions to compute metrics and labels.

    Args:
        functions: List of function dictionaries.
        smell_mapping: Mapping from Pylint codes to canonical names.

    Returns:
        List of processed function dictionaries with metrics and labels.
    """
    processed = []
    for func in functions:
        code = func["code"]
        func_id = func["id"]

        # Compute Radon metrics
        metrics = compute_radon_metrics(code)

        # Run Pylint
        raw_codes = run_pylint_analysis(code)

        # Normalize
        labels = normalize_pylint_smells(raw_codes, smell_mapping)

        processed.append({
            "code": code,
            "id": func_id,
            "loc": metrics["loc"],
            "cyclomatic_complexity": metrics["cyclomatic_complexity"],
            "max_nesting_depth": metrics["max_nesting_depth"],
            "static_smell_labels": labels,
        })

    return processed


def save_to_csv(data: List[Dict[str, Any]], filepath: Path) -> None:
    """Save processed data to a CSV file.

    Args:
        data: List of dictionaries to save.
        filepath: Path to the output CSV file.
    """
    df = pd.DataFrame(data)
    # Ensure columns are in a specific order if needed
    cols = ["code", "id", "loc", "cyclomatic_complexity", "max_nesting_depth", "static_smell_labels"]
    # Only keep columns that exist
    existing_cols = [c for c in cols if c in df.columns]
    df = df[existing_cols]
    df.to_csv(filepath, index=False)
    logger.info(f"Saved {len(data)} records to {filepath}")


def validate_output(filepath: Path, min_success_rate: float = 0.95) -> bool:
    """Validate that the output CSV meets success rate requirements.

    Args:
        filepath: Path to the CSV file.
        min_success_rate: Minimum required percentage of valid rows.

    Returns:
        True if validation passes, False otherwise.
    """
    if not filepath.exists():
        logger.error(f"Output file {filepath} does not exist.")
        return False

    df = pd.read_csv(filepath)
    required_cols = ["code", "loc", "cyclomatic_complexity", "static_smell_labels"]

    # Check if all required columns exist
    if not all(col in df.columns for col in required_cols):
        logger.error(f"Missing required columns in {filepath}")
        return False

    # Check for non-null values in critical columns
    valid_rows = df.dropna(subset=required_cols)
    success_rate = len(valid_rows) / len(df)

    if success_rate < min_success_rate:
        logger.error(f"Success rate {success_rate:.2%} is below {min_success_rate:.2%}")
        return False

    logger.info(f"Validation passed: {success_rate:.2%} valid rows")
    return True


def run_pipeline() -> None:
    """Execute the full data pipeline."""
    # Load smell mapping
    mapping_path = get_data_path("smell_mapping.json") # Adjust path if needed
    # Fallback to a default mapping if file not found (for robustness in demo)
    smell_mapping = {
        "invalid-name": "NamingConvention",
        "too-many-arguments": "TooManyArguments",
        "too-many-locals": "TooManyLocals",
        "too-many-statements": "LongMethod",
        "too-many-nested-blocks": "DeepNesting",
        "duplicate-code": "DuplicateCode",
        "unreachable": "DeadCode",
        "no-member": "MissingAttribute",
    }

    # Load sample
    functions = load_sampled_functions()

    # Process
    processed = process_functions(functions, smell_mapping)

    # Save
    output_path = get_data_path("static_baseline.csv")
    save_to_csv(processed, output_path)

    # Validate
    validate_output(output_path)


if __name__ == "__main__":
    run_pipeline()
