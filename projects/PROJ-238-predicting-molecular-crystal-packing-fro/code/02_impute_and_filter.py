import os
import pandas as pd
import logging
from pathlib import Path
from datetime import datetime
import json
import sys

# Add project root to path for imports if running as script
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from code.config import get_config, log_event

def setup_logger(name: str) -> logging.Logger:
    """Setup a logger that outputs JSON to stdout."""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger

def load_raw_descriptors(filepath: Path) -> pd.DataFrame:
    """Load the raw descriptors CSV."""
    logger = logging.getLogger(__name__)
    if not filepath.exists():
        logger.error(f"File not found: {filepath}")
        raise FileNotFoundError(f"Raw descriptors file not found at {filepath}")
    
    logger.info(f"Loading raw descriptors from {filepath}")
    df = pd.read_csv(filepath)
    logger.info(f"Loaded {len(df)} rows with columns: {list(df.columns)}")
    return df

def impute_missing_auxiliary(df: pd.DataFrame, target_col: str = 'packing_coefficient') -> pd.DataFrame:
    """
    Impute missing auxiliary descriptors (e.g., Dipole) with the training-set median.
    Flags the row with a boolean column 'dipole_imputed'.
    """
    logger = logging.getLogger(__name__)
    df = df.copy()
    
    # Identify auxiliary columns to impute (exclude ID and target)
    # Based on T012/T014, expected columns: ID, Volume, SurfaceArea, Dipole, HBD, HBA, PSA, packing_coefficient
    auxiliary_cols = ['Volume', 'SurfaceArea', 'Dipole', 'HBD', 'HBA', 'PSA']
    cols_to_check = [c for c in auxiliary_cols if c in df.columns]
    
    imputation_stats = {}
    
    for col in cols_to_check:
        missing_mask = df[col].isna()
        if missing_mask.any():
            # Calculate median on non-missing values
            median_val = df.loc[~missing_mask, col].median()
            if pd.isna(median_val):
                logger.warning(f"Median for {col} is NaN (all values missing). Skipping imputation for this column.")
                continue
            
            logger.info(f"Imputing {missing_mask.sum()} missing values in '{col}' with median {median_val:.4f}")
            df.loc[missing_mask, col] = median_val
            imputation_stats[col] = median_val
            
            # Add specific flag for Dipole as requested in T016
            if col == 'Dipole':
                df['dipole_imputed'] = df['dipole_imputed'].fillna(False) | missing_mask
            elif 'imputed' not in df.columns:
                # Initialize generic imputation flag if Dipole isn't the only one or first
                df['dipole_imputed'] = False

    # Ensure the specific flag column exists even if no imputation happened yet (for schema consistency)
    if 'dipole_imputed' not in df.columns:
        df['dipole_imputed'] = False
    
    logger.info(f"Imputation complete. Stats: {imputation_stats}")
    return df

def filter_missing_target(df: pd.DataFrame, target_col: str = 'packing_coefficient') -> tuple[pd.DataFrame, int]:
    """
    Exclude rows with missing target values and return the count of excluded rows.
    """
    logger = logging.getLogger(__name__)
    initial_count = len(df)
    
    missing_mask = df[target_col].isna()
    excluded_count = missing_mask.sum()
    
    if excluded_count > 0:
        logger.warning(f"Excluding {excluded_count} rows with missing target '{target_col}'")
        df_clean = df[~missing_mask].copy()
    else:
        df_clean = df.copy()
        logger.info(f"No rows excluded due to missing target.")
    
    final_count = len(df_clean)
    return df_clean, excluded_count

def save_outputs(df: pd.DataFrame, output_path: Path, log_path: Path, excluded_count: int):
    """Save the processed dataframe and the log file."""
    logger = logging.getLogger(__name__)
    
    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save CSV
    logger.info(f"Saving processed descriptors to {output_path}")
    df.to_csv(output_path, index=False)
    
    # Save Log
    timestamp = datetime.now().isoformat()
    log_content = {
        "timestamp": timestamp,
        "task": "T016 - Missing Data Handling",
        "input_file": str(output_path),
        "rows_excluded_missing_target": excluded_count,
        "rows_remaining": len(df),
        "columns": list(df.columns),
        "imputation_flags_present": 'dipole_imputed' in df.columns
    }
    
    logger.info(f"Writing log to {log_path}")
    with open(log_path, 'w') as f:
        json.dump(log_content, f, indent=2)

def main():
    """Main entry point for the imputation and filtering pipeline."""
    logger = setup_logger("T016_Impute_Filter")
    log_event("start", "T016")
    
    config = get_config()
    
    # Define paths based on project structure
    # Input: raw_descriptors.csv from T012/T014/T015
    input_path = Path("data/descriptors/raw_descriptors.csv")
    
    # Output: Updated raw_descriptors.csv (or processed version)
    output_path = Path("data/descriptors/raw_descriptors.csv")
    
    # Log file for missing target exclusions
    log_path = Path("data/processed/missing_target.log")
    
    try:
        # 1. Load Data
        df = load_raw_descriptors(input_path)
        
        # 2. Impute Auxiliary Descriptors
        df = impute_missing_auxiliary(df)
        
        # 3. Filter Missing Target
        df_clean, excluded_count = filter_missing_target(df)
        
        # 4. Save Outputs
        save_outputs(df_clean, output_path, log_path, excluded_count)
        
        log_event("complete", "T016", {"rows_processed": len(df), "rows_excluded": excluded_count})
        logger.info("T016 completed successfully.")
        
    except FileNotFoundError as e:
        logger.error(f"Input file missing: {e}")
        log_event("failed", "T016", {"reason": str(e)})
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        log_event("failed", "T016", {"reason": str(e)})
        sys.exit(1)

if __name__ == "__main__":
    main()
