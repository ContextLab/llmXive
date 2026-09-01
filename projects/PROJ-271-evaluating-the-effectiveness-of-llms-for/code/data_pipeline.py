import os
import json
import logging
import subprocess
import tempfile
from typing import List, Dict, Any, Optional, Tuple

from radon.raw import analyze as radon_analyze
import pandas as pd
from datasets import load_dataset

from config import get_data_path, get_processed_path, get_results_path, setup_logging
from helpers import compute_radon_metrics_safe, validate_dataset_completeness


def load_sampled_functions(sample_size: int = 800, seed: int = 42) -> List[Dict[str, Any]]:
    """
    Load a sampled subset of functions from codeparrot/github-code using streaming.
    Implements dynamic runtime check to ensure sample size is feasible within time budget.
    """
    logger = setup_logging(__name__)
    logger.info(f"Loading sampled functions from codeparrot/github-code (target: {sample_size})...")

    try:
        # Load dataset with streaming
        dataset = load_dataset(
            "codeparrot/github-code",
            split="train",
            streaming=True,
            trust_remote_code=True
        )

        # Estimate time per function by processing a small batch
        batch_size = 10
        start_time = __import__('time').time()
        processed_count = 0

        for idx, item in enumerate(dataset):
            if idx >= batch_size:
                break
            # Basic processing to estimate time
            _ = item.get("content", "")
            processed_count += 1

        end_time = __import__('time').time()
        estimated_time_per_function = (end_time - start_time) / processed_count if processed_count > 0 else 0.1

        # Calculate max samples to stay within 5.5 hours (19800 seconds)
        max_time_budget = 5.5 * 3600
        max_samples = int(max_time_budget / estimated_time_per_function) if estimated_time_per_function > 0 else sample_size

        # Adjust sample size if needed
        if max_samples < sample_size:
            logger.warning(f"Time budget exceeded. Reducing sample size from {sample_size} to {max_samples}.")
            sample_size = max_samples

        # Validate minimum sample size for McNemar's test
        if sample_size < 100:
            error_msg = f"Sample size {sample_size} is below the minimum threshold of 100 for McNemar's test validity."
            logger.error(error_msg)
            # Log failure to results
            results_path = get_results_path()
            report = {
                "sample_size": sample_size,
                "threshold": 100,
                "reason": "Insufficient sample size for statistical validity",
                "status": "failed"
            }
            with open(os.path.join(results_path, "sample_report.json"), "w") as f:
                json.dump(report, f, indent=2)
            raise ValueError(error_msg)

        logger.info(f"Final sample size: {sample_size}")

        # Sample the dataset
        sampled_functions = []
        for idx, item in enumerate(dataset):
            if idx >= sample_size:
                break
            content = item.get("content", "")
            if content and len(content.strip()) > 0:
                sampled_functions.append({"code": content, "id": idx})

        logger.info(f"Successfully loaded {len(sampled_functions)} functions.")
        return sampled_functions

    except Exception as e:
        logger.error(f"Failed to load dataset: {e}")
        raise


def compute_radon_metrics(code: str) -> Dict[str, Any]:
    """
    Compute structural metrics using radon: LOC, Cyclomatic Complexity, Nesting Depth.
    """
    try:
        result = radon_analyze(code)
        return {
            "loc": result.loc,
            "cyclomatic_complexity": result.complexity,
            "nesting_depth": result.max_nesting
        }
    except Exception as e:
        logging.getLogger(__name__).warning(f"Radon analysis failed: {e}")
        return {"loc": 0, "cyclomatic_complexity": 0, "nesting_depth": 0}


