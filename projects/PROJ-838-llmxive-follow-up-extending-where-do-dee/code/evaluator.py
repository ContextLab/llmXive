import csv
import json
import os
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
import pandas as pd

def load_metrics(file_path: str) -> pd.DataFrame:
    """Loads metrics from a CSV file."""
    return pd.read_csv(file_path)

def save_metrics(df: pd.DataFrame, file_path: str):
    """Saves a DataFrame to a CSV file."""
    df.to_csv(file_path, index=False)

def load_json_file(file_path: str) -> Any:
    """Loads data from a JSON file."""
    with open(file_path, 'r') as f:
        return json.load(f)

def save_json_file(data: Any, file_path: str):
    """Saves data to a JSON file."""
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=4)

def stratified_split(df: pd.DataFrame, label_column: str, test_size: float = 0.2, random_state: int = 42) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Splits a DataFrame into train and test sets while preserving label balance."""
    
    labels = df[label_column].unique()
    train_df_list = []
    test_df_list = []

    for label in labels:
        label_df = df[df[label_column] == label]
        train_size = int(len(label_df) * (1 - test_size))
        train_df_list.append(label_df[:train_size])
        test_df_list.append(label_df[train_size:])

    train_df = pd.concat(train_df_list)
    test_df = pd.concat(test_df_list)

    # Shuffle the DataFrames to ensure randomness
    train_df = train_df.sample(frac=1, random_state=random_state).reset_index(drop=True)
    test_df = test_df.sample(frac=1, random_state=random_state).reset_index(drop=True)

    return train_df, test_df

def run_stratified_split(input_file: str, train_output: str, test_output: str, label_column: str = "label", test_size: float = 0.2, random_state: int = 42):
    """
    Reads metrics from input_file, performs a stratified split, and writes
    train_metrics.csv and test_metrics.csv to the specified output paths.
    
    Args:
        input_file: Path to the source metrics CSV (data/processed/metrics.csv).
        train_output: Path for the train split output (data/processed/train_metrics.csv).
        test_output: Path for the test split output (data/processed/test_metrics.csv).
        label_column: The column name to use for stratification.
        test_size: Proportion of data to include in the test split.
        random_state: Random seed for reproducibility.
    """
    logging.info(f"Loading metrics from {input_file}")
    df = load_metrics(input_file)
    
    if label_column not in df.columns:
        raise ValueError(f"Label column '{label_column}' not found in {input_file}. Columns: {df.columns.tolist()}")
    
    logging.info(f"Performing stratified split on column '{label_column}' with test_size={test_size}")
    train_df, test_df = stratified_split(df, label_column=label_column, test_size=test_size, random_state=random_state)
    
    logging.info(f"Writing train split to {train_output} (n={len(train_df)})")
    save_metrics(train_df, train_output)
    
    logging.info(f"Writing test split to {test_output} (n={len(test_df)})")
    save_metrics(test_df, test_output)
    
    logging.info("Stratified split completed successfully.")

def main():
    """
    Entry point for the stratified split task.
    Expects input at data/processed/metrics.csv and writes to data/processed/train_metrics.csv and data/processed/test_metrics.csv.
    """
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    input_path = "data/processed/metrics.csv"
    train_path = "data/processed/train_metrics.csv"
    test_path = "data/processed/test_metrics.csv"
    
    if not os.path.exists(input_path):
        logging.error(f"Input file not found: {input_path}")
        logging.error("Ensure T023 (process_batch) has run successfully to generate metrics.csv.")
        return 1
    
    try:
        run_stratified_split(input_path, train_path, test_path)
        return 0
    except Exception as e:
        logging.error(f"Error during stratified split: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
