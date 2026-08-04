import os
import sys
import argparse
import json
import pandas as pd
import numpy as np

# Ensure imports from sibling modules exist as per API surface
from utils import set_seed, load_json, save_json, calculate_checksum, update_checksums, ensure_directory

def load_raw_data(input_path: str) -> pd.DataFrame:
    """Load raw data from a CSV file."""
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    df = pd.read_csv(input_path)
    return df

def map_to_categorical(df: pd.DataFrame) -> pd.DataFrame:
    """Map status_level and observed_behavior to categorical factors."""
    # Ensure columns exist
    required_cols = ['status_level', 'observed_behavior', 'risk_taking_score', 'participant_id']
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Missing required column: {col}")

    # Map status_level (assuming values like 'high', 'low', 'medium' or similar)
    if 'status_level' in df.columns:
        # Normalize to High/Low
        df['status_level'] = df['status_level'].astype(str).str.lower()
        df['status_level'] = df['status_level'].replace({
            'high': 'High',
            'low': 'Low',
            'medium': 'Low',  # Default medium to low if binning not applied yet
            'high_status': 'High',
            'low_status': 'Low'
        })

    # Map observed_behavior (assuming values like 'risky', 'conservative')
    if 'observed_behavior' in df.columns:
        df['observed_behavior'] = df['observed_behavior'].astype(str).str.lower()
        df['observed_behavior'] = df['observed_behavior'].replace({
            'risky': 'Risky',
            'conservative': 'Conservative',
            'risk': 'Risky',
            'safe': 'Conservative'
        })

    return df

def apply_binning_strategy(df: pd.DataFrame, binning_output_path: str = None) -> pd.DataFrame:
    """
    Implement specific binning strategy for input data with >2 levels.
    Returns the dataframe with binning applied.
    """
    if 'status_level' not in df.columns:
        return df

    unique_levels = df['status_level'].nunique()
    binning_applied = False

    if unique_levels > 2:
        # Example strategy: Map 'Medium' to 'Low' (or other logic based on spec)
        # Here we assume High is High, and everything else is Low for binary analysis
        # Or if we have High, Medium, Low -> High vs (Medium+Low)
        original_levels = df['status_level'].unique()
        df['status_level'] = df['status_level'].apply(
            lambda x: 'High' if x == 'High' else 'Low'
        )
        binning_applied = True

    if binning_output_path:
        ensure_directory(binning_output_path)
        binning_state = {
            "binning_applied": binning_applied,
            "original_levels": list(original_levels) if 'original_levels' in locals() else [],
            "final_levels": list(df['status_level'].unique())
        }
        with open(binning_output_path, 'w') as f:
            json.dump(binning_state, f, indent=2)

    return df

def handle_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    """Handle missing values (imputation or exclusion)."""
    # Check for nulls in critical columns
    critical_cols = ['participant_id', 'status_level', 'observed_behavior', 'risk_taking_score']
    for col in critical_cols:
        if col not in df.columns:
            continue
        null_count = df[col].isnull().sum()
        if null_count > 0:
            # For this implementation, we drop rows with missing critical values
            # to preserve participant_id granularity and avoid aggregation
            initial_len = len(df)
            df = df.dropna(subset=[col])
            dropped = initial_len - len(df)
            print(f"Dropped {dropped} rows due to missing {col}")

    # Verify no duplicate participant_id for the same condition if required by T053
    # (This is a validation step, not imputation)
    if 'participant_id' in df.columns and 'status_level' in df.columns and 'observed_behavior' in df.columns:
        duplicates = df.duplicated(subset=['participant_id', 'status_level', 'observed_behavior'], keep=False)
        if duplicates.any():
            raise ValueError("Data Integrity Error: Duplicate entries found for same participant in same condition.")

    return df

def save_processed_data(df: pd.DataFrame, output_path: str) -> None:
    """Save the processed dataframe to CSV."""
    ensure_directory(output_path)
    df.to_csv(output_path, index=False)
    # Update checksums
    update_checksums(output_path)

def detect_outcome_type(df: pd.DataFrame, output_path: str) -> str:
    """
    Detect outcome variable type (binary vs continuous) based on data distribution.
    If unique values in risk_taking_score < 10, assume binary; else continuous.
    """
    if 'risk_taking_score' not in df.columns:
        raise ValueError("Column 'risk_taking_score' not found in dataframe")

    unique_count = df['risk_taking_score'].nunique()
    detected_type = "binary" if unique_count < 10 else "continuous"

    ensure_directory(output_path)
    with open(output_path, 'w') as f:
        json.dump({"type": detected_type}, f, indent=2)

    return detected_type

def detect_data_structure(df: pd.DataFrame) -> str:
    """
    Detect data structure (within-subjects vs between-subjects).
    If unique participant_id < total rows, within-subjects; else between-subjects.
    """
    if 'participant_id' not in df.columns:
        raise ValueError("Column 'participant_id' not found in dataframe")

    unique_participants = df['participant_id'].nunique()
    total_rows = len(df)

    if unique_participants < total_rows:
        return "within-subjects"
    else:
        return "between-subjects"

def save_analysis_config(design_type: str, family_type: str, n_subjects: int, output_path: str) -> None:
    """Save the analysis configuration to a JSON file."""
    config = {
        "design_type": design_type,
        "family_type": family_type,
        "n_subjects": n_subjects
    }
    ensure_directory(output_path)
    with open(output_path, 'w') as f:
        json.dump(config, f, indent=2)

def preprocess_pipeline(input_path: str, output_path: str, structure_output_path: str = None, seed: int = 42) -> None:
    """
    Main pipeline function to preprocess data.
    1. Load raw data
    2. Map to categorical
    3. Apply binning
    4. Handle missing values
    5. Detect outcome type and write to file
    6. Detect data structure and write config
    7. Save cleaned data
    """
    set_seed(seed)

    # 1. Load
    df = load_raw_data(input_path)

    # 2. Map
    df = map_to_categorical(df)

    # 3. Bin
    binning_state_path = structure_output_path.replace('.json', '_binning.json') if structure_output_path else None
    df = apply_binning_strategy(df, binning_state_path)

    # 4. Handle missing
    df = handle_missing_values(df)

    # 5. Detect Outcome Type
    outcome_type_path = output_path.replace('cleaned_data.csv', 'outcome_type.json')
    detect_outcome_type(df, outcome_type_path)

    # 6. Detect Structure & Save Config
    design_type = detect_data_structure(df)
    n_subjects = df['participant_id'].nunique()
    # Family type is determined by outcome type, but for now we save the design config
    # The family type is explicitly handled in analysis.py based on outcome_type.json
    structure_config_path = structure_output_path or output_path.replace('cleaned_data.csv', 'structure_config.json')
    save_analysis_config(design_type, "gaussian", n_subjects, structure_config_path)

    # 7. Save
    save_processed_data(df, output_path)

def main():
    parser = argparse.ArgumentParser(description="Preprocess research data")
    parser.add_argument('--input', type=str, required=True, help="Path to input raw data CSV")
    parser.add_argument('--output', type=str, required=True, help="Path to output cleaned data CSV")
    parser.add_argument('--structure-output', type=str, required=False, help="Path to output structure config JSON")
    parser.add_argument('--seed', type=int, default=42, help="Random seed for reproducibility")

    args = parser.parse_args()

    preprocess_pipeline(
        input_path=args.input,
        output_path=args.output,
        structure_output_path=args.structure_output,
        seed=args.seed
    )
    print(f"Preprocessing complete. Output saved to {args.output}")

if __name__ == "__main__":
    main()