import os
import sys
import json
import logging
import pickle
from pathlib import Path
from typing import Dict, Any, List, Tuple

import pandas as pd
import numpy as np
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import balanced_accuracy_score, f1_score

# Import project utilities
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from utils.config import get_models_dir, get_data_dir, get_seed, set_seed
from utils.provenance import record_artifact_provenance, load_metadata_config, save_metadata_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_species_profiles(input_path: str) -> pd.DataFrame:
    """
    Load the species profiles CSV.
    
    Args:
        input_path: Path to species_profiles.csv
        
    Returns:
        DataFrame with species profiles
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    df = pd.read_csv(input_path)
    logger.info(f"Loaded {len(df)} species profiles from {input_path}")
    
    # Verify required columns exist
    required_cols = ['species_id', 'foraging_guild']
    land_cover_cols = [col for col in df.columns if 'prop_100m' in col]
    
    if not all(col in df.columns for col in required_cols):
        missing = [col for col in required_cols if col not in df.columns]
        raise ValueError(f"Missing required columns: {missing}")
    
    if len(land_cover_cols) == 0:
        raise ValueError("No land cover proportion columns found (expected columns with 'prop_100m')")
    
    logger.info(f"Found {len(land_cover_cols)} land cover predictor columns")
    return df

def prepare_features(df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray, List[str], LabelEncoder]:
    """
    Prepare features and labels for training.
    
    Args:
        df: DataFrame with species profiles
        
    Returns:
        Tuple of (X_scaled, y_encoded, feature_names, label_encoder)
    """
    # Identify predictor columns (land cover proportions)
    feature_cols = [col for col in df.columns if 'prop_100m' in col]
    feature_names = feature_cols.copy()
    
    # Extract features and labels
    X = df[feature_cols].values
    y = df['foraging_guild'].values
    
    # Encode labels
    label_encoder = LabelEncoder()
    y_encoded = label_encoder.fit_transform(y)
    
    logger.info(f"Feature matrix shape: {X.shape}")
    logger.info(f"Label classes: {label_encoder.classes_}")
    
    # Check for sufficient samples
    if len(np.unique(y_encoded)) < 2:
        raise ValueError("Need at least 2 classes for classification")
    
    # Standardize features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    return X_scaled, y_encoded, feature_names, label_encoder, scaler

def train_random_forest(X: np.ndarray, y: np.ndarray, feature_names: List[str], n_splits: int = 5) -> Tuple[RandomForestClassifier, Dict[str, Any], np.ndarray, np.ndarray]:
    """
    Train a Random Forest classifier with k-fold cross-validation.
    
    Args:
        X: Scaled feature matrix
        y: Encoded labels
        feature_names: List of feature names
        n_splits: Number of CV folds
        
    Returns:
        Tuple of (model, metrics, oof_predictions, true_labels)
    """
    seed = get_seed()
    set_seed(seed)
    
    # Define cross-validation strategy
    cv = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=seed)
    
    # Initialize model with fixed hyperparameters
    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=None,
        min_samples_split=2,
        min_samples_leaf=1,
        random_state=seed,
        n_jobs=-1
    )
    
    # Get out-of-fold predictions
    logger.info(f"Running {n_splits}-fold cross-validation...")
    oof_predictions = cross_val_predict(model, X, y, cv=cv, method='predict')
    
    # Calculate metrics
    balanced_acc = balanced_accuracy_score(y, oof_predictions)
    f1_macro = f1_score(y, oof_predictions, average='macro')
    f1_weighted = f1_score(y, oof_predictions, average='weighted')
    f1_per_class = f1_score(y, oof_predictions, average=None)
    
    metrics = {
        'balanced_accuracy': float(balanced_acc),
        'f1_macro': float(f1_macro),
        'f1_weighted': float(f1_weighted),
        'f1_per_class': [float(f) for f in f1_per_class],
        'n_splits': n_splits,
        'random_seed': seed,
        'n_samples': len(y),
        'n_classes': len(np.unique(y))
    }
    
    logger.info(f"Cross-validated Balanced Accuracy: {balanced_acc:.4f}")
    logger.info(f"Cross-validated F1 Macro: {f1_macro:.4f}")
    
    # Train final model on full dataset for feature importance and saving
    model.fit(X, y)
    
    return model, metrics, oof_predictions, y

def save_artifacts(model: RandomForestClassifier, metrics: Dict[str, Any], 
                 oof_predictions: np.ndarray, true_labels: np.ndarray,
                 label_encoder: LabelEncoder, scaler: StandardScaler,
                 feature_names: List[str]) -> Dict[str, str]:
    """
    Save all model artifacts and training results.
    
    Args:
        model: Trained RandomForestClassifier
        metrics: Training metrics dictionary
        oof_predictions: Out-of-fold predictions
        true_labels: True labels
        label_encoder: Fitted LabelEncoder
        scaler: Fitted StandardScaler
        feature_names: List of feature names
        
    Returns:
        Dictionary of saved file paths
    """
    models_dir = get_models_dir()
    models_dir.mkdir(parents=True, exist_ok=True)
    
    # Save model
    model_path = models_dir / 'random_forest.pkl'
    with open(model_path, 'wb') as f:
        pickle.dump({
            'model': model,
            'scaler': scaler,
            'label_encoder': label_encoder,
            'feature_names': feature_names
        }, f)
    logger.info(f"Saved model to {model_path}")
    
    # Save training metrics
    metrics_path = models_dir / 'training_metrics.json'
    with open(metrics_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    logger.info(f"Saved metrics to {metrics_path}")
    
    # Save cross-validation predictions
    cv_preds_path = models_dir / 'cv_predictions.json'
    cv_data = {
        'out_of_fold_predictions': oof_predictions.tolist(),
        'true_labels': true_labels.tolist(),
        'label_classes': label_encoder.classes_.tolist(),
        'feature_names': feature_names,
        'n_folds': 5
    }
    with open(cv_preds_path, 'w') as f:
        json.dump(cv_data, f, indent=2)
    logger.info(f"Saved CV predictions to {cv_preds_path}")
    
    # Record provenance
    provenance = {
        'step': 'train_model',
        'artifacts': [
            str(model_path),
            str(metrics_path),
            str(cv_preds_path)
        ],
        'input': 'species_profiles.csv',
        'parameters': {
            'n_estimators': 100,
            'random_state': get_seed(),
            'cv_splits': 5
        }
    }
    record_artifact_provenance(provenance)
    
    return {
        'model': str(model_path),
        'metrics': str(metrics_path),
        'cv_predictions': str(cv_preds_path)
    }

def main():
    """Main entry point for training pipeline."""
    logger.info("Starting model training...")
    
    # Load data
    input_path = os.path.join(get_data_dir(), 'processed', 'species_profiles.csv')
    df = load_species_profiles(input_path)
    
    # Check minimum sample size
    if len(df) < 25:
        raise ValueError(f"Insufficient data: {len(df)} species profiles. Need at least 25 for statistical power.")
    
    # Prepare features
    X, y, feature_names, label_encoder, scaler = prepare_features(df)
    
    # Train model
    model, metrics, oof_predictions, true_labels = train_random_forest(X, y, feature_names)
    
    # Save artifacts
    saved_paths = save_artifacts(model, metrics, oof_predictions, true_labels, 
                                label_encoder, scaler, feature_names)
    
    logger.info("Training complete!")
    logger.info(f"Model saved to: {saved_paths['model']}")
    logger.info(f"Metrics saved to: {saved_paths['metrics']}")
    logger.info(f"CV predictions saved to: {saved_paths['cv_predictions']}")
    
    return saved_paths

if __name__ == '__main__':
    main()