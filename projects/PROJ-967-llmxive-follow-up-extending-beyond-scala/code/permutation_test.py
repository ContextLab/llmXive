"""
Permutation Test Implementation for US3.

Computes the p-value by permuting the target variable (y_train) and
comparing the resulting R² scores against the observed R².
"""
import argparse
import json
import logging
import os
import sys
import pickle
import numpy as np
from pathlib import Path

# Import existing project utilities
# Note: We assume train.py or evaluate.py logic is available or we re-implement minimal R2 here
# Since the API surface shows 'from train import ... calculate_permutation_pvalue',
# but that function is what we are implementing for T030a, we will implement it here
# and ensure it can be imported by evaluate.py or train.py if needed, 
# or we implement the logic inline as requested by T030a.

# However, the API surface lists:
# code/train.py: calculate_permutation_pvalue
# code/evaluate.py: calculate_permutation_pvalue
# code/integrate_train_eval.py: calculate_permutation_pvalue
# code/permutation_test.py: calculate_permutation_pvalue (this file)

# To avoid circular imports and satisfy T030a (Implement permutation test),
# we implement the core logic here.

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

def load_features(features_path):
    """Load the processed features from parquet/CSV."""
    import pandas as pd
    if not os.path.exists(features_path):
        raise FileNotFoundError(f"Features file not found: {features_path}")
    # Assuming parquet based on previous tasks (T024, T025)
    if features_path.endswith('.parquet'):
        return pd.read_parquet(features_path)
    elif features_path.endswith('.csv'):
        return pd.read_csv(features_path)
    else:
        raise ValueError(f"Unsupported file format: {features_path}")

def load_split_config(split_config_path):
    """Load the train/test split configuration."""
    if not os.path.exists(split_config_path):
        raise FileNotFoundError(f"Split config not found: {split_config_path}")
    with open(split_config_path, 'r') as f:
        return json.load(f)

def load_model(model_path):
    """Load the trained model."""
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model file not found: {model_path}")
    with open(model_path, 'rb') as f:
        return pickle.load(f)

def r2_score(y_true, y_pred):
    """Calculate R² score manually to avoid sklearn dependency if not available, 
    though sklearn is likely installed. Using numpy for robustness."""
    y_true = np.array(y_true)
    y_pred = np.array(y_pred)
    ss_res = np.sum((y_true - y_pred) ** 2)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
    if ss_tot == 0:
        return 0.0
    return 1 - (ss_res / ss_tot)

def calculate_permutation_pvalue(X_train, y_train, model, n_permutations=1000, random_state=42):
    """
    Calculate the permutation test p-value.
    
    1. Compute observed R² on the original (X_train, y_train).
    2. Permute y_train n_permutations times.
    3. For each permutation, compute R².
    4. p-value = (count of permuted R² >= observed R²) / n_permutations.
    
    Args:
        X_train: Feature matrix (numpy array or pandas DataFrame).
        y_train: Target vector (numpy array or pandas Series).
        model: Trained scikit-learn compatible model.
        n_permutations: Number of permutations.
        random_state: Random seed for reproducibility.
        
    Returns:
        float: The calculated p-value.
    """
    np.random.seed(random_state)
    X_train = np.array(X_train)
    y_train = np.array(y_train)
    
    # 1. Compute observed R²
    y_pred_observed = model.predict(X_train)
    r2_observed = r2_score(y_train, y_pred_observed)
    logging.info(f"Observed R²: {r2_observed:.4f}")
    
    # 2. Permutation loop
    count_ge_observed = 0
    
    for i in range(n_permutations):
        # Permute y_train
        y_permuted = y_train.copy()
        np.random.shuffle(y_permuted)
        
        # Compute R² on permuted data
        y_pred_permuted = model.predict(X_train)
        r2_permuted = r2_score(y_permuted, y_pred_permuted)
        
        if r2_permuted >= r2_observed:
            count_ge_observed += 1
        
        if (i + 1) % 100 == 0:
            logging.debug(f"Permutation {i+1}/{n_permutations} completed.")

    # 3. Calculate p-value
    p_value = count_ge_observed / n_permutations
    logging.info(f"Permutation test completed. P-value: {p_value:.4f}")
    
    return p_value

def run_permutation_test(args):
    """
    Main entry point for the permutation test task.
    """
    logger = setup_logging()
    
    # Load inputs
    try:
        df = load_features(args.features_path)
        split_config = load_split_config(args.split_config_path)
        model = load_model(args.model_path)
    except Exception as e:
        logger.error(f"Failed to load required artifacts: {e}")
        sys.exit(1)
    
    # Extract training data based on split config
    # The split config should contain indices or a boolean mask for the train set.
    # Assuming split_config has 'train_indices' or similar.
    # If not, we might need to re-split, but T027a says "Store split indices".
    
    if 'train_indices' not in split_config:
        logger.error("Split config missing 'train_indices'. Cannot run permutation test.")
        sys.exit(1)
        
    train_indices = split_config['train_indices']
    
    # Select training features and target
    # Assuming feature columns are all except 'fidelity_loss' and metadata
    # We need to know the target column name. T024 says it's 'fidelity_loss'.
    target_col = 'fidelity_loss'
    feature_cols = [col for col in df.columns if col != target_col and col not in ['sample_id', 'excluded_reason']]
    
    X_train = df.loc[train_indices, feature_cols].values
    y_train = df.loc[train_indices, target_col].values
    
    logger.info(f"Training data shape: X={X_train.shape}, y={y_train.shape}")
    
    if len(y_train) < 2:
        logger.error("Not enough training samples for permutation test.")
        sys.exit(1)
    
    # Run permutation test
    p_value = calculate_permutation_pvalue(
        X_train, 
        y_train, 
        model, 
        n_permutations=args.n_permutations, 
        random_state=args.random_state
    )
    
    # Save results
    result = {
        "p_value_permutation": float(p_value),
        "n_permutations": args.n_permutations,
        "random_state": args.random_state,
        "status": "success"
    }
    
    output_path = Path(args.output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)
    
    logger.info(f"Permutation test results saved to {args.output_path}")
    return result

def parse_args():
    parser = argparse.ArgumentParser(description="Run permutation test for model significance.")
    parser.add_argument("--features-path", type=str, default="data/processed/cleaned_data.parquet",
                        help="Path to the cleaned features dataset.")
    parser.add_argument("--split-config-path", type=str, default="data/processed/split_config.json",
                        help="Path to the split configuration JSON.")
    parser.add_argument("--model-path", type=str, default="results/model.pkl",
                        help="Path to the trained model pickle file.")
    parser.add_argument("--output-path", type=str, default="results/permutation_test.json",
                        help="Path to save the permutation test results.")
    parser.add_argument("--n-permutations", type=int, default=1000,
                        help="Number of permutations to run.")
    parser.add_argument("--random-state", type=int, default=42,
                        help="Random seed for reproducibility.")
    return parser.parse_args()

def main():
    args = parse_args()
    run_permutation_test(args)

if __name__ == "__main__":
    main()
