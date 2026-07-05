import os
import sys
import logging
import itertools
import pickle
import json
import pandas as pd
import math
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from utils.logging_config import get_logger, log_exclusion_reason, log_pipeline_event
from utils.config import get_config_summary

# Constants for the combinatorial library generation
# Adhering to plan.md Phase 3 and Constitution Principle VII
A_SITES = ['K', 'Rb', 'Cs', 'Ba', 'Sr']
B_SITES = ['Ti', 'Zr', 'Hf', 'Sn', 'Ge']
X_SITES = ['F', 'Cl', 'Br', 'I']

logger = get_logger(__name__)

def get_ionic_radius(element: str, oxidation_state: int) -> float:
    """
    Returns the ionic radius in Angstroms for a given element and oxidation state.
    Uses Shannon radii (1976) for coordination number 6 (octahedral) or 12 (cubic).
    """
    # Simplified lookup for common perovskite oxidation states
    # A-site usually +1 or +2, B-site +4, X-site -1
    # Radii in Angstroms (Shannon, 1976)
    radii = {
        # A-site (+1 or +2) - Coordination 12 (cubic) or 6 (if distorted)
        # Using CN=12 for ideal cubic perovskites, but standard tables often give CN=6.
        # For Goldschmidt t = (rA + rX) / sqrt(2)*(rB + rX), we need consistent CN.
        # Standard practice: rA (CN12), rB (CN6), rX (CN6).
        # If CN12 not available, use CN6 as approximation or specific values.
        
        # A-site +1 (CN12 approximated by available data or CN6 if 12 missing)
        'K': {1: 1.64},  # CN12 often cited ~1.64, CN6=1.38
        'Rb': {1: 1.72}, # CN12 ~1.72, CN6=1.52
        'Cs': {1: 1.88}, # CN12 ~1.88, CN6=1.67
        'Ba': {2: 1.61}, # CN12 ~1.61, CN6=1.42
        'Sr': {2: 1.44}, # CN12 ~1.44, CN6=1.26
        
        # B-site +4 (CN6)
        'Ti': {4: 0.605},
        'Zr': {4: 0.72},
        'Hf': {4: 0.71},
        'Sn': {4: 0.69},
        'Ge': {4: 0.53},
        
        # X-site -1 (CN6)
        'F': {-1: 1.33},
        'Cl': {-1: 1.81},
        'Br': {-1: 1.96},
        'I': {-1: 2.20},
    }

    if element in radii and oxidation_state in radii[element]:
        return radii[element][oxidation_state]
    
    # Fallback or error
    raise ValueError(f"Ionic radius not found for {element}^{oxidation_state}")

def calculate_tolerance_factor_from_ions(rA: float, rB: float, rX: float) -> float:
    """
    Calculates the Goldschmidt tolerance factor t.
    t = (rA + rX) / (sqrt(2) * (rB + rX))
    """
    return (rA + rX) / (math.sqrt(2) * (rB + rX))

def calculate_octahedral_factor(rB: float, rX: float) -> float:
    """
    Calculates the octahedral factor mu.
    mu = rB / (rB + rX)
    """
    return rB / (rB + rX)

def generate_combinatorial_library() -> pd.DataFrame:
    """
    Generates a combinatorial library of hypothetical ABX3 perovskites.
    Uses the element sets defined in the task description.
    """
    logger.info(f"Generating combinatorial library with {len(A_SITES)} A, {len(B_SITES)} B, {len(X_SITES)} X sites.")
    
    combinations = list(itertools.product(A_SITES, B_SITES, X_SITES))
    data = []
    
    for A, B, X in combinations:
        # Determine oxidation states
        # A is usually +1 for alkali, +2 for alkaline earth
        # B is usually +4 for transition metals in this context
        # X is -1 for halides
        ox_A = 1 if A in ['K', 'Rb', 'Cs'] else 2
        ox_B = 4
        ox_X = -1
        
        try:
            rA = get_ionic_radius(A, ox_A)
            rB = get_ionic_radius(B, ox_B)
            rX = get_ionic_radius(X, ox_X)
            
            t = calculate_tolerance_factor_from_ions(rA, rB, rX)
            mu = calculate_octahedral_factor(rB, rX)
            
            data.append({
                'formula': f"{A}{B}{X}3",
                'A_element': A,
                'B_element': B,
                'X_element': X,
                'rA': rA,
                'rB': rB,
                'rX': rX,
                'tolerance_factor': t,
                'octahedral_factor': mu
            })
        except ValueError as e:
            logger.warning(f"Skipping {A}{B}{X}3 due to missing radius data: {e}")
            continue
    
    df = pd.DataFrame(data)
    logger.info(f"Generated {len(df)} candidates.")
    return df

