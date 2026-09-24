import os
import sys
import logging
import json
import pickle
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Union
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import LeaveOneGroupOut, GroupKFold
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error
from sklearn.pipeline import Pipeline
from sklearn.base import clone
import joblib

# Import project utilities
# Assuming the code is run from the project root or code/ is in sys.path
# The prompt implies running as a module or script where imports are resolved relative to code/
try:
    from data.features import compute_features, parse_composition_string
    from utils.logger import get_logger, log_info, log_warning, log_error, log_critical
    from config.env import load_config, initialize_random_seeds
except ImportError:
    # Fallback for direct script execution if path setup differs
    # In a real pipeline, sys.path is usually set up correctly
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    from data.features import compute_features, parse_composition_string
    from utils.logger import get_logger, log_info, log_warning, log_error, log_critical
    from config.env import load_config, initialize_random_seeds

logger = get_logger(__name__)

def load_features_data(data_path: str) -> pd.DataFrame:
    """Load the processed features dataset."""
    path = Path(data_path)
    if not path.exists():
        raise FileNotFoundError(f"Feature file not found: {data_path}")
    logger.info(f"Loading features from {data_path}")
    df = pd.read_csv(data_path)
    # Ensure composition column is string
    if 'composition' in df.columns:
        df['composition'] = df['composition'].astype(str)
    return df

def extract_primary_element(composition_str: str) -> str:
    """
    Extract the primary element from a composition string.
    Logic: Parse composition, find element with highest atomic fraction.
    If tied, choose the element with the higher atomic number.
    """
    # Re-implement parsing logic to match features.py or import if available
    # Assuming format like "Al50Cu50" or "Al_50_Cu_50" or similar
    # The features.py likely has parse_composition_string which returns a dict/list of (elem, frac)
    # We need to replicate the parsing to get the primary element without recomputing all features.
    
    # Simple regex-based parser for common formats (ElementFraction)
    # e.g., "Al50Cu50", "Al_50_Cu_50", "Fe40Ni40Cr20"
    import re
    
    # Normalize: replace underscores with nothing if present, handle potential spaces
    comp_clean = composition_str.replace("_", "").replace(" ", "")
    
    # Regex to find element symbols and optional numbers
    # Element symbols are 1 or 2 letters, first uppercase, second lowercase
    pattern = r'([A-Z][a-z]?)(\d+(?:\.\d+)?)'
    matches = re.findall(pattern, comp_clean)
    
    if not matches:
        # Fallback: try to parse as "Element%Element%" or similar if regex fails
        # This is a heuristic; proper parsing depends on exact input format from T013
        log_warning(f"Could not parse composition for primary element: {composition_str}")
        return "Unknown"
    
    elements = []
    for elem, frac_str in matches:
        frac = float(frac_str) if frac_str else 1.0 # Default if no number? Unlikely in this dataset
        elements.append((elem, frac))
    
    if not elements:
        return "Unknown"
    
    # Find max fraction
    max_frac = max(e[1] for e in elements)
    
    # Filter elements with max fraction
    candidates = [e for e in elements if e[1] == max_frac]
    
    if len(candidates) == 1:
        return candidates[0][0]
    
    # Tie-breaking: higher atomic number
    # We need atomic numbers. Use a simple dict or import from pymatgen if available
    # Since features.py uses pymatgen, we should use it here too for consistency
    try:
        from pymatgen.core import Element
        # Sort by atomic number descending
        candidates.sort(key=lambda x: Element(x[0]).number, reverse=True)
        return candidates[0][0]
    except ImportError:
        # Fallback: alphabetical or arbitrary if pymatgen not available (should not happen)
        log_warning("pymatgen not available for tie-breaking, using alphabetical order")
        candidates.sort(key=lambda x: x[0], reverse=True)
        return candidates[0][0]

def assign_element_families(df: pd.DataFrame, primary_col: str = 'primary_element') -> pd.DataFrame:
    """
    Assign a 'family' group to each row based on the primary element.
    For LOCO, we group by the primary element.
    """
    # Simple mapping: Primary Element -> Group ID
    # We can just use the element symbol as the group ID directly for LeaveOneGroupOut
    # or map to integer IDs if required by specific sklearn version.
    # LeaveOneGroupOut accepts any hashable labels for groups.
    df = df.copy()
    if primary_col not in df.columns:
        df[primary_col] = df['composition'].apply(extract_primary_element)
    
    # The group is simply the primary element string
    return df

