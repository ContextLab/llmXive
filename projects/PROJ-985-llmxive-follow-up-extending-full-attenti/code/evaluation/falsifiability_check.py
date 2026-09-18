"""
T031: Implement Falsifiability Check.

Calculates the performance drop (Static vs Learned) and compares it against
the <1% threshold defined in Constitution Principle VI.
Logs the boolean result and the exact drop percentage to data/results/metrics.csv.
"""
import os
import json
import csv
import logging
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
RESULTS_DIR = "data/results"
STATIC_AGGREGATED_FILE = os.path.join(RESULTS_DIR, "static_aggregated.json")
LEARNED_AGGREGATED_FILE = os.path.join(RESULTS_DIR, "baseline_aggregated.json")
OUTPUT_FILE = os.path.join(RESULTS_DIR, "metrics.csv")
THRESHOLD_PERCENTAGE = 1.0  # 1%

def load_json_file(filepath: str) -> Dict[str, Any]:
    """Load a JSON file and return its contents."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Required aggregated results file not found: {filepath}")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def calculate_performance_drop(static_mean: float, learned_mean: float) -> float:
    """
    Calculate the performance drop percentage.
    
    Formula: ((Learned - Static) / Learned) * 100
    Positive value indicates Static is worse than Learned.
    Negative value indicates Static is better (surpassing baseline).
    """
    if learned_mean == 0:
        raise ValueError("Learned baseline mean is zero, cannot calculate percentage drop.")
    
    drop = ((learned_mean - static_mean) / learned_mean) * 100
    return drop

def main():
    """
    Execute the falsifiability check.
    
    1. Load static aggregated results (mean metric).
    2. Load learned aggregated results (mean metric).
    3. Calculate performance drop.
    4. Compare against <1% threshold.
    5. Write result to data/results/metrics.csv.
    """
    logger.info("Starting Falsifiability Check (T031)...")

    # Ensure output directory exists
    os.makedirs(RESULTS_DIR, exist_ok=True)

    try:
        # Load Static Aggregated Results
        logger.info(f"Loading static results from {STATIC_AGGREGATED_FILE}")
        static_data = load_json_file(STATIC_AGGREGATED_FILE)
        static_mean = static_data.get('mean_metric')
        if static_mean is None:
            raise ValueError("Static aggregated JSON missing 'mean_metric' key.")
        
        # Load Learned Aggregated Results
        logger.info(f"Loading learned baseline results from {LEARNED_AGGREGATED_FILE}")
        learned_data = load_json_file(LEARNED_AGGREGATED_FILE)
        learned_mean = learned_data.get('mean_metric')
        if learned_mean is None:
            raise ValueError("Learned aggregated JSON missing 'mean_metric' key.")

        logger.info(f"Static Mean: {static_mean:.4f}")
        logger.info(f"Learned Mean: {learned_mean:.4f}")

        # Calculate Drop
        drop_percentage = calculate_performance_drop(static_mean, learned_mean)
        is_falsified = drop_percentage >= THRESHOLD_PERCENTAGE

        logger.info(f"Performance Drop: {drop_percentage:.4f}%")
        logger.info(f"Threshold: {THRESHOLD_PERCENTAGE}%")
        logger.info(f"Result: {'FALSIFIED (Drop >= 1%)' if is_falsified else 'NOT FALSIFIED (Drop < 1%)'}")

        # Write to CSV
        file_exists = os.path.exists(OUTPUT_FILE)
        with open(OUTPUT_FILE, mode='a', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['task_id', 'metric_type', 'static_mean', 'learned_mean', 'drop_percentage', 'threshold', 'is_falsified']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            if not file_exists:
                writer.writeheader()

            writer.writerow({
                'task_id': 'T031',
                'metric_type': 'perplexity_or_exact_match', # Context dependent, generic label
                'static_mean': f"{static_mean:.6f}",
                'learned_mean': f"{learned_mean:.6f}",
                'drop_percentage': f"{drop_percentage:.6f}",
                'threshold': f"{THRESHOLD_PERCENTAGE}",
                'is_falsified': str(is_falsified)
            })

        logger.info(f"Successfully wrote results to {OUTPUT_FILE}")

    except FileNotFoundError as e:
        logger.error(f"Data dependency missing: {e}")
        raise
    except Exception as e:
        logger.error(f"Error during falsifiability check: {e}")
        raise

if __name__ == "__main__":
    main()