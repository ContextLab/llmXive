"""
Train a Random Forest classifier to predict avian foraging guilds from land cover proportions.

This script implements T019:
1. Loads species profiles from data/processed/species_profiles.csv
2. Normalizes land cover proportion features
3. Encodes foraging guild labels
4. Handles missing values via imputation
5. Trains a Random Forest with k-fold cross-validation
6. Saves the model to data/models/random_forest.pkl
7. Saves training metrics to data/models/training_metrics.json
"""
import os
import sys
import json
import logging
import pickle
from pathlib import Path
from typing import Dict, Any, Tuple

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import cross_val_score, StratifiedKFold
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from utils.config import get_models_dir, get_processed_dir, get_seed, set_seed, get_model_params

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(project_root / 'code' / 'models' / 'train.log')
    ]
)
logger = logging.getLogger(__name__)


def load_species_profiles(input_path: Path) -> pd.DataFrame:
    """Load and validate the species profiles CSV."""
    logger.info(f"Loading species profiles from {input_path}")
    
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    df = pd.read_csv(input_path)
    
    required_cols = ['species_id', 'foraging_guild']
    if not all(col in df.columns for col in required_cols):
        raise ValueError(f"Missing required columns. Found: {df.columns.tolist()}, Required: {required_cols}")
    
    # Identify land cover columns (expected to have '_prop' suffix)
    land_cover_cols = [col for col in df.columns if col.endswith('_prop')]
    if not land_cover_cols:
        raise ValueError("No land cover proportion columns found in input data")
    
    logger.info(f"Found {len(land_cover_cols)} land cover features")
    logger.info(f"Loaded {len(df)} species profiles")
    
    return df, land_cover_cols


def prepare_features(df: pd.DataFrame, land_cover_cols: list) -> Tuple[np.ndarray, np.ndarray, LabelEncoder]:
    """
    Prepare features and labels for training.
    
    Returns:
      X: Feature matrix (land cover proportions)
      y: Label array (encoded foraging guilds)
      le: Fitted LabelEncoder for guilds
    """
    # Extract features
    X = df[land_cover_cols].values.astype(np.float64)
    
    # Encode labels
    le = LabelEncoder()
    y = le.fit_transform(df['foraging_guild'].values)
    
    logger.info(f"Feature matrix shape: {X.shape}")
    logger.info(f"Label classes: {le.classes_.tolist()}")
    
    return X, y, le


def train_random_forest(X: np.ndarray, y: np.ndarray, seed: int) -> Tuple[Pipeline, Dict[str, Any]]:
    """
    Train a Random Forest classifier with cross-validation.
    
    Returns:
      model: Fitted sklearn Pipeline
      metrics: Dictionary of training metrics
    """
    params = get_model_params()
    n_splits = params.get('n_splits', 5)
    cv_seed = params.get('cv_seed', seed)
    
    # Create preprocessing and model pipeline
    model = Pipeline([
        ('imputer', SimpleImputer(strategy='mean')),
        ('scaler', StandardScaler()),
        ('rf', RandomForestClassifier(
            n_estimators=params.get('n_estimators', 100),
            max_depth=params.get('max_depth', None),
            min_samples_split=params.get('min_samples_split', 2),
            min_samples_leaf=params.get('min_samples_leaf', 1),
            random_state=seed,
            n_jobs=-1,
            class_weight='balanced'
        ))
    ])
    
    # Cross-validation
    logger.info(f"Performing {n_splits}-fold stratified cross-validation")
    cv = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=cv_seed)
    
    cv_scores = cross_val_score(model, X, y, cv=cv, scoring='accuracy')
    
    # Train final model on full data
    logger.info("Training final model on full dataset")
    model.fit(X, y)
    
    # Compute additional metrics
    train_accuracy = model.score(X, y)
    
    # Feature importance
    feature_importances = model.named_steps['rf'].feature_importances_
    
    metrics = {
        'cv_mean_accuracy': float(np.mean(cv_scores)),
        'cv_std_accuracy': float(np.std(cv_scores)),
        'cv_scores': cv_scores.tolist(),
        'train_accuracy': float(train_accuracy),
        'n_estimators': params.get('n_estimators', 100),
        'n_features': X.shape[1],
        'n_samples': X.shape[0],
        'n_classes': len(np.unique(y)),
        'feature_importances': {
            str(i): float(imp) for i, imp in enumerate(feature_importances)
        }
    }
    
    logger.info(f"Cross-validation accuracy: {metrics['cv_mean_accuracy']:.4f} (+/- {metrics['cv_std_accuracy']:.4f})")
    logger.info(f"Training accuracy: {metrics['train_accuracy']:.4f}")
    
    return model, metrics


def save_artifacts(model: Pipeline, metrics: Dict[str, Any], le: LabelEncoder, output_dir: Path, seed: int):
    """Save model, metrics, and label encoder to disk."""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    model_path = output_dir / 'random_forest.pkl'
    metrics_path = output_dir / 'training_metrics.json'
    encoder_path = output_dir / 'label_encoder.pkl'
    
    # Save model
    logger.info(f"Saving model to {model_path}")
    with open(model_path, 'wb') as f:
        pickle.dump(model, f)
    
    # Save metrics
    logger.info(f"Saving metrics to {metrics_path}")
    metrics['seed'] = seed
    metrics['timestamp'] = pd.Timestamp.now().isoformat()
    with open(metrics_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    # Save label encoder
    logger.info(f"Saving label encoder to {encoder_path}")
    with open(encoder_path, 'wb') as f:
        pickle.dump(le, f)
    
    return model_path, metrics_path, encoder_path


def main():
    """Main entry point for training pipeline."""
    logger.info("Starting Random Forest training for avian foraging guild prediction")
    
    # Set random seed for reproducibility
    seed = get_seed()
    set_seed(seed)
    logger.info(f"Random seed set to: {seed}")
    
    # Paths
    input_path = get_processed_dir() / 'species_profiles.csv'
    output_dir = get_models_dir()
    
    # Load data
    df, land_cover_cols = load_species_profiles(input_path)
    
    # Prepare features
    X, y, le = prepare_features(df, land_cover_cols)
    
    # Train model
    model, metrics = train_random_forest(X, y, seed)
    
    # Save artifacts
    model_path, metrics_path, encoder_path = save_artifacts(model, metrics, le, output_dir, seed)
    
    # Verify outputs exist
    assert model_path.exists(), "Model file not created"
    assert metrics_path.exists(), "Metrics file not created"
    
    logger.info("Training completed successfully")
    logger.info(f"Model saved to: {model_path}")
    logger.info(f"Metrics saved to: {metrics_path}")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
