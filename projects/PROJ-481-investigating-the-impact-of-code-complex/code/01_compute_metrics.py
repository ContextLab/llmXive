import argparse
import csv
import logging
import os
import sys
import random
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from utils.metrics import calculate_all_metrics, validate_code_syntax, MetricsCalculationError
from utils.config import get_optional_env

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('code/logs/compute_metrics.log', mode='a')
    ]
)
logger = logging.getLogger(__name__)

def load_dataset(input_path: str):
    """Load dataset from CSV or other format."""
    logger.info(f"Loading dataset from {input_path}")
    # Placeholder for actual loading logic (T012 will implement this)
    # Assuming a list of dictionaries representing code functions
    return []

def extract_functions_from_row(row: dict) -> list:
    """Extract individual code functions from a dataset row."""
    # Placeholder: In T012, this will parse the actual code content
    # Returns a list of code strings
    code_content = row.get('code', '')
    if code_content:
        return [code_content]
    return []

def compute_metrics_for_function(code: str) -> dict:
    """Compute all complexity metrics for a single function."""
    try:
        if not validate_code_syntax(code):
            logger.warning(f"Invalid syntax detected, skipping: {code[:50]}...")
            return None
        
        metrics = calculate_all_metrics(code)
        return metrics
    except MetricsCalculationError as e:
        logger.error(f"Metrics calculation error: {e}")
        return None

def save_metrics(metrics_list: list, output_path: str):
    """Save computed metrics to CSV."""
    logger.info(f"Saving metrics to {output_path}")
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        if not metrics_list:
            logger.warning("No metrics to save.")
            return
        
        writer = csv.DictWriter(f, fieldnames=metrics_list[0].keys())
        writer.writeheader()
        writer.writerows(metrics_list)

def log_sampling_info(total_count: int, sampled_count: int, output_path: str):
    """Log sampling information to a text file."""
    log_path = Path(output_path).parent / 'sampling_log.txt'
    with open(log_path, 'a') as f:
        f.write(f"Total functions: {total_count}, Sampled: {sampled_count}\n")
    logger.info(f"Sampling logged to {log_path}")

def generate_statistical_summary(metrics_list: list, output_path: str):
    """Generate a statistical summary of the metrics."""
    if not metrics_list:
        return
    
    # Placeholder for statistical summary generation
    # T014 will implement actual statistical analysis
    summary = {
        'total_functions': len(metrics_list),
        'avg_complexity': sum(m.get('cyclomatic', 0) for m in metrics_list) / len(metrics_list)
    }
    logger.info(f"Statistical summary generated: {summary}")

def main():
    parser = argparse.ArgumentParser(description='Compute complexity metrics for code functions.')
    parser.add_argument('--input', type=str, required=True,
                        help='Path to input dataset (CSV)')
    parser.add_argument('--output', type=str, default='data/derived/metrics.csv',
                        help='Path to output metrics CSV')
    parser.add_argument('--sample-size', type=int, default=1000,
                        help='Maximum number of functions to process')
    
    args = parser.parse_args()
    
    logger.info(f"Starting metric computation for {args.input}")
    
    try:
        # Load data
        data = load_dataset(args.input)
        
        # Extract and compute metrics
        metrics_list = []
        count = 0
        for row in data:
            if count >= args.sample_size:
                break
            
            functions = extract_functions_from_row(row)
            for func in functions:
                metrics = compute_metrics_for_function(func)
                if metrics:
                    metrics_list.append(metrics)
                    count += 1
        
        # Save results
        save_metrics(metrics_list, args.output)
        
        # Log sampling info
        log_sampling_info(len(data), count, args.output)
        
        # Generate summary
        generate_statistical_summary(metrics_list, args.output)
        
        logger.info("Metric computation complete.")
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
