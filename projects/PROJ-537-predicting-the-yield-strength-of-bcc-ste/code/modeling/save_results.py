import os
import sys
import json
import logging
import pickle
from pathlib import Path
from typing import Dict, Any, Optional
import yaml

from config import CONFIG
from utils.logging import get_logger

logger = get_logger(__name__)

def load_schema_contracts() -> Dict[str, Any]:
    """Load the output schema from contracts/output.schema.yaml."""
    schema_path = CONFIG.OUTPUT_SCHEMA_PATH
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, 'r') as f:
        schema = yaml.safe_load(f)
    
    logger.info(f"Loaded schema from {schema_path}")
    return schema

def validate_output_against_schema(data: Dict[str, Any], schema: Dict[str, Any]) -> bool:
    """
    Perform basic validation of output data against the schema.
    Checks for required fields and basic type constraints.
    """
    required_fields = schema.get('required', [])
    properties = schema.get('properties', {})
    
    # Check required fields
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        logger.error(f"Missing required fields in output: {missing_fields}")
        return False
    
    # Check field types
    for field, value in data.items():
        if field in properties:
            expected_type = properties[field].get('type')
            if expected_type:
                if expected_type == 'number' and not isinstance(value, (int, float)):
                    logger.error(f"Field '{field}' should be a number, got {type(value)}")
                    return False
                elif expected_type == 'string' and not isinstance(value, str):
                    logger.error(f"Field '{field}' should be a string, got {type(value)}")
                    return False
                elif expected_type == 'boolean' and not isinstance(value, bool):
                    logger.error(f"Field '{field}' should be a boolean, got {type(value)}")
                    return False
                elif expected_type == 'array' and not isinstance(value, list):
                    logger.error(f"Field '{field}' should be an array, got {type(value)}")
                    return False
                elif expected_type == 'object' and not isinstance(value, dict):
                    logger.error(f"Field '{field}' should be an object, got {type(value)}")
                    return False
    
    logger.info("Output validation passed against schema")
    return True

def assemble_final_metrics() -> Dict[str, Any]:
    """
    Load all results from modeling and interpretability pipelines
    and assemble them into the final output structure.
    """
    output = {}
    
    # Load modeling results (from evaluate.py)
    eval_results_path = CONFIG.EVALUATION_RESULTS_PATH
    if eval_results_path.exists():
        with open(eval_results_path, 'r') as f:
            eval_data = json.load(f)
        output['modeling'] = eval_data
        logger.info(f"Loaded modeling results from {eval_results_path}")
    else:
        logger.warning(f"Evaluation results not found at {eval_results_path}")
    
    # Load correlation results
    correlation_path = CONFIG.CORRELATION_RESULTS_PATH
    if correlation_path.exists():
        with open(correlation_path, 'r') as f:
            corr_data = json.load(f)
        output['correlation_analysis'] = corr_data
        logger.info(f"Loaded correlation results from {correlation_path}")
    else:
        logger.warning(f"Correlation results not found at {correlation_path}")
    
    # Load interpretability results (from bootstrap_stability.py)
    bootstrap_path = CONFIG.BOOTSTRAP_RESULTS_PATH
    if bootstrap_path.exists():
        with open(bootstrap_path, 'r') as f:
            bootstrap_data = json.load(f)
        output['interpretability'] = bootstrap_data
        logger.info(f"Loaded interpretability results from {bootstrap_path}")
    else:
        logger.warning(f"Interpretability results not found at {bootstrap_path}")
    
    # Load SHAP results if available
    shap_path = CONFIG.SHAP_RESULTS_PATH
    if shap_path.exists():
        with open(shap_path, 'r') as f:
            shap_data = json.load(f)
        output['shap_analysis'] = shap_data
        logger.info(f"Loaded SHAP results from {shap_path}")
    else:
        logger.warning(f"SHAP results not found at {shap_path}")
    
    # Add metadata
    output['metadata'] = {
        'project_id': 'PROJ-537-predicting-the-yield-strength-of-bcc-ste',
        'pipeline_version': '1.0.0',
        'data_source': 'MatNavi/NIST + Materials Project API',
        'timestamp': str(Path.home())  # Placeholder for actual timestamp
    }
    
    return output

def write_output_json(data: Dict[str, Any], output_path: Path) -> None:
    """Write the final metrics to the output JSON file."""
    # Ensure parent directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2, default=str)
    
    logger.info(f"Wrote final metrics to {output_path}")

def main():
    """Main entry point for T032: Write final metrics to output.json."""
    try:
        logger.info("Starting T032: Assembling and writing final metrics")
        
        # Load schema
        schema = load_schema_contracts()
        
        # Assemble final metrics
        final_metrics = assemble_final_metrics()
        
        # Validate against schema
        if not validate_output_against_schema(final_metrics, schema):
            logger.error("Final metrics failed schema validation")
            sys.exit(1)
        
        # Write to output file
        output_path = CONFIG.OUTPUT_JSON_PATH
        write_output_json(final_metrics, output_path)
        
        logger.info("T032 completed successfully")
        print(f"Final metrics written to {output_path}")
        
    except Exception as e:
        logger.error(f"T032 failed: {e}")
        raise

if __name__ == '__main__':
    main()
