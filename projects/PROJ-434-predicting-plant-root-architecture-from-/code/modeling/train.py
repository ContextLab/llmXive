import os
import sys
import json
import logging
import pickle
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import LeaveOneGroupOut, StratifiedKFold
from sklearn.metrics import r2_score, mean_squared_error
from sklearn.preprocessing import LabelEncoder

# Local imports from project API
from utils.config import load_environment, get_env
from utils.exceptions import DataQualityError
from utils.stats import permutation_test, stratified_permutation_test, calculate_metrics

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
DEFAULT_RANDOM_SEED = 42
DEFAULT_PERMUTATION_ITERATIONS = 1000

def preprocess_data(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series, np.ndarray]:
    """
    Preprocess the merged dataset for modeling.
    Returns: X, y, groups (species), encoded_species
    """
    logger.info("Preprocessing data...")
    
    # Drop rows with missing values in predictors or targets
    # Assuming predictors are N, P, K, pH and targets are root traits
    # We need to identify columns dynamically or assume standard names
    # Based on tasks.md, we have soil nutrients (N, P, K, pH) and root traits
    
    # Identify numeric columns for predictors (soil)
    soil_cols = ['N', 'P', 'K', 'pH']
    # Check if these columns exist
    missing_cols = [col for col in soil_cols if col not in df.columns]
    if missing_cols:
        raise DataQualityError(f"Missing required soil columns: {missing_cols}")
    
    # Identify target columns (root traits) - assume 'root_depth' and 'root_mass' or similar
    # Based on context, let's assume generic trait columns
    trait_cols = [col for col in df.columns if 'root' in col.lower() or 'trait' in col.lower()]
    if not trait_cols:
        # Fallback: try common names
        trait_cols = ['root_depth', 'root_mass', 'total_root_length']
        trait_cols = [col for col in trait_cols if col in df.columns]
    
    if not trait_cols:
        raise DataQualityError("No root trait columns found in dataset")
    
    # Use the first trait column for this implementation (or handle multiple)
    # For simplicity, we'll process one target at a time or aggregate
    # Let's assume we're predicting 'root_depth' as primary target
    target_col = trait_cols[0]
    
    # Drop rows with NaN in predictors or target
    valid_mask = df[soil_cols + [target_col]].notna().all(axis=1)
    df_clean = df[valid_mask].copy()
    
    if len(df_clean) == 0:
        raise DataQualityError("No valid rows after cleaning")
    
    # Encode species
    species_col = 'species_name' if 'species_name' in df.columns else 'species'
    if species_col not in df_clean.columns:
        raise DataQualityError("Species column not found")
    
    le = LabelEncoder()
    df_clean['species_encoded'] = le.fit_transform(df_clean[species_col])
    groups = df_clean['species_encoded'].values
    
    X = df_clean[soil_cols]
    y = df_clean[target_col]
    
    logger.info(f"Preprocessed {len(X)} rows, {len(soil_cols)} features, target: {target_col}")
    return X, y, groups, le, target_col

def train_model(X: pd.DataFrame, y: pd.Series, random_state: int = DEFAULT_RANDOM_SEED) -> RandomForestRegressor:
    """Train a Random Forest model."""
    model = RandomForestRegressor(
        n_estimators=100,
        random_state=random_state,
        n_jobs=-1
    )
    model.fit(X, y)
    return model

def run_loso_cv(X: pd.DataFrame, y: pd.Series, groups: np.ndarray, 
                random_state: int = DEFAULT_RANDOM_SEED) -> Dict[str, Any]:
    """
    Run Leave-One-Species-Out Cross-Validation.
    Returns metrics dictionary.
    """
    logger.info("Running LOSO Cross-Validation...")
    
    logo = LeaveOneGroupOut()
    r2_scores = []
    rmse_scores = []
    fold_results = []
    
    for train_idx, test_idx in logo.split(X, y, groups):
        X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
        y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
        
        model = train_model(X_train, y_train, random_state)
        y_pred = model.predict(X_test)
        
        r2 = r2_score(y_test, y_pred)
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        
        r2_scores.append(r2)
        rmse_scores.append(rmse)
        
        fold_results.append({
            'fold': len(r2_scores),
            'r2': r2,
            'rmse': rmse
        })
    
    return {
        'r2_scores': r2_scores,
        'rmse_scores': rmse_scores,
        'mean_r2': float(np.mean(r2_scores)),
        'mean_rmse': float(np.mean(rmse_scores)),
        'r2_std': float(np.std(r2_scores)),
        'per_fold': fold_results
    }

