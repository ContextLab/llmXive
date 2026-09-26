import os
import json
import csv
import logging
import argparse
from typing import Dict, Any, Optional, Tuple
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data/logs/falsifiability_check.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def get_project_root() -> Path:
    """Get the project root directory (parent of code/)."""
    return Path(__file__).resolve().parent.parent.parent

def load_json_file(file_path: str) -> Dict[str, Any]:
    """Load a JSON file and return its contents as a dictionary."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Required input file not found: {file_path}")
    
    with open(file_path, 'r') as f:
        return json.load(f)

def load_yaml_config(file_path: str) -> Dict[str, Any]:
    """Load a simple YAML config file (handles key: value format)."""
    config = {}
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Config file not found: {file_path}")
    
    with open(file_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip()
                # Try to parse as number
                try:
                    if '.' in value:
                        config[key] = float(value)
                    else:
                        config[key] = int(value)
                except ValueError:
                    config[key] = value
    return config

def calculate_performance_drop(
    learned_mean: float, 
    static_mean: float, 
    metric_name: str = "perplexity"
) -> Tuple[float, bool]:
    """
    Calculate the relative performance drop between Learned and Static baselines.
    
    Formula: (Learned_Mean - Static_Mean) / Learned_Mean
    
    Args:
        learned_mean: Mean metric value from the learned (RTPurbo) baseline.
        static_mean: Mean metric value from the static heuristic baseline.
        metric_name: Name of the metric being compared (for logging).
    
    Returns:
        Tuple of (performance_drop, is_valid)
        - performance_drop: The calculated relative drop.
        - is_valid: True if drop <= threshold, False otherwise.
    
    Raises:
        ZeroDivisionError: If learned_mean is near zero (< 1e-6).
    """
    # Zero-division guard
    if abs(learned_mean) < 1e-6:
        logger.error(f"Learned mean for {metric_name} is near zero ({learned_mean}). "
                     "Cannot calculate relative performance drop. Skipping calculation.")
        raise ZeroDivisionError(f"Learned mean for {metric_name} is too close to zero: {learned_mean}")
    
    performance_drop = (learned_mean - static_mean) / learned_mean
    return performance_drop

def main():
    """
    Main entry point for the Falsifiability Check (Task T031).
    
    Loads aggregated metrics from T026b (Learned) and T027b (Static),
    reads the threshold from T031a config, calculates the performance drop,
    and logs the result to data/results/metrics.csv.
    """
    project_root = get_project_root()
    
    # Define paths
    learned_aggregated_path = project_root / "data" / "results" / "baseline_aggregated.json"
    static_aggregated_path = project_root / "data" / "results" / "static_eval_aggregated.json"
    threshold_config_path = project_root / "data" / "config" / "threshold.yaml"
    output_csv_path = project_root / "data" / "results" / "metrics.csv"
    
    logger.info("Starting Falsifiability Check (T031)...")
    
    # 1. Load Threshold Configuration
    try:
        config = load_yaml_config(str(threshold_config_path))
        drop_threshold = config.get('drop_threshold', 0.01)
        logger.info(f"Loaded drop_threshold from config: {drop_threshold}")
    except FileNotFoundError as e:
        logger.error(f"Configuration file missing: {e}")
        return 1
    
    # 2. Load Learned Baseline Aggregated Results (T026b)
    try:
        learned_data = load_json_file(str(learned_aggregated_path))
        # Assume the metric key is 'mean_perplexity' or similar based on T026b schema
        learned_mean = learned_data.get('mean_perplexity')
        if learned_mean is None:
            # Fallback to generic mean_metric if specific key missing
            learned_mean = learned_data.get('mean_metric')
        
        if learned_mean is None:
            raise ValueError("Could not find 'mean_perplexity' or 'mean_metric' in learned aggregated data.")
        
        logger.info(f"Loaded Learned Mean Perplexity: {learned_mean}")
    except (FileNotFoundError, ValueError) as e:
        logger.error(f"Failed to load Learned baseline data: {e}")
        return 1
    
    # 3. Load Static Heuristic Aggregated Results (T027b)
    try:
        static_data = load_json_file(str(static_aggregated_path))
        static_mean = static_data.get('mean_perplexity')
        if static_mean is None:
            static_mean = static_data.get('mean_metric')
        
        if static_mean is None:
            raise ValueError("Could not find 'mean_perplexity' or 'mean_metric' in static aggregated data.")
        
        logger.info(f"Loaded Static Mean Perplexity: {static_mean}")
    except (FileNotFoundError, ValueError) as e:
        logger.error(f"Failed to load Static baseline data: {e}")
        return 1
    
    # 4. Calculate Performance Drop
    try:
        performance_drop = calculate_performance_drop(learned_mean, static_mean)
        logger.info(f"Calculated Performance Drop: {performance_drop:.6f} ({performance_drop*100:.4f}%)")
    except ZeroDivisionError as e:
        logger.error(f"Zero-division error encountered: {e}")
        # Log the error state to CSV as well
        with open(output_csv_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['task_id', 'status', 'learned_mean', 'static_mean', 'performance_drop', 'threshold', 'result', 'error_message'])
            writer.writerow(['T031', 'failed_zero_div', learned_mean, static_mean, 'N/A', drop_threshold, 'skipped', str(e)])
        return 1
    
    # 5. Compare against Threshold
    is_valid = performance_drop <= drop_threshold
    status = "passed" if is_valid else "failed"
    logger.info(f"Threshold: {drop_threshold} | Result: {status}")
    
    # 6. Write Results to CSV
    output_csv_path.parent.mkdir(parents=True, exist_ok=True)
    
    file_exists = os.path.exists(output_csv_path)
    
    with open(output_csv_path, 'a', newline='') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['task_id', 'status', 'learned_mean', 'static_mean', 'performance_drop', 'threshold', 'result', 'error_message'])
        
        writer.writerow([
            'T031',
            'completed',
            learned_mean,
            static_mean,
            f"{performance_drop:.6f}",
            drop_threshold,
            status,
            ''
        ])
    
    logger.info(f"Results written to {output_csv_path}")
    logger.info("Falsifiability Check (T031) completed successfully.")
    return 0

if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)
