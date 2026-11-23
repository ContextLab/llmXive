"""
Variable Selection Module for Species Distribution Modeling.

Implements Variance Inflation Factor (VIF) analysis to select a non-collinear
subset of climate variables for modeling, as required by task T015a.

This module:
1. Loads a stratified sample of occurrence data with extracted climate variables.
2. Calculates VIF for all 19 Bioclim variables.
3. Iteratively removes the variable with the highest VIF until all remaining
   variables have VIF < 5.
4. Outputs the list of selected variable names to metrics/selected_climate_variables.json.
"""
import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

import pandas as pd
import numpy as np
from statsmodels.stats.outliers_influence import variance_inflation_factor

# Add project root to path if running as script
if __name__ == "__main__":
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root))

from config import DATA_DIR, METRICS_DIR, RND_SEED
from logging_config import get_logger

logger = get_logger("variable_selection")


def load_sampled_data(input_path: str, sample_size: int = 5000, seed: int = 42) -> pd.DataFrame:
    """
    Load occurrence data and create a stratified sample by species.
    
    Args:
        input_path: Path to the CSV file with occurrence data and climate variables.
        sample_size: Total number of samples to draw.
        seed: Random seed for reproducibility.
        
    Returns:
        A DataFrame with the stratified sample.
    """
    logger.log("load_sampled_data", input=input_path, sample_size=sample_size, seed=seed)
    
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    df = pd.read_csv(input_path)
    
    # Identify species column (assuming 'species' based on task context)
    if 'species' not in df.columns:
        raise ValueError("Input CSV must contain a 'species' column for stratified sampling.")
    
    # Calculate samples per species (proportional)
    species_counts = df['species'].value_counts()
    samples_per_species = {}
    remaining = sample_size
    
    # Sort by count descending to ensure rare species get at least 1 sample if possible
    for species, count in species_counts.sort_values(ascending=False).items():
        if remaining <= 0:
            break
        # Calculate proportional share, ensure at least 1 if possible
        share = max(1, int((count / len(df)) * sample_size))
        if share > count:
            share = count
        samples_per_species[species] = share
        remaining -= share
    
    # If we still have remaining slots, distribute them
    if remaining > 0:
        for species in samples_per_species:
            if remaining <= 0:
                break
            if samples_per_species[species] < species_counts[species]:
                samples_per_species[species] += 1
                remaining -= 1
    
    # Perform stratified sampling
    sampled_dfs = []
    for species, n in samples_per_species.items():
        species_df = df[df['species'] == species]
        if len(species_df) > n:
            sample = species_df.sample(n=n, random_state=seed)
        else:
            sample = species_df
        sampled_dfs.append(sample)
    
    result = pd.concat(sampled_dfs, ignore_index=True)
    logger.log("load_sampled_data_success", total_samples=len(result))
    return result


def calculate_vif(df: pd.DataFrame, features: List[str]) -> pd.DataFrame:
    """
    Calculate Variance Inflation Factor for each feature.
    
    Args:
        df: DataFrame containing the features.
        features: List of feature column names.
        
    Returns:
        DataFrame with feature names and their VIF values.
    """
    logger.log("calculate_vif", num_features=len(features))
    
    # Handle missing values by dropping rows (for VIF calculation only)
    # In a production pipeline, we might want to be more careful here
    df_clean = df[features].dropna()
    
    if len(df_clean) < len(features) + 1:
        logger.log("calculate_vif_warning", 
                   message="Not enough samples to calculate VIF reliably",
                   samples=len(df_clean),
                   features=len(features))
        # Return NaN for all if we can't calculate
        return pd.DataFrame({
            'variable': features,
            'vif': [np.nan] * len(features)
        })
    
    # Add intercept column for VIF calculation
    X = df_clean[features]
    X = X.values
    
    vif_data = []
    for i, feature in enumerate(features):
        try:
            vif = variance_inflation_factor(X, i)
            vif_data.append({'variable': feature, 'vif': vif})
        except Exception as e:
            logger.log("calculate_vif_error", 
                       variable=feature, 
                       error=str(e))
            vif_data.append({'variable': feature, 'vif': np.nan})
    
    return pd.DataFrame(vif_data)


def select_variables_by_vif(
    df: pd.DataFrame, 
    features: List[str], 
    max_vif: float = 5.0,
    min_features: int = 1
) -> List[str]:
    """
    Iteratively remove features with VIF > max_vif until all remaining
    features have VIF < max_vif.
    
    Args:
        df: DataFrame containing the features.
        features: List of all candidate feature names.
        max_vif: Maximum allowed VIF threshold.
        min_features: Minimum number of features to keep.
        
    Returns:
        List of selected feature names.
    """
    logger.log("select_variables_by_vif", 
               initial_features=len(features), 
               max_vif=max_vif, 
               min_features=min_features)
    
    selected_features = features.copy()
    iteration = 0
    
    while True:
        iteration += 1
        logger.log("vif_iteration", iteration=iteration, 
                   remaining_features=len(selected_features))
        
        # Calculate VIF for current features
        vif_df = calculate_vif(df, selected_features)
        
        # Find max VIF
        max_vif_value = vif_df['vif'].max()
        
        if max_vif_value < max_vif or len(selected_features) <= min_features:
            logger.log("vif_converged", 
                       final_features=selected_features,
                       max_vif_reached=max_vif_value)
            break
        
        # Identify variable with highest VIF
        max_vif_row = vif_df.loc[vif_df['vif'].idxmax()]
        variable_to_remove = max_vif_row['variable']
        
        logger.log("removing_variable", 
                   variable=variable_to_remove, 
                   vif=max_vif_row['vif'])
        
        selected_features.remove(variable_to_remove)
        
        # Safety check to prevent infinite loops
        if iteration > len(features):
            logger.log("vif_safety_stop", 
                       message="Iteration limit reached, stopping VIF selection")
            break
    
    logger.log("vif_selection_complete", 
               selected_count=len(selected_features),
               selected_features=selected_features)
    return selected_features


