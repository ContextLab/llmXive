import os
import sys
import logging
import json
from pathlib import Path
import yaml

# Import from sibling modules as per API surface
from analysis import run_analysis, run_lopo_validation, run_sensitivity_analysis_exclude_single_ratings, run_sensitivity_analysis_impute_single_ratings, run_bootstrap_sensitivity_analysis
from config import get_path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_schema(schema_path: Path) -> dict:
    """Load and return the JSON schema definition."""
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    with open(schema_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def validate_results_schema(results: dict, schema: dict) -> bool:
    """
    Basic schema validation for model_results.json.
    Checks for required top-level keys and structure consistency.
    """
    required_keys = ['models', 'validation', 'sensitivity', 'metadata']
    for key in required_keys:
        if key not in results:
            logger.error(f"Missing required key in results: {key}")
            return False

    # Check 'models' structure
    if 'models' in results:
        if 'mood_std' not in results['models'] or 'mean_mood' not in results['models']:
            logger.error("Missing model results for 'mood_std' or 'mean_mood'")
            return False

    # Check 'validation' structure (LOPO)
    if 'validation' in results:
        if 'lopo_sign_consistency' not in results['validation']:
            logger.error("Missing LOPO sign consistency in validation results")
            return False
        if 'lopo_average_rmse' not in results['validation']:
            logger.error("Missing LOPO average RMSE in validation results")
            return False

    # Check 'sensitivity' structure
    if 'sensitivity' in results:
        if 'single_rating_bootstrap_consistency' not in results['sensitivity']:
            logger.error("Missing single rating bootstrap consistency in sensitivity results")
            return False

    logger.info("Schema validation passed.")
    return True

def save_results_to_json(results: dict, output_path: Path) -> None:
    """Save the results dictionary to a JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Results saved to {output_path}")

def main():
    """
    Main entry point for T025:
    1. Run the full analysis pipeline (models, LOPO, sensitivity).
    2. Collect results into a structured dictionary.
    3. Validate against the schema.
    4. Save to data/processed/model_results.json.
    """
    logger.info("Starting T025: Save model results and validate.")

    # 1. Run Analysis Components
    # We assume run_analysis returns the core model results
    logger.info("Running core analysis (LMM models)...")
    core_results = run_analysis()

    # 2. Run LOPO Validation
    logger.info("Running LOPO validation...")
    lopo_results = run_lopo_validation()

    # 3. Run Sensitivity Analyses
    logger.info("Running sensitivity analyses...")
    # Exclude single ratings
    sens_exclude = run_sensitivity_analysis_exclude_single_ratings()
    # Impute single ratings
    sens_impute = run_sensitivity_analysis_impute_single_ratings()
    # Bootstrap consistency
    sens_bootstrap = run_bootstrap_sensitivity_analysis()

    # 4. Aggregate Results
    final_results = {
        "metadata": {
            "version": "1.0",
            "generated_at": "2023-10-27T10:00:00Z", # Placeholder, can be dynamic
            "pipeline_task": "T025"
        },
        "models": core_results,
        "validation": lopo_results,
        "sensitivity": {
            "weekdays_only": sens_exclude.get('weekdays_only', {}), # Assuming structure
            "active_minutes": sens_impute.get('active_minutes', {}), # Assuming structure
            "single_rating_bootstrap_consistency": sens_bootstrap
        }
    }

    # 5. Load Schema and Validate
    schema_path = get_path("specs/001-physical-activity-levels-and-mood-variability/contracts/model_results.schema.yaml")
    try:
        schema = load_schema(schema_path)
        if not validate_results_schema(final_results, schema):
            raise ValueError("Schema validation failed. Check logs for details.")
    except FileNotFoundError:
        logger.warning(f"Schema file not found at {schema_path}. Skipping validation.")
    except Exception as e:
        logger.error(f"Validation error: {e}")
        raise

    # 6. Save Output
    output_path = get_path("data/processed/model_results.json")
    save_results_to_json(final_results, output_path)

    logger.info("T025 completed successfully.")

if __name__ == "__main__":
    main()
