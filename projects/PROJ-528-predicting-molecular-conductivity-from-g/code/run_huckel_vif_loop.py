import os
import sys
import json
import logging
import argparse
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple

# Import from existing API surface
from code.logging_config import setup_logging
from code.analysis import (
    calculate_vif,
    exclude_high_vif_features,
    train_and_evaluate_model,
    run_vif_iterative_loop,
    update_model_results
)
from code.model_training import train_models, apply_log_transformation, select_target_variable
from code.scaffold_split import scaffold_split
from code.config import SEED, TARGET_VAR, VIF_THRESHOLD, DATA_PATH, RAW_DATA_PATH
from code.data_loader import load_processed_data

logger = logging.getLogger(__name__)

def load_augmented_descriptors(path: str) -> pd.DataFrame:
    """Load the augmented descriptors including Hückel resonance energy."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Augmented descriptors file not found: {path}")
    df = pd.read_csv(path)
    logger.info(f"Loaded {len(df)} rows from {path}")
    if 'huckel_resonance_energy' not in df.columns:
        raise ValueError("huckel_resonance_energy column missing in descriptors")
    return df

def run_huckel_vif_evaluation(
    descriptors_path: str,
    results_output_path: str,
    vif_log_path: str = "data/processed/huckel_vif_iteration_log.json"
) -> Dict[str, Any]:
    """
    Re-run the full VIF loop and model training including the new huckel_resonance_energy feature.
    1. Load augmented descriptors.
    2. Run VIF filtering loop (iterative exclusion of VIF > 10).
    3. Train models (RF, GB) on the filtered set.
    4. Save results to huckel_impact_report.json.
    """
    # Load data
    df = load_augmented_descriptors(descriptors_path)

    # Identify target and features
    # T026 logic: Check for conductivity or HOMO_LUMO_gap
    target_col = None
    if 'conductivity' in df.columns:
        target_col = 'conductivity'
    elif 'HOMO_LUMO_gap' in df.columns:
        target_col = 'HOMO_LUMO_gap'
    else:
        raise ValueError("No valid target variable found (conductivity or HOMO_LUMO_gap)")

    logger.info(f"Using target variable: {target_col}")

    # Prepare features (exclude non-feature columns)
    feature_cols = [c for c in df.columns if c not in ['smiles', target_col, 'valid', 'error_msg']]
    X = df[feature_cols].dropna()
    y = df.loc[X.index, target_col]

    # Log transform target if needed (per T028)
    if target_col == 'conductivity':
        # Assuming log transform is standard for conductivity
        y = np.log(y + 1e-9) # Avoid log(0)
        target_col_log = f"log_{target_col}"
        y.name = target_col_log
    else:
        # For HOMO-LUMO, check if log transform is appropriate or use raw
        # T028 says "Implement log-transformation of the selected target variable"
        # We will apply it consistently as per spec T028
        y = np.log(y + 1e-9)
        target_col_log = f"log_{target_col}"
        y.name = target_col_log

    # Re-run VIF loop
    logger.info("Starting VIF iterative loop with Hückel feature...")
    vif_log, final_X, final_features, final_r2, final_mae = run_vif_iterative_loop(
        X, y, target_col_log, VIF_THRESHOLD, SEED
    )

    # Save VIF log
    os.makedirs(os.path.dirname(vif_log_path), exist_ok=True)
    with open(vif_log_path, 'w') as f:
        json.dump(vif_log, f, indent=2)
    logger.info(f"VIF iteration log saved to {vif_log_path}")

    # Final Model Training on filtered data (T029)
    # Note: run_vif_iterative_loop likely trained internally, but we ensure final save
    logger.info("Training final models on VIF-filtered data...")
    rf_model, gb_model, r2_rf, r2_gb, mae_rf, mae_gb = train_and_evaluate_model(
        final_X, y, SEED
    )

    # Prepare results
    results = {
        "final_features": final_features,
        "vif_iterations": vif_log.get("iterations", []),
        "final_metrics": {
            "rf_r2": float(r2_rf),
            "rf_mae": float(mae_rf),
            "gb_r2": float(r2_gb),
            "gb_mae": float(mae_gb)
        },
        "target_variable": target_col,
        "huckel_feature_included": 'huckel_resonance_energy' in final_features
    }

    # Save results
    os.makedirs(os.path.dirname(results_output_path), exist_ok=True)
    with open(results_output_path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Results saved to {results_output_path}")

    return results

def main():
    parser = argparse.ArgumentParser(description="Re-evaluate model with Hückel feature (T064)")
    parser.add_argument("--data", type=str, default="data/processed/descriptors_augmented.csv",
                        help="Path to augmented descriptors CSV")
    parser.add_argument("--output", type=str, default="data/processed/huckel_impact_report.json",
                        help="Path to output results JSON")
    parser.add_argument("--vif-log", type=str, default="data/processed/huckel_vif_iteration_log.json",
                        help="Path to VIF iteration log")
    args = parser.parse_args()

    setup_logging()
    logger.info("Starting T064: Re-evaluate Model with Hückel Feature")

    try:
        results = run_huckel_vif_evaluation(
            descriptors_path=args.data,
            results_output_path=args.output,
            vif_log_path=args.vif_log
        )
        logger.info(f"T064 Complete. R2 RF: {results['final_metrics']['rf_r2']:.4f}, R2 GB: {results['final_metrics']['gb_r2']:.4f}")
    except Exception as e:
        logger.error(f"T064 Failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