def identify_climate_columns(df: pd.DataFrame) -> List[str]:
    """
    Identify all climate variable columns (bio1 through bio19).
    
    Args:
        df: DataFrame to scan for climate columns.
        
    Returns:
        List of climate column names.
    """
    climate_vars = []
    for col in df.columns:
        # Check for standard Bioclim naming (bio1, bio2, ..., bio19)
        if col.lower().startswith('bio') and col[3:].isdigit():
            num = int(col[3:])
            if 1 <= num <= 19:
                climate_vars.append(col)
        # Also check for alternative naming patterns if needed
        elif col.lower() in ['bio1', 'bio2', 'bio3', 'bio4', 'bio5', 'bio6', 
                             'bio7', 'bio8', 'bio9', 'bio10', 'bio11', 'bio12',
                             'bio13', 'bio14', 'bio15', 'bio16', 'bio17', 'bio18', 'bio19']:
            if col not in climate_vars:
                climate_vars.append(col)
    
    # Sort to ensure consistent ordering
    climate_vars.sort(key=lambda x: int(x[3:]))
    return climate_vars


def save_selected_variables(selected_features: List[str], output_path: str) -> None:
    """
    Save the list of selected variables to a JSON file.
    
    Args:
        selected_features: List of selected variable names.
        output_path: Path to the output JSON file.
    """
    logger.log("save_selected_variables", 
               num_variables=len(selected_features),
               output=output_path)
    
    output_data = {
        "selected_variables": selected_features,
        "count": len(selected_features),
        "timestamp": datetime.utcnow().isoformat(),
        "method": "VIF",
        "threshold": 5.0,
        "reason": "Variables selected via iterative VIF analysis (threshold < 5) for modeling efficiency. Full dataset remains available in data/processed/."
    }
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    logger.log("save_selected_variables_success", output_path=output_path)


def run_variable_selection(
    input_path: str,
    output_path: str,
    sample_size: int = 5000,
    seed: int = 42,
    max_vif: float = 5.0
) -> List[str]:
    """
    Main function to run the full variable selection pipeline.
    
    Args:
        input_path: Path to the input CSV with occurrence and climate data.
        output_path: Path to save the selected variables JSON.
        sample_size: Number of samples to use for VIF calculation.
        seed: Random seed for reproducibility.
        max_vif: Maximum allowed VIF threshold.
        
    Returns:
        List of selected variable names.
    """
    logger.log("run_variable_selection_start", 
               input=input_path, 
               output=output_path,
               sample_size=sample_size)
    
    # Step 1: Load and sample data
    sampled_df = load_sampled_data(input_path, sample_size=sample_size, seed=seed)
    
    # Step 2: Identify climate variables
    climate_vars = identify_climate_columns(sampled_df)
    
    if not climate_vars:
        raise ValueError("No climate variables (bio1-bio19) found in input data.")
    
    logger.log("climate_vars_found", count=len(climate_vars), vars=climate_vars)
    
    # Step 3: Perform VIF-based selection
    selected_vars = select_variables_by_vif(
        sampled_df, 
        climate_vars, 
        max_vif=max_vif
    )
    
    # Step 4: Save results
    save_selected_variables(selected_vars, output_path)
    
    logger.log("run_variable_selection_complete", 
               selected_count=len(selected_vars))
    
    return selected_vars


def main():
    """
    Entry point for the variable selection script.
    
    Expected usage:
    python code/variable_selection.py --input data/processed/occurrence_with_climate.csv --output metrics/selected_climate_variables.json
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Perform VIF-based variable selection for climate variables.")
    parser.add_argument("--input", type=str, required=True,
                      help="Path to input CSV with occurrence and climate data")
    parser.add_argument("--output", type=str, required=True,
                      help="Path to output JSON file for selected variables")
    parser.add_argument("--sample-size", type=int, default=5000,
                      help="Number of samples to use for VIF calculation")
    parser.add_argument("--seed", type=int, default=42,
                      help="Random seed for reproducibility")
    parser.add_argument("--max-vif", type=float, default=5.0,
                      help="Maximum allowed VIF threshold")
    
    args = parser.parse_args()
    
    try:
        selected_vars = run_variable_selection(
            input_path=args.input,
            output_path=args.output,
            sample_size=args.sample_size,
            seed=args.seed,
            max_vif=args.max_vif
        )
        print(f"Variable selection complete. Selected {len(selected_vars)} variables.")
        print(f"Selected variables: {selected_vars}")
        print(f"Results saved to: {args.output}")
    except Exception as e:
        logger.log("run_variable_selection_error", error=str(e))
        print(f"Error during variable selection: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
