"""
Centralized error handling infrastructure for the molecular complexity pipeline.
Defines custom exceptions, error classification, and recovery utilities.
"""
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List, Callable
from datetime import datetime
import json
import traceback
from enum import Enum

from rdkit import Chem
from rdkit import RDLogger

# Suppress RDKit warnings to avoid cluttering logs with valence warnings we handle explicitly
RDLogger.DisableLog('rdApp.*')

class PipelineStage(Enum):
    """Enumeration of pipeline stages for structured error reporting."""
    SETUP = "setup"
    INGESTION = "ingestion"
    DESCRIPTOR_CALCULATION = "descriptor_calculation"
    DATA_STANDARDIZATION = "data_standardization"
    ANALYSIS = "analysis"
    VISUALIZATION = "visualization"
    REPORTING = "reporting"


class PipelineError(Exception):
    """Base exception for all pipeline-specific errors."""
    def __init__(self, message: str, stage: PipelineStage, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.stage = stage
        self.details = details or {}
        self.timestamp = datetime.utcnow().isoformat()

class DataIngestionError(PipelineError):
    """Raised when data fetching or validation fails."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, PipelineStage.INGESTION, details)

class DescriptorCalculationError(PipelineError):
    """Raised when molecular descriptor calculation fails."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, PipelineStage.DESCRIPTOR_CALCULATION, details)

class AnalysisError(PipelineError):
    """Raised when statistical analysis or modeling fails."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, PipelineStage.ANALYSIS, details)

class VisualizationError(PipelineError):
    """Raised when plot generation fails."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, PipelineStage.VISUALIZATION, details)

class ConfigurationError(PipelineError):
    """Raised when configuration or environment setup fails."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, PipelineStage.SETUP, details)


def validate_smiles(smiles: str) -> bool:
    """
    Validate a SMILES string using RDKit.
    Returns True if valid, False otherwise.
    """
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return False
        # Check for sanitization issues (valence, etc.)
        Chem.SanitizeMol(mol)
        return True
    except Exception:
        return False


def handle_molecule_error(smiles: str, error: Exception, error_log_path: Path) -> None:
    """
    Log a molecule processing error to the specified file.
    Format: timestamp | smiles | error_type | error_message
    """
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "smiles": smiles,
        "error_type": type(error).__name__,
        "error_message": str(error),
        "traceback": traceback.format_exc()
    }

    with open(error_log_path, 'a', encoding='utf-8') as f:
        f.write(json.dumps(log_entry) + '\n')


def retry_on_failure(func: Callable, max_retries: int = 3, backoff_factor: float = 2.0) -> Callable:
    """
    Decorator to retry a function on failure with exponential backoff.
    Only catches transient errors (e.g., network, timeouts).
    """
    import time

    def wrapper(*args, **kwargs):
        last_exception = None
        for attempt in range(1, max_retries + 1):
            try:
                return func(*args, **kwargs)
            except (ConnectionError, TimeoutError, OSError) as e:
                last_exception = e
                if attempt == max_retries:
                    raise
                wait_time = backoff_factor ** attempt
                logging.warning(f"Attempt {attempt} failed: {e}. Retrying in {wait_time}s...")
                time.sleep(wait_time)
        raise last_exception

    return wrapper


def create_error_report(errors: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Generate a JSON error report summarizing all captured errors.
    """
    report = {
        "generated_at": datetime.utcnow().isoformat(),
        "total_errors": len(errors),
        "errors_by_stage": {},
        "errors": errors
    }

    # Group by stage
    for error in errors:
        stage = error.get('stage', 'unknown')
        if stage not in report['errors_by_stage']:
            report['errors_by_stage'][stage] = 0
        report['errors_by_stage'][stage] += 1

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    
    logging.info(f"Error report generated: {output_path}")