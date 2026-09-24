import os
import sys
import json
import pandas as pd
import numpy as np
from pathlib import Path

# Ensure imports match the existing API surface in utils
from utils.stoichiometry_parser import parse_formula, normalize_formula
from utils.periodic_data import get_atomic_radius, get_electronegativity, get_valence_electrons, get_atomic_number

# Constants for paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
INPUT_FILE = PROJECT_ROOT / "data" / "processed" / "cleaned_compositions.csv"
OUTPUT_FILE = PROJECT_ROOT / "data" / "processed" / "final_features.csv"
MAPPING_FILE = PROJECT_ROOT / "code" / "utils" / "mapping.json"

def calculate_weighted_mean(formula_dict, property_func):
    """
    Calculate the weighted average of a property based on stoichiometry.
    
    Args:
        formula_dict (dict): Dictionary of {element: count}
        property_func: Function to get the property value for an element string
    
    Returns:
        float: Weighted mean of the property, or np.nan if calculation fails
    """
    if not formula_dict:
        return np.nan
    
    total_atoms = sum(formula_dict.values())
    if total_atoms == 0:
        return np.nan
    
    weighted_sum = 0.0
    for element, count in formula_dict.items():
        try:
            val = property_func(element)
            if val is None or np.isnan(val):
                return np.nan
            weighted_sum += val * count
        except Exception:
            return np.nan
    
    return weighted_sum / total_atoms

def calculate_variance(formula_dict, property_func):
    """
    Calculate the variance of a property based on stoichiometry.
    
    Args:
        formula_dict (dict): Dictionary of {element: count}
        property_func: Function to get the property value for an element string
    
    Returns:
        float: Variance of the property, or np.nan if calculation fails
    """
    if not formula_dict:
        return np.nan
    
    total_atoms = sum(formula_dict.values())
    if total_atoms == 0:
        return np.nan
    
    # Calculate weighted mean first
    mean_val = calculate_weighted_mean(formula_dict, property_func)
    if np.isnan(mean_val):
        return np.nan
    
    weighted_sq_diff_sum = 0.0
    for element, count in formula_dict.items():
        try:
            val = property_func(element)
            if val is None or np.isnan(val):
                return np.nan
            weighted_sq_diff_sum += ((val - mean_val) ** 2) * count
        except Exception:
            return np.nan
    
    return weighted_sq_diff_sum / total_atoms

def engineer_features(df):
    """
    Engineer compositional features for the dataframe.
    
    Args:
        df (pd.DataFrame): Input dataframe with 'composition' and 'temperature' columns,
                           and 'material_family' column.
    
    Returns:
        pd.DataFrame: DataFrame with added engineered feature columns.
    """
    # Create a copy to avoid modifying the original
    result_df = df.copy()
    
    # Parse formulas
    result_df['parsed_formula'] = result_df['composition'].apply(
        lambda x: parse_formula(x) if isinstance(x, str) and pd.notna(x) else {}
    )
    
    # Calculate Mean Atomic Radius (weighted avg)
    result_df['mean_atomic_radius'] = result_df['parsed_formula'].apply(
        lambda d: calculate_weighted_mean(d, get_atomic_radius)
    )
    
    # Calculate Electronegativity Variance
    result_df['electronegativity_variance'] = result_df['parsed_formula'].apply(
        lambda d: calculate_variance(d, get_electronegativity)
    )
    
    # Calculate Valence Electron Concentration (VEC) (weighted avg)
    result_df['vec'] = result_df['parsed_formula'].apply(
        lambda d: calculate_weighted_mean(d, get_valence_electrons)
    )
    
    # Calculate Atomic Number Variance
    result_df['atomic_number_variance'] = result_df['parsed_formula'].apply(
        lambda d: calculate_variance(d, get_atomic_number)
    )
    
    # Ensure Temperature is numeric and a covariate
    if 'temperature' in result_df.columns:
        result_df['temperature'] = pd.to_numeric(result_df['temperature'], errors='coerce')
    else:
        # If missing, create a placeholder or handle as needed (spec implies it exists)
        result_df['temperature'] = np.nan
    
    # Ensure Material Family is categorical
    if 'material_family' in result_df.columns:
        result_df['material_family'] = result_df['material_family'].astype('category')
    else:
        result_df['material_family'] = 'Unknown'
    
    # Select final columns
    final_columns = [
        'material_family', 'temperature', 'mean_atomic_radius', 
        'electronegativity_variance', 'vec', 'atomic_number_variance'
    ]
    
    # Check if any other columns from original input should be preserved (e.g., Seebeck)
    # The task implies saving the engineered dataset. Usually, target variable (Seebeck) is needed for modeling.
    # Assuming 'seebeck' column exists from previous cleaning step (T012).
    if 'seebeck' in result_df.columns:
        final_columns.insert(0, 'seebeck')
    
    # Filter to final columns
    result_df = result_df[final_columns]
    
    # Drop rows with nulls in engineered features if strictly required, 
    # but task says "verify... has no nulls". We will drop rows that have NaN in feature columns.
    feature_cols = ['mean_atomic_radius', 'electronegativity_variance', 'vec', 'atomic_number_variance']
    result_df = result_df.dropna(subset=feature_cols)
    
    return result_df

def main():
    """Main entry point for feature engineering."""
    print(f"Loading data from: {INPUT_FILE}")
    if not INPUT_FILE.exists():
        print(f"ERROR: Input file {INPUT_FILE} does not exist. Run T011-T014 first.")
        sys.exit(1)
    
    df = pd.read_csv(INPUT_FILE)
    print(f"Loaded {len(df)} records.")
    
    print("Engineering features...")
    engineered_df = engineer_features(df)
    
    print(f"Engineered {len(engineered_df)} records after cleaning nulls.")
    
    # Verify columns
    expected_cols = ['mean_atomic_radius', 'electronegativity_variance', 'vec', 'atomic_number_variance', 'temperature', 'material_family']
    missing_cols = [c for c in expected_cols if c not in engineered_df.columns]
    if missing_cols:
        print(f"ERROR: Missing expected columns: {missing_cols}")
        sys.exit(1)
    
    # Verify no nulls in engineered feature columns
    feature_cols = ['mean_atomic_radius', 'electronegativity_variance', 'vec', 'atomic_number_variance']
    null_counts = engineered_df[feature_cols].isnull().sum()
    if null_counts.any():
        print(f"ERROR: Null values found in feature columns:\n{null_counts[null_counts > 0]}")
        sys.exit(1)
    
    # Save to output
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    engineered_df.to_csv(OUTPUT_FILE, index=False)
    print(f"Saved final engineered dataset to: {OUTPUT_FILE}")
    print(f"Columns: {list(engineered_df.columns)}")
    
    return True

if __name__ == "__main__":
    main()