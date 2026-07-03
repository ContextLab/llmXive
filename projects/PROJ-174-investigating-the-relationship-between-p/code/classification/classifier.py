"""
Sliding-window logistic regression classifier for real-time cognitive load estimation.

Implements a fixed-duration lookback window for feature extraction, updating the classifier
every 200ms. Uses L2 regularization to prevent overfitting.
"""

import os
import sys
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
import argparse
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
UPDATE_INTERVAL_MS = 200  # Update classifier every 200ms
LOOKBACK_WINDOW_SEC = 5.0  # Fixed-duration lookback window for features
L2_REGULARIZATION_C = 1.0  # Inverse of regularization strength

def extract_sliding_window_features(
    df: pd.DataFrame,
    window_size_sec: float,
    sampling_rate_hz: float = 1000.0
) -> List[Dict[str, float]]:
    """
    Extract features from a sliding window of pupil data.

    Args:
        df: DataFrame with 'timestamp' and 'pupil_diameter' columns
        window_size_sec: Size of the lookback window in seconds
        sampling_rate_hz: Assumed sampling rate of the data

    Returns:
        List of feature dictionaries for each valid window
    """
    if 'timestamp' not in df.columns or 'pupil_diameter' not in df.columns:
        raise ValueError("DataFrame must contain 'timestamp' and 'pupil_diameter' columns")

    # Convert timestamps to numeric (seconds since epoch)
    if df['timestamp'].dtype == 'object':
        df = df.copy()
        df['timestamp'] = pd.to_datetime(df['timestamp']).astype(np.int64) // 10**9

    features_list = []
    window_samples = int(window_size_sec * sampling_rate_hz)

    # Iterate through the data with the sliding window
    for i in range(window_samples, len(df)):
        window_data = df.iloc[i - window_samples:i]
        pupil_values = window_data['pupil_diameter'].values

        # Skip windows with too many NaNs (>30%)
        if np.isnan(pupil_values).sum() / len(pupil_values) > 0.3:
            continue

        # Compute features
        features = {
            'timestamp': df.iloc[i]['timestamp'],
            'mean_pupil': np.nanmean(pupil_values),
            'std_pupil': np.nanstd(pupil_values),
            'min_pupil': np.nanmin(pupil_values),
            'max_pupil': np.nanmax(pupil_values),
            'pupil_range': np.nanmax(pupil_values) - np.nanmin(pupil_values),
            'pupil_trend': (pupil_values[-1] - pupil_values[0]) / len(pupil_values) if len(pupil_values) > 1 else 0.0,
            'fixation_count': 0  # Placeholder, would be computed from x,y if available
        }

        # Add derived features
        if 'x' in df.columns and 'y' in df.columns:
            x_vals = df.iloc[i - window_samples:i]['x'].values
            y_vals = df.iloc[i - window_samples:i]['y'].values
            fixation_distance = np.sqrt(np.diff(x_vals)**2 + np.diff(y_vals)**2)
            features['fixation_count'] = np.sum(fixation_distance < 0.1)  # Threshold for fixation
            features['avg_fixation_distance'] = np.mean(fixation_distance)

        features_list.append(features)

    return features_list

