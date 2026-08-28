"""
Checksum verification and state management for downloaded data.
Implements T018: Add checksum verification for downloaded raw data to state.yaml
and calculate/report final 'linked metadata percentage'.
"""
import os
import hashlib
import logging
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
import pandas as pd

from config import get_path

logger = logging.getLogger(__name__)


def calculate_file_checksum(file_path: Path, algorithm: str = "sha256") -> str:
    """
    Calculate the checksum of a file.

    Args:
        file_path: Path to the file to checksum
        algorithm: Hash algorithm to use (default: sha256)

    Returns:
        Hexadecimal checksum string
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    hash_func = hashlib.new(algorithm)
    with open(file_path, "rb") as f:
        # Read in chunks to handle large files
        for chunk in iter(lambda: f.read(8192), b""):
            hash_func.update(chunk)

    return hash_func.hexdigest()


def load_state_yaml(state_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load the state.yaml file.

    Args:
        state_path: Optional path to state.yaml. If None, uses default project state path.

    Returns:
        Dictionary containing state data
    """
    if state_path is None:
        state_path = get_path("state", "projects", "PROJ-345", "state.yaml")

    if not state_path.exists():
        logger.warning(f"State file not found at {state_path}, initializing empty state")
        return {"artifacts": {}, "checksums": {}, "metadata": {}}

    with open(state_path, "r") as f:
        return yaml.safe_load(f)


def save_state_yaml(state_data: Dict[str, Any], state_path: Optional[Path] = None) -> Path:
    """
    Save the state.yaml file.

    Args:
        state_data: Dictionary containing state data
        state_path: Optional path to state.yaml. If None, uses default project state path.

    Returns:
        Path to the saved file
    """
    if state_path is None:
        state_path = get_path("state", "projects", "PROJ-345", "state.yaml")

    state_path.parent.mkdir(parents=True, exist_ok=True)

    with open(state_path, "w") as f:
        yaml.safe_dump(state_data, f, default_flow_style=False, sort_keys=False)

    logger.info(f"State file saved to {state_path}")
    return state_path


def verify_and_record_checksums(
    raw_data_dir: Optional[Path] = None,
    state_path: Optional[Path] = None
) -> Dict[str, str]:
    """
    Calculate checksums for all files in the raw data directory and record them in state.yaml.

    Args:
        raw_data_dir: Path to raw data directory. If None, uses default.
        state_path: Optional path to state.yaml. If None, uses default.

    Returns:
        Dictionary mapping file paths to their checksums
    """
    if raw_data_dir is None:
        raw_data_dir = get_path("data", "raw")

    if not raw_data_dir.exists():
        logger.warning(f"Raw data directory not found: {raw_data_dir}")
        return {}

    state_data = load_state_yaml(state_path)

    if "checksums" not in state_data:
        state_data["checksums"] = {}

    if "raw_data" not in state_data["checksums"]:
        state_data["checksums"]["raw_data"] = {}

    checksums = {}

    for file_path in raw_data_dir.rglob("*"):
        if file_path.is_file():
            relative_path = str(file_path.relative_to(raw_data_dir))
            logger.info(f"Calculating checksum for: {relative_path}")

            try:
                checksum = calculate_file_checksum(file_path)
                checksums[relative_path] = checksum

                # Record in state
                state_data["checksums"]["raw_data"][relative_path] = {
                    "checksum": checksum,
                    "algorithm": "sha256",
                    "recorded_at": str(file_path.stat().st_mtime)
                }
            except Exception as e:
                logger.error(f"Failed to calculate checksum for {relative_path}: {e}")

    save_state_yaml(state_data, state_path)
    logger.info(f"Recorded checksums for {len(checksums)} files in state.yaml")

    return checksums


