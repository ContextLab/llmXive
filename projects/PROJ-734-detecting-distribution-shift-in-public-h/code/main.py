import os
import sys
import yaml
import logging
from pydantic import BaseModel, Field, ValidationError
from typing import Optional
from exceptions import E_NO_DATA

# Import validation functions from contracts module
from contracts import load_schema, validate_record

# Import preprocessing pipeline
from preprocess import preprocess_pipeline

# Import baseline detectors
from pettitt import run_pettitt_rolling_window
from bocpd import run_bocpd_rolling_window

# Import evaluation and reporting
from evaluate import load_ground_truth, calculate_detection_delay, compute_metrics, evaluate_pipeline
from report_generator import generate_report

class Config(BaseModel):
    seed: int = Field(default=42, ge=0)
    permutations: int = Field(default=1000, ge=1)
    window_size: int = Field(default=12, ge=1)
    stride: int = Field(default=1, ge=1)
    alpha: float = Field(default=0.01, gt=0, lt=1)

    class Config:
        extra = "forbid"

def load_config(config_path: str = "code/config.yaml") -> Config:
    """Load and validate configuration from YAML file using Pydantic and Schema."""
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path, 'r') as f:
        config_data = yaml.safe_load(f)

    # Validate against schema file if available
    schema_path = "contracts/config.schema.yaml"
    if os.path.exists(schema_path):
        schema = load_schema(schema_path)
        errors = validate_record(config_data, schema)
        if errors:
            raise ValueError(f"Configuration validation errors: {errors}")

    try:
        config = Config(**config_data)
    except ValidationError as e:
        raise ValueError(f"Invalid configuration: {e}")

    return config

def validate_data_availability():
    """Check for existence of required raw data files."""
    required_files = [
        "data/raw/fluview_ili.csv",
        "data/raw/ground_truth_events.csv"
    ]

    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)

    if missing_files:
        raise E_NO_DATA(f"Pipeline halted: Real CDC data unavailable. Missing: {missing_files}")

def main():
    """Main entry point for the pipeline."""
    # Setup logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)

    # Load configuration
    try:
        config = load_config()
        logger.info(f"Loaded config: {config}")
    except (FileNotFoundError, ValueError) as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)

    # Validate data availability
    try:
        validate_data_availability()
        logger.info("Data availability check passed.")
    except E_NO_DATA as e:
        logger.error(f"Error: {e}")
        sys.exit(1)

    # Step 1: Preprocess data
    logger.info("Starting preprocessing pipeline...")
    try:
        processed_df = preprocess_pipeline(config)
        logger.info(f"Preprocessing complete. Processed {len(processed_df)} rows.")
    except Exception as e:
        logger.error(f"Preprocessing failed: {e}")
        sys.exit(1)

    # Step 2: Run Baseline Detectors (US2 Integration)
    logger.info("Running baseline change-point detection methods...")
    
    # Extract ILI series and weeks
    weeks = processed_df['week'].values
    ili_values = processed_df['ili'].values

    # Run Pettitt Rolling Window
    logger.info("Executing Pettitt Rolling Window test...")
    try:
        pettitt_results = run_pettitt_rolling_window(
            weeks=weeks, 
            values=ili_values, 
            window_size=config.window_size, 
            stride=config.stride,
            alpha=config.alpha
        )
        logger.info(f"Pettitt detected {len(pettitt_results)} change points.")
    except Exception as e:
        logger.error(f"Pettitt execution failed: {e}")
        pettitt_results = []

    # Run BOCPD
    logger.info("Executing BOCPD test...")
    try:
        bocpd_results = run_bocpd_rolling_window(
            weeks=weeks, 
            values=ili_values, 
            window_size=config.window_size, 
            stride=config.stride,
            alpha=config.alpha
        )
        logger.info(f"BOCPD detected {len(bocpd_results)} change points.")
    except Exception as e:
        logger.error(f"BOCPD execution failed: {e}")
        bocpd_results = []

    # Combine baseline results
    all_baseline_results = pettitt_results + bocpd_results

    # Step 3: Evaluate Baselines
    if all_baseline_results:
        logger.info("Evaluating baseline detection performance...")
        try:
            # Load ground truth
            ground_truth = load_ground_truth()
            
            # Calculate delays for baselines
            baseline_delays = []
            for result in all_baseline_results:
                delay = calculate_detection_delay(
                    detected_week=result['week'], 
                    ground_truth=ground_truth, 
                    tolerance_weeks=2
                )
                if delay is not None:
                    baseline_delays.append(delay)
            
            # Compute metrics
            if baseline_delays:
                metrics = compute_metrics(
                    detected_weeks=[r['week'] for r in all_baseline_results],
                    ground_truth=ground_truth,
                    tolerance_weeks=2
                )
                logger.info(f"Baseline Metrics: {metrics}")
            else:
                logger.warning("No valid detection delays calculated for baselines.")
                metrics = {}
        except Exception as e:
            logger.error(f"Baseline evaluation failed: {e}")
            metrics = {}
    else:
        logger.warning("No baseline results to evaluate.")
        metrics = {}

    # Step 4: Generate Report (includes baseline comparison if data exists)
    logger.info("Generating final report...")
    try:
        # We need to generate the report. 
        # Note: This assumes MMD flags are already generated or generated here if needed.
        # For US2 integration, we primarily ensure baselines run and are reported.
        # The report_generator expects metrics and flags. 
        # If MMD hasn't run yet in this flow, we might just report baseline stats.
        # However, tasks.md implies MMD (US1) is already done or parallel.
        # We will attempt to call generate_report which handles loading existing artifacts.
        
        generate_report(
            metrics=metrics,
            baseline_results=all_baseline_results,
            output_path="data/processed/report.pdf"
        )
        logger.info("Report generation complete.")
    except Exception as e:
        logger.error(f"Report generation failed: {e}")
        # Do not exit, as baselines ran successfully

    logger.info("Pipeline execution complete.")

if __name__ == "__main__":
    main()