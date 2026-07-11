import os
import csv
import tempfile
import shutil
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import json

# Import from sibling modules based on API surface
from generation.tester import update_samples_with_results, run_tester_pipeline
from generation.generator import run_generation_pipeline
from utils.logger import log_generation_error, log_timeout_error, initialize_memory_log
from config.loader import load_config, validate_config, get_config_value

# Constants
SUBSTANTIAL_THRESHOLD = 0.15  # 15% difference in pass rate considered substantial (FR-016)
MIN_PASS_RATE_THRESHOLD = 0.01  # 1% minimum pass rate (FR-017 / T018b requirement)

logger = logging.getLogger(__name__)

def ensure_output_dirs() -> Path:
    """Ensure output directories exist."""
    output_dir = Path("data/processed")
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir

def calculate_pass_rates(samples_file: Path) -> Dict[str, float]:
    """
    Calculate pass rates for each style group from the samples CSV.
    
    Args:
        samples_file: Path to samples_all.csv or samples_valid.csv
        
    Returns:
        Dictionary mapping style names to their pass rates (0.0 to 1.0)
    """
    if not samples_file.exists():
        raise FileNotFoundError(f"Samples file not found: {samples_file}")
    
    style_counts = {}
    style_passes = {}
    
    with open(samples_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            style = row.get('style', 'unknown')
            pass_status = row.get('pass_status', '')
            
            if style not in style_counts:
                style_counts[style] = 0
                style_passes[style] = 0
            
            style_counts[style] += 1
            
            if pass_status.lower() in ['true', '1', 'yes']:
                style_passes[style] += 1
    
    pass_rates = {}
    for style in style_counts:
        if style_counts[style] > 0:
            pass_rates[style] = style_passes[style] / style_counts[style]
        else:
            pass_rates[style] = 0.0
    
    return pass_rates

def detect_significant_bias(pass_rates: Dict[str, float]) -> Optional[str]:
    """
    Detect if any two style groups have a substantial difference in pass rates.
    
    Args:
        pass_rates: Dictionary of style -> pass rate
        
    Returns:
        "Potentially Biased" if difference exceeds threshold, None otherwise
    """
    styles = list(pass_rates.keys())
    if len(styles) < 2:
        return None
    
    for i in range(len(styles)):
        for j in range(i + 1, len(styles)):
            diff = abs(pass_rates[styles[i]] - pass_rates[styles[j]])
            if diff > SUBSTANTIAL_THRESHOLD:
                logger.warning(
                    f"Significant bias detected: {styles[i]} ({pass_rates[styles[i]]:.2%}) "
                    f"vs {styles[j]} ({pass_rates[styles[j]]:.2%}), diff={diff:.2%}"
                )
                return "Potentially Biased"
    
    return None

def check_model_incapability(pass_rates: Dict[str, float]) -> bool:
    """
    Check if any style group has a pass rate below the minimum threshold.
    
    Args:
        pass_rates: Dictionary of style -> pass rate
        
    Returns:
        True if model is incapable (pass rate < 1% for any style), False otherwise
    """
    for style, rate in pass_rates.items():
        if rate < MIN_PASS_RATE_THRESHOLD:
            logger.error(
                f"Model Incapability detected: {style} style has pass rate {rate:.2%} "
                f"(below {MIN_PASS_RATE_THRESHOLD:.0%} threshold). HALTING execution."
            )
            return True
    return False

def inject_bias_flag_to_csv(csv_path: Path, bias_flag: Optional[str]):
    """
    Add a bias flag column to the CSV if bias was detected.
    
    Args:
        csv_path: Path to the CSV file to update
        bias_flag: The flag string to inject, or None
    """
    if not csv_path.exists():
        logger.warning(f"Cannot inject bias flag: file not found {csv_path}")
        return
    
    temp_path = csv_path.with_suffix('.csv.tmp')
    
    with open(csv_path, 'r', encoding='utf-8') as infile, \
         open(temp_path, 'w', newline='', encoding='utf-8') as outfile:
        
        reader = csv.DictReader(infile)
        fieldnames = reader.fieldnames + ['bias_flag'] if reader.fieldnames else ['bias_flag']
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for row in reader:
            row['bias_flag'] = bias_flag if bias_flag else ""
            writer.writerow(row)
    
    shutil.move(str(temp_path), str(csv_path))
    logger.info(f"Injected bias flag '{bias_flag}' into {csv_path}")

def update_samples_with_pass_status(all_samples_path: Path, results_path: Path) -> Path:
    """
    Update samples_all.csv with pass_status from tester results.
    
    Args:
        all_samples_path: Path to samples_all.csv
        results_path: Path to tester results
        
    Returns:
        Path to the updated CSV file
    """
    ensure_output_dirs()
    
    # Read results
    results = {}
    if results_path.exists():
        with open(results_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                key = (row['task_id'], row['style'], row['sample_id'])
                results[key] = row.get('pass_status', '')
    
    # Update samples
    temp_path = all_samples_path.with_suffix('.csv.tmp')
    updated_count = 0
    
    with open(all_samples_path, 'r', encoding='utf-8') as infile, \
         open(temp_path, 'w', newline='', encoding='utf-8') as outfile:
        
        reader = csv.DictReader(infile)
        fieldnames = reader.fieldnames
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for row in reader:
            key = (row['task_id'], row['style'], row['sample_id'])
            if key in results:
                row['pass_status'] = results[key]
                updated_count += 1
            else:
                row['pass_status'] = ''  # Keep null if not found
            writer.writerow(row)
    
    shutil.move(str(temp_path), str(all_samples_path))
    logger.info(f"Updated {updated_count} samples with pass_status")
    return all_samples_path

def filter_valid_samples(all_samples_path: Path, valid_samples_path: Path) -> Path:
    """
    Filter samples_all.csv to create samples_valid.csv (only pass_status=True).
    
    Args:
        all_samples_path: Path to samples_all.csv
        valid_samples_path: Path to write samples_valid.csv
        
    Returns:
        Path to the filtered CSV file
    """
    ensure_output_dirs()
    
    if not all_samples_path.exists():
        raise FileNotFoundError(f"Source file not found: {all_samples_path}")
    
    with open(all_samples_path, 'r', encoding='utf-8') as infile, \
         open(valid_samples_path, 'w', newline='', encoding='utf-8') as outfile:
        
        reader = csv.DictReader(infile)
        writer = csv.DictWriter(outfile, fieldnames=reader.fieldnames)
        writer.writeheader()
        
        valid_count = 0
        for row in reader:
            if row.get('pass_status', '').lower() in ['true', '1', 'yes']:
                writer.writerow(row)
                valid_count += 1
    
    logger.info(f"Filtered {valid_count} valid samples to {valid_samples_path}")
    return valid_samples_path

def run_pipeline(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Run the full generation, testing, filtering, and bias detection pipeline.
    
    This implements T017a, T017b, and T018:
    1. Update samples_all.csv with pass_status (T017a)
    2. Filter to samples_valid.csv (T017b)
    3. Calculate pass rates and detect bias (T018)
    4. Inject bias flag into output CSVs
    
    Args:
        config_path: Optional path to config file, uses default if None
        
    Returns:
        Dictionary with pipeline results and metadata
    """
    # Load config
    if config_path is None:
        config_path = "config/analysis.yaml"
    
    try:
        config = load_config(config_path)
        validate_config(config)
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        raise
    
    # Initialize logging
    initialize_memory_log()
    
    # Define paths
    samples_all_path = Path("data/processed/samples_all.csv")
    samples_valid_path = Path("data/processed/samples_valid.csv")
    results_path = Path("data/processed/test_results.csv")
    
    # Step 1: Run generation (if samples_all.csv doesn't exist)
    if not samples_all_path.exists():
        logger.info("Running generation pipeline...")
        run_generation_pipeline(config)
    
    # Step 2: Run testing (if results don't exist)
    if not results_path.exists():
        logger.info("Running tester pipeline...")
        run_tester_pipeline(samples_all_path, results_path)
    
    # Step 3: Update samples_all.csv with pass_status (T017a)
    logger.info("Updating samples with pass status...")
    update_samples_with_pass_status(samples_all_path, results_path)
    
    # Step 4: Filter valid samples (T017b)
    logger.info("Filtering valid samples...")
    filter_valid_samples(samples_all_path, samples_valid_path)
    
    # Step 5: Calculate pass rates and detect bias (T018)
    logger.info("Calculating pass rates and checking for bias...")
    pass_rates = calculate_pass_rates(samples_all_path)
    
    # Log pass rates
    for style, rate in pass_rates.items():
        logger.info(f"Pass rate for {style}: {rate:.2%}")
    
    # Check for model incapability (T018b requirement - halt if < 1%)
    if check_model_incapability(pass_rates):
        return {
            "status": "halted",
            "reason": "Model Incapability",
            "pass_rates": pass_rates
        }
    
    # Detect significant bias
    bias_flag = detect_significant_bias(pass_rates)
    
    # Inject bias flag into output CSVs
    if bias_flag:
        inject_bias_flag_to_csv(samples_all_path, bias_flag)
        inject_bias_flag_to_csv(samples_valid_path, bias_flag)
    
    # Prepare result metadata
    result = {
        "status": "completed",
        "samples_all_path": str(samples_all_path),
        "samples_valid_path": str(samples_valid_path),
        "pass_rates": pass_rates,
        "bias_detected": bias_flag,
        "bias_threshold": SUBSTANTIAL_THRESHOLD,
        "min_pass_rate_threshold": MIN_PASS_RATE_THRESHOLD
    }
    
    logger.info(f"Pipeline completed. Bias flag: {bias_flag}")
    return result

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    result = run_pipeline()
    print(json.dumps(result, indent=2, default=str))
    
    if result.get("status") == "halted":
        exit(1)
    exit(0)
