"""
Interpretability module for LST wear resistance models.
Computes SHAP values and generates interpretability reports.
"""
import os
import sys
import json
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

# Import from project modules
from seed import set_seed, get_seed, ensure_seed_set
from logging_config import setup_logging, get_logger, raise_on_missing_data
from hygiene import calculate_md5, update_artifact_hash, save_artifact_hashes

# Try to import SHAP and model loading dependencies
try:
    import joblib
    import shap
    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False
    # We will raise an error in main if not available

# Constants
PROJECT_ROOT = Path(__file__).parent.parent
MODELS_DIR = PROJECT_ROOT / "models"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
REPORTS_DIR = PROJECT_ROOT / "reports"
STATE_DIR = PROJECT_ROOT / "state"

# Ensure directories exist
DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)
STATE_DIR.mkdir(parents=True, exist_ok=True)

def load_best_model(model_path: Optional[Path] = None):
    """
    Load the best model saved by the training pipeline.
    
    Args:
        model_path: Path to the model file. Defaults to models/best_model.joblib
        
    Returns:
        The loaded model object
        
    Raises:
        FileNotFoundError: If model file does not exist
        ImportError: If SHAP or joblib is not installed
    """
    if not SHAP_AVAILABLE:
        raise ImportError(
            "SHAP or joblib is not installed. "
            "Please install dependencies: pip install shap joblib"
        )
    
    if model_path is None:
        model_path = MODELS_DIR / "best_model.joblib"
    
    model_path = Path(model_path)
    if not model_path.exists():
        raise FileNotFoundError(f"Best model not found at {model_path}. "
                              "Run training pipeline (T025) first.")
    
    logger = get_logger(__name__)
    logger.info(f"Loading best model from {model_path}")
    model = joblib.load(model_path)
    return model

def load_processed_data(data_path: Optional[Path] = None) -> pd.DataFrame:
    """
    Load the normalized dataset used for training.
    
    Args:
        data_path: Path to the data file. Defaults to data/processed/normalized_only.csv
        
    Returns:
        DataFrame with processed data
        
    Raises:
        FileNotFoundError: If data file does not exist
    """
    if data_path is None:
        data_path = DATA_PROCESSED_DIR / "normalized_only.csv"
    
    data_path = Path(data_path)
    if not data_path.exists():
        raise FileNotFoundError(f"Normalized data not found at {data_path}. "
                              "Run ingestion pipeline (T014) first.")
    
    logger = get_logger(__name__)
    logger.info(f"Loading normalized data from {data_path}")
    df = pd.read_csv(data_path)
    return df

def prepare_features_targets(df: pd.DataFrame, target_col: str = 'wear_coefficient') -> Tuple[np.ndarray, np.ndarray, list]:
    """
    Prepare features and targets from the dataframe.
    
    Args:
        df: Processed DataFrame
        target_col: Name of the target column
        
    Returns:
        Tuple of (features_array, target_array, feature_names)
    """
    logger = get_logger(__name__)
    
    # Identify feature columns (exclude target and metadata columns)
    exclude_cols = [target_col, 'normalization_method', 'material_class', 'source_id']
    feature_cols = [col for col in df.columns if col not in exclude_cols]
    
    # Filter to only numeric features
    numeric_features = []
    for col in feature_cols:
        if pd.api.types.is_numeric_dtype(df[col]):
            numeric_features.append(col)
        else:
            logger.warning(f"Skipping non-numeric feature column: {col}")
    
    if len(numeric_features) == 0:
        raise ValueError("No numeric feature columns found in dataset")
    
    logger.info(f"Using {len(numeric_features)} features: {numeric_features}")
    
    X = df[numeric_features].values
    y = df[target_col].values if target_col in df.columns else None
    
    return X, y, numeric_features

