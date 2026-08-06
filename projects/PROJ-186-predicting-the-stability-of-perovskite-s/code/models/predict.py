"""
Virtual Screening and Candidate Ranking Module (US3)

Implements prediction logic for hypothetical perovskite structures using
a pre-trained model to calculate predicted decomposition energy.
"""

import os
import sys
import logging
import itertools
import pickle
import json
import math
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Set

# Import logging utilities
from utils.logging_config import get_logger, log_pipeline_event, log_exclusion_reason
from utils.config import get_config_summary

# Import descriptor utilities for feature calculation
# These are defined in code/data/descriptors.py
from data.descriptors import (
    get_ionic_radius,
    calculate_tolerance_factor,
    calculate_octahedral_factor,
    get_element_electronegativity,
    calculate_electronegativity_difference,
    calculate_ionic_radius_mismatch,
    calculate_all_descriptors
)

# Constants for the combinatorial library (Phase 3, Constitution Principle VII)
# A-site: K, Rb, Cs, Ba, Sr
# B-site: Ti, Zr, Hf, Sn, Ge
# X-site: F, Cl, Br, I
A_SITE_ELEMENTS: Set[str] = {"K", "Rb", "Cs", "Ba", "Sr"}
B_SITE_ELEMENTS: Set[str] = {"Ti", "Zr", "Hf", "Sn", "Ge"}
X_SITE_ELEMENTS: Set[str] = {"F", "Cl", "Br", "I"}

# Paths relative to project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
MODEL_PATH = PROJECT_ROOT / "results" / "model.pkl"
TRAINING_STATS_PATH = PROJECT_ROOT / "results" / "training_stats.json"
OUTPUT_FULL_PATH = PROJECT_ROOT / "results" / "screening_full.csv"
OUTPUT_CANDIDATES_PATH = PROJECT_ROOT / "results" / "screening_candidates.md"

logger = get_logger(__name__)


def calculate_tolerance_factor_from_ions(
    r_a: float, r_b: float, r_x: float
) -> float:
    """
    Calculate Goldschmidt tolerance factor (t) from ionic radii.
    t = (r_A + r_X) / (sqrt(2) * (r_B + r_X))
    """
    numerator = r_a + r_x
    denominator = math.sqrt(2) * (r_b + r_x)
    if denominator == 0:
        return 0.0
    return numerator / denominator


def generate_combinatorial_library() -> pd.DataFrame:
    """
    Generate a combinatorial library of hypothetical ABX3 structures.
    Uses A={K, Rb, Cs, Ba, Sr}, B={Ti, Zr, Hf, Sn, Ge}, X={F, Cl, Br, I}.
    Returns a DataFrame with columns: 'formula', 'A', 'B', 'X'.
    """
    logger.info(f"Generating combinatorial library with {len(A_SITE_ELEMENTS)} A, "
                f"{len(B_SITE_ELEMENTS)} B, {len(X_SITE_ELEMENTS)} X elements.")

    combinations = list(itertools.product(A_SITE_ELEMENTS, B_SITE_ELEMENTS, X_SITE_ELEMENTS))
    logger.info(f"Total raw combinations: {len(combinations)}")

    data = []
    for a, b, x in combinations:
        formula = f"{a}{b}{x}3"
        data.append({
            "formula": formula,
            "A": a,
            "B": b,
            "X": x
        })

    df = pd.DataFrame(data)
    logger.info(f"Combinatorial library generated with {len(df)} entries.")
    return df


def load_training_statistics() -> Dict[str, Any]:
    """
    Load training statistics (min/max ranges for OOD checks) from JSON.
    """
    if not TRAINING_STATS_PATH.exists():
        raise FileNotFoundError(
            f"Training statistics file not found at {TRAINING_STATS_PATH}. "
            "Please ensure the model training pipeline (T031) has completed successfully."
        )

    with open(TRAINING_STATS_PATH, 'r') as f:
        stats = json.load(f)

    logger.info(f"Loaded training statistics from {TRAINING_STATS_PATH}")
    return stats


