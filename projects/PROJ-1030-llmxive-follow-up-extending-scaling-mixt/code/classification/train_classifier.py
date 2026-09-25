import os
import sys
import json
import logging
import pickle
import argparse
from pathlib import Path
from typing import Tuple, Optional, Dict, Any

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.metrics import classification_report
from sklearn.preprocessing import StandardScaler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_filtered_data(
    features_path: Path,
    labels_path: Path
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Load features and labels, filtering out 'null' labels.
    
    Returns:
        X: Feature matrix (n_samples, n_features)
        y: Labels (n_samples,) encoded as integers
        indices: Original indices for traceability
    """
    logger.info(f"Loading features from {features_path}")
    if not features_path.exists():
        raise FileNotFoundError(f"Features file not found: {features_path}")
    
    features_data = np.load(features_path, allow_pickle=True)
    # Handle both dict (with 'features') and direct array formats
    if isinstance(features_data, dict):
        X = features_data['features']
    else:
        X = features_data
    
    logger.info(f"Loading labels from {labels_path}")
    if not labels_path.exists():
        raise FileNotFoundError(f"Labels file not found: {labels_path}")
    
    import pandas as pd
    labels_df = pd.read_csv(labels_path)
    
    # Filter out 'null' labels as per T030.1 requirements
    non_null_mask = labels_df['label'] != 'null'
    filtered_df = labels_df[non_null_mask]
    
    if len(filtered_df) == 0:
        raise ValueError("No valid (non-null) labels found in the dataset.")
    
    # Extract clip IDs for traceability
    indices = filtered_df['clip_id'].values
    
    # Encode labels: valid -> 1, invalid -> 0
    label_map = {'valid': 1, 'invalid': 0}
    y = filtered_df['label'].map(label_map).values
    
    if np.any(np.isnan(y)):
        raise ValueError("Found labels that could not be mapped to valid/invalid.")
    
    logger.info(f"Loaded {len(X)} samples. Filtered to {len(y)} non-null samples.")
    return X, y, indices

def encode_labels(y: np.ndarray) -> np.ndarray:
    """
    Ensure labels are integers (0 for invalid, 1 for valid).
    """
    return y.astype(int)

def train_model(
    X: np.ndarray,
    y: np.ndarray,
    model_type: str = "random_forest",
    output_path: Path = None
) -> Dict[str, Any]:
    """
    Train a shallow classifier (MLP or Random Forest) on CPU.
    
    Args:
        X: Feature matrix
        y: Labels
        model_type: 'random_forest' or 'mlp'
        output_path: Path to save the trained model
    
    Returns:
        Dictionary containing the trained model and training stats
    """
    logger.info(f"Training {model_type} model...")
    
    # Split data for validation (80/20)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    # Standardize features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Define hyperparameter grid for limited grid search (FR-004)
    if model_type == "random_forest":
        param_grid = {
            'n_estimators': [50, 100],
            'max_depth': [5, 10, None],
            'min_samples_split': [2, 5]
        }
        base_model = RandomForestClassifier(random_state=42, n_jobs=-1)
    else:  # mlp
        param_grid = {
            'hidden_layer_sizes': [(50,), (100,), (50, 25)],
            'max_iter': [200, 500],
            'alpha': [0.0001, 0.001]
        }
        base_model = MLPClassifier(random_state=42, max_iter=1000, early_stopping=True)
    
    # Perform limited grid search
    logger.info("Performing limited grid search...")
    grid_search = GridSearchCV(
        base_model, 
        param_grid, 
        cv=3, 
        scoring='f1', 
        n_jobs=-1,
        verbose=1
    )
    
    grid_search.fit(X_train_scaled, y_train)
    
    logger.info(f"Best parameters: {grid_search.best_params_}")
    logger.info(f"Best CV F1 score: {grid_search.best_score_:.4f}")
    
    # Evaluate on test set
    best_model = grid_search.best_estimator_
    y_pred = best_model.predict(X_test_scaled)
    
    report = classification_report(y_test, y_pred, output_dict=True)
    test_f1 = report['weighted avg']['f1-score']
    
    logger.info(f"Test set F1 score: {test_f1:.4f}")
    
    # Prepare results
    result = {
        'model': best_model,
        'scaler': scaler,
        'model_type': model_type,
        'best_params': grid_search.best_params_,
        'best_cv_f1': grid_search.best_score_,
        'test_f1': test_f1,
        'classification_report': report
    }
    
    # Save model if path provided
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'wb') as f:
            pickle.dump(result, f)
        logger.info(f"Model saved to {output_path}")
    
    return result

def main():
    parser = argparse.ArgumentParser(description="Train a physical validity classifier.")
    parser.add_argument(
        "--features", 
        type=str, 
        default="data/processed/features.npy",
        help="Path to features.npy"
    )
    parser.add_argument(
        "--labels", 
        type=str, 
        default="data/processed/labels.csv",
        help="Path to labels.csv"
    )
    parser.add_argument(
        "--output", 
        type=str, 
        default="data/processed/classifier.pkl",
        help="Path to save the trained model"
    )
    parser.add_argument(
        "--model", 
        type=str, 
        choices=["random_forest", "mlp"], 
        default="random_forest",
        help="Model type to train"
    )
    
    args = parser.parse_args()
    
    try:
        # Load data
        X, y, indices = load_filtered_data(
            Path(args.features), 
            Path(args.labels)
        )
        
        # Train model
        result = train_model(
            X, 
            y, 
            model_type=args.model, 
            output_path=Path(args.output)
        )
        
        # Save training stats as JSON for audit
        stats_path = Path(args.output).with_suffix('.json')
        stats_to_save = {
            'model_type': result['model_type'],
            'best_params': result['best_params'],
            'best_cv_f1': result['best_cv_f1'],
            'test_f1': result['test_f1'],
            'classification_report': result['classification_report']
        }
        with open(stats_path, 'w') as f:
            json.dump(stats_to_save, f, indent=2)
        logger.info(f"Training stats saved to {stats_path}")
        
        logger.info("Training completed successfully.")
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Data error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during training: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
