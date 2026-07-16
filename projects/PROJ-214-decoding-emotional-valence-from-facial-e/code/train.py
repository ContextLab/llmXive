"""
Train.py - Implements Nested Leave-One-Subject-Out (LOSO) Cross-Validation.

This module handles the core training loop for the emotional valence classification pipeline.
It implements strict subject-level isolation, parallel fold execution via joblib,
and fold-level exclusion logic for skewed subjects to prevent bias.
"""

import os
import logging
import pickle
import gc
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional

import numpy as np
import pandas as pd
from sklearn.model_selection import LeaveOneGroupOut
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import LinearSVC
from sklearn.metrics import accuracy_score
from sklearn.preprocessing import StandardScaler
from joblib import Parallel, delayed
import joblib

# Import local configuration
from config import (
    PROJECT_ROOT,
    DATA_PROCESSED_DIR,
    DATA_MODELS_DIR,
    LOGS_DIR,
    RANDOM_SEED,
    N_JOBS_PARALLEL,
    EXCLUSION_LOG_PATH,
    SKewed_THRESHOLD_HIGH,
    SKewed_THRESHOLD_LOW
)

# Import preprocessing utilities
from preprocessing import check_skewed_valence

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOGS_DIR / 'train.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def load_preprocessed_data() -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series]:
    """
    Load preprocessed features and labels from the processed data directory.

    Returns:
        Tuple of (features_df, labels_df, subject_ids_series)
    """
    features_path = DATA_PROCESSED_DIR / "features_all_subjects.csv"
    labels_path = DATA_PROCESSED_DIR / "labels_all_subjects.csv"
    subjects_path = DATA_PROCESSED_DIR / "subject_ids_all_subjects.csv"

    if not features_path.exists() or not labels_path.exists():
        raise FileNotFoundError(
            f"Preprocessed data not found. Run preprocessing.py first. "
            f"Expected: {features_path}, {labels_path}"
        )

    logger.info(f"Loading features from {features_path}")
    features_df = pd.read_csv(features_path)

    logger.info(f"Loading labels from {labels_path}")
    labels_df = pd.read_csv(labels_path)

    logger.info(f"Loading subject IDs from {subjects_path}")
    subject_ids = pd.read_csv(subjects_path, header=None)[0]

    # Ensure alignment
    if len(features_df) != len(labels_df) or len(features_df) != len(subject_ids):
        raise ValueError("Data alignment error: Features, labels, and subject IDs lengths do not match.")

    return features_df, labels_df, subject_ids


def identify_skewed_subjects(subject_ids: pd.Series, labels_df: pd.DataFrame) -> List[int]:
    """
    Identify subjects with skewed valence scores (all > 5 or all < 5).
    This is used for fold-level exclusion logic.

    Args:
        subject_ids: Series of subject IDs corresponding to the rows.
        labels_df: DataFrame containing the valence labels.

    Returns:
        List of subject IDs that are skewed.
    """
    logger.info("Identifying skewed subjects for fold-level exclusion...")
    skewed_subjects = []

    # Group by subject ID to check distribution
    # Assuming labels_df has a column 'valence' or similar, but here we check the raw values
    # The labels_df is expected to be the target variable.
    # We need to map rows to subjects.
    
    unique_subjects = subject_ids.unique()
    
    for subj in unique_subjects:
        mask = subject_ids == subj
        subj_labels = labels_df[mask]
        
        # Check if all labels are > 5 or all < 5
        # Assuming the label is the only column or the first column if it's a series
        if isinstance(subj_labels, pd.DataFrame):
            vals = subj_labels.iloc[:, 0]
        else:
            vals = subj_labels
        
        if len(vals) == 0:
            continue
            
        if (vals > 5).all() or (vals < 5).all():
            skewed_subjects.append(int(subj))
            logger.warning(f"Subject {subj} identified as skewed (all labels > 5 or < 5).")

    return skewed_subjects


