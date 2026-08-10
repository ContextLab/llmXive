import os
import sys
import json
import pandas as pd
import numpy as np
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.periodic_data import (
    get_atomic_radius,
    get_electronegativity,
    get_valence_electrons,
    get_atomic_number
)
from utils.stoichiometry_parser import parse_formula

def calculate_weighted_mean(formula_str: str, property_func) -> float:
    """
    Calculate the weighted average of a property based on stoichiometry.
    
    Args:
        formula_str: Chemical formula string (e.g., "Bi2Te3")
        property_func: Function to get property value for an element symbol
        
    Returns:
        Weighted average of the property, or np.nan if calculation fails
    """
    try:
        composition = parse_formula(formula_str)
        if not composition:
            return np.nan
        
        total_atoms = sum(composition.values())
        if total_atoms == 0:
            return np.nan
        
        weighted_sum = 0.0
        for element, count in composition.items():
            try:
                prop_val = property_func(element)
                if prop_val is None:
                    return np.nan
                weighted_sum += prop_val * count
            except Exception:
                return np.nan
        
        return weighted_sum / total_atoms
    except Exception:
        return np.nan

def calculate_variance(formula_str: str, property_func) -> float:
    """
    Calculate the variance of a property based on stoichiometry.
    
    Args:
        formula_str: Chemical formula string (e.g., "Bi2Te3")
        property_func: Function to get property value for an element symbol
        
    Returns:
        Variance of the property, or np.nan if calculation fails
    """
    try:
        composition = parse_formula(formula_str)
        if not composition:
            return np.nan
        
        total_atoms = sum(composition.values())
        if total_atoms == 0:
            return np.nan
        
        values = []
        weights = []
        for element, count in composition.items():
            try:
                prop_val = property_func(element)
                if prop_val is None:
                    return np.nan
                values.append(prop_val)
                weights.append(count)
            except Exception:
                return np.nan
        
        if not values:
            return np.nan
        
        # Weighted mean
        mean_val = np.average(values, weights=weights)
        
        # Weighted variance
        variance = np.average([(v - mean_val) ** 2 for v in values], weights=weights)
        return variance
    except Exception:
        return np.nan

def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add engineered compositional features to the DataFrame.
    
    Args:
        df: DataFrame with 'composition' and 'temperature' columns
            
    Returns:
        DataFrame with added feature columns
    """
    df = df.copy()
    
    # Ensure we have necessary columns
    if 'composition' not in df.columns:
        raise ValueError("DataFrame must contain 'composition' column")
    
    # Calculate Mean Atomic Radius (weighted avg)
    print("Calculating Mean Atomic Radius...")
    df['mean_atomic_radius'] = df['composition'].apply(
        lambda x: calculate_weighted_mean(x, get_atomic_radius)
    )
    
    # Calculate Electronegativity Variance
    print("Calculating Electronegativity Variance...")
    df['electronegativity_variance'] = df['composition'].apply(
        lambda x: calculate_variance(x, get_electronegativity)
    )
    
    # Calculate Valence Electron Concentration (VEC) (weighted avg)
    print("Calculating VEC...")
    df['vec'] = df['composition'].apply(
        lambda x: calculate_weighted_mean(x, get_valence_electrons)
    )
    
    # Calculate Atomic Number Variance
    print("Calculating Atomic Number Variance...")
    df['atomic_number_variance'] = df['composition'].apply(
        lambda x: calculate_variance(x, get_atomic_number)
    )
    
    # Ensure Temperature is present (if not, fill with a default or keep existing)
    if 'temperature' not in df.columns:
        # If temperature is missing, we might need to handle it based on context
        # For now, we'll assume it might be present in raw data or handle missing
        df['temperature'] = np.nan
    
    # Ensure Material Family is present
    if 'material_family' not in df.columns:
        raise ValueError("DataFrame must contain 'material_family' column (from T013)")
    
    # Handle potential nulls in engineered features by dropping or imputing
    # For this task, we will drop rows where critical engineered features are null
    feature_cols = ['mean_atomic_radius', 'electronegativity_variance', 'vec', 'atomic_number_variance']
    initial_count = len(df)
    df = df.dropna(subset=feature_cols)
    dropped_count = initial_count - len(df)
    if dropped_count > 0:
        print(f"Dropped {dropped_count} rows due to null engineered features.")
    
    # Select and order final columns as per spec
    final_cols = [
        'mean_atomic_radius',
        'electronegativity_variance',
        'vec',
        'atomic_number_variance',
        'temperature',
        'material_family'
    ]
    
    # Ensure all final columns exist (add missing ones with NaN if necessary, though spec implies they exist)
    for col in final_cols:
        if col not in df.columns:
            df[col] = np.nan
    
    return df[final_cols]

def main():
    """
    Main execution function for T020.
    Loads cleaned data, engineers features, and saves final CSV.
    """
    # Define paths relative to project root
    project_root = Path(__file__).parent.parent
    input_path = project_root / "data" / "processed" / "cleaned_compositions.csv"
    output_path = project_root / "data" / "processed" / "final_features.csv"
    
    if not input_path.exists():
        print(f"ERROR: Input file not found: {input_path}")
        print("T011/T012/T013 must complete first to generate cleaned_compositions.csv")
        sys.exit(1)
    
    print(f"Loading data from {input_path}...")
    try:
        df = pd.read_csv(input_path)
    except Exception as e:
        print(f"ERROR: Failed to load input CSV: {e}")
        sys.exit(1)
    
    print(f"Loaded {len(df)} records.")
    
    # Engineer features
    print("Engineering features...")
    df_engineered = engineer_features(df)
    
    # Verify no nulls in engineered feature columns
    feature_cols = ['mean_atomic_radius', 'electronegativity_variance', 'vec', 'atomic_number_variance']
    null_counts = df_engineered[feature_cols].isnull().sum()
    if null_counts.any():
        print(f"WARNING: Null values found in engineered features after processing:\n{null_counts}")
        # If strict, we might exit, but we already dropped them in engineer_features
        # If any remain (e.g., in temperature), it's not a hard fail for this specific task's verification
        # unless the task requires NO nulls in ANY column. The task says "no nulls in engineered feature columns".
    
    # Save to final CSV
    print(f"Saving final dataset to {output_path}...")
    df_engineered.to_csv(output_path, index=False)
    
    # Verification
    if output_path.exists():
        final_df = pd.read_csv(output_path)
        print(f"Successfully saved {len(final_df)} records to {output_path}")
        
        # Check columns
        expected_cols = ['mean_atomic_radius', 'electronegativity_variance', 'vec', 'atomic_number_variance', 'temperature', 'material_family']
        missing_cols = [c for c in expected_cols if c not in final_df.columns]
        if missing_cols:
            print(f"ERROR: Missing expected columns: {missing_cols}")
            sys.exit(1)
        
        # Check for nulls in engineered features
        nulls_in_features = final_df[feature_cols].isnull().sum().sum()
        if nulls_in_features > 0:
            print(f"ERROR: Found {nulls_in_features} null values in engineered feature columns.")
            sys.exit(1)
        
        print("Verification passed: File exists, columns present, no nulls in engineered features.")
    else:
        print("ERROR: Output file was not created.")
        sys.exit(1)

if __name__ == "__main__":
    main()
