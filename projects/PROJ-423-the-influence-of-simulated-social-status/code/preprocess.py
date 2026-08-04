import os
import sys
import argparse
import json
import pandas as pd
import numpy as np

from utils import ensure_directory, save_json, update_checksums
from logger import setup_logger

ensure_directory("logs")
logger = setup_logger("preprocess", "logs/preprocess.log")

def load_raw_data(input_path: str) -> pd.DataFrame:
    """Loads raw data from CSV."""
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    return pd.read_csv(input_path)

def map_to_categorical(df: pd.DataFrame) -> pd.DataFrame:
    """Maps status_level and observed_behavior to categorical factors."""
    # Example mapping logic, adjust based on actual data values
    if 'status_level' in df.columns:
        df['status_level'] = df['status_level'].astype('category')
    if 'observed_behavior' in df.columns:
        df['observed_behavior'] = df['observed_behavior'].astype('category')
    return df

def apply_binning_strategy(df: pd.DataFrame) -> tuple:
    """Applies binning strategy if >2 levels exist."""
    binning_applied = False
    # Check unique values
    if 'status_level' in df.columns:
        unique_levels = df['status_level'].nunique()
        if unique_levels > 2:
            # Example: Bin into High vs Low/Medium
            # This is a placeholder logic; real logic depends on data distribution
            logger.info("Binning strategy applied.")
            binning_applied = True
    return df, binning_applied

def flag_ambiguity(df: pd.DataFrame) -> bool:
    """Flags ambiguity if binning is insufficient."""
    # Placeholder logic
    return False

def handle_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    """Handles missing values by dropping or imputing."""
    # Drop rows with missing critical columns
    if 'participant_id' in df.columns:
        df = df.dropna(subset=['participant_id', 'risk_taking_score'])
    return df

def detect_outcome_type(df: pd.DataFrame) -> str:
    """Detects if outcome is binary or continuous."""
    if 'risk_taking_score' not in df.columns:
        raise ValueError("Column 'risk_taking_score' not found.")
    
    unique_values = df['risk_taking_score'].nunique()
    if unique_values < 10:
        return "binary"
    return "continuous"

def save_processed_data(df: pd.DataFrame, output_path: str) -> None:
    """Saves processed data to CSV."""
    ensure_directory(os.path.dirname(output_path))
    df.to_csv(output_path, index=False)
    update_checksums(output_path)

def save_analysis_config(config: Dict, output_path: str) -> None:
    """Saves analysis configuration to JSON."""
    ensure_directory(os.path.dirname(output_path))
    with open(output_path, 'w') as f:
        json.dump(config, f, indent=2)

def detect_data_structure(df: pd.DataFrame) -> str:
    """Detects data structure (within/between subjects)."""
    total_rows = len(df)
    unique_participants = df['participant_id'].nunique()
    if unique_participants < total_rows:
        return "within-subjects"
    return "between-subjects"

def save_binning_state(state: Dict, output_path: str) -> None:
    """Saves binning state."""
    save_json(state, output_path)

def preprocess_pipeline(input_path: str, output_path: str, structure_output_path: Optional[str] = None, seed: int = 42) -> None:
    """Runs the full preprocessing pipeline."""
    import random
    random.seed(seed)
    np.random.seed(seed)

    df = load_raw_data(input_path)
    df = map_to_categorical(df)
    df, binning_applied = apply_binning_strategy(df)
    
    if flag_ambiguity(df):
        logger.warning("Ambiguity detected. Manual review required.")
        # In a real scenario, this might halt or write a flag file
    
    df = handle_missing_values(df)
    
    outcome_type = detect_outcome_type(df)
    save_analysis_config({"type": outcome_type}, "data/processed/outcome_type.json")
    
    save_processed_data(df, output_path)
    
    if structure_output_path:
        structure = detect_data_structure(df)
        save_analysis_config({"structure": structure}, structure_output_path)

def main():
    parser = argparse.ArgumentParser(description="Preprocess research data.")
    parser.add_argument("--input", required=True, help="Path to input CSV")
    parser.add_argument("--output", required=True, help="Path to output CSV")
    parser.add_argument("--structure-output", help="Path to structure config output")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    
    args = parser.parse_args()
    
    try:
        preprocess_pipeline(args.input, args.output, args.structure_output, args.seed)
        logger.info("Preprocessing completed successfully.")
    except Exception as e:
        logger.error(f"Preprocessing failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