def perform_loco_cv(
    X: np.ndarray, 
    y: np.ndarray, 
    groups: np.ndarray, 
    model_type: str = 'random_forest',
    n_jobs: int = -1,
    random_state: int = 42
) -> Tuple[float, Dict[str, Any]]:
    """
    Perform Leave-One-Group-Out Cross-Validation.
    
    Logic:
    1. Iterate through each unique group (primary element family).
    2. Hold out that group as test, train on the rest.
    3. Scale features within the training fold.
    4. Evaluate MAE on the held-out group.
    5. Aggregate MAE across all folds.
    
    Returns:
    - Overall MAE (mean of fold MAEs)
    - Detailed results per fold
    """
    logo = LeaveOneGroupOut()
    fold_results = []
    fold_mae_scores = []
    
    # Define model
    if model_type == 'random_forest':
        base_model = RandomForestRegressor(
            n_estimators=100, 
            max_depth=None, 
            random_state=random_state, 
            n_jobs=n_jobs
        )
    elif model_type == 'gradient_boosting':
        base_model = GradientBoostingRegressor(
            n_estimators=100, 
            random_state=random_state
        )
    else:
        raise ValueError(f"Unknown model type: {model_type}")
    
    logger.info(f"Starting LOCO CV with {model_type} ({len(np.unique(groups))} groups)")
    
    unique_groups = np.unique(groups)
    
    for train_idx, test_idx in logo.split(X, y, groups):
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]
        group_train = groups[train_idx]
        group_test = groups[test_idx] # Should be uniform
        
        # Fit Scaler on training fold ONLY
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        # Train model
        model = clone(base_model)
        model.fit(X_train_scaled, y_train)
        
        # Predict
        y_pred = model.predict(X_test_scaled)
        
        # Calculate MAE
        mae = mean_absolute_error(y_test, y_pred)
        fold_mae_scores.append(mae)
        
        fold_results.append({
            "held_out_group": group_test[0] if len(group_test) > 0 else "Unknown",
            "train_size": len(train_idx),
            "test_size": len(test_idx),
            "mae": mae
        })
        
        logger.debug(f"Fold: {group_test[0]}, Train: {len(train_idx)}, Test: {len(test_idx)}, MAE: {mae:.4f}")
    
    overall_mae = np.mean(fold_mae_scores)
    
    return overall_mae, {
        "overall_mae": overall_mae,
        "fold_results": fold_results,
        "num_folds": len(fold_results)
    }

def train_models(
    df: pd.DataFrame, 
    feature_cols: List[str], 
    target_col: str = 'log10_Rc',
    model_type: str = 'random_forest',
    save_dir: str = 'data/processed',
    state_dir: str = 'state',
    random_state: int = 42
) -> Tuple[Any, float, Dict[str, Any]]:
    """
    Main training function that handles LOCO CV, model selection, and artifact saving.
    
    Returns:
    - Best trained model (fitted on full data)
    - LOCO MAE score
    - Training metadata
    """
    logger.info("Preparing data for training...")
    
    # Extract features and target
    X = df[feature_cols].values
    y = df[target_col].values
    
    # Assign groups based on primary element
    df_with_groups = assign_element_families(df)
    groups = df_with_groups['primary_element'].values
    
    logger.info(f"Dataset shape: {X.shape}, Target shape: {y.shape}")
    logger.info(f"Number of unique groups (families): {len(np.unique(groups))}")
    
    # Perform LOCO CV
    loco_mae, loco_details = perform_loco_cv(X, y, groups, model_type=model_type, random_state=random_state)
    
    logger.info(f"LOCO CV MAE for {model_type}: {loco_mae:.4f}")
    
    # Save LOCO results to state
    state_path = Path(state_dir)
    state_path.mkdir(parents=True, exist_ok=True)
    loco_output_path = state_path / 'loco_mae.json'
    
    with open(loco_output_path, 'w') as f:
        json.dump(loco_details, f, indent=2)
    logger.info(f"Saved LOCO MAE results to {loco_output_path}")
    
    # Train final model on FULL dataset
    logger.info("Training final model on full dataset...")
    
    # Fit scaler on full data
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # Train model
    if model_type == 'random_forest':
        final_model = RandomForestRegressor(
            n_estimators=100, 
            max_depth=None, 
            random_state=random_state, 
            n_jobs=-1
        )
    elif model_type == 'gradient_boosting':
        final_model = GradientBoostingRegressor(
            n_estimators=100, 
            random_state=random_state
        )
    else:
        raise ValueError(f"Unknown model type: {model_type}")
    
    final_model.fit(X_scaled, y)
    
    # Save artifacts
    save_path = Path(save_dir)
    save_path.mkdir(parents=True, exist_ok=True)
    
    # Save Scaler
    scaler_path = save_path / 'scaler.pkl'
    with open(scaler_path, 'wb') as f:
        pickle.dump(scaler, f)
    logger.info(f"Saved scaler to {scaler_path}")
    
    # Save Transformed Training Data (X_train_raw in the context of the scaler, but actually scaled)
    # Task T021 says: "save the transformed training data as data/processed/X_train_raw.pkl and data/processed/y_train.pkl"
    # Note: The name X_train_raw is slightly confusing if it's scaled, but we follow the spec.
    # The spec says "fit a StandardScaler on the training features of each fold, save the fitted scaler... After model selection, fit the scaler on the *entire* training set and save the transformed training data"
    X_train_scaled_path = save_path / 'X_train_raw.pkl'
    y_train_path = save_path / 'y_train.pkl'
    
    with open(X_train_scaled_path, 'wb') as f:
        pickle.dump(X_scaled, f)
    with open(y_train_path, 'wb') as f:
        pickle.dump(y, f)
    
    logger.info(f"Saved transformed training data to {X_train_scaled_path} and {y_train_path}")
    
    # Save Model
    model_path = save_path / 'best_model.pkl'
    with open(model_path, 'wb') as f:
        pickle.dump(final_model, f)
    logger.info(f"Saved best model to {model_path}")
    
    return final_model, loco_mae, loco_details

