import os
import sys
import logging
import json
from pathlib import Path
import pandas as pd
import numpy as np
import pickle
from typing import Dict, Any, List, Optional, Tuple

# Import local utilities
from utils.logger import get_logger, log_info, log_warning, log_error, log_critical
from config.env import load_config, initialize_random_seeds

# Initialize logger
logger = get_logger(__name__)

def load_features_data(features_path: str) -> pd.DataFrame:
    """Load the feature-engineered dataset."""
    path = Path(features_path)
    if not path.exists():
        raise FileNotFoundError(f"Features file not found: {features_path}")
    df = pd.read_csv(path)
    return df

def load_family_map(family_map_path: str) -> Dict[str, str]:
    """Load the element-to-family mapping from YAML."""
    path = Path(family_map_path)
    if not path.exists():
        raise FileNotFoundError(f"Family map file not found: {family_map_path}")
    import yaml
    with open(path, 'r') as f:
        data = yaml.safe_load(f)
    return data

def extract_primary_element(composition_str: str) -> Tuple[str, float]:
    """
    Extract the primary element (highest atomic fraction) from a composition string.
    Format: 'Element1:0.5,Element2:0.3,Element3:0.2'
    Returns: (element_symbol, fraction)
    Tie-breaker: If fractions are equal, choose the element with the higher atomic number.
    """
    import re
    from pymatgen.core import Element

    parts = composition_str.split(',')
    elements = []
    for part in parts:
        if ':' in part:
            elem_sym, frac_str = part.split(':')
            frac = float(frac_str)
            elements.append((elem_sym.strip(), frac))

    if not elements:
        return None, 0.0

    # Sort by fraction descending, then by atomic number descending (for tie-breaker)
    def sort_key(item):
        sym, frac = item
        try:
            atomic_num = Element(sym).number
        except Exception:
            atomic_num = 0
        return (-frac, -atomic_num)

    elements.sort(key=sort_key)
    return elements[0]

def assign_element_families(df: pd.DataFrame, family_map: Dict[str, str]) -> pd.DataFrame:
    """
    Assign a 'primary_family' column to the dataframe based on the primary element.
    Handles unmapped elements by grouping with periodic table neighbors or 'Other'.
    """
    from pymatgen.core import Element
    import pandas as pd

    def get_family_for_element(elem_sym: str) -> str:
        if elem_sym in family_map:
            return family_map[elem_sym]
        
        # Fallback: Try to find a neighbor in the same group
        try:
            el = Element(elem_sym)
            group = el.group_number
            # Look for other elements in the dataset that are in the same group
            # This is a simplified fallback; in practice, we might need a more robust lookup
            # For now, assign to 'Other' if not found
            return 'Other'
        except Exception:
            return 'Other'

    primary_elements = []
    for _, row in df.iterrows():
        comp_str = row['composition']
        primary_elem, _ = extract_primary_element(comp_str)
        if primary_elem:
            family = get_family_for_element(primary_elem)
            primary_elements.append(family)
        else:
            primary_elements.append('Unknown')
    
    df = df.copy()
    df['primary_family'] = primary_elements
    return df

def perform_loco_cv(df: pd.DataFrame, model_class, param_grid: Dict[str, Any], family_col: str = 'primary_family') -> Dict[str, Any]:
    """
    Perform Leave-One-Cluster-Out (LOCO) cross-validation.
    Clusters are defined by the 'family_col' (primary metallic element family).
    """
    from sklearn.model_selection import GroupKFold
    from sklearn.metrics import mean_absolute_error
    import numpy as np

    # GroupKFold handles the "leave one group out" logic
    gkf = GroupKFold(n_splits=df[family_col].nunique())
    
    mae_scores = []
    fold_results = []

    # Assuming 'log10_Rc' is the target
    if 'log10_Rc' not in df.columns:
        # Try 'Rc' and convert if necessary
        if 'Rc' in df.columns:
            df['log10_Rc'] = np.log10(df['Rc'])
        else:
            raise KeyError("Target column 'log10_Rc' or 'Rc' not found in dataframe")

    y = df['log10_Rc'].values
    X = df.drop(columns=['composition', 'log10_Rc', 'Rc', 'primary_family']).values
    groups = df[family_col].values

    for fold_idx, (train_idx, test_idx) in enumerate(gkf.split(X, y, groups)):
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]
        train_groups = groups[train_idx]
        test_groups = groups[test_idx]

        model = model_class(**param_grid)
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        mae = mean_absolute_error(y_test, y_pred)
        mae_scores.append(mae)
        
        fold_results.append({
            "fold": fold_idx + 1,
            "held_out_family": list(set(test_groups)),
            "mae": mae
        })
        logger.info(f"LOCO Fold {fold_idx+1}: Held out {set(test_groups)}, MAE={mae:.4f}")

    avg_mae = np.mean(mae_scores)
    return {
        "mae_scores": mae_scores,
        "average_mae": avg_mae,
        "fold_details": fold_results
    }