def perform_ood_check(
    row: Dict[str, Any],
    stats: Dict[str, Any],
    tolerance: float = 0.1
) -> bool:
    """
    Perform Out-Of-Distribution (OOD) check based on descriptor ranges.
    Returns True if the sample is OOD (outside range + tolerance).
    """
    descriptor_keys = ['tolerance_factor', 'octahedral_factor', 'ionic_radius_mismatch', 'electronegativity_diff']

    for key in descriptor_keys:
        if key not in stats['ranges']:
            logger.warning(f"Missing range for descriptor {key} in training stats.")
            continue

        min_val = stats['ranges'][key]['min']
        max_val = stats['ranges'][key]['max']

        val = row.get(key)
        if val is None:
            continue

        # Check if value is outside range with tolerance buffer
        if val < (min_val - tolerance) or val > (max_val + tolerance):
            logger.debug(f"OOD detected for {row.get('formula', 'unknown')}: {key}={val} "
                         f"(range: {min_val}-{max_val})")
            return True

    return False


def load_model() -> Any:
    """
    Load the pre-trained Random Forest model from results/model.pkl.
    """
    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Model file not found at {MODEL_PATH}. "
            "Please ensure the model training pipeline (T031) has completed successfully."
        )

    logger.info(f"Loading model from {MODEL_PATH}")
    with open(MODEL_PATH, 'rb') as f:
        model = pickle.load(f)

    logger.info("Model loaded successfully.")
    return model