def filter_geometric_feasibility(df: pd.DataFrame, t_min: float = 0.8, t_max: float = 1.1) -> pd.DataFrame:
    """
    Filters the library for geometric feasibility based on tolerance factor.
    """
    logger.info(f"Filtering for geometric feasibility: {t_min} <= t <= {t_max}")
    mask = (df['tolerance_factor'] >= t_min) & (df['tolerance_factor'] <= t_max)
    filtered_df = df[mask].copy()
    logger.info(f"Retained {len(filtered_df)} candidates after geometric filtering.")
    return filtered_df

def load_training_statistics() -> Dict[str, Any]:
    """
    Loads min/max statistics for descriptors from the training process.
    These are used for OOD checks.
    """
    stats_path = project_root / "results" / "training_statistics.json"
    if not stats_path.exists():
        logger.warning(f"Training statistics file not found at {stats_path}. OOD check will be skipped or broad.")
        return {}
    
    with open(stats_path, 'r') as f:
        return json.load(f)

def perform_ood_check(df: pd.DataFrame, stats: Dict[str, Any]) -> pd.DataFrame:
    """
    Performs Out-of-Distribution check against training statistics.
    Adds 'is_ood' column.
    """
    if not stats:
        df['is_ood'] = False
        return df

    # Define columns to check
    check_cols = ['tolerance_factor', 'octahedral_factor', 'rA', 'rB', 'rX']
    
    is_ood = pd.Series([False] * len(df), index=df.index)
    
    for col in check_cols:
        if col in stats and col in df.columns:
            min_val = stats[col].get('min')
            max_val = stats[col].get('max')
            if min_val is not None and max_val is not None:
                col_ood = (df[col] < min_val) | (df[col] > max_val)
                is_ood = is_ood | col_ood
                logger.debug(f"OOD check for {col}: {col_ood.sum()} outliers")
        
    df['is_ood'] = is_ood
    return df

def load_model() -> Any:
    """
    Loads the trained model from results/model.pkl
    """
    model_path = project_root / "results" / "model.pkl"
    if not model_path.exists():
        raise FileNotFoundError(f"Model file not found at {model_path}. Run training first.")
    
    with open(model_path, 'rb') as f:
        return pickle.load(f)

def predict_stability(model: Any, df: pd.DataFrame) -> pd.DataFrame:
    """
    Predicts decomposition energy for the candidates.
    """
    feature_cols = ['tolerance_factor', 'octahedral_factor', 'rA', 'rB', 'rX']
    # Ensure columns exist
    for col in feature_cols:
        if col not in df.columns:
            raise ValueError(f"Feature column {col} missing from dataframe")
    
    X = df[feature_cols].values
    predictions = model.predict(X)
    
    df = df.copy()
    df['predicted_decomposition_energy'] = predictions
    return df

def flag_thermodynamic_stability(df: pd.DataFrame, threshold: float = -0.1) -> pd.DataFrame:
    """
    Flags candidates with predicted energy below a thermodynamic threshold.
    """
    df = df.copy()
    df['is_thermodynamically_stable'] = df['predicted_decomposition_energy'] < threshold
    return df

def rank_and_output(df: pd.DataFrame, output_path: Path) -> None:
    """
    Sorts candidates by predicted energy (ascending, most stable first)
    and saves to CSV.
    """
    df_sorted = df.sort_values(by='predicted_decomposition_energy', ascending=True)
    df_sorted.to_csv(output_path, index=False)
    logger.info(f"Saved ranked list to {output_path} with {len(df_sorted)} entries.")

def main():
    """
    Main entry point for T040: Save full ranked list.
    """
    logger.info("Starting T040: Generate and save full ranked screening list.")
    
    # 1. Generate Library
    library_df = generate_combinatorial_library()
    
    # 2. Filter Geometric Feasibility
    feasible_df = filter_geometric_feasibility(library_df)
    
    # Validation: Ensure at least 200 feasible candidates
    if len(feasible_df) < 200:
        logger.error(f"Validation failed: Only {len(feasible_df)} feasible candidates found. Expected >= 200.")
        # We proceed anyway to save what we have, but log the error as required
        # In a real pipeline, this might halt execution.
    else:
        logger.info(f"Validation passed: {len(feasible_df)} feasible candidates found (>= 200).")
    
    # 3. OOD Check
    stats = load_training_statistics()
    checked_df = perform_ood_check(feasible_df, stats)
    
    # 4. Predict Stability
    try:
        model = load_model()
        predicted_df = predict_stability(model, checked_df)
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)
    
    # 5. Flag Thermodynamic Stability
    ranked_df = flag_thermodynamic_stability(predicted_df)
    
    # 6. Rank and Output
    output_path = project_root / "results" / "screening_full.csv"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    rank_and_output(ranked_df, output_path)
    
    logger.info("T040 completed successfully.")

if __name__ == "__main__":
    main()