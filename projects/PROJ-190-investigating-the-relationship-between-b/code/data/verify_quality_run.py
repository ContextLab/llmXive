"""
Script to verify quality of the preprocessed dataset by calculating the
mean framewise displacement (FD) across all retained subjects, logging the
result, checking against the ≤0.2 mm threshold, and writing the value to a
results file.
"""

from pathlib import Path
import sys

# Project utilities
from llmxive_toolkit import paths, get_logger

# Functions from the existing verification module
from data.verify_quality import (
    load_preprocessing_metadata,
    calculate_mean_fd,
)

def main() -> int:
    """
    Execute the verification steps:
    1. Load preprocessing metadata JSON files from the processed data directory.
    2. Compute the mean FD across all subjects.
    3. Log the value and a warning if it exceeds the 0.2 mm threshold.
    4. Persist the numeric mean FD to a results file for downstream checks.
    """
    logger = get_logger(__name__)

    # Directory containing per‑subject metadata JSON files
    processed_dir: Path = paths.data("processed")
    logger.info(f"Loading preprocessing metadata from {processed_dir}")

    # Load metadata; this will raise if the directory or files are missing,
    # which is intentional – the pipeline must fail loudly on absent real data.
    metadata_list = load_preprocessing_metadata(processed_dir)

    # Compute the overall mean FD
    mean_fd: float = calculate_mean_fd(metadata_list)
    logger.info(f"Mean framewise displacement across retained subjects: {mean_fd:.4f} mm")

    # Quality threshold check
    threshold: float = 0.2
    if mean_fd > threshold:
        logger.warning(
            f"Mean FD {mean_fd:.4f} mm exceeds the quality threshold of {threshold:.3f} mm"
        )
    else:
        logger.info(
            f"Mean FD {mean_fd:.4f} mm is within the acceptable threshold of {threshold:.3f} mm"
        )

    # Persist the mean FD for downstream validation steps
    output_path: Path = paths.results("mean_fd.txt")
    output_path.write_text(f"{mean_fd:.6f}")
    logger.info(f"Wrote mean FD value to {output_path}")

    return 0

if __name__ == "__main__":
    sys.exit(main())
