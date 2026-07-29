"""
Ingestion module for the Temporal Discounting in Procrastination project.
Handles DGP generation, validation, harmonization, and dataset writing.
"""
import os
import sys
import json
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

# Import from local config
from config import get_config, get_project_root, get_random_state, get_config_value
from utils.checksum import update_artifact_hash

# Constants
MIN_CRONBACH_ALPHA = 0.7
MAX_MISSING_RATE = 0.10

def validate_dgp_config(config: Dict[str, Any]) -> None:
    """
    Validates the DGP configuration against schema and reliability targets.
    Raises SystemExit(1) if invalid.
    """
    required_keys = ['n_participants', 'discounting_params', 'procrastination_params', 'wm_params']
    for key in required_keys:
        if key not in config:
            print(f"CRITICAL: Missing DGP config key: {key}")
            sys.exit(1)
    
    if config['n_participants'] < 10:
        print("CRITICAL: n_participants must be >= 10")
        sys.exit(1)
    
    print("DGP Configuration validated successfully.")

def calculate_cronbach_alpha(data: pd.DataFrame, item_columns: List[str]) -> float:
    """
    Calculates Cronbach's alpha for a set of item columns.
    """
    if len(item_columns) < 2:
        return 0.0
    
    # Ensure only numeric columns
    numeric_data = data[item_columns].dropna()
    if numeric_data.empty:
        return 0.0
    
    n_items = len(item_columns)
    n_participants = len(numeric_data)
    
    if n_participants < 2:
        return 0.0
    
    # Variance of total score
    total_scores = numeric_data.sum(axis=1)
    var_total = total_scores.var(ddof=1)
    
    if var_total == 0:
        return 0.0
    
    # Sum of variances of individual items
    var_items = numeric_data.var(axis=0, ddof=1).sum()
    
    if var_items == 0:
        return 0.0
    
    alpha = (n_items / (n_items - 1)) * (1 - (var_items / var_total))
    return alpha

def generate_delay_discounting_data(n: int, rng: np.random.Generator, params: Dict[str, Any]) -> pd.DataFrame:
    """
    Generates synthetic delay discounting data.
    Returns a DataFrame with participant_id, delay, amount, and choice.
    """
    participant_ids = [f"PID_{i:04d}" for i in range(n)]
    
    # Simulate indifference points based on hyperbolic model with noise
    # V = A / (1 + k*D) -> k is the discount rate
    delays = [1, 7, 30, 90, 180, 365] # days
    base_amount = 100.0
    
    rows = []
    for pid in participant_ids:
        # Individual k drawn from log-normal distribution
        k = rng.lognormal(mean=params['k_mean'], sigma=params['k_sigma'])
        
        for delay in delays:
            # Indifference point approximation with noise
            # Ideal V = 100 / (1 + k*delay)
            ideal_v = base_amount / (1 + k * delay)
            noise = rng.normal(0, params['noise_std'])
            observed_v = max(1, min(base_amount, ideal_v + noise))
            
            rows.append({
                'participant_id': pid,
                'delay': delay,
                'amount': base_amount,
                'indifference_point': observed_v,
                'k_true': k
            })
    
    df = pd.DataFrame(rows)
    return df

def generate_procrastination_data(n: int, rng: np.random.Generator, params: Dict[str, Any]) -> pd.DataFrame:
    """
    Generates synthetic procrastination scale data.
    Returns a DataFrame with participant_id and scale item responses.
    """
    participant_ids = [f"PID_{i:04d}" for i in range(n)]
    items = [f"PROC_ITEM_{i}" for i in range(1, params['n_items'] + 1)]
    
    rows = []
    for pid in participant_ids:
        # True latent trait
        trait = rng.normal(loc=params['trait_mean'], scale=params['trait_std'])
        
        responses = []
        for item in items:
            # Item response with noise
            score = int(np.clip(trait + rng.normal(0, params['item_noise']), 1, 5))
            responses.append(score)
        
        row = {'participant_id': pid}
        for i, item in enumerate(items):
            row[item] = responses[i]
        rows.append(row)
    
    return pd.DataFrame(rows)

def generate_nback_data(n: int, rng: np.random.Generator, params: Dict[str, Any]) -> pd.DataFrame:
    """
    Generates synthetic n-back working memory task data.
    Returns a DataFrame with participant_id, accuracy, and reaction time.
    """
    participant_ids = [f"PID_{i:04d}" for i in range(n)]
    
    rows = []
    for pid in participant_ids:
        # Individual WM capacity
        capacity = rng.normal(loc=params['capacity_mean'], scale=params['capacity_std'])
        
        # Accuracy and RT based on capacity (simplified)
        acc = np.clip(0.5 + 0.4 * (capacity - params['capacity_mean']) / params['capacity_std'] + rng.normal(0, 0.05), 0, 1)
        rt = np.clip(params['base_rt'] - 200 * (capacity - params['capacity_mean']) / params['capacity_std'] + rng.normal(0, 50), 200, 2000)
        
        rows.append({
            'participant_id': pid,
            'wm_accuracy': acc,
            'wm_rt': rt,
            'wm_load': params['n_back_level']
        })
    
    return pd.DataFrame(rows)

