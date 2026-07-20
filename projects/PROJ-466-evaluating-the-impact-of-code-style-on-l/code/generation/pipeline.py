import os
import csv
import tempfile
import shutil
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd
from utils.logger import log_generation_error
from generation.buffer_writer import create_sample_buffer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('data/logs/pipeline.log')
    ]
)
logger = logging.getLogger(__name__)

def ensure_output_dirs():
    """Ensure all required output directories exist."""
    dirs = [
        'data/processed',
        'data/logs',
        'data/raw/humaneval',
        'data/processed/raw_samples'
    ]
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)
    logger.info("Output directories ensured")

def write_samples_atomic(samples: List[Dict[str, Any]], output_path: str) -> None:
    """
    Write samples to CSV atomically using a temporary file and rename.
    This ensures data integrity even if the process is interrupted.
    """
    ensure_output_dirs()
    
    # Create temporary file in the same directory
    temp_path = output_path + '.tmp'
    
    try:
        with open(temp_path, 'w', newline='', encoding='utf-8') as f:
            if samples:
                writer = csv.DictWriter(f, fieldnames=samples[0].keys())
                writer.writeheader()
                writer.writerows(samples)
            else:
                # Write empty file with headers if no samples
                writer = csv.DictWriter(f, fieldnames=['task_id', 'style', 'code', 'pass_status', 'generation_time', 'error'])
                writer.writeheader()
        
        # Atomic rename
        shutil.move(temp_path, output_path)
        logger.info(f"Samples written atomically to {output_path} ({len(samples)} samples)")
        
    except Exception as e:
        # Clean up temp file if it exists
        if os.path.exists(temp_path):
            os.remove(temp_path)
        logger.error(f"Failed to write samples atomically: {e}")
        raise

def update_samples_with_pass_status(samples_path: str, test_results: List[Dict]) -> None:
    """
    Update samples with pass/fail status from test results.
    """
    if not os.path.exists(samples_path):
        raise FileNotFoundError(f"Samples file not found: {samples_path}")
    
    # Create a lookup for test results
    result_lookup = {}
    for res in test_results:
        key = (res['task_id'], res['style'])
        result_lookup[key] = res['passed']
    
    # Read and update
    df = pd.read_csv(samples_path)
    
    def get_pass_status(row):
        key = (row['task_id'], row['style'])
        return result_lookup.get(key, False)
    
    df['pass_status'] = df.apply(get_pass_status, axis=1)
    
    # Write back
    df.to_csv(samples_path, index=False)
    logger.info(f"Updated {len(df)} samples with pass status")

def filter_valid_samples(input_path: str, output_path: str) -> pd.DataFrame:
    """
    Filter samples to keep only those with pass_status=True.
    Creates a new file (does not modify input).
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    df = pd.read_csv(input_path)
    
    if 'pass_status' not in df.columns:
        logger.warning("pass_status column not found, no filtering applied")
        df.to_csv(output_path, index=False)
        return df
    
    df_valid = df[df['pass_status'] == True].copy()
    df_valid.to_csv(output_path, index=False)
    
    logger.info(f"Filtered {len(df)} samples to {len(df_valid)} valid samples -> {output_path}")
    return df_valid

def calculate_pass_rates(samples_path: str) -> Dict[str, float]:
    """
    Calculate pass rates for each style group.
    """
    if not os.path.exists(samples_path):
        raise FileNotFoundError(f"Samples file not found: {samples_path}")
    
    df = pd.read_csv(samples_path)
    
    if df.empty:
        return {}
    
    if 'pass_status' not in df.columns:
        logger.warning("pass_status column not found")
        return {}
    
    pass_rates = {}
    for style in df['style'].unique():
        style_df = df[df['style'] == style]
        total = len(style_df)
        passed = style_df['pass_status'].sum()
        pass_rates[style] = passed / total if total > 0 else 0.0
    
    logger.info(f"Pass rates calculated: {pass_rates}")
    return pass_rates

def check_model_incapability(pass_rates: Dict[str, float], threshold: float = 0.01) -> bool:
    """
    Check if any style group has a pass rate below the threshold.
    Returns True if model incapability is detected.
    """
    for style, rate in pass_rates.items():
        if rate < threshold:
            logger.error(f"Model Incapability: Pass rate < 1% for style {style}: {rate:.4f}")
            return True
    
    logger.info("Model capability check passed")
    return False

def detect_significant_bias(pass_rates: Dict[str, float], threshold: float = 0.10) -> bool:
    """
    Detect if the difference between any two style groups exceeds the threshold.
    Returns True if potentially biased.
    """
    styles = list(pass_rates.keys())
    for i in range(len(styles)):
        for j in range(i + 1, len(styles)):
            diff = abs(pass_rates[styles[i]] - pass_rates[styles[j]])
            if diff > threshold:
                logger.warning(f"Potentially Biased: Difference between {styles[i]} and {styles[j]} is {diff:.4f} > {threshold}")
                return True
    
    logger.info("Bias check passed")
    return False

def inject_bias_flag_to_csv(csv_path: str, bias_flag: bool) -> None:
    """
    Inject a bias flag column into the CSV file.
    """
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"CSV file not found: {csv_path}")
    
    df = pd.read_csv(csv_path)
    df['bias_flag'] = bias_flag
    df.to_csv(csv_path, index=False)
    logger.info(f"Bias flag {'injected' if bias_flag else 'added as False'} to {csv_path}")

def ensure_samples_all_exists(samples_path: str) -> bool:
    """
    Check if samples_all.csv exists and is not empty.
    """
    if not os.path.exists(samples_path):
        logger.error(f"Required file not found: {samples_path}")
        return False
    
    df = pd.read_csv(samples_path)
    if df.empty:
        logger.error(f"File is empty: {samples_path}")
        return False
    
    return True

def run_pipeline(generation_buffer: List[Dict], samples_all_path: str, samples_valid_path: str) -> Dict[str, Any]:
    """
    Run the full generation pipeline: write samples, filter, calculate rates, check flags.
    """
    ensure_output_dirs()
    
    # Step 1: Write samples atomically
    write_samples_atomic(generation_buffer, samples_all_path)
    
    # Step 2: Filter valid samples (T017a)
    if not ensure_samples_all_exists(samples_all_path):
        raise RuntimeError("samples_all.csv is missing or empty after writing")
    
    filter_valid_samples(samples_all_path, samples_valid_path)
    
    # Step 3: Calculate pass rates (T018)
    pass_rates = calculate_pass_rates(samples_all_path)
    
    # Step 4: Check model incapability
    incapability_flag = check_model_incapability(pass_rates)
    
    # Step 5: Detect significant bias (T019)
    bias_flag = detect_significant_bias(pass_rates)
    
    # Step 6: Inject bias flag into valid samples CSV
    inject_bias_flag_to_csv(samples_valid_path, bias_flag)
    
    logger.info(f"Pipeline completed. Incapability: {incapability_flag}, Bias: {bias_flag}")
    
    return {
        'pass_rates': pass_rates,
        'incapability_flag': incapability_flag,
        'bias_flag': bias_flag,
        'samples_all_path': samples_all_path,
        'samples_valid_path': samples_valid_path
    }

if __name__ == "__main__":
    # Example usage for testing
    logger.info("Running pipeline as standalone script")
    # In a real scenario, generation_buffer would come from the generation step
    # For now, we assume the pipeline is called from main.py
    logger.info("Pipeline module loaded successfully")
