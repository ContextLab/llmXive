"""
Modeling training module for predictive analysis of plant secondary metabolites.

This module contains functions for:
- Stratified splitting based on phylogenetic clades
- Leave-One-Out Cross-Validation (LOO-CV) training
- Model training (Random Forest, Elastic Net, Gradient Boosting)
- PCA feature reduction (if needed)
"""
import os
import logging
import random
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union, Any, Callable
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import ElasticNet
from sklearn.model_selection import LeaveOneOut, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.metrics import r2_score, mean_squared_error
import pickle

from config import get_config, get_data_path
from utils.logging import get_logger
from data_models import AlignedDataset

logger = get_logger(__name__)


class StratifiedSplitError(Exception):
    """Exception raised for errors in stratified splitting."""
    pass


class ModelTrainingError(Exception):
    """Exception raised for errors during model training."""
    pass


def get_clade_members(tree_data: Dict[str, List[str]], clade_name: str) -> List[str]:
    """
    Get all species members of a specific clade from the phylogeny data.
    
    Args:
        tree_data: Dictionary mapping clade names to lists of species
        clade_name: Name of the clade to query
        
    Returns:
        List of species names in the clade
    """
    return tree_data.get(clade_name, [])


def find_balanced_clades(clade_sizes: Dict[str, int], min_size: int = 3, max_size: int = 15) -> List[str]:
    """
    Find clades that are suitable for stratified splitting (not too small, not too large).
    
    Args:
        clade_sizes: Dictionary mapping clade names to their sizes
        min_size: Minimum acceptable clade size
        max_size: Maximum acceptable clade size
        
    Returns:
        List of balanced clade names
    """
    balanced = [
        name for name, size in clade_sizes.items()
        if min_size <= size <= max_size
    ]
    logger.info(f"Found {len(balanced)} balanced clades out of {len(clade_sizes)} total")
    return balanced


def create_stratified_split(
    species_list: List[str],
    clade_assignments: Dict[str, str],
    test_size: float = 0.2,
    random_state: Optional[int] = None
) -> Tuple[List[str], List[str]]:
    """
    Create a stratified train/test split based on phylogenetic clades.
    
    Args:
        species_list: List of all species
        clade_assignments: Dictionary mapping species to their clade
        test_size: Fraction of data to use for testing
        random_state: Random seed for reproducibility
        
    Returns:
        Tuple of (train_species, test_species)
    """
    if random_state is not None:
        random.seed(random_state)
        np.random.seed(random_state)
    
    # Group species by clade
    clade_groups: Dict[str, List[str]] = {}
    for species in species_list:
        clade = clade_assignments.get(species, "unknown")
        if clade not in clade_groups:
            clade_groups[clade] = []
        clade_groups[clade].append(species)
    
    train_species = []
    test_species = []
    
    # Stratified split: maintain clade proportions
    for clade, members in clade_groups.items():
        n_test = max(1, int(len(members) * test_size))
        test_members = random.sample(members, n_test)
        train_members = [m for m in members if m not in test_members]
        
        train_species.extend(train_members)
        test_species.extend(test_members)
    
    logger.info(f"Stratified split: {len(train_species)} train, {len(test_species)} test")
    return train_species, test_species


def load_pca_features(pca_path: str) -> pd.DataFrame:
    """
    Load PCA-reduced features from the specified path.
    
    Args:
        pca_path: Path to the PCA features CSV file
        
    Returns:
        DataFrame with PCA features
    """
    if not os.path.exists(pca_path):
        raise FileNotFoundError(f"PCA features file not found: {pca_path}")
    
    df = pd.read_csv(pca_path)
    logger.info(f"Loaded PCA features: {df.shape}")
    return df


def apply_pca(
    X: np.ndarray,
    n_components: Optional[int] = None,
    random_state: int = 42
) -> Tuple[np.ndarray, PCA]:
    """
    Apply PCA for dimensionality reduction.
    
    Args:
        X: Feature matrix
        n_components: Number of components to keep (default: min(n_samples, n_features))
        random_state: Random seed for reproducibility
        
    Returns:
        Tuple of (reduced_features, pca_object)
    """
    if n_components is None:
        n_components = min(X.shape[0], X.shape[1])
    
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    pca = PCA(n_components=n_components, random_state=random_state)
    X_pca = pca.fit_transform(X_scaled)
    
    logger.info(f"PCA: {X.shape} -> {X_pca.shape}, explained variance: {np.sum(pca.explained_variance_ratio_):.4f}")
    return X_pca, pca


