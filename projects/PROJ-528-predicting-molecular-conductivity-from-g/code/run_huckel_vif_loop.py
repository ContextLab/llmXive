"""
Run the full VIF loop and model training including the Hückel resonance energy feature.
This script re-evaluates the model performance with the new descriptor.
"""
import os
import sys
import json
import logging
import argparse
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional

# Import from existing modules
from code.descriptors import compute_huckel_resonance_energy, compute_all_descriptors
from code.analysis import run_vif_iterative_loop, calculate_vif, exclude_high_vif_features, train_and_evaluate_model, update_model_results
from code.model_training import train_models, run_cross_validation, save_model_results, select_target_variable
from code.scaffold_split import scaffold_split
from code.config import SEED, DATA_PATH, RAW_DATA_PATH, TARGET_VAR, OUTLIER_SIGMA
from code.logging_config import setup_logging
from code.data_loader import load_processed_data
from code.outlier_utils import apply_threshold_filter

def load_augmented_descriptors(path: str = 'data/processed/descriptors_augmented.csv') -> pd.DataFrame:
    """Load the augmented descriptors including Hückel resonance energy."""
    if not os.path.exists(path):
        # Fallback to base descriptors if augmented not found, but log warning
        logging.warning(f"Augmented descriptors not found at {path}. Attempting to load base descriptors.")
        path = 'data/processed/descriptors.csv'
        if not os.path.exists(path):
            raise FileNotFoundError(f"Neither augmented nor base descriptors found at {path}")
    
    df = pd.read_csv(path)
    logging.info(f"Loaded {len(df)} molecules from {path}")
    return df

