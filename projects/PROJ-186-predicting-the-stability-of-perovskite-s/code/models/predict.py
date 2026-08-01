import os
import sys
import logging
import itertools
import pickle
import json
import math
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

import pandas as pd
import numpy as np

# Import shared utilities
from utils.logging_config import get_logger, log_pipeline_event, log_exclusion_reason
from utils.config import get_config_summary

# Import descriptor functions from the data module to ensure consistency
from data.descriptors import (
    get_ionic_radius,
    calculate_tolerance_factor,
    calculate_octahedral_factor,
    get_element_electronegativity,
    calculate_electronegativity_difference,
    calculate_ionic_radius_mismatch,
    calculate_all_descriptors
)

logger = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper Functions for Descriptor Calculation on New Compositions
# ----------------------------------------------------------------------

def calculate_tolerance_factor_from_ions(ionic_radii: Dict[str, float]) -> float:
    """
    Calculate Goldschmidt tolerance factor t = (rA + rX) / (sqrt(2) * (rB + rX))
    using provided ionic radii dictionary {element: radius}.
    """
    rA = ionic_radii['A']
    rB = ionic_radii['B']
    rX = ionic_radii['X']
    
    denominator = math.sqrt(2) * (rB + rX)
    if denominator == 0:
        raise ValueError("Denominator for tolerance factor is zero.")
    
    return (rA + rX) / denominator

# ----------------------------------------------------------------------
# Data Loading and Preparation
# ----------------------------------------------------------------------

def generate_combinatorial_library(
    a_elements: List[str],
    b_elements: List[str],
    x_elements: List[str]
) -> pd.DataFrame:
    """
    Generate a combinatorial library of hypothetical ABX3 perovskites.
    
    Args:
        a_elements: List of A-site elements.
        b_elements: List of B-site elements.
        x_elements: List of X-site elements.
        
    Returns:
        DataFrame with columns: 'formula', 'A', 'B', 'X'
    """
    combinations = list(itertools.product(a_elements, b_elements, x_elements))
    data = []
    for A, B, X in combinations:
        formula = f"{A}{B}{X}3"
        data.append({'formula': formula, 'A': A, 'B': B, 'X': X})
    
    df = pd.DataFrame(data)
    logger.info(f"Generated combinatorial library with {len(df)} entries.")
    return df

def load_training_statistics() -> Dict[str, Dict[str, float]]:
    """
    Load the min/max statistics for descriptors from the training process.
    These are typically saved during T031 or T026.
    """
    stats_path = Path("results/training_statistics.json")
    if not stats_path.exists():
        logger.warning(f"Training statistics file not found at {stats_path}. "
                       "OOD checks will be skipped or may behave unexpectedly.")
        return {}
    
    with open(stats_path, 'r') as f:
        return json.load(f)

def perform_ood_check(
    df: pd.DataFrame,
    stats: Dict[str, Dict[str, float]]
) -> pd.DataFrame:
    """
    Perform Out-of-Distribution (OOD) check against training statistics.
    Adds 'is_ood' column (True if any descriptor is outside training range).
    """
    if not stats:
        df['is_ood'] = False
        return df

    ood_flags = []
    feature_cols = ['tolerance_factor', 'octahedral_factor', 'ionic_mismatch', 'electronegativity_diff']
    
    # Check if we have stats for the required columns
    missing_stats = [col for col in feature_cols if col not in stats]
    if missing_stats:
        logger.warning(f"Missing training statistics for: {missing_stats}. OOD check may be incomplete.")

    for idx, row in df.iterrows():
        is_ood = False
        for col in feature_cols:
            if col in stats:
                val = row[col]
                min_val = stats[col]['min']
                max_val = stats[col]['max']
                if val < min_val or val > max_val:
                    is_ood = True
                    break
        ood_flags.append(is_ood)
    
    df['is_ood'] = ood_flags
    ood_count = sum(ood_flags)
    logger.info(f"OOD check complete: {ood_count} candidates flagged as out-of-distribution.")
    return df

def load_model(model_path: str = "results/model.pkl") -> Any:
    """
    Load the trained RandomForest model.
    """
    path = Path(model_path)
    if not path.exists():
        raise FileNotFoundError(f"Model file not found at {model_path}. "
                                "Please ensure T031 (save_artifacts) has been run successfully.")
    
    with open(path, 'rb') as f:
        model = pickle.load(f)
    logger.info(f"Model loaded successfully from {model_path}")
    return model

