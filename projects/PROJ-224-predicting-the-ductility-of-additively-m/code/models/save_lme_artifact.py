"""
Save the MixedEffectsResult artifact.

This module loads the results extracted by lme_model.py (which includes
fixed effects coefficients, random effects, convergence status, and diagnostics),
packages them into a structured artifact, and saves them to `artifacts/mixed_effects_result.json`.

It ensures the artifact contains:
- metrics: R², AIC, BIC, convergence status, p-values, CIs.
- random_effects: intercept estimates per alloy family.
- model_spec: formula and predictor list.
"""
import os
import sys
import logging
import json
import pandas as pd
import numpy as np
from pathlib import Path

# Ensure code is in path for imports
code_dir = Path(__file__).resolve().parent.parent
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from models.lme_model import extract_results, load_data, prepare_features, fit_lme_model

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

ARTIFACT_PATH = Path("artifacts/mixed_effects_result.json")

def save_lme_artifact(results_dict: dict, output_path: str = None) -> str:
    """
    Save the LME results dictionary to a JSON file.

    Args:
        results_dict: Dictionary containing the extracted results from fit_lme_model.
        output_path: Path to save the artifact. Defaults to artifacts/mixed_effects_result.json.

    Returns:
        str: Path to the saved artifact.
    """
    if output_path is None:
        output_path = str(ARTIFACT_PATH)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Ensure numpy types are converted to native Python types for JSON serialization
    def convert_for_json(obj):
        if isinstance(obj, (np.integer, np.int64, np.int32)):
            return int(obj)
        if isinstance(obj, (np.floating, np.float64, np.float32)):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, dict):
            return {k: convert_for_json(v) for k, v in obj.items()}
        if isinstance(obj, (list, tuple)):
            return [convert_for_json(i) for i in obj]
        return obj

    clean_results = convert_for_json(results_dict)

    with open(output_path, 'w') as f:
        json.dump(clean_results, f, indent=2)

    logger.info(f"MixedEffectsResult artifact saved to: {output_path}")
    return str(output_path)

def main():
    """
    Main entry point to run the LME model and save the artifact.
    This function orchestrates the full flow: load data -> fit model -> extract -> save.
    """
    logger.info("Starting MixedEffectsResult artifact generation...")

    try:
        # 1. Load Data
        data_path = Path("data/curated_builds.csv")
        if not data_path.exists():
            logger.error(f"Data file not found: {data_path}")
            sys.exit(1)

        df = load_data(data_path)
        
        # 2. Prepare Features (based on VIF logic in T023)
        # We assume the VIF logic has already been applied or is part of the pipeline flow.
        # For this artifact generation, we rely on the specific predictors selected.
        # The lme_model.py expects specific column names.
        df_processed, feature_cols, target_col = prepare_features(df)

        if df_processed.empty:
            logger.error("Processed data is empty after feature preparation.")
            sys.exit(1)

        # 3. Fit Model
        logger.info("Fitting Linear Mixed-Effects model...")
        model, is_converged = fit_lme_model(df_processed, feature_cols, target_col)

        if not is_converged:
            logger.warning("Model did not converge. Saving results with convergence_failed=True.")

        # 4. Extract Results
        logger.info("Extracting model results...")
        # extract_results expects the model object and the dataframe used for fitting
        results_dict = extract_results(model, df_processed, feature_cols, target_col)
        
        # Add convergence status explicitly if not already in extract_results
        results_dict['convergence_status'] = 'converged' if is_converged else 'failed'
        results_dict['artifact_version'] = '1.0.0'

        # 5. Save Artifact
        artifact_path = save_lme_artifact(results_dict)
        
        logger.info(f"Artifact generation complete: {artifact_path}")
        return 0

    except Exception as e:
        logger.exception(f"Failed to generate MixedEffectsResult artifact: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
