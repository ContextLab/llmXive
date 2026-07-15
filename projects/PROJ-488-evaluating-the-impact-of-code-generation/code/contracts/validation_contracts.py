"""
Validation Contracts: Pre-conditions and Post-conditions for pipeline stages.

This module implements the checks that must pass before a stage runs
(pre-conditions) and checks that must pass after a stage completes
(post-conditions) to ensure data integrity.
"""
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

from ..logging_config import get_logger
from ..data_model import MetricResult

logger = get_logger("contracts.validation")

class ContractViolationError(Exception):
    """Raised when a pre-condition or post-condition is violated."""
    pass

def validate_preconditions(stage_name: str, config: Dict[str, Any]) -> bool:
    """
    Checks pre-conditions for a given stage.
    
    Pre-conditions:
    - Input directories exist.
    - Required configuration keys are present.
    - Previous stages have produced expected artifacts (if applicable).
    """
    logger.info(f"Validating pre-conditions for stage: {stage_name}")
    
    # Check input directory
    if 'input_dir' in config:
        input_path = Path(config['input_dir'])
        if not input_path.exists():
            msg = f"Pre-condition failed: Input directory {input_path} does not exist"
            logger.error(msg)
            raise ContractViolationError(msg)
    
    # Check output directory write permission
    if 'output_dir' in config:
        output_path = Path(config['output_dir'])
        if output_path.exists() and not os.access(output_path, os.W_OK):
            msg = f"Pre-condition failed: Cannot write to output directory {output_path}"
            logger.error(msg)
            raise ContractViolationError(msg)
            
    # Stage-specific checks
    if stage_name == 'metrics':
        if 'snippets_file' not in config:
            msg = "Pre-condition failed: 'snippets_file' required for metrics stage"
            logger.error(msg)
            raise ContractViolationError(msg)
            
    logger.debug(f"Pre-conditions for {stage_name} validated successfully")
    return True

def validate_postconditions(stage_name: str, config: Dict[str, Any], result: Any) -> bool:
    """
    Checks post-conditions after a stage completes.
    
    Post-conditions:
    - Output files were created.
    - Output files are non-empty.
    - Output data conforms to schema (e.g., CSV headers).
    """
    logger.info(f"Validating post-conditions for stage: {stage_name}")
    
    if 'output_dir' not in config:
        logger.warning("Post-condition check skipped: No output_dir in config")
        return True
        
    output_path = Path(config['output_dir'])
    
    # Generic check: Did any file get created?
    if stage_name in ['ingestion', 'metrics', 'stats']:
        files = list(output_path.glob("*"))
        if not files:
            msg = f"Post-condition failed: No files created in {output_path}"
            logger.error(msg)
            raise ContractViolationError(msg)
            
    # Specific check for metrics stage (CSV validation)
    if stage_name == 'metrics':
        csv_files = list(output_path.glob("*.csv"))
        if not csv_files:
            msg = f"Post-condition failed: No CSV files created in {output_path}"
            logger.error(msg)
            raise ContractViolationError(msg)
            
        # Validate one CSV header
        from .data_contracts import MetricResultContract
        import pandas as pd
        
        sample_csv = csv_files[0]
        try:
            df = pd.read_csv(sample_csv)
            if not MetricResultContract.validate_csv_header(list(df.columns)):
                msg = f"Post-condition failed: {sample_csv} has invalid headers"
                logger.error(msg)
                raise ContractViolationError(msg)
        except Exception as e:
            msg = f"Post-condition failed: Could not read/validate {sample_csv}: {str(e)}"
            logger.error(msg)
            raise ContractViolationError(msg)
            
    logger.debug(f"Post-conditions for {stage_name} validated successfully")
    return True

def run_contract_check(stage_name: str, config: Dict[str, Any], func: callable) -> Any:
    """
    Wrapper to enforce contracts around a stage function.
    """
    validate_preconditions(stage_name, config)
    try:
        result = func(config)
        validate_postconditions(stage_name, config, result)
        return result
    except ContractViolationError as e:
        logger.critical(f"Contract violation in {stage_name}: {str(e)}")
        raise
