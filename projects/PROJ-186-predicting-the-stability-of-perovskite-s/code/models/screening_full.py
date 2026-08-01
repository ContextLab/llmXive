"""
T040: Save full ranked list to results/screening_full.csv.

This script loads the hypothetical library, performs stability prediction
(reusing logic from code/models/predict.py), ranks candidates by predicted
decomposition energy, and saves the full ranked list to results/screening_full.csv.

It validates that at least 200 feasible candidates are present in the output.
"""
import os
import sys
import logging
import pandas as pd
import pickle
import json
from pathlib import Path
from typing import List, Dict, Any, Tuple

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.logging_config import get_logger, log_pipeline_event
from models.predict import (
    load_model,
    calculate_tolerance_factor_from_ions,
    perform_ood_check,
    flag_thermodynamic_stability
)

# Constants
RESULTS_DIR = project_root / "results"
DATA_DIR = project_root / "data" / "processed"
MODEL_PATH = RESULTS_DIR / "model.pkl"
TRAIN_STATS_PATH = RESULTS_DIR / "training_stats.json"
OUTPUT_PATH = RESULTS_DIR / "screening_full.csv"
MIN_CANDIDATES = 200

logger = get_logger(__name__)

def load_training_statistics() -> Dict[str, Any]:
    """Load training statistics for OOD checks."""
    if not TRAIN_STATS_PATH.exists():
        raise FileNotFoundError(f"Training statistics not found at {TRAIN_STATS_PATH}")
    
    with open(TRAIN_STATS_PATH, 'r') as f:
        return json.load(f)

def predict_stability_batch(
    df: pd.DataFrame, 
    model, 
    training_stats: Dict[str, Any]
) -> pd.DataFrame:
    """
    Predict stability for a batch of candidates.
    
    Args:
        df: DataFrame with candidate compositions and descriptors
        model: Trained RandomForest model
        training_stats: Statistics from training data for OOD checks
        
    Returns:
        DataFrame with predictions added
    """
    # Ensure required columns exist
    required_cols = ['tolerance_factor', 'octahedral_factor', 'ionic_mismatch', 
                    'electronegativity_diff', 'A_site', 'B_site', 'X_site']
    
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Missing required column: {col}")
    
    # Prepare feature matrix
    feature_cols = ['tolerance_factor', 'octahedral_factor', 'ionic_mismatch', 
                   'electronegativity_diff']
    X = df[feature_cols].values
    
    # Make predictions
    predictions = model.predict(X)
    df = df.copy()
    df['predicted_decomposition_energy'] = predictions
    
    # Perform OOD check
    df = perform_ood_check(df, training_stats)
    
    # Flag thermodynamic stability
    df = flag_thermodynamic_stability(df)
    
    return df

def load_ranked_candidates() -> pd.DataFrame:
    """
    Load the hypothetical library and perform predictions.
    
    Returns:
        DataFrame with ranked candidates
    """
    library_path = DATA_DIR / "hypothetical_library.csv"
    
    if not library_path.exists():
        raise FileNotFoundError(
            f"Hypothetical library not found at {library_path}. "
            "Run code/models/predict.py first to generate it."
        )
    
    logger.info(f"Loading hypothetical library from {library_path}")
    df = pd.read_csv(library_path)
    
    logger.info(f"Loaded {len(df)} candidates")
    
    # Load model and training stats
    logger.info(f"Loading model from {MODEL_PATH}")
    model = load_model(MODEL_PATH)
    
    training_stats = load_training_statistics()
    
    # Predict stability
    logger.info("Predicting stability for all candidates")
    df = predict_stability_batch(df, model, training_stats)
    
    # Sort by predicted energy (ascending - more negative is more stable)
    df = df.sort_values('predicted_decomposition_energy', ascending=True).reset_index(drop=True)
    
    return df

def validate_output(df: pd.DataFrame) -> bool:
    """
    Validate that the output meets requirements.
    
    Args:
        df: The ranked candidates DataFrame
        
    Returns:
        True if validation passes
    """
    if len(df) < MIN_CANDIDATES:
        logger.error(f"Only {len(df)} candidates found, but at least {MIN_CANDIDATES} are required")
        return False
    
    # Check for required columns
    required_cols = ['A_site', 'B_site', 'X_site', 'tolerance_factor', 
                    'octahedral_factor', 'ionic_mismatch', 'electronegativity_diff',
                    'predicted_decomposition_energy', 'is_ood', 'is_stable']
                    
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        logger.error(f"Missing required columns: {missing_cols}")
        return False
    
    # Check for nulls in key columns
    null_cols = df[required_cols].isnull().sum()
    if null_cols.sum() > 0:
        logger.warning(f"Found nulls in key columns: {null_cols[null_cols > 0].to_dict()}")
        # This is a warning, not a failure, as long as we have enough candidates
    
    return True

def main():
    """Main entry point for T040."""
    log_pipeline_event("T040", "Starting full ranked list generation")
    
    try:
        # Ensure results directory exists
        RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        
        # Load and rank candidates
        ranked_df = load_ranked_candidates()
        
        # Validate output
        if not validate_output(ranked_df):
            raise RuntimeError("Output validation failed")
        
        # Save to CSV
        logger.info(f"Saving {len(ranked_df)} candidates to {OUTPUT_PATH}")
        ranked_df.to_csv(OUTPUT_PATH, index=False)
        
        # Log summary statistics
        logger.info(f"Total candidates: {len(ranked_df)}")
        logger.info(f"Stable candidates (predicted < 0): {sum(ranked_df['predicted_decomposition_energy'] < 0)}")
        logger.info(f"OOD candidates: {sum(ranked_df['is_ood'])}")
        logger.info(f"Best predicted energy: {ranked_df['predicted_decomposition_energy'].min():.4f} eV/atom")
        logger.info(f"Worst predicted energy: {ranked_df['predicted_decomposition_energy'].max():.4f} eV/atom")
        
        log_pipeline_event("T040", "Successfully saved full ranked list")
        print(f"Successfully saved {len(ranked_df)} candidates to {OUTPUT_PATH}")
        
    except Exception as e:
        log_pipeline_event("T040", f"Failed: {str(e)}", level="ERROR")
        logger.exception("Error in T040")
        raise

if __name__ == "__main__":
    main()