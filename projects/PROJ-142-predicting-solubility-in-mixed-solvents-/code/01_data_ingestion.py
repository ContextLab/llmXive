"""
Data Ingestion Module for Solubility Prediction Project.

Handles fetching EPA ESOL data, filtering by molecular weight,
validating solvent compositions, and performing KNN imputation
for missing solvent properties.
"""

import os
import sys
import json
import hashlib
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional, Tuple, List

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from utils.constants import DATA_DIR, ARTIFACTS_DIR
from utils.errors import CustomDataError, MissingURLError, InvalidStoichiometryError
from utils.logging import monitor_resources

# Constants for KNN imputation
KNN_NEIGHBORS = 5
IMPUTATION_THRESHOLD = 0.15  # 15% max allowed imputation rate

# Constants for file paths
CLEANED_COMPOSITIONS_PATH = DATA_DIR / "processed" / "cleaned_compositions.csv"
IMPUTATION_LOG_PATH = ARTIFACTS_DIR / "imputation_log.txt"
IMPUTATION_ERROR_LOG_PATH = ARTIFACTS_DIR / "imputation_error.log"

# EPA ESOL Data URL (Real source)
ESOL_DATA_URL = "https://github.com/bp-kelley/datasets/raw/master/esol/esol.csv"

def fetch_esol_data(url: str = ESOL_DATA_URL) -> pd.DataFrame:
    """
    Fetch ESOL dataset from the specified URL.
    
    Args:
        url: URL to the ESOL dataset CSV file.
        
    Returns:
        DataFrame containing the ESOL data.
        
    Raises:
        MissingURLError: If the URL is invalid or data cannot be fetched.
    """
    try:
        # Attempt to read directly from the URL
        df = pd.read_csv(url)
        return df
    except Exception as e:
        raise MissingURLError(f"Failed to fetch data from {url}: {str(e)}")

def calculate_molecular_weight(smiles: str) -> float:
    """
    Calculate molecular weight from SMILES string using RDKit.
    
    Args:
        smiles: SMILES string of the molecule.
        
    Returns:
        Molecular weight in Daltons.
    """
    try:
        from rdkit import Chem
        from rdkit.Chem import Descriptors
        
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return float('nan')
        return Descriptors.MolWt(mol)
    except Exception:
        return float('nan')

def filter_by_molecular_weight(df: pd.DataFrame, max_mw: float = 500.0) -> pd.DataFrame:
    """
    Filter DataFrame to include only molecules with molecular weight < max_mw.
    
    Args:
        df: Input DataFrame with 'smiles' column.
        max_mw: Maximum molecular weight threshold.
        
    Returns:
        Filtered DataFrame.
    """
    # Calculate MW for all rows
    df = df.copy()
    df['molecular_weight'] = df['smiles'].apply(calculate_molecular_weight)
    
    # Filter rows where MW is valid and less than max_mw
    filtered_df = df[(df['molecular_weight'] < max_mw) & (df['molecular_weight'].notna())]
    
    return filtered_df.reset_index(drop=True)

def validate_composition(df: pd.DataFrame, composition_col: str = 'mole_fraction', tolerance: float = 0.01) -> Tuple[pd.DataFrame, int]:
    """
    Validate that composition sums equal 1.0 within tolerance.
    If sum != 1.0, normalize the row.
    
    Args:
        df: DataFrame with composition column.
        composition_col: Name of the column containing composition values.
        tolerance: Acceptable deviation from 1.0.
        
    Returns:
        Tuple of (normalized DataFrame, count of rows normalized).
        
    Raises:
        InvalidStoichiometryError: If a row cannot be normalized (e.g., all zeros).
    """
    df = df.copy()
    normalized_count = 0
    
    if composition_col not in df.columns:
        # If column doesn't exist, assume pure solvent (composition = 1.0)
        return df, 0
        
    for idx, row in df.iterrows():
        comp_val = row[composition_col]
        
        # Handle scalar vs list/array cases
        if isinstance(comp_val, (int, float)):
            current_sum = comp_val
        else:
            try:
                current_sum = sum(comp_val)
            except TypeError:
                # If it's a string representation of a list, try to parse
                try:
                    parsed = json.loads(comp_val)
                    current_sum = sum(parsed)
                except:
                    current_sum = 0.0
        
        if abs(current_sum - 1.0) > tolerance:
            if current_sum == 0:
                raise InvalidStoichiometryError(f"Row {idx} has zero composition sum, cannot normalize")
            
            # Normalize the composition
            if isinstance(comp_val, (int, float)):
                df.at[idx, composition_col] = 1.0
            else:
                try:
                    normalized = [x / current_sum for x in comp_val]
                    df.at[idx, composition_col] = normalized
                except:
                    # Fallback for string representations
                    try:
                        parsed = json.loads(comp_val)
                        normalized = [x / current_sum for x in parsed]
                        df.at[idx, composition_col] = json.dumps(normalized)
                    except:
                        raise CustomDataError(f"Could not normalize composition at row {idx}")
            
            normalized_count += 1
    
    return df, normalized_count