def validate_loco_cluster_assignment(df: pd.DataFrame, family_map: Dict[str, str], test_df: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
    """
    Validate the LOCO cluster assignment logic.
    
    1. Verify that the cluster assignment rule (highest atomic fraction, then highest atomic number)
       is applied consistently.
    2. Verify that family mapping is applied correctly.
    3. Create a synthetic dataset with tied fractions to verify the tie-breaker logic.
    
    Returns a dictionary with validation results.
    """
    from pymatgen.core import Element
    import numpy as np

    results = {
        "passed": True,
        "details": [],
        "warnings": []
    }

    # --- Test 1: Consistency on existing data ---
    logger.info("Validating cluster assignment on existing data...")
    # Re-calculate primary element for each row and compare with assigned family
    # We need to re-derive the family from the composition string to compare
    
    errors = []
    for idx, row in df.iterrows():
        comp_str = row['composition']
        assigned_family = row.get('primary_family', 'Unknown')
        
        # Re-extract primary element
        primary_elem, frac = extract_primary_element(comp_str)
        if primary_elem is None:
            errors.append(f"Row {idx}: Could not extract primary element from '{comp_str}'")
            continue
        
        # Determine expected family
        if primary_elem in family_map:
            expected_family = family_map[primary_elem]
        else:
            expected_family = 'Other' # Based on fallback logic in assign_element_families
        
        if assigned_family != expected_family:
            errors.append(f"Row {idx}: Mismatch. Expected {expected_family}, got {assigned_family} for element {primary_elem}")

    if errors:
        results["passed"] = False
        results["details"].extend(errors)
    else:
        results["details"].append("Consistency check on existing data passed.")

    # --- Test 2: Tie-breaker logic with synthetic data ---
    logger.info("Validating tie-breaker logic with synthetic data...")
    
    # Create a synthetic dataset with tied fractions
    # Element 1: Fe (Atomic Number 26)
    # Element 2: Cu (Atomic Number 29)
    # Both at 0.5 fraction
    # Expected primary: Cu (higher atomic number)
    
    synthetic_row = {
        'composition': 'Fe:0.5,Cu:0.5',
        'log10_Rc': 5.0,
        'primary_family': 'Unknown' # To be calculated
    }
    
    # Manually calculate expected primary
    primary_elem, frac = extract_primary_element(synthetic_row['composition'])
    expected_primary = 'Cu' # Cu has Z=29, Fe has Z=26
    
    if primary_elem != expected_primary:
        results["passed"] = False
        results["details"].append(f"Tie-breaker failed: Expected {expected_primary}, got {primary_elem} for 'Fe:0.5,Cu:0.5'")
    else:
        results["details"].append(f"Tie-breaker passed: Correctly selected {primary_elem} over Fe (higher atomic number).")
    
    # Another tie case: Same element? (Shouldn't happen in valid composition, but let's test logic)
    # Or different elements with same Z? (Impossible for distinct elements)
    
    # Test 3: Three-way tie
    # Al (13), Si (14), P (15) all at 0.3333
    synthetic_row_2 = {
        'composition': 'Al:0.3333,Si:0.3333,P:0.3333',
        'log10_Rc': 5.0
    }
    primary_elem_2, _ = extract_primary_element(synthetic_row_2['composition'])
    expected_primary_2 = 'P' # Highest Z (15)
    
    if primary_elem_2 != expected_primary_2:
        results["passed"] = False
        results["details"].append(f"Three-way tie-breaker failed: Expected {expected_primary_2}, got {primary_elem_2}")
    else:
        results["details"].append(f"Three-way tie-breaker passed: Correctly selected {primary_elem_2}.")

    # Log results
    if results["passed"]:
        log_info("LOCO cluster assignment validation PASSED.")
    else:
        log_error("LOCO cluster assignment validation FAILED.")
        for detail in results["details"]:
            log_error(f"  - {detail}")

    return results

def train_models(df: pd.DataFrame, family_map_path: str, output_dir: str, seed: int = 42) -> Dict[str, Any]:
    """
    Main training function that orchestrates feature loading, family assignment,
    LOCO CV, and model selection.
    """
    initialize_random_seeds(seed)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Load data
    logger.info("Loading features data...")
    # Assuming df is already loaded or passed in. If not, load from path.
    # For this function, we assume df is passed.
    
    # Load family map
    family_map = load_family_map(family_map_path)
    logger.info(f"Loaded family map: {len(family_map)} mappings.")

    # Assign families
    logger.info("Assigning element families...")
    df = assign_element_families(df, family_map)

    # Validate assignment logic (T053 requirement)
    logger.info("Running LOCO cluster assignment validation...")
    validation_results = validate_loco_cluster_assignment(df, family_map)
    
    # Save validation results
    validation_path = output_path / "loco_cluster_validation.json"
    with open(validation_path, 'w') as f:
        json.dump(validation_results, f, indent=2)
    logger.info(f"Saved validation results to {validation_path}")

    if not validation_results["passed"]:
        log_warning("Validation failed. Check logs for details. Proceeding with training but results may be compromised.")

    # Prepare features and target
    # Drop non-feature columns
    feature_cols = [col for col in df.columns if col not in ['composition', 'log10_Rc', 'Rc', 'primary_family']]
    X = df[feature_cols].values
    y = df['log10_Rc'].values
    groups = df['primary_family'].values

    # Train models (RandomForest and GradientBoosting)
    from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
    from sklearn.model_selection import GridSearchCV

    models = {
        "RandomForest": RandomForestRegressor(random_state=seed),
        "GradientBoosting": GradientBoostingRegressor(random_state=seed)
    }

    param_grids = {
        "RandomForest": {
            "n_estimators": [50, 100],
            "max_depth": [None, 10]
        },
        "GradientBoosting": {
            "n_estimators": [50, 100],
            "learning_rate": [0.1, 0.01]
        }
    }

    best_models = {}
    best_scores = {}

    for name, model in models.items():
        logger.info(f"Training {name} with LOCO CV...")
        # Perform LOCO CV
        cv_results = perform_loco_cv(df, model, param_grids[name])
        best_scores[name] = cv_results["average_mae"]
        logger.info(f"{name} LOCO CV Average MAE: {best_scores[name]:.4f}")
        
        # Retrain on full data with best params (simplified: use grid search best params if needed)
        # For now, we just retrain with the grid search best params if we did grid search.
        # But perform_loco_cv didn't do grid search inside, it just trained with fixed params.
        # We need to do a full grid search to find the best hyperparameters for the final model.
        
        # Let's do a GridSearchCV with GroupKFold for the final model selection
        gkf = GroupKFold(n_splits=df['primary_family'].nunique())
        grid_search = GridSearchCV(model, param_grids[name], cv=gkf, scoring='neg_mean_absolute_error', n_jobs=-1)
        grid_search.fit(X, y, groups=groups)
        
        best_models[name] = grid_search.best_estimator_
        logger.info(f"Best {name} params: {grid_search.best_params_}")
        logger.info(f"Best {name} CV score: {grid_search.best_score_:.4f}")

    # Select best model based on LOCO CV MAE (from perform_loco_cv, not grid search, to avoid leakage)
    # Actually, we should use the LOCO CV MAE from perform_loco_cv for selection.
    selected_name = min(best_scores, key=best_scores.get)
    logger.info(f"Selected best model: {selected_name} with LOCO MAE {best_scores[selected_name]:.4f}")

    # Save artifacts
    best_model_path = output_path / "best_model.pkl"
    with open(best_model_path, 'wb') as f:
        pickle.dump(best_models[selected_name], f)
    logger.info(f"Saved best model to {best_model_path}")

    # Save LOCO MAE scores
    loco_mae_path = output_path.parent / "state" / "loco_mae.json"
    loco_mae_path.parent.mkdir(parents=True, exist_ok=True)
    loco_data = {
        "selected_model": selected_name,
        "mae_scores": {k: v for k, v in best_scores.items()},
        "validation_results": validation_results
    }
    with open(loco_mae_path, 'w') as f:
        json.dump(loco_data, f, indent=2)
    logger.info(f"Saved LOCO MAE results to {loco_mae_path}")

    return {
        "best_model_name": selected_name,
        "best_model": best_models[selected_name],
        "mae_scores": best_scores
    }

def main():
    """Entry point for the training script."""
    config = load_config()
    seed = config.get('random_seed', 42)
    features_path = config.get('features_path', 'data/processed/features.csv')
    family_map_path = config.get('family_map_path', 'data/config/family_map.yaml')
    output_dir = config.get('model_output_dir', 'code/models/output')

    logger.info("Starting model training...")
    try:
        df = load_features_data(features_path)
        train_models(df, family_map_path, output_dir, seed)
        logger.info("Training completed successfully.")
    except Exception as e:
        log_critical(f"Training failed: {e}")
        raise

if __name__ == "__main__":
    main()
