"""
Minimal placeholder for the HCP data download module.
This implementation provides a stub `download_hcp_subset` function that
satisfies imports used by the main orchestration script. Real data
acquisition is handled in later tasks.
"""
import logging

from llmxive_toolkit import paths

logger = logging.getLogger(__name__)

def download_hcp_subset(subset: int | None = None) -> None:
    """
    Stub function for downloading a subset of HCP data.

    Args:
        subset: Optional integer specifying how many subjects to download.
                If None, the full dataset would be requested in a
                production implementation.

    The real implementation will stream data from the verified HCP
    source, verify checksums, and store files under ``data/raw``.
    For the skeleton stage we simply ensure that the expected raw
    directory exists so that downstream code can operate without
    raising ``FileNotFoundError``.
    """
    raw_dir = paths.data("raw", "HCP_1200")
    raw_dir.mkdir(parents=True, exist_ok=True)
    logger.info(
        f"Created placeholder raw data directory at {raw_dir}. "
        "Actual download to be performed in a later task."
    )
    # No actual download performed at this stage.