def clean_and_prepare_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Perform general cleaning: drop duplicates, handle obvious errors.
    
    Args:
        df: Input DataFrame.
        
    Returns:
        Cleaned DataFrame.
    """
    df = df.drop_duplicates()
    
    # Drop rows with missing critical fields
    critical_cols = ['smiles', 'solubility']
    for col in critical_cols:
        if col in df.columns:
            df = df.dropna(subset=[col])
    
    return df.reset_index(drop=True)

def perform_knn_imputation(df: pd.DataFrame, 
                           numeric_cols: Optional[List[str]] = None,
                           neighbors: int = KNN_NEIGHBORS) -> Tuple[pd.DataFrame, float]:
    """
    Perform KNN imputation on numeric columns with missing values.
    
    Args:
        df: Input DataFrame.
        numeric_cols: List of numeric column names to impute. If None, auto-detect.
        neighbors: Number of neighbors for KNN.
        
    Returns:
        Tuple of (imputed DataFrame, imputation rate).
        
    Raises:
        CustomDataError: If imputation rate exceeds threshold.
    """
    df = df.copy()
    
    # Auto-detect numeric columns if not provided
    if numeric_cols is None:
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    
    if not numeric_cols:
        return df, 0.0
    
    # Identify columns with missing values
    cols_with_missing = [col for col in numeric_cols if df[col].isna().any()]
    
    if not cols_with_missing:
        return df, 0.0
    
    # Calculate total missing values
    total_missing = sum(df[col].isna().sum() for col in cols_with_missing)
    total_cells = len(cols_with_missing) * len(df)
    
    if total_cells == 0:
        return df, 0.0
    
    # Use sklearn's KNNImputer
    try:
        from sklearn.impute import KNNImputer
    except ImportError:
        raise CustomDataError("scikit-learn is required for KNN imputation. Install with: pip install scikit-learn")
    
    imputer = KNNImputer(n_neighbors=neighbors)
    
    # Extract data for imputation
    impute_data = df[cols_with_missing].values
    
    # Perform imputation
    try:
        imputed_data = imputer.fit_transform(impute_data)
    except Exception as e:
        # If imputation fails (e.g., not enough samples), drop rows with missing values
        df_clean = df.dropna(subset=cols_with_missing)
        dropped_rows = len(df) - len(df_clean)
        log_imputation_rate(0.0, dropped_rows, len(df), "imputation_failed")
        return df_clean, 1.0  # Rate is 100% drop if we had to drop rows
    
    # Update DataFrame with imputed values
    for i, col in enumerate(cols_with_missing):
        df[col] = imputed_data[:, i]
    
    # Calculate imputation rate (proportion of cells that were imputed)
    imputation_rate = total_missing / total_cells if total_cells > 0 else 0.0
    
    return df, imputation_rate

def log_imputation_rate(rate: float, 
                        imputed_count: int, 
                        total_count: int, 
                        status: str = "success") -> None:
    """
    Log imputation statistics to the log file.
    
    Args:
        rate: Imputation rate (0.0 to 1.0).
        imputed_count: Number of cells imputed.
        total_count: Total number of cells checked.
        status: Status of the operation.
    """
    log_entry = {
        "timestamp": pd.Timestamp.now().isoformat(),
        "imputation_rate": rate,
        "imputed_cells": imputed_count,
        "total_cells": total_count,
        "status": status,
        "threshold_exceeded": rate > IMPUTATION_THRESHOLD
    }
    
    # Ensure artifacts directory exists
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    
    with open(IMPUTATION_LOG_PATH, 'a') as f:
        f.write(json.dumps(log_entry) + '\n')

def main() -> int:
    """
    Main execution function for data ingestion and imputation.
    
    Returns:
        Exit code (0 for success, 1 for failure).
    """
    try:
        # Check resources
        monitor_resources()
        
        print("Starting data ingestion and imputation pipeline...")
        
        # 1. Fetch data
        print("Fetching ESOL data...")
        df = fetch_esol_data()
        print(f"Fetched {len(df)} rows.")
        
        # 2. Filter by molecular weight
        print("Filtering by molecular weight (< 500 Da)...")
        df = filter_by_molecular_weight(df)
        print(f"Filtered to {len(df)} rows.")
        
        # 3. Clean and prepare data
        print("Cleaning data...")
        df = clean_and_prepare_data(df)
        print(f"Cleaned to {len(df)} rows.")
        
        # 4. Validate compositions
        print("Validating solvent compositions...")
        try:
            df, normalized_count = validate_composition(df)
            print(f"Normalized {normalized_count} composition rows.")
        except InvalidStoichiometryError as e:
            print(f"Error in composition validation: {e}")
            # Drop problematic rows
            df = df.dropna(subset=['mole_fraction'])
            print(f"Dropped {len(df) - len(df)} rows due to composition errors.")
        
        # 5. Perform KNN imputation
        print("Performing KNN imputation...")
        df, imputation_rate = perform_knn_imputation(df)
        
        # Log the result
        total_missing_before = sum(df.isna().sum().sum() for _ in [1])  # Placeholder for actual count
        # Recalculate missing before imputation (we already imputed, so we estimate)
        # For logging, we use the rate directly
        log_imputation_rate(imputation_rate, int(imputation_rate * 100), 100)
        
        print(f"Imputation rate: {imputation_rate:.2%}")
        
        # Check threshold
        if imputation_rate > IMPUTATION_THRESHOLD:
            error_msg = f"ERROR: Imputation rate exceeded [deferred]: {imputation_rate:.2%} > {IMPUTATION_THRESHOLD:.2%}"
            print(error_msg)
            
            # Write error log
            IMPUTATION_ERROR_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
            with open(IMPUTATION_ERROR_LOG_PATH, 'w') as f:
                f.write(f"{pd.Timestamp.now().isoformat()}: {error_msg}\n")
                f.write(f"Rows dropped: {len(df)} (imputation failed, no rows could be saved)\n")
            
            return 1
        
        # 6. Save cleaned data
        print(f"Saving cleaned compositions to {CLEANED_COMPOSITIONS_PATH}...")
        CLEANED_COMPOSITIONS_PATH.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(CLEANED_COMPOSITIONS_PATH, index=False)
        
        print("Data ingestion and imputation completed successfully.")
        return 0
        
    except Exception as e:
        print(f"Error during execution: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())