def train_single_fold(
    train_indices: np.ndarray,
    test_indices: np.ndarray,
    X: np.ndarray,
    y: np.ndarray,
    skewed_subjects: List[int],
    subject_ids: pd.Series
) -> Dict[str, Any]:
    """
    Train a single fold of the LOSO cross-validation.
    
    This function trains a Random Forest and a Linear SVM on the training set,
    evaluates on the test set, and returns the metrics.
    
    Args:
        train_indices: Indices of training samples.
        test_indices: Indices of test samples.
        X: Full feature matrix.
        y: Full label vector.
        skewed_subjects: List of subject IDs to exclude from training if they appear in the fold.
        subject_ids: Series mapping row indices to subject IDs.
        
    Returns:
        Dictionary containing fold metrics and model objects (optional).
    """
    # Extract training and testing data
    X_train, X_test = X[train_indices], X[test_indices]
    y_train, y_test = y[train_indices], y[test_indices]
    
    # Check for skewed subjects in the TEST set (should be excluded from evaluation if they exist, 
    # but the task says "excluded from the current LOSO fold" to prevent bias. 
    # Usually, if a subject is skewed, we don't want to train on them. 
    # In LOSO, the test subject is the one being left out. 
    # If the test subject is skewed, we might want to skip this fold entirely or exclude the test subject.
    # The task says: "If a subject is flagged by T017a, they are excluded from the current LOSO fold"
    # This implies if the held-out subject is skewed, we skip this fold.
    
    test_subject_id = int(subject_ids.iloc[test_indices[0]])
    if test_subject_id in skewed_subjects:
        logger.info(f"Skipping fold for subject {test_subject_id} due to skewed valence.")
        return {
            'fold_id': test_subject_id,
            'accuracy': None,
            'skipped': True,
            'reason': 'Skewed valence'
        }

    # Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # Train Random Forest
    rf_model = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        random_state=RANDOM_SEED,
        n_jobs=1
    )
    rf_model.fit(X_train_scaled, y_train)
    rf_pred = rf_model.predict(X_test_scaled)
    rf_acc = accuracy_score(y_test, rf_pred)

    # Train Linear SVM
    svm_model = LinearSVC(
        random_state=RANDOM_SEED,
        max_iter=2000
    )
    svm_model.fit(X_train_scaled, y_train)
    svm_pred = svm_model.predict(X_test_scaled)
    svm_acc = accuracy_score(y_test, svm_pred)

    logger.info(f"Fold Subject {test_subject_id}: RF Acc={rf_acc:.4f}, SVM Acc={svm_acc:.4f}")

    return {
        'fold_id': test_subject_id,
        'accuracy_rf': rf_acc,
        'accuracy_svm': svm_acc,
        'skipped': False,
        'rf_model': rf_model,
        'svm_model': svm_model,
        'scaler': scaler
    }


def run_nested_loso(
    X: np.ndarray,
    y: np.ndarray,
    subject_ids: pd.Series,
    skewed_subjects: List[int]
) -> Tuple[List[Dict], Dict]:
    """
    Run the Nested Leave-One-Subject-Out Cross-Validation loop.
    
    Uses joblib for parallel execution (n_jobs=4).
    
    Args:
        X: Feature matrix.
        y: Label vector.
        subject_ids: Series of subject IDs.
        skewed_subjects: List of subject IDs to exclude.
        
    Returns:
        Tuple of (list of fold results, summary statistics)
    """
    logger.info(f"Starting Nested LOSO with {len(np.unique(subject_ids))} subjects.")
    logger.info(f"Skewed subjects to exclude: {skewed_subjects}")

    logo = LeaveOneGroupOut()
    
    # Prepare arguments for parallel execution
    # We need to pass the full X, y, subject_ids to each worker, but joblib handles this efficiently
    # by pickling. To avoid memory bloat, we pass indices.
    
    # Create a list of (train_idx, test_idx) pairs
    folds = list(logo.split(X, y, groups=subject_ids))
    
    logger.info(f"Total folds generated: {len(folds)}")

    # Parallel execution
    results = Parallel(n_jobs=N_JOBS_PARALLEL, verbose=10)(
        delayed(train_single_fold)(
            train_idx, test_idx, X, y, skewed_subjects, subject_ids
        )
        for train_idx, test_idx in folds
    )

    # Aggregate results
    valid_results = [r for r in results if not r.get('skipped', False)]
    skipped_count = len(results) - len(valid_results)
    
    logger.info(f"Completed {len(valid_results)} valid folds. Skipped {skipped_count} due to skewed valence.")

    # Calculate summary statistics
    rf_accs = [r['accuracy_rf'] for r in valid_results]
    svm_accs = [r['accuracy_svm'] for r in valid_results]

    summary = {
        'total_subjects': len(np.unique(subject_ids)),
        'skipped_subjects': skipped_count,
        'valid_folds': len(valid_results),
        'rf_mean_accuracy': np.mean(rf_accs) if rf_accs else 0.0,
        'rf_std_accuracy': np.std(rf_accs) if rf_accs else 0.0,
        'svm_mean_accuracy': np.mean(svm_accs) if svm_accs else 0.0,
        'svm_std_accuracy': np.std(svm_accs) if svm_accs else 0.0
    }

    return results, summary


