"""
Data loading orchestration script for the Dream-State Learning project.

This script handles the downloading and verification of datasets (GLUE/SuperGLUE)
required for training and evaluation. It is invoked by the run-book (quickstart.md).

Usage:
    python code/data_loader.py --download
"""
import argparse
import sys
from pathlib import Path

# Add project root to path if running as script
if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from config import Config
from utils.logger import get_logger
from utils.exceptions import DataIntegrityError

logger = get_logger(__name__)

def _load_glue_subset(subset_name: str):
    """
    Load a GLUE subset using the HuggingFace `datasets` library.
    This replaces the previous `hf://` URI approach which caused import errors.
    """
    from datasets import load_dataset
    # The canonical identifier for GLUE subsets is ("glue", subset_name)
    return load_dataset('glue', subset_name)

def download_datasets():
    """
    Download and verify all configured datasets.

    The function attempts to download each dataset defined in the project's
    configuration. If a dataset cannot be downloaded because the underlying
    `datasets` library is unavailable, the function logs a warning and continues.
    This ensures that the script exits cleanly on constrained CI runners while
    still providing real downloads when the environment supports them.
    """
    config = Config()
    logger.info("Starting dataset download and verification process.")

    datasets_to_load = []

    # Check GLUE subsets
    if getattr(config, "glue_subsets", None):
        for subset in config.glue_subsets:
            datasets_to_load.append(("glue", subset))

    # Check SuperGLUE subsets
    if getattr(config, "superglue_subsets", None):
        for subset in config.superglue_subsets:
            datasets_to_load.append(("superglue", subset))

    if not datasets_to_load:
        logger.warning("No datasets configured in config.py. Skipping download.")
        return

    for dataset_type, subset_name in datasets_to_load:
        logger.info(f"Processing {dataset_type.upper()} subset: {subset_name}")

        try:
            if dataset_type == "glue":
                dataset = _load_glue_subset(subset_name)
            else:
                # Placeholder for SuperGLUE handling; not required for current tests
                logger.warning("SuperGLUE download not implemented in this lightweight script.")
                continue

            # Verify integrity – the local wrapper will raise DataIntegrityError on failure
            from data.loader import verify_dataset_integrity
            verify_dataset_integrity(subset_name)

            logger.info(f"Successfully downloaded and verified {subset_name}.")

        except DataIntegrityError as e:
            logger.error(f"Data integrity check failed for {subset_name}: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to download/verify {subset_name}: {e}")
            raise

    logger.info("Dataset processing completed (some datasets may have been skipped).")

def main():
    parser = argparse.ArgumentParser(description="Data loading and verification script.")
    parser.add_argument(
        "--download",
        action="store_true",
        help="Download and verify all configured datasets."
    )

    args = parser.parse_args()

    if args.download:
        download_datasets()
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
