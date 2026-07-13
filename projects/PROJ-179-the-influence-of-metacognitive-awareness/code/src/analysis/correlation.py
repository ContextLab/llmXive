import os
import sys
import json
import logging
import numpy as np
import pandas as pd
from pathlib import Path

# Ensure project root is in path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config.env_config import load_config, setup_logging
from src.utils.stats import compute_type2_auc, compute_sdt_metrics

CONFIG = load_config()
BASE_DIR = Path(CONFIG.get("paths", {}).get("base", "projects/PROJ-179-the-influence-of-metacognitive-awareness"))
DATA_DIR = BASE_DIR / "data"
DERIVED_DIR = DATA_DIR / "derived"
RESULTS_DIR = DATA_DIR / "results"

INPUT_FILE = DERIVED_DIR / "trial_data.csv"
OUTPUT_FILE = RESULTS_DIR / "correlation_results.json"

def log_info(msg):
    logging.info(msg)

def log_error(msg):
    logging.error(msg)

def load_trial_data():
    """Load trial data from CSV."""
    if not INPUT_FILE.exists():
        log_error(f"Trial data not found: {INPUT_FILE}. Run preprocessing first.")
        sys.exit(1)
    return pd.read_csv(INPUT_FILE)

def compute_hold_out_metrics(df):
    """
    Implement Hold-Out Accuracy design:
    1. Split trials 70/30 (Train/Test)
    2. Compute Type-2 AUC (Metacognitive Score) on TRAIN
    3. Compute d' (Reality Testing Accuracy) on TEST
    """
    log_info("Computing hold-out metrics...")
    
    # Ensure random seed for reproducibility
    seed = CONFIG.get("analysis", {}).get("random_seed", 42)
    np.random.seed(seed)
    
    # Split data
    train_df, test_df = np.split(df.sample(frac=1, random_state=seed), [int(len(df)*0.7)])
    
    log_info(f"Train size: {len(train_df)}, Test size: {len(test_df)}")
    
    # Compute Metacognitive Score (Type-2 AUC) on Training set
    # Assuming 'participant_response' is correct/incorrect (1/0) and 'confidence_rating' is the confidence
    train_accuracy = (train_df['participant_response'] == train_df['source_label']).astype(int)
    meta_score = compute_type2_auc(train_accuracy.values, train_df['confidence_rating'].values)
    
    # Compute Reality Testing Accuracy (d') on Test set
    test_accuracy = (test_df['participant_response'] == test_df['source_label']).astype(int)
    # d' calculation requires hits and false alarms. 
    # For simplicity in this pipeline, we compute d' based on binary accuracy if modality is not specified,
    # or assume a standard signal detection setup.
    # Here we assume a simplified d' calculation based on proportion correct if binary,
    # or use a helper that handles the specifics.
    # Since we don't have explicit 'signal' vs 'noise' labels per trial in the simplified schema,
    # we will compute a group-level d' based on the test set's hit/FA rates if we had them.
    # Given the schema, we'll compute d' as a proxy using the accuracy distribution.
    # A robust implementation would require more detailed trial labels.
    # For this task, we compute d' using the standard formula if we can infer hits/FA.
    # Assuming 'source_label' indicates the true state (e.g., 1=Signal, 0=Noise)
    # and 'participant_response' is the decision.
    
    # Calculate hits and false alarms
    # Hit: Response=1 when Source=1
    # FA: Response=1 when Source=0
    hits = ((test_df['participant_response'] == 1) & (test_df['source_label'] == 1)).sum()
    total_signal = (test_df['source_label'] == 1).sum()
    false_alarms = ((test_df['participant_response'] == 1) & (test_df['source_label'] == 0)).sum()
    total_noise = (test_df['source_label'] == 0).sum()
    
    if total_signal == 0 or total_noise == 0:
        log_error("Cannot compute d': missing signal or noise trials in test set.")
        sys.exit(1)
        
    hit_rate = hits / total_signal
    fa_rate = false_alarms / total_noise
    
    # Adjust rates to avoid 0 or 1
    hit_rate = np.clip(hit_rate, 0.001, 0.999)
    fa_rate = np.clip(fa_rate, 0.001, 0.999)
    
    from scipy.stats import norm
    d_prime = norm.ppf(hit_rate) - norm.ppf(fa_rate)
    
    return {
        "meta_score": meta_score,
        "d_prime": d_prime,
        "train_size": len(train_df),
        "test_size": len(test_df)
    }

def write_results(results):
    """Write results to JSON."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(results, f, indent=2)
    log_info(f"Results written to {OUTPUT_FILE}")

def main():
    log_info("Starting correlation analysis (T014)...")
    
    df = load_trial_data()
    results = compute_hold_out_metrics(df)
    write_results(results)
    
    log_info("Correlation analysis (T014) completed successfully.")

if __name__ == "__main__":
    logger = setup_logging("info")
    main()
