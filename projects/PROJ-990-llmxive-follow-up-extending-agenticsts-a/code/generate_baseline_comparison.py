"""
Task T022: Generate summary CSV output for baseline comparison.

Reads simulation logs from T017 (Dynamic), T019 (Static), and T020 (Random).
Aggregates win_rate and token usage metrics per condition.
Calculates standard deviation of token usage to satisfy SC-004.
Output: data/processed/baseline_comparison.csv
"""

import os
import sys
import json
import logging
import pandas as pd
from pathlib import Path
from typing import Dict, Any, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_simulation_data(file_path: str) -> pd.DataFrame:
    """
    Load simulation logs from a JSON file and return a DataFrame.
    Expected schema in JSON: list of records with 'trajectory_id', 'win' (bool), 'tokens_used' (int).
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Simulation log file not found: {file_path}")

    with open(file_path, 'r') as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError(f"Expected list of records in {file_path}, got {type(data)}")

    df = pd.DataFrame(data)

    # Ensure required columns exist
    required_cols = ['trajectory_id', 'win', 'tokens_used']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in {file_path}: {missing_cols}")

    # Normalize win column to boolean if needed
    if df['win'].dtype == object:
        df['win'] = df['win'].astype(str).str.lower().map({'true': True, 'false': False, '1': True, '0': False})

    return df

def generate_baseline_comparison(
    dynamic_path: str,
    static_path: str,
    random_path: str,
    output_path: str
) -> None:
    """
    Aggregate results from Dynamic, Static, and Random baselines and write to CSV.

    Schema: condition, win_rate, avg_tokens, std_dev_tokens
    """
    # Load data
    logger.info(f"Loading dynamic simulation data from {dynamic_path}")
    df_dynamic = load_simulation_data(dynamic_path)
    df_dynamic['condition'] = 'dynamic'

    logger.info(f"Loading static simulation data from {static_path}")
    df_static = load_simulation_data(static_path)
    df_static['condition'] = 'static'

    logger.info(f"Loading random simulation data from {random_path}")
    df_random = load_simulation_data(random_path)
    df_random['condition'] = 'random'

    # Combine all data
    df_all = pd.concat([df_dynamic, df_static, df_random], ignore_index=True)

    # Calculate metrics per condition
    # win_rate: mean of boolean 'win' column
    # avg_tokens: mean of 'tokens_used'
    # std_dev_tokens: std of 'tokens_used'
    aggregations = {
        'win': 'mean',
        'tokens_used': ['mean', 'std']
    }

    summary = df_all.groupby('condition').agg(aggregations)

    # Flatten column names
    summary.columns = ['win_rate', 'avg_tokens', 'std_dev_tokens']

    # Reset index to make 'condition' a column
    summary = summary.reset_index()

    # Ensure output directory exists
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)

    # Write to CSV
    summary.to_csv(output_path, index=False)

    logger.info(f"Baseline comparison written to {output_path}")
    logger.info(f"Summary:\n{summary.to_string()}")

def main():
    """Main entry point for T022."""
    # Define paths relative to project root
    project_root = Path(__file__).parent.parent
    processed_dir = project_root / "data" / "processed"

    dynamic_path = processed_dir / "simulation_logs_dynamic.json"
    static_path = processed_dir / "simulation_logs_static.json"
    random_path = processed_dir / "simulation_logs_random.json"
    output_path = processed_dir / "baseline_comparison.csv"

    # Check if input files exist
    missing_inputs = []
    for path in [dynamic_path, static_path, random_path]:
        if not path.exists():
            missing_inputs.append(path)

    if missing_inputs:
        logger.error("Missing required input files:")
        for p in missing_inputs:
            logger.error(f"  - {p}")
        logger.error("Please ensure T017, T019, and T020 have completed successfully.")
        sys.exit(1)

    try:
        generate_baseline_comparison(
            str(dynamic_path),
            str(static_path),
            str(random_path),
            str(output_path)
        )
        logger.info("T022 completed successfully.")
    except Exception as e:
        logger.error(f"Error generating baseline comparison: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
