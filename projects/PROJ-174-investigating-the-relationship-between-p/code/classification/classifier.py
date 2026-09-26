import os
import sys
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Tuple
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import time

from config import load_config
from preprocessing.features import extract_features

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def extract_sliding_window_features(
    pupil_data: pd.DataFrame,
    window_size: int = 2000,  # 2000ms window (assuming 1000Hz sampling)
    step_size: int = 200     # Update every 200ms
) -> pd.DataFrame:
    """
    Extract features from sliding windows of pupil data.

    Args:
        pupil_data: DataFrame with timestamp and pupil diameter
        window_size: Window size in milliseconds
        step_size: Step size between windows in milliseconds

    Returns:
        DataFrame with window features
    """
    # Ensure data is sorted by timestamp
    pupil_data = pupil_data.sort_values('timestamp')

    features = []
    window_ms = window_size
    step_ms = step_size

    timestamps = pupil_data['timestamp'].values
    pupil = pupil_data['pupil_diameter'].values

    # Convert to indices (assuming 1ms resolution for simplicity, adjust if needed)
    # In real data, convert ms to sample indices based on sampling rate
    # For this implementation, we assume 1 sample = 1ms for simplicity

    for i in range(0, len(timestamps) - window_ms, step_ms):
        window_data = pupil[i:i+window_ms]
        if len(window_data) < window_ms // 2:
            continue

        # Compute features
        feat = {
            'window_start_idx': i,
            'mean_pupil': np.mean(window_data),
            'std_pupil': np.std(window_data),
            'max_pupil': np.max(window_data),
            'min_pupil': np.min(window_data),
            'slope': np.polyfit(range(len(window_data)), window_data, 1)[0] if len(window_data) > 1 else 0
        }
        features.append(feat)

    return pd.DataFrame(features)

def prepare_training_data(
    features_df: pd.DataFrame,
    labels: pd.Series,
    test_size: float = 0.2
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    """
    Prepare training and test data for classification.

    Args:
        features_df: DataFrame of features
        labels: Series of labels (low/high cognitive load)
        test_size: Fraction of data to use for testing

    Returns:
        Tuple of (X_train, X_test, y_train, y_test)
    """
    X = features_df.drop(columns=['window_start_idx'], errors='ignore')
    y = labels

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=42, stratify=y
    )

    return X_train, X_test, y_train, y_test

def train_classifier(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    l2_regularization: float = 1.0
) -> Tuple[LogisticRegression, StandardScaler]:
    """
    Train a logistic regression classifier with L2 regularization.

    Args:
        X_train: Training features
        y_train: Training labels
        l2_regularization: Inverse of regularization strength (C parameter)

    Returns:
        Tuple of (trained model, scaler)
    """
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)

    model = LogisticRegression(
        C=l2_regularization,
        solver='lbfgs',
        max_iter=1000,
        random_state=42
    )
    model.fit(X_train_scaled, y_train)

    return model, scaler

def update_classifier_periodically(
    model: LogisticRegression,
    scaler: StandardScaler,
    new_features: pd.DataFrame,
    new_labels: pd.Series,
    update_interval_ms: int = 200
) -> Tuple[LogisticRegression, StandardScaler]:
    """
    Update the classifier periodically with new data.

    Args:
        model: Current model
        scaler: Current scaler
        new_features: New feature data
        new_labels: New labels
        update_interval_ms: Interval for updates (not used for batch update here)

    Returns:
        Tuple of (updated model, updated scaler)
    """
    # In a real-time system, we would use partial_fit
    # Here we retrain on accumulated data for simplicity
    X_new = new_features.drop(columns=['window_start_idx'], errors='ignore')
    y_new = new_labels

    # Combine old and new data (simulated)
    # In practice, we would maintain a buffer of recent data
    X_combined = X_new
    y_combined = y_new

    X_scaled = scaler.transform(X_combined)
    model.fit(X_scaled, y_combined)

    return model, scaler

def run_classification_pipeline(
    pupil_data_path: Path,
    search_time_path: Path,
    output_path: Path,
    config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Run the full classification pipeline.

    Args:
        pupil_data_path: Path to preprocessed pupil data
        search_time_path: Path to search time data for labeling
        output_path: Path to save classification results
        config: Configuration dictionary

    Returns:
        Dictionary with pipeline results
    """
    logger.info("Starting classification pipeline")

    # Load data
    pupil_df = pd.read_csv(pupil_data_path)
    search_time_df = pd.read_csv(search_time_path)

    # Extract features
    features_df = extract_sliding_window_features(pupil_df)

    # Label data (using median split of search time)
    # Merge search time with features
    # Note: In a real scenario, we'd need to align timestamps properly
    # For this implementation, we assume a direct mapping or use trial-level aggregation

    # Simple aggregation: assign search time to each window based on nearest trial
    # This is a placeholder logic; real implementation needs precise temporal alignment
    if 'trial_id' in search_time_df.columns and 'trial_id' in pupil_df.columns:
        merged = pd.merge(
            features_df,
            search_time_df[['trial_id', 'search_time']],
            on='trial_id',
            how='left'
        )
    else:
        # Fallback: use median search time for all
        median_time = search_time_df['search_time'].median()
        merged = features_df.copy()
        merged['search_time'] = median_time

    # Create labels (1 = high load, 0 = low load)
    median_search_time = merged['search_time'].median()
    merged['label'] = (merged['search_time'] > median_search_time).astype(int)

    # Prepare training data
    X_train, X_test, y_train, y_test = prepare_training_data(merged, merged['label'])

    # Train classifier
    model, scaler = train_classifier(X_train, y_train)

    # Predict on test set
    X_test_scaled = scaler.transform(X_test)
    y_pred = model.predict(X_test_scaled)
    y_prob = model.predict_proba(X_test_scaled)[:, 1]

    # Create output dataframe
    output_df = pd.DataFrame({
        'window_start_idx': X_test['window_start_idx'] if 'window_start_idx' in X_test.columns else range(len(y_pred)),
        'predicted_probability': y_prob,
        'true_label': y_test.values,
        'predicted_label': y_pred
    })

    # Save results
    if not output_path.parent.exists():
        output_path.parent.mkdir(parents=True, exist_ok=True)
    output_df.to_csv(output_path, index=False)

    logger.info(f"Classification results saved to {output_path}")

    return {
        'n_samples': len(y_test),
        'accuracy': np.mean(y_pred == y_test.values),
        'output_path': str(output_path)
    }

def main():
    """CLI entry point for classification pipeline."""
    import argparse
    parser = argparse.ArgumentParser(description="Run sliding-window logistic regression classification")
    parser.add_argument("--pupil-data", type=str, required=True, help="Path to pupil data CSV")
    parser.add_argument("--search-time", type=str, required=True, help="Path to search time CSV")
    parser.add_argument("--output", type=str, default="results/classification_results.csv", help="Output path")
    parser.add_argument("--config", type=str, default="code/config.yaml", help="Config path")
    args = parser.parse_args()

    config = load_config(args.config) if os.path.exists(args.config) else None
    run_classification_pipeline(
        Path(args.pupil_data),
        Path(args.search_time),
        Path(args.output),
        config
    )

if __name__ == "__main__":
    main()
