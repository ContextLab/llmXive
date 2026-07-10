import logging
from pathlib import Path
from typing import Optional, Dict, Any, List, Callable
from datetime import datetime
import json
import traceback
from enum import Enum

from logging_config import get_logger

logger = get_logger(__name__)

class PipelineStage(Enum):
    INGESTION = "ingestion"
    DESCRIPTORS = "descriptors"
    STANDARDIZATION = "standardization"
    ANALYSIS = "analysis"
    VISUALIZATION = "visualization"

def validate_smiles(smiles: str) -> bool:
    """
    Basic validation of SMILES string format.
    Returns True if valid, False otherwise.
    """
    if not isinstance(smiles, str) or not smiles.strip():
        return False
    
    # Basic check: no whitespace inside (unless quoted, but simple check first)
    # RDKit will do the heavy lifting, but this catches obvious typos
    if any(c in smiles for c in ['\n', '\r', '\t']):
        return False
    return True

def handle_molecule_error(
    smiles: str, 
    error_type: str, 
    stage: PipelineStage, 
    details: Optional[str] = None
):
    """
    Centralized handler for molecule-level errors.
    Logs to data/errors.log and optional structured JSON log.
    """
    timestamp = datetime.now().isoformat()
    error_record = {
        "timestamp": timestamp,
        "stage": stage.value,
        "error_type": error_type,
        "smiles": smiles,
        "details": details or "No details provided"
    }

    # Log to standard error log
    log_path = Path("data/errors.log")
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    log_line = f"[{timestamp}] {stage.value.upper()} - {error_type}: {details or 'Unknown'} | SMILES: {smiles}\n"
    
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(log_line)
    
    logger.error(f"Molecule error logged: {error_type} for {smiles[:50]}...")

def retry_on_failure(
    func: Callable, 
    max_retries: int = 3, 
    stage: PipelineStage = PipelineStage.DESCRIPTORS
) -> Callable:
    """
    Decorator to retry a function on failure.
    Useful for flaky network calls or transient RDKit issues.
    """
    def wrapper(*args, **kwargs):
        last_exception = None
        for attempt in range(1, max_retries + 1):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                logger.warning(f"Attempt {attempt}/{max_retries} failed in {stage.value}: {str(e)}")
                if attempt == max_retries:
                    logger.error(f"Failed after {max_retries} attempts in {stage.value}")
                    # Log the final failure
                    handle_molecule_error(
                        smiles=str(args[0]) if args else "N/A",
                        error_type="RETRY_EXHAUSTED",
                        stage=stage,
                        details=str(e)
                    )
                    raise
        return None
    return wrapper

def create_error_report(errors: List[Dict[str, Any]], output_path: str = "data/error_report.json"):
    """
    Create a structured JSON report of errors.
    """
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    report = {
        "generated_at": datetime.now().isoformat(),
        "total_errors": len(errors),
        "errors": errors
    }
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Error report generated: {output_path}")
    return report