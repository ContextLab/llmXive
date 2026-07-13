"""
T014: Implement Hold-Out Accuracy design for correlation analysis.

Computes metacognitive awareness (Type-2 AUC) on training split
and reality testing accuracy (d') on held-out test split.
"""
import os
import sys
import json
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.model_selection import train_test_split
from scipy.stats import pearsonr

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config.env_config import load_config, setup_logging
from src.utils.stats import compute_sdt_metrics, compute_type2_auc

def log_info(logger, msg):
    if logger:
        logger.info(msg)
    else:
        print(f"[INFO] {msg}")

def log_error(logger, msg):
    if logger:
        logger.error(msg)
    else:
        print(f"[ERROR] {msg}")

def load_trial_data():
    """Load preprocessed trial data."""
    trial_data_path = Path("data") / "derived" / "trial_data.csv"
    if not trial_data_path.exists():
        raise FileNotFoundError(f"Trial data not found at {trial_data_path}. Run T012 first.")
    
    return pd.read_csv(trial_data_path)

def compute_hold_out_metrics(df, train_ratio=0.7):
    """
    Compute metrics using Hold-Out design.
    
    1. Split trials into training (70%) and test (30%) sets
    2. Compute Type-2 AUC (metacognitive score) on training set
    3. Compute d' (reality testing accuracy) on test set
    4. Return correlation between participant-level metrics
    """
    log_info(None, "Computing hold-out metrics...")
    
    # Ensure required columns exist
    required_cols = ['participant_id', 'source_label', 'participant_response', 'confidence_rating']
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    
    # Group by participant
    participants = df['participant_id'].unique()
    participant_metrics = []
    
    for participant_id in participants:
        participant_data = df[df['participant_id'] == participant_id].copy()
        
        if len(participant_data) < 10:  # Need enough trials for split
            continue
        
        # Split trials
        train_data, test_data = train_test_split(
            participant_data, 
            train_size=train_ratio, 
            random_state=42
        )
        
        # Compute Type-2 AUC on training set
        try:
            type2_auc = compute_type2_auc(
                train_data['source_label'],
                train_data['participant_response'],
                train_data['confidence_rating']
            )
        except Exception as e:
            log_info(None, f"Warning: Could not compute Type-2 AUC for participant {participant_id}: {e}")
            type2_auc = np.nan
        
        # Compute d' on test set
        try:
            d_prime, criterion = compute_sdt_metrics(
                test_data['source_label'],
                test_data['participant_response']
            )
        except Exception as e:
            log_info(None, f"Warning: Could not compute d' for participant {participant_id}: {e}")
            d_prime = np.nan
        
        participant_metrics.append({
            'participant_id': participant_id,
            'type2_auc': type2_auc,
            'd_prime': d_prime
        })
    
    metrics_df = pd.DataFrame(participant_metrics)
    
    # Compute correlation
    valid_metrics = metrics_df.dropna(subset=['type2_auc', 'd_prime'])
    
    if len(valid_metrics) < 3:
        log_info(None, "Insufficient participants for correlation analysis")
        return {
            'correlation': np.nan,
            'p_value': np.nan,
            'n_participants': len(valid_metrics),
            'status': 'insufficient_data'
        }
    
    correlation, p_value = pearsonr(valid_metrics['type2_auc'], valid_metrics['d_prime'])
    
    return {
        'correlation': float(correlation),
        'p_value': float(p_value),
        'n_participants': len(valid_metrics),
        'status': 'success'
    }

def write_results(results, output_path):
    """Write results to JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    log_info(None, f"Results written to {output_path}")

def main():
    """Main entry point for T014."""
    config = load_config()
    logger = setup_logging(config)
    
    log_info(logger, "Starting correlation analysis (T014)...")
    
    try:
        # Load data
        df = load_trial_data()
        
        # Compute metrics
        results = compute_hold_out_metrics(df)
        
        # Write results
        output_path = Path("data") / "results" / "primary_analysis.json"
        write_results(results, output_path)
        
        log_info(logger, f"Analysis complete. Correlation: {results['correlation']:.3f}")
        return 0
        
    except Exception as e:
        log_error(logger, f"Analysis failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