def train_models_loo(
    X: np.ndarray,
    y: np.ndarray,
    model_names: Optional[List[str]] = None,
    save_path: Optional[str] = None
) -> Dict[str, Dict[str, Any]]:
    """
    Train multiple models using Leave-One-Out Cross-Validation.
    
    Args:
        X: Feature matrix (PCA-reduced if applicable)
        y: Target values (metabolite abundances)
        model_names: List of model names to train (default: ['rf', 'elastic_net', 'gb'])
        save_path: Path to save model results
        
    Returns:
        Dictionary with model names as keys and metrics as values
    """
    if model_names is None:
        model_names = ['random_forest', 'elastic_net', 'gradient_boosting']
    
    models = {
        'random_forest': RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            n_jobs=-1
        ),
        'elastic_net': ElasticNet(
            alpha=0.1,
            l1_ratio=0.5,
            random_state=42,
            max_iter=1000
        ),
        'gradient_boosting': GradientBoostingRegressor(
            n_estimators=100,
            max_depth=5,
            random_state=42
        )
    }
    
    results = {}
    loo = LeaveOneOut()
    
    logger.info(f"Training {len(model_names)} models with Leave-One-Out CV on {X.shape[0]} samples")
    
    for name in model_names:
        if name not in models:
            logger.warning(f"Model {name} not found, skipping")
            continue
        
        model = models[name]
        scores = cross_val_score(model, X, y, cv=loo, scoring='r2', n_jobs=-1)
        
        # Train final model on full data
        model.fit(X, y)
        
        # Calculate R2 on full data (for reporting)
        y_pred = model.predict(X)
        r2_full = r2_score(y, y_pred)
        
        results[name] = {
            'mean_r2': float(np.mean(scores)),
            'std_r2': float(np.std(scores)),
            'r2_full': float(r2_full),
            'n_samples': X.shape[0],
            'n_features': X.shape[1],
            'cv_method': 'LOO'
        }
        
        logger.info(f"{name}: LOO R2 = {np.mean(scores):.4f} (+/- {np.std(scores):.4f}), Full R2 = {r2_full:.4f}")
    
    # Save results if path provided
    if save_path:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        with open(save_path, 'w') as f:
            json.dump(results, f, indent=2)
        logger.info(f"Saved model results to {save_path}")
    
    return results


def train_models_5fold(
    X: np.ndarray,
    y: np.ndarray,
    model_names: Optional[List[str]] = None,
    save_path: Optional[str] = None
) -> Dict[str, Dict[str, Any]]:
    """
    Train multiple models using 5-fold Cross-Validation.
    
    Args:
        X: Feature matrix (PCA-reduced if applicable)
        y: Target values (metabolite abundances)
        model_names: List of model names to train
        save_path: Path to save model results
        
    Returns:
        Dictionary with model names as keys and metrics as values
    """
    if model_names is None:
        model_names = ['random_forest', 'elastic_net', 'gradient_boosting']
    
    models = {
        'random_forest': RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            n_jobs=-1
        ),
        'elastic_net': ElasticNet(
            alpha=0.1,
            l1_ratio=0.5,
            random_state=42,
            max_iter=1000
        ),
        'gradient_boosting': GradientBoostingRegressor(
            n_estimators=100,
            max_depth=5,
            random_state=42
        )
    }
    
    results = {}
    n_splits = 5
    
    logger.info(f"Training {len(model_names)} models with 5-fold CV on {X.shape[0]} samples")
    
    for name in model_names:
        if name not in models:
            logger.warning(f"Model {name} not found, skipping")
            continue
        
        model = models[name]
        scores = cross_val_score(model, X, y, cv=n_splits, scoring='r2', n_jobs=-1)
        
        # Train final model on full data
        model.fit(X, y)
        
        # Calculate R2 on full data
        y_pred = model.predict(X)
        r2_full = r2_score(y, y_pred)
        
        results[name] = {
            'mean_r2': float(np.mean(scores)),
            'std_r2': float(np.std(scores)),
            'r2_full': float(r2_full),
            'n_samples': X.shape[0],
            'n_features': X.shape[1],
            'cv_method': '5-fold'
        }
        
        logger.info(f"{name}: 5-fold R2 = {np.mean(scores):.4f} (+/- {np.std(scores):.4f}), Full R2 = {r2_full:.4f}")
    
    if save_path:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        with open(save_path, 'w') as f:
            json.dump(results, f, indent=2)
        logger.info(f"Saved model results to {save_path}")
    
    return results


def determine_cv_method(n_samples: int) -> str:
    """
    Determine which CV method to use based on sample size.
    
    Args:
        n_samples: Number of samples in the dataset
        
    Returns:
        'loo' if n_samples < 20, else '5fold'
    """
    if n_samples < 20:
        return 'loo'
    else:
        return '5fold'


def main():
    """
    Main function to run model training pipeline.
    
    This function:
    1. Loads PCA-reduced features from data/interim/pca_features.csv
    2. Determines CV method based on sample size
    3. Trains models using appropriate CV method
    4. Saves results to data/processed/model_results.json
    """
    config = get_config()
    data_path = get_data_path()
    
    # Load PCA features
    pca_path = os.path.join(data_path, 'interim', 'pca_features.csv')
    if not os.path.exists(pca_path):
        logger.error(f"PCA features file not found: {pca_path}")
        logger.error("Please run T023a-PCA first to generate PCA features.")
        return
    
    df = pd.read_csv(pca_path)
    
    # Separate features and target
    # Assuming first column is species name, last column is target (metabolite abundance)
    # Adjust based on actual data structure
    species_col = df.columns[0]
    target_col = df.columns[-1]
    feature_cols = df.columns[1:-1]
    
    X = df[feature_cols].values
    y = df[target_col].values
    species = df[species_col].values
    
    n_samples = X.shape[0]
    logger.info(f"Loaded data: {n_samples} samples, {X.shape[1]} features")
    
    # Determine CV method
    cv_method = determine_cv_method(n_samples)
    logger.info(f"Using {cv_method} cross-validation (n_samples={n_samples})")
    
    # Save path for results
    results_path = os.path.join(data_path, 'processed', 'model_results.json')
    
    # Train models
    if cv_method == 'loo':
        results = train_models_loo(X, y, save_path=results_path)
    else:
        results = train_models_5fold(X, y, save_path=results_path)
    
    # Log summary
    logger.info("=== Model Training Summary ===")
    for name, metrics in results.items():
        logger.info(f"{name}: R2 = {metrics['mean_r2']:.4f} (+/- {metrics['std_r2']:.4f})")
    
    logger.info(f"Results saved to {results_path}")


if __name__ == "__main__":
    main()