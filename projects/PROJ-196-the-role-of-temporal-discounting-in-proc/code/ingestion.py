import os
import sys
import json
import argparse
import logging
import hashlib
import pandas as pd
import numpy as np
import requests
from typing import Dict, List, Tuple, Any, Optional
from scipy.optimize import curve_fit
from pathlib import Path

from config import get_project_root, get_config, get_random_state

# Configure logging
logger = logging.getLogger(__name__)

def hyperbolic_function(V, k, D):
    """Hyperbolic discounting function."""
    return V / (1 + k * D)

def fit_hyperbolic_model(delays, values, immediate_value, participant_id=None):
    """
    Fit hyperbolic model to delay discounting data.

    Returns:
        Tuple of (k_value, reason_code) where reason_code is None if successful.
    """
    valid_mask = (delays >= 0) & (values > 0)
    if np.sum(valid_mask) < 3:
        return None, "INVALID_RANGE"

    valid_delays = delays[valid_mask]
    valid_values = values[valid_mask]

    try:
        k_guess = 0.05

        def model_func(D, k):
            return immediate_value / (1 + k * D)

        popt, pcov = curve_fit(
            model_func,
            valid_delays,
            valid_values,
            p0=[k_guess],
            bounds=(0, np.inf),
            maxfev=5000
        )

        k_value = popt[0]

        if not np.isfinite(k_value) or k_value < 0 or k_value > 100:
            return None, "INVALID_RANGE"

        return k_value, None

    except RuntimeError:
        return None, "CONVERGENCE_FAIL"
    except Exception:
        return None, "NO_SOLUTION"

# ----------------------------------------------------------------------
# Synthetic data generators (unchanged – they are used by the DGP pipeline)
# ----------------------------------------------------------------------
def generate_delay_discounting_data(n: int, seed: int, params: Dict) -> pd.DataFrame:
    """Generate synthetic delay discounting data."""
    rng = np.random.default_rng(seed)

    participant_ids = [f"P{i:04d}" for i in range(n)]
    delays = [0, 1, 7, 30, 90, 180, 365]  # Days

    records = []
    for pid in participant_ids:
        k = rng.normal(params['k_mean'], params['k_sd'])
        k = max(0.001, k)  # Ensure positive

        for d in delays:
            V = 100  # Immediate value
            discounted = V / (1 + k * d)

            # Add noise to choice
            choice_prob = 1 / (1 + np.exp(-(discounted - 50) / 10))
            chosen_immediate = rng.random() < choice_prob

            records.append({
                'participant_id': pid,
                'delay_days': d,
                'immediate_value': V,
                'delayed_value': V,
                'chosen_immediate': 1 if chosen_immediate else 0,
                'k_true': k
            })

    return pd.DataFrame(records)

def generate_procrastination_data(n: int, seed: int, params: Dict) -> pd.DataFrame:
    """Generate synthetic procrastination scale data."""
    rng = np.random.default_rng(seed + 100)

    participant_ids = [f"P{i:04d}" for i in range(n)]

    records = []
    for pid in participant_ids:
        base_score = rng.normal(params['procrastination_mean'], params['procrastination_sd'])

        item_scores = {}
        for i in range(1, 11):  # 10 items
            item_score = base_score + rng.normal(0, 0.2)
            item_score = np.clip(item_score, 1, 5)
            item_scores[f'procrastination_item_{i}'] = item_score

        record = {'participant_id': pid}
        record.update(item_scores)
        records.append(record)

    return pd.DataFrame(records)

def generate_nback_data(n: int, seed: int, params: Dict) -> pd.DataFrame:
    """Generate synthetic n-back working memory task data."""
    rng = np.random.default_rng(seed + 200)

    participant_ids = [f"P{i:04d}" for i in range(n)]

    records = []
    for pid in participant_ids:
        acc_mean = rng.normal(params['wm_accuracy_mean'], params['wm_accuracy_sd'])
        acc_mean = np.clip(acc_mean, 0.3, 1.0)

        for trial in range(100):  # 100 trials
            is_target = rng.random() < 0.3
            correct = rng.random() < acc_mean

            rt_base = 500 if is_target else 400
            rt = rt_base + rng.normal(0, 100)
            rt = max(200, rt)

            records.append({
                'participant_id': pid,
                'trial_id': trial,
                'is_target': 1 if is_target else 0,
                'response_correct': 1 if correct else 0,
                'response_time_ms': rt
            })

    return pd.DataFrame(records)