def compute_shap_values(
    model=None,
    data_path: Optional[Path] = None,
    model_path: Optional[Path] = None,
    output_path: Optional[Path] = None,
    use_tree_explainer: bool = True
) -> Dict[str, Any]:
    """
    Compute SHAP values for the best model.
    
    This function:
    1. Loads the best model from disk
    2. Loads the normalized dataset
    3. Prepares features and targets
    4. Computes SHAP values using the appropriate explainer
    5. Saves SHAP values to disk
    6. Updates artifact hashes
    
    Args:
        model: Pre-loaded model (optional)
        data_path: Path to normalized data CSV
        model_path: Path to best_model.joblib
        output_path: Path to save SHAP values (default: data/processed/shap_values.npy)
        use_tree_explainer: Use TreeExplainer for tree-based models, otherwise use KernelExplainer
        
    Returns:
        Dictionary containing SHAP computation metadata
        
    Raises:
        FileNotFoundError: If model or data files not found
        ImportError: If SHAP is not installed
        ValueError: If computation fails
    """
    logger = get_logger(__name__)
    logger.info("Starting SHAP value computation")
    
    if not SHAP_AVAILABLE:
        raise ImportError(
            "SHAP library is required for interpretability analysis. "
            "Install with: pip install shap"
        )
    
    # Set seed for reproducibility
    set_seed(get_seed())
    
    # Load model if not provided
    if model is None:
        model = load_best_model(model_path)
    
    # Load data if not provided
    if data_path is None:
        data_path = DATA_PROCESSED_DIR / "normalized_only.csv"
    
    df = load_processed_data(data_path)
    
    # Prepare features
    X, y, feature_names = prepare_features_targets(df)
    
    logger.info(f"Feature matrix shape: {X.shape}")
    
    # Create explainer based on model type
    model_type = type(model).__name__
    logger.info(f"Model type: {model_type}")
    
    try:
        if use_tree_explainer and 'Tree' in model_type:
            # Use TreeExplainer for tree-based models (faster)
            logger.info("Using TreeExplainer for tree-based model")
            explainer = shap.TreeExplainer(model)
        else:
            # Use KernelExplainer for other models (more general but slower)
            logger.info("Using KernelExplainer for model")
            # Sample background data for KernelExplainer
            background = shap.kmeans(X, 10)
            explainer = shap.KernelExplainer(model.predict, background)
        
        logger.info("Computing SHAP values...")
        shap_values = explainer.shap_values(X)
        
        # Handle multi-output case (some models return list of arrays)
        if isinstance(shap_values, list):
            logger.warning("SHAP values returned as list, using first element")
            shap_values = shap_values[0]
        
        logger.info(f"SHAP values shape: {shap_values.shape}")
        
        # Ensure output directory exists
        if output_path is None:
            output_path = DATA_PROCESSED_DIR / "shap_values.npy"
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save SHAP values
        logger.info(f"Saving SHAP values to {output_path}")
        np.save(output_path, shap_values)
        
        # Also save feature names for reference
        feature_names_path = DATA_PROCESSED_DIR / "shap_feature_names.json"
        with open(feature_names_path, 'w') as f:
            json.dump(feature_names, f, indent=2)
        
        # Update artifact hash
        update_artifact_hash(output_path)
        save_artifact_hashes()
        
        # Compute summary statistics
        mean_abs_shap = np.abs(shap_values).mean(axis=0)
        shap_importance_rank = np.argsort(mean_abs_shap)[::-1]
        
        result = {
            "status": "success",
            "output_path": str(output_path),
            "shap_shape": list(shap_values.shape),
            "n_samples": X.shape[0],
            "n_features": X.shape[1],
            "feature_names": feature_names,
            "feature_importance_rank": shap_importance_rank.tolist(),
            "mean_abs_shap_values": mean_abs_shap.tolist(),
            "model_type": model_type,
            "explainer_type": "TreeExplainer" if use_tree_explainer and 'Tree' in model_type else "KernelExplainer"
        }
        
        logger.info(f"SHAP computation completed successfully. "
                   f"Top 3 features: {[feature_names[i] for i in shap_importance_rank[:3]]}")
        
        return result
        
    except Exception as e:
        logger.error(f"SHAP computation failed: {str(e)}", exc_info=True)
        raise ValueError(f"Failed to compute SHAP values: {str(e)}")

def main():
    """
    Main entry point for SHAP value computation.
    
    Usage:
        python code/interpret.py
    """
    # Setup logging
    setup_logging()
    logger = get_logger(__name__)
    
    logger.info("=" * 60)
    logger.info("Starting SHAP Value Computation (Task T026)")
    logger.info("=" * 60)
    
    try:
        # Ensure required files exist
        model_path = MODELS_DIR / "best_model.joblib"
        data_path = DATA_PROCESSED_DIR / "normalized_only.csv"
        
        if not model_path.exists():
            raise FileNotFoundError(
                f"Best model not found at {model_path}. "
                "Please run the training pipeline (T025) first."
            )
        
        if not data_path.exists():
            raise FileNotFoundError(
                f"Normalized data not found at {data_path}. "
                "Please run the ingestion pipeline (T014) first."
            )
        
        # Compute SHAP values
        result = compute_shap_values(
            model_path=model_path,
            data_path=data_path,
            output_path=DATA_PROCESSED_DIR / "shap_values.npy"
        )
        
        # Save result metadata
        result_path = REPORTS_DIR / "shap_computation_status.json"
        with open(result_path, 'w') as f:
            json.dump(result, f, indent=2)
        
        logger.info(f"Results saved to {result_path}")
        logger.info(f"SHAP values saved to {result['output_path']}")
        
        logger.info("=" * 60)
        logger.info("SHAP Value Computation Completed Successfully")
        logger.info("=" * 60)
        
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"Required file not found: {str(e)}")
        return 1
    except ImportError as e:
        logger.error(f"Missing dependency: {str(e)}")
        return 2
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
