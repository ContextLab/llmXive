"""
Generate summary CSV output for baseline comparison.
Task T022: Generate summary CSV output in `data/processed/baseline_comparison.csv`.
Schema: condition, win_rate, avg_tokens, std_dev_tokens.
Aggregation Logic: Mean of win_rate and token columns grouped by condition;
Calculate standard deviation of token savings per condition to satisfy SC-004.
Depends on: T021 (stats.py for aggregation logic).
"""

import os
import sys
import json
import logging
import pandas as pd
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_simulation_data():
    """
    Load simulation results from T017 (dynamic), T019 (static), and T020 (random).
    Returns a dictionary of DataFrames keyed by condition.
    """
    data_dir = Path("data/processed")
    conditions = {
        "dynamic": data_dir / "simulation_logs_dynamic.json",
        "static": data_dir / "simulation_logs_static.json",
        "random": data_dir / "simulation_logs_random.json"
    }

    simulation_data = {}

    for condition, file_path in conditions.items():
        if not file_path.exists():
            logger.error(f"Missing required input file for {condition}: {file_path}")
            raise FileNotFoundError(f"Missing required input file: {file_path}")

        try:
            with open(file_path, 'r') as f:
                logs = json.load(f)
            
            # Convert list of dicts to DataFrame
            df = pd.DataFrame(logs)
            
            # Ensure required columns exist
            required_cols = ['win', 'tokens_used']
            for col in required_cols:
                if col not in df.columns:
                    logger.error(f"Missing required column '{col}' in {condition} data")
                    raise ValueError(f"Missing required column '{col}' in {condition} data")
            
            # Convert win (bool/int) to win_rate (0.0 or 1.0)
            df['win_rate'] = df['win'].astype(float)
            
            simulation_data[condition] = df
            logger.info(f"Loaded {len(df)} records for {condition}")
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON for {condition}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error loading {condition} data: {e}")
            raise

    return simulation_data

def generate_baseline_comparison(simulation_data):
    """
    Aggregate simulation data by condition and compute statistics.
    Returns a DataFrame with columns: condition, win_rate, avg_tokens, std_dev_tokens.
    """
    results = []

    for condition, df in simulation_data.items():
        # Calculate win rate (mean of win_rate column)
        win_rate = df['win_rate'].mean()
        
        # Calculate average tokens used
        avg_tokens = df['tokens_used'].mean()
        
        # Calculate standard deviation of tokens used (SC-004 requirement)
        std_dev_tokens = df['tokens_used'].std()
        
        results.append({
            'condition': condition,
            'win_rate': win_rate,
            'avg_tokens': avg_tokens,
            'std_dev_tokens': std_dev_tokens
        })

    return pd.DataFrame(results)

def main():
    """Main entry point for T022."""
    logger.info("Starting T022: Generate baseline comparison CSV")

    try:
        # Load simulation data from T017, T019, T020
        simulation_data = load_simulation_data()

        # Generate aggregated comparison
        comparison_df = generate_baseline_comparison(simulation_data)

        # Ensure output directory exists
        output_dir = Path("data/processed")
        output_dir.mkdir(parents=True, exist_ok=True)

        # Write to CSV
        output_path = output_dir / "baseline_comparison.csv"
        comparison_df.to_csv(output_path, index=False)

        logger.info(f"Successfully wrote baseline comparison to {output_path}")
        logger.info(f"Generated {len(comparison_df)} rows")
        
        # Log summary
        logger.info("Summary:")
        for _, row in comparison_df.iterrows():
            logger.info(f"  {row['condition']}: win_rate={row['win_rate']:.4f}, "
                        f"avg_tokens={row['avg_tokens']:.2f}, "
                        f"std_dev_tokens={row['std_dev_tokens']:.2f}")

        return 0

    except Exception as e:
        logger.error(f"Failed to generate baseline comparison: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())