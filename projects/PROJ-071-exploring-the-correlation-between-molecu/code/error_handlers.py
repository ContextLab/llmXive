import logging
from pathlib import Path
from typing import Optional, Dict, Any, List, Callable
from datetime import datetime
import json
import traceback

from rdkit.Chem import rdchem

class PipelineError(Exception):
    """Base class for pipeline errors."""
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
    """Error during statistical analysis."""
    pass

class VisualizationError(PipelineError):
    """Error during visualization generation."""
    pass

class ConfigurationError(PipelineError):
    """Error in configuration."""
    pass

class StatisticalInsufficiencyError(PipelineError):
    """Error when statistical requirements are not met."""
    pass

class AtomValenceException(Exception):
    """
    Custom exception for non-standard valence in molecules.
    This is raised when RDKit's sanitization fails due to valence issues.
    """
    pass

def validate_smiles(smiles: str) -> bool:
    """Basic validation of SMILES string."""
    from rdkit import Chem
    try:
        mol = Chem.MolFromSmiles(smiles)
        return mol is not None
    except Exception:
        return False

def handle_molecule_error(smiles: str, error: Exception, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Handle a molecule processing error.
    Returns a structured error report.
    """
    error_report = {
        "smiles": smiles,
        "error_type": type(error).__name__,
        "error_message": str(error),
        "timestamp": datetime.utcnow().isoformat(),
        "context": context or {}
    }
    return error_report

def retry_on_failure(
    func: Callable,
    max_retries: int = 3,
    delay: float = 1.0,
    exceptions: Optional[List[type]] = None
) -> Callable:
    """
    Decorator to retry a function on failure.
    """
    import time
    if exceptions is None:
        exceptions = [Exception]

    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except tuple(exceptions) as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        time.sleep(delay)
                    else:
                        raise
            raise last_exception
        return wrapper
    return decorator

def create_error_report(
    operation: str,
    error: Exception,
    context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Create a comprehensive error report for logging.
    """
    return {
        "operation": operation,
        "error_type": type(error).__name__,
        "error_message": str(error),
        "traceback": traceback.format_exc(),
        "timestamp": datetime.utcnow().isoformat(),
        "context": context or {}
    }
