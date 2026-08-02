import logging
from pathlib import Path
from typing import Dict, List, Optional

from src.utils.logging_config import create_logger

logger = create_logger(__name__)

def check_fr001_gate(source_counts: Dict[str, int]) -> bool:
    """
    Enforce Spec FR-001: At least 3 distinct sources must have data.
    This is a validation check that logs a warning if the condition is not met,
    but does NOT halt the pipeline (as per T028c logic).
    
    Args:
        source_counts: Dict mapping source_type to row count.
        
    Returns:
        True if the gate passes (>=3 sources) or if we proceed anyway (warning logged).
        Always returns True to allow pipeline continuation, but logs appropriately.
    """
    distinct_sources_with_data = [k for k, v in source_counts.items() if v > 0]
    count = len(distinct_sources_with_data)
    
    if count < 3:
        warning_msg = f"FR-001 Warning: Fewer than 3 distinct sources found ({count}: {distinct_sources_with_data}). Proceeding with available data."
        logger.warning(warning_msg)
        # Do not raise exception; pipeline continues
    else:
        logger.info(f"FR-001 Check passed: {count} distinct sources found.")
        
    return True

def main():
    """
    Standalone runner for FR-001 gate check.
    Expected to be called by the ingestion or preprocessing pipeline with source counts.
    """
    # Example usage if run directly
    sample_counts = {"NIST": 0, "Journal": 0, "Manual": 5}
    check_fr001_gate(sample_counts)

if __name__ == "__main__":
    main()
