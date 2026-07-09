"""
Data Ingestion and Preprocessing Module.
Handles Data Generating Process (DGP) simulation, validation, and harmonization.
"""
import os
import sys
import json
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Union, Any
import logging

# Import from local project modules
from config import get_random_state, get_project_root
from utils.checksum import update_artifact_hash

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- DGP Configuration Schema ---
DEFAULT_DGP_CONFIG = {
    "n_participants": 500,
    "delay_discounting": {
        "k_mean": 0.05,
        "k_std": 0.02,
        "delays": [1, 7, 30, 90, 365],  # Days
        "noise_scale": 0.1
    },
    "procrastination": {
        "mean": 3.5,
        "std": 0.8,
        "n_items": 10
    },
    "nback": {
        "accuracy_mean": 0.85,
        "accuracy_std": 0.1,
        "rt_mean": 600,  # ms
        "rt_std": 100,
        "n_trials": 50
    },
    "demographics": {
        "age_mean": 30,
        "age_std": 10,
        "gender_distribution": {"M": 0.45, "F": 0.45, "Other": 0.10},
        "education_mean": 14,
        "education_std": 2
    }
}

def validate_dgp_config(config: Dict[str, Any]) -> bool:
    """
    Validates the DGP configuration schema and parameters against project specs.
    
    Args:
        config: Dictionary containing DGP parameters.
        
    Returns:
        bool: True if valid.
        
    Raises:
        SystemExit: If configuration is invalid.
    """
    required_sections = ["n_participants", "delay_discounting", "procrastination", "nback"]
    
    for section in required_sections:
        if section not in config:
            logger.error(f"CRITICAL: Missing required DGP config section: {section}")
            sys.exit(1)
    
    # Validate n_participants
    if not isinstance(config["n_participants"], int) or config["n_participants"] <= 0:
        logger.error("CRITICAL: n_participants must be a positive integer.")
        sys.exit(1)
        
    # Validate delay_discounting parameters
    dd_config = config["delay_discounting"]
    if "k_mean" not in dd_config or "delays" not in dd_config:
        logger.error("CRITICAL: delay_discounting missing k_mean or delays.")
        sys.exit(1)
        
    if not isinstance(dd_config["delays"], list) or len(dd_config["delays"]) == 0:
        logger.error("CRITICAL: delays must be a non-empty list.")
        sys.exit(1)
        
    # Validate procrastination reliability target (simulated via item count)
    if "n_items" not in config["procrastination"] or config["procrastination"]["n_items"] < 3:
        logger.error("CRITICAL: procrastination n_items must be >= 3 for reliability calculation.")
        sys.exit(1)

    logger.info("DGP Configuration validated successfully.")
    return True

def calculate_cronbach_alpha(data: np.ndarray) -> float:
    """
    Calculates Cronbach's alpha for a set of items.
    
    Args:
        data: 2D numpy array where rows are participants and columns are items.
        
    Returns:
        float: Cronbach's alpha coefficient.
    """
    if data.ndim != 2:
        raise ValueError("Data must be a 2D array (participants x items).")
        
    n_items = data.shape[1]
    if n_items < 2:
        return 0.0
        
    # Variance of each item
    var_items = np.var(data, axis=0, ddof=1)
    # Total variance (sum of items)
    var_total = np.var(np.sum(data, axis=1), ddof=1)
    
    if var_total == 0:
        return 0.0
        
    alpha = (n_items / (n_items - 1)) * (1 - np.sum(var_items) / var_total)
    return float(alpha)

def generate_delay_discounting_data(
    n_participants: int,
    output_path: str,
    seed: Optional[int] = None
) -> pd.DataFrame:
    """
    Generates synthetic delay discounting data.
    
    Simulates indifference points for various delays based on a hyperbolic model.
    V = A / (1 + k*D)
    
    Args:
        n_participants: Number of participants to simulate.
        output_path: Path to save the CSV file.
        seed: Random seed for reproducibility.
        
    Returns:
        pd.DataFrame: The generated dataframe.
    """
    rng = get_random_state(seed)
    config = DEFAULT_DGP_CONFIG["delay_discounting"]
    
    # Generate individual k values (log-normal distribution often fits better)
    k_values = rng.lognormal(mean=np.log(config["k_mean"]), sigma=config["k_std"], size=n_participants)
    
    # Generate delays
    delays = config["delays"]
    
    # Create a long-format dataframe
    rows = []
    for pid in range(1, n_participants + 1):
        k = k_values[pid-1]
        for d in delays:
            # True value: V = 100 / (1 + k*D)
            true_value = 100.0 / (1 + k * d)
            # Add noise
            noise = rng.normal(0, config["noise_scale"] * 100)
            indifference = max(0, true_value + noise)
            rows.append({
                "participant_id": pid,
                "delay": d,
                "indifference_point": indifference
            })
    
    df = pd.DataFrame(rows)
    df.to_csv(output_path, index=False)
    logger.info(f"Generated delay discounting data: {len(df)} rows -> {output_path}")
    return df

