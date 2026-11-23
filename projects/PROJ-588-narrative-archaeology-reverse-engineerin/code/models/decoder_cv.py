"""
K-Fold Cross-Validation and Accuracy Reporting for Narrative Reconstruction.

Implements 5-fold cross-validation for the decoder model and reports accuracy
against a chance baseline calculated as 1/N (where N is the number of unique
labels after aggregation).
"""
import numpy as np
import json
import logging
import sys
from pathlib import Path

from sklearn.linear_model import RidgeClassifier
from sklearn.model_selection import KFold, cross_val_score
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score

# Add parent directory to path for imports if running as script
if str(Path(__file__).parent.parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent.parent))

import code.config as config
from models.decoder import run_decoder_analysis  # Import base logic if needed, though we reimplement for CV

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_roi_features_and_labels():
    """
    Loads pre-extracted ROI timecourses and corresponding narrative labels.
    
    Returns:
        tuple: (X, y, label_encoder, original_labels)
            X: numpy array of shape (n_samples, n_features)
            y: numpy array of shape (n_samples,) containing integer labels
            label_encoder: fitted LabelEncoder object
            original_labels: list of original string labels
    """
    # Determine paths based on config
    data_path = Path(config.get_data_path())
    features_path = data_path / "processed" / "roi_timecourses.h5"
    labels_path = data_path / "processed" / "events_aligned.csv"
    
    logger.info(f"Loading features from {features_path}")
    logger.info(f"Loading labels from {labels_path}")
    
    if not features_path.exists():
        raise FileNotFoundError(f"Feature file not found: {features_path}. "
                                "Please ensure T013 (ROI Masker) has completed.")
    if not labels_path.exists():
        raise FileNotFoundError(f"Labels file not found: {labels_path}. "
                                "Please ensure T012 (Segmentation) has completed.")
    
    # Load features
    import h5py
    with h5py.File(features_path, 'r') as f:
        # Assuming 'data' key holds the flattened timecourses or a specific ROI aggregation
        # The schema from T013 usually stores timecourses. We flatten per event.
        # For this implementation, we assume the features have already been aggregated 
        # per event in T013 or T030 logic. If T013 outputs raw timecourses, we need 
        # to aggregate them here based on event indices.
        # To be robust, we look for a pre-aggregated matrix if available, or construct it.
        # Given T030 description implies aggregation happens there, we assume 
        # the input to this function is the aggregated matrix.
        
        # Fallback: If the file structure is raw timecourses, we need event indices.
        # For this task, we assume the data is pre-aggregated into events.
        if 'features' in f:
            X = f['features'][:]
        else:
            # Try to load 'data' and reshape if necessary
            X = f['data'][:]
            # If shape is (n_events, n_timepoints, n_voxels), flatten
            if len(X.shape) == 3:
                X = X.reshape(X.shape[0], -1)
    
    # Load labels
    import pandas as pd
    df = pd.read_csv(labels_path)
    
    # Ensure we have the 'label' column (from T004b)
    if 'label' not in df.columns:
        # Try common variations
        if 'narrative_label' in df.columns:
            y_str = df['narrative_label'].values
        elif 'category' in df.columns:
            y_str = df['category'].values
        else:
            raise KeyError("Could not find label column in events_aligned.csv. "
                           "Expected 'label', 'narrative_label', or 'category'.")
    else:
        y_str = df['label'].values
    
    # Remove NaNs
    valid_mask = ~np.isnan(X).any(axis=1) & pd.notna(y_str)
    X = X[valid_mask]
    y_str = y_str[valid_mask]
    
    if len(X) == 0:
        raise ValueError("No valid data points found after filtering NaNs.")
    
    # Encode labels
    le = LabelEncoder()
    y = le.fit_transform(y_str)
    
    logger.info(f"Loaded {X.shape[0]} samples with {len(le.classes_)} unique labels: {list(le.classes_)}")
    
    return X, y, le, list(le.classes_)

def run_kfold_cross_validation(X, y, k=5, random_state=42):
    """
    Runs K-Fold cross-validation using RidgeClassifier.
    
    Args:
        X: Feature matrix (n_samples, n_features)
        y: Labels (n_samples,)
        k: Number of folds (default 5)
        random_state: Random seed for reproducibility
        
    Returns:
        dict: Metrics including accuracy, chance baseline, and fold scores.
    """
    logger.info(f"Running {k}-fold cross-validation with RidgeClassifier...")
    
    # Calculate chance baseline (1/N)
    n_classes = len(np.unique(y))
    chance_baseline = 1.0 / n_classes
    
    # Setup K-Fold
    kf = KFold(n_splits=k, shuffle=True, random_state=random_state)
    
    # Initialize classifier
    clf = RidgeClassifier()
    
    # Run cross-validation
    # scoring='accuracy' is default for classification
    scores = cross_val_score(clf, X, y, cv=kf, scoring='accuracy')
    
    mean_accuracy = np.mean(scores)
    std_accuracy = np.std(scores)
    
    logger.info(f"Cross-validation completed. Mean Accuracy: {mean_accuracy:.4f} (+/- {std_accuracy:.4f})")
    logger.info(f"Chance Baseline (1/{n_classes}): {chance_baseline:.4f}")
    logger.info(f"Deviation from chance: {mean_accuracy - chance_baseline:.4f}")
    
    results = {
        "k_folds": k,
        "n_samples": X.shape[0],
        "n_classes": n_classes,
        "chance_baseline": chance_baseline,
        "mean_accuracy": float(mean_accuracy),
        "std_accuracy": float(std_accuracy),
        "fold_scores": scores.tolist(),
        "deviation_from_chance": float(mean_accuracy - chance_baseline),
        "random_state": random_state
    }
    
    return results

def main():
    """
    Main entry point for T031.
    Loads data, runs CV, and saves results to results/decoder_cv_metrics.json.
    """
    try:
        # 1. Load Data
        X, y, le, original_labels = load_roi_features_and_labels()
        
        # 2. Run Cross-Validation
        cv_results = run_kfold_cross_validation(X, y, k=5)
        
        # 3. Prepare Output
        output_dir = Path(config.get_output_path())
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / "decoder_cv_metrics.json"
        
        # Add label info to results for context
        cv_results["label_classes"] = original_labels
        
        # Save to JSON
        with open(output_file, 'w') as f:
            json.dump(cv_results, f, indent=2)
        
        logger.info(f"Results saved to {output_file}")
        
        # 4. Print Summary
        print(f"\n=== T031 Cross-Validation Summary ===")
        print(f"Samples: {cv_results['n_samples']}")
        print(f"Classes: {cv_results['n_classes']} ({original_labels})")
        print(f"Chance Baseline: {cv_results['chance_baseline']:.4f}")
        print(f"Mean Accuracy: {cv_results['mean_accuracy']:.4f} (+/- {cv_results['std_accuracy']:.4f})")
        print(f"Deviation from Chance: {cv_results['deviation_from_chance']:.4f}")
        print(f"Fold Scores: {cv_results['fold_scores']}")
        
        # Verification: Check if accuracy > chance
        if cv_results['mean_accuracy'] > cv_results['chance_baseline']:
            print("✓ Accuracy exceeds chance baseline.")
        else:
            print("✗ Accuracy does NOT exceed chance baseline.")
            
    except Exception as e:
        logger.error(f"Task T031 failed: {e}")
        raise

if __name__ == "__main__":
    main()
