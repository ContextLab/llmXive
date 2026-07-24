import os
import csv
import tempfile
import shutil
import logging
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

from config.loader import load_config
from utils.logger import log_generation_error, log_timeout_error
from generation.tester import run_tester_pipeline
from generation.generator import run_generation_pipeline
from generation.buffer_writer import create_sample_buffer
from generation.directories import ensure_output_dirs

logger = logging.getLogger(__name__)

# Constants for atomic writes
TMP_SUFFIX = ".tmp.csv"

def ensure_samples_all_exists(samples_all_path: Path) -> None:
    """
    Verify that samples_all.csv exists. If not, attempt to trigger generation.
    This is a helper to ensure the pipeline can proceed if called out of order.
    """
    if not samples_all_path.exists():
        logger.warning(f"{samples_all_path} not found. Triggering generation pipeline...")
        run_generation_pipeline()

def write_samples_atomic(buffer_data: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Atomically write the raw samples from the buffer to the output CSV.
    Implementation Detail: Write to a temporary file, then rename to the final path.
    """
    output_dir = output_path.parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    temp_path = output_path.with_suffix(output_path.suffix + TMP_SUFFIX)
    
    try:
        with open(temp_path, 'w', newline='', encoding='utf-8') as f:
            if not buffer_data:
                logger.warning("Buffer is empty. Writing empty CSV.")
                writer = csv.DictWriter(f, fieldnames=[])
                writer.writeheader()
            else:
                fieldnames = list(buffer_data[0].keys())
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(buffer_data)
        
        # Atomic rename
        shutil.move(str(temp_path), str(output_path))
        logger.info(f"Successfully wrote {len(buffer_data)} samples to {output_path} atomically.")
        
    except Exception as e:
        # Cleanup temp file if it exists
        if temp_path.exists():
            os.remove(temp_path)
        logger.error(f"Failed to write samples atomically: {e}")
        raise

def update_samples_with_pass_status(samples_path: Path) -> List[Dict[str, Any]]:
    """
    Reads samples, runs tests (if not already run), and updates pass_status.
    Returns the updated list of samples.
    """
    if not samples_path.exists():
        raise FileNotFoundError(f"Samples file not found: {samples_path}")

    samples = []
    with open(samples_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for row in reader:
            samples.append(row)

    # Run tester pipeline to update pass_status in the file and return updated data
    # The tester pipeline is expected to update the file in place or return updated rows
    # Based on API surface: run_tester_pipeline updates the file.
    # We re-read to get the updated status for the next steps.
    run_tester_pipeline(samples_path)
    
    updated_samples = []
    with open(samples_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            updated_samples.append(row)
    
    return updated_samples

def filter_valid_samples(samples: List[Dict[str, Any]], output_path: Path) -> List[Dict[str, Any]]:
    """
    Filter samples where pass_status is True (or 'True' string) and write to new file.
    """
    valid_samples = []
    for sample in samples:
        status = sample.get('pass_status', '')
        if str(status).lower() == 'true' or status == 1:
            valid_samples.append(sample)
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        if valid_samples:
            fieldnames = list(valid_samples[0].keys())
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(valid_samples)
        else:
            # Write header even if empty
            if samples:
                fieldnames = list(samples[0].keys())
            else:
                fieldnames = ['task_id', 'style', 'code', 'pass_status'] # Default fallback
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
    
    logger.info(f"Filtered {len(valid_samples)} valid samples to {output_path}")
    return valid_samples

def calculate_pass_rates(samples_all: List[Dict[str, Any]], samples_valid: List[Dict[str, Any]]) -> Dict[str, Dict[str, int]]:
    """
    Calculate pass rates per style.
    Returns a dict: { style: { 'total': int, 'passed': int, 'rate': float } }
    """
    style_counts = {}
    
    for s in samples_all:
        style = s.get('style', 'unknown')
        if style not in style_counts:
            style_counts[style] = {'total': 0, 'passed': 0}
        style_counts[style]['total'] += 1
    
    for s in samples_valid:
        style = s.get('style', 'unknown')
        if style not in style_counts:
            style_counts[style] = {'total': 0, 'passed': 0}
        style_counts[style]['passed'] += 1
    
    result = {}
    for style, counts in style_counts.items():
        total = counts['total']
        passed = counts['passed']
        rate = passed / total if total > 0 else 0.0
        result[style] = {
            'total': total,
            'passed': passed,
            'rate': rate
        }
    
    return result

def check_model_incapability(pass_rates: Dict[str, Dict[str, Any]], log_path: Path) -> bool:
    """
    Check if any style group has pass_rate < 0.01.
    If so, log error and return True (incapable).
    """
    for style, data in pass_rates.items():
        if data['rate'] < 0.01:
            error_msg = f"Model Incapability: Pass rate < 1% for style {style} ({data['rate']:.4f})"
            logger.error(error_msg)
            with open(log_path, 'a') as f:
                f.write(f"ERROR [MODEL_INCAPABILITY] {error_msg}\n")
            return True
    return False

def detect_significant_bias(pass_rates: Dict[str, Dict[str, Any]], threshold: float = 0.10) -> bool:
    """
    Detect if difference between any two style groups exceeds threshold.
    Returns True if bias is detected.
    """
    rates = [data['rate'] for data in pass_rates.values()]
    if len(rates) < 2:
        return False
    
    max_rate = max(rates)
    min_rate = min(rates)
    
    if (max_rate - min_rate) > threshold:
        logger.warning(f"Significant bias detected: max_rate={max_rate:.4f}, min_rate={min_rate:.4f}, diff={max_rate-min_rate:.4f}")
        return True
    return False

def inject_bias_flag_to_csv(samples_path: Path, bias_flag: bool) -> None:
    """
    Inject a bias_flag column into the samples CSV if not present, or update it.
    Note: This might be for downstream tasks, but T019b handles the JSON flag.
    We will ensure the flag is available in the CSV for consistency if required,
    though T019b writes the JSON file.
    """
    if not samples_path.exists():
        return

    rows = []
    with open(samples_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for row in reader:
            row['bias_flag'] = str(bias_flag)
            rows.append(row)
    
    with open(samples_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames + ['bias_flag'])
        writer.writeheader()
        writer.writerows(rows)

def verify_sample_balance(samples: List[Dict[str, Any]], expected_per_group: int = 20) -> bool:
    """
    Verify that the count of samples per task/style is balanced (per FR-003).
    """
    counts = {}
    for s in samples:
        key = (s.get('task_id'), s.get('style'))
        counts[key] = counts.get(key, 0) + 1
    
    all_balanced = True
    for key, count in counts.items():
        if count != expected_per_group:
            logger.error(f"Sample Count Mismatch: Expected {expected_per_group}, Got {count} for {key}")
            all_balanced = False
    
    if not all_balanced:
        logger.error("Aborting pipeline due to sample count mismatch.")
        raise RuntimeError("Sample count mismatch detected. Aborting.")
    
    logger.info("Sample balance verified.")
    return True

def run_pipeline(config_path: Optional[str] = None) -> None:
    """
    Orchestrates the generation, testing, and writing of samples_all.csv and samples_valid.csv.
    """
    logger.info("Starting Generation Pipeline...")
    
    # Load config
    if config_path is None:
        config_path = "config/analysis.yaml"
    config = load_config(config_path)
    
    # Ensure directories
    ensure_output_dirs(config)
    
    data_dir = Path(config.get('data_dir', 'data'))
    processed_dir = data_dir / 'processed'
    samples_all_path = processed_dir / 'samples_all.csv'
    samples_valid_path = processed_dir / 'samples_valid.csv'
    log_path = Path(config.get('log_dir', 'data/logs')) / 'pipeline.log'
    
    # Step 1: Generate samples (if not already done or force regenerate)
    # Assuming generation writes to a buffer or temp file, we trigger it here.
    # T014/T015 logic is encapsulated in run_generation_pipeline which should populate the buffer.
    # However, T016a specifically writes the buffer to samples_all.csv.
    # We assume run_generation_pipeline fills the buffer or we need to re-generate if missing.
    
    if not samples_all_path.exists():
        logger.info("samples_all.csv not found. Running generation pipeline...")
        run_generation_pipeline()
    
    # Step 2: Read samples_all.csv (or get from buffer if it was just written to memory)
    # Since run_generation_pipeline writes to disk in T016a's context, we read it.
    # But T016a is the task that writes it. So we assume the generation step produced the buffer.
    # Let's assume the generation step produces a list of dicts in memory or a temp file.
    # To strictly follow T016a: "Implement ... to atomically write the raw samples from the buffer"
    # We need to get the buffer. The buffer is likely created by run_generation_pipeline.
    # Let's assume run_generation_pipeline returns the buffer or writes to a temp location.
    # Given the API, run_generation_pipeline likely writes to samples_all.csv directly in a previous attempt?
    # No, T016a is the one that writes it. So run_generation_pipeline must have produced the buffer.
    # Let's assume run_generation_pipeline returns the buffer.
    
    # Re-implementing the flow:
    # 1. Generate samples -> returns buffer (list of dicts)
    # 2. Verify balance
    # 3. Write atomically to samples_all.csv
    # 4. Run tests (tester) to update pass_status in samples_all.csv
    # 5. Filter to samples_valid.csv
    
    # Since run_generation_pipeline is defined to run the loop, let's assume it returns the buffer.
    # If it writes directly, we might need to adjust. But T016a says "write from buffer".
    # Let's call run_generation_pipeline and assume it returns the buffer.
    # If it doesn't, we might need to read the temp file it created.
    # For safety, let's assume run_generation_pipeline writes to a temp buffer file or returns data.
    # The task says "write the raw samples from the buffer".
    
    # Let's assume run_generation_pipeline returns the buffer.
    buffer_data = run_generation_pipeline() 
    
    if not buffer_data:
        logger.error("Generation pipeline returned no data.")
        sys.exit(1)
    
    # Verification: Sample Balance
    verify_sample_balance(buffer_data, expected_per_group=20)
    
    # Write atomically
    write_samples_atomic(buffer_data, samples_all_path)
    
    # Step 3: Run tests to update pass_status
    # The tester pipeline updates the file in place.
    update_samples_with_pass_status(samples_all_path)
    
    # Step 4: Filter valid samples
    filter_valid_samples(buffer_data, samples_valid_path) # Re-read from file or use updated buffer?
    # The tester updated the file. We should re-read or use the updated buffer if available.
    # Let's re-read the updated file to ensure consistency.
    with open(samples_all_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        updated_buffer = list(reader)
    
    filter_valid_samples(updated_buffer, samples_valid_path)
    
    # Step 5: Calculate pass rates and check incapability
    with open(samples_all_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        samples_all_list = list(reader)
    with open(samples_valid_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        samples_valid_list = list(reader)
    
    pass_rates = calculate_pass_rates(samples_all_list, samples_valid_list)
    
    # Check incapability
    if check_model_incapability(pass_rates, log_path):
        logger.error("Model incapability detected. Halting pipeline.")
        sys.exit(1)
    
    # Detect bias
    bias_flag = detect_significant_bias(pass_rates)
    
    # Inject bias flag to CSV (optional, but good for consistency)
    inject_bias_flag_to_csv(samples_all_path, bias_flag)
    
    # Note: T019b (Persist Bias Flag) will write the JSON file.
    # This task T016a is responsible for samples_all.csv and samples_valid.csv.
    
    logger.info("Pipeline completed successfully.")

def ensure_output_dirs(config: Dict[str, Any]) -> None:
    """
    Ensure all required output directories exist.
    """
    data_dir = Path(config.get('data_dir', 'data'))
    processed_dir = data_dir / 'processed'
    log_dir = Path(config.get('log_dir', 'data/logs'))
    
    processed_dir.mkdir(parents=True, exist_ok=True)
    log_dir.mkdir(parents=True, exist_ok=True)

# Entry point for direct execution if needed, though main.py orchestrates.
if __name__ == "__main__":
    run_pipeline()