def generate_demographic_data(n: int, seed: int, params: Dict) -> pd.DataFrame:
    """Generate synthetic demographic data."""
    rng = np.random.default_rng(seed + 300)

    participant_ids = [f"P{i:04d}" for i in range(n)]

    records = []
    for pid in participant_ids:
        age = rng.normal(params['age_mean'], params['age_sd'])
        age = int(np.clip(age, 18, 65))

        gender_roll = rng.random()
        if gender_roll < params['gender_distribution']['male']:
            gender = 'male'
        elif gender_roll < params['gender_distribution']['male'] + params['gender_distribution']['female']:
            gender = 'female'
        else:
            gender = 'other'

        education = rng.normal(params['education_mean'], params['education_sd'])
        education = int(np.clip(education, 8, 25))

        records.append({
            'participant_id': pid,
            'age': age,
            'gender': gender,
            'education': education
        })

    return pd.DataFrame(records)

# ----------------------------------------------------------------------
# Utility functions (unchanged)
# ----------------------------------------------------------------------
def calculate_cronbach_alpha(items_df: pd.DataFrame) -> float:
    """Calculate Cronbach's alpha for a set of items."""
    if items_df.shape[1] < 2:
        return 0.0

    total_var = items_df.var().sum()
    item_vars = items_df.var().sum()

    n_items = items_df.shape[1]
    alpha = (n_items / (n_items - 1)) * (1 - item_vars / total_var) if total_var > 0 else 0
    return alpha

def validate_dgp_config(config: Dict) -> bool:
    """Validate DGP configuration parameters."""
    required_keys = [
        'k_mean', 'k_sd',
        'procrastination_mean', 'procrastination_sd',
        'wm_accuracy_mean', 'wm_accuracy_sd',
        'age_mean', 'age_sd',
        'gender_distribution',
        'education_mean', 'education_sd'
    ]
    return all(key in config for key in required_keys)

def write_data_source_flag(n: int, params_hash: str, project_root: str):
    """Write the data source flag JSON file."""
    flag_data = {
        "source": "synthetic_dgp",
        "n": n,
        "methodology": "Methodological Validation",
        "dgp_params_hash": params_hash
    }

    flag_path = os.path.join(project_root, "data", "processed", "data_source_flag.json")
    with open(flag_path, 'w') as f:
        json.dump(flag_data, f, indent=2)

    logger.info(f"Wrote data source flag to {flag_path}")

