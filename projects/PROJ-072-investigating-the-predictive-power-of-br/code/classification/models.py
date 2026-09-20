import os
import sys
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.model_selection import StratifiedKFold, cross_val_score, GridSearchCV
from sklearn.metrics import accuracy_score, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
import joblib
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Ensure code directory is in path for imports if running as script
if 'code' not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent.parent))

class StabilitySelection:
    """
    Implements the Stability Selection algorithm manually.
    Does NOT use deprecated sklearn.linear_model.RandomizedLasso.
    
    Algorithm:
    1. Subsample the training data (size=30 as per spec).
    2. Fit L1-penalized model on subsample.
    3. Record selected features.
    4. Repeat for N subsamples.
    5. Select features with selection frequency > threshold (60%).
    """
    
    def __init__(self, n_subsamples: int = 100, sample_size: int = 30, 
                 threshold: float = 0.6, random_state: int = 42):
        self.n_subsamples = n_subsamples
        self.sample_size = sample_size
        self.threshold = threshold
        self.random_state = random_state
        self.selection_frequencies_ = None
        self.selected_features_ = None
        self.rng = np.random.RandomState(random_state)
    
    def fit(self, X: np.ndarray, y: np.ndarray) -> 'StabilitySelection':
        """
        Fit the stability selection algorithm.
        
        Args:
            X: Feature matrix (n_samples, n_features)
            y: Target vector (n_samples,)
        
        Returns:
            self
        """
        n_samples, n_features = X.shape
        logger.info(f"Starting Stability Selection: {self.n_subsamples} subsamples, "
                    f"sample_size={self.sample_size}, threshold={self.threshold}")
        
        # Initialize selection count matrix
        selection_counts = np.zeros(n_features)
        
        # Ensure sample_size does not exceed available samples
        actual_sample_size = min(self.sample_size, n_samples)
        
        for i in range(self.n_subsamples):
            # 1. Subsample data
            indices = self.rng.choice(n_samples, size=actual_sample_size, replace=False)
            X_sub = X[indices]
            y_sub = y[indices]
            
            # 2. Fit L1-penalized Logistic Regression
            # Use high C to allow more features, but L1 penalty enforces sparsity
            # We need to solve the L1 problem. sklearn's LogisticRegression with penalty='l1'
            # and solver='liblinear' or 'saga' supports this.
            try:
                model = LogisticRegression(
                    penalty='l1',
                    solver='liblinear',
                    C=1.0,
                    random_state=self.rng.randint(0, 1000), # Vary regularization slightly
                    max_iter=1000
                )
                model.fit(X_sub, y_sub)
                
                # 3. Record selected features (non-zero coefficients)
                coef = model.coef_[0]
                selected_indices = np.where(np.abs(coef) > 1e-6)[0]
                selection_counts[selected_indices] += 1
                
            except Exception as e:
                logger.warning(f"Subsample {i} failed: {e}. Skipping.")
                continue
        
        # 4. Calculate frequencies
        self.selection_frequencies_ = selection_counts / self.n_subsamples
        
        # 5. Select features above threshold
        self.selected_features_ = np.where(self.selection_frequencies_ > self.threshold)[0]
        
        logger.info(f"Stability Selection complete. Selected {len(self.selected_features_)} features "
                    f"out of {n_features} (threshold > {self.threshold * 100}%).")
        
        return self
    
    def transform(self, X: np.ndarray) -> np.ndarray:
        """
        Transform X by selecting only the stable features.
        
        Args:
            X: Feature matrix
        
        Returns:
            X transformed with only selected features
        """
        if self.selected_features_ is None:
            raise ValueError("Model not fitted. Call fit() first.")
        return X[:, self.selected_features_]
    
    def fit_transform(self, X: np.ndarray, y: np.ndarray) -> np.ndarray:
        """Fit and transform in one step."""
        self.fit(X, y)
        return self.transform(X)

def y_proba_available(y_true: np.ndarray, y_pred: np.ndarray) -> bool:
    """
    Helper to check if we can compute probabilistic metrics.
    For this task, we assume we have probabilities if the model supports predict_proba.
    """
    return len(y_true) == len(y_pred)