def harmonize_datasets(delay_df: pd.DataFrame, proc_df: pd.DataFrame, nback_df: pd.DataFrame) -> pd.DataFrame:
    """
    Merges the three datasets on participant_id.
    Checks for >10% drop due to ID mismatch.
    """
    # Calculate expected participants
    all_ids = set(delay_df['participant_id']) | set(proc_df['participant_id']) | set(nback_df['participant_id'])
    expected_count = len(all_ids)
    
    # Merge
    merged = delay_df.merge(proc_df, on='participant_id', how='inner')
    merged = merged.merge(nback_df, on='participant_id', how='inner')
    
    actual_count = len(merged)
    drop_rate = (expected_count - actual_count) / expected_count if expected_count > 0 else 0
    
    if drop_rate > MAX_MISSING_RATE:
        print(f"WARNING: >{int(drop_rate*100)}% of participants dropped due to ID mismatch. ({expected_count} -> {actual_count})")
        # In a strict pipeline, we might halt, but the task says "flag/halt if exceeded"
        # For this implementation, we proceed but log the warning.
        # If strict halting is required:
        # sys.exit(1)
    
    print(f"Harmonization complete. Participants: {actual_count} (Drop rate: {drop_rate:.2%})")
    return merged

def fit_hyperbolic_model(df: pd.DataFrame) -> pd.DataFrame:
    """
    Fits the hyperbolic model to calculate discount_rate_k for each participant.
    This function is expected to be called after harmonization.
    It calculates 'discount_rate_k' per participant.
    """
    from scipy.optimize import curve_fit
    
    def hyperbolic_func(x, k):
        # x is delay, returns indifference point as fraction of amount (assuming amount=1)
        # V = 1 / (1 + k*x)
        return 1.0 / (1.0 + k * x)
    
    results = []
    
    for pid, group in df.groupby('participant_id'):
        delays = group['delay'].values
        # Normalize indifference points by amount
        indiff_points = group['indifference_point'].values / group['amount'].values
        
        try:
            # Initial guess for k
            p0 = [0.1]
            popt, _ = curve_fit(hyperbolic_func, delays, indiff_points, p0=p0, maxfev=10000)
            k_est = popt[0]
            
            # Ensure k is positive
            if k_est < 0:
                k_est = 0.0
                
            results.append({'participant_id': pid, 'discount_rate_k': k_est})
        except Exception as e:
            print(f"Warning: Could not fit model for {pid}: {e}")
            results.append({'participant_id': pid, 'discount_rate_k': np.nan})
    
    return pd.DataFrame(results)

def validate_core_constructs(df: pd.DataFrame) -> None:
    """
    Checks for missing core constructs in the harmonized dataset.
    Raises SystemExit(1) if any are missing.
    """
    core_cols = ['discount_rate_k', 'procrastination_score', 'wm_accuracy']
    
    # Calculate procrastination score if not present (mean of items)
    if 'procrastination_score' not in df.columns:
        proc_items = [c for c in df.columns if c.startswith('PROC_ITEM_')]
        if proc_items:
            df['procrastination_score'] = df[proc_items].mean(axis=1)
        else:
            # If items are not merged correctly, this will fail validation later
            pass
    
    for col in core_cols:
        if col not in df.columns:
            print(f"CRITICAL: Missing core construct: {col}")
            sys.exit(1)
        
        if df[col].isnull().any():
            # For the purpose of this check, if the column exists but has NaNs,
            # it might be acceptable depending on imputation strategy (T016).
            # However, T015b says "Missing core constructs".
            # We assume T016 handles NaNs, but T015b checks for existence of the column and non-null values in key predictors.
            # If the column exists but is all NaN, that's a failure.
            if df[col].isnull().all():
                print(f"CRITICAL: Missing core construct: {col}")
                sys.exit(1)
    
    print("Core constructs validated.")

