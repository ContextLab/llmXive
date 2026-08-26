"""
Save final evaluation metrics to data/results/output.json.

This task (T032) consolidates results from the modeling pipeline (T024-T031)
and writes them to the final output file conforming to contracts/output.schema.yaml.

Expected inputs:
- data/intermediate/merged.csv (from US1)
- data/results/cv_results.pkl (from US2 training)
- data/results/models.pkl (from US2 training)

Expected outputs:
- data/results/output.json (final metrics)
"""
import os
import sys
import json
import logging
import pickle
from pathlib import Path
from typing import Dict, Any, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import CONFIG
from utils.logging import get_logger, log_provenance_event
from modeling.evaluate import (
    load_models,
    load_cv_results,
    calculate_metrics,
    perform_paired_ttest,
    calculate_statistical_power,
    calculate_shear_yield_correlation,
    save_results as save_evaluation_results
)

logger = get_logger(__name__)

def load_schema_contracts() -> Dict[str, Any]:
    """
    Load the output schema to validate the structure of results.
    Returns the schema definition.
    """
    schema_path = Path(CONFIG.PROJECT_ROOT) / "contracts" / "output.schema.yaml"
    try:
        import yaml
        with open(schema_path, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.warning(f"Could not load schema from {schema_path}: {e}")
        # Return a minimal expected structure if schema is missing
        return {
            "required_fields": [
                "r2_baseline", "mae_baseline", "r2_dft", "mae_dft",
                "p_value_ttest", "statistical_power", "pearson_correlation",
                "timestamp", "dataset_rows"
            ]
        }

def validate_output_against_schema(output_data: Dict[str, Any], schema: Dict[str, Any]) -> bool:
    """
    Validate that output_data contains all required fields from the schema.
    Returns True if valid, False otherwise.
    """
    required_fields = schema.get("required_fields", [])
    missing_fields = [field for field in required_fields if field not in output_data]
    
    if missing_fields:
        logger.error(f"Output missing required fields: {missing_fields}")
        return False
    
    # Check for non-null values in critical fields
    critical_fields = ["r2_baseline", "mae_baseline", "r2_dft", "mae_dft", "p_value_ttest"]
    for field in critical_fields:
        if field in output_data and output_data[field] is None:
            logger.error(f"Critical field '{field}' is None")
            return False
    
    return True

def assemble_final_metrics() -> Dict[str, Any]:
    """
    Load all intermediate results and assemble the final metrics dictionary.
    """
    results_dir = Path(CONFIG.PROJECT_ROOT) / "data" / "results"
    intermediate_dir = Path(CONFIG.PROJECT_ROOT) / "data" / "intermediate"
    
    # Load CV results (contains fold-wise metrics for both models)
    cv_results_path = results_dir / "cv_results.pkl"
    if not cv_results_path.exists():
        raise FileNotFoundError(f"CV results not found at {cv_results_path}. Run modeling pipeline first.")
    
    cv_results = load_cv_results(cv_results_path)
    
    # Load models (for reference, though metrics come from CV results)
    models_path = results_dir / "models.pkl"
    models = load_models(models_path) if models_path.exists() else None
    
    # Calculate aggregate metrics from CV results
    metrics = calculate_metrics(cv_results)
    
    # Perform paired t-test on fold-wise errors
    ttest_result = perform_paired_ttest(cv_results)
    p_value = ttest_result.get('p_value')
    
    # Calculate statistical power
    power = calculate_statistical_power(cv_results, alpha=0.05)
    
    # Calculate Pearson correlation between Shear Modulus and Yield Strength
    merged_path = intermediate_dir / "merged.csv"
    if not merged_path.exists():
        raise FileNotFoundError(f"Merged dataset not found at {merged_path}. Run ingestion pipeline first.")
    
    correlation_result = calculate_shear_yield_correlation(merged_path)
    pearson_corr = correlation_result.get('pearson_r')
    
    # Get dataset row count
    import pandas as pd
    df = pd.read_csv(merged_path)
    dataset_rows = len(df)
    
    # Assemble final output dictionary
    final_metrics = {
        "r2_baseline": metrics.get('r2_baseline'),
        "mae_baseline": metrics.get('mae_baseline'),
        "r2_dft": metrics.get('r2_dft'),
        "mae_dft": metrics.get('mae_dft'),
        "p_value_ttest": p_value,
        "statistical_power": power,
        "pearson_correlation": pearson_corr,
        "dataset_rows": dataset_rows,
        "timestamp": cv_results.get('timestamp', None),
        "model_config": {
            "n_estimators": cv_results.get('model_config', {}).get('n_estimators', 100),
            "max_depth": cv_results.get('model_config', {}).get('max_depth', None),
            "random_state": cv_results.get('model_config', {}).get('random_state', 42)
        }
    }
    
    return final_metrics

def write_output_json(output_data: Dict[str, Any], output_path: Path) -> None:
    """
    Write the final metrics to JSON file.
    """
    # Ensure parent directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    logger.info(f"Final metrics written to {output_path}")
    log_provenance_event(
        event_type="artifact_saved",
        artifact_path=str(output_path),
        artifact_type="json",
        details={"rows": output_data.get('dataset_rows')}
    )

def main():
    """
    Main entry point for T032: Write final metrics to data/results/output.json.
    """
    logger.info("Starting T032: Writing final metrics to output.json")
    
    try:
        # Load schema for validation
        schema = load_schema_contracts()
        
        # Assemble final metrics
        final_metrics = assemble_final_metrics()
        
        # Validate against schema
        if not validate_output_against_schema(final_metrics, schema):
            raise ValueError("Final metrics do not conform to output schema")
        
        # Write to file
        output_path = Path(CONFIG.PROJECT_ROOT) / "data" / "results" / "output.json"
        write_output_json(final_metrics, output_path)
        
        logger.info("T032 completed successfully")
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"Required data file not found: {e}")
        logger.error("Ensure US1 (ingestion) and US2 (modeling) have been completed successfully.")
        return 1
    except Exception as e:
        logger.error(f"Error in T032: {e}")
        raise

if __name__ == "__main__":
    sys.exit(main())