def main():
    """
    Entry point for the training script.
    Loads features, performs LOCO CV, trains models, and saves artifacts.
    """
    # Initialize config and seeds
    try:
        config = load_config()
        random_state = config.get('random_state', 42)
        initialize_random_seeds(random_state)
    except Exception as e:
        log_warning(f"Could not load config or initialize seeds: {e}. Using default seed 42.")
        random_state = 42
        initialize_random_seeds(random_state)
    
    # Paths
    # Assuming data/processed/features.csv is the output of T017
    features_path = 'data/processed/features.csv'
    
    if not Path(features_path).exists():
        log_critical(f"Feature file not found at {features_path}. Please run data pipeline first.")
        sys.exit(1)
    
    # Load data
    df = load_features_data(features_path)
    
    # Identify feature columns (exclude composition, target, source_row_id, etc.)
    exclude_cols = ['composition', 'log10_Rc', 'source_row_id', 'primary_element']
    feature_cols = [col for col in df.columns if col not in exclude_cols]
    
    if not feature_cols:
        log_critical("No feature columns found. Check feature engineering output.")
        sys.exit(1)
    
    logger.info(f"Using {len(feature_cols)} features: {feature_cols[:5]}...")
    
    # Train Random Forest
    logger.info("=" * 50)
    logger.info("Training Random Forest Model")
    logger.info("=" * 50)
    rf_model, rf_mae, rf_details = train_models(
        df, 
        feature_cols, 
        model_type='random_forest',
        random_state=random_state
    )
    
    # Train Gradient Boosting
    logger.info("=" * 50)
    logger.info("Training Gradient Boosting Model")
    logger.info("=" * 50)
    gb_model, gb_mae, gb_details = train_models(
        df, 
        feature_cols, 
        model_type='gradient_boosting',
        random_state=random_state
    )
    
    # Model Selection (Lowest LOCO-MAE)
    logger.info("=" * 50)
    logger.info("Model Selection")
    logger.info("=" * 50)
    
    if rf_mae < gb_mae:
        best_model = rf_model
        best_mae = rf_mae
        best_type = 'random_forest'
        best_details = rf_details
        logger.info(f"Winner: Random Forest (MAE: {rf_mae:.4f} vs GB: {gb_mae:.4f})")
    else:
        best_model = gb_model
        best_mae = gb_mae
        best_type = 'gradient_boosting'
        best_details = gb_details
        logger.info(f"Winner: Gradient Boosting (MAE: {gb_mae:.4f} vs RF: {rf_mae:.4f})")
    
    # Overwrite best_model.pkl with the winner if we want a single artifact
    # The task says "output: best_model.pkl and best_model_weighted.pkl (if applicable)"
    # We already saved one per type. Let's ensure the 'best' one is clearly identified or copied.
    # Since we saved to data/processed/best_model.pkl in each train_models call, the last one runs overwrites.
    # We should explicitly save the winner to avoid ambiguity if the script is re-run partially.
    
    save_dir = Path('data/processed')
    final_model_path = save_dir / 'best_model.pkl'
    with open(final_model_path, 'wb') as f:
        pickle.dump(best_model, f)
    
    logger.info(f"Final Best Model ({best_type}) saved to {final_model_path}")
    logger.info(f"Final LOCO MAE: {best_mae:.4f}")
    
    # Save summary
    summary = {
        "best_model_type": best_type,
        "best_loco_mae": best_mae,
        "rf_mae": rf_mae,
        "gb_mae": gb_mae,
        "random_state": random_state
    }
    
    summary_path = save_dir / 'training_summary.json'
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)
    
    logger.info(f"Training summary saved to {summary_path}")

if __name__ == "__main__":
    main()