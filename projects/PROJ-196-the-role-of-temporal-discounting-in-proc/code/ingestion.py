import os
import sys
import json
import numpy as np
import pandas as pd
from pathlib import Path
from scipy.optimize import curve_fit
from statsmodels.stats.diagnostic import het_breuschpagan
from statsmodels.stats.outliers_influence import variance_inflation_factor

# Import from project config
from config import get_project_root, get_random_state, get_config_value

def hyperbolic_function(t, k):
    """
    Hyperbolic discounting function: V = A / (1 + k*t)
    
    Args:
        t: Delay time
        k: Discount rate parameter
        
    Returns:
        Discounted value
    """
    return 1.0 / (1.0 + k * t)

def generate_delay_discounting_data(n_participants, random_state):
    """
    Generate synthetic delay discounting data.
    
    Args:
        n_participants: Number of participants
        random_state: Random state for reproducibility
        
    Returns:
        DataFrame with delay discounting data
    """
    rng = np.random.RandomState(random_state)
    
    participant_ids = [f"sub_{i:04d}" for i in range(1, n_participants + 1)]
    
    # Generate individual discount rates (log-normal distribution)
    log_k = rng.normal(loc=-2.0, scale=0.8, size=n_participants)
    k_values = np.exp(log_k)
    
    data = []
    delays = [1, 7, 30, 90, 365]  # Days
    
    for i, pid in enumerate(participant_ids):
        k = k_values[i]
        for delay in delays:
            # True indifference point based on hyperbolic model
            true_value = 100.0 / (1.0 + k * delay)
            
            # Add noise
            noise = rng.normal(0, 5.0)
            indifference = max(0, min(100, true_value + noise))
            
            data.append({
                'participant_id': pid,
                'delay_days': delay,
                'indifference_point': indifference,
                'k_individual': k
            })
    
    return pd.DataFrame(data)

def generate_procrastination_data(n_participants, random_state):
    """
    Generate synthetic procrastination scale data.
    
    Args:
        n_participants: Number of participants
        random_state: Random state for reproducibility
        
    Returns:
        DataFrame with procrastination scale data
    """
    rng = np.random.RandomState(random_state)
    
    participant_ids = [f"sub_{i:04d}" for i in range(1, n_participants + 1)]
    
    # Procrastination scale items (1-5 Likert)
    n_items = 10
    
    data = []
    for pid in participant_ids:
        # Generate individual procrastination tendency
        base_score = rng.normal(loc=3.0, scale=0.8)
        
        items = []
        for j in range(n_items):
            # Item response with some noise
            item_score = base_score + rng.normal(0, 0.5)
            item_score = max(1, min(5, round(item_score)))
            items.append(item_score)
        
        data.append({
            'participant_id': pid,
            **{f'item_{j+1}': items[j] for j in range(n_items)}
        })
    
    return pd.DataFrame(data)

def generate_nback_data(n_participants, random_state):
    """
    Generate synthetic n-back working memory task data.
    
    Args:
        n_participants: Number of participants
        random_state: Random state for reproducibility
        
    Returns:
        DataFrame with n-back task data
    """
    rng = np.random.RandomState(random_state)
    
    participant_ids = [f"sub_{i:04d}" for i in range(1, n_participants + 1)]
    
    data = []
    for pid in participant_ids:
        # Individual WM capacity parameter
        base_accuracy = rng.normal(loc=0.75, scale=0.12)
        base_rt = rng.normal(loc=600, scale=80)  # ms
        
        # 2-back condition
        acc_2back = max(0.3, min(0.95, base_accuracy + rng.normal(0, 0.05)))
        rt_2back = max(300, base_rt + rng.normal(0, 40))
        
        # 3-back condition (harder)
        acc_3back = max(0.25, min(0.90, base_accuracy - 0.10 + rng.normal(0, 0.05)))
        rt_3back = max(350, base_rt + 50 + rng.normal(0, 40))
        
        data.append({
            'participant_id': pid,
            'wm_accuracy_2back': round(acc_2back, 3),
            'wm_rt_2back': round(rt_2back, 1),
            'wm_accuracy_3back': round(acc_3back, 3),
            'wm_rt_3back': round(rt_3back, 1)
        })
    
    return pd.DataFrame(data)

