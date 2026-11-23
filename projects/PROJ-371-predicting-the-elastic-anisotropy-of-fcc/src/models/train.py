import os
import sys
import json
import logging
import traceback
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import LeaveOneGroupOut
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
from sklearn.preprocessing import StandardScaler

# Import project utilities
from src.utils.config import get_config, get_path, set_random_seed, get_seed, ensure_directories
from src.utils.logging import get_logger, log_info, log_warning, log_error, log_success

# Configure logger
logger = get_logger(__name__)

def load_processed_data(data_path: Path) -> pd.DataFrame:
    """
    Load the preprocessed elastic anisotropy dataset.
    Expects columns: 'material_id', 'formula', 'C11', 'C12', 'C44', 'A1', 
    and compositional descriptors (atomic_radius_variance, electronegativity_std, valence_electron_concentration).
    """
    if not data_path.exists():
        raise FileNotFoundError(f"Processed data file not found at {data_path}. "
                                "Please run the data pipeline (T015) first.")
    
    df = pd.read_csv(data_path)
    
    required_cols = ['material_id', 'formula', 'C11', 'C12', 'C44', 'A1',
                    'atomic_radius_variance', 'electronegativity_std', 'valence_electron_concentration']
    
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Processed data missing required columns: {missing}")
    
    log_info(f"Loaded {len(df)} records from {data_path}")
    return df

def prepare_loeo_data(df: pd.DataFrame, element_groups_path: Path) -> Tuple[pd.DataFrame, Dict[str, List[str]]]:
    """
    Prepare data for Leave-One-Element-Out (LOEO) cross-validation.
    Loads element_groups.json to map materials to their constituent elements.
    """
    if not element_groups_path.exists():
        raise FileNotFoundError(f"Element groups file not found at {element_groups_path}. "
                                "Please run the element grouping script (T014b) first.")
    
    with open(element_groups_path, 'r') as f:
        element_groups = json.load(f)
    
    # Create a reverse mapping: material_id -> list of elements
    material_to_elements = {}
    for elem, mats in element_groups.items():
        for mat_id in mats:
            if mat_id not in material_to_elements:
                material_to_elements[mat_id] = []
            material_to_elements[mat_id].append(elem)
    
    # Add element groups as a column for sklearn
    # We need a group identifier for each row. 
    # For LOEO, we want to leave out ALL materials containing a specific element.
    # However, sklearn's LeaveOneGroupOut expects one group ID per sample.
    # The standard approach for "Leave-One-Element-Out" where elements are the groups:
    # We assign each sample the set of elements it contains. 
    # But sklearn's GroupKFold/LeaveOneGroupOut works with a single label per sample.
    # To implement LOEO correctly with sklearn:
    # We iterate over unique elements. For each element E:
    #   Test set = all materials containing E
    #   Train set = all materials NOT containing E
    
    # We will not use sklearn's LeaveOneGroupOut directly for the split logic 
    # because it splits by a single group ID per sample. 
    # Instead, we will manually implement the split loop in run_loeo_cross_validation.
    
    # We just need to ensure the dataframe has the element info for splitting.
    # We'll store the element list as a string or keep the mapping external.
    # Let's keep the mapping external and pass it to the training loop.
    
    log_info(f"Prepared LOEO data with {len(element_groups)} unique elements")
    return df, element_groups

def train_single_model(X_train: np.ndarray, y_train: np.ndarray, 
                       model_name: str, hyperparams: Dict[str, Any],
                       random_state: int) -> Any:
    """
    Train a single regression model.
    """
    if model_name == "RandomForest":
        model = RandomForestRegressor(random_state=random_state, **hyperparams)
    elif model_name == "GradientBoosting":
        model = GradientBoostingRegressor(random_state=random_state, **hyperparams)
    elif model_name == "LinearRegression":
        model = LinearRegression()
    else:
        raise ValueError(f"Unknown model: {model_name}")
    
    model.fit(X_train, y_train)
    return model

def evaluate_model(model: Any, X_test: np.ndarray, y_test: np.ndarray) -> Dict[str, float]:
    """
    Evaluate a trained model and return R2, MAE, RMSE.
    """
    y_pred = model.predict(X_test)
    
    r2 = r2_score(y_test, y_pred)
    mae = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    
    return {
        "r2": float(r2),
        "mae": float(mae),
        "rmse": float(rmse),
        "n_test_samples": int(len(y_test))
    }

def run_loeo_cross_validation(df: pd.DataFrame, element_groups: Dict[str, List[str]], 
                              feature_cols: List[str], target_col: str,
                              models_config: List[Dict[str, Any]], 
                              random_state: int) -> Dict[str, Any]:
    """
    Perform Leave-One-Element-Out cross-validation.
    For each unique element in the dataset:
      - Test set: all materials containing that element
      - Train set: all materials NOT containing that element
    Train and evaluate each model configuration.
    """
    # Extract unique elements from the groups
    all_elements = list(element_groups.keys())
    log_info(f"Starting LOEO CV with {len(all_elements)} elements to leave out")
    
    if len(all_elements) == 0:
        raise ValueError("No elements found in element_groups. Cannot perform LOEO.")
    
    # Prepare feature matrix
    X = df[feature_cols].values
    y = df[target_col].values
    
    # Build a mapping from material_id to its elements for quick lookup
    # We assume the dataframe has 'material_id' and we have element_groups
    # We need to know which materials contain which elements to split correctly.
    # element_groups is {element: [mat_id1, mat_id2, ...]}
    # We need {mat_id: [elem1, elem2, ...]}
    
    mat_to_elems = {}
    for elem, mats in element_groups.items():
        for mat in mats:
            if mat not in mat_to_elems:
                mat_to_elems[mat] = set()
            mat_to_elems[mat].add(elem)
    
    # Ensure all rows in df are accounted for in mat_to_elems
    for _, row in df.iterrows():
        mat_id = row['material_id']
        if mat_id not in mat_to_elems:
            # This material has no elements? Skip or warn
            log_warning(f"Material {mat_id} has no elements in groups. Skipping.")
    
    results = {
        "cv_scores": [],
        "model_metrics": {},
        "summary": {}
    }
    
    # Initialize storage for each model
    for model_cfg in models_config:
        model_name = model_cfg["name"]
        results["model_metrics"][model_name] = {
            "fold_scores": [],
            "mean_r2": None,
            "mean_mae": None,
            "mean_rmse": None
        }
    
    # Loop over each element to leave out
    for i, leave_out_elem in enumerate(all_elements):
        log_info(f"LOEO Fold {i+1}/{len(all_elements)}: Leaving out element '{leave_out_elem}'")
        
        # Identify test indices (materials containing the leave-out element)
        test_mat_ids = set(element_groups.get(leave_out_elem, []))
        train_mat_ids = set(mat_to_elems.keys()) - test_mat_ids
        
        if len(test_mat_ids) == 0:
            log_warning(f"No materials found for element {leave_out_elem}. Skipping fold.")
            continue
        
        if len(train_mat_ids) == 0:
            log_error(f"No materials found for training when leaving out {leave_out_elem}. Skipping fold.")
            continue
        
        # Map material IDs to dataframe indices
        # Assuming df['material_id'] is unique
        mat_id_to_idx = {row['material_id']: idx for idx, row in df.iterrows()}
        
        test_indices = [mat_id_to_idx[mid] for mid in test_mat_ids if mid in mat_id_to_idx]
        train_indices = [mat_id_to_idx[mid] for mid in train_mat_ids if mid in mat_id_to_idx]
        
        if not test_indices or not train_indices:
            log_warning(f"Invalid split for element {leave_out_elem}. Skipping.")
            continue
        
        X_train, X_test = X[train_indices], X[test_indices]
        y_train, y_test = y[train_indices], y[test_indices]
        
        # Scale features (fit on train, transform both)
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        # Train and evaluate each model
        for model_cfg in models_config:
            model_name = model_cfg["name"]
            hyperparams = model_cfg.get("hyperparameters", {})
            
            try:
                model = train_single_model(X_train_scaled, y_train, model_name, hyperparams, random_state)
                metrics = evaluate_model(model, X_test_scaled, y_test)
                
                results["model_metrics"][model_name]["fold_scores"].append(metrics)
                
                # Optionally store the trained model for the fold if needed, 
                # but for now we just aggregate metrics.
                
            except Exception as e:
                log_error(f"Error training/evaluating {model_name} on fold {leave_out_elem}: {e}")
                traceback.print_exc()
                continue
    
    # Aggregate results
    for model_name, metrics_data in results["model_metrics"].items():
        if metrics_data["fold_scores"]:
            scores = metrics_data["fold_scores"]
            mean_r2 = np.mean([s["r2"] for s in scores])
            mean_mae = np.mean([s["mae"] for s in scores])
            mean_rmse = np.mean([s["rmse"] for s in scores])
            
            metrics_data["mean_r2"] = float(mean_r2)
            metrics_data["mean_mae"] = float(mean_mae)
            metrics_data["mean_rmse"] = float(mean_rmse)
            metrics_data["n_folds"] = len(scores)
            
            log_success(f"Model {model_name} LOEO Summary: R2={mean_r2:.4f}, MAE={mean_mae:.4f}, RMSE={mean_rmse:.4f}")
        else:
            log_warning(f"No valid folds for model {model_name}")
    
    return results

def save_results(results: Dict[str, Any], output_path: Path):
    """
    Save cross-validation results to a JSON file.
    """
    ensure_directories([output_path.parent])
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    log_info(f"Results saved to {output_path}")

def main():
    """
    Main entry point for training models with LOEO cross-validation.
    """
    config = get_config()
    set_random_seed(config.get("seed", 42))
    
    # Paths
    data_path = get_path("processed", "elastic_anisotropy.csv")
    groups_path = get_path("processed", "element_groups.json")
    output_path = get_path("output", "model_cv_results.json")
    
    ensure_directories([output_path.parent])
    
    try:
        # Load data
        df = load_processed_data(data_path)
        df, element_groups = prepare_loeo_data(df, groups_path)
        
        # Define features and target
        feature_cols = [
            'atomic_radius_variance', 
            'electronegativity_std', 
            'valence_electron_concentration'
        ]
        target_col = 'A1'
        
        # Model configurations
        # Using simple defaults for CPU efficiency
        models_config = [
            {
                "name": "RandomForest",
                "hyperparameters": {
                    "n_estimators": 50,
                    "max_depth": 5,
                    "min_samples_split": 2
                }
            },
            {
                "name": "GradientBoosting",
                "hyperparameters": {
                    "n_estimators": 50,
                    "max_depth": 3,
                    "learning_rate": 0.1
                }
            },
            {
                "name": "LinearRegression",
                "hyperparameters": {}
            }
        ]
        
        log_info("Starting LOEO Cross-Validation Training...")
        results = run_loeo_cross_validation(
            df, 
            element_groups, 
            feature_cols, 
            target_col, 
            models_config,
            get_seed()
        )
        
        save_results(results, output_path)
        
        log_success("Training and evaluation complete.")
        
    except FileNotFoundError as e:
        log_error(f"Data file missing: {e}")
        sys.exit(1)
    except Exception as e:
        log_error(f"Training failed: {e}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
