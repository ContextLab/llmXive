import os
import json
import logging
import pandas as pd
import numpy as np
from pathlib import Path

def run_stratified_analysis(df):
    """
    Performs a stratified analysis by splitting the dataset into "High AI‑Noise"
    and "Low AI‑Noise" groups and comparing effect sizes.

    Args:
        df (pd.DataFrame): The input DataFrame.

    Returns:
        dict: A dictionary containing the stratified effect sizes and comparison metrics.
    """
    high_ai_noise_df = df[df['ai_noise_flag'] == True]
    low_ai_noise_df = df[df['ai_noise_flag'] == False]

    # Example: Calculate the mean iteration_count for each group
    mean_iteration_count_high = high_ai_noise_df['iteration_count'].mean()
    mean_iteration_count_low = low_ai_noise_df['iteration_count'].mean()

    # Calculate the difference in effect sizes
    effect_size_difference = mean_iteration_count_high - mean_iteration_count_low

    stratified_results = {
        'high_ai_noise_mean_iteration_count': mean_iteration_count_high,
        'low_ai_noise_mean_iteration_count': mean_iteration_count_low,
        'effect_size_difference': effect_size_difference
    }

    return stratified_results

def main():
    """
    Main function to load data, run stratified analysis, and save results.
    """
    try:
        # Load the master dataset
        data_dir = Path("data/derived")
        if not data_dir.exists():
            logging.error(f"Data directory {data_dir} does not exist.")
            return

        master_dataset_path = data_dir / "master_dataset.csv"
        if not master_dataset_path.exists():
            logging.error(f"Master dataset {master_dataset_path} does not exist.")
            return

        df = pd.read_csv(master_dataset_path)

        # Run the stratified analysis
        stratified_results = run_stratified_analysis(df)

        # Save the results to a JSON file
        output_path = Path("data/derived/stratified_results.json")
        with open(output_path, "w") as f:
            json.dump(stratified_results, f, indent=4)

        logging.info(f"Stratified analysis completed. Results saved to {output_path}")

    except Exception as e:
        logging.error(f"An error occurred: {e}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    main()