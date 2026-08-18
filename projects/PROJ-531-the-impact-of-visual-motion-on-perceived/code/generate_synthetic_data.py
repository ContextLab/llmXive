"""
Synthetic Data Generator for Visual Motion Agency Study.

Generates synthetic human-avatar interaction data with known ground-truth
motion-agency relationships (FR-011). This module is designed to run in parallel
with the real data downloader (T012) and outputs data ONLY if the real source
is unavailable or invalid.

Key constraints:
- `user_response_trigger` is distinct from `agency_score` (FR-012).
- Ground-truth correlations are explicitly injected.
- No real human data is used; strictly a stress-test artifact.
"""
import os
import json
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime
import sys
import logging

# Configure logging to match project standards
# Attempt to import project logger, fallback to basic config
try:
    from utils.logging_config import get_logger
    logger = get_logger("synthetic_generator")
except ImportError:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger("synthetic_generator")

def generate_synthetic_data(n_samples: int = 150, seed: int = 42) -> pd.DataFrame:
    """
    Generate synthetic human-avatar interaction data.
    
    Args:
        n_samples: Number of observations to generate.
        seed: Random seed for reproducibility.
    
    Returns:
        pd.DataFrame: Synthetic dataset with motion features and agency scores.
    
    Raises:
        ValueError: If n_samples is non-positive.
    """
    if n_samples <= 0:
        raise ValueError("n_samples must be positive")
    
    np.random.seed(seed)
    logger.info(f"Generating {n_samples} synthetic samples with seed {seed}")
    
    # 1. Generate Latency (ms) - Realistic range for network/handshake lag
    # Distribution: Skewed right, typical mean ~150ms
    latency = np.random.exponential(scale=80, size=n_samples) + 50
    
    # 2. Generate Smoothness (Jerk) - Inverse of movement fluidity
    # Distribution: Normal, higher values = jerkier
    smoothness = np.random.normal(loc=2.5, scale=0.8, size=n_samples)
    smoothness = np.clip(smoothness, 0.1, 10.0)
    
    # 3. Generate Lead Time (ms) - Anticipation capability
    # Distribution: Normal, can be negative (reactive) or positive (proactive)
    lead_time = np.random.normal(loc=50, scale=30, size=n_samples)
    
    # 4. Generate User Response Trigger (ms) - Distinct from agency score (FR-012)
    # This represents the raw time taken to react to a visual cue, independent of
    # the perceived agency score.
    user_response_trigger = np.random.normal(loc=200, scale=40, size=n_samples)
    
    # 5. Generate Ground-Truth Agency Score (0.0 - 1.0)
    # FR-011: Known ground-truth motion-agency relationships.
    # Relationship: Higher Smoothness (lower jerk) and lower Latency increase Agency.
    # Relationship: Positive Lead Time increases Agency.
    # We normalize features to 0-1 for linear combination logic.
    
    lat_norm = (latency - latency.min()) / (latency.max() - latency.min() + 1e-8)
    sm_norm = (smoothness - smoothness.min()) / (smoothness.max() - smoothness.min() + 1e-8)
    lead_norm = (lead_time - lead_time.min()) / (lead_time.max() - lead_time.min() + 1e-8)
    
    # Inject known correlations:
    # - Latency: Negative correlation (higher latency -> lower agency)
    # - Smoothness: Negative correlation (higher jerk -> lower agency)
    # - Lead Time: Positive correlation (better anticipation -> higher agency)
    base_agency = (
        1.0 
        - 0.4 * lat_norm  # Latency weight
        - 0.3 * sm_norm   # Smoothness weight
        + 0.3 * lead_norm # Lead time weight
    )
    
    # Add noise to simulate measurement error and unmodeled factors
    noise = np.random.normal(0, 0.05, size=n_samples)
    agency_score = base_agency + noise
    
    # Clip to [0, 1] range
    agency_score = np.clip(agency_score, 0.0, 1.0)
    
    # Create DataFrame
    df = pd.DataFrame({
        'participant_id': [f"syn_{i:04d}" for i in range(n_samples)],
        'latency': latency,
        'smoothness': smoothness,
        'lead_time': lead_time,
        'user_response_trigger': user_response_trigger,
        'agency_score': agency_score
    })
    
    # Add metadata column for provenance (optional but good practice)
    df['data_source'] = 'synthetic'
    df['generation_timestamp'] = datetime.now().isoformat()
    
    logger.info(f"Synthetic data generation complete. Shape: {df.shape}")
    logger.info(f"Correlations (Latency, Smoothness, LeadTime) vs Agency: "
                f"{df[['latency', 'smoothness', 'lead_time']].corrwith(df['agency_score']).to_dict()}")
    
    return df

