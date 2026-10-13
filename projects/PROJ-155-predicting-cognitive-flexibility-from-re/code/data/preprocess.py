"""
Minimal placeholder for the preprocessing pipeline.

The real preprocessing (parcellation, time‑series extraction, etc.)
will be implemented in later tasks. Here we provide a stub that
creates the expected ``data/processed`` directory and returns a
dummy count of processed subjects so that downstream scripts can
continue.
"""
import logging

from llmxive_toolkit import paths

logger = logging.getLogger(__name__)

def run_preprocessing_pipeline() -> int:
    """
    Stub preprocessing routine.

    Returns:
        int: Number of subjects “processed”. For the skeleton we
        return ``0`` to indicate that no real preprocessing has
        occurred yet.
    """
    proc_dir = paths.data("processed")
    proc_dir.mkdir(parents=True, exist_ok=True)
    logger.info(
        f"Created placeholder processed data directory at {proc_dir}. "
        "Real preprocessing to be added later."
    )
    return 0