def calculate_cronbach_alpha(dataframe, item_columns):
    """
    Calculate Cronbach's alpha for reliability.
    
    Args:
        dataframe: DataFrame containing item responses
        item_columns: List of column names for items
        
    Returns:
        Cronbach's alpha coefficient
    """
    items = dataframe[item_columns].values
    n_items = items.shape[1]
    n_participants = items.shape[0]
    
    # Calculate item variances
    item_variances = np.var(items, axis=0, ddof=1)
    
    # Calculate total score variance
    total_scores = np.sum(items, axis=1)
    total_variance = np.var(total_scores, ddof=1)
    
    if total_variance == 0:
        return 0.0
    
    # Cronbach's alpha formula
    alpha = (n_items / (n_items - 1)) * (1 - np.sum(item_variances) / total_variance)
    
    return alpha

def validate_dgp_config(config):
    """
    Validate DGP configuration parameters.
    
    Args:
        config: Dictionary of DGP parameters
        
    Returns:
        True if valid, raises SystemExit if invalid
    """
    required_keys = ['n_participants', 'reliability_target']
    
    for key in required_keys:
        if key not in config:
            print(f"CRITICAL: Missing required DGP config key: {key}")
            sys.exit(1)
    
    if config['n_participants'] <= 0:
        print("CRITICAL: n_participants must be positive")
        sys.exit(1)
    
    if config['reliability_target'] < 0 or config['reliability_target'] > 1:
        print("CRITICAL: reliability_target must be between 0 and 1")
        sys.exit(1)
    
    return True

def fit_hyperbolic_model(delays, indifference_points, random_state):
    """
    Fit hyperbolic discounting model to individual data.
    
    Args:
        delays: Array of delay times
        indifference_points: Array of indifference points
        random_state: Random state for reproducibility
        
    Returns:
        Fitted k parameter
    """
    try:
        # Initial guess for k
        p0 = [0.1]
        
        # Fit the model
        popt, pcov = curve_fit(
            hyperbolic_function, 
            delays, 
            indifference_points, 
            p0=p0,
            bounds=(0, np.inf)
        )
        
        return popt[0]
    except Exception as e:
        # Fallback: use mean of k_individual if available or estimate
        print(f"Warning: Model fitting failed for participant, using fallback. Error: {e}")
        return 0.01

def run_dgp_pipeline(n_participants, random_seed):
    """
    Run the complete DGP generation pipeline.
    
    Args:
        n_participants: Number of participants
        random_seed: Random seed for reproducibility
        
    Returns:
        Tuple of (delay_df, procrastination_df, nback_df)
    """
    rng = np.random.RandomState(random_seed)
    base_seed = rng.randint(0, 2**31 - 1)
    
    delay_df = generate_delay_discounting_data(n_participants, base_seed)
    procrastination_df = generate_procrastination_data(n_participants, base_seed + 1)
    nback_df = generate_nback_data(n_participants, base_seed + 2)
    
    return delay_df, procrastination_df, nback_df

def harmonize_datasets(delay_df, procrastination_df, nback_df):
    """
    Merge the three datasets by participant_id.
    
    Args:
        delay_df: Delay discounting DataFrame
        procrastination_df: Procrastination DataFrame
        nback_df: n-back DataFrame
        
    Returns:
        Merged DataFrame
    """
    # Calculate procrastination score (mean of items)
    item_cols = [col for col in procrastination_df.columns if col.startswith('item_')]
    procrastination_df['procrastination_score'] = procrastination_df[item_cols].mean(axis=1)
    
    # Merge datasets
    merged = delay_df.merge(procrastination_df, on='participant_id', how='inner')
    merged = merged.merge(nback_df, on='participant_id', how='inner')
    
    # Check for significant drop
    expected_n = len(delay_df)
    actual_n = len(merged)
    drop_rate = 1 - (actual_n / expected_n)
    
    if drop_rate > 0.10:
        print(f"Warning: {drop_rate*100:.1f}% of participants dropped during harmonization")
    
    return merged

def validate_core_constructs(df):
    """
    Validate that core constructs exist in the harmonized dataset.
    
    Args:
        df: Harmonized DataFrame
        
    Returns:
        True if valid, raises SystemExit if missing core constructs
    """
    required_cols = ['discount_rate_k', 'procrastination_score', 'wm_accuracy']
    
    for col in required_cols:
        if col not in df.columns:
            print(f"CRITICAL: Missing core construct: {col}")
            sys.exit(1)
        
        if df[col].isnull().sum() > 0:
            print(f"CRITICAL: Core construct {col} has missing values")
            sys.exit(1)
    
    return True

