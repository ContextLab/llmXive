import os
import sys
import json
import pickle
import pandas as pd
from pathlib import Path
import logging

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.constants import RESULTS_DIR, DATA_PROCESSED_DIR
from utils.io import compute_file_hash, log_artifact

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_model():
    """Load the trained model from results/model.pkl."""
    model_path = RESULTS_DIR / "model.pkl"
    if not model_path.exists():
        raise FileNotFoundError(f"Model file not found: {model_path}")
    
    with open(model_path, 'rb') as f:
        model = pickle.load(f)
    return model

def extract_importance(model, feature_names):
    """
    Extract feature importances from the trained Random Forest model.
    Rank metabolites by mean decrease in impurity.
    
    Args:
        model: Trained RandomForestClassifier.
        feature_names: List of feature names corresponding to model columns.
    
    Returns:
        list: List of dicts with 'feature', 'importance', 'rank'.
    """
    importances = model.feature_importances_
    indices = np.argsort(importances)[::-1] # Sort descending
    
    ranked_features = []
    for rank, idx in enumerate(indices, start=1):
        ranked_features.append({
            "rank": rank,
            "feature": feature_names[idx],
            "importance": float(importances[idx])
        })
    
    return ranked_features

def main():
    """
    Main entry point for T020c (Feature Importance Extraction).
    Reads model.pkl, extracts importances, saves to results/feature_importance_ranking.json.
    """
    try:
        # Load model
        model = load_model()
        
        # We need the original feature names. 
        # They should be stored in the model's feature_importances_dict if we saved it in train.py
        # Or we can load from the processed data matrix to ensure alignment.
        matrix_path = DATA_PROCESSED_DIR / "batch_corrected_matrix.csv"
        if matrix_path.exists():
            df = pd.read_csv(matrix_path, index_col=0)
            feature_names = df.columns.tolist()
        else:
            # Fallback if we stored it in the model (as done in train.py)
            if hasattr(model, 'feature_importances_dict'):
                feature_names = list(model.feature_importances_dict.keys())
            else:
                raise RuntimeError("Cannot determine feature names. Please ensure batch_corrected_matrix.csv exists.")

        logger.info(f"Extracting importances for {len(feature_names)} features.")
        
        # Extract and rank
        ranking = extract_importance(model, feature_names)
        
        # Save output
        output_path = RESULTS_DIR / "feature_importance_ranking.json"
        with open(output_path, 'w') as f:
            json.dump(ranking, f, indent=2)
        
        logger.info(f"Feature importance ranking saved to {output_path}")
        log_artifact("feature_importance_ranking.json", compute_file_hash(output_path))
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error during extraction: {e}")
        raise

if __name__ == "__main__":
    main()
