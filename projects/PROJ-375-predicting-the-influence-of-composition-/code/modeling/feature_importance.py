import os
import sys
import json
import logging
import pandas as pd
from pathlib import Path
import joblib

# Add project root to path if running as script
if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from modeling.serialize import load_model
from utils.io import setup_logging, compute_sha256
from utils.config import get_env_var

logger = setup_logging()

def load_latest_rf_model(models_dir: Path) -> tuple:
    """
    Locate and load the latest Random Forest model and its metadata.
    Returns (model, metadata_dict).
    Raises FileNotFoundError if no model is found.
    """
    if not models_dir.exists():
        raise FileNotFoundError(f"Models directory not found: {models_dir}")

    # Look for files matching pattern: random_forest_v*.pkl
    # Sort by modification time to get the latest
    model_files = sorted(models_dir.glob("random_forest_v*.pkl"), key=lambda x: x.stat().st_mtime, reverse=True)
    
    if not model_files:
        raise FileNotFoundError(f"No Random Forest model found in {models_dir}")

    latest_model_path = model_files[0]
    logger.info(f"Loading latest Random Forest model from: {latest_model_path}")
    
    try:
        model = joblib.load(str(latest_model_path))
    except Exception as e:
        logger.error(f"Failed to load model {latest_model_path}: {e}")
        raise

    # Try to load corresponding metadata
    meta_path = latest_model_path.with_suffix('.meta.json')
    metadata = {}
    if meta_path.exists():
        try:
            with open(meta_path, 'r') as f:
                metadata = json.load(f)
        except Exception as e:
            logger.warning(f"Could not load metadata from {meta_path}: {e}")
    else:
        logger.warning(f"No metadata file found for {latest_model_path}")

    return model, metadata

def extract_feature_importance(model, feature_names: list) -> pd.DataFrame:
    """
    Extract feature importance from a trained Random Forest model.
    
    Args:
        model: Trained RandomForestRegressor
        feature_names: List of feature names corresponding to model's feature order
        
    Returns:
        DataFrame with columns 'feature' and 'importance_score'
    """
    if not hasattr(model, 'feature_importances_'):
        raise AttributeError("Model does not have feature_importances_ attribute")
    
    importances = model.feature_importances_
    
    # Create DataFrame
    df = pd.DataFrame({
        'feature': feature_names,
        'importance_score': importances
    })
    
    # Sort by importance descending
    df = df.sort_values(by='importance_score', ascending=False).reset_index(drop=True)
    
    return df

def save_feature_importance(df: pd.DataFrame, output_path: Path) -> str:
    """
    Save feature importance DataFrame to CSV.
    
    Args:
        df: DataFrame with 'feature' and 'importance_score' columns
        output_path: Path to save the CSV file
        
    Returns:
        SHA256 checksum of the saved file
    """
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save to CSV
    df.to_csv(output_path, index=False)
    logger.info(f"Feature importance saved to: {output_path}")
    
    # Compute checksum
    checksum = compute_sha256(str(output_path))
    logger.info(f"Checksum: {checksum}")
    
    return checksum

def main():
    """
    Main entry point for feature importance extraction.
    Loads the latest RF model, extracts importance, and saves to results/.
    """
    # Define paths
    project_root = Path(__file__).resolve().parent.parent.parent
    models_dir = project_root / "code" / "models"
    results_dir = project_root / "results"
    output_file = results_dir / "feature_importance.csv"
    
    # Expected feature names based on T025 and T016
    feature_names = [
        'mean_atomic_radius',
        'electronegativity_var',
        'vec',
        'size_mismatch'
    ]
    
    try:
        # Load model
        model, metadata = load_latest_rf_model(models_dir)
        
        # Extract importance
        importance_df = extract_feature_importance(model, feature_names)
        
        # Save results
        checksum = save_feature_importance(importance_df, output_file)
        
        # Log summary
        logger.info("Feature Importance Summary:")
        for _, row in importance_df.iterrows():
            logger.info(f"  {row['feature']}: {row['importance_score']:.6f}")
        
        logger.info(f"Task T037 completed successfully. Output: {output_file}")
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return 1
    except Exception as e:
        logger.error(f"Error during feature importance extraction: {e}")
        raise

if __name__ == "__main__":
    sys.exit(main())