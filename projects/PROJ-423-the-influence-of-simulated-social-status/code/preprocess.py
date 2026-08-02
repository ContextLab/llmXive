import os
import sys
import argparse
import pandas as pd
import numpy as np
from datetime import datetime
import json

# Importing from sibling modules as per API surface
from utils import save_json, ensure_directory, set_seed
from logger import get_logger

logger = get_logger(__name__)

def load_raw_data(file_path: str) -> pd.DataFrame:
    """Load raw data from a CSV file."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Raw data file not found: {file_path}")
    return pd.read_csv(file_path)

def map_to_categorical(df: pd.DataFrame) -> pd.DataFrame:
    """Map status_level and observed_behavior to categorical factors."""
    df = df.copy()
    if 'status_level' in df.columns:
        df['status_level'] = df['status_level'].astype('category')
    if 'observed_behavior' in df.columns:
        df['observed_behavior'] = df['observed_behavior'].astype('category')
    return df

def apply_binning_strategy(df: pd.DataFrame, config: dict) -> pd.DataFrame:
    """Apply binning strategy for input data with >2 levels."""
    # Placeholder for specific binning logic
    return df

def handle_missing_values(df: pd.DataFrame, strategy: str = 'exclude') -> pd.DataFrame:
    """Handle missing values based on strategy."""
    if strategy == 'exclude':
        return df.dropna()
    elif strategy == 'impute_mean':
        return df.fillna(df.mean(numeric_only=True))
    return df

def save_processed_data(df: pd.DataFrame, file_path: str):
    """Save processed data to a CSV file."""
    ensure_directory(file_path)
    df.to_csv(file_path, index=False)
    logger.info(f"Processed data saved to {file_path}")

def log_meta_analysis_decision(decision: str):
    """Log the decision made for meta-analysis path."""
    logger.info(f"Meta-analysis decision: {decision}")

def detect_outcome_type(df: pd.DataFrame, column: str) -> str:
    """Detect outcome variable type (binary vs. continuous)."""
    if df[column].nunique() == 2:
        return 'binary'
    return 'continuous'

def determine_regression_family(outcome_type: str) -> str:
    """Determine regression family based on outcome type."""
    return 'binomial' if outcome_type == 'binary' else 'gaussian'

def save_analysis_config(config: dict, file_path: str):
    """Save analysis configuration to a JSON file."""
    ensure_directory(file_path)
    with open(file_path, 'w') as f:
        json.dump(config, f, indent=2)
    logger.info(f"Analysis config saved to {file_path}")

def detect_data_structure(df: pd.DataFrame, output_path: str) -> dict:
    """
    Dynamically generate structure_config.json based on cleaned_data.csv.
    
    Logic:
    - Count unique participant_id values vs total rows.
    - If unique < total, set type: "within-subjects", else "between-subjects".
    - Set n_subjects to count of unique participant_id.
    - Set model_type based on type.
    
    Args:
        df: The cleaned dataframe.
        output_path: Path to write the structure_config.json.
        
    Returns:
        dict: The generated structure config.
    """
    if 'participant_id' not in df.columns:
        raise ValueError("Input dataframe must contain 'participant_id' column.")

    total_rows = len(df)
    unique_subjects = df['participant_id'].nunique()
    
    if unique_subjects < total_rows:
        design_type = "within-subjects"
        model_type = "mixed-effects"
    else:
        design_type = "between-subjects"
        model_type = "fixed-effects"
    
    structure_config = {
        "type": design_type,
        "n_subjects": int(unique_subjects),
        "model_type": model_type
    }
    
    ensure_directory(output_path)
    with open(output_path, 'w') as f:
        json.dump(structure_config, f, indent=2)
    
    logger.info(f"Data structure detected: {design_type} (N={unique_subjects}). Config saved to {output_path}")
    return structure_config

def preprocess_pipeline(input_path: str, output_path: str, config: dict = None):
    """Run the full preprocessing pipeline."""
    if config is None:
        config = {}
    
    set_seed(config.get('seed', 42))
    
    logger.info(f"Loading raw data from {input_path}")
    df = load_raw_data(input_path)
    
    logger.info("Mapping to categorical factors")
    df = map_to_categorical(df)
    
    if 'binning_strategy' in config:
        logger.info("Applying binning strategy")
        df = apply_binning_strategy(df, config)
    
    logger.info("Handling missing values")
    df = handle_missing_values(df, config.get('missing_strategy', 'exclude'))
    
    logger.info("Detecting outcome type")
    outcome_type = detect_outcome_type(df, config.get('outcome_column', 'risk_taking_score'))
    family = determine_regression_family(outcome_type)
    
    logger.info(f"Outcome type: {outcome_type}, Regression family: {family}")
    
    logger.info("Saving processed data")
    save_processed_data(df, output_path)
    
    return df

def main():
    parser = argparse.ArgumentParser(description="Preprocessing Pipeline")
    parser.add_argument("--input", type=str, required=True, help="Path to raw data CSV")
    parser.add_argument("--output", type=str, required=True, help="Path to save processed data CSV")
    parser.add_argument("--structure-output", type=str, default="data/processed/structure_config.json",
                        help="Path to save structure config JSON")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    
    args = parser.parse_args()
    
    set_seed(args.seed)
    
    # Run pipeline
    df = preprocess_pipeline(args.input, args.output, {'seed': args.seed})
    
    # Detect structure and save config (Task T020a)
    detect_data_structure(df, args.structure_output)

if __name__ == "__main__":
    main()
