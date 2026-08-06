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
