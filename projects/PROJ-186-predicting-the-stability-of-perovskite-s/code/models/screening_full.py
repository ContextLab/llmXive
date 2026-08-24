import os
import sys
import logging
import pandas as pd
import pickle
import json
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.logging_config import get_logger, log_pipeline_event
from models.model_utils import calculate_permutation_importance

logger = get_logger(__name__)

# Threshold for thermodynamically favorable stability (eV/atom)
STABILITY_THRESHOLD = -0.1

def load_hypothetical_library(path: str) -> pd.DataFrame:
    """Load the hypothetical library CSV."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Hypothetical library not found at {path}")
    return pd.read_csv(path)

def load_training_statistics(path: str) -> Dict[str, Any]:
    """Load training statistics if needed."""
    if os.path.exists(path):
        with open(path, 'r') as f:
            return json.load(f)
    return {}

def load_ranked_candidates(path: str) -> pd.DataFrame:
    """Load the ranked candidates CSV (output of T029)."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Ranked candidates not found at {path}")
    df = pd.read_csv(path)
    return df

def predict_stability_batch(
    df: pd.DataFrame,
    model_path: str,
    feature_cols: List[str]
) -> pd.DataFrame:
    """
    Predict stability for a batch of candidates using the trained model.
    
    Args:
        df: DataFrame with candidate features
        model_path: Path to the saved model pickle
        feature_cols: List of feature column names expected by the model
        
    Returns:
        DataFrame with added 'predicted_energy' column
    """
    logger.info(f"Loading model from {model_path}")
    with open(model_path, 'rb') as f:
        model = pickle.load(f)
    
    logger.info(f"Predicting stability for {len(df)} candidates")
    
    # Ensure all required features are present
    missing_cols = set(feature_cols) - set(df.columns)
    if missing_cols:
        raise ValueError(f"Missing required features: {missing_cols}")
    
    X = df[feature_cols]
    predictions = model.predict(X)
    
    df = df.copy()
    df['predicted_energy'] = predictions
    
    logger.info(f"Prediction complete. Min: {predictions.min():.4f}, Max: {predictions.max():.4f}")
    return df

def apply_stability_threshold(df: pd.DataFrame, threshold: float = STABILITY_THRESHOLD) -> pd.DataFrame:
    """
    Add a boolean column 'is_stable_candidate' indicating if predicted_energy < threshold.
    
    Args:
        df: DataFrame with 'predicted_energy' column
        threshold: Energy threshold in eV/atom (default: -0.1)
        
    Returns:
        DataFrame with added 'is_stable_candidate' column
    """
    df = df.copy()
    df['is_stable_candidate'] = df['predicted_energy'] < threshold
    stable_count = df['is_stable_candidate'].sum()
    logger.info(f"Threshold flagging complete: {stable_count} candidates below {threshold} eV/atom")
    return df

def validate_output(df: pd.DataFrame, output_path: str) -> None:
    """Validate the output DataFrame before saving."""
    required_cols = ['formula', 'predicted_energy', 'rank', 'is_stable_candidate']
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise ValueError(f"Output missing required columns: {missing}")
    
    if df['is_stable_candidate'].dtype != bool:
        raise ValueError(f"is_stable_candidate must be boolean, got {df['is_stable_candidate'].dtype}")
    
    logger.info(f"Validation passed for {len(df)} rows")

def save_results(df: pd.DataFrame, output_path: str) -> None:
    """Save the final screening results to CSV."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Results saved to {output_path}")

def main():
    """
    Main entry point for T030: Threshold flagging.
    
    This script:
    1. Loads the ranked candidates from T029 (results/screening_full.csv)
    2. Applies the stability threshold (-0.1 eV/atom)
    3. Adds 'is_stable_candidate' boolean column
    4. Saves the updated DataFrame back to results/screening_full.csv
    """
    # Paths
    results_dir = project_root / 'results'
    input_path = results_dir / 'screening_full.csv'
    model_path = results_dir / 'model.pkl'
    output_path = results_dir / 'screening_full.csv'
    
    # Feature columns used in training (must match T014/T015)
    feature_cols = [
        'tolerance_factor',
        'octahedral_factor',
        'ionic_radius_mismatch',
        'electronegativity_diff'
    ]
    
    logger.info("Starting T030: Threshold flagging for stability candidates")
    
    # Load ranked candidates (output of T029)
    try:
        df = load_ranked_candidates(str(input_path))
        logger.info(f"Loaded {len(df)} ranked candidates")
    except FileNotFoundError as e:
        logger.error(f"Input file not found: {e}")
        raise
    
    # Apply stability threshold
    df = apply_stability_threshold(df, threshold=STABILITY_THRESHOLD)
    
    # Validate output
    validate_output(df, str(output_path))
    
    # Save results (overwrite the same file as per task description)
    save_results(df, str(output_path))
    
    # Summary
    stable_count = df['is_stable_candidate'].sum()
    total_count = len(df)
    logger.info(f"Final Summary: {stable_count}/{total_count} candidates are stable (E < {STABILITY_THRESHOLD} eV/atom)")
    
    log_pipeline_event("T030_COMPLETE", {
        "stable_candidates": int(stable_count),
        "total_candidates": int(total_count),
        "threshold": STABILITY_THRESHOLD
    })
    
    return 0

if __name__ == "__main__":
    sys.exit(main())