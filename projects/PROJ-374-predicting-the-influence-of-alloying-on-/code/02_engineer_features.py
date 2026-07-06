import os
import sys
import json
import pandas as pd
import numpy as np
from utils.periodic_data import (
    get_atomic_radius,
    get_electronegativity,
    get_valence_electrons,
    get_atomic_number
)
from utils.stoichiometry_parser import parse_formula

def calculate_weighted_mean(composition_str, property_func):
    """
    Calculate the weighted mean of a property based on stoichiometry.
    
    Args:
        composition_str: String like "Bi2Te3"
        property_func: Function that takes element symbol and returns property value
        
    Returns:
        float: Weighted mean property value
    """
    if not composition_str or not isinstance(composition_str, str):
        return np.nan
        
    try:
        composition = parse_formula(composition_str)
        total_atoms = sum(composition.values())
        
        if total_atoms == 0:
            return np.nan
            
        weighted_sum = 0.0
        for element, count in composition.items():
            try:
                prop_value = property_func(element)
                if prop_value is None or np.isnan(prop_value):
                    return np.nan
                weighted_sum += prop_value * count
            except Exception:
                return np.nan
                
        return weighted_sum / total_atoms
    except Exception:
        return np.nan

def calculate_variance(composition_str, property_func):
    """
    Calculate the variance of a property based on stoichiometry.
    
    Args:
        composition_str: String like "Bi2Te3"
        property_func: Function that takes element symbol and returns property value
        
    Returns:
        float: Variance of the property values weighted by composition
    """
    if not composition_str or not isinstance(composition_str, str):
        return np.nan
        
    try:
        composition = parse_formula(composition_str)
        total_atoms = sum(composition.values())
        
        if total_atoms == 0:
            return np.nan
            
        # First calculate the weighted mean
        mean_val = calculate_weighted_mean(composition_str, property_func)
        if np.isnan(mean_val):
            return np.nan
            
        # Calculate weighted variance
        weighted_sq_diff_sum = 0.0
        for element, count in composition.items():
            try:
                prop_value = property_func(element)
                if prop_value is None or np.isnan(prop_value):
                    return np.nan
                diff = prop_value - mean_val
                weighted_sq_diff_sum += (diff ** 2) * count
            except Exception:
                return np.nan
                
        return weighted_sq_diff_sum / total_atoms
    except Exception:
        return np.nan

def engineer_features(df):
    """
    Add compositional features to the dataframe.
    
    Args:
        df: DataFrame with 'formula' column
        
    Returns:
        DataFrame with added feature columns
    """
    # Create a copy to avoid modifying original
    result_df = df.copy()
    
    # Calculate Mean Atomic Radius (weighted avg)
    result_df['mean_atomic_radius'] = result_df['formula'].apply(
        lambda x: calculate_weighted_mean(x, get_atomic_radius)
    )
    
    # Calculate Electronegativity Variance
    result_df['electronegativity_variance'] = result_df['formula'].apply(
        lambda x: calculate_variance(x, get_electronegativity)
    )
    
    # Calculate Valence Electron Concentration (VEC) (weighted avg)
    result_df['vec'] = result_df['formula'].apply(
        lambda x: calculate_weighted_mean(x, get_valence_electrons)
    )
    
    # Calculate Atomic Number Variance
    result_df['atomic_number_variance'] = result_df['formula'].apply(
        lambda x: calculate_variance(x, get_atomic_number)
    )
    
    # Temperature is already a covariate (assumed to be in the input df or added externally)
    # Material Family is already a categorical feature (assumed to be in the input df)
    
    return result_df

def main():
    """
    Main function to engineer features and save the final dataset.
    """
    # Define paths relative to project root
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    input_path = os.path.join(base_dir, 'data', 'processed', 'cleaned_compositions.csv')
    output_path = os.path.join(base_dir, 'data', 'processed', 'final_features.csv')
    
    # Check if input file exists
    if not os.path.exists(input_path):
        print(f"Error: Input file not found at {input_path}")
        sys.exit(1)
        
    # Load the cleaned data
    try:
        df = pd.read_csv(input_path)
        print(f"Loaded {len(df)} records from {input_path}")
    except Exception as e:
        print(f"Error loading input file: {e}")
        sys.exit(1)
        
    # Verify required columns exist
    required_cols = ['formula']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        print(f"Error: Missing required columns: {missing_cols}")
        sys.exit(1)
        
    # Engineer features
    print("Engineering features...")
    df_engineered = engineer_features(df)
    
    # Ensure Temperature and Material Family are present (they should be from T019)
    # If not, we assume they were added in T019, but let's check
    if 'temperature' not in df_engineered.columns:
        print("Warning: 'temperature' column not found. Adding placeholder (should be set by T019).")
        df_engineered['temperature'] = 300.0  # Default value if missing
        
    if 'material_family' not in df_engineered.columns:
        print("Warning: 'material_family' column not found. Adding placeholder (should be set by T019).")
        df_engineered['material_family'] = 'Unknown'
        
    # Check for nulls in engineered feature columns
    engineered_cols = ['mean_atomic_radius', 'electronegativity_variance', 
                     'vec', 'atomic_number_variance']
    null_counts = df_engineered[engineered_cols].isnull().sum()
    total_nulls = null_counts.sum()
    
    if total_nulls > 0:
        print(f"Warning: Found {total_nulls} null values in engineered feature columns:")
        print(null_counts)
        # We proceed anyway as the task asks to verify, not necessarily to halt
        # But in a real pipeline, we might want to filter these out
        
    # Save to CSV
    try:
        df_engineered.to_csv(output_path, index=False)
        print(f"Successfully saved {len(df_engineered)} records to {output_path}")
        
        # Verify output
        if os.path.exists(output_path):
            output_df = pd.read_csv(output_path)
            expected_cols = ['mean_atomic_radius', 'electronegativity_variance', 
                           'vec', 'atomic_number_variance', 'temperature', 'material_family']
            missing_output_cols = [col for col in expected_cols if col not in output_df.columns]
            if missing_output_cols:
                print(f"Error: Output file missing expected columns: {missing_output_cols}")
                sys.exit(1)
            print("Verification: Output file contains all expected columns.")
        else:
            print("Error: Output file was not created.")
            sys.exit(1)
            
    except Exception as e:
        print(f"Error saving output file: {e}")
        sys.exit(1)
        
    print("Feature engineering complete.")

if __name__ == "__main__":
    main()
