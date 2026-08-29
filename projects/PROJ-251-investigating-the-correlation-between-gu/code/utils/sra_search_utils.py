import logging
from pathlib import Path
from typing import Dict, Any, Optional
from utils.logging_config import get_logger

logger = get_logger(__name__)

def log_search_progress(stage: str, details: str = "") -> None:
    """Log a search progress message."""
    msg = f"SRA Search: {stage}"
    if details:
        msg += f" - {details}"
    logger.info(msg)

def validate_accession_format(accession: str) -> bool:
    """Validate SRA accession format."""
    if not accession:
        return False
    prefixes = ('SRP', 'SRS', 'SRX', 'SRR')
    return any(accession.upper().startswith(p) for p in prefixes)

def format_search_query() -> str:
    """Return the standardized search query."""
    return (
        '"16S rRNA AND (influenza OR flu) AND (serology OR antibody OR titer) AND (human OR Homo sapiens)"'
    )

def create_error_report(error_type: str, message: str) -> Dict[str, Any]:
    """Create a standardized error report dictionary."""
    return {
        "error_type": error_type,
        "message": message,
        "status": "failed"
    }
