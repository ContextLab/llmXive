import os
import json
import logging
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define paths relative to project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
DYNAMIC_LOG = PROCESSED_DIR / "simulation_logs_dynamic.json"
STATIC_LOG = PROCESSED_DIR / "simulation_logs_static.json"
RANDOM_LOG = PROCESSED_DIR / "simulation_logs_random.json"
OUTPUT_FILE = PROCESSED_DIR / "baseline_comparison.csv"

def load_simulation_data(log_path: Path) -> List[Dict[str, Any]]:
    """Load simulation results from a JSON file."""
    if not log_path.exists():
        raise FileNotFoundError(f"Simulation log not found: {log_path}")
    
    with open(log_path, 'r') as f:
        data = json.load(f)
    
    # Ensure data is a list of records
    if isinstance(data, dict) and 'results' in data:
        return data['results']
    elif isinstance(data, list):
        return data
    else:
        raise ValueError(f"Unexpected data format in {log_path}")

def calculate_aggregates(records: List[Dict[str, Any]], condition_name: str) -> Dict[str, float]:
    """
    Calculate mean win_rate, mean tokens, and std_dev of tokens for a condition.
    SC-004 requires standard deviation of token savings/usage.
    """
    if not records:
        logger.warning(f"No records found for condition {condition_name}")
        return {
            "condition": condition_name,
            "win_rate": 0.0,
            "avg_tokens": 0.0,
            "std_dev_tokens": 0.0
        }

    win_rates = [r.get("win_rate", 0.0) for r in records if "win_rate" in r]
    tokens = [r.get("tokens_used", r.get("token_count", 0)) for r in records if "tokens_used" in r or "token_count" in r]

    # Calculate mean win rate
    mean_win_rate = sum(win_rates) / len(win_rates) if win_rates else 0.0

    # Calculate mean and std dev of tokens
    mean_tokens = sum(tokens) / len(tokens) if tokens else 0.0
    
    std_dev_tokens = 0.0
    if len(tokens) > 1:
        variance = sum((t - mean_tokens) ** 2 for t in tokens) / (len(tokens) - 1)
        std_dev_tokens = variance ** 0.5

    return {
        "condition": condition_name,
        "win_rate": mean_win_rate,
        "avg_tokens": mean_tokens,
        "std_dev_tokens": std_dev_tokens
    }

def generate_baseline_comparison() -> None:
    """
    Main function to generate the baseline comparison CSV.
    Loads dynamic, static, and random simulation logs, aggregates metrics,
    and writes the result to data/processed/baseline_comparison.csv.
    """
    logger.info("Starting baseline comparison generation.")
    
    # Ensure output directory exists
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    try:
        # Load data for all three conditions
        dynamic_data = load_simulation_data(DYNAMIC_LOG)
        static_data = load_simulation_data(STATIC_LOG)
        random_data = load_simulation_data(RANDOM_LOG)

        # Calculate aggregates for each
        dynamic_agg = calculate_aggregates(dynamic_data, "dynamic")
        static_agg = calculate_aggregates(static_data, "static")
        random_agg = calculate_aggregates(random_data, "random")

        # Create DataFrame
        df = pd.DataFrame([dynamic_agg, static_agg, random_agg])
        
        # Ensure column order matches schema
        df = df[["condition", "win_rate", "avg_tokens", "std_dev_tokens"]]

        # Round for readability (optional, but good practice)
        df["win_rate"] = df["win_rate"].round(4)
        df["avg_tokens"] = df["avg_tokens"].round(2)
        df["std_dev_tokens"] = df["std_dev_tokens"].round(2)

        # Write to CSV
        df.to_csv(OUTPUT_FILE, index=False)
        
        logger.info(f"Successfully wrote baseline comparison to {OUTPUT_FILE}")
        logger.info(f"Output content:\n{df.to_string()}")

    except FileNotFoundError as e:
        logger.error(f"Missing required simulation data: {e}")
        raise
    except Exception as e:
        logger.error(f"Error generating baseline comparison: {e}")
        raise

def main():
    generate_baseline_comparison()

if __name__ == "__main__":
    main()