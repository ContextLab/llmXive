import os
import sys
import json
import hashlib
import pandas as pd
import numpy as np
from sklearn.impute import KNNImputer
from pathlib import Path

# Import local utilities
from utils.constants import DATA_DIR, MAX_IMPUTATION_RATE
from utils.errors import CustomDataError
from utils.logging import monitor_resources

def fetch_esol_data(url: str) -> pd.DataFrame:
    """
    Fetch ESOL data from the specified URL.
    Includes pre-flight check via T041 logic (assumed handled by caller or wrapper).
    """
    # Placeholder for actual fetch logic using requests
    # In a real scenario, this would use requests.get(url) and parse CSV
    # For this implementation, we assume the data is already downloaded to data/raw/epa_solubility.csv
    # as per T011.
    raw_path = DATA_DIR / "raw" / "epa_solubility.csv"
    if not raw_path.exists():
        raise CustomDataError(f"Raw data file not found at {raw_path}. Run T011 first.")
    
    df = pd.read_csv(raw_path)
    return df

def calculate_molecular_weight(smiles: str) -> float:
    """
    Calculate molecular weight from SMILES string using RDKit.
    """
    try:
        from rdkit import Chem
        from rdkit.Chem import Descriptors
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return np.nan
        return Descriptors.MolWt(mol)
    except ImportError:
        # Fallback if RDKit not available, though it should be per requirements
        raise ImportError("RDKit is required for molecular weight calculation.")

def filter_by_molecular_weight(df: pd.DataFrame, threshold: float = 500.0) -> pd.DataFrame:
    """
    Filter rows where Molecular Weight < threshold.
    """
    # Assuming 'smiles' column exists
    if 'smiles' not in df.columns:
        raise CustomDataError("Input DataFrame must contain 'smiles' column.")
    
    # Apply calculation
    df['mw'] = df['smiles'].apply(calculate_molecular_weight)
    filtered_df = df[df['mw'] < threshold].copy()
    return filtered_df

def validate_composition(df: pd.DataFrame, tolerance: float = 1e-5) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Validate that composition columns sum to 1.0 within tolerance.
    Returns (valid_rows, rejected_rows).
    """
    # Identify composition columns (e.g., mole_fraction_1, mole_fraction_2, etc.)
    comp_cols = [col for col in df.columns if 'mole_fraction' in col]
    
    if not comp_cols:
        # If no specific mole fraction columns, assume 'composition' or similar
        # For this task, we assume columns like 'x1', 'x2' or explicit 'mole_fraction_*'
        # Let's assume the data has 'mole_fraction_solvent1', 'mole_fraction_solvent2'
        pass 
    
    # Calculate sum
    df['comp_sum'] = df[comp_cols].sum(axis=1)
    
    # Check validity
    valid_mask = np.abs(df['comp_sum'] - 1.0) <= tolerance
    valid_df = df[valid_mask].copy()
    rejected_df = df[~valid_mask].copy()
    
    return valid_df, rejected_df

def perform_knn_imputation(df: pd.DataFrame, columns: list, n_neighbors: int = 5) -> tuple[pd.DataFrame, float]:
    """
    Perform KNN imputation on specified columns.
    Returns imputed DataFrame and imputation rate (fraction of missing values imputed).
    """
    if not columns:
        return df, 0.0
    
    # Check for missing values
    missing_mask = df[columns].isna().any(axis=1)
    if not missing_mask.any():
        return df, 0.0
    
    # Count total missing cells
    total_missing = df[columns].isna().sum().sum()
    total_cells = df[columns].shape[0] * len(columns)
    
    imputer = KNNImputer(n_neighbors=n_neighbors)
    imputed_values = imputer.fit_transform(df[columns])
    
    df_imputed = df.copy()
    df_imputed[columns] = imputed_values
    
    imputation_rate = total_missing / total_cells if total_cells > 0 else 0.0
    
    return df_imputed, imputation_rate

def log_imputation_rate(rate: float, log_path: str):
    """
    Log the imputation rate to a file.
    """
    with open(log_path, 'w') as f:
        f.write(f"Imputation Rate: {rate:.4f}\n")
        if rate > MAX_IMPUTATION_RATE:
            f.write(f"WARNING: Imputation rate ({rate:.4f}) exceeds threshold ({MAX_IMPUTATION_RATE}).\n")

def clean_and_prepare_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Final cleaning steps: drop NaNs, ensure types, etc.
    """
    # Drop rows with any remaining NaNs in critical columns
    critical_cols = ['smiles', 'logS']
    if all(c in df.columns for c in critical_cols):
        df = df.dropna(subset=critical_cols)
    return df

