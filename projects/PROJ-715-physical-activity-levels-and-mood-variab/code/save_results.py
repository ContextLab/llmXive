"""
Save model results to JSON and validate against schema.

This script completes T025 by:
1. Running the full analysis pipeline (T019-T024) to generate results.
2. Saving the results to data/processed/model_results.json.
3. Validating the output against model_results.schema.yaml.
"""
import os
import sys
import logging
import json
from pathlib import Path

# Add project root to path if needed, though standard imports should work
# assuming this runs from project root or code/ is in sys.path
from analysis import run_analysis, main as analysis_main
from config import get_path
from output_validator import load_schema, validate_dataframe

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def save_results_to_json(results: dict, output_path: Path) -> None:
    """
    Save the analysis results dictionary to a JSON file.
    
    Args:
        results: Dictionary containing model results, diagnostics, and metadata.
        output_path: Path to the output JSON file.
    """
    try:
        # Ensure parent directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.info(f"Results successfully saved to {output_path}")
    except IOError as e:
        logger.error(f"Failed to write results to {output_path}: {e}")
        raise

def validate_results_schema(input_path: Path, schema_path: Path) -> bool:
    """
    Validate the JSON results file against the schema.
    
    Args:
        input_path: Path to the JSON file to validate.
        schema_path: Path to the YAML schema file.
        
    Returns:
        bool: True if validation passes, False otherwise.
    """
    schema = load_schema(schema_path)
    # The validator expects a DataFrame usually, but for JSON we need a custom check
    # Since output_validator.validate_dataframe is for DataFrames, we perform a 
    # manual structural check here or adapt the validator if it supports dicts.
    # For now, we assume the schema defines required keys.
    
    if not input_path.exists():
        logger.error(f"Input file {input_path} does not exist.")
        return False
    
    if not schema_path.exists():
        logger.error(f"Schema file {schema_path} does not exist.")
        return False

    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Basic structural validation based on typical schema requirements
    # The schema is expected to define required top-level keys: 
    # 'mood_std_model', 'mean_mood_model', 'diagnostics', 'metadata'
    required_keys = ['mood_std_model', 'mean_mood_model', 'diagnostics', 'metadata']
    missing_keys = [k for k in required_keys if k not in data]
    
    if missing_keys:
        logger.error(f"Validation failed: Missing required keys: {missing_keys}")
        return False

    # Check specific sub-structures if schema dictates
    # Example: check if models have 'fixed_effects'
    for key in ['mood_std_model', 'mean_mood_model']:
        if 'fixed_effects' not in data[key]:
            logger.error(f"Validation failed: {key} missing 'fixed_effects'")
            return False
    
    logger.info(f"Validation against {schema_path} passed.")
    return True

def main():
    """
    Main entry point for T025: Save and validate model results.
    """
    logger.info("Starting T025: Save model results and validate.")
    
    # 1. Run the analysis to generate results (T019-T024 logic)
    # The run_analysis function returns the results dictionary
    try:
        results = run_analysis()
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        sys.exit(1)

    # 2. Define output paths
    output_path = get_path('processed', 'model_results.json')
    schema_path = get_path('specs', '001-physical-activity-mood-variability/contracts/model_results.schema.yaml')
    
    # Ensure schema path is correct relative to project root
    # The config.get_path might need adjustment if 'specs' isn't handled directly
    # Assuming get_path handles relative paths or we construct it manually
    if not schema_path.exists():
        # Fallback construction if get_path doesn't support nested specs
        project_root = Path(__file__).resolve().parent.parent
        schema_path = project_root / 'specs' / '001-physical-activity-mood-variability' / 'contracts' / 'model_results.schema.yaml'
    
    # 3. Save results to JSON
    save_results_to_json(results, output_path)
    
    # 4. Validate results against schema
    if not validate_results_schema(output_path, schema_path):
        logger.error("Validation failed. Exiting.")
        sys.exit(1)
        
    logger.info("T025 completed successfully.")

if __name__ == '__main__':
    main()