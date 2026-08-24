"""
Perovskite Stability Prediction and Screening Module.

This module handles the virtual screening phase:
1. Loading hypothetical libraries.
2. Calculating geometric descriptors (Tolerance Factor).
3. Filtering for geometric feasibility (0.8 <= t <= 1.1).
4. Predicting stability using trained models.
5. Ranking and reporting candidates.
"""

import os
import sys
import logging
import itertools
import pickle
import json
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Project imports based on API surface
from utils.logging_config import get_logger, log_pipeline_event, log_exclusion_reason
from utils.config import get_config_summary

# Constants for Element Sets (FR-004)
A_SITES = ['K', 'Rb', 'Cs', 'Ba', 'Sr']
B_SITES = ['Ti', 'Zr', 'Hf', 'Sn', 'Ge']
X_SITES = ['F', 'Cl', 'Br', 'I']

# Geometric Feasibility Thresholds
TOLERANCE_FACTOR_MIN = 0.8
TOLERANCE_FACTOR_MAX = 1.1

logger = get_logger(__name__)

# --- Ionic Radii and Electronegativity Data (Shannon Radii / Pauling) ---
# Hardcoded reference data to avoid external API calls for screening
# Radii in Angstroms (CN=12 for A, CN=6 for B, CN=6 for X)
IONIC_RADII = {
    'K': {'CN12': 1.64},
    'Rb': {'CN12': 1.72},
    'Cs': {'CN12': 1.88},
    'Ba': {'CN12': 1.61}, # Ba2+ CN12
    'Sr': {'CN12': 1.44}, # Sr2+ CN12
    'Ti': {'CN6': 0.605}, # Ti4+ CN6
    'Zr': {'CN6': 0.72},  # Zr4+ CN6
    'Hf': {'CN6': 0.71},  # Hf4+ CN6
    'Sn': {'CN6': 0.69},  # Sn4+ CN6
    'Ge': {'CN6': 0.53},  # Ge4+ CN6
    'F': {'CN6': 1.33},
    'Cl': {'CN6': 1.81},
    'Br': {'CN6': 1.96},
    'I': {'CN6': 2.20}
}

# Electronegativity (Pauling)
ELECTRONEGATIVITY = {
    'K': 0.82, 'Rb': 0.82, 'Cs': 0.79, 'Ba': 0.89, 'Sr': 0.95,
    'Ti': 1.54, 'Zr': 1.33, 'Hf': 1.30, 'Sn': 1.96, 'Ge': 2.01,
    'F': 3.98, 'Cl': 3.16, 'Br': 2.96, 'I': 2.66
}

def get_ionic_radius(element: str, oxidation_state: int = None, cn: str = 'CN6') -> float:
    """
    Retrieve ionic radius for an element.
    For screening, we assume standard oxidation states: A=+2, B=+4, X=-1.
    """
    # Map standard oxidation states to radii keys if needed, but for this
    # specific screening set, we use the hardcoded CN keys above.
    if element not in IONIC_RADII:
        raise ValueError(f"Element {element} not found in ionic radii database.")
    
    # Determine key based on site type (inferred from element or explicit)
    # A sites (K, Rb, Cs, Ba, Sr) -> CN12
    # B sites (Ti, Zr, Hf, Sn, Ge) -> CN6
    # X sites (F, Cl, Br, I) -> CN6
    
    if element in ['K', 'Rb', 'Cs', 'Ba', 'Sr']:
        key = 'CN12'
    else:
        key = 'CN6'
        
    if key not in IONIC_RADII[element]:
        raise ValueError(f"No radius data for {element} with coordination {key}.")
        
    return IONIC_RADII[element][key]

def get_element_electronegativity(element: str) -> float:
    """Retrieve electronegativity for an element."""
    if element not in ELECTRONEGATIVITY:
        raise ValueError(f"Element {element} not found in electronegativity database.")
    return ELECTRONEGATIVITY[element]

def calculate_tolerance_factor_from_ions(r_A: float, r_B: float, r_X: float) -> float:
    """
    Calculate Goldschmidt tolerance factor t.
    t = (r_A + r_X) / (sqrt(2) * (r_B + r_X))
    """
    import math
    numerator = r_A + r_X
    denominator = math.sqrt(2) * (r_B + r_X)
    if denominator == 0:
        raise ValueError("Denominator in tolerance factor calculation is zero.")
    return numerator / denominator

