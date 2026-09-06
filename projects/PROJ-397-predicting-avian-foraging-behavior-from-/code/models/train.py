"""
Train a Random Forest classifier to predict avian foraging guilds from land cover proportions.

This script loads species-level profiles aggregated from merged eBird and NLCD data,
prepares features (normalization, encoding), trains a Random Forest model with k-fold CV,
and saves the trained model and training metrics.

Dependencies:
  - data/processed/species_profiles.csv (from T040)

Outputs:
  - data/models/random_forest.pkl: Trained Random Forest model
  - data/models/training_metrics.json: Training metrics log
"""
import os
import sys
import json
import logging
import pickle
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import cross_val_score, StratifiedKFold
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from utils.config import get_data_dir, get_models_dir, get_seed, get_model_params
from utils.provenance import record_artifact_provenance, load_metadata_config, save_metadata_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_species_profiles(input_path: Optional[str] = None) -> pd.DataFrame:
    """
    Load the species profiles CSV containing land cover proportions and foraging guilds.
    
    Args:
        input_path: Optional path to the input CSV. If None, uses default path.
        
    Returns:
        DataFrame with species profiles
        
    Raises:
        FileNotFoundError: If the input file does not exist
        ValueError: If required columns are missing
    """
    if input_path is None:
        input_path = str(get_data_dir() / "processed" / "species_profiles.csv")
    
    input_path = Path(input_path)
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    logger.info(f"Loading species profiles from {input_path}")
    df = pd.read_csv(input_path)
    
    # Validate required columns
    required_cols = ['species_id', 'foraging_guild']
    land_cover_cols = [col for col in df.columns if col.endswith('_prop_100m')]
    
    if not all(col in df.columns for col in required_cols):
        missing = [col for col in required_cols if col not in df.columns]
        raise ValueError(f"Missing required columns: {missing}")
    
    if len(land_cover_cols) == 0:
        raise ValueError("No land cover proportion columns found in input")
    
    logger.info(f"Loaded {len(df)} species profiles with {len(land_cover_cols)} land cover features")
    return df

def prepare_features(df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray, LabelEncoder, Pipeline]:
    """
    Prepare features and target for model training.
    
    Handles:
      - Missing values (imputation)
      - Normalization (StandardScaler)
      - Label encoding for foraging guilds
      - Train/test split logic (handled via CV)
    
    Args:
        df: DataFrame with species profiles
        
    Returns:
        Tuple of (X, y, label_encoder, pipeline)
    """
    # Extract features and target
    land_cover_cols = [col for col in df.columns if col.endswith('_prop_100m')]
    X = df[land_cover_cols].values
    y = df['foraging_guild'].values
    
    # Encode labels
    label_encoder = LabelEncoder()
    y_encoded = label_encoder.fit_transform(y)
    
    logger.info(f"Feature matrix shape: {X.shape}")
    logger.info(f"Number of classes: {len(label_encoder.classes_)}")
    logger.info(f"Classes: {list(label_encoder.classes_)}")
    
    # Create preprocessing pipeline
    pipeline = Pipeline([
        ('imputer', SimpleImputer(strategy='mean')),
        ('scaler', StandardScaler())
    ])
    
    # Fit and transform features
    X_processed = pipeline.fit_transform(X)
    
    return X_processed, y_encoded, label_encoder, pipeline