def handle_missing_data(df, config_path):
    """
    Handle missing data and write model config.
    
    Args:
        df: DataFrame to process
        config_path: Path to write model config
        
    Returns:
        Processed DataFrame
    """
    project_root = get_project_root()
    processed_dir = project_root / 'data' / 'processed'
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    # Check missing covariates
    covariates = ['age', 'gender', 'education']
    missing_rates = {}
    
    for col in covariates:
        if col in df.columns:
            missing_rates[col] = df[col].isnull().mean()
    
    reduced_model = False
    if any(rate > 0.10 for rate in missing_rates.values()):
        reduced_model = True
        # Write reduced model config
        config_data = {'reduced_model': True, 'excluded_covariates': []}
        for col, rate in missing_rates.items():
            if rate > 0.10:
                config_data['excluded_covariates'].append(col)
        
        with open(config_path, 'w') as f:
            json.dump(config_data, f, indent=2)
        print(f"Reduced model config written: {config_path}")
    
    # Impute or delete based on missingness
    if df.isnull().any().any():
        # Mean imputation for numeric, mode for categorical
        for col in df.columns:
            if df[col].isnull().any():
                if df[col].dtype in ['float64', 'int64']:
                    df[col].fillna(df[col].mean(), inplace=True)
                else:
                    df[col].fillna(df[col].mode()[0], inplace=True)
    
    return df

def write_harmonized_dataset(df, output_path):
    """
    Write the final harmonized dataset to parquet format.
    
    Args:
        df: Final harmonized DataFrame
        output_path: Path to output file
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    df.to_parquet(output_path, index=False)
    print(f"Harmonized dataset written to: {output_path}")
    return output_path

def main():
    """
    Main entry point for the ingestion pipeline.
    """
    project_root = get_project_root()
    raw_dir = project_root / 'data' / 'raw'
    processed_dir = project_root / 'data' / 'processed'
    
    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    # Get configuration
    config = get_config()
    n_participants = config.get('n_participants', 500)
    random_seed = config.get('random_seed', 42)
    
    print(f"Starting DGP pipeline with {n_participants} participants, seed={random_seed}")
    
    # Run DGP
    delay_df, procrastination_df, nback_df = run_dgp_pipeline(n_participants, random_seed)
    
    # Write raw files
    delay_path = raw_dir / 'delay_discounting.csv'
    procrastination_path = raw_dir / 'procrastination.csv'
    nback_path = raw_dir / 'nback.csv'
    
    delay_df.to_csv(delay_path, index=False)
    procrastination_df.to_csv(procrastination_path, index=False)
    nback_df.to_csv(nback_path, index=False)
    
    print(f"Raw data files written to {raw_dir}")
    
    # Check reliability
    item_cols = [col for col in procrastination_df.columns if col.startswith('item_')]
    alpha = calculate_cronbach_alpha(procrastination_df, item_cols)
    print(f"Cronbach's Alpha: {alpha:.3f}")
    
    if alpha < 0.7:
        print("CRITICAL: Synthetic data reliability below threshold (alpha < 0.7)")
        sys.exit(1)
    
    # Harmonize
    merged_df = harmonize_datasets(delay_df, procrastination_df, nback_df)
    
    # Calculate discount rate k for each participant
    delays = merged_df['delay_days'].unique()
    k_values = []
    
    for pid in merged_df['participant_id'].unique():
        participant_data = merged_df[merged_df['participant_id'] == pid]
        p_delays = participant_data['delay_days'].values
        p_values = participant_data['indifference_point'].values
        
        k = fit_hyperbolic_model(p_delays, p_values, random_seed)
        k_values.append(k)
    
    merged_df['discount_rate_k'] = k_values
    
    # Set working memory accuracy (average of 2-back and 3-back)
    merged_df['wm_accuracy'] = merged_df[['wm_accuracy_2back', 'wm_accuracy_3back']].mean(axis=1)
    
    # Validate core constructs
    validate_core_constructs(merged_df)
    
    # Handle missing data
    config_path = processed_dir / 'model_config.json'
    merged_df = handle_missing_data(merged_df, config_path)
    
    # Write final dataset
    output_path = processed_dir / 'harmonized_dataset.parquet'
    write_harmonized_dataset(merged_df, output_path)
    
    print("Pipeline completed successfully!")
    return merged_df

if __name__ == "__main__":
    main()