def calculate_linked_metadata_percentage(
    linked_trials_path: Optional[Path] = None,
    threshold: float = 0.95
) -> Dict[str, Any]:
    """
    Calculate the percentage of trials with linked metadata and verify against threshold.

    Args:
        linked_trials_path: Path to linked_trials.csv. If None, uses default.
        threshold: Minimum required percentage (default: 0.95 for 95%)

    Returns:
        Dictionary with calculation results
    """
    if linked_trials_path is None:
        linked_trials_path = get_path("data", "processed", "linked_trials.csv")

    if not linked_trials_path.exists():
        raise FileNotFoundError(f"Linked trials file not found: {linked_trials_path}")

    logger.info(f"Loading linked trials from: {linked_trials_path}")
    df = pd.read_csv(linked_trials_path)

    total_trials = len(df)
    if total_trials == 0:
        raise ValueError("Linked trials file is empty")

    # Count trials with valid stimulus_id (not null/empty)
    valid_mask = df["stimulus_id"].notna() & (df["stimulus_id"] != "")
    linked_count = valid_mask.sum()

    percentage = linked_count / total_trials

    result = {
        "total_trials": total_trials,
        "linked_trials": int(linked_count),
        "unlinked_trials": int(total_trials - linked_count),
        "linked_percentage": round(percentage, 4),
        "threshold": threshold,
        "meets_threshold": percentage >= threshold
    }

    # Log the results
    logger.info(f"=== Linked Metadata Verification ===")
    logger.info(f"Total trials: {total_trials}")
    logger.info(f"Trials with linked metadata: {linked_count}")
    logger.info(f"Linked percentage: {percentage:.2%}")
    logger.info(f"Threshold: {threshold:.2%}")
    logger.info(f"Result: {'PASS' if result['meets_threshold'] else 'FAIL'}")

    if not result["meets_threshold"]:
        logger.warning(
            f"SC-001 target not met: {percentage:.2%} < {threshold:.2%}. "
            f"Consider reviewing linkage derivation (T016)."
        )
    else:
        logger.info(
            f"SC-001 target met: {percentage:.2%} >= {threshold:.2%}. "
            f"'Vast majority' of trials have linked metadata."
        )

    return result


def main():
    """
    Main entry point for checksum verification and metadata percentage calculation.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    logger.info("Starting checksum verification and metadata percentage calculation (T018)")

    state_path = get_path("state", "projects", "PROJ-345", "state.yaml")
    linked_trials_path = get_path("data", "processed", "linked_trials.csv")

    # Step 1: Verify and record checksums for raw data
    logger.info("Step 1: Verifying raw data checksums...")
    try:
        checksums = verify_and_record_checksums(state_path=state_path)
        logger.info(f"Checksum verification complete. Recorded {len(checksums)} files.")
    except Exception as e:
        logger.error(f"Checksum verification failed: {e}")
        # Continue to metadata check even if checksums fail

    # Step 2: Calculate linked metadata percentage
    logger.info("Step 2: Calculating linked metadata percentage...")
    try:
        # Get threshold from config or use default
        threshold = 0.95  # Default per SC-001
        result = calculate_linked_metadata_percentage(
            linked_trials_path=linked_trials_path,
            threshold=threshold
        )

        # Record the result in state.yaml
        state_data = load_state_yaml(state_path)
        if "metadata" not in state_data:
            state_data["metadata"] = {}

        state_data["metadata"]["linked_metadata_verification"] = {
            "total_trials": result["total_trials"],
            "linked_trials": result["linked_trials"],
            "linked_percentage": result["linked_percentage"],
            "threshold": result["threshold"],
            "meets_threshold": result["meets_threshold"],
            "status": "PASS" if result["meets_threshold"] else "FAIL"
        }

        save_state_yaml(state_data, state_path)
        logger.info(f"Linked metadata verification result saved to state.yaml")

        # Return exit code based on threshold
        if not result["meets_threshold"]:
            logger.error("Exiting with error: Linked metadata percentage below threshold")
            return 1

    except FileNotFoundError as e:
        logger.error(f"Required file not found: {e}")
        return 1
    except ValueError as e:
        logger.error(f"Data validation error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Metadata percentage calculation failed: {e}")
        return 1

    logger.info("T018 checksum verification and metadata percentage calculation completed successfully")
    return 0


if __name__ == "__main__":
    exit(main())