def train_random_forest(
    X: np.ndarray, 
    y: np.ndarray, 
    cv_folds: int = 5,
    random_state: Optional[int] = None
) -> Tuple[RandomForestClassifier, Dict[str, Any]]:
    """
    Train a Random Forest classifier with k-fold cross-validation.
    
    Args:
        X: Feature matrix (processed)
        y: Target labels (encoded)
        cv_folds: Number of CV folds
        random_state: Random seed for reproducibility
        
    Returns:
        Tuple of (trained model, metrics dict)
    """
    if random_state is None:
        random_state = get_seed()
    
    logger.info(f"Training Random Forest with {cv_folds}-fold CV (random_state={random_state})")
    
    # Get model parameters from config
    model_params = get_model_params()
    model_params['random_state'] = random_state
    
    # Initialize model
    rf_model = RandomForestClassifier(**model_params)
    
    # Setup cross-validation
    cv = StratifiedKFold(n_splits=cv_folds, shuffle=True, random_state=random_state)
    
    # Perform cross-validation
    cv_scores = cross_val_score(rf_model, X, y, cv=cv, scoring='accuracy')
    
    logger.info(f"CV Accuracy scores: {cv_scores}")
    logger.info(f"Mean CV Accuracy: {cv_scores.mean():.4f} (+/- {cv_scores.std():.4f})")
    
    # Train final model on full data
    rf_model.fit(X, y)
    
    # Compute feature importances
    feature_importances = dict(zip(
        [f"feature_{i}" for i in range(X.shape[1])],
        rf_model.feature_importances_.tolist()
    ))
    
    metrics = {
        'cv_folds': cv_folds,
        'cv_scores': cv_scores.tolist(),
        'mean_cv_accuracy': float(cv_scores.mean()),
        'std_cv_accuracy': float(cv_scores.std()),
        'n_estimators': model_params.get('n_estimators', 100),
        'max_depth': model_params.get('max_depth', None),
        'random_state': random_state,
        'feature_importances': feature_importances,
        'n_samples': X.shape[0],
        'n_classes': len(np.unique(y)),
        'training_status': 'completed'
    }
    
    return rf_model, metrics

def save_artifacts(
    model: RandomForestClassifier,
    metrics: Dict[str, Any],
    label_encoder: LabelEncoder,
    pipeline: Pipeline,
    model_path: Optional[str] = None,
    metrics_path: Optional[str] = None
) -> None:
    """
    Save the trained model and metrics to disk.
    
    Args:
        model: Trained Random Forest model
        metrics: Training metrics dictionary
        label_encoder: Fitted label encoder
        pipeline: Fitted preprocessing pipeline
        model_path: Optional path for model pickle
        metrics_path: Optional path for metrics JSON
    """
    if model_path is None:
        model_path = str(get_models_dir() / "random_forest.pkl")
    if metrics_path is None:
        metrics_path = str(get_models_dir() / "training_metrics.json")
    
    model_path = Path(model_path)
    metrics_path = Path(metrics_path)
    
    # Ensure directory exists
    model_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Saving model to {model_path}")
    logger.info(f"Saving metrics to {metrics_path}")
    
    # Save model and pipeline together
    artifact_bundle = {
        'model': model,
        'label_encoder': label_encoder,
        'pipeline': pipeline,
        'metrics': metrics
    }
    
    with open(model_path, 'wb') as f:
        pickle.dump(artifact_bundle, f)
    
    # Save metrics separately for easy access
    with open(metrics_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    # Record provenance
    try:
        metadata = load_metadata_config()
        record_artifact_provenance(
            metadata,
            artifact_name='random_forest_model',
            artifact_path=str(model_path),
            source_file='code/models/train.py',
            input_files=['data/processed/species_profiles.csv'],
            parameters=metrics
        )
        save_metadata_config(metadata)
    except Exception as e:
        logger.warning(f"Could not record provenance: {e}")
    
    logger.info("Artifacts saved successfully")

def main() -> None:
    """Main entry point for training script."""
    logger.info("Starting model training pipeline")
    
    try:
        # Load data
        df = load_species_profiles()
        
        # Prepare features
        X, y, label_encoder, pipeline = prepare_features(df)
        
        # Train model
        model, metrics = train_random_forest(X, y)
        
        # Save artifacts
        save_artifacts(model, metrics, label_encoder, pipeline)
        
        logger.info("Training pipeline completed successfully")
        
    except FileNotFoundError as e:
        logger.error(f"Data file not found: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Data validation error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during training: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