def predict_stability(
    model: Any,
    df: pd.DataFrame
) -> pd.DataFrame:
    """
    Predict decomposition energy for all feasible candidates in the DataFrame.
    Adds a 'predicted_decomposition_energy' column.
    """
    logger.info(f"Predicting stability for {len(df)} candidates...")

    # Define the feature columns expected by the model
    # These must match the columns used during training (T023)
    feature_cols = [
        'tolerance_factor',
        'octahedral_factor',
        'ionic_radius_mismatch',
        'electronegativity_diff'
    ]

    # Ensure all required columns exist
    missing_cols = [col for col in feature_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required feature columns in input data: {missing_cols}")

    X = df[feature_cols].values

    # Perform prediction
    predictions = model.predict(X)

    # Add predictions to DataFrame
    df['predicted_decomposition_energy'] = predictions

    logger.info(f"Predictions complete. Min: {predictions.min():.4f}, Max: {predictions.max():.4f}")
    return df


def flag_thermodynamic_stability(
    df: pd.DataFrame,
    threshold: float = -0.1
) -> pd.DataFrame:
    """
    Flag candidates as thermodynamically stable if predicted energy < threshold.
    Adds a 'is_stable' boolean column.
    """
    df['is_stable'] = df['predicted_decomposition_energy'] < threshold
    stable_count = df['is_stable'].sum()
    logger.info(f"Flagged {stable_count} candidates as stable (threshold < {threshold} eV/atom).")
    return df


def rank_and_output(df: pd.DataFrame) -> pd.DataFrame:
    """
    Sort candidates by predicted decomposition energy (ascending, most stable first).
    Saves the full ranked list to results/screening_full.csv.
    Returns the sorted DataFrame.
    """
    # Sort by predicted energy ascending (lower energy = more stable)
    df_sorted = df.sort_values(by='predicted_decomposition_energy', ascending=True)

    # Save full list
    df_sorted.to_csv(OUTPUT_FULL_PATH, index=False)
    logger.info(f"Saved full ranked list to {OUTPUT_FULL_PATH}")

    return df_sorted


def main():
    """
    Main execution flow for User Story 3 - Virtual Screening and Ranking.
    1. Load model and training stats.
    2. Generate combinatorial library.
    3. Calculate descriptors for all candidates.
    4. Perform OOD check and filter.
    5. Predict stability.
    6. Flag stable candidates.
    7. Rank and output full list.
    """
    log_pipeline_event("Starting Virtual Screening Pipeline (T037)")

    try:
        # 1. Load Model and Stats
        model = load_model()
        stats = load_training_statistics()

        # 2. Generate Combinatorial Library
        df = generate_combinatorial_library()

        # 3. Calculate Descriptors for all candidates
        logger.info("Calculating descriptors for combinatorial library...")
        # We need to calculate descriptors for each row.
        # We'll do this by iterating and applying the descriptor logic.
        # Since we don't have a bulk vectorized function for hypotheticals,
        # we iterate carefully.
        
        descriptors_data = []
        for idx, row in df.iterrows():
            try:
                a = row['A']
                b = row['B']
                x = row['X']

                # Get radii
                r_a = get_ionic_radius(a, 6) # Coordination number 6 for A
                r_b = get_ionic_radius(b, 6) # Coordination number 6 for B
                r_x = get_ionic_radius(x, 6) # Coordination number 6 for X

                if None in [r_a, r_b, r_x]:
                    log_exclusion_reason(f"Missing ionic radius for {row['formula']}", "T037")
                    continue

                # Calculate descriptors
                t = calculate_tolerance_factor_from_ions(r_a, r_b, r_x)
                mu = calculate_octahedral_factor(r_b, r_x)
                mismatch = calculate_ionic_radius_mismatch(r_a, r_b)
                en_diff = calculate_electronegativity_difference(a, b, x) # Simplified: usually A-X or B-X diff

                descriptors_data.append({
                    'tolerance_factor': t,
                    'octahedral_factor': mu,
                    'ionic_radius_mismatch': mismatch,
                    'electronegativity_diff': en_diff
                })
            except Exception as e:
                log_exclusion_reason(f"Error calculating descriptors for {row['formula']}: {str(e)}", "T037")
                continue

        if not descriptors_data:
            raise RuntimeError("Failed to calculate descriptors for any candidate.")

        # Merge descriptors back to main DF
        df_desc = pd.DataFrame(descriptors_data)
        # Ensure alignment (assuming no rows dropped in loop, but safe to re-index)
        # If rows were dropped, we need to filter df too.
        # For simplicity, if we assume all passed, we just assign.
        # If some failed, we need to filter df to match the index of valid rows.
        # Let's assume the loop succeeded for all or we handle the index mismatch.
        # The loop above uses iterrows, so if a row fails, we skip it.
        # We need to track which rows were successful.
        
        # Re-doing the loop with tracking to be safe
        valid_indices = []
        valid_descs = []
        for idx, row in df.iterrows():
            try:
                a = row['A']
                b = row['B']
                x = row['X']

                r_a = get_ionic_radius(a, 6)
                r_b = get_ionic_radius(b, 6)
                r_x = get_ionic_radius(x, 6)

                if None in [r_a, r_b, r_x]:
                    continue

                t = calculate_tolerance_factor_from_ions(r_a, r_b, r_x)
                mu = calculate_octahedral_factor(r_b, r_x)
                mismatch = calculate_ionic_radius_mismatch(r_a, r_b)
                en_diff = calculate_electronegativity_difference(a, b, x)

                valid_indices.append(idx)
                valid_descs.append({
                    'tolerance_factor': t,
                    'octahedral_factor': mu,
                    'ionic_radius_mismatch': mismatch,
                    'electronegativity_diff': en_diff
                })
            except Exception as e:
                continue

        df = df.loc[valid_indices].reset_index(drop=True)
        df_desc = pd.DataFrame(valid_descs)
        df = pd.concat([df, df_desc], axis=1)

        logger.info(f"Descriptors calculated for {len(df)} candidates.")

        # 4. Perform OOD Check
        # T036: Add is_ood column
        df['is_ood'] = df.apply(lambda row: perform_ood_check(row, stats), axis=1)
        ood_count = df['is_ood'].sum()
        logger.info(f"Found {ood_count} OOD candidates.")

        # Filter out OOD candidates for prediction (optional, but standard practice)
        # The task says "predict ... for all feasible candidates".
        # Feasibility usually implies geometric (T035) and OOD (T036).
        # We will predict on non-OOD candidates to ensure reliability,
        # or predict on all and flag. The task says "calculate ... for all feasible".
        # Let's assume "feasible" includes passing OOD check.
        df_feasible = df[~df['is_ood']].copy()
        logger.info(f"Predicting on {len(df_feasible)} feasible (non-OOD) candidates.")

        if len(df_feasible) == 0:
            logger.warning("No feasible candidates found after OOD check. Predicting on all to avoid empty output.")
            df_feasible = df.copy()

        # 5. Predict Stability
        df_feasible = predict_stability(model, df_feasible)

        # 6. Flag Thermodynamic Stability
        df_feasible = flag_thermodynamic_stability(df_feasible)

        # 7. Rank and Output
        df_ranked = rank_and_output(df_feasible)

        # Log summary
        log_pipeline_event(f"T037 Complete. Generated {len(df_ranked)} ranked candidates.")
        logger.info(f"Top 5 stable candidates:")
        stable_top = df_ranked[df_ranked['is_stable']].head(5)
        for _, row in stable_top.iterrows():
            logger.info(f"  {row['formula']}: {row['predicted_decomposition_energy']:.4f} eV/atom")

    except FileNotFoundError as e:
        logger.error(f"Critical file missing: {e}")
        raise
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        raise

    return df_ranked


if __name__ == "__main__":
    main()