def generate_combinatorial_library() -> pd.DataFrame:
    """
    Generate a combinatorial library of hypothetical ABX3 perovskites.
    Uses element sets defined in FR-004.
    """
    logger.info("Generating combinatorial library...")
    combinations = list(itertools.product(A_SITES, B_SITES, X_SITES))
    
    data = []
    for A, B, X in combinations:
        formula = f"{A}{B}{X}3"
        data.append({
            'A': A,
            'B': B,
            'X': X,
            'formula': formula
        })
    
    df = pd.DataFrame(data)
    logger.info(f"Generated {len(df)} combinations.")
    return df

def load_hypothetical_library(input_path: str) -> pd.DataFrame:
    """Load the hypothetical library from a CSV file."""
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    logger.info(f"Loading hypothetical library from {input_path}")
    df = pd.read_csv(path)
    
    required_cols = ['A', 'B', 'X', 'formula']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in library: {missing}")
        
    return df

def filter_geometric_feasibility(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter the library for geometric feasibility based on Tolerance Factor (t).
    Criteria: 0.8 <= t <= 1.1
    
    Input: DataFrame with columns A, B, X
    Output: DataFrame with added 'tolerance_factor' and 'is_geometrically_feasible' columns,
            filtered to only feasible rows.
    """
    logger.info("Calculating geometric feasibility (tolerance factor)...")
    
    if df.empty:
        logger.warning("Input dataframe is empty, returning empty result.")
        return df

    def calculate_t(row):
        try:
            r_A = get_ionic_radius(row['A'])
            r_B = get_ionic_radius(row['B'])
            r_X = get_ionic_radius(row['X'])
            t = calculate_tolerance_factor_from_ions(r_A, r_B, r_X)
            return t
        except Exception as e:
            logger.warning(f"Could not calculate t for {row['formula']}: {e}")
            return None

    df['tolerance_factor'] = df.apply(calculate_t, axis=1)
    
    # Drop rows where calculation failed
    initial_count = len(df)
    df = df.dropna(subset=['tolerance_factor'])
    dropped_count = initial_count - len(df)
    if dropped_count > 0:
        logger.warning(f"Dropped {dropped_count} rows due to missing radii data.")

    # Apply filter
    feasible = (df['tolerance_factor'] >= TOLERANCE_FACTOR_MIN) & \
               (df['tolerance_factor'] <= TOLERANCE_FACTOR_MAX)
    
    df_filtered = df[feasible].copy()
    df_filtered['is_geometrically_feasible'] = True
    
    excluded_count = len(df) - len(df_filtered)
    logger.info(f"Filtered library: {len(df_filtered)} feasible out of {len(df)} candidates "
                f"(excluded {excluded_count} based on 0.8 <= t <= 1.1).")
    
    return df_filtered

def load_training_statistics() -> Dict[str, Any]:
    """Load training statistics (means/stds) used for feature scaling if necessary."""
    # In a real pipeline, this might load from a JSON file generated during training.
    # For now, we assume the model handles scaling internally or we use raw values.
    # If scaling is needed, we would load a scaler object.
    return {}

def load_model(model_path: str) -> Any:
    """Load the trained scikit-learn model."""
    path = Path(model_path)
    if not path.exists():
        raise FileNotFoundError(f"Model file not found: {model_path}")
    
    logger.info(f"Loading model from {model_path}")
    with open(path, 'rb') as f:
        model = pickle.load(f)
    return model

def predict_stability_batch(df: pd.DataFrame, model: Any) -> pd.DataFrame:
    """
    Predict stability (decomposition energy) for a batch of candidates.
    Assumes the model expects the same features used during training.
    Features: tolerance_factor, octahedral_factor, ionic_radius_mismatch, electronegativity_diff
    """
    logger.info("Predicting stability for candidates...")
    
    # We need to calculate the other descriptors that the model expects.
    # Since we only have A, B, X, we must compute:
    # 1. tolerance_factor (already done in filter_geometric_feasibility)
    # 2. octahedral_factor (r_B / r_X)
    # 3. ionic_radius_mismatch (|r_A - r_B|? or similar metric)
    # 4. electronegativity_diff (|chi_A - chi_B|)
    
    # Re-calculate or ensure these columns exist
    def calculate_octahedral_factor(row):
        try:
            r_B = get_ionic_radius(row['B'])
            r_X = get_ionic_radius(row['X'])
            if r_X == 0: return None
            return r_B / r_X
        except: return None

    def calculate_ionic_radius_mismatch(row):
        # Common definition: |r_A - r_B| / r_B or similar. 
        # Using |r_A - r_B| as a simple mismatch metric for now.
        try:
            r_A = get_ionic_radius(row['A'])
            r_B = get_ionic_radius(row['B'])
            return abs(r_A - r_B)
        except: return None

    def calculate_electronegativity_diff(row):
        try:
            chi_A = get_element_electronegativity(row['A'])
            chi_B = get_element_electronegativity(row['B'])
            return abs(chi_A - chi_B)
        except: return None

    df['octahedral_factor'] = df.apply(calculate_octahedral_factor, axis=1)
    df['ionic_radius_mismatch'] = df.apply(calculate_ionic_radius_mismatch, axis=1)
    df['electronegativity_diff'] = df.apply(calculate_electronegativity_diff, axis=1)
    
    # Drop rows with missing descriptors
    feature_cols = ['tolerance_factor', 'octahedral_factor', 'ionic_radius_mismatch', 'electronegativity_diff']
    df = df.dropna(subset=feature_cols)
    
    if df.empty:
        raise ValueError("No candidates left after calculating descriptors for prediction.")

    X = df[feature_cols]
    predictions = model.predict(X)
    
    df['predicted_energy'] = predictions
    logger.info(f"Predictions generated for {len(df)} candidates.")
    return df

def rank_and_output(df: pd.DataFrame, output_path: str) -> pd.DataFrame:
    """
    Rank candidates by predicted energy (ascending, lower is more stable)
    and save the full results.
    """
    logger.info("Ranking candidates...")
    df = df.sort_values(by='predicted_energy', ascending=True)
    df['rank'] = range(1, len(df) + 1)
    
    # Flag stable candidates (e.g., < -0.1 eV/atom)
    df['is_stable_candidate'] = df['predicted_energy'] < -0.1
    
    df.to_csv(output_path, index=False)
    logger.info(f"Ranked results saved to {output_path}")
    return df

def main():
    """
    Main entry point for the prediction and screening pipeline.
    This function orchestrates:
    1. Loading the hypothetical library (or generating it if not present).
    2. Filtering for geometric feasibility (T027).
    3. Predicting stability.
    4. Ranking and saving results.
    """
    # Paths
    input_library_path = "data/processed/hypothetical_library.csv"
    output_filtered_path = "data/processed/filtered_hypothetical_library.csv"
    model_path = "results/model.pkl"
    output_full_path = "results/screening_full.csv"
    
    # Ensure directories exist
    Path("data/processed").mkdir(parents=True, exist_ok=True)
    Path("results").mkdir(parents=True, exist_ok=True)

    # 1. Load Library
    # Check if input exists, if not generate it (T026a logic)
    if not Path(input_library_path).exists():
        logger.warning(f"Input library {input_library_path} not found. Generating...")
        df_lib = generate_combinatorial_library()
        df_lib.to_csv(input_library_path, index=False)
        logger.info(f"Saved generated library to {input_library_path}")
    else:
        df_lib = load_hypothetical_library(input_library_path)

    # 2. Filter Geometric Feasibility (T027 Task)
    df_filtered = filter_geometric_feasibility(df_lib)
    
    # Save the filtered library as required by T027
    df_filtered.to_csv(output_filtered_path, index=False)
    logger.info(f"Saved filtered library to {output_filtered_path}")
    
    if df_filtered.empty:
        raise RuntimeError("No geometrically feasible candidates found. Cannot proceed to prediction.")

    # 3. Load Model
    model = load_model(model_path)

    # 4. Predict Stability
    df_predicted = predict_stability_batch(df_filtered, model)

    # 5. Rank and Output
    df_ranked = rank_and_output(df_predicted, output_full_path)

    logger.info("Screening pipeline completed successfully.")
    return df_ranked

if __name__ == "__main__":
    main()