def prepare_training_data(
    features_df: pd.DataFrame,
    label_column: str = 'search_time_median_split'
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Prepare data for training the classifier.

    Args:
        features_df: DataFrame with extracted features
        label_column: Name of the column containing ground truth labels

    Returns:
        X_train, X_test, y_train, y_test
    """
    if label_column not in features_df.columns:
        raise ValueError(f"Label column '{label_column}' not found in features DataFrame")

    feature_cols = [col for col in features_df.columns if col not in ['timestamp', label_column]]
    X = features_df[feature_cols].values
    y = features_df[label_column].values

    # Remove rows with NaN in features
    mask = ~np.isnan(X).any(axis=1) & ~np.isnan(y)
    X = X[mask]
    y = y[mask]

    if len(X) == 0:
        raise ValueError("No valid data points after cleaning")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    return X_train, X_test, y_train, y_test

def train_classifier(
    X_train: np.ndarray,
    y_train: np.ndarray
) -> Pipeline:
    """
    Train a logistic regression classifier with L2 regularization.

    Args:
        X_train: Training features
        y_train: Training labels

    Returns:
        Trained Pipeline with StandardScaler and LogisticRegression
    """
    classifier = Pipeline([
        ('scaler', StandardScaler()),
        ('clf', LogisticRegression(
            C=L2_REGULARIZATION_C,
            penalty='l2',
            solver='lbfgs',
            max_iter=1000,
            random_state=42
        ))
    ])

    classifier.fit(X_train, y_train)
    logger.info(f"Classifier trained with accuracy: {classifier.score(X_train, y_train):.3f}")
    return classifier

def update_classifier_periodically(
    data_stream: pd.DataFrame,
    update_interval_ms: int = UPDATE_INTERVAL_MS,
    window_size_sec: float = LOOKBACK_WINDOW_SEC,
    label_column: str = 'search_time_median_split'
) -> Tuple[Pipeline, List[Dict[str, Any]]]:
    """
    Update the classifier every 200ms using the latest data in the stream.

    Args:
        data_stream: DataFrame with continuous data stream
        update_interval_ms: Time between classifier updates in milliseconds
        window_size_sec: Lookback window size for feature extraction
        label_column: Column name for ground truth labels

    Returns:
        Final trained classifier and list of update metadata
    """
    update_interval_sec = update_interval_ms / 1000.0
    last_update_time = time.time()
    updates = []
    current_classifier = None

    # Process data in chunks corresponding to update intervals
    # For simulation, we'll iterate through the data with the specified interval
    data_points_per_update = int(update_interval_sec * 1000)  # Assuming 1000 Hz sampling

    for start_idx in range(0, len(data_stream) - int(LOOKBACK_WINDOW_SEC * 1000), data_points_per_update):
        current_time = time.time()
        elapsed = current_time - last_update_time

        if elapsed >= update_interval_sec:
            # Extract features for the current window
            window_end = start_idx + int(LOOKBACK_WINDOW_SEC * 1000)
            window_data = data_stream.iloc[start_idx:window_end]

            if len(window_data) < int(LOOKBACK_WINDOW_SEC * 1000 * 0.7):  # Skip if not enough data
                continue

            try:
                features_list = extract_sliding_window_features(window_data, window_size_sec)
                if len(features_list) < 10:  # Need minimum data points for training
                    continue

                features_df = pd.DataFrame(features_list)

                if label_column not in features_df.columns:
                    # Create synthetic labels for demonstration if not present
                    # In real usage, this should come from ground truth
                    logger.warning(f"Label column '{label_column}' not found. Using placeholder labels.")
                    median_val = features_df['mean_pupil'].median()
                    features_df[label_column] = (features_df['mean_pupil'] > median_val).astype(int)

                X_train, X_test, y_train, y_test = prepare_training_data(features_df, label_column)
                current_classifier = train_classifier(X_train, y_train)

                # Record update metadata
                update_info = {
                    'timestamp': datetime.now().isoformat(),
                    'window_start_idx': start_idx,
                    'window_end_idx': window_end,
                    'samples_processed': len(window_data),
                    'training_samples': len(X_train),
                    'test_samples': len(X_test),
                    'test_accuracy': float(current_classifier.score(X_test, y_test))
                }
                updates.append(update_info)

                last_update_time = current_time
                logger.info(f"Classifier updated. Test accuracy: {update_info['test_accuracy']:.3f}")

            except Exception as e:
                logger.error(f"Error during classifier update: {e}")
                continue

    return current_classifier, updates

def run_classification_pipeline(
    input_path: str,
    output_path: str,
    label_column: str = 'search_time_median_split'
) -> None:
    """
    Run the full classification pipeline.

    Args:
        input_path: Path to input data file
        output_path: Path to save classification results
    """
    logger.info(f"Loading data from {input_path}")
    data = pd.read_csv(input_path)

    if 'pupil_diameter' not in data.columns:
        raise ValueError("Input data must contain 'pupil_diameter' column")

    # Ensure required columns exist
    if 'timestamp' not in data.columns:
        data['timestamp'] = range(len(data))

    logger.info(f"Running sliding-window classifier with {UPDATE_INTERVAL_MS}ms update interval")
    classifier, updates = update_classifier_periodically(
        data,
        update_interval_ms=UPDATE_INTERVAL_MS,
        window_size_sec=LOOKBACK_WINDOW_SEC,
        label_column=label_column
    )

    if classifier is None:
        raise RuntimeError("Failed to train any classifier")

    # Generate predictions for the entire dataset
    all_features = extract_sliding_window_features(data, LOOKBACK_WINDOW_SEC)
    features_df = pd.DataFrame(all_features)

    if label_column not in features_df.columns:
        median_val = features_df['mean_pupil'].median()
        features_df[label_column] = (features_df['mean_pupil'] > median_val).astype(int)

    feature_cols = [col for col in features_df.columns if col not in ['timestamp', label_column]]
    X = features_df[feature_cols].values
    y_true = features_df[label_column].values

    y_pred = classifier.predict(X)
    y_proba = classifier.predict_proba(X)

    # Create output DataFrame
    output_df = features_df.copy()
    output_df['predicted_class'] = y_pred
    output_df['predicted_probability'] = y_proba[:, 1] if y_proba.shape[1] == 2 else y_proba[:, 0]
    output_df['status'] = 'UNVALIDATED'  # As per T029 requirements

    # Save results
    output_df.to_csv(output_path, index=False)
    logger.info(f"Classification results saved to {output_path}")

    # Save update metadata
    updates_path = output_path.replace('.csv', '_updates.json')
    import json
    with open(updates_path, 'w') as f:
        json.dump(updates, f, indent=2)
    logger.info(f"Classifier update metadata saved to {updates_path}")

def main():
    parser = argparse.ArgumentParser(description='Sliding-window logistic regression classifier')
    parser.add_argument('--input', type=str, required=True, help='Input data file path')
    parser.add_argument('--output', type=str, required=True, help='Output results file path')
    parser.add_argument('--label-column', type=str, default='search_time_median_split',
                        help='Column name for ground truth labels')

    args = parser.parse_args()

    try:
        run_classification_pipeline(args.input, args.output, args.label_column)
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