def generate_procrastination_data(
    n_participants: int,
    output_path: str,
    seed: Optional[int] = None
) -> pd.DataFrame:
    """
    Generates synthetic procrastination scale data.
    
    Args:
        n_participants: Number of participants.
        output_path: Path to save the CSV file.
        seed: Random seed.
        
    Returns:
        pd.DataFrame: The generated dataframe.
    """
    rng = get_random_state(seed)
    config = DEFAULT_DGP_CONFIG["procrastination"]
    
    rows = []
    for pid in range(1, n_participants + 1):
        # Generate item responses (1-5 Likert scale)
        # Base score + some individual variance
        base = rng.normal(config["mean"], config["std"])
        items = []
        for _ in range(config["n_items"]):
            val = rng.normal(base, 0.5)
            val = max(1, min(5, val)) # Clamp to 1-5
            items.append(round(val, 2))
        
        # Calculate total score
        score = sum(items)
        rows.append({
            "participant_id": pid,
            "procrastination_score": score,
            **{f"item_{i+1}": items[i] for i in range(len(items))}
        })
    
    df = pd.DataFrame(rows)
    df.to_csv(output_path, index=False)
    logger.info(f"Generated procrastination data: {len(df)} rows -> {output_path}")
    return df

def generate_nback_data(
    n_participants: int,
    output_path: str,
    seed: Optional[int] = None
) -> pd.DataFrame:
    """
    Generates synthetic n-back working memory task data.
    
    Args:
        n_participants: Number of participants.
        output_path: Path to save the CSV file.
        seed: Random seed.
        
    Returns:
        pd.DataFrame: The generated dataframe.
    """
    rng = get_random_state(seed)
    config = DEFAULT_DGP_CONFIG["nback"]
    
    rows = []
    for pid in range(1, n_participants + 1):
        # Individual variability
        acc_base = rng.normal(config["accuracy_mean"], config["accuracy_std"])
        rt_base = rng.normal(config["rt_mean"], config["rt_std"])
        
        acc_base = max(0.5, min(1.0, acc_base))
        rt_base = max(200, rt_base)
        
        # Simulate aggregate stats over n_trials
        n_trials = config["n_trials"]
        # Generate trial-level data to calculate aggregate
        trials = rng.normal(0, 1, n_trials)
        # Map to accuracy (sigmoid-like)
        trial_acc = 1 / (1 + np.exp(-trials * 2 + (acc_base - 0.5) * 10))
        # Map to RT
        trial_rt = rt_base + rng.normal(0, config["rt_std"] * 0.2, n_trials)
        
        agg_acc = float(np.mean(trial_acc))
        agg_rt = float(np.mean(trial_rt))
        
        rows.append({
            "participant_id": pid,
            "wm_accuracy": agg_acc,
            "wm_rt": agg_rt,
            "n_trials": n_trials
        })
    
    df = pd.DataFrame(rows)
    df.to_csv(output_path, index=False)
    logger.info(f"Generated n-back data: {len(df)} rows -> {output_path}")
    return df

