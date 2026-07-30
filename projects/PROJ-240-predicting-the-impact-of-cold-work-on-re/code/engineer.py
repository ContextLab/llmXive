import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Tuple
import pandas as pd
import numpy as np

# Constants
MIN_DATASET_SIZE = 50
COLD_WORK_COL = "cold_work"
MN_COL = "Mn_content"
MG_COL = "Mg_content"
SI_COL = "Si_content"
CU_COL = "Cu_content"
TEMP_COL = "annealing_temperature"
TARGET_COL = "time_to_peak_softening"
INTERACTION_COLS = [
    "cold_work_Mn_interaction",
    "cold_work_Mg_interaction",
    "cold_work_Si_interaction",
    "cold_work_Cu_interaction",
]

def calculate_interaction_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate interaction features between cold work and alloying elements.
    
    Adds:
    - cold_work_Mn_interaction = cold_work * Mn_content
    - cold_work_Mg_interaction = cold_work * Mg_content
    - cold_work_Si_interaction = cold_work * Si_content
    - cold_work_Cu_interaction = cold_work * Cu_content
    
    Args:
        df: DataFrame with required composition and cold work columns.
        
    Returns:
        DataFrame with new interaction columns appended.
        
    Raises:
        KeyError: If required columns are missing.
    """
    required_cols = [COLD_WORK_COL, MN_COL, MG_COL, SI_COL, CU_COL]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise KeyError(f"Missing required columns for interaction features: {missing}")
    
    df = df.copy()
    df["cold_work_Mn_interaction"] = df[COLD_WORK_COL] * df[MN_COL]
    df["cold_work_Mg_interaction"] = df[COLD_WORK_COL] * df[MG_COL]
    df["cold_work_Si_interaction"] = df[COLD_WORK_COL] * df[SI_COL]
    df["cold_work_Cu_interaction"] = df[COLD_WORK_COL] * df[CU_COL]
    
    return df

def ensure_temperature_feature(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ensures the annealing temperature feature exists.
    If missing, raises an error or creates a placeholder if spec allows (here we raise).
    
    Args:
        df: Input DataFrame.
        
    Returns:
        DataFrame with temperature feature (or raises).
    """
    if TEMP_COL not in df.columns:
        raise KeyError(f"Missing required feature column: {TEMP_COL}")
    return df

def validate_dataset_size(df: pd.DataFrame, min_rows: int = MIN_DATASET_SIZE) -> None:
    """
    Validates that the dataset has at least `min_rows` rows.
    
    Implements FR-008: Raise ValueError if rows < 50.
    
    Args:
        df: DataFrame to validate.
        min_rows: Minimum required number of rows (default 50).
        
    Raises:
        ValueError: If the dataset has fewer rows than required.
    """
    row_count = len(df)
    if row_count < min_rows:
        raise ValueError(
            f"Dataset size validation failed (FR-008): "
            f"Expected at least {min_rows} rows, but found {row_count}. "
            f"Cannot proceed with modeling."
        )

def run_engineering_pipeline(input_path: str, output_path: str) -> Dict[str, Any]:
    """
    Orchestrates the feature engineering pipeline:
    1. Load validated data.
    2. Calculate interaction features.
    3. Ensure temperature feature exists.
    4. Validate dataset size (FR-008).
    5. Save engineered features.
    
    Args:
        input_path: Path to the validated CSV (from ingest.py).
        output_path: Path to save the engineered features CSV.
        
    Returns:
        Dictionary with pipeline metadata (row count, features added).
        
    Raises:
        ValueError: If dataset size is insufficient (FR-008).
        FileNotFoundError: If input file does not exist.
        KeyError: If required columns are missing.
    """
    # 1. Load data
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    df = pd.read_csv(input_path)
    
    # 2. Calculate interaction features
    df = calculate_interaction_features(df)
    
    # 3. Ensure temperature feature
    df = ensure_temperature_feature(df)
    
    # 4. Validate dataset size (FR-008)
    validate_dataset_size(df)
    
    # 5. Save output
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    df.to_csv(output_path, index=False)
    
    return {
        "input_rows": len(df),
        "output_rows": len(df),
        "features_added": INTERACTION_COLS + [TEMP_COL],
        "output_path": output_path
    }

def main():
    """Entry point for running the engineering pipeline."""
    # Define paths relative to project root
    project_root = Path(__file__).parent.parent
    input_file = project_root / "data" / "processed" / "validated.csv"
    output_file = project_root / "data" / "processed" / "engineered_features.csv"
    
    print(f"Starting feature engineering pipeline...")
    print(f"Input: {input_file}")
    print(f"Output: {output_file}")
    
    try:
        result = run_engineering_pipeline(str(input_file), str(output_file))
        print(f"Pipeline completed successfully.")
        print(f"Rows processed: {result['input_rows']}")
        print(f"Features added: {result['features_added']}")
        print(f"Output saved to: {result['output_path']}")
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"Validation Error: {e}")
        sys.exit(1)
    except KeyError as e:
        print(f"Data Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()