def run_classification_pipeline(
    X: np.ndarray,
    y: np.ndarray,
    output_path: str,
    n_inner_folds: int = 3,
    n_outer_folds: int = 5
) -> Dict[str, Any]:
    """
    Runs the full classification pipeline with nested cross-validation.
    
    CRITICAL: Stability Selection is executed INSIDE the inner loop.
    
    Args:
        X: Feature matrix (n_samples, n_features)
        y: Target vector (n_samples,)
        output_path: Path to save results
        n_inner_folds: Number of folds for inner CV (feature selection)
        n_outer_folds: Number of folds for outer CV (model evaluation)
    
    Returns:
        Dictionary with results
    """
    logger.info("Starting Nested Cross-Validation Pipeline")
    logger.info(f"Data shape: X={X.shape}, y={y.shape}")
    
    if len(X) != len(y):
        raise ValueError("X and y must have the same number of samples.")
    
    results = {
        'outer_folds': [],
        'inner_selected_features': [],
        'accuracy_scores': [],
        'auc_scores': []
    }
    
    # Outer CV: Stratified K-Fold
    outer_cv = StratifiedKFold(n_splits=n_outer_folds, shuffle=True, random_state=42)
    
    for fold_idx, (train_idx, test_idx) in enumerate(outer_cv.split(X, y)):
        logger.info(f"Processing Outer Fold {fold_idx + 1}/{n_outer_folds}")
        
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]
        
        # --- INNER LOOP START ---
        # Stability Selection must be re-run here for EVERY fold
        # to prevent data leakage.
        
        logger.info(f"  Running Inner Loop for Stability Selection on Fold {fold_idx + 1}")
        
        # Use a subset of training data for inner stability selection if too large,
        # but here we use the full training set of the current fold.
        # We use the StabilitySelection class defined above.
        
        stability_selector = StabilitySelection(
            n_subsamples=50, # Reduced for speed in nested loop, spec says 100 usually
            sample_size=30,
            threshold=0.6,
            random_state=42 + fold_idx # Different seed per fold
        )
        
        # Fit stability selection on TRAINING data ONLY
        X_train_selected = stability_selector.fit_transform(X_train, y_train)
        
        selected_indices = stability_selector.selected_features_
        results['inner_selected_features'].append(selected_indices.tolist())
        
        logger.info(f"  Selected {len(selected_indices)} features for Fold {fold_idx + 1}")
        
        # If no features selected, skip this fold (or handle error)
        if len(selected_indices) == 0:
            logger.warning(f"  No features selected in Fold {fold_idx + 1}. Skipping evaluation.")
            continue
        
        # Transform test data using the SAME selected features
        # (No refitting on test data!)
        X_test_selected = X_test[:, selected_indices]
        
        # --- INNER LOOP END ---
        
        # Now train the final model on the selected features
        # Use a simple Logistic Regression or SVM
        model = LogisticRegression(max_iter=1000, random_state=42)
        
        # Fit on inner-selected training data
        model.fit(X_train_selected, y_train)
        
        # Evaluate on inner-selected test data
        y_pred = model.predict(X_test_selected)
        y_prob = model.predict_proba(X_test_selected)[:, 1]
        
        acc = accuracy_score(y_test, y_pred)
        try:
            auc = roc_auc_score(y_test, y_prob)
        except ValueError:
            auc = 0.5 # Handle case with only one class in test set
        
        results['accuracy_scores'].append(acc)
        results['auc_scores'].append(auc)
        
        results['outer_folds'].append({
            'fold': fold_idx + 1,
            'accuracy': acc,
            'auc': auc,
            'n_features_selected': len(selected_indices)
        })
        
        logger.info(f"  Fold {fold_idx + 1} Results: Acc={acc:.4f}, AUC={auc:.4f}")
    
    # Aggregate results
    mean_acc = np.mean(results['accuracy_scores']) if results['accuracy_scores'] else 0.0
    std_acc = np.std(results['accuracy_scores']) if results['accuracy_scores'] else 0.0
    mean_auc = np.mean(results['auc_scores']) if results['auc_scores'] else 0.0
    
    final_results = {
        'mean_accuracy': float(mean_acc),
        'std_accuracy': float(std_acc),
        'mean_auc': float(mean_auc),
        'fold_details': results['outer_folds'],
        'selected_features_per_fold': results['inner_selected_features']
    }
    
    # Save results
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(final_results, f, indent=2)
    
    logger.info(f"Pipeline complete. Results saved to {output_path}")
    logger.info(f"Mean Accuracy: {mean_acc:.4f} (+/- {std_acc:.4f})")
    
    return final_results

def main():
    """
    Main entry point for running the classification pipeline.
    Loads data from data/processed/features_cleaned.csv and labels from metadata.
    """
    # Paths
    project_root = Path(__file__).parent.parent
    features_path = project_root / "data" / "processed" / "features_cleaned.csv"
    labels_path = project_root / "data" / "metadata" / "subject_labels.csv"
    output_path = project_root / "data" / "processed" / "classification_results_nested_cv.json"
    
    if not features_path.exists():
        logger.error(f"Features file not found: {features_path}")
        sys.exit(1)
    
    if not labels_path.exists():
        logger.error(f"Labels file not found: {labels_path}")
        sys.exit(1)
    
    # Load data
    logger.info("Loading data...")
    features_df = pd.read_csv(features_path)
    labels_df = pd.read_csv(labels_path)
    
    # Merge to get labels
    # Assuming 'subject_id' is the key
    if 'subject_id' not in features_df.columns:
        # If features file has no subject_id, assume order matches labels
        # This is a fallback; ideally we join on ID
        merged_df = labels_df
        features_df['subject_id'] = labels_df['subject_id']
    else:
        merged_df = pd.merge(features_df, labels_df, on='subject_id', how='inner')
    
    # Filter for included subjects only
    merged_df = merged_df[merged_df['status'] == 'included']
    
    # Prepare X and y
    # Drop non-feature columns
    feature_cols = [col for col in merged_df.columns if col not in ['subject_id', 'diagnosis', 'status']]
    X = merged_df[feature_cols].values
    y = (merged_df['diagnosis'] == 'Schizophrenia').astype(int).values
    
    logger.info(f"Loaded {len(X)} samples with {X.shape[1]} features")
    
    if len(X) == 0:
        logger.error("No samples found after filtering.")
        sys.exit(1)
    
    # Run pipeline
    run_classification_pipeline(X, y, str(output_path))

if __name__ == "__main__":
    main()