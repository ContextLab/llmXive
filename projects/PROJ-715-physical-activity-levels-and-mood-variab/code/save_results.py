import os
import sys
import logging
import json
from pathlib import Path
import yaml

# Add project root to path for imports if running as script
if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(project_root))

from config import get_path, init_logger
from analysis import run_analysis

logger = init_logger("save_results")

def load_schema(schema_path: str) -> dict:
    """Load a YAML schema definition."""
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def validate_results_schema(results: dict, schema: dict) -> bool:
    """
    Validate model results against the schema.
    Checks for required top-level keys and nested structures.
    """
    required_keys = ['model_type', 'fixed_effects', 'random_effects', 'model_fit', 'validation', 'sensitivity']
    
    for key in required_keys:
        if key not in results:
            logger.error(f"Missing required key in results: {key}")
            return False
        
    # Validate nested structures roughly
    if not isinstance(results['fixed_effects'], dict):
        logger.error("fixed_effects must be a dict")
        return False
    
    if not isinstance(results['random_effects'], dict):
        logger.error("random_effects must be a dict")
        return False

    if not isinstance(results['validation'], dict):
        logger.error("validation must be a dict")
        return False
        
    if not isinstance(results['sensitivity'], dict):
        logger.error("sensitivity must be a dict")
        return False

    logger.info("Schema validation passed.")
    return True

def save_results_to_json(results: dict, output_path: str) -> None:
    """Save results dictionary to a JSON file."""
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Results saved to {output_path}")

def main():
    """
    Main entry point to run analysis and save results.
    This function orchestrates the full analysis pipeline and ensures
    the final model_results.json is written to disk.
    """
    logger.info("Starting results generation pipeline")
    
    # 1. Run the full analysis (fits models, diagnostics, LOPO, sensitivity)
    # This returns the consolidated results dictionary
    try:
        results = run_analysis()
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        sys.exit(1)

    if not results:
        logger.error("Analysis returned no results.")
        sys.exit(1)

    # 2. Define output path
    output_path = get_path('data', 'processed', 'model_results.json')
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # 3. Validate against schema
    schema_path = get_path("specs", "001-physical-activity-levels-and-mood-variability", "contracts", "model_results.schema.yaml")
    
    if not os.path.exists(schema_path):
        logger.warning(f"Schema file not found at {schema_path}. Skipping validation.")
    else:
        try:
            schema = load_schema(schema_path)
            if not validate_results_schema(results, schema):
                logger.error("Schema validation failed. Aborting save.")
                sys.exit(1)
        except Exception as e:
            logger.error(f"Error during schema validation: {e}")
            sys.exit(1)

    # 4. Save to disk
    try:
        save_results_to_json(results, output_path)
        logger.info("Pipeline completed successfully.")
    except Exception as e:
        logger.error(f"Failed to save results: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
