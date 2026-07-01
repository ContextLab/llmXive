import os
import sys
import logging
import json
import pandas as pd
import numpy as np
from pathlib import Path

# Ensure project root is in path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from models.lme_model import load_data, prepare_features, fit_lme_model, extract_results
from data.preprocessing import perform_vif_analysis
from analysis.sensitivity import run_diagnostics

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def save_lme_artifact(
    model_results: dict,
    output_path: Path
) -> None:
    """
    Saves the MixedEffectsResult artifact as JSON.
    
    Args:
        model_results: Dictionary containing all metrics, convergence status, 
                       fixed effects, and random effects.
        output_path: Path to save the JSON artifact.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Convert numpy types to native Python types for JSON serialization
    def convert_numpy_types(obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, (np.int64, np.int32)):
            return int(obj)
        elif isinstance(obj, (np.float64, np.float32)):
            return float(obj)
        elif isinstance(obj, dict):
            return {k: convert_numpy_types(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_numpy_types(i) for i in obj]
        return obj

    clean_results = convert_numpy_types(model_results)
    
    with open(output_path, 'w') as f:
        json.dump(clean_results, f, indent=2)
    
    logger.info(f"Saved MixedEffectsResult artifact to {output_path}")

def main():
    """
    Main entry point to generate and save the MixedEffectsResult artifact.
    """
    logger.info("Starting LME Artifact Generation (Task T027)")
    
    # Paths
    curated_data_path = PROJECT_ROOT / "data" / "curated_builds.csv"
    output_path = PROJECT_ROOT / "artifacts" / "mixed_effects_result.json"
    
    if not curated_data_path.exists():
        logger.error(f"Curated data not found at {curated_data_path}. Please run acquisition and cleaning first.")
        sys.exit(1)

    try:
        # 1. Load Data
        logger.info(f"Loading data from {curated_data_path}")
        df = load_data(curated_data_path)
        
        # 2. Prepare Features (VIF analysis happens here internally or before)
        # Note: T023 handles VIF filtering. We assume the data passed here 
        # is already filtered or we re-run the filter to be safe.
        # For T027, we assume the data is ready for modeling.
        df_processed, predictors = prepare_features(df)
        
        if df_processed.empty:
            logger.error("Processed dataframe is empty. Cannot fit model.")
            sys.exit(1)

        # 3. Fit Model
        logger.info("Fitting Linear Mixed-Effects Model...")
        model, fixed_effects, random_effects, convergence_status = fit_lme_model(
            df_processed, 
            predictors, 
            target_col="ductility", 
            group_col="alloy_family"
        )
        
        if not convergence_status:
            logger.warning("Model failed to converge. Saving results with convergence_failed=True.")

        # 4. Extract Results (Standardized Coeffs, CIs, P-values, Partial R2, etc.)
        logger.info("Extracting model results...")
        # Run diagnostics to get partial R2 and likelihood ratio test results
        diagnostics = run_diagnostics(model, df_processed, predictors, target_col="ductility")
        
        results_dict = extract_results(
            model, 
            fixed_effects, 
            random_effects, 
            convergence_status,
            diagnostics
        )
        
        # 5. Save Artifact
        logger.info("Saving artifact...")
        save_lme_artifact(results_dict, output_path)
        
        logger.info("Task T027 completed successfully.")
        
    except Exception as e:
        logger.error(f"Error during T027 execution: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()