"""Custom exception classes for the llmXive science pipeline."""
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

class DataFetchError(DataIngestionError):
    """Error fetching data from external sources."""
    pass

class DataInefficiencyError(DataIngestionError):
    """Data is insufficient for analysis."""
    pass

class DescriptorCalculationError(PipelineError):
    """Error calculating molecular descriptors."""
    pass

class AnalysisError(PipelineError):
    """Error during statistical analysis."""
    pass

class VisualizationError(PipelineError):
    """Error during visualization generation."""
    pass

class ConfigurationError(PipelineError):
    """Error in configuration."""
    pass

class StatisticalInsufficiencyError(AnalysisError):
    """Raised when the dataset is statistically insufficient (e.g., N < 30)."""
    def __init__(self, message: str, n_count: int = 0, reason: str = ""):
        super().__init__(message)
        self.n_count = n_count
        self.reason = reason

class AtomValenceException(Exception):
    """Exception for invalid atom valence in molecules."""
    def __init__(self, smiles: str, error_type: str):
        super().__init__(f"Invalid valence for SMILES {smiles}: {error_type}")
        self.smiles = smiles
        self.error_type = error_type

def validate_smiles(smiles: str) -> bool:
    """Basic SMILES validation."""
    if not smiles or not isinstance(smiles, str):
        return False
    return True

def handle_molecule_error(error: Exception, smiles: str, context: str) -> Dict[str, Any]:
    """Handle errors during molecule processing."""
    return {
        "smiles": smiles,
        "error_type": type(error).__name__,
        "message": str(error),
        "context": context,
        "timestamp": datetime.utcnow().isoformat()
    }

def retry_on_failure(func: Callable, max_retries: int = 3, delay: float = 1.0) -> Callable:
    """Decorator to retry a function on failure."""
    import time
    def wrapper(*args, **kwargs):
        last_exception = None
        for attempt in range(max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                logging.warning(f"Attempt {attempt + 1} failed: {e}")
                time.sleep(delay)
        raise last_exception
    return wrapper

def create_error_report(errors: List[Dict[str, Any]], output_path: str) -> None:
    """Create a JSON error report."""
    with open(output_path, 'w') as f:
        json.dump(errors, f, indent=2)