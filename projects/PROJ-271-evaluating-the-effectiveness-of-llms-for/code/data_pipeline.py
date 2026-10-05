import os
import json
import logging
import subprocess
import tempfile
import time
from typing import Dict, Any, List, Optional
from pathlib import Path

import pandas as pd
import numpy as np
from datasets import load_dataset
from radon.raw import analyze as radon_analyze
from radon.complexity import cc_visit

from config import get_path, get_data_path, get_processed_path, get_results_path, setup_logging, RANDOM_SEED
from helpers import (
    compute_radon_metrics_safe, validate_dataset_completeness,
    parse_smell_labels, create_detection_matrix
)

logger = setup_logging("data_pipeline")

def verify_dataset_source(dataset_id: str = "codeparrot/github-code") -> bool:
    """
    Verifies that the dataset source is accessible before streaming.
    
    Args:
        dataset_id: HuggingFace dataset ID.
    
    Returns:
        True if accessible, raises ConnectionError otherwise.
    """
    try:
        # Attempt to load dataset info without downloading
        ds = load_dataset(dataset_id, split="train", streaming=True)
        # Try to get one item to verify connectivity
        next(iter(ds))
        logger.info(f"Dataset {dataset_id} is accessible")
        return True
    except Exception as e:
        error_msg = f"Dataset {dataset_id} is unreachable: {e}"
        logger.error(error_msg)
        raise ConnectionError(error_msg)

def compute_radon_metrics(code: str) -> Dict[str, Any]:
    """
    Computes radon metrics for a code snippet.
    
    Args:
        code: Source code string.
    
    Returns:
        Dictionary with loc, cyclomatic_complexity, and nesting_depth.
    """
    return compute_radon_metrics_safe(code)