def handle_missing_data(df: pd.DataFrame, config_path: Path) -> pd.DataFrame:
    """
    Handles missing data for covariates.
    If >10% missing, writes model_config.json with reduced_model: true.
    Otherwise performs listwise deletion or mean imputation.
    """
    covariates = ['age', 'gender', 'education']
    missing_counts = {}
    total_rows = len(df)
    
    for col in covariates:
        if col in df.columns:
            missing_counts[col] = df[col].isnull().sum()
        else:
            missing_counts[col] = total_rows # Treat missing column as 100% missing
    
    reduced_model = False
    reduced_cols = []
    
    for col, count in missing_counts.items():
        rate = count / total_rows
        if rate > MAX_MISSING_RATE:
            reduced_model = True
            reduced_cols.append(col)
            print(f"Warning: {col} missing >10% ({rate:.2%}). Excluding from model.")
    
    if reduced_model:
        config = {'reduced_model': True, 'excluded_covariates': reduced_cols}
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        print(f"Model config written: {config_path}")
        
        # Remove excluded columns from df for downstream
        df = df.drop(columns=reduced_cols, errors='ignore')
    else:
        # Mean imputation for numeric, mode for categorical
        for col in covariates:
            if col in df.columns:
                if df[col].dtype in ['float64', 'int64']:
                    df[col] = df[col].fillna(df[col].mean())
                else:
                    df[col] = df[col].fillna(df[col].mode()[0])
        
        # Write config indicating full model
        config = {'reduced_model': False, 'excluded_covariates': []}
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
    
    # Listwise deletion for any remaining NaNs in core constructs
    core_cols = ['discount_rate_k', 'procrastination_score', 'wm_accuracy']
    present_core = [c for c in core_cols if c in df.columns]
    if present_core:
        df = df.dropna(subset=present_core)
    
    return df

def write_harmonized_dataset(df: pd.DataFrame, output_path: Path) -> None:
    """
    Writes the final harmonized dataset to a Parquet file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(output_path, index=False)
    print(f"Harmonized dataset written to {output_path}")
    
    # Update checksums
    try:
        from utils.checksum import update_artifact_hash
        update_artifact_hash(str(output_path))
    except ImportError:
        print("Warning: Could not update artifact hash (utils.checksum not available)")

def run_dgp_pipeline(config: Dict[str, Any], output_dir: Path) -> pd.DataFrame:
    """
    Runs the full DGP pipeline: generate, validate, harmonize, fit, write.
    """
    rng = get_random_state()
    n = config['n_participants']
    
    # 1. Generate Data
    print("Generating delay discounting data...")
    delay_df = generate_delay_discounting_data(n, rng, config['discounting_params'])
    delay_df.to_csv(output_dir / 'delay_discounting.csv', index=False)
    
    print("Generating procrastination data...")
    proc_df = generate_procrastination_data(n, rng, config['procrastination_params'])
    proc_df.to_csv(output_dir / 'procrastination.csv', index=False)
    
    print("Generating n-back data...")
    nback_df = generate_nback_data(n, rng, config['wm_params'])
    nback_df.to_csv(output_dir / 'nback.csv', index=False)
    
    # 2. Validate Reliability (T014b)
    print("Checking reliability...")
    proc_items = [c for c in proc_df.columns if c.startswith('PROC_ITEM_')]
    alpha = calculate_cronbach_alpha(proc_df, proc_items)
    if alpha < MIN_CRONBACH_ALPHA:
        print(f"CRITICAL: Synthetic data reliability below threshold (alpha < {MIN_CRONBACH_ALPHA}). Alpha={alpha:.4f}")
        sys.exit(1)
    print(f"Cronbach's Alpha: {alpha:.4f}")
    
    # 3. Harmonize
    print("Harmonizing datasets...")
    merged_df = harmonize_datasets(delay_df, proc_df, nback_df)
    
    # 4. Fit Model (T015c) - calculate discount_rate_k
    # Note: The DGP already has k_true, but we must fit it from the data to simulate real analysis
    print("Fitting hyperbolic model...")
    fitted_df = fit_hyperbolic_model(merged_df)
    
    # Merge fitted k back into main df
    merged_df = merged_df.merge(fitted_df[['participant_id', 'discount_rate_k']], on='participant_id', how='left')
    
    # 5. Validate Core Constructs (T015b)
    print("Validating core constructs...")
    validate_core_constructs(merged_df)
    
    # 6. Handle Missing Data (T016)
    print("Handling missing data...")
    config_path = output_dir.parent / 'model_config.json'
    final_df = handle_missing_data(merged_df, config_path)
    
    # 7. Write Dataset (T018)
    print("Writing final dataset...")
    write_harmonized_dataset(final_df, output_dir / 'harmonized_dataset.parquet')
    
    return final_df

def main():
    """
    Entry point for the DGP pipeline.
    """
    # Load config
    config = get_config()
    project_root = get_project_root()
    
    # Ensure directories
    raw_dir = project_root / 'data' / 'raw'
    processed_dir = project_root / 'data' / 'processed'
    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    # Validate config
    validate_dgp_config(config['dgp'])
    
    # Run pipeline
    run_dgp_pipeline(config['dgp'], raw_dir)

if __name__ == '__main__':
    main()