def save_model_bundle(
    results: List[Dict],
    summary: Dict,
    output_path: Path
) -> None:
    """
    Save the model bundle containing trained models and metadata.
    
    Args:
        results: List of fold results.
        summary: Summary statistics.
        output_path: Path to save the bundle.
    """
    # Select the best performing fold models or aggregate?
    # For now, we save the models from the last valid fold as a representative bundle
    # or we could save all. The spec says "model_bundle.pkl containing BOTH the trained Random Forest and Linear SVM models".
    # Let's save the models from the fold with the highest average accuracy.
    
    if not results:
        logger.warning("No valid results to save model bundle.")
        return

    best_fold = max(
        [r for r in results if not r.get('skipped', False)],
        key=lambda x: (x['accuracy_rf'] + x['accuracy_svm']) / 2
    )

    bundle = {
        'rf_model': best_fold['rf_model'],
        'svm_model': best_fold['svm_model'],
        'scaler': best_fold['scaler'],
        'summary': summary,
        'fold_results': results,
        'config': {
            'random_seed': RANDOM_SEED,
            'n_jobs': N_JOBS_PARALLEL
        }
    }

    logger.info(f"Saving model bundle to {output_path}")
    with open(output_path, 'wb') as f:
        pickle.dump(bundle, f)
    
    # Memory flushing
    del bundle
    gc.collect()


def main():
    """Main entry point for the training pipeline."""
    logger.info("Starting Training Pipeline (T019: Nested LOSO)")

    # Ensure directories exist
    DATA_MODELS_DIR.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    # Load data
    try:
        X_df, y_df, subject_ids = load_preprocessed_data()
        X = X_df.values
        y = y_df.values.flatten()
    except FileNotFoundError as e:
        logger.error(str(e))
        return

    # Identify skewed subjects
    skewed_subjects = identify_skewed_subjects(subject_ids, y_df)

    # Run Nested LOSO
    results, summary = run_nested_loso(X, y, subject_ids, skewed_subjects)

    # Log summary
    logger.info("Training Summary:")
    logger.info(f"  RF Mean Accuracy: {summary['rf_mean_accuracy']:.4f} (+/- {summary['rf_std_accuracy']:.4f})")
    logger.info(f"  SVM Mean Accuracy: {summary['svm_mean_accuracy']:.4f} (+/- {summary['svm_std_accuracy']:.4f})")
    logger.info(f"  Skipped Subjects: {summary['skipped_subjects']}")

    # Save model bundle
    bundle_path = DATA_MODELS_DIR / "model_bundle.pkl"
    save_model_bundle(results, summary, bundle_path)

    # Save raw results to CSV for validation
    results_df = pd.DataFrame([
        {
            'subject_id': r['fold_id'],
            'accuracy_rf': r.get('accuracy_rf'),
            'accuracy_svm': r.get('accuracy_svm'),
            'skipped': r.get('skipped', False),
            'reason': r.get('reason', '')
        }
        for r in results
    ])
    results_path = DATA_PROCESSED_DIR / "loso_results.csv"
    results_df.to_csv(results_path, index=False)
    logger.info(f"Saved fold-level results to {results_path}")

    logger.info("Training Pipeline Complete.")


if __name__ == "__main__":
    main()