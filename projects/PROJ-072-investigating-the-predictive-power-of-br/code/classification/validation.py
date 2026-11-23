import os
import sys
import logging
import numpy as np
import pandas as pd
from scipy import stats
from typing import Optional, Tuple, List
from sklearn.model_selection import StratifiedKFold
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.metrics import accuracy_score
import json

if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent))

from pathlib import Path

logger = logging.getLogger(__name__)

def permuted_t_test(
    group1_values: np.ndarray,
    group2_values: np.ndarray,
    n_permutations: int = 10000,
    random_state: int = 42
) -> float:
    """
    Perform a non-parametric permutation t-test.
    
    Args:
        group1_values: Values for group 1
        group2_values: Values for group 2
        n_permutations: Number of permutations
        random_state: Random seed
        
    Returns:
        float: Two-sided p-value
    """
    np.random.seed(random_state)
    
    # Observed statistic
    observed_diff = np.mean(group1_values) - np.mean(group2_values)
    
    # Combine groups
    combined = np.concatenate([group1_values, group2_values])
    n1 = len(group1_values)
    n_total = len(combined)
    
    # Permutation distribution
    permuted_diffs = []
    for _ in range(n_permutations):
        np.random.shuffle(combined)
        perm_diff = np.mean(combined[:n1]) - np.mean(combined[n1:])
        permuted_diffs.append(perm_diff)
    
    permuted_diffs = np.array(permuted_diffs)
    
    # Calculate p-value (two-sided)
    p_value = np.mean(np.abs(permuted_diffs) >= np.abs(observed_diff))
    
    return float(p_value)

def permutation_accuracy_test(
    X: np.ndarray,
    y: np.ndarray,
    n_permutations: int = 1000,
    random_state: int = 42
) -> float:
    """
    Perform permutation test for classification accuracy.
    
    Args:
        X: Feature matrix
        y: Labels
        n_permutations: Number of permutations
        random_state: Random seed
        
    Returns:
        float: p-value for accuracy significance
    """
    np.random.seed(random_state)
    
    # Build a simple classifier pipeline
    def train_and_score(X_train, y_train, X_test, y_test):
        pipeline = Pipeline([
            ('scaler', StandardScaler()),
            ('clf', LogisticRegression(max_iter=1000, random_state=42, solver='liblinear'))
        ])
        pipeline.fit(X_train, y_train)
        return accuracy_score(y_test, pipeline.predict(X_test))
    
    # Cross-validation setup
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    
    # Observed accuracy (using cross-validation)
    observed_scores = []
    for train_idx, test_idx in cv.split(X, y):
        score = train_and_score(X[train_idx], y[train_idx], X[test_idx], y[test_idx])
        observed_scores.append(score)
    observed_accuracy = np.mean(observed_scores)
    
    logger.info(f"Observed cross-validation accuracy: {observed_accuracy:.4f}")
    
    # Permutation distribution
    permuted_accuracies = []
    n_samples = len(y)
    
    for i in range(n_permutations):
        # Shuffle labels
        y_shuffled = np.random.permutation(y)
        
        # Calculate accuracy with shuffled labels
        shuffled_scores = []
        for train_idx, test_idx in cv.split(X, y_shuffled):
            score = train_and_score(X[train_idx], y_shuffled[train_idx], X[test_idx], y_shuffled[test_idx])
            shuffled_scores.append(score)
        permuted_accuracies.append(np.mean(shuffled_scores))
    
    permuted_accuracies = np.array(permuted_accuracies)
    
    # Calculate p-value (one-sided: is observed accuracy better than chance?)
    p_value = np.mean(permuted_accuracies >= observed_accuracy)
    
    logger.info(f"Permutation test p-value: {p_value:.4f}")
    
    return float(p_value)

def run_validation_pipeline(
    features_path: str,
    status_path: str,
    label_column: str = 'label',
    output_path: Optional[str] = None,
    n_permutations: int = 1000,
    random_state: int = 42
) -> dict:
    """
    Run the full validation pipeline including permutation tests.
    
    Args:
        features_path: Path to features CSV
        status_path: Path to subject status CSV
        label_column: Name of the label column
        output_path: Path to save results
        n_permutations: Number of permutations
        random_state: Random seed
        
    Returns:
        dict: Validation results
    """
    # Load data
    features_df = pd.read_csv(features_path)
    status_df = pd.read_csv(status_path)
    
    # Filter included subjects
    included_subjects = status_df[status_df['status'] == 'included']['subject_id'].tolist()
    
    if 'subject_id' in features_df.columns:
        features_df = features_df[features_df['subject_id'].isin(included_subjects)]
    
    # Extract features and labels
    feature_columns = [col for col in features_df.columns if col != label_column and col != 'subject_id']
    X = features_df[feature_columns].values
    y = features_df[label_column].values
    
    # Run permutation test
    p_value = permutation_accuracy_test(
        X, y,
        n_permutations=n_permutations,
        random_state=random_state
    )
    
    results = {
        'p_value': p_value,
        'n_permutations': n_permutations,
        'n_samples': len(y),
        'significant': p_value < 0.05
    }
    
    if output_path:
        output_dir = Path(output_path).parent
        output_dir.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        logger.info(f"Validation results saved to {output_path}")
    
    return results

def main():
    """Main entry point for validation pipeline."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run validation pipeline')
    parser.add_argument('--features', type=str, required=True, help='Path to features CSV')
    parser.add_argument('--status', type=str, required=True, help='Path to subject status CSV')
    parser.add_argument('--output', type=str, default='data/processed/validation_results.json', help='Output JSON path')
    parser.add_argument('--permutations', type=int, default=1000, help='Number of permutations')
    
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.INFO)
    run_validation_pipeline(
        features_path=args.features,
        status_path=args.status,
        output_path=args.output,
        n_permutations=args.permutations
    )

if __name__ == "__main__":
    main()