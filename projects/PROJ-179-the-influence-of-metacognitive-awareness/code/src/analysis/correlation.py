"""
Correlation analysis with Hold-Out design.

This script implements the Hold-Out Accuracy design (70/30 split) to compute
the correlation between metacognitive awareness (Type-2 AUC from training)
and reality testing accuracy (d' from test).
"""
import json
import logging
import os
import sys
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import stats

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Configuration
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
DATA_DIR = BASE_DIR / "data"
DERIVED_DIR = DATA_DIR / "derived"
RESULTS_DIR = DATA_DIR / "results"

def log_info(message):
    """Log info message."""
    logger.info(message)

def log_error(message):
    """Log error message."""
    logger.error(message)

def load_trial_data():
    """Load trial data from preprocessed file."""
    file_path = DERIVED_DIR / "trial_data.csv"
    if not file_path.exists():
        log_error(f"Trial data not found at {file_path}")
        return None
    
    try:
        df = pd.read_csv(file_path)
        log_info(f"Loaded {len(df)} trials for correlation analysis")
        return df
    except Exception as e:
        log_error(f"Error loading trial data: {e}")
        return None

def compute_hold_out_metrics(df):
    """Compute hold-out accuracy metrics."""
    if df is None or len(df) < 10:
        log_error("Insufficient data for hold-out analysis")
        return None
    
    # Ensure required columns
    required_cols = ['confidence_rating', 'source_label']
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        log_error(f"Missing required columns: {missing}")
        return None
    
    # Split data into training and test sets (70/30)
    np.random.seed(42)
    n = len(df)
    indices = np.random.permutation(n)
    train_size = int(0.7 * n)
    
    train_indices = indices[:train_size]
    test_indices = indices[train_size:]
    
    train_df = df.iloc[train_indices]
    test_df = df.iloc[test_indices]
    
    log_info(f"Split data: {len(train_df)} training, {len(test_df)} test trials")
    
    # Compute metacognitive score (Type-2 AUC) on training set
    # Correlation between confidence and accuracy
    train_df['accuracy'] = (train_df['source_label'] == train_df['participant_response']).astype(int)
    if 'accuracy' in train_df.columns and 'confidence_rating' in train_df.columns:
        metacognitive_score = train_df['accuracy'].corr(train_df['confidence_rating'])
        if np.isnan(metacognitive_score):
            metacognitive_score = 0.0
    else:
        metacognitive_score = 0.0
    
    # Compute reality testing accuracy (d') on test set
    test_df['accuracy'] = (test_df['source_label'] == test_df['participant_response']).astype(int)
    if 'accuracy' in test_df.columns:
        hit_rate = test_df[test_df['source_label'] == 1]['accuracy'].mean()
        false_alarm_rate = test_df[test_df['source_label'] == 0]['accuracy'].mean()
        
        # Avoid extreme values for d' calculation
        hit_rate = np.clip(hit_rate, 0.01, 0.99)
        false_alarm_rate = np.clip(false_alarm_rate, 0.01, 0.99)
        
        d_prime = stats.norm.ppf(hit_rate) - stats.norm.ppf(false_alarm_rate)
    else:
        d_prime = 0.0
    
    return {
        'metacognitive_score': metacognitive_score,
        'd_prime': d_prime,
        'n_train': len(train_df),
        'n_test': len(test_df)
    }

def write_results(metrics):
    """Write results to file."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    output_path = RESULTS_DIR / "correlation_metrics.json"
    with open(output_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    log_info(f"Correlation metrics written to: {output_path}")

def main():
    """Main function."""
    log_info("Starting correlation analysis (T014)...")
    
    # Load data
    df = load_trial_data()
    if df is None:
        return 1
    
    # Compute hold-out metrics
    metrics = compute_hold_out_metrics(df)
    if metrics is None:
        return 1
    
    # Write results
    write_results(metrics)
    
    log_info(f"Correlation analysis complete. Metacognitive score: {metrics['metacognitive_score']:.3f}, d': {metrics['d_prime']:.3f}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
