import logging
from pathlib import Path
from typing import Optional, Dict, Any, List, Callable
from datetime import datetime
import json
import traceback

class PipelineError(Exception):
    """Base exception for pipeline errors."""
    pass

class DataIngestionError(PipelineError):
    """Error during data ingestion."""
    pass

class DataFetchError(PipelineError):
    """Error fetching data from external sources."""
    pass

class DataInefficiencyError(PipelineError):
    """Error due to insufficient data."""
    pass

class DescriptorCalculationError(PipelineError):
    """Error during descriptor calculation."""
    pass

class AnalysisError(PipelineError):
    """Error during analysis."""
    pass

class VisualizationError(PipelineError):
    """Error during visualization."""
    pass

class ConfigurationError(PipelineError):
    """Error in configuration."""
    pass

class StatisticalInsufficiencyError(PipelineError):
    """Error when statistical requirements are not met."""
    pass

class AtomValenceException(PipelineError):
    """Exception for valence errors in molecules."""
    def __init__(self, smiles: str, message: str):
        self.smiles = smiles
        self.message = message
        super().__init__(f"Valence error for {smiles}: {message}")


def validate_smiles(smiles: str) -> bool:
    """Basic validation for SMILES string."""
    if not smiles or not isinstance(smiles, str):
        return False
    return len(smiles.strip()) > 0


def handle_molecule_error(smiles: str, error: Exception) -> Dict[str, Any]:
    """Handle a molecule processing error and return context."""
    return {
        "smiles": smiles,
        "error_type": type(error).__name__,
        "error_message": str(error),
        "timestamp": datetime.utcnow().isoformat()
    }


def retry_on_failure(func: Callable, max_retries: int = 3, delay: float = 1.0) -> Callable:
    """Decorator to retry a function on failure."""
    def wrapper(*args, **kwargs):
        for attempt in range(max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                logging.warning(f"Attempt {attempt+1} failed: {e}. Retrying...")
                import time
                time.sleep(delay)
    return wrapper


def create_error_report(error_type: str, message: str, details: Optional[Dict] = None) -> str:
    """Create a JSON-formatted error report string."""
    report = {
        "error_type": error_type,
        "message": message,
        "timestamp": datetime.utcnow().isoformat(),
        "details": details or {}
    }
    return json.dumps(report, indent=2)
