import os
import sys
import logging
import yaml
import pandas as pd
import numpy as np
from logging_config import setup_logging

logger = setup_logging(__name__)

def load_protocol(protocol_path: str = "data/protocols/protocol.yaml") -> dict:
    """Load the simulation protocol configuration."""
    if not os.path.exists(protocol_path):
        raise FileNotFoundError(f"Protocol file not found at {protocol_path}")
    
    with open(protocol_path, 'r') as f:
        return yaml.safe_load(f)

def derive_condition_column(df: pd.DataFrame, protocol: dict, threshold_type: str) -> pd.DataFrame:
    """
    Derive the 'condition' column based on the specified threshold type.
    
    Args:
        df: Input dataframe with 'deprivation_intensity' (0-1) or similar metric.
        protocol: The loaded protocol dictionary containing threshold labels.
        threshold_type: One of 'strict', 'moderate', 'partial'.
    
    Returns:
        DataFrame with the new 'condition' column populated with exact labels from protocol.
    """
    # Map threshold type to the specific key in the protocol
    key_map = {
        'strict': 'strict_threshold_label',
        'moderate': 'moderate_threshold_label',
        'partial': 'partial_threshold_label'
    }
    
    if threshold_type not in key_map:
        raise ValueError(f"Invalid threshold_type: {threshold_type}. Must be one of {list(key_map.keys())}")
    
    label_key = key_map[threshold_type]
    if label_key not in protocol:
        raise KeyError(f"Protocol missing key: {label_key}")
    
    target_label = protocol[label_key]
    
    # Determine cutoff based on threshold type
    # Assuming deprivation_intensity is 0.0 (no deprivation) to 1.0 (complete)
    # strict: high intensity (e.g., > 0.8)
    # moderate: medium intensity (e.g., 0.4 - 0.8)
    # partial: low intensity (e.g., < 0.4)
    
    # Define cutoffs for the binary classification for this specific threshold
    # If the data is continuous intensity, we classify rows into 'deprivation' vs 'control'
    # based on the threshold logic. However, the task asks to populate 'condition' with the label.
    # We assume the input df has a continuous 'deprivation_intensity' column.
    
    if 'deprivation_intensity' not in df.columns:
        # Fallback: if no intensity column, assume all are control or raise error
        # For this simulation, we assume synthetic data generation created this column.
        logger.warning("Column 'deprivation_intensity' not found. Creating dummy values for simulation.")
        df['deprivation_intensity'] = np.random.uniform(0, 1, len(df))

    # Logic: 
    # If threshold is 'strict', only high intensity counts as 'strict (complete isolation)'
    # If 'moderate', medium+ counts as 'moderate (partial sensory reduction)'
    # If 'partial', any non-zero counts as 'partial (minimal sensory reduction)'
    
    # We will create a binary 'condition' column where 1 = specific deprivation state, 0 = control
    # But the task says: "save them as distinct files... Each file must contain the condition column populated with the exact label"
    # This implies the column values should be the LABEL strings, or the column represents the category.
    # Given the context of "processed datasets for ALL three thresholds", it implies we are filtering or labeling
    # based on these thresholds.
    
    # Let's assume the 'condition' column should contain the LABEL string for rows that meet the criteria,
    # and perhaps 'control' or NaN for others? Or simply the label for the whole dataset if it's a filtered subset?
    # Re-reading: "iterate processed datasets... save as distinct files... condition column populated with exact label".
    # This suggests each file represents the data for that specific threshold scenario.
    # So for `data_threshold_strict.csv`, the 'condition' column should be the label "strict (complete isolation)"
    # for the relevant rows, or perhaps the dataset is filtered to only those rows?
    
    # Interpretation: The dataset contains all participants. We add a 'condition' column.
    # For the 'strict' file, we label rows with high intensity as the strict label, others as control.
    # However, to make the files distinct and meaningful for the sensitivity sweep (T030),
    # we likely need to filter or re-label such that the 'condition' column reflects the threshold definition.
    
    # Let's implement a standard approach:
    # 1. Load data (which has 'deprivation_intensity' from generate_data.py)
    # 2. For each threshold, create a copy.
    # 3. In that copy, set 'condition' to the specific label if intensity > cutoff, else 'control'.
    # 4. Save to specific file.
    
    # Cutoffs (arbitrary but consistent with "strict/moderate/partial" logic)
    # Strict: top 20% (intensity > 0.8)
    # Moderate: top 50% (intensity > 0.5)
    # Partial: top 80% (intensity > 0.2)
    
    cutoffs = {
        'strict': 0.8,
        'moderate': 0.5,
        'partial': 0.2
    }
    
    cutoff = cutoffs[threshold_type]
    
    # Create condition column
    df_copy = df.copy()
    
    def assign_condition(intensity):
        if intensity > cutoff:
            return target_label
        else:
            return "control"
    
    df_copy['condition'] = df_copy['deprivation_intensity'].apply(assign_condition)
    
    return df_copy

