"""
T014: Implement correlation analysis with Hold-Out Accuracy design.

Computes Metacognitive Score (Type-2 AUC) on a training split and 
Reality Testing Accuracy (d') on a held-out test split to ensure independence.
"""
import os
import sys
import json
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from sklearn.model_selection import train_test_split
from scipy.stats import pearsonr
import warnings

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from config.env_config import load_config, AppConfig
from src.utils.stats import compute_type2_auc, compute_sdt_metrics

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Tolerant config wrapper to handle missing attributes gracefully
class TolerantConfig:
    def __init__(self, config_dict: Dict[str, Any]):
        self._config = config_dict

    def get(self, section: str, default: Any = None) -> Any:
        return self._config.get(section, default) if self._config else default

def load_trial_data() -> pd.DataFrame:
    """Load the preprocessed trial data."""
    trial_data_path = project_root / "data" / "derived" / "trial_data.csv"
    
    if not trial_data_path.exists():
        logger.error(f"Trial data not found at {trial_data_path}. Run preprocessing first.")
        raise FileNotFoundError(f"Trial data file not found: {trial_data_path}")
    
    df = pd.read_csv(trial_data_path)
    logger.info(f"Loaded {len(df)} trials from {trial_data_path}")
    return df

def compute_hold_out_metrics(
    df: pd.DataFrame, 
    test_size: float = 0.3, 
    random_state: int = 42
) -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, Any]]:
    """
    Implement Hold-Out Accuracy design.
    
    Split trials into training (70%) and test (30%) sets.
    Compute Type-2 AUC on training set and d' on test set.
    
    Returns:
        train_df: Training split data
        test_df: Test split data
        metrics: Dictionary with correlation results
    """
    logger.info(f"Performing Hold-Out split (test_size={test_size}, random_state={random_state})")
    
    # Ensure required columns exist
    required_cols = ['participant_id', 'trial_id', 'participant_response', 
                    'confidence_rating', 'source_label', 'stimulus_modality']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")
    
    # Calculate accuracy for each trial (binary: correct/incorrect)
    # Assuming source_label indicates ground truth and participant_response is the guess
    # Normalize strings for comparison
    df['source_clean'] = df['source_label'].astype(str).str.lower().str.strip()
    df['response_clean'] = df['participant_response'].astype(str).str.lower().str.strip()
    df['accuracy'] = (df['source_clean'] == df['response_clean']).astype(int)
    
    # Split by participant to avoid data leakage (trials from same participant in both sets)
    participants = df['participant_id'].unique()
    train_participants, test_participants = train_test_split(
        participants, 
        test_size=test_size, 
        random_state=random_state
    )
    
    train_df = df[df['participant_id'].isin(train_participants)].copy()
    test_df = df[df['participant_id'].isin(test_participants)].copy()
    
    logger.info(f"Training set: {len(train_df)} trials ({len(train_participants)} participants)")
    logger.info(f"Test set: {len(test_df)} trials ({len(test_participants)} participants)")
    
    if len(train_df) == 0 or len(test_df) == 0:
        raise ValueError("Split resulted in empty train or test set.")
    
    # Compute Metacognitive Score (Type-2 AUC) on TRAINING set
    # Group by participant to compute per-participant meta-d' or Type-2 AUC
    train_metrics = []
    for pid in train_participants:
        p_data = train_df[train_df['participant_id'] == pid]
        
        # Need binary accuracy and confidence ratings
        if p_data['accuracy'].nunique() < 2 or p_data['confidence_rating'].nunique() < 2:
            # Skip participants with insufficient variance
            continue
        
        try:
            # Compute Type-2 AUC using the helper function
            # Inputs: confidence ratings and binary accuracy
            auc_val = compute_type2_auc(
                confidence=p_data['confidence_rating'].values,
                accuracy=p_data['accuracy'].values
            )
            train_metrics.append({
                'participant_id': pid,
                'metacognitive_score': auc_val,
                'n_trials': len(p_data)
            })
        except Exception as e:
            logger.warning(f"Could not compute Type-2 AUC for participant {pid}: {e}")
            continue
    
    if not train_metrics:
        raise ValueError("No valid metacognitive scores computed from training set.")
    
    train_metrics_df = pd.DataFrame(train_metrics)
    logger.info(f"Computed metacognitive scores for {len(train_metrics_df)} participants")
    
    # Compute Reality Testing Accuracy (d') on TEST set
    # d' is computed per participant based on hits and false alarms
    # We need to define signal/noise. Assuming 'source_label' has categories like 'real', 'fake'
    # Let's assume 'real' is signal, 'fake' is noise for d' calculation
    test_metrics = []
    for pid in test_participants:
        p_data = test_df[test_df['participant_id'] == pid]
        
        # Calculate hits and false alarms
        # Hit: Real stimulus identified as Real
        # FA: Fake stimulus identified as Real
        p_data['is_real'] = (p_data['source_clean'] == 'real').astype(int)
        p_data['responded_real'] = (p_data['response_clean'] == 'real').astype(int)
        
        hits = p_data[(p_data['is_real'] == 1) & (p_data['responded_real'] == 1)].shape[0]
        total_real = p_data[p_data['is_real'] == 1].shape[0]
        
        fas = p_data[(p_data['is_real'] == 0) & (p_data['responded_real'] == 1)].shape[0]
        total_fake = p_data[p_data['is_real'] == 0].shape[0]
        
        if total_real == 0 or total_fake == 0:
            continue
        
        hit_rate = hits / total_real
        fa_rate = fas / total_fake
        
        # Apply logit correction for extreme values
        if hit_rate == 0: hit_rate = 0.5 / total_real
        if hit_rate == 1: hit_rate = 1 - (0.5 / total_real)
        if fa_rate == 0: fa_rate = 0.5 / total_fake
        if fa_rate == 1: fa_rate = 1 - (0.5 / total_fake)
        
        # Compute d'
        z_hit = norm.ppf(hit_rate)
        z_fa = norm.ppf(fa_rate)
        d_prime = z_hit - z_fa
        
        test_metrics.append({
            'participant_id': pid,
            'd_prime': d_prime,
            'hit_rate': hit_rate,
            'fa_rate': fa_rate,
            'n_trials': len(p_data)
        })
    
    if not test_metrics:
        raise ValueError("No valid d' scores computed from test set.")
    
    test_metrics_df = pd.DataFrame(test_metrics)
    logger.info(f"Computed d' scores for {len(test_metrics_df)} participants")
    
    # Merge metrics (participants must exist in both sets for correlation)
    # Note: Due to random split, some participants might only be in one set if the split was by trial
    # But we split by participant, so this should be disjoint. 
    # Wait, we need correlation between Metacognitive (Train) and Accuracy (Test).
    # Since we split by participant, a participant is EITHER in train OR in test.
    # This means we CANNOT compute correlation at participant level directly from this split.
    
    # Correction: The task description says "Compute Metacognitive Score on training split... 
    # Compute Reality Testing Accuracy on held-out test split."
    # If we split by participant, we have disjoint participants. 
    # We cannot correlate X_train_participants with Y_test_participants.
    
    # Alternative interpretation (Hold-Out Accuracy Design):
    # Split trials for EACH participant into train/test.
    # Compute Meta for that participant on their train trials.
    # Compute Acc for that participant on their test trials.
    # Then correlate Meta vs Acc across participants.
    
    # Let's re-implement: Split trials WITHIN each participant
    logger.info("Re-calculating: Splitting trials WITHIN each participant (Hold-Out per participant)")
    
    meta_scores = []
    acc_scores = []
    
    valid_participants = 0
    
    for pid in df['participant_id'].unique():
        p_data = df[df['participant_id'] == pid].copy()
        
        if len(p_data) < 10: # Minimum trials required
            continue
        
        # Split trials for this participant
        p_train, p_test = train_test_split(
            p_data, 
            test_size=test_size, 
            random_state=random_state + int(pid) # Ensure reproducibility per participant
        )
        
        if len(p_train) < 5 or len(p_test) < 5:
            continue
        
        # Compute Meta (Type-2 AUC) on TRAIN trials
        try:
            auc_val = compute_type2_auc(
                confidence=p_train['confidence_rating'].values,
                accuracy=p_train['accuracy'].values
            )
            meta_scores.append(auc_val)
        except Exception as e:
            logger.warning(f"Meta AUC failed for {pid}: {e}")
            continue
        
        # Compute d' on TEST trials
        # Recalculate hits/FA for this participant's test set
        p_test['is_real'] = (p_test['source_clean'] == 'real').astype(int)
        p_test['responded_real'] = (p_test['response_clean'] == 'real').astype(int)
        
        hits = p_test[(p_test['is_real'] == 1) & (p_test['responded_real'] == 1)].shape[0]
        total_real = p_test[p_test['is_real'] == 1].shape[0]
        fas = p_test[(p_test['is_real'] == 0) & (p_test['responded_real'] == 1)].shape[0]
        total_fake = p_test[p_test['is_real'] == 0].shape[0]
        
        if total_real == 0 or total_fake == 0:
            continue
        
        hit_rate = hits / total_real
        fa_rate = fas / total_fake
        
        # Correction
        if hit_rate == 0: hit_rate = 0.5 / total_real
        if hit_rate == 1: hit_rate = 1 - (0.5 / total_real)
        if fa_rate == 0: fa_rate = 0.5 / total_fake
        if fa_rate == 1: fa_rate = 1 - (0.5 / total_fake)
        
        z_hit = norm.ppf(hit_rate)
        z_fa = norm.ppf(fa_rate)
        d_prime = z_hit - z_fa
        
        acc_scores.append(d_prime)
        valid_participants += 1
    
    if valid_participants < 2:
        raise ValueError(f"Insufficient participants with valid split data ({valid_participants}).")
    
    results_df = pd.DataFrame({
        'participant_id': [f"sub_{i:03d}" for i in range(valid_participants)],
        'metacognitive_score': meta_scores,
        'd_prime': acc_scores
    })
    
    # Compute Pearson correlation
    r, p_value = pearsonr(results_df['metacognitive_score'], results_df['d_prime'])
    
    metrics = {
        'correlation_coefficient': float(r),
        'p_value': float(p_value),
        'n_participants': valid_participants,
        'split_ratio': f"70/30",
        'method': 'Hold-Out Accuracy (Trial-wise split per participant)',
        'random_state': random_state
    }
    
    logger.info(f"Correlation: r={r:.4f}, p={p_value:.4f}")
    
    return train_df, test_df, metrics, results_df

def write_results(metrics: Dict[str, Any], results_df: pd.DataFrame):
    """Write the primary analysis results to JSON and CSV."""
    output_dir = project_root / "data" / "results"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Write JSON summary
    json_path = output_dir / "primary_analysis.json"
    with open(json_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    logger.info(f"Wrote results to {json_path}")
    
    # Write detailed participant data
    csv_path = output_dir / "correlation_participants.csv"
    results_df.to_csv(csv_path, index=False)
    logger.info(f"Wrote participant data to {csv_path}")

def main():
    """Main entry point for T014."""
    try:
        # Load config (tolerant)
        config = load_config()
        tolerant_config = TolerantConfig(config)
        
        # Get parameters from config or defaults
        test_size = tolerant_config.get('analysis', {}).get('test_size', 0.3)
        random_state = tolerant_config.get('analysis', {}).get('random_state', 42)
        
        logger.info("Starting T014: Correlation Analysis with Hold-Out Design")
        
        # Load data
        df = load_trial_data()
        
        # Compute metrics
        train_df, test_df, metrics, results_df = compute_hold_out_metrics(
            df, 
            test_size=test_size, 
            random_state=random_state
        )
        
        # Write results
        write_results(metrics, results_df)
        
        logger.info("T014 completed successfully.")
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"Data file error: {e}")
        return 1
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
