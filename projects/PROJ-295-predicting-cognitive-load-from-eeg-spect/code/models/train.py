import numpy as np
import pandas as pd
from typing import Tuple, List, Optional
from sklearn.linear_model import Ridge
from sklearn.model_selection import GroupKFold
from sklearn.metrics import r2_score, mean_squared_error
import mne
import os
import sys
import json
import hashlib
import datetime
import logging
import argparse
from pathlib import Path

# Ensure we can import from the project root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from config import load_config, get_config_value
from data.loader import load_epochs_chunked, get_epoch_metadata
from features.extract import extract_features
from features.validity import identify_missing_sensor_epochs

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def calculate_subject_split_size(
    n_subjects: int,
    test_size: float = 0.2,
    n_folds: int = 5
) -> int:
    """
    Calculate the dynamic subject split size for cross-validation.
    
    Args:
        n_subjects: Total number of subjects.
        test_size: Fraction of subjects for the test set.
        n_folds: Number of folds for cross-validation.
        
    Returns:
        Number of subjects per fold (training set size per fold).
    """
    # Calculate number of subjects for the test set
    n_test = max(1, int(n_subjects * test_size))
    n_train = n_subjects - n_test
    
    # Ensure we have enough subjects for CV
    if n_train < n_folds:
        raise ValueError(f"Not enough subjects ({n_train}) for {n_folds}-fold cross-validation. "
                       f"Need at least {n_folds} subjects for training.")
    
    # Return the number of subjects per fold for the training set
    return n_train // n_folds

def subject_wise_cv(
    features: np.ndarray,
    labels: np.ndarray,
    subject_ids: np.ndarray,
    n_folds: int = 5,
    alpha: float = 1.0
) -> Tuple[List[Ridge], List[float], List[float]]:
    """
    Perform subject-wise 5-fold cross-validation.
    
    Args:
        features: Feature matrix (n_samples, n_features).
        labels: Target labels (n_samples,).
        subject_ids: Subject IDs for each sample.
        n_folds: Number of folds.
        alpha: Regularization strength for Ridge regression.
        
    Returns:
        Tuple of (models, r2_scores, rmse_scores).
    """
    gkf = GroupKFold(n_splits=n_folds)
    models = []
    r2_scores = []
    rmse_scores = []
    
    for train_idx, test_idx in gkf.split(features, labels, subject_ids):
        X_train, X_test = features[train_idx], features[test_idx]
        y_train, y_test = labels[train_idx], labels[test_idx]
        
        # Train model
        model = Ridge(alpha=alpha)
        model.fit(X_train, y_train)
        models.append(model)
        
        # Evaluate
        y_pred = model.predict(X_test)
        r2 = r2_score(y_test, y_pred)
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        
        r2_scores.append(r2)
        rmse_scores.append(rmse)
    
    return models, r2_scores, rmse_scores