def harmonize_datasets(
    dd_path: str,
    proc_path: str,
    nback_path: str
) -> pd.DataFrame:
    """
    Harmonizes and merges the three generated datasets.
    
    Args:
        dd_path: Path to delay discounting CSV.
        proc_path: Path to procrastination CSV.
        nback_path: Path to n-back CSV.
        
    Returns:
        pd.DataFrame: Merged dataframe.
        
    Raises:
        SystemExit: If ID mismatch > 10%.
    """
    logger.info("Starting data harmonization...")
    
    df_dd = pd.read_csv(dd_path)
    df_proc = pd.read_csv(proc_path)
    df_nback = pd.read_csv(nback_path)
    
    # Get unique IDs from each
    ids_dd = set(df_dd['participant_id'])
    ids_proc = set(df_proc['participant_id'])
    ids_nback = set(df_nback['participant_id'])
    
    # Check for perfect overlap first
    common_ids = ids_dd.intersection(ids_proc).intersection(ids_nback)
    total_expected = len(ids_dd)
    
    if total_expected > 0:
        mismatch_rate = 1.0 - (len(common_ids) / total_expected)
        if mismatch_rate > 0.10:
            logger.error(f"CRITICAL: ID mismatch rate {mismatch_rate:.2%} exceeds 10% threshold.")
            sys.exit(1)
    
    # Aggregate scores for delay discounting (calculate k per participant)
    # We need to fit the hyperbolic model or use a simplified metric if fitting fails.
    # For this ingestion step, we calculate a simple mean indifference ratio as a proxy 
    # or attempt to fit. Since T015c does the real fitting, here we just ensure columns exist.
    # However, to match the schema expected by later steps, we need a 'discount_rate_k'.
    # We will perform a simple fit here to populate the column for the harmonized set.
    
    def simple_k_fit(df):
        # Group by participant
        results = []
        for pid, group in df.groupby('participant_id'):
            delays = group['delay'].values
            ips = group['indifference_point'].values
            if len(delays) < 2:
                results.append((pid, 0.0))
                continue
            # Simple linear regression on 1/V vs D? Or just use a heuristic for ingestion test
            # Heuristic: k ~ (100 - min_ip) / (100 * max_delay) approx
            # Better: fit 100/(1+kD) = ip -> 100/ip - 1 = kD -> k = (100/ip - 1)/D
            k_vals = []
            for d, ip in zip(delays, ips):
                if ip > 0 and d > 0:
                    k_est = (100.0/ip - 1.0) / d
                    if k_est > 0:
                        k_vals.append(k_est)
            k_mean = np.mean(k_vals) if k_vals else 0.0
            results.append((pid, k_mean))
        return pd.DataFrame(results, columns=['participant_id', 'discount_rate_k'])

    agg_dd = simple_k_fit(df_dd)
    
    # Aggregate procrastination (mean of items)
    item_cols = [c for c in df_proc.columns if c.startswith('item_')]
    df_proc['procrastination_score'] = df_proc[item_cols].mean(axis=1)
    agg_proc = df_proc[['participant_id', 'procrastination_score']]
    
    # N-back is already aggregated
    agg_nback = df_nback[['participant_id', 'wm_accuracy', 'wm_rt']]
    
    # Merge
    df_merged = pd.merge(agg_dd, agg_proc, on='participant_id', how='inner')
    df_merged = pd.merge(df_merged, agg_nback, on='participant_id', how='inner')
    
    logger.info(f"Harmonized dataset size: {len(df_merged)}")
    return df_merged

def run_dgp_pipeline(output_dir: str, seed: Optional[int] = None):
    """
    Runs the full DGP generation, validation, and reliability check pipeline.
    This is the main entry point for data generation tasks (T014, T014b).
    """
    root = Path(output_dir)
    raw_dir = root / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    
    config = DEFAULT_DGP_CONFIG
    validate_dgp_config(config)
    
    n = config["n_participants"]
    s = seed if seed is not None else 42
    
    dd_path = raw_dir / "delay_discounting.csv"
    proc_path = raw_dir / "procrastination.csv"
    nback_path = raw_dir / "nback.csv"
    
    # Generate
    df_dd = generate_delay_discounting_data(n, str(dd_path), s)
    df_proc = generate_procrastination_data(n, str(proc_path), s)
    df_nback = generate_nback_data(n, str(nback_path), s)
    
    # Reliability Check (T014b)
    logger.info("Checking Cronbach's alpha for procrastination data...")
    item_cols = [c for c in df_proc.columns if c.startswith('item_')]
    if len(item_cols) > 1:
        alpha = calculate_cronbach_alpha(df_proc[item_cols].values)
        logger.info(f"Cronbach's Alpha: {alpha:.4f}")
        if alpha < 0.7:
            logger.critical(f"CRITICAL: Synthetic data reliability below threshold (alpha < 0.7). Alpha was {alpha}.")
            sys.exit(1)
    else:
        logger.warning("Not enough items to calculate Cronbach's alpha.")
        
    # Harmonize (T015a)
    logger.info("Harmonizing datasets...")
    df_harmonized = harmonize_datasets(str(dd_path), str(proc_path), str(nback_path))
    
    # Save harmonized to processed (interim step for T015a)
    processed_dir = root / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    harmonized_path = processed_dir / "harmonized_interim.csv"
    df_harmonized.to_csv(harmonized_path, index=False)
    
    # Update checksums
    update_artifact_hash(str(dd_path))
    update_artifact_hash(str(proc_path))
    update_artifact_hash(str(nback_path))
    update_artifact_hash(str(harmonized_path))
    
    logger.info("DGP Pipeline completed successfully.")
    return df_harmonized

if __name__ == "__main__":
    # Example execution for testing
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="data", help="Output directory")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    args = parser.parse_args()
    
    run_dgp_pipeline(args.output, args.seed)