def run_stratified_cv(X: pd.DataFrame, y: pd.Series, groups: np.ndarray,
                     n_splits: int = 5, random_state: int = DEFAULT_RANDOM_SEED) -> Dict[str, Any]:
    """
    Run Stratified k-Fold Cross-Validation (by species).
    """
    logger.info(f"Running Stratified {n_splits}-Fold Cross-Validation...")
    
    # Create species labels for stratification
    # We need to map groups back to species names for stratification
    # Assuming groups are already encoded, we can use them directly
    skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=random_state)
    
    r2_scores = []
    rmse_scores = []
    
    for train_idx, test_idx in skf.split(X, y, groups):
        X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
        y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
        
        model = train_model(X_train, y_train, random_state)
        y_pred = model.predict(X_test)
        
        r2_scores.append(r2_score(y_test, y_pred))
        rmse_scores.append(np.sqrt(mean_squared_error(y_test, y_pred)))
    
    return {
        'r2_scores': r2_scores,
        'rmse_scores': rmse_scores,
        'mean_r2': float(np.mean(r2_scores)),
        'mean_rmse': float(np.mean(rmse_scores)),
        'r2_std': float(np.std(r2_scores))
    }

def run_nested_permutation_tests(X: pd.DataFrame, y: pd.Series, groups: np.ndarray,
                                 n_iterations: int = DEFAULT_PERMUTATION_ITERATIONS,
                                 random_state: int = DEFAULT_RANDOM_SEED) -> Dict[str, Any]:
    """
    Execute nested permutation tests as per T022.
    
    For Model A (Soil-Only): permute target variable within training folds.
    For Model B (Soil+Species): permute soil features (N, P, K, pH) stratified by species within training folds.
    
    Returns distribution of R² scores.
    """
    logger.info(f"Running nested permutation tests with {n_iterations} iterations...")
    
    logo = LeaveOneGroupOut()
    
    # Store distributions for both models
    model_a_r2_dist = []  # Permute target
    model_b_r2_dist = []  # Permute soil features stratified by species
    
    # Get original LOSO scores for reference
    original_scores = []
    
    for train_idx, test_idx in logo.split(X, y, groups):
        X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
        y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
        
        # Train original model
        original_model = train_model(X_train, y_train, random_state)
        y_pred_orig = original_model.predict(X_test)
        original_r2 = r2_score(y_test, y_pred_orig)
        original_scores.append(original_r2)
        
        # --- Model A: Permute target within training fold ---
        # We permute y_train and re-evaluate
        permuted_r2_a = []
        for _ in range(n_iterations):
            # Permute target within training set
            y_train_perm = y_train.sample(frac=1, random_state=random_state + _).reset_index(drop=True)
            model_a_perm = train_model(X_train, y_train_perm, random_state)
            y_pred_perm = model_a_perm.predict(X_test)
            r2_perm = r2_score(y_test, y_pred_perm)
            permuted_r2_a.append(r2_perm)
        
        model_a_r2_dist.append(permuted_r2_a)
        
        # --- Model B: Permute soil features stratified by species ---
        # This is more complex: we need to permute within species groups in training set
        # Get species indices for training set
        train_species = groups[train_idx]
        unique_species = np.unique(train_species)
        
        X_train_perm_list = []
        for species in unique_species:
            species_mask = train_species == species
            X_species = X_train.iloc[species_mask]
            # Permute rows within this species group
            X_species_perm = X_species.sample(frac=1, random_state=random_state + _).reset_index(drop=True)
            X_train_perm_list.append(X_species_perm)
        
        X_train_perm = pd.concat(X_train_perm_list, ignore_index=True)
        
        permuted_r2_b = []
        for _ in range(n_iterations):
            # Re-permute for each iteration
            X_train_perm_iter = X_train_perm.copy()
            for species in unique_species:
                species_mask = groups[train_idx] == species
                # Actually, we need to re-do the permutation logic per iteration
                # Let's redo properly
                pass
            
            # Simpler approach: permute the entire X_train but maintain species structure
            # Actually, the requirement is to permute features stratified by species
            # This means for each species, we shuffle the rows
            X_train_perm_iter = pd.DataFrame()
            for species in unique_species:
                species_mask = train_species == species
                X_species = X_train.iloc[species_mask]
                X_species_perm = X_species.sample(frac=1, random_state=random_state + _).reset_index(drop=True)
                X_train_perm_iter = pd.concat([X_train_perm_iter, X_species_perm], ignore_index=True)
            
            model_b_perm = train_model(X_train_perm_iter, y_train, random_state)
            y_pred_perm_b = model_b_perm.predict(X_test)
            r2_perm_b = r2_score(y_test, y_pred_perm_b)
            permuted_r2_b.append(r2_perm_b)
        
        model_b_r2_dist.append(permuted_r2_b)
    
    # Flatten distributions
    model_a_flat = [r for fold in model_a_r2_dist for r in fold]
    model_b_flat = [r for fold in model_b_r2_dist for r in fold]
    
    return {
        'model_a': {
            'distribution': model_a_flat,
            'mean': float(np.mean(model_a_flat)),
            'std': float(np.std(model_a_flat)),
            'iterations_per_fold': n_iterations,
            'n_folds': len(model_a_r2_dist)
        },
        'model_b': {
            'distribution': model_b_flat,
            'mean': float(np.mean(model_b_flat)),
            'std': float(np.std(model_b_flat)),
            'iterations_per_fold': n_iterations,
            'n_folds': len(model_b_r2_dist)
        },
        'original_mean_r2': float(np.mean(original_scores)),
        'n_iterations': n_iterations,
        'random_seed': random_state
    }

