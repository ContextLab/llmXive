"""
Main CLI entry point for the Plant Disease Resistance Prediction Pipeline.

Orchestrates the full pipeline: Fetch -> Preprocess -> Split -> Select -> Train -> Validate.
Includes data integrity checks and handles Simulation Mode exceptions.
"""
import os
import sys
import logging
import argparse
from pathlib import Path
from typing import Dict, Any, Optional

# Project imports matching the API surface
from config import load_config, get_path
from utils.logging import setup_logger, log_pipeline_step, log_config_summary
from utils.exceptions import PipelineException, EX_DATA_INTEGRITY, EX_POWER_INSUFFICIENT
from data.manifest import ManifestLoader, get_manifest_source_type
from data.download import download_or_generate
from data.preprocess import preprocess_pipeline
from data.split import split_pipeline
from analysis.feature_selection import feature_selection_pipeline
from analysis.modeling import modeling_pipeline
from analysis.validation import run_validation_pipeline

def check_data_integrity(manifest_data: Dict[str, Any], source_type: str, logger: logging.Logger) -> None:
    """
    Check data integrity and power constraints.
    
    Rules:
    1. If source_type != SIMULATED:
       - If aligned samples < 100 OR missing modalities -> EX_DATA_INTEGRITY (02)
       - If samples < 100 -> EX_POWER_INSUFFICIENT (03)
    2. If source_type == SIMULATED:
       - Bypass all halts (Simulation Mode exception)
    
    Priority: FR-008 (Power) then FR-007 (Integrity) with unified message.
    """
    if source_type == "SIMULATED":
        logger.info("Simulation Mode detected. Bypassing data integrity and power checks.")
        return

    # Extract sample counts from manifest if available, otherwise default to 0
    # The manifest structure is assumed to have 'statistics' or 'samples' count
    total_samples = manifest_data.get('statistics', {}).get('total_samples', 0)
    aligned_samples = manifest_data.get('statistics', {}).get('aligned_samples', total_samples)
    has_missing_modalities = manifest_data.get('statistics', {}).get('missing_modalities', 0) > 0

    error_messages = []

    # Check Power (FR-008) first - requires at least 100 samples
    if total_samples < 100:
        error_messages.append(f"Insufficient power: {total_samples} samples found (requirement: >= 100).")

    # Check Integrity (FR-007) - requires >= 100 aligned samples and no missing modalities
    if aligned_samples < 100 or has_missing_modalities:
        reasons = []
        if aligned_samples < 100:
            reasons.append(f"only {aligned_samples} aligned samples")
        if has_missing_modalities:
            reasons.append("missing modalities detected")
        error_messages.append(f"Data integrity compromised: {', '.join(reasons)}.")

    if error_messages:
        # Prioritize Power error if both exist, otherwise Integrity
        if total_samples < 100 and (aligned_samples < 100 or has_missing_modalities):
            # Both conditions met, prioritize Power per spec
            raise PipelineException(
                code=EX_POWER_INSUFFICIENT,
                message=f"Power check failed: {total_samples} total samples. "
                        f"Also failed integrity check: {aligned_samples} aligned samples, missing modalities: {has_missing_modalities}."
            )
        elif total_samples < 100:
            raise PipelineException(
                code=EX_POWER_INSUFFICIENT,
                message=error_messages[0]
            )
        else:
            raise PipelineException(
                code=EX_DATA_INTEGRITY,
                message=error_messages[0]
            )

def run_pipeline(config: Dict[str, Any], logger: logging.Logger) -> None:
    """
    Execute the full pipeline steps in order.
    """
    logger.info("Starting Pipeline Execution")
    
    # 1. Fetch / Generate Data
    log_pipeline_step(logger, "Step 1: Fetching/Generating Data")
    download_or_generate(config, logger)
    
    # 2. Preprocess
    log_pipeline_step(logger, "Step 2: Preprocessing Data")
    preprocess_pipeline(config, logger)
    
    # 3. Split
    log_pipeline_step(logger, "Step 3: Splitting Data")
    split_pipeline(config, logger)
    
    # 4. Feature Selection
    log_pipeline_step(logger, "Step 4: Feature Selection")
    feature_selection_pipeline(config, logger)
    
    # 5. Modeling
    log_pipeline_step(logger, "Step 5: Training Models")
    modeling_pipeline(config, logger)
    
    # 6. Validation
    log_pipeline_step(logger, "Step 6: Validation")
    run_validation_pipeline(config, logger)
    
    logger.info("Pipeline completed successfully.")

def main():
    parser = argparse.ArgumentParser(description="Plant Disease Resistance Prediction Pipeline")
    parser.add_argument('--config', type=str, default='data/data_manifest.yaml',
                        help='Path to the data manifest/config file')
    parser.add_argument('--log-level', type=str, default='INFO',
                        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                        help='Logging level')
    args = parser.parse_args()

    # Setup Logger
    logger = setup_logger(level=args.log_level)
    
    try:
        # Load Config/Manifest
        config = load_config(args.config)
        log_config_summary(logger, config)
        
        # Determine Source Type
        source_type = get_manifest_source_type(args.config)
        logger.info(f"Data Source Type: {source_type}")
        
        # Load full manifest for integrity checks
        manifest_loader = ManifestLoader(args.config)
        manifest_data = manifest_loader.load()
        
        # Check Integrity/Power BEFORE running pipeline
        check_data_integrity(manifest_data, source_type, logger)
        
        # Run Pipeline
        run_pipeline(config, logger)
        
    except PipelineException as e:
        logger.error(f"Pipeline halted: {e}")
        sys.exit(e.code)
    except Exception as e:
        logger.exception(f"Unexpected error during pipeline execution: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
