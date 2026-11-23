import logging
from pathlib import Path
from typing import Dict, Any, Optional
from utils.logging_config import get_logger

def log_search_progress(current: int, total: int) -> None:
    """Logs progress of SRA search."""
    logger = get_logger(__name__)
    logger.info(f"Search progress: {current}/{total}")

def validate_accession_format(accession: str) -> bool:
    """Validates SRA accession format."""
    if not accession:
        return False
    return accession.startswith(("SRP", "SRR", "SRX"))

def format_search_query(query: str) -> str:
    """Formats a search query."""
    return query.strip()

def create_error_report(error: Exception, context: str) -> Dict[str, Any]:
    """Creates an error report dictionary."""
    return {
        "error": str(error),
        "context": context
    }