def calculate_p_value(original_score: float, permuted_scores: List[float]) -> float:
    """
    Calculate p-value for permutation test.
    p = (number of permuted scores >= original) / total permutations
    """
    count = sum(1 for score in permuted_scores if score >= original_score)
    return count / len(permuted_scores)

def enforce_sc002(original_r2: float, permuted_distributions: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enforce SC-002 compliance: ΔR² ≥ 0.05 AND p < 0.05.
    Returns status dictionary.
    """
    logger.info("Enforcing SC-002 compliance...")
    
    # Calculate delta R2 for Model A (target permutation)
    # The original score should be compared against the permuted distribution
    # For Model A: we permuted the target, so the permuted scores should be low (near 0)
    # Original R2 should be significantly higher than permuted R2s
    
    model_a_dist = permuted_distributions['model_a']['distribution']
    model_b_dist = permuted_distributions['model_b']['distribution']
    
    # Calculate p-values
    p_val_a = calculate_p_value(original_r2, model_a_dist)
    p_val_b = calculate_p_value(original_r2, model_b_dist)
    
    # Calculate delta R2 (original - mean of permuted)
    delta_r2_a = original_r2 - np.mean(model_a_dist)
    delta_r2_b = original_r2 - np.mean(model_b_dist)
    
    # SC-002: delta R2 >= 0.05 AND p < 0.05
    # We check both models, but Model B is the primary
    pass_a = delta_r2_a >= 0.05 and p_val_a < 0.05
    pass_b = delta_r2_b >= 0.05 and p_val_b < 0.05
    
    return {
        'model_a': {
            'delta_r2': float(delta_r2_a),
            'p_value': float(p_val_a),
            'pass': bool(pass_a)
        },
        'model_b': {
            'delta_r2': float(delta_r2_b),
            'p_value': float(p_val_b),
            'pass': bool(pass_b)
        },
        'overall_pass': bool(pass_a and pass_b),
        'original_r2': float(original_r2)
    }

def main():
    """Main entry point for T022: Nested Permutation Tests."""
    logger.info("Starting T022: Nested Permutation Tests")
    
    # Load configuration
    config = load_environment()
    random_seed = config.get('RANDOM_SEED', DEFAULT_RANDOM_SEED)
    n_iterations = config.get('PERMUTATION_ITERATIONS', DEFAULT_PERMUTATION_ITERATIONS)
    
    # Set random seed for reproducibility
    np.random.seed(random_seed)
    
    # Load merged dataset
    merged_data_path = Path('data/processed/merged_dataset.csv')
    if not merged_data_path.exists():
        raise DataQualityError(f"Merged dataset not found at {merged_data_path}")
    
    df = pd.read_csv(merged_data_path)
    logger.info(f"Loaded {len(df)} rows from {merged_data_path}")
    
    # Preprocess data
    X, y, groups, le, target_col = preprocess_data(df)
    
    # Run original LOSO CV to get baseline R2
    loso_results = run_loso_cv(X, y, groups, random_seed)
    original_r2 = loso_results['mean_r2']
    logger.info(f"Original LOSO Mean R2: {original_r2:.4f}")
    
    # Run nested permutation tests
    permutation_results = run_nested_permutation_tests(
        X, y, groups, 
        n_iterations=n_iterations, 
        random_state=random_seed
    )
    
    # Write permutation distributions to artifacts
    artifacts_dir = Path('artifacts')
    artifacts_dir.mkdir(exist_ok=True)
    
    output_path = artifacts_dir / 'permutation_distributions.json'
    with open(output_path, 'w') as f:
        json.dump(permutation_results, f, indent=2)
    
    logger.info(f"Permutation distributions written to {output_path}")
    
    # Enforce SC-002 (optional, but good to run here)
    sc002_status = enforce_sc002(original_r2, permutation_results)
    sc002_path = artifacts_dir / 'sc002_status.json'
    with open(sc002_path, 'w') as f:
        json.dump(sc002_status, f, indent=2)
    
    logger.info(f"SC-002 status written to {sc002_path}")
    logger.info(f"SC-002 Overall Pass: {sc002_status['overall_pass']}")
    
    print(f"T022 Complete. Permutation distributions saved to {output_path}")
    print(f"Original R2: {original_r2:.4f}")
    print(f"Model A Delta R2: {sc002_status['model_a']['delta_r2']:.4f}, p-value: {sc002_status['model_a']['p_value']:.4f}")
    print(f"Model B Delta R2: {sc002_status['model_b']['delta_r2']:.4f}, p-value: {sc002_status['model_b']['p_value']:.4f}")

if __name__ == '__main__':
    main()