def main():
    """
    Main entry point for the synthetic data generator.
    
    This script is intended to be run as a standalone process.
    It checks for the existence of real data (via T012 status).
    If real data is unavailable or invalid, it generates synthetic data.
    
    Workflow:
    1. Check `data/raw/download_status.json` (produced by T012).
    2. If status is "available" and "valid", exit gracefully (no synthetic data needed).
    3. If status is "unavailable", "invalid", or missing, generate synthetic data.
    4. Write output to `data/processed/synthetic_data.csv`.
    5. Write a manifest to `data/processed/synthetic_manifest.json`.
    """
    logger.info("Starting synthetic data generation check...")
    
    base_path = Path("data")
    raw_path = base_path / "raw"
    processed_path = base_path / "processed"
    
    # Ensure directories exist
    raw_path.mkdir(parents=True, exist_ok=True)
    processed_path.mkdir(parents=True, exist_ok=True)
    
    status_file = raw_path / "download_status.json"
    output_csv = processed_path / "synthetic_data.csv"
    manifest_file = processed_path / "synthetic_manifest.json"
    
    # Check T012 status
    generate_synthetic = False
    reason = ""
    
    if not status_file.exists():
        generate_synthetic = True
        reason = "T012 status file not found. Assuming real data unavailable."
    else:
        try:
            with open(status_file, 'r') as f:
                status = json.load(f)
            
            status_val = status.get('status', '').lower()
            valid_val = status.get('valid', False)
            
            if status_val == 'unavailable' or status_val == 'invalid' or not valid_val:
                generate_synthetic = True
                reason = f"T012 reported status '{status_val}' or valid={valid_val}."
            else:
                logger.info(f"T012 reported real data available. Skipping synthetic generation.")
                print("SKIP: Real data available. No synthetic data generated.")
                return 0
        except Exception as e:
            generate_synthetic = True
            reason = f"Error reading T012 status: {str(e)}. Defaulting to synthetic."
    
    if generate_synthetic:
        logger.info(f"Generating synthetic data because: {reason}")
        
        # Generate data
        df = generate_synthetic_data(n_samples=150, seed=42)
        
        # Write CSV
        df.to_csv(output_csv, index=False)
        logger.info(f"Synthetic data written to {output_csv}")
        
        # Write Manifest
        manifest = {
            "source": "synthetic_generator",
            "generator_version": "1.0.0",
            "n_samples": len(df),
            "seed": 42,
            "ground_truth_correlations": {
                "latency": "negative",
                "smoothness": "negative",
                "lead_time": "positive"
            },
            "timestamp": datetime.now().isoformat(),
            "reason_for_generation": reason,
            "fr_012_compliance": "user_response_trigger is distinct from agency_score"
        }
        
        with open(manifest_file, 'w') as f:
            json.dump(manifest, f, indent=2)
        
        logger.info(f"Manifest written to {manifest_file}")
        print(f"SUCCESS: Synthetic data generated and saved to {output_csv}")
        return 0
    
    return 1

if __name__ == "__main__":
    sys.exit(main())
