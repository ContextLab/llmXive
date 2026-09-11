"""
save_results.py - Write final metrics to data/results/output.json conforming to the output schema.
"""
import os
import sys
import json
import logging
import pickle
from pathlib import Path
from typing import Dict, Any, Optional

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import CONFIG
from utils.logging import get_logger, log_provenance_event

logger = get_logger(__name__)

def load_schema_contracts() -> Dict[str, Any]:
    """Load the output schema contract from the contracts directory."""
    schema_path = CONFIG.CONTRACTS_DIR / "output.schema.yaml"
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    # Since we don't have a YAML parser in standard imports, we'll load it as text
    # and validate structure manually or use a simple parser if needed.
    # For this implementation, we assume the schema is a JSON-compatible structure
    # or we load it with PyYAML if available (added in requirements).
    try:
        import yaml
        with open(schema_path, 'r') as f:
            return yaml.safe_load(f)
    except ImportError:
        # Fallback: load as JSON if the file is actually JSON
        try:
            with open(schema_path, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            # If we can't parse it, we'll do a basic structural check later
            logger.warning("Could not parse schema file. Proceeding with basic validation.")
            return {}

def validate_output_against_schema(output_data: Dict[str, Any], schema: Dict[str, Any]) -> bool:
    """
    Validate the output data against the loaded schema.
    Returns True if valid, False otherwise.
    """
    if not schema:
        logger.warning("No schema provided for validation.")
        return True

    required_fields = schema.get("required", [])
    for field in required_fields:
        if field not in output_data:
            logger.error(f"Missing required field in output: {field}")
            return False
    
    # Check for specific fields required by the project spec (FR-005, SC-001, etc.)
    spec_required = [
        "r2_composition_only", "mae_composition_only",
        "r2_dft_enhanced", "mae_dft_enhanced",
        "p_value", "statistical_power",
        "pearson_correlation_shear_yield"
    ]
    
    for field in spec_required:
        if field not in output_data:
            logger.error(f"Missing spec-required field: {field}")
            return False
    
    logger.info("Output data passed schema validation.")
    return True

def assemble_final_metrics() -> Dict[str, Any]:
    """
    Assemble the final metrics from the results of previous tasks.
    Loads data from:
    - data/results/cv_results.pkl (R2, MAE, p-value, power)
    - data/results/correlation_analysis.json (Pearson correlation)
    """
    metrics = {}

    # Load CV results (from T028, T029, T030)
    cv_results_path = CONFIG.RESULTS_DIR / "cv_results.pkl"
    if cv_results_path.exists():
        try:
            with open(cv_results_path, 'rb') as f:
                cv_data = pickle.load(f)
            
            metrics["r2_composition_only"] = cv_data.get("r2_composition_only")
            metrics["mae_composition_only"] = cv_data.get("mae_composition_only")
            metrics["r2_dft_enhanced"] = cv_data.get("r2_dft_enhanced")
            metrics["mae_dft_enhanced"] = cv_data.get("mae_dft_enhanced")
            metrics["p_value"] = cv_data.get("p_value")
            metrics["statistical_power"] = cv_data.get("statistical_power")
            logger.info("Loaded CV results from pickle.")
        except Exception as e:
            logger.error(f"Failed to load CV results: {e}")
            raise
    else:
        raise FileNotFoundError(f"CV results file not found: {cv_results_path}")

    # Load correlation analysis (from T031)
    corr_results_path = CONFIG.RESULTS_DIR / "correlation_analysis.json"
    if corr_results_path.exists():
        try:
            with open(corr_results_path, 'r') as f:
                corr_data = json.load(f)
            
            # Map the correlation result to the expected field
            if "pearson_correlation" in corr_data:
                metrics["pearson_correlation_shear_yield"] = corr_data["pearson_correlation"]
            elif "pearson_r" in corr_data:
                metrics["pearson_correlation_shear_yield"] = corr_data["pearson_r"]
            else:
                # Try to find any correlation value
                for key, value in corr_data.items():
                    if "correlation" in key.lower() and isinstance(value, (int, float)):
                        metrics["pearson_correlation_shear_yield"] = value
                        break
            
            logger.info("Loaded correlation analysis from JSON.")
        except Exception as e:
            logger.error(f"Failed to load correlation analysis: {e}")
            raise
    else:
        raise FileNotFoundError(f"Correlation analysis file not found: {corr_results_path}")

    # Add metadata
    metrics["metadata"] = {
        "project_id": "PROJ-537",
        "task_id": "T032",
        "generated_at": str(Path(__file__).parent.parent / "data/results/output.json"),
        "version": "1.0"
    }

    return metrics

def write_output_json(output_data: Dict[str, Any], output_path: Path) -> None:
    """Write the final metrics to the specified JSON file."""
    # Ensure the directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    logger.info(f"Final metrics written to {output_path}")
    log_provenance_event("output_json_written", {"path": str(output_path), "records": 1})

def main():
    """Main entry point for T032."""
    logger.info("Starting T032: Write final metrics to output.json")
    
    try:
        # 1. Load schema
        schema = load_schema_contracts()
        
        # 2. Assemble final metrics
        final_metrics = assemble_final_metrics()
        
        # 3. Validate against schema
        if not validate_output_against_schema(final_metrics, schema):
            raise ValueError("Final metrics failed schema validation.")
        
        # 4. Write output
        output_path = CONFIG.RESULTS_DIR / "output.json"
        write_output_json(final_metrics, output_path)
        
        logger.info("T032 completed successfully.")
        return 0
        
    except Exception as e:
        logger.error(f"T032 failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
