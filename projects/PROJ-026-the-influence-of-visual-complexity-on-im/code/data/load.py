"""
Data loading module.
Handles loading of real data or generation of synthetic data for CI/testing.
"""
import argparse
import os
import sys
import json
import hashlib
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

from config import get_project_root, get_data_path
from utils.logging import get_logger

logger = get_logger(__name__)

def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def verify_checksum(file_path: Path, stored_hash: str) -> bool:
    """Verify file checksum against stored hash."""
    current_hash = compute_sha256(file_path)
    return current_hash == stored_hash

def generate_synthetic_response_logs(
    n_participants: int = 60,
    seed: int = 42,
    null_effect: bool = False
) -> pd.DataFrame:
    """
    Generate synthetic response logs for testing.
    
    Args:
        n_participants: Number of synthetic participants.
        seed: Random seed for reproducibility.
        null_effect: If True, generate data with no effect (D-scores ~ 0).
    
    Returns:
        DataFrame with synthetic response logs.
    """
    np.random.seed(seed)
    
    # Define blocks and trials
    blocks = ["Practice1", "Test1", "Practice2", "Test2", "Test3"]
    trials_per_block = [20, 40, 20, 40, 40]
    
    data = []
    for p_idx in range(n_participants):
        participant_id = f"P{p_idx:03d}"
        
        for block_idx, block_name in enumerate(blocks):
            n_trials = trials_per_block[block_idx]
            for trial_idx in range(n_trials):
                # Simulate reaction time (normal distribution, truncated)
                rt = np.random.normal(600, 100)
                rt = np.clip(rt, 300, 10000)
                
                # Simulate correctness (mostly correct)
                is_correct = np.random.random() > 0.05
                
                # Simulate stimulus condition (simplified)
                # In a real IAT, this would depend on block and set
                stimulus_type = "Compatible" if block_idx in [1, 3] else "Incompatible"
                
                data.append({
                    "participant_id": participant_id,
                    "session_id": f"S{block_idx}",
                    "trial_number": trial_idx,
                    "block_name": block_name,
                    "reaction_time_ms": rt,
                    "is_correct": is_correct,
                    "stimulus_type": stimulus_type,
                    "timestamp": datetime.now().isoformat()
                })
    
    df = pd.DataFrame(data)
    
    # If null_effect is True, ensure D-scores will be near zero
    if null_effect:
        # Adjust reaction times to minimize difference between conditions
        # This is a simplified approach; real null-effect generation would be more nuanced
        compatible_mask = df["stimulus_type"] == "Compatible"
        incompatible_mask = df["stimulus_type"] == "Incompatible"
        
        mean_rt = df["reaction_time_ms"].mean()
        df.loc[compatible_mask, "reaction_time_ms"] = mean_rt + np.random.normal(0, 10, compatible_mask.sum())
        df.loc[incompatible_mask, "reaction_time_ms"] = mean_rt + np.random.normal(0, 10, incompatible_mask.sum())
    
    return df

def load_response_logs(
    null_effect: bool = False,
    output_path: Optional[Path] = None
) -> pd.DataFrame:
    """
    Load response logs from real data or generate synthetic data.
    
    Args:
        null_effect: If True, generate synthetic data with null effect.
        output_path: Path to save generated synthetic data (optional).
    
    Returns:
        DataFrame with response logs.
    
    Raises:
        RuntimeError: If real data is missing and not in CI/null-effect mode.
    """
    project_root = get_project_root()
    data_path = get_data_path()
    
    # Check for real data
    real_data_path = data_path / "raw" / "responses" / "participants.csv"
    
    if real_data_path.exists():
        logger.info(f"Loading real data from {real_data_path}")
        df = pd.read_csv(real_data_path)
        
        # Verify checksum if exists
        checksum_path = data_path / "checksums.json"
        if checksum_path.exists():
            with open(checksum_path, "r") as f:
                checksums = json.load(f)
            
            expected_hash = checksums.get(str(real_data_path.relative_to(project_root)))
            if expected_hash:
                if not verify_checksum(real_data_path, expected_hash):
                    raise ValueError("Data checksum mismatch! File may be corrupted.")
                logger.info("Data checksum verified.")
        else:
            # Generate checksum on first run
            current_hash = compute_sha256(real_data_path)
            checksums = {}
            if checksum_path.exists():
                with open(checksum_path, "r") as f:
                    checksums = json.load(f)
            checksums[str(real_data_path.relative_to(project_root))] = current_hash
            with open(checksum_path, "w") as f:
                json.dump(checksums, f, indent=2)
            logger.info(f"Generated and stored checksum for {real_data_path}")
        
        return df
    
    # No real data found
    if os.environ.get("GITHUB_ACTIONS") or null_effect:
        logger.warning("Real data not found. Generating synthetic data.")
        df = generate_synthetic_response_logs(n_participants=60, seed=42, null_effect=null_effect)
        
        # Save synthetic data if output_path provided
        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            df.to_csv(output_path, index=False)
            logger.info(f"Synthetic data saved to {output_path}")
        
        return df
    else:
        raise RuntimeError(
            "Real data not found and not in CI/null-effect mode. "
            "Please provide real data or run with --null-effect flag."
        )

def main(null_effect: bool = False) -> None:
    """
    Main entry point for data loading.
    
    Args:
        null_effect: If True, generate synthetic data with null effect.
    """
    logger.info("Starting data loading...")
    
    df = load_response_logs(null_effect=null_effect)
    
    # Save processed data
    data_path = get_data_path()
    processed_dir = data_path / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    output_path = processed_dir / "response_logs.csv"
    df.to_csv(output_path, index=False)
    logger.info(f"Response logs saved to {output_path}")
    
    logger.info("Data loading completed.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Load response logs")
    parser.add_argument(
        "--null-effect",
        action="store_true",
        help="Generate synthetic data with null effect"
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Output path for synthetic data"
    )
    
    args = parser.parse_args()
    
    output_path = Path(args.output) if args.output else None
    main(null_effect=args.null_effect)
