import argparse
import csv
import logging
import os
import sys
import random
from pathlib import Path

# Import from local utils
from utils.metrics import (
    calculate_all_metrics,
    validate_code_syntax,
    MetricsCalculationError
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/metrics_computation.log', mode='a')
    ]
)
logger = logging.getLogger(__name__)

# Constants
SAMPLING_LIMIT = 1000
LOG_FILE_PATH = "data/derived/sampling_log.txt"

def load_dataset(dataset_path: str):
    """
    Load the raw dataset from the specified path.
    Expects a CSV or similar structured format based on the project plan.
    """
    logger.info(f"Loading dataset from {dataset_path}")
    if not os.path.exists(dataset_path):
        raise FileNotFoundError(f"Dataset file not found: {dataset_path}")
    
    data = []
    with open(dataset_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append(row)
    
    logger.info(f"Loaded {len(data)} records")
    return data

def extract_functions_from_row(row: dict) -> list:
    """
    Extract individual code functions from a dataset row.
    Assumes the row contains a 'code' or 'function' field.
    """
    # Check for common field names based on BigCodeBench/CodeSearchNet schemas
    code_fields = ['code', 'function', 'source_code', 'content']
    code_content = None
    
    for field in code_fields:
        if field in row and row[field]:
            code_content = row[field]
            break
    
    if not code_content:
        logger.warning(f"No code content found in row: {row.get('id', 'unknown')}")
        return []
    
    # If the content is a list of functions, return as is
    if isinstance(code_content, list):
        return code_content
    
    # If it's a single string, treat as one function
    return [code_content]

def compute_metrics_for_function(code: str, function_id: str) -> dict:
    """
    Compute all complexity metrics for a single function.
    Returns a dictionary with metrics or None if computation fails.
    """
    try:
        # Validate syntax first
        if not validate_code_syntax(code):
            logger.warning(f"Invalid syntax for function {function_id}, skipping")
            return None
        
        # Calculate all metrics
        metrics = calculate_all_metrics(code)
        
        # Add metadata
        metrics['function_id'] = function_id
        metrics['code_length'] = len(code)
        
        return metrics
        
    except MetricsCalculationError as e:
        logger.error(f"Error calculating metrics for {function_id}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error for {function_id}: {e}")
        return None

def save_metrics(metrics_list: list, output_path: str):
    """
    Save computed metrics to a CSV file.
    """
    if not metrics_list:
        logger.warning("No metrics to save")
        return
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Define fieldnames based on expected metrics
    fieldnames = [
        'function_id', 'code_length',
        'cyclomatic_complexity', 'halstead_n1', 'halstead_n2',
        'halstead_N1', 'halstead_N2', 'halstead_length',
        'halstead_volume', 'halstead_difficulty', 'halstead_effort',
        'halstead_time', 'halstead_vocab_size',
        'cognitive_complexity', 'lines_of_code', 'comment_lines'
    ]
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(metrics_list)
    
    logger.info(f"Saved {len(metrics_list)} metrics to {output_path}")

def log_sampling_info(total_count: int, sampled_count: int, output_path: str):
    """
    Log sampling information to a dedicated log file.
    This satisfies T015: Cap sampling at N=1,000 and log the action.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'a', encoding='utf-8') as f:
        f.write(f"\n--- Sampling Log Entry ---\n")
        f.write(f"Timestamp: {logging.Formatter().formatTime(logging.LogRecord('', '', '', '', '', (), None))}\n")
        f.write(f"Total dataset size: {total_count}\n")
        f.write(f"Sampled count: {sampled_count}\n")
        if sampled_count >= SAMPLING_LIMIT:
            f.write(f"CAP APPLIED: Sampling limited to {SAMPLING_LIMIT} as per plan constraints.\n")
        else:
            f.write(f"CAP NOT APPLIED: Dataset size {total_count} was below the limit.\n")
        f.write(f"--------------------------------\n")
    
    logger.info(f"Sampling log written to {output_path}")

def generate_statistical_summary(metrics_list: list, output_dir: str):
    """
    Generate a basic statistical summary of the computed metrics.
    """
    if not metrics_list:
        logger.warning("No metrics for summary generation")
        return
    
    # Extract complexity values
    cc_values = [m['cyclomatic_complexity'] for m in metrics_list if 'cyclomatic_complexity' in m]
    cognitive_values = [m['cognitive_complexity'] for m in metrics_list if 'cognitive_complexity' in m]
    
    if not cc_values or not cognitive_values:
        logger.warning("Insufficient data for statistical summary")
        return
    
    summary = {
        "total_functions": len(metrics_list),
        "cyclomatic": {
            "min": min(cc_values),
            "max": max(cc_values),
            "mean": sum(cc_values) / len(cc_values),
            "median": sorted(cc_values)[len(cc_values)//2]
        },
        "cognitive": {
            "min": min(cognitive_values),
            "max": max(cognitive_values),
            "mean": sum(cognitive_values) / len(cognitive_values),
            "median": sorted(cognitive_values)[len(cognitive_values)//2]
        }
    }
    
    # Save summary to JSON
    summary_path = os.path.join(output_dir, "metrics_summary.json")
    with open(summary_path, 'w', encoding='utf-8') as f:
        import json
        json.dump(summary, f, indent=2)
    
    logger.info(f"Statistical summary saved to {summary_path}")
    return summary

def main():
    parser = argparse.ArgumentParser(description="Compute code complexity metrics for a dataset.")
    parser.add_argument("--input", type=str, required=True, help="Path to input dataset CSV")
    parser.add_argument("--output", type=str, default="data/derived/metrics.csv", help="Path to output metrics CSV")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for sampling")
    
    args = parser.parse_args()
    
    logger.info("Starting metrics computation pipeline")
    
    # Load dataset
    try:
        data = load_dataset(args.input)
    except Exception as e:
        logger.error(f"Failed to load dataset: {e}")
        sys.exit(1)
    
    total_count = len(data)
    random.seed(args.seed)
    
    # Apply sampling cap (T015 requirement)
    if total_count > SAMPLING_LIMIT:
        sampled_indices = random.sample(range(total_count), SAMPLING_LIMIT)
        sampled_data = [data[i] for i in sampled_indices]
        sampled_count = SAMPLING_LIMIT
    else:
        sampled_data = data
        sampled_count = total_count
    
    logger.info(f"Processing {sampled_count} functions (Total: {total_count})")
    
    # Compute metrics
    metrics_list = []
    for i, row in enumerate(sampled_data):
        function_id = row.get('id', f'func_{i}')
        functions = extract_functions_from_row(row)
        
        for func_code in functions:
            metrics = compute_metrics_for_function(func_code, function_id)
            if metrics:
                metrics_list.append(metrics)
        
        # Progress logging
        if (i + 1) % 100 == 0:
            logger.info(f"Processed {i + 1}/{sampled_count} rows")
    
    # Save results
    save_metrics(metrics_list, args.output)
    
    # Log sampling info (T015 requirement)
    log_sampling_info(total_count, sampled_count, LOG_FILE_PATH)
    
    # Generate summary
    generate_statistical_summary(metrics_list, os.path.dirname(args.output))
    
    logger.info("Metrics computation pipeline completed successfully")

if __name__ == "__main__":
    main()