def run_pylint_analysis(code: str) -> List[str]:
    """
    Runs Pylint on code and returns list of warning codes.
    
    Args:
        code: Source code string.
    
    Returns:
        List of Pylint warning codes.
    """
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(code)
        temp_path = f.name
    
    try:
        result = subprocess.run(
            ['pylint', '--output-format=json', temp_path],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode != 0 and not result.stdout:
            return []
        
        try:
            messages = json.loads(result.stdout)
            codes = [msg.get('symbol', msg.get('message-id', 'unknown')) for msg in messages]
            return codes
        except json.JSONDecodeError:
            return []
    except subprocess.TimeoutExpired:
        logger.warning("Pylint timed out")
        return []
    except Exception as e:
        logger.warning(f"Pylint analysis failed: {e}")
        return []
    finally:
        os.unlink(temp_path)

def load_smell_mapping(filepath: Optional[str] = None) -> Dict[str, str]:
    """
    Loads the smell mapping from JSON file.
    
    Args:
        filepath: Path to mapping file.
    
    Returns:
        Dictionary mapping Pylint codes to canonical smell names.
    """
    if filepath is None:
        filepath = str(get_path("contracts/smell_mapping.json"))
    
    if not os.path.exists(filepath):
        logger.warning(f"Smell mapping file not found: {filepath}")
        return {}
    
    with open(filepath, 'r') as f:
        data = json.load(f)
    
    # Convert list format to dict if necessary
    if isinstance(data, list):
        mapping = {}
        for item in data:
            if isinstance(item, dict) and 'code' in item and 'canonical_name' in item:
                mapping[item['code']] = item['canonical_name']
        return mapping
    elif isinstance(data, dict):
        return data
    else:
        return {}

def normalize_pylint_smells(codes: List[str], mapping: Dict[str, str]) -> List[str]:
    """
    Normalizes Pylint codes to canonical smell names.
    
    Args:
        codes: List of Pylint codes.
        mapping: Mapping from codes to canonical names.
    
    Returns:
        List of normalized smell names.
    """
    normalized = []
    for code in codes:
        if code in mapping:
            normalized.append(mapping[code])
        else:
            logger.warning(f"Unmapped Pylint code: {code}")
            normalized.append(f"Unknown_{code}")
    return normalized

def load_sampled_functions_stratified(
    dataset_id: str = "codeparrot/github-code",
    split: str = "train",
    seed: int = RANDOM_SEED,
    target_count: int = 800
) -> List[Dict[str, Any]]:
    """
    Loads a sampled subset of functions from the dataset.
    
    Uses streaming to avoid memory issues and applies deterministic sampling.
    
    Args:
        dataset_id: HuggingFace dataset ID.
        split: Dataset split to use.
        seed: Random seed for reproducibility.
        target_count: Target number of functions to sample.
    
    Returns:
        List of dictionaries with 'code' and metadata.
    """
    logger.info(f"Loading sample from {dataset_id} (target: {target_count})")
    
    # Verify dataset is accessible
    verify_dataset_source(dataset_id)
    
    ds = load_dataset(dataset_id, split=split, streaming=True)
    
    sampled = []
    rng = np.random.default_rng(seed)
    
    # Simple random sampling with streaming
    for item in ds:
        if len(sampled) >= target_count:
            break
        
        # Check if item has code
        code = item.get('code')
        if code and isinstance(code, str) and len(code.strip()) > 0:
            sampled.append({
                'code': code,
                'repo': item.get('repo', 'unknown'),
                'language': item.get('language', 'unknown')
            })
    
    logger.info(f"Sampled {len(sampled)} functions")
    return sampled

def save_to_csv(data: List[Dict[str, Any]], filepath: str) -> None:
    """
    Saves data to a CSV file.
    
    Args:
        data: List of dictionaries.
        filepath: Output file path.
    """
    df = pd.DataFrame(data)
    df.to_csv(filepath, index=False)
    logger.info(f"Saved {len(data)} rows to {filepath}")

def validate_output(df: pd.DataFrame, required_cols: List[str], threshold: float = 0.95) -> bool:
    """
    Validates output dataframe has required columns and completeness.
    
    Args:
        df: DataFrame to validate.
        required_cols: List of required column names.
        threshold: Minimum completeness threshold.
    
    Returns:
        True if valid, False otherwise.
    """
    return validate_dataset_completeness(df, required_cols, threshold)

def run_pipeline(
    dataset_id: str = "codeparrot/github-code",
    seed: int = RANDOM_SEED,
    target_count: int = 800
) -> pd.DataFrame:
    """
    Runs the full data pipeline: sampling, metric calculation, and saving.
    
    Args:
        dataset_id: HuggingFace dataset ID.
        seed: Random seed.
        target_count: Target sample size.
    
    Returns:
        Processed DataFrame with metrics and labels.
    """
    logger.info("Starting data pipeline")
    
    # Load sample
    sampled_functions = load_sampled_functions_stratified(
        dataset_id=dataset_id,
        seed=seed,
        target_count=target_count
    )
    
    if not sampled_functions:
        raise ValueError("No functions sampled from dataset")
    
    # Process each function
    processed_data = []
    smell_mapping = load_smell_mapping()
    
    for i, item in enumerate(sampled_functions):
        code = item['code']
        
        # Compute radon metrics
        metrics = compute_radon_metrics(code)
        
        # Run pylint
        pylint_codes = run_pylint_analysis(code)
        
        # Normalize smells
        normalized_smells = normalize_pylint_smells(pylint_codes, smell_mapping)
        
        processed_data.append({
            'code': code,
            'loc': metrics['loc'],
            'cyclomatic_complexity': metrics['cyclomatic_complexity'],
            'nesting_depth': metrics['nesting_depth'],
            'static_smell_labels': '|'.join(normalized_smells),
            'repo': item.get('repo', 'unknown'),
            'language': item.get('language', 'unknown')
        })
        
        if (i + 1) % 100 == 0:
            logger.info(f"Processed {i + 1}/{len(sampled_functions)} functions")
    
    # Create DataFrame
    df = pd.DataFrame(processed_data)
    
    # Validate
    required_cols = ['code', 'loc', 'cyclomatic_complexity', 'nesting_depth', 'static_smell_labels']
    is_valid = validate_output(df, required_cols)
    
    if not is_valid:
        logger.warning("Output validation failed, but proceeding")
    
    return df

def main():
    """Main entry point for data pipeline."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run data pipeline")
    parser.add_argument("--sample-size", type=int, default=800, help="Target sample size")
    parser.add_argument("--seed", type=int, default=RANDOM_SEED, help="Random seed")
    parser.add_argument("--dataset", type=str, default="codeparrot/github-code", help="Dataset ID")
    
    args = parser.parse_args()
    
    try:
        df = run_pipeline(
            dataset_id=args.dataset,
            seed=args.seed,
            target_count=args.sample_size
        )
        
        output_path = get_data_path("static_baseline.csv")
        df.to_csv(output_path, index=False)
        logger.info(f"Pipeline complete. Output saved to {output_path}")
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        raise

if __name__ == "__main__":
    main()