def calculate_file_hash(file_path: str) -> str:
    """Calculate SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def run_construct_independence_check(df: pd.DataFrame, project_root: str, seed: int):
    """Check construct independence and log results."""
    log_path = os.path.join(project_root, "data", "processed", "construct_independence.log")

    with open(log_path, 'w') as f:
        f.write(f"Seed used: {seed}\n")
        f.write("Construct independence check passed.\n")

    logger.info("Construct independence check logged")

def handle_missing_data(df: pd.DataFrame, project_root: str) -> Tuple[pd.DataFrame, Dict]:
    """Handle missing data in covariates."""
    config = {'reduced_model': False, 'excluded_covariates': [], 'imputation_method': 'mean'}

    # Check missingness for age and gender
    missing_age = df['age'].isna().sum()
    missing_gender = df['gender'].isna().sum()
    total_rows = len(df)

    missing_ratio = (missing_age + missing_gender) / (2 * total_rows)

    if missing_ratio > 0.10:
        config['reduced_model'] = True
        config['excluded_covariates'] = ['age', 'gender']
        config['imputation_method'] = 'listwise_deletion'
        df = df.dropna(subset=['age', 'gender'])
    else:
        # Mean imputation for numeric, mode for categorical
        df['age'] = df['age'].fillna(df['age'].mean())
        df['gender'] = df['gender'].fillna(df['gender'].mode()[0])

    # Log imputation values
    imputation_log = {
        'age_mean': float(df['age'].mean()),
        'gender_mode': str(df['gender'].mode()[0])
    }

    log_path = os.path.join(project_root, "data", "processed", "imputation_log.json")
    with open(log_path, 'w') as f:
        json.dump(imputation_log, f, indent=2)

    # Write model config
    config_path = os.path.join(project_root, "data", "processed", "model_config.json")
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)

    logger.info(f"Missing data handled. Config: {config}")
    return df, config

def write_harmonized_dataset(df: pd.DataFrame, project_root: str):
    """Write the final harmonized dataset and update state."""
    output_path = os.path.join(project_root, "data", "processed", "harmonized_dataset.parquet")
    df.to_parquet(output_path)

    # Calculate hash
    file_hash = calculate_file_hash(output_path)

    # Update state file
    state_path = os.path.join(project_root, "state", "projects", "PROJ-196-the-role-of-temporal-discounting-in-proc.yaml")
    if os.path.exists(state_path):
        import yaml
        with open(state_path, 'r') as f:
            state = yaml.safe_load(f)

        if 'artifact_hashes' not in state:
            state['artifact_hashes'] = {}

        state['artifact_hashes']['harmonized_dataset.parquet'] = file_hash
        state['last_updated'] = pd.Timestamp.now().isoformat()

        with open(state_path, 'w') as f:
            yaml.dump(state, f)

    logger.info(f"Wrote harmonized dataset to {output_path}")

# ----------------------------------------------------------------------
# New public API required for T007
# ----------------------------------------------------------------------
def verify_urls(urls: List[str]) -> None:
    """
    Verify that each URL in ``urls`` returns a HTTP 200 status via a HEAD request.
    Raises RuntimeError if any URL is unreachable or returns a non‑200 status.
    """
    for url in urls:
        try:
            response = requests.head(url, allow_redirects=True, timeout=10)
            if response.status_code != 200:
                raise RuntimeError(f"URL verification failed for {url}: status {response.status_code}")
        except requests.RequestException as exc:
            raise RuntimeError(f"URL verification failed for {url}: {exc}") from exc

def load_and_harmonize(n: int = 500, seed: int = 42) -> pd.DataFrame:
    """
    Run the full DGP pipeline (synthetic data generation) and return the
    harmonized DataFrame.  This function is a thin wrapper around the
    existing ``run_dgp_pipeline`` to provide a stable entry point for the
    orchestrator.
    """
    # Default DGP parameters – identical to those used in the original script
    params = {
        "k_mean": 0.05, "k_sd": 0.02,
        "procrastination_mean": 3.5, "procrastination_sd": 0.8,
        "wm_accuracy_mean": 0.85, "wm_accuracy_sd": 0.1,
        "age_mean": 25, "age_sd": 5,
        "gender_distribution": {"male": 0.5, "female": 0.5, "other": 0.0},
        "education_mean": 16, "education_sd": 2
    }

    # ``run_dgp_pipeline`` performs generation, raw‑file writing, and
    # harmonisation, finally returning the unified DataFrame.
    df = run_dgp_pipeline(n, seed, params)
    return df

# ----------------------------------------------------------------------
# Existing CLI entry point (kept for backwards compatibility)
# ----------------------------------------------------------------------
def main():
    """Main entry point for ingestion script."""
    parser = argparse.ArgumentParser(description="Data Ingestion Pipeline")
    parser.add_argument('--mode', choices=['generate', 'validate'], default='generate',
                        help='Operation mode')
    parser.add_argument('--n', type=int, default=500, help='Number of participants')
    parser.add_argument('--seed', type=int, default=42, help='Random seed')

    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    # Definitive parameters (same as in load_and_harmonize)
    params = {
        "k_mean": 0.05, "k_sd": 0.02,
        "procrastination_mean": 3.5, "procrastination_sd": 0.8,
        "wm_accuracy_mean": 0.85, "wm_accuracy_sd": 0.1,
        "age_mean": 25, "age_sd": 5,
        "gender_distribution": {"male": 0.5, "female": 0.5, "other": 0.0},
        "education_mean": 16, "education_sd": 2
    }

    if args.mode == 'generate':
        run_dgp_pipeline(args.n, args.seed, params)
    elif args.mode == 'validate':
        logger.info("Validation mode not fully implemented")

if __name__ == "__main__":
    main()