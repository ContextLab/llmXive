"""
Main entry point for the distribution shift detection pipeline.
Handles configuration loading, validation, and orchestration of the pipeline steps.
"""
import os
import sys
import yaml
import logging
from pydantic import BaseModel, Field, ValidationError
from typing import Optional, Dict, Any
import json

# Import local modules
from exceptions import E_NO_DATA
from logging_setup import setup_logging
from download_data import fetch_cdc_data, parse_virological_to_events, validate_downloaded_data
from preprocess import preprocess_pipeline
from mmd_detector import detect_shifts, main as run_mmd
from evaluate import evaluate_pipeline, main as run_evaluate
from report_generator import generate_report, main as run_report
from bocpd import run_bocpd_rolling_window
from pettitt import run_pettitt_rolling_window
from sensitivity import run_tolerance_sweep

# Configure logging
logger = logging.getLogger(__name__)

class Config(BaseModel):
    """
    Configuration model for the distribution shift detection pipeline.
    Validates against the schema defined in contracts/config.schema.yaml.
    """
    seed: int = Field(42, ge=0, description="Random seed for reproducibility")
    permutations: int = Field(1000, ge=1, description="Number of permutations for MMD")
    window_size: int = Field(12, ge=1, description="Sliding window size")
    stride: int = Field(1, ge=1, description="Stride for sliding window")
    alpha: float = Field(0.01, ge=0.0, le=1.0, description="Significance level")
    bandwidth_method: str = Field("median", description="Bandwidth estimation method")
    min_samples: int = Field(5, ge=1, description="Minimum samples per window")
    tolerance_weeks: int = Field(2, ge=0, description="Tolerance for detection delay")

    class Config:
        extra = "forbid"

def load_config(config_path: str = "code/config.yaml") -> Config:
    """
    Load configuration from YAML file and validate against Pydantic model.
    """
    if not os.path.exists(config_path):
        logger.error(f"Configuration file not found: {config_path}")
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    try:
        with open(config_path, 'r') as f:
            config_data = yaml.safe_load(f)
        
        # Validate against Pydantic model
        config = Config(**config_data)
        logger.info(f"Configuration loaded and validated successfully from {config_path}")
        return config
    
    except ValidationError as e:
        logger.error(f"Configuration validation failed: {e}")
        raise
    except yaml.YAMLError as e:
        logger.error(f"YAML parsing error: {e}")
        raise

def validate_config_schema(config_data: Dict[str, Any], schema_path: str = "contracts/config.schema.yaml") -> bool:
    """
    Validate configuration data against the JSON schema.
    This provides an additional layer of validation beyond Pydantic.
    """
    try:
        import jsonschema
        with open(schema_path, 'r') as f:
            schema = yaml.safe_load(f)
        
        jsonschema.validate(instance=config_data, schema=schema)
        logger.info("Configuration validated against JSON schema")
        return True
    except ImportError:
        logger.warning("jsonschema not installed, skipping schema validation")
        return True
    except FileNotFoundError:
        logger.error(f"Schema file not found: {schema_path}")
        return False
    except jsonschema.ValidationError as e:
        logger.error(f"Schema validation error: {e}")
        return False

def validate_data_availability() -> None:
    """
    Validate that required real data files exist before proceeding.
    Raises E_NO_DATA if files are missing.
    """
    required_files = [
        "data/raw/fluview_ili.csv",
        "data/raw/ground_truth_events.csv"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        error_msg = f"Pipeline halted: Real CDC data unavailable. Missing: {', '.join(missing_files)}"
        logger.error(error_msg)
        raise E_NO_DATA(error_msg)
    
    logger.info("All required data files found")

def run_pipeline(config: Config) -> None:
    """
    Execute the full distribution shift detection pipeline.
    """
    logger.info("Starting distribution shift detection pipeline")
    
    # Step 1: Validate data availability
    validate_data_availability()
    
    # Step 2: Preprocess data
    logger.info("Preprocessing data...")
    processed_data = preprocess_pipeline(config)
    
    # Step 3: Run MMD detection
    logger.info("Running MMD shift detection...")
    mmd_results = run_mmd(processed_data, config)
    
    # Step 4: Run baseline methods (Pettitt and BOCPD)
    logger.info("Running baseline change-point detection...")
    pettitt_results = run_pettitt_rolling_window(processed_data, config)
    bocpd_results = run_bocpd_rolling_window(processed_data, config)
    
    # Step 5: Evaluate results
    logger.info("Evaluating pipeline results...")
    evaluation_results = run_evaluate(mmd_results, pettitt_results, bocpd_results, config)
    
    # Step 6: Generate report
    logger.info("Generating final report...")
    report_path = run_report(evaluation_results, config)
    
    logger.info(f"Pipeline completed successfully. Report saved to: {report_path}")

def run_sensitivity_analysis(config: Config) -> None:
    """
    Run sensitivity analysis on key parameters.
    """
    logger.info("Starting sensitivity analysis...")
    run_tolerance_sweep(config)
    logger.info("Sensitivity analysis completed")

def main():
    """
    Main entry point for the pipeline.
    """
    # Setup logging
    setup_logging()
    
    try:
        # Load and validate configuration
        config = load_config()
        
        # Additional schema validation if jsonschema is available
        with open("code/config.yaml", 'r') as f:
            config_data = yaml.safe_load(f)
        validate_config_schema(config_data)
        
        # Parse command line arguments for mode selection
        if len(sys.argv) > 1:
            mode = sys.argv[1]
            if mode == "sensitivity":
                run_sensitivity_analysis(config)
            else:
                run_pipeline(config)
        else:
            run_pipeline(config)
            
    except E_NO_DATA as e:
        logger.critical(str(e))
        sys.exit(1)
    except FileNotFoundError as e:
        logger.critical(str(e))
        sys.exit(1)
    except ValidationError as e:
        logger.critical(f"Configuration error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.critical(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()