def run_huckel_vif_evaluation(
    df: pd.DataFrame,
    target_col: str = None,
    outlier_sigma: float = 3.0,
    vif_threshold: float = 10.0,
    output_results: str = 'data/processed/huckel_impact_report.json',
    output_vif_log: str = 'data/processed/vif_huckel_iteration_log.json'
) -> Dict[str, Any]:
    """
    Run the full VIF loop and model training including the Hückel resonance energy feature.
    
    Args:
        df: DataFrame with descriptors and target
        target_col: Name of the target column (conductivity or HOMO_LUMO_gap)
        outlier_sigma: Sigma threshold for outlier filtering
        vif_threshold: VIF threshold for feature exclusion
        output_results: Path to save final results
        output_vif_log: Path to save VIF iteration log
    
    Returns:
        Dictionary with results
    """
    if target_col is None:
        # Determine target column
        if 'conductivity' in df.columns:
            target_col = 'conductivity'
        elif 'HOMO_LUMO_gap' in df.columns:
            target_col = 'HOMO_LUMO_gap'
        else:
            raise ValueError("No valid target column found in DataFrame")
    
    logging.info(f"Using target variable: {target_col}")
    
    # Filter outliers
    logging.info(f"Filtering outliers with sigma={outlier_sigma}")
    df_filtered = apply_threshold_filter(df, target_col=target_col, sigma_threshold=outlier_sigma)
    logging.info(f"Filtered from {len(df)} to {len(df_filtered)} rows")
    
    if len(df_filtered) == 0:
        raise ValueError("No data remaining after outlier filtering")
    
    # Prepare features (exclude non-feature columns)
    feature_cols = [col for col in df_filtered.columns if col not in ['smiles', target_col, f'log_{target_col}']]
    
    # Ensure Hückel feature is present
    if 'huckel_resonance_energy' not in feature_cols:
        logging.warning("Hückel resonance energy feature not found in descriptors. Skipping VIF loop.")
        return {"error": "Hückel feature missing"}
    
    # Split data using scaffold split
    logging.info("Performing scaffold split")
    train_idx, test_idx = scaffold_split(df_filtered, seed=SEED)
    X_train = df_filtered.loc[train_idx, feature_cols].values
    y_train = df_filtered.loc[train_idx, target_col].values
    X_test = df_filtered.loc[test_idx, feature_cols].values
    y_test = df_filtered.loc[test_idx, target_col].values
    
    # Log transform target
    y_train_log = np.log(y_train)
    y_test_log = np.log(y_test)
    
    # Run VIF iterative loop
    logging.info("Starting VIF iterative loop")
    vif_log = run_vif_iterative_loop(
        X_train=X_train,
        y_train=y_train_log,
        feature_names=feature_cols,
        vif_threshold=vif_threshold,
        seed=SEED
    )
    
    # Save VIF log
    with open(output_vif_log, 'w') as f:
        json.dump(vif_log, f, indent=2)
    logging.info(f"VIF iteration log saved to {output_vif_log}")
    
    # Get final feature set
    final_features = vif_log.get('final_features', feature_cols)
    if not final_features:
        raise ValueError("All features were excluded by VIF filtering")
    
    logging.info(f"Final feature set: {final_features}")
    
    # Retrain models on final feature set
    X_train_final = df_filtered.loc[train_idx, final_features].values
    X_test_final = df_filtered.loc[test_idx, final_features].values
    
    # Train models
    rf_model, gb_model, rf_metrics, gb_metrics = train_models(
        X_train=X_train_final,
        y_train=y_train_log,
        X_test=X_test_final,
        y_test=y_test_log,
        seed=SEED
    )
    
    # Cross-validation
    cv_scores_rf = run_cross_validation(rf_model, X_train_final, y_train_log)
    cv_scores_gb = run_cross_validation(gb_model, X_train_final, y_train_log)
    
    # Prepare results
    results = {
        "target_variable": target_col,
        "outlier_sigma": outlier_sigma,
        "vif_threshold": vif_threshold,
        "initial_features": feature_cols,
        "final_features": final_features,
        "vif_iterations": vif_log.get('iterations', []),
        "rf_r2": rf_metrics['r2'],
        "rf_mae": rf_metrics['mae'],
        "rf_cv_mean": np.mean(cv_scores_rf),
        "rf_cv_std": np.std(cv_scores_rf),
        "gb_r2": gb_metrics['r2'],
        "gb_mae": gb_metrics['mae'],
        "gb_cv_mean": np.mean(cv_scores_gb),
        "gb_cv_std": np.std(cv_scores_gb),
        "huckel_feature_included": 'huckel_resonance_energy' in final_features
    }
    
    # Save results
    with open(output_results, 'w') as f:
        json.dump(results, f, indent=2)
    logging.info(f"Results saved to {output_results}")
    
    return results

def main():
    parser = argparse.ArgumentParser(description="Run VIF loop and model training with Hückel feature")
    parser.add_argument('--data', type=str, default='data/processed/descriptors_augmented.csv',
                        help='Path to augmented descriptors CSV')
    parser.add_argument('--output', type=str, default='data/processed/huckel_impact_report.json',
                        help='Path to output results JSON')
    parser.add_argument('--vif-log', type=str, default='data/processed/vif_huckel_iteration_log.json',
                        help='Path to VIF iteration log JSON')
    parser.add_argument('--target', type=str, default=None,
                        help='Target column name (default: auto-detect)')
    parser.add_argument('--outlier-sigma', type=float, default=3.0,
                        help='Sigma threshold for outlier filtering')
    parser.add_argument('--vif-threshold', type=float, default=10.0,
                        help='VIF threshold for feature exclusion')
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging()
    logging.info("Starting Hückel VIF evaluation")
    
    try:
        # Load data
        df = load_augmented_descriptors(args.data)
        
        # Run evaluation
        results = run_huckel_vif_evaluation(
            df=df,
            target_col=args.target,
            outlier_sigma=args.outlier_sigma,
            vif_threshold=args.vif_threshold,
            output_results=args.output,
            output_vif_log=args.vif_log
        )
        
        logging.info("Hückel VIF evaluation completed successfully")
        print(json.dumps(results, indent=2))
        
    except Exception as e:
        logging.error(f"Error during Hückel VIF evaluation: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == '__main__':
    main()