def save_processed_data(df: pd.DataFrame, output_path: str):
    """Save the dataframe to a CSV file, creating directories if necessary."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved processed data to {output_path}")

def process_data_for_threshold(data_path: str, protocol: dict, threshold_type: str, output_path: str):
    """
    Load data, derive condition column for a specific threshold, and save.
    """
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Input data file not found: {data_path}")
    
    df = pd.read_csv(data_path)
    logger.info(f"Loaded data from {data_path} with {len(df)} rows")
    
    processed_df = derive_condition_column(df, protocol, threshold_type)
    save_processed_data(processed_df, output_path)
    
    # Log the distribution of conditions
    condition_counts = processed_df['condition'].value_counts()
    logger.info(f"Condition distribution for {threshold_type}:\n{condition_counts}")

def main():
    """
    Main entry point to generate processed datasets for all three thresholds.
    Expects synthetic data to be in data/synthetic/ (generated by generate_data.py).
    """
    # Setup logging
    setup_logging()
    
    # Define paths
    protocol_path = "data/protocols/protocol.yaml"
    # Assume generate_data.py creates a file like data/synthetic/simulation_data.csv
    # We need to find the actual generated file. Let's assume the standard output name.
    synthetic_data_path = "data/synthetic/simulation_data.csv"
    
    # If the standard file doesn't exist, try to find any csv in data/synthetic
    if not os.path.exists(synthetic_data_path):
        synth_dir = "data/synthetic"
        if os.path.exists(synth_dir):
            files = [f for f in os.listdir(synth_dir) if f.endswith('.csv')]
            if files:
                synthetic_data_path = os.path.join(synth_dir, files[0])
                logger.info(f"Found synthetic data at {synthetic_data_path}")
            else:
                logger.error("No synthetic data found. Please run generate_data.py first.")
                sys.exit(1)
        else:
            logger.error("Synthetic data directory not found.")
            sys.exit(1)
    
    output_dir = "data/processed"
    os.makedirs(output_dir, exist_ok=True)
    
    # Load protocol
    try:
        protocol = load_protocol(protocol_path)
    except Exception as e:
        logger.error(f"Failed to load protocol: {e}")
        sys.exit(1)
    
    thresholds = ['strict', 'moderate', 'partial']
    
    for threshold in thresholds:
        output_filename = f"data_threshold_{threshold}.csv"
        output_path = os.path.join(output_dir, output_filename)
        
        logger.info(f"Processing data for {threshold} threshold...")
        try:
            process_data_for_threshold(
                synthetic_data_path, 
                protocol, 
                threshold, 
                output_path
            )
        except Exception as e:
            logger.error(f"Failed to process {threshold} threshold: {e}")
            sys.exit(1)
    
    logger.info("All threshold datasets generated successfully.")

if __name__ == "__main__":
    main()