def create_held_out_test_set(
    features: np.ndarray,
    labels: np.ndarray,
    subject_ids: np.ndarray,
    test_size: float = 0.2
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Create a distinct, non-overlapping held-out test set.
    
    Args:
        features: Feature matrix.
        labels: Target labels.
        subject_ids: Subject IDs.
        test_size: Fraction of subjects for the test set.
        
    Returns:
        Tuple of (X_train, y_train, X_test, y_test, test_subject_ids).
    """
    unique_subjects = np.unique(subject_ids)
    n_test = max(1, int(len(unique_subjects) * test_size))
    
    # Randomly select test subjects (seeded for reproducibility)
    np.random.seed(42)
    test_subjects = np.random.choice(unique_subjects, size=n_test, replace=False)
    
    # Split data
    test_mask = np.isin(subject_ids, test_subjects)
    train_mask = ~test_mask
    
    X_train = features[train_mask]
    y_train = labels[train_mask]
    X_test = features[test_mask]
    y_test = labels[test_mask]
    test_subject_ids = subject_ids[test_mask]
    
    return X_train, y_train, X_test, y_test, test_subject_ids

def train_final_model(
    X_train: np.ndarray,
    y_train: np.ndarray,
    alpha: float = 1.0
) -> Ridge:
    """
    Train the final model on the training set.
    
    Args:
        X_train: Training features.
        y_train: Training labels.
        alpha: Regularization strength.
        
    Returns:
        Trained Ridge model.
    """
    model = Ridge(alpha=alpha)
    model.fit(X_train, y_train)
    return model

def load_data_for_training(data_dir: str, feature_dir: str) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Load features and labels from processed data.
    
    Args:
        data_dir: Directory containing processed data.
        feature_dir: Directory containing extracted features.
        
    Returns:
        Tuple of (features, labels, subject_ids).
    """
    # Load features
    feature_path = os.path.join(feature_dir, 'extracted_features.parquet')
    if not os.path.exists(feature_path):
        raise FileNotFoundError(f"Features not found at {feature_path}. Run feature extraction first.")
    
    df_features = pd.read_parquet(feature_path)
    
    # Load labels
    label_path = os.path.join(data_dir, 'cognitive_load_labels.parquet')
    if not os.path.exists(label_path):
        raise FileNotFoundError(f"Labels not found at {label_path}. Run label generation first.")
    
    df_labels = pd.read_parquet(label_path)
    
    # Merge features and labels
    df = pd.merge(df_features, df_labels, on=['epoch_id', 'subject_id'])
    
    # Extract features and labels
    feature_cols = [col for col in df.columns if col not in ['epoch_id', 'subject_id', 'cognitive_load']]
    features = df[feature_cols].values
    labels = df['cognitive_load'].values
    subject_ids = df['subject_id'].values
    
    return features, labels, subject_ids

def main():
    """
    Main entry point for training pipeline.
    Calculates dynamic subject split size and prepares data for training.
    """
    parser = argparse.ArgumentParser(description='Train cognitive load prediction model')
    parser.add_argument('--data-dir', type=str, default='data/processed',
                      help='Directory containing processed data')
    parser.add_argument('--feature-dir', type=str, default='data/processed',
                      help='Directory containing extracted features')
    parser.add_argument('--output-dir', type=str, default='results',
                      help='Directory for output files')
    parser.add_argument('--test-size', type=float, default=0.2,
                      help='Fraction of subjects for test set')
    parser.add_argument('--n-folds', type=int, default=5,
                      help='Number of folds for cross-validation')
    args = parser.parse_args()
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Load configuration
    config = load_config()
    
    logger.info(f"Loading data from {args.data_dir} and {args.feature_dir}")
    
    try:
        # Load data
        features, labels, subject_ids = load_data_for_training(args.data_dir, args.feature_dir)
        
        # Get unique subjects
        unique_subjects = np.unique(subject_ids)
        n_subjects = len(unique_subjects)
        
        logger.info(f"Loaded {len(features)} samples from {n_subjects} subjects")
        
        # Calculate dynamic subject split size
        split_size = calculate_subject_split_size(
            n_subjects=n_subjects,
            test_size=args.test_size,
            n_folds=args.n_folds
        )
        
        logger.info(f"Calculated subject split size: {split_size} subjects per fold")
        logger.info(f"Test set will contain {int(n_subjects * args.test_size)} subjects")
        logger.info(f"Training set will contain {n_subjects - int(n_subjects * args.test_size)} subjects")
        
        # Create held-out test set
        X_train, y_train, X_test, y_test, test_subject_ids = create_held_out_test_set(
            features=features,
            labels=labels,
            subject_ids=subject_ids,
            test_size=args.test_size
        )
        
        logger.info(f"Created held-out test set with {len(np.unique(test_subject_ids))} subjects")
        logger.info(f"Training set: {len(X_train)} samples, {len(np.unique(subject_ids[~np.isin(subject_ids, test_subject_ids)]))} subjects")
        
        # Train final model
        alpha = get_config_value(config, 'model.alpha', 1.0)
        model = train_final_model(X_train, y_train, alpha=alpha)
        
        logger.info(f"Trained final model with alpha={alpha}")
        
        # Evaluate on test set
        y_pred = model.predict(X_test)
        r2 = r2_score(y_test, y_pred)
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        
        logger.info(f"Test set performance: R²={r2:.4f}, RMSE={rmse:.4f}")
        
        # Save results
        results = {
            'split_info': {
                'total_subjects': n_subjects,
                'test_subjects': int(n_subjects * args.test_size),
                'train_subjects': n_subjects - int(n_subjects * args.test_size),
                'subjects_per_fold': split_size
            },
            'test_performance': {
                'r2': float(r2),
                'rmse': float(rmse),
                'n_test_samples': len(X_test),
                'n_test_subjects': len(np.unique(test_subject_ids))
            },
            'model_params': {
                'alpha': alpha,
                'test_size': args.test_size,
                'n_folds': args.n_folds
            }
        }
        
        output_path = os.path.join(args.output_dir, 'split_config.json')
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"Saved split configuration to {output_path}")
        
    except FileNotFoundError as e:
        logger.error(f"Data file not found: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error during training pipeline: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()