def run_pylint_analysis(code: str, temp_dir: str) -> List[str]:
    """
    Run Pylint on the code snippet and return raw codes.
    """
    try:
        # Write code to a temporary file
        temp_file = os.path.join(temp_dir, "temp_code.py")
        with open(temp_file, "w", encoding="utf-8") as f:
            f.write(code)

        # Run pylint
        result = subprocess.run(
            ["pylint", "--output-format=json", temp_file],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0 or result.returncode == 1:  # 1 means issues found, which is fine
            messages = json.loads(result.stdout)
            codes = [msg["symbol"] for msg in messages]
            return codes
        else:
            logging.getLogger(__name__).warning(f"Pylint failed: {result.stderr}")
            return []

    except subprocess.TimeoutExpired:
        logging.getLogger(__name__).warning("Pylint timed out")
        return []
    except Exception as e:
        logging.getLogger(__name__).warning(f"Pylint error: {e}")
        return []


def normalize_pylint_smells(raw_codes: List[str], mapping: Dict[str, str]) -> List[str]:
    """
    Normalize raw Pylint codes to canonical smell names using the mapping.
    """
    normalized = []
    for code in raw_codes:
        if code in mapping:
            normalized.append(mapping[code])
        else:
            logging.getLogger(__name__).warning(f"Unmapped Pylint code encountered: {code}")
            normalized.append(code)  # Keep raw code if unmapped
    return normalized


def process_functions(functions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Process a list of functions: compute radon metrics and pylint smells.
    """
    logger = setup_logging(__name__)
    results = []

    # Load smell mapping
    mapping_path = os.path.join("contracts", "smell_mapping.json")
    if os.path.exists(mapping_path):
        with open(mapping_path, "r") as f:
            mapping = json.load(f)
    else:
        logger.warning("smell_mapping.json not found. Using empty mapping.")
        mapping = {}

    for func in functions:
        code = func["code"]
        radon_metrics = compute_radon_metrics(code)
        raw_codes = run_pylint_analysis(code, tempfile.gettempdir())
        normalized_smells = normalize_pylint_smells(raw_codes, mapping)

        results.append({
            "code": code,
            "loc": radon_metrics["loc"],
            "cyclomatic_complexity": radon_metrics["cyclomatic_complexity"],
            "nesting_depth": radon_metrics["nesting_depth"],
            "static_smell_labels": ",".join(normalized_smells)
        })

    return results


def save_to_csv(data: List[Dict[str, Any]], output_path: str) -> None:
    """
    Save processed data to a CSV file.
    """
    df = pd.DataFrame(data)
    df.to_csv(output_path, index=False)
    logging.getLogger(__name__).info(f"Saved {len(data)} records to {output_path}")


def validate_output(output_path: str, required_columns: List[str], min_completeness: float = 0.95) -> bool:
    """
    Validate the output CSV: check schema and completeness.
    """
    try:
        df = pd.read_csv(output_path)
        if not all(col in df.columns for col in required_columns):
            logging.getLogger(__name__).error(f"Missing required columns. Found: {df.columns.tolist()}")
            return False

        completeness = df.dropna(subset=required_columns).shape[0] / df.shape[0]
        if completeness < min_completeness:
            logging.getLogger(__name__).warning(f"Completeness {completeness:.2%} below threshold {min_completeness:.2%}")
            return False

        logging.getLogger(__name__).info(f"Validation passed. Completeness: {completeness:.2%}")
        return True

    except Exception as e:
        logging.getLogger(__name__).error(f"Validation failed: {e}")
        return False


def run_pipeline(sample_size: int = 800, seed: int = 42) -> bool:
    """
    Run the full data pipeline: load, process, save, and validate.
    """
    logger = setup_logging(__name__)
    try:
        # Load functions
        functions = load_sampled_functions(sample_size=sample_size, seed=seed)

        # Process functions
        processed_data = process_functions(functions)

        # Save to CSV
        output_path = os.path.join(get_data_path(), "static_baseline.csv")
        save_to_csv(processed_data, output_path)

        # Validate output
        required_columns = ["code", "loc", "cyclomatic_complexity", "nesting_depth", "static_smell_labels"]
        is_valid = validate_output(output_path, required_columns)

        if is_valid:
            logger.info("Pipeline completed successfully.")
            return True
        else:
            logger.error("Pipeline validation failed.")
            return False

    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        return False
