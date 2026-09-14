import os
import json
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import numpy as np
from config import get_config
from data_model import Passage

def extract_passage_data(dataset_path: str) -> pd.DataFrame:
    """
    Extracts passage text data from the raw dataset.

    Args:
        dataset_path (str): Path to the raw dataset.

    Returns:
        pd.DataFrame: DataFrame containing passage data.
    """
    config = get_config()
    raw_data_path = config.get("raw_data_path")
    dataset_file = os.path.join(raw_data_path, "ds004041_pupil_data.csv")

    try:
        df = pd.read_csv(dataset_file)
        # Select relevant columns
        passage_data = df[["passage_text", "passage_id"]].copy()
        passage_data.rename(columns={"passage_text": "original_text"}, inplace=True)
        # Remove duplicates based on passage_id
        passage_data.drop_duplicates(subset=["passage_id"], inplace=True)
        passage_data["passage_id"] = passage_data["passage_id"].astype(str)
        return passage_data
    except FileNotFoundError:
        print(f"Error: Dataset file not found at {dataset_file}")
        return pd.DataFrame()  # Return an empty DataFrame in case of error

def generate_counterfactual_text(original_text: str) -> str:
    """
    Generates a simplified version of the original text.
    For simplicity, this function returns the original text.
    In a real implementation, a language model would be used.

    Args:
        original_text (str): The original text.

    Returns:
        str: The simplified text.
    """
    # Placeholder for a more sophisticated text simplification method
    return original_text

def select_text_version(cli_value: float, original_text: str, simplified_text: str) -> str:
    """
    Selects the text version based on the CLI value.

    Args:
        cli_value (float): The cognitive load index value.
        original_text (str): The original text.
        simplified_text (str): The simplified text.

    Returns:
        str: The selected text version.
    """
    cli_threshold = 0.5
    if cli_value > cli_threshold and simplified_text:
        return simplified_text
    else:
        return original_text

def main():
    """
    Main function to extract passage data and prepare it for joining with CLI data.
    """
    passage_data = extract_passage_data(dataset_path="data/raw")
    if passage_data.empty:
        print("No passage data extracted. Exiting.")
        return

    # Apply text simplification
    passage_data["simplified_text"] = passage_data["original_text"].apply(generate_counterfactual_text)

    # Save the processed data
    output_path = "data/derived/passage_data.parquet"
    passage_data.to_parquet(output_path, index=False)
    print(f"Passage data saved to {output_path}")

if __name__ == "__main__":
    main()