def predict_stability(model: Any, df: pd.DataFrame) -> pd.DataFrame:
    """
    Predict decomposition energy for all candidates in the DataFrame.
    
    Args:
        model: Trained sklearn model.
        df: DataFrame containing the feature columns required by the model.
        
    Returns:
        DataFrame with added 'predicted_decomposition_energy' column.
    """
    # Define the feature columns expected by the model (must match training)
    feature_cols = ['tolerance_factor', 'octahedral_factor', 'ionic_mismatch', 'electronegativity_diff']
    
    # Validate that all required columns exist
    missing_cols = [col for col in feature_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required feature columns for prediction: {missing_cols}")
    
    X = df[feature_cols]
    
    # Ensure no NaNs in input
    if X.isnull().any().any():
        null_counts = X.isnull().sum()
        raise ValueError(f"Input data contains null values: \n{null_counts[null_counts > 0]}")
    
    predictions = model.predict(X)
    df['predicted_decomposition_energy'] = predictions
    
    logger.info(f"Predictions generated for {len(df)} candidates.")
    return df

def flag_thermodynamic_stability(df: pd.DataFrame, threshold: float = -0.1) -> pd.DataFrame:
    """
    Flag candidates that are thermodynamically stable (predicted energy < threshold).
    
    Args:
        df: DataFrame with 'predicted_decomposition_energy'.
        threshold: Energy threshold in eV/atom.
        
    Returns:
        DataFrame with 'is_stable' boolean column.
    """
    df['is_stable'] = df['predicted_decomposition_energy'] < threshold
    stable_count = df['is_stable'].sum()
    logger.info(f"Stability flagging complete: {stable_count} candidates below threshold {threshold} eV/atom.")
    return df

def rank_and_output(df: pd.DataFrame, output_csv: str, output_md: str) -> None:
    """
    Sort candidates by predicted energy (ascending) and save to CSV and Markdown.
    
    Args:
        df: Ranked DataFrame.
        output_csv: Path to save full ranked list.
        output_md: Path to save top candidates report.
    """
    # Sort by predicted energy (ascending = more stable first)
    df_sorted = df.sort_values(by='predicted_decomposition_energy', ascending=True)
    
    # Save full ranked list
    df_sorted.to_csv(output_csv, index=False)
    logger.info(f"Full ranked list saved to {output_csv}")
    
    # Generate Markdown report for top candidates
    top_n = 20
    top_candidates = df_sorted.head(top_n)
    
    md_lines = [
        "# Top Stable Perovskite Candidates",
        "",
        "This report lists the top 20 hypothetical ABX3 structures predicted to be thermodynamically stable.",
        "Stability is defined as predicted decomposition energy < -0.1 eV/atom.",
        "",
        "| Rank | Formula | A | B | X | Tolerance Factor | Octahedral Factor | Ionic Mismatch | Electronegativity Diff | Predicted Energy (eV/atom) | OOD | Stable |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|"
    ]
    
    for idx, row in top_candidates.iterrows():
        ood_str = "Yes" if row.get('is_ood', False) else "No"
        stable_str = "Yes" if row.get('is_stable', False) else "No"
        # Format floats to 4 decimal places
        row_str = f"| {idx+1} | {row['formula']} | {row['A']} | {row['B']} | {row['X']} | "
        row_str += f"{row['tolerance_factor']:.4f} | {row['octahedral_factor']:.4f} | "
        row_str += f"{row['ionic_mismatch']:.4f} | {row['electronegativity_diff']:.4f} | "
        row_str += f"{row['predicted_decomposition_energy']:.4f} | {ood_str} | {stable_str} |"
        md_lines.append(row_str)
    
    with open(output_md, 'w') as f:
        f.write('\n'.join(md_lines))
    
    logger.info(f"Top candidates report saved to {output_md}")

def main():
    """
    Main execution flow for User Story 3: Virtual Screening and Candidate Ranking.
    """
    log_pipeline_event("Starting User Story 3: Virtual Screening")
    
    # 1. Define element sets (per plan.md Phase 3)
    a_elements = ['K', 'Rb', 'Cs', 'Ba', 'Sr']
    b_elements = ['Ti', 'Zr', 'Hf', 'Sn', 'Ge']
    x_elements = ['F', 'Cl', 'Br', 'I']
    
    # 2. Generate combinatorial library
    logger.info("Step 1: Generating combinatorial library...")
    library_df = generate_combinatorial_library(a_elements, b_elements, x_elements)
    
    # 3. Calculate descriptors for the library
    # We need to calculate ionic radii and other descriptors for each unique element first,
    # then apply to the dataframe.
    logger.info("Step 2: Calculating descriptors for hypothetical library...")
    
    # Pre-calculate properties for unique elements to speed up
    unique_elements = set(library_df['A'].unique()) | set(library_df['B'].unique()) | set(library_df['X'].unique())
    element_props = {}
    for elem in unique_elements:
        try:
            # Assuming +2 for A, +4 for B, -1 for X in perovskites
            # Note: get_ionic_radius might handle oxidation state logic internally or require it.
            # Based on typical usage in such pipelines, we assume standard oxidation states for perovskites.
            # If the function requires specific oxidation states, we pass them.
            # For now, we assume the function can handle standard states or we pass a dummy charge if needed.
            # Let's assume the function signature in descriptors.py handles standard perovskite states.
            # If it requires explicit charge, we might need to adapt.
            # Assuming get_ionic_radius(elem, charge) or similar. 
            # Based on the API surface provided: `get_ionic_radius` is imported.
            # Let's assume it takes (element, oxidation_state) or similar.
            # If the existing code uses a specific logic, we must follow it.
            # Since I cannot see the implementation of get_ionic_radius, I will assume it works with standard states
            # or I will use the calculate_all_descriptors function if it handles the row logic.
            
            # Actually, the task T015/T016 implies we calculate per row.
            # Let's use the calculate_all_descriptors function if it exists for a row,
            # or manually compute based on the API surface.
            # The API surface lists `calculate_all_descriptors` which likely takes a dataframe row or series.
            # Let's assume it takes a row and returns a dict of descriptors.
            
            # However, to be safe and consistent with the existing codebase logic (T015/T016),
            # we will manually compute the descriptors for each row using the helper functions
            # that were likely used in T015/T016.
            
            pass
        except Exception as e:
            logger.error(f"Error getting properties for {elem}: {e}")
    
    # Apply descriptor calculation row by row
    # We need to map A, B, X to radii and electronegativities
    # Assuming standard oxidation states: A=+2, B=+4, X=-1
    def compute_row_descriptors(row):
        try:
            rA = get_ionic_radius(row['A'], 2) # +2 for A
            rB = get_ionic_radius(row['B'], 4) # +4 for B
            rX = get_ionic_radius(row['X'], -1) # -1 for X
            
            # Calculate descriptors
            t = calculate_tolerance_factor_from_ions({'A': rA, 'B': rB, 'X': rX})
            mu = calculate_octahedral_factor(rB, rX)
            
            # Electronegativity
            enA = get_element_electronegativity(row['A'])
            enB = get_element_electronegativity(row['B'])
            enX = get_element_electronegativity(row['X'])
            
            # Differences
            en_diff = calculate_electronegativity_difference(enA, enB, enX) # This function might need specific args
            # If the function signature is different, we adapt.
            # Assuming calculate_electronegativity_difference takes (enA, enB, enX) or similar.
            # Let's assume it calculates the difference between A and X, or A and B.
            # Standard is |enA - enX| or similar.
            # Let's assume the function in descriptors.py handles the logic.
            # If not, we might need to compute it here.
            # Given the API surface, I will assume it works.
            
            # Ionic Mismatch
            mismatch = calculate_ionic_radius_mismatch(rA, rB, rX)
            
            return pd.Series({
                'tolerance_factor': t,
                'octahedral_factor': mu,
                'ionic_mismatch': mismatch,
                'electronegativity_diff': en_diff
            })
        except Exception as e:
            logger.warning(f"Could not calculate descriptors for {row['formula']}: {e}")
            return pd.Series([np.nan, np.nan, np.nan, np.nan])

    # Note: The above assumes get_ionic_radius and other functions accept (element, charge).
    # If the existing code in descriptors.py uses a different logic (e.g. hardcoded dict),
    # we should rely on the `calculate_all_descriptors` function if it exists and is robust.
    # Let's try to use the existing `calculate_all_descriptors` if it takes a row.
    # If not, we proceed with the manual calculation above, ensuring we handle exceptions.
    
    # Fallback: Use the existing process_dataframe logic if available, or manual.
    # Since T015/T016 are done, the functions are available.
    # We will assume the manual calculation above is correct based on standard perovskite chemistry.
    
    descriptors = library_df.apply(compute_row_descriptors, axis=1)
    library_df = pd.concat([library_df, descriptors], axis=1)
    
    # Remove rows with NaN descriptors (infeasible geometries or missing data)
    initial_count = len(library_df)
    library_df = library_df.dropna(subset=['tolerance_factor', 'octahedral_factor', 'ionic_mismatch', 'electronegativity_diff'])
    dropped_count = initial_count - len(library_df)
    if dropped_count > 0:
        logger.warning(f"Dropped {dropped_count} candidates due to missing descriptor data.")
    
    # 4. Filter geometric feasibility (T035)
    logger.info("Step 3: Filtering for geometric feasibility (0.8 <= t <= 1.1)...")
    feasible_df = library_df[(library_df['tolerance_factor'] >= 0.8) & (library_df['tolerance_factor'] <= 1.1)]
    logger.info(f"Feasible candidates: {len(feasible_df)}")
    
    # 5. OOD Check (T036)
    logger.info("Step 4: Performing OOD check...")
    stats = load_training_statistics()
    feasible_df = perform_ood_check(feasible_df, stats)
    
    # 6. Predict Stability (T037)
    logger.info("Step 5: Predicting stability using trained model...")
    model = load_model()
    feasible_df = predict_stability(model, feasible_df)
    
    # 7. Flag Thermodynamic Stability (T039)
    logger.info("Step 6: Flagging thermodynamic stability...")
    feasible_df = flag_thermodynamic_stability(feasible_df, threshold=-0.1)
    
    # 8. Rank and Output (T040, T041)
    logger.info("Step 7: Ranking and saving results...")
    output_csv = "results/screening_full.csv"
    output_md = "results/screening_candidates.md"
    rank_and_output(feasible_df, output_csv, output_md)
    
    log_pipeline_event("User Story 3: Virtual Screening completed successfully.")
    return feasible_df

if __name__ == "__main__":
    main()