"""
T013: Generate synthetic data IF download_status is 'unavailable'.
Checks status file. Raises SystemExit if 'invalid'.
Generates data with independent trigger column.
"""
import os
import json
import sys
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime
from utils.logging_config import get_logger

logger = get_logger(__name__)

def check_download_status():
    """Read data/raw/download_status.json."""
    status_path = Path("data/raw/download_status.json")
    if not status_path.exists():
        logger.error("download_status.json not found. Run T012 first.")
        return None
    
    with open(status_path, 'r') as f:
        return json.load(f).get("status")

def generate_synthetic_data(n_samples: int = 150):
    """
    Generate synthetic human-avatar interaction data.
    - Ground truth motion-agency relationships.
    - Independent user_response_trigger.
    """
    logger.info(f"Generating {n_samples} synthetic samples.")
    
    # 1. Generate Motion Features (Latency, Smoothness, Lead_time)
    latency = np.random.normal(loc=200, scale=50, size=n_samples) # ms
    smoothness = np.random.beta(a=5, b=2, size=n_samples) # 0-1
    lead_time = np.random.normal(loc=100, scale=30, size=n_samples) # ms
    
    # 2. Generate Agency Score (Ground Truth: Function of motion)
    # Agency = 0.5*smoothness - 0.3*(latency/500) + noise
    agency_raw = (0.5 * smoothness) - (0.3 * (latency / 500)) + (0.2 * np.random.normal(0, 1, n_samples))
    # Normalize to 0-1
    agency_score = (agency_raw - agency_raw.min()) / (agency_raw.max() - agency_raw.min())
    
    # 3. Generate User Response Trigger (INDEPENDENT of Agency)
    # Must be statistically independent.
    # We generate it from a different distribution and ensure no correlation.
    trigger_raw = np.random.exponential(scale=1.0, size=n_samples)
    trigger = (trigger_raw - trigger_raw.min()) / (trigger_raw.max() - trigger_raw.min())
    
    # 4. Verify Independence
    corr = np.corrcoef(trigger, agency_score)[0, 1]
    if abs(corr) >= 0.05:
        logger.error(f"Synthetic data failed independence check: |corr| = {abs(corr):.4f}")
        # Regenerate or fail. Failing is safer to prevent bad data.
        raise ValueError(f"Trigger/Agency correlation {corr} exceeds threshold 0.05")
    
    logger.info(f"Trigger/Agency correlation: {corr:.4f} (OK)")
    
    # 5. Assemble DataFrame
    df = pd.DataFrame({
        "participant_id": [f"P{i:03d}" for i in range(n_samples)],
        "latency": latency,
        "smoothness": smoothness,
        "lead_time": lead_time,
        "agency_score": agency_score,
        "user_response_trigger": trigger
    })
    
    return df

def main():
    status = check_download_status()
    
    if status is None:
        sys.exit(1)
    
    if status == "invalid":
        logger.error("Dataset excluded: Unvalidated instrument (FR-009). Aborting synthetic generation.")
        sys.exit(1)
    
    if status == "success":
        logger.info("Real data available. Skipping synthetic generation.")
        return 0
    
    if status == "unavailable":
        try:
            df = generate_synthetic_data()
            
            output_path = Path("data/raw/synthetic_data.csv")
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            df.to_csv(output_path, index=False)
            logger.info(f"Saved synthetic data to {output_path}")
            return 0
        except Exception as e:
            logger.error(f"Synthetic generation failed: {e}")
            sys.exit(1)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())