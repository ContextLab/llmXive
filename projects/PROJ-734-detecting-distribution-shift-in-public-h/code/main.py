import os
import sys
import yaml
import logging
from pydantic import BaseModel, Field, ValidationError, validator
from typing import Optional, Dict, Any, List
from pathlib import Path

# Import local modules
from exceptions import E_NO_DATA
from logging_setup import setup_logging
from contracts import load_schema, validate_record

# Configuration Model Definition
class DataPathsConfig(BaseModel):
    raw_ili: str = Field(..., description="Path to raw ILI data CSV")
    raw_ground_truth: str = Field(..., description="Path to ground truth events CSV")
    processed: str = Field(..., description="Path to processed data directory")
    outputs: str = Field(..., description="Path to output directory")

class LoggingConfig(BaseModel):
    level: str = Field("INFO", description="Logging level")
    format: str = Field("%(asctime)s - %(name)s - %(levelname)s - %(message)s", description="Log format")

class Config(BaseModel):
    seed: int = Field(42, ge=0, description="Random seed for reproducibility")
    permutations: int = Field(1000, ge=1, description="Number of permutations for MMD")
    window_size: int = Field(12, ge=2, description="Sliding window size")
    stride: int = Field(1, ge=1, description="Sliding window stride")
    alpha: float = Field(0.01, gt=0, lt=1, description="Significance level")
    bandwidth: str = Field("median", description="Kernel bandwidth strategy")
    tolerance_weeks: int = Field(2, ge=0, description="Tolerance in weeks for evaluation")
    data_paths: DataPathsConfig
    logging: LoggingConfig

    class Config:
        extra = 'forbid'

def load_config(config_path: str = "code/config.yaml") -> Config:
    """Load and parse the configuration file."""
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(config_path, 'r') as f:
        raw_config = yaml.safe_load(f)
    
    # Validate against Pydantic model
    try:
        config = Config(**raw_config)
    except ValidationError as e:
        raise ValueError(f"Configuration validation failed: {e}")
    
    return config

def validate_config_schema(config_path: str = "code/config.yaml") -> bool:
    """
    Validate the config.yaml file against the JSON schema in contracts/config.schema.yaml.
    Returns True if valid, raises ValueError if invalid.
    """
    schema_path = "contracts/config.schema.yaml"
    if not os.path.exists(schema_path):
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    # Load schema
    schema = load_schema(schema_path)
    
    # Load config
    with open(config_path, 'r') as f:
        config_data = yaml.safe_load(f)
    
    # Validate using the schema validation logic
    # Note: pydantic already did structural validation, this is for strict schema adherence
    try:
        validate_record(config_data, schema)
    except Exception as e:
        raise ValueError(f"Schema validation failed: {e}")
    
    return True

def validate_data_availability(config: Config) -> None:
    """
    Check if required data files exist.
    Raises E_NO_DATA if files are missing.
    """
    required_files = [
        config.data_paths.raw_ili,
        config.data_paths.raw_ground_truth
    ]
    
    missing = []
    for f in required_files:
        if not os.path.exists(f):
            missing.append(f)
    
    if missing:
        msg = f"Pipeline halted: Real CDC data unavailable. Missing: {missing}"
        logging.error(msg)
        raise E_NO_DATA(msg)
    
    logging.info("Data availability check passed.")

def run_pipeline(config: Config) -> Dict[str, Any]:
    """Execute the main distribution shift detection pipeline."""
    logging.info("Starting pipeline execution...")
    
    # Preprocessing
    from preprocess import preprocess_pipeline
    processed_data = preprocess_pipeline(config)
    
    # MMD Detection
    from mmd_detector import detect_shifts
    flags = detect_shifts(processed_data, config)
    
    # Evaluation
    from evaluate import evaluate_pipeline
    metrics = evaluate_pipeline(flags, config)
    
    # Report Generation
    from report_generator import generate_report
    generate_report(metrics, flags, config)
    
    logging.info("Pipeline execution completed successfully.")
    return metrics

def run_sensitivity_analysis(config: Config) -> Dict[str, Any]:
    """Run sensitivity analysis over grid parameters."""
    logging.info("Starting sensitivity analysis...")
    from sensitivity import run_grid_search, run_tolerance_sweep
    
    grid_results = run_grid_search(config)
    tolerance_results = run_tolerance_sweep(config)
    
    from sensitivity_aggregator import save_aggregated_metrics
    aggregated = save_aggregated_metrics(grid_results, tolerance_results, config)
    
    logging.info("Sensitivity analysis completed.")
    return aggregated

def main():
    """Main entry point for the pipeline."""
    # Setup logging first
    setup_logging()
    
    try:
        # Load and validate config
        config = load_config()
        validate_config_schema()
        
        # Setup logging with config values
        # (Re-setup if logging config changed, though typically done once)
        
        # Validate data
        validate_data_availability(config)
        
        # Run main pipeline
        run_pipeline(config)
        
        # Run sensitivity analysis
        run_sensitivity_analysis(config)
        
    except E_NO_DATA as e:
        logging.error(str(e))
        sys.exit(1)
    except Exception as e:
        logging.error(f"Pipeline failed with error: {e}")
        raise

if __name__ == "__main__":
    main()