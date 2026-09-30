"""
Stratified Analysis Module for User Story 2 (T030).

This module performs per-group performance analysis of the GPR model based on
categorical variables (specifically 'alloy_type') to identify potential
confounding effects or performance disparities across different material classes.

Outputs:
    results/confounder_analysis.json: A JSON artifact containing per-group metrics.
"""

import os
import sys
import json
import logging
import numpy as np
import pandas as pd
import pickle
from typing import Dict, Any, List, Optional, Tuple

# Import from local project structure
from config import get_project_root, get_processed_data_dir, get_results_dir, get_models_dir, ensure_directories, get_logger
from utils.logger import setup_logging

# Ensure deterministic behavior
np.random.seed(42)

def setup_logger(name: str) -> logging.Logger:
    """Configure and return a logger for this module."""
    return setup_logging(name, log_file="stratified_analysis.log")

def load_processed_data() -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Load the preprocessed train and test datasets.

    Returns:
        Tuple of (train_df, test_df)
    """
    processed_dir = get_processed_data_dir()
    train_path = os.path.join(processed_dir, "train.csv")
    test_path = os.path.join(processed_dir, "test.csv")

    if not os.path.exists(train_path):
        raise FileNotFoundError(f"Train data not found at {train_path}. Run preprocessing first.")
    if not os.path.exists(test_path):
        raise FileNotFoundError(f"Test data not found at {test_path}. Run preprocessing first.")

    train_df = pd.read_csv(train_path)
    test_df = pd.read_csv(test_path)

    logging.info(f"Loaded train data: {train_df.shape}, test data: {test_df.shape}")
    return train_df, test_df

def load_model() -> Any:
    """
    Load the trained GPR model.

    Returns:
        The trained model object.
    """
    models_dir = get_models_dir()
    # Assuming the model is saved as 'gpr_model.pkl' based on standard pipeline conventions
    model_path = os.path.join(models_dir, "gpr_model.pkl")

    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model not found at {model_path}. Run training first.")

    with open(model_path, 'rb') as f:
        model = pickle.load(f)

    logging.info(f"Loaded model from {model_path}")
    return model

def identify_group_column(df: pd.DataFrame) -> Optional[str]:
    """
    Identify the categorical column used for stratification.
    Currently hard-coded to look for 'alloy_type' or similar encoded columns,
    but since we one-hot encoded it, we need to check if the original column
    was preserved or if we need to reconstruct it.
    
    Note: In T016B-2, 'alloy_type' is one-hot encoded and the original column is dropped.
    However, for stratified analysis, we typically need the original label.
    
    Strategy:
    1. Check if 'alloy_type' exists (in case it wasn't dropped or was re-added).
    2. If not, check for columns starting with 'is_' (the one-hot columns).
    3. If found, reconstruct the original group labels by taking the argmax of the one-hot columns.
    4. If neither, return None (no stratification possible).
    """
    if 'alloy_type' in df.columns:
        return 'alloy_type'
    
    # Look for one-hot encoded columns
    one_hot_cols = [c for c in df.columns if c.startswith('is_')]
    if one_hot_cols:
        # Reconstruct the group name
        # We assume the column names are 'is_<type>', so we strip 'is_'
        # We need to know the original mapping. For now, we'll use the column names as proxy groups
        # or try to infer from the data.
        # A robust way: if we have 'is_AlloyA', 'is_AlloyB', we can map rows to 'AlloyA', 'AlloyB'.
        # Let's create a temporary column 'reconstructed_alloy_type'
        group_map = {}
        for col in one_hot_cols:
            group_name = col.replace('is_', '')
            group_map[col] = group_name
        
        # We will handle this reconstruction in calculate_group_stats
        return 'RECONSTRUCTED_ONEHOT'
    
    return None

def calculate_group_stats(
    df: pd.DataFrame, 
    y_true: np.ndarray, 
    y_pred: np.ndarray, 
    model: Any,
    group_col: str
) -> Dict[str, Dict[str, float]]:
    """
    Calculate performance metrics (R², RMSE, MAE) for each group.

    Args:
        df: The dataframe containing the group column and features.
        y_true: True target values.
        y_pred: Predicted target values.
        model: The trained model (used for permutation importance if needed, though not strictly required for basic stats).
        group_col: The column name containing group labels.

    Returns:
        Dictionary keyed by group name with metrics.
    """
    metrics = {}
    
    # Handle reconstructed one-hot case
    if group_col == 'RECONSTRUCTED_ONEHOT':
        one_hot_cols = [c for c in df.columns if c.startswith('is_')]
        if not one_hot_cols:
            return metrics
        
        # Reconstruct groups
        reconstructed_groups = []
        for idx, row in df.iterrows():
            # Find which one-hot column is 1
            group_name = None
            for col in one_hot_cols:
                if row[col] == 1:
                    group_name = col.replace('is_', '')
                    break
            if group_name is None:
                group_name = "Unknown"
            reconstructed_groups.append(group_name)
        
        df = df.copy()
        df['reconstructed_group'] = reconstructed_groups
        group_col = 'reconstructed_group'

    if group_col not in df.columns:
        logging.warning(f"Group column '{group_col}' not found in dataframe. Skipping stratified analysis.")
        return metrics

    groups = df[group_col].unique()
    
    for group in groups:
        mask = df[group_col] == group
        y_true_group = y_true[mask]
        y_pred_group = y_pred[mask]
        
        if len(y_true_group) == 0:
            continue

        # Calculate Metrics
        # R²
        ss_res = np.sum((y_true_group - y_pred_group) ** 2)
        ss_tot = np.sum((y_true_group - np.mean(y_true_group)) ** 2)
        r2 = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0.0
        
        # RMSE
        rmse = np.sqrt(np.mean((y_true_group - y_pred_group) ** 2))
        
        # MAE
        mae = np.mean(np.abs(y_true_group - y_pred_group))
        
        metrics[str(group)] = {
            "count": int(len(y_true_group)),
            "r2": float(r2),
            "rmse": float(rmse),
            "mae": float(mae)
        }
        logging.info(f"Group '{group}': n={len(y_true_group)}, R²={r2:.4f}, RMSE={rmse:.4f}, MAE={mae:.4f}")
    
    return metrics

def assess_variance_heterogeneity(metrics: Dict[str, Dict[str, float]]) -> Dict[str, Any]:
    """
    Assess if variance in errors differs significantly between groups.
    Simple check: Compare RMSE across groups.
    """
    if not metrics:
        return {"status": "no_data", "details": "No groups found."}
    
    rmse_values = [m["rmse"] for m in metrics.values()]
    if len(rmse_values) < 2:
        return {"status": "insufficient_groups", "details": "Less than 2 groups to compare."}
    
    max_rmse = max(rmse_values)
    min_rmse = min(rmse_values)
    ratio = max_rmse / min_rmse if min_rmse > 0 else float('inf')
    
    status = "high_heterogeneity" if ratio > 2.0 else "low_heterogeneity"
    
    return {
        "status": status,
        "max_rmse": max_rmse,
        "min_rmse": min_rmse,
        "ratio": ratio,
        "interpretation": f"RMSE varies by a factor of {ratio:.2f} across groups."
    }

def run_stratified_analysis() -> Dict[str, Any]:
    """
    Main orchestration function for T030.
    
    1. Loads train/test data.
    2. Loads the trained model.
    3. Predicts on test set.
    4. Identifies group column.
    5. Calculates per-group metrics.
    6. Writes results to results/confounder_analysis.json.
    """
    logger = setup_logger("stratified_analysis")
    
    try:
        # Load Data
        train_df, test_df = load_processed_data()
        model = load_model()
        
        # Identify Target Columns
        # We need to know which column is the target. 
        # Based on T016A-2, targets are yield_strength and ductility.
        # We assume the model was trained on a specific target (usually the first active one or a combined one).
        # For this analysis, we look for standard target columns in the processed data.
        # If the model predicts multiple targets, we need to handle that. 
        # Assuming single target for now (yield_strength) as per typical GPR setup unless specified otherwise.
        
        # Heuristic: Find columns that look like targets (not features, not group)
        possible_targets = [c for c in test_df.columns if c in ['yield_strength', 'ductility', 'fatigue_life']]
        if not possible_targets:
            raise ValueError("Could not identify target column in processed test data.")
        
        target_col = possible_targets[0] # Default to first found
        logging.info(f"Using target column: {target_col}")
        
        X_test = test_df.drop(columns=[target_col])
        y_true = test_df[target_col].values
        
        # Predict
        y_pred = model.predict(X_test)
        
        # Ensure y_pred is 1D
        if y_pred.ndim > 1:
            y_pred = y_pred.ravel()
        
        # Identify Group Column
        group_col = identify_group_column(test_df)
        
        if group_col is None:
            logging.warning("No stratification column found. Creating empty analysis.")
            results = {
                "status": "no_stratification_column",
                "message": "Could not identify 'alloy_type' or one-hot encoded groups in test data.",
                "groups": {}
            }
        else:
            # Calculate Stats
            group_metrics = calculate_group_stats(test_df, y_true, y_pred, model, group_col)
            
            # Assess Heterogeneity
            heterogeneity = assess_variance_heterogeneity(group_metrics)
            
            results = {
                "target_column": target_col,
                "group_column": group_col,
                "heterogeneity_assessment": heterogeneity,
                "groups": group_metrics
            }
        
        # Save Results
        results_dir = get_results_dir()
        output_path = os.path.join(results_dir, "confounder_analysis.json")
        
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        logging.info(f"Stratified analysis complete. Results saved to {output_path}")
        return results

    except Exception as e:
        logging.error(f"Error during stratified analysis: {e}", exc_info=True)
        raise

def main():
    """Entry point for the script."""
    run_stratified_analysis()

if __name__ == "__main__":
    main()