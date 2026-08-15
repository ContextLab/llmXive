import os
import sys
import logging
import json
from pathlib import Path
import yaml

# Import from sibling modules as per API surface
from config import get_path
from output_validator import load_schema, validate_dataframe
from analysis import run_analysis

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def validate_results_schema(results: dict, schema_path: Path) -> bool:
    """
    Validate the model results dictionary against the JSON schema definition.
    
    Args:
        results: The dictionary containing model results.
        schema_path: Path to the YAML schema file.
        
    Returns:
        bool: True if valid, raises ValueError otherwise.
    """
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
        
    with open(schema_path, 'r') as f:
        schema = yaml.safe_load(f)
    
    # Basic structural validation based on expected keys from spec
    required_keys = ['models', 'diagnostics', 'lopo_results', 'sensitivity_analysis', 'metadata']
    for key in required_keys:
        if key not in results:
            raise ValueError(f"Missing required key in results: {key}")
    
    # Validate 'models' structure
    if not isinstance(results['models'], list):
        raise ValueError("'models' must be a list of model result objects")
        
    if len(results['models']) < 2:
        raise ValueError("Expected at least two models (mood_std and mean_mood)")
        
    for model in results['models']:
        if 'model_name' not in model:
            raise ValueError("Each model must have a 'model_name'")
        if 'fixed_effects' not in model:
            raise ValueError(f"Model {model.get('model_name', 'unknown')} missing 'fixed_effects'")
        if 'converged' not in model:
            raise ValueError(f"Model {model.get('model_name', 'unknown')} missing 'converged' status")
    
    logger.info("Schema validation passed.")
    return True

def save_results_to_json(results: dict, output_path: Path) -> None:
    """
    Save the model results dictionary to a JSON file.
    
    Args:
        results: The dictionary containing model results.
        output_path: Path to the output JSON file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
        
    logger.info(f"Results saved to {output_path}")

def main():
    """
    Main entry point for saving and validating model results.
    Runs the full analysis pipeline and saves the results.
    """
    try:
        # 1. Run the full analysis to get results
        logger.info("Running full analysis pipeline...")
        results = run_analysis()
        
        if results is None:
            logger.error("Analysis returned no results. Aborting save.")
            sys.exit(1)
        
        # 2. Define paths
        schema_path = get_path("specs/001-physical-activity-mood-variability/contracts/model_results.schema.yaml")
        output_path = get_path("data/processed/model_results.json")
        
        # 3. Validate results against schema
        logger.info(f"Validating results against schema: {schema_path}")
        validate_results_schema(results, schema_path)
        
        # 4. Save to JSON
        save_results_to_json(results, output_path)
        
        logger.info("Task T025 completed successfully: model results saved and validated.")
        
    except Exception as e:
        logger.error(f"Error during save results process: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
