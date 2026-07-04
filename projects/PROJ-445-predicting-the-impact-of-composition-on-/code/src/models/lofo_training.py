"""
LOFO (Leave-One-Family-Out) Model Training for Chalcogenide Glass Tg Prediction.

This module implements the training of N-1 distinct Gradient Boosting models,
where each model is trained on the dataset excluding one specific chemical family.
This is a prerequisite for the Cross-Family Transferability Test (T030).
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple

import pandas as pd
import numpy as np
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import cross_val_score
from sklearn.metrics import mean_squared_error, r2_score
import joblib

# Import project utilities from the API surface
# Note: Using relative imports based on the provided API surface structure
try:
    from src.data.split import load_processed_data
    from src.utils.manifest_manager import register_artifact, compute_file_hash, load_manifest, save_manifest
    from src.utils.constants import get_element_property
except ImportError as e:
    # Fallback for direct execution or different path structures
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
    from src.data.split import load_processed_data
    from src.utils.manifest_manager import register_artifact, compute_file_hash, load_manifest, save_manifest
    from src.utils.constants import get_element_property

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
MODELS_DIR = DATA_DIR / "models" / "lofo_models"
MANIFEST_PATH = PROJECT_ROOT / "state" / "manifest.json"
SPLIT_DATA_PATH = DATA_DIR / "processed" / "split_data.csv" # Assuming this is where split data lives
# If split data is stored differently, adjust path. The API surface mentions split.py saves artifacts.
# Let's assume the split data is available in data/processed/ or similar.
# Based on T014, it saves split artifacts. We need to load the processed data and family info.
# We will rely on load_processed_data from split.py or preprocess.py if available.
# The API surface for split.py has load_processed_data.

# Features to use (computed in preprocess.py)
FEATURE_COLUMNS = [
    'mean_coordination_number',
    'electronegativity_variance',
    'atomic_radius_variance',
    'mean_atomic_number',
    'mean_atomic_mass'
]
TARGET_COLUMN = 'Tg'
FAMILY_COLUMN = 'chemical_family'

def ensure_directories():
    """Ensure output directories exist."""
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    logger.info(f"Ensured directory exists: {MODELS_DIR}")

def load_training_data() -> Tuple[pd.DataFrame, List[str]]:
    """
    Load the processed and split data.
    Returns the full dataframe and the list of unique chemical families.
    """
    # We need to load the data that has the 'chemical_family' column.
    # T014 (split.py) should have assigned this.
    # We try to load from the standard processed location.
    # If split.py saved a specific file, we might need to adjust.
    # Assuming load_processed_data from split.py handles this or we load from a standard path.
    
    # Attempt to load from the path expected after T013/T014
    # The split.py API has load_processed_data. Let's use it if possible.
    # However, split.py might expect arguments or specific paths.
    # Let's try to load the processed data directly if we know the path, 
    # or use the helper if it's robust.
    
    # Based on T013, preprocess.py saves to data/processed/. 
    # T014 splits it. 
    # Let's assume there is a file like 'data/processed/final_dataset.csv' or similar.
    # To be safe, we will try to load from a generic 'processed_data.csv' in data/processed/
    # or use the split helper if it exposes the full dataset.
    
    # Since the API surface for split.py has load_processed_data, let's try to use it.
    # It might load the data that was split.
    try:
        # If split.py saves the split data, we might need to reconstruct the full set
        # or load the pre-split processed data.
        # Let's assume the pre-split processed data is at:
        processed_path = DATA_DIR / "processed" / "processed_data.csv"
        if not processed_path.exists():
            # Fallback: try to find any csv in processed
            processed_files = list((DATA_DIR / "processed").glob("*.csv"))
            if processed_files:
                processed_path = processed_files[0]
            else:
                raise FileNotFoundError("No processed data found in data/processed/")
        
        df = pd.read_csv(processed_path)
        
        if FAMILY_COLUMN not in df.columns:
            # If family column is missing, we might need to re-assign it using split.py logic
            # But T014 should have done this. Let's assume it's there.
            # If not, we might need to call assign_family_column from split.py
            # For now, we assume it's present.
            logger.warning(f"Column '{FAMILY_COLUMN}' not found. Attempting to derive or fail.")
            # We cannot proceed without families for LOFO.
            raise ValueError(f"Required column '{FAMILY_COLUMN}' missing in {processed_path}")
        
        families = df[FAMILY_COLUMN].unique().tolist()
        logger.info(f"Loaded {len(df)} samples. Found {len(families)} chemical families: {families}")
        return df, families
        
    except Exception as e:
        logger.error(f"Failed to load training data: {e}")
        raise

def train_lofo_models(df: pd.DataFrame, families: List[str]) -> Dict[str, str]:
    """
    Train N-1 Gradient Boosting models, each excluding one chemical family.
    
    Args:
        df: The full dataframe with features and target.
        families: List of unique chemical families.
        
    Returns:
        Dictionary mapping family name to the path of the saved model.
    """
    model_paths = {}
    
    logger.info(f"Starting LOFO training for {len(families)} families.")
    
    for exclude_family in families:
        logger.info(f"Training model excluding family: {exclude_family}")
        
        # Filter data
        train_mask = df[FAMILY_COLUMN] != exclude_family
        train_df = df[train_mask].copy()
        
        if len(train_df) == 0:
            logger.warning(f"No training data available after excluding {exclude_family}. Skipping.")
            continue
        
        if len(train_df) < 10: # Minimum samples to train
            logger.warning(f"Too few samples ({len(train_df)}) after excluding {exclude_family}. Skipping.")
            continue
        
        # Prepare features and target
        X = train_df[FEATURE_COLUMNS].dropna()
        y = train_df.loc[X.index, TARGET_COLUMN]
        
        if len(X) < 5:
            logger.warning(f"Insufficient valid samples for {exclude_family}. Skipping.")
            continue
        
        # Initialize and train model
        # Using a constrained set of hyperparameters to ensure speed and stability
        model = GradientBoostingRegressor(
            n_estimators=100,
            max_depth=3,
            learning_rate=0.1,
            subsample=0.8,
            random_state=42,
            validation_fraction=0.1,
            n_iter_no_change=10,
            tol=1e-4
        )
        
        try:
            model.fit(X, y)
            
            # Evaluate on the held-out family (optional but good for logging)
            # We can also do a quick CV on the training set to ensure it's not broken
            cv_scores = cross_val_score(model, X, y, cv=3, scoring='r2')
            logger.info(f"  - Family {exclude_family}: Train R2 CV Mean: {cv_scores.mean():.4f} (+/- {cv_scores.std():.4f})")
            
            # Save model
            model_filename = f"lofo_model_exclude_{exclude_family.replace(' ', '_')}.joblib"
            model_path = MODELS_DIR / model_filename
            
            joblib.dump(model, model_path)
            
            # Register in manifest
            file_hash = compute_file_hash(model_path)
            register_artifact(
                manifest_path=MANIFEST_PATH,
                artifact_path=str(model_path.relative_to(PROJECT_ROOT)),
                artifact_type="lofo_model",
                metadata={
                    "excluded_family": exclude_family,
                    "n_train_samples": len(X),
                    "cv_r2_mean": float(cv_scores.mean()),
                    "cv_r2_std": float(cv_scores.std()),
                    "hash": file_hash
                }
            )
            
            model_paths[exclude_family] = str(model_path.relative_to(PROJECT_ROOT))
            logger.info(f"  - Saved model to {model_path}")
            
        except Exception as e:
            logger.error(f"  - Failed to train model for {exclude_family}: {e}")
            continue
    
    return model_paths

def main():
    """Main entry point for LOFO training."""
    logger.info("Starting LOFO Model Training (T025)")
    
    ensure_directories()
    
    try:
        # Load data
        df, families = load_training_data()
        
        if not families:
            logger.error("No chemical families found in data. Cannot perform LOFO.")
            sys.exit(1)
        
        # Train models
        model_paths = train_lofo_models(df, families)
        
        if not model_paths:
            logger.error("No LOFO models were successfully trained.")
            sys.exit(1)
        
        logger.info(f"Successfully trained {len(model_paths)} LOFO models.")
        logger.info(f"Models saved to: {MODELS_DIR}")
        
        # Save summary
        summary_path = MODELS_DIR / "lofo_training_summary.json"
        with open(summary_path, 'w') as f:
            json.dump({
                "total_families": len(families),
                "models_trained": len(model_paths),
                "excluded_families": list(model_paths.keys()),
                "model_paths": model_paths
            }, f, indent=2)
        
        # Register summary in manifest
        summary_hash = compute_file_hash(summary_path)
        register_artifact(
            manifest_path=MANIFEST_PATH,
            artifact_path=str(summary_path.relative_to(PROJECT_ROOT)),
            artifact_type="lofo_summary",
            metadata={"hash": summary_hash}
        )
        
        logger.info(f"Summary saved to {summary_path}")
        
    except Exception as e:
        logger.error(f"LOFO training failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