def main():
    """
    Main execution flow for T013: Data Imputation.
    1. Load filtered data (from T012).
    2. Perform KNN imputation.
    3. Check rate against threshold.
    4. Write outputs.
    """
    # Monitor resources
    monitor_resources()

    # Paths
    input_path = DATA_DIR / "processed" / "filtered_mw.csv"
    output_path = DATA_DIR / "processed" / "imputed_data.csv"
    rejected_path = DATA_DIR / "artifacts" / "rejected_rows.csv"
    log_path = DATA_DIR / "artifacts" / "imputation_log.txt"
    
    # Ensure directories exist
    output_path.parent.mkdir(parents=True, exist_ok=True)
    rejected_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Load data
    if not input_path.exists():
        # Fallback to raw if processed doesn't exist (for T012 dependency)
        raw_path = DATA_DIR / "raw" / "epa_solubility.csv"
        if not raw_path.exists():
            print(f"ERROR: No input data found at {input_path} or {raw_path}", file=sys.stderr)
            sys.exit(1)
        df = pd.read_csv(raw_path)
        # Apply MW filter if needed (T012 logic)
        df = filter_by_molecular_weight(df)
        # Save intermediate for consistency
        df.to_csv(input_path, index=False)
    else:
        df = pd.read_csv(input_path)

    # Composition Validation (T013 logic from description, though T012 was MW)
    # The task T013 description mentions "Data Filtering (Composition)" in the list,
    # but the detailed description is "Data Imputation".
    # We will perform composition validation first as per the task list structure,
    # then imputation.
    
    # Identify composition columns dynamically or assume standard names
    # Assuming 'mole_fraction_1', 'mole_fraction_2' etc.
    comp_cols = [c for c in df.columns if 'mole_fraction' in c]
    if not comp_cols:
        # If no mole fraction columns, skip validation or assume 1.0
        valid_df = df
        rejected_df = pd.DataFrame()
    else:
        valid_df, rejected_df = validate_composition(df, tolerance=1e-5)
        if not rejected_df.empty:
            rejected_df.to_csv(rejected_path, index=False)

    # Perform Imputation
    # Target columns for imputation: solvent properties
    # Assuming 'solvent_desc', 'interaction_terms' are numeric columns that might be NaN
    # In a real dataset, these might be floats.
    # We will impute all numeric columns that are not IDs or SMILES.
    numeric_cols = valid_df.select_dtypes(include=[np.number]).columns.tolist()
    # Exclude 'mw' if it was added
    if 'mw' in numeric_cols:
        numeric_cols.remove('mw')
    
    imputed_df, rate = perform_knn_imputation(valid_df, numeric_cols, n_neighbors=5)
    
    # Log rate
    log_imputation_rate(rate, str(log_path))
    
    # Check threshold
    if rate > MAX_IMPUTATION_RATE:
        error_log = DATA_DIR / "artifacts" / "imputation_error.log"
        with open(error_log, 'w') as f:
            f.write(f"ERROR: Imputation rate ({rate:.4f}) exceeded threshold ({MAX_IMPUTATION_RATE}).\n")
        print(f"ERROR: Imputation rate exceeded threshold. Check {error_log}", file=sys.stderr)
        sys.exit(1)

    # Final cleaning
    final_df = clean_and_prepare_data(imputed_df)
    
    # Write output
    final_df.to_csv(output_path, index=False)
    print(f"Successfully wrote imputed data to {output_path}")
    print(f"Imputation rate: {rate:.4f}")

if __name__ == "__main__":
    main()
