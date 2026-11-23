import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score

from code.config import PROCESSED_PATH, get_logger
from code.models.regression import load_interaction_terms, prepare_features_and_target
from code.errors import DataLoadError

logger = get_logger(__name__)

def load_regression_data_for_system(system_name: str) -> Tuple[np.ndarray, np.ndarray]:
    """
    Load interaction terms and target segregation energies for a specific alloy system.
    Returns features (X) and target (y).
    """
    input_path = PROCESSED_PATH / "interaction_terms.csv"
    if not input_path.exists():
        raise DataLoadError(f"Interaction terms file not found: {input_path}")
    
    df = pd.read_csv(input_path)
    
    # Filter for the specific system. Assuming 'system' column exists or derived from filename logic.
    # Since the interaction_terms.csv is generated from segregation_profiles.json which contains system info,
    # we assume the CSV has a 'system' column or we filter by system name prefix in other columns if necessary.
    # Based on T021a-Gen, the CSV contains columns like Cr, Mo, Cr_Mo etc. and likely a 'system' identifier.
    # If 'system' column is missing, we might need to reconstruct it or assume the file is per-system.
    # However, T021a-Gen says "Input file: data/processed/segregation_profiles.json".
    # Let's assume the CSV has a 'system' column for now, or we filter rows where the system matches.
    
    if 'system' not in df.columns:
        # Fallback: if no system column, assume the whole file is for one system or raise error.
        # For this task, we expect a combined file. If not, we raise.
        logger.warning("No 'system' column found in interaction_terms.csv. Attempting to infer or raising error.")
        # If the file is aggregated, we need to know how to split. 
        # Let's assume the file has a 'system' column as per standard practice in T021a.
        raise DataLoadError(f"Missing 'system' column in {input_path}. Cannot filter by system.")
    
    system_df = df[df['system'] == system_name]
    
    if system_df.empty:
        raise DataLoadError(f"No data found for system {system_name} in {input_path}")
    
    # Prepare features and target
    # Assuming target is 'segregation_energy' or similar. T021b uses prepare_features_and_target.
    # Let's use the helper from regression module if available, or reconstruct.
    # T021b imports load_interaction_terms. Let's use that.
    # But load_interaction_terms loads the whole file. We need to slice.
    
    # Re-implementing feature selection here for clarity after filtering
    feature_cols = [col for col in system_df.columns if col not in ['system', 'segregation_energy', 'temperature', 'bulk_concentration']]
    # Actually, T021a-Gen says columns are [Cr, Mo, Cr_Mo,...]. 
    # Let's assume the target is 'segregation_energy'.
    
    if 'segregation_energy' not in system_df.columns:
         # Try common aliases
         target_col = None
         for alias in ['target', 'energy', 'seg_energy']:
             if alias in system_df.columns:
                 target_col = alias
                 break
         if not target_col:
             raise DataLoadError(f"Target column 'segregation_energy' not found in {input_path}")
    else:
         target_col = 'segregation_energy'

    X = system_df[feature_cols].values
    y = system_df[target_col].values
    
    return X, y

def evaluate_transferability(
    train_system: str = "Fe-Cr-Mo",
    test_system: str = "Fe-Cr-V"
) -> Dict[str, Any]:
    """
    Train a linear regression model on the source system (Fe-Cr-Mo)
    and evaluate it on the held-out target system (Fe-Cr-V).
    Returns metrics: train_r2, test_r2, train_mse, test_mse, transferability_score.
    """
    logger.info(f"Starting transferability check: Train on {train_system}, Test on {test_system}")
    
    try:
        X_train, y_train = load_regression_data_for_system(train_system)
        X_test, y_test = load_regression_data_for_system(test_system)
    except DataLoadError as e:
        logger.error(f"Data loading failed: {e}")
        return {
            "status": "failed",
            "reason": str(e),
            "train_system": train_system,
            "test_system": test_system
        }

    if X_train.shape[0] == 0 or X_test.shape[0] == 0:
        return {
            "status": "failed",
            "reason": "Empty dataset after filtering",
            "train_system": train_system,
            "test_system": test_system
        }

    # Ensure feature dimensions match
    if X_train.shape[1] != X_test.shape[1]:
        logger.warning(f"Feature dimension mismatch: Train {X_train.shape[1]} vs Test {X_test.shape[1]}. Attempting to align.")
        # If dimensions don't match, we can't directly transfer. 
        # For this specific task, we assume the interaction terms are consistent across systems (same elements involved).
        # If not, we raise an error.
        raise DataLoadError(f"Feature mismatch between {train_system} and {test_system}. Cannot evaluate transferability.")

    # Train model
    model = LinearRegression()
    model.fit(X_train, y_train)
    
    # Predict
    y_train_pred = model.predict(X_train)
    y_test_pred = model.predict(X_test)
    
    # Metrics
    train_r2 = r2_score(y_train, y_train_pred)
    test_r2 = r2_score(y_test, y_test_pred)
    train_mse = mean_squared_error(y_train, y_train_pred)
    test_mse = mean_squared_error(y_test, y_test_pred)
    
    # Transferability score: ratio of test performance to train performance
    # Or simply the drop in R2
    transferability_score = test_r2 - train_r2
    
    result = {
        "status": "success",
        "train_system": train_system,
        "test_system": test_system,
        "train_r2": float(train_r2),
        "test_r2": float(test_r2),
        "train_mse": float(train_mse),
        "test_mse": float(test_mse),
        "transferability_score": float(transferability_score),
        "model_coefficients": model.coef_.tolist(),
        "model_intercept": float(model.intercept_)
    }
    
    logger.info(f"Transferability check complete. Train R2: {train_r2:.4f}, Test R2: {test_r2:.4f}")
    return result

def save_transferability_results(results: Dict[str, Any]) -> Path:
    """Save results to data/processed/transferability_results.json"""
    output_path = PROCESSED_PATH / "transferability_results.json"
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Results saved to {output_path}")
    return output_path

def main():
    """Main entry point for T031"""
    logger.info("Executing T031: Transferability Check")
    
    results = evaluate_transferability(
        train_system="Fe-Cr-Mo",
        test_system="Fe-Cr-V"
    )
    
    if results["status"] == "success":
        save_transferability_results(results)
    else:
        logger.warning(f"Transferability check failed: {results.get('reason')}")
        # Still save the failure record for logging
        save_transferability_results(results)
        
    return results

if __name__ == "__main__":
    main()
