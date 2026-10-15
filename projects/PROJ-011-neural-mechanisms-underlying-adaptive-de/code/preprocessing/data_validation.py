"""
Data Validation Module for OpenNeuro ds003694.
Verifies the presence of required NIfTI and behavioral files for each participant
and writes a dataset manifest JSON file.
"""
import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple

from utils.config import get_config
from utils.logger import get_logger
from utils.io import ensure_dir, save_json, file_exists, load_csv

logger = get_logger(__name__)

# Required behavioral columns (as defined in the spec)
REQUIRED_BEHAVIORAL_COLUMNS = {"private_belief", "social_feedback", "choice"}


def validate_dataset_structure(dataset_root: Path) -> Tuple[bool, List[str]]:
    """
    Validate that the dataset root follows the BIDS-like structure expected for ds003694.

    Returns:
        (is_valid, errors)
    """
    errors: List[str] = []
    if not dataset_root.is_dir():
        errors.append(f"Dataset root directory does not exist: {dataset_root}")
        return False, errors

    # ds003694 should contain a dataset_description.json at the top level
    if not (dataset_root / "dataset_description.json").is_file():
        errors.append("Missing dataset_description.json at dataset root.")

    # At least one participant directory should exist
    participant_dirs = [p for p in dataset_root.iterdir() if p.is_dir() and p.name.startswith("sub-")]
    if not participant_dirs:
        errors.append("No participant directories (sub-*) found under dataset root.")

    return len(errors) == 0, errors


def validate_participant_session(dataset_root: Path, participant: str, session: str) -> Tuple[bool, List[str], Dict]:
    """
    Validate a single participant/session pair.

    Returns:
        (is_valid, errors, info_dict)
    """
    errors: List[str] = []
    info: Dict = {"participant": participant, "session": session}

    base = dataset_root / participant
    if session:
        base = base / session

    # Functional NIfTI file
    func_path = base / "func" / f"{participant}_{session}_task-social_bold.nii.gz"
    if not file_exists(func_path):
        errors.append(f"Missing functional image: {func_path}")
    else:
        info["func"] = str(func_path)

    # Behavioral TSV (BIDS convention)
    beh_path = base / "beh" / f"{participant}_{session}_task-social_beh.tsv"
    if not file_exists(beh_path):
        # Try a fallback location that some datasets use
        beh_path = base / f"{participant}_{session}_task-social_beh.tsv"
        if not file_exists(beh_path):
            errors.append(f"Missing behavioral log file for {participant}/{session}")
            beh_path = None
    if beh_path:
        info["beh"] = str(beh_path)
        # Validate required columns
        try:
            df = load_csv(beh_path)
            missing = REQUIRED_BEHAVIORAL_COLUMNS - set(df[0].keys())
            if missing:
                errors.append(
                    f"Behavioral file {beh_path} missing columns: {sorted(missing)}"
                )
        except Exception as e:
            errors.append(f"Failed to read behavioral file {beh_path}: {e}")

    return len(errors) == 0, errors, info


def build_manifest(dataset_root: Path) -> Dict:
    """
    Walk through the dataset and build a manifest dictionary.
    Raises FileNotFoundError if any required file is missing.
    """
    valid, struct_errors = validate_dataset_structure(dataset_root)
    if not valid:
        raise FileNotFoundError("Dataset structure validation failed: " + "; ".join(struct_errors))

    manifest = {"participants": []}
    participants = [p.name for p in dataset_root.iterdir() if p.is_dir() and p.name.startswith("sub-")]

    for pid in participants:
        participant_entry = {"id": pid, "sessions": []}
        participant_dir = dataset_root / pid
        # Sessions may be present or not; handle both cases
        session_dirs = [
            d.name for d in participant_dir.iterdir()
            if d.is_dir() and d.name.startswith("ses-")
        ]
        if not session_dirs:
            # Treat as a single session with empty string
            session_dirs = [""]

        for sid in session_dirs:
            valid_sess, sess_errors, info = validate_participant_session(dataset_root, pid, sid)
            if not valid_sess:
                raise FileNotFoundError(
                    f"Validation errors for participant {pid}, session '{sid or 'N/A'}': "
                    + "; ".join(sess_errors)
                )
            # Clean up empty session string for manifest readability
            session_id = sid if sid else "default"
            participant_entry["sessions"].append(
                {
                    "id": session_id,
                    "func": info.get("func"),
                    "beh": info.get("beh"),
                }
            )
        manifest["participants"].append(participant_entry)

    return manifest


def write_manifest(manifest: Dict, output_path: Path) -> None:
    """
    Write the manifest JSON to the given location, ensuring parent directories exist.
    """
    ensure_dir(output_path.parent)
    save_json(manifest, output_path, indent=2)
    logger.info(f"Dataset manifest written to {output_path}")


def main() -> None:
    """
    Main entry point.
    Loads configuration, validates the dataset, builds a manifest, and writes it to
    state/dataset_manifest.json.
    """
    cfg = get_config()
    dataset_root = cfg.data_root / "raw"
    logger.info(f"Starting validation of dataset at {dataset_root}")

    manifest = build_manifest(dataset_root)

    # Write manifest
    manifest_path = cfg.project_root / "state" / "dataset_manifest.json"
    write_manifest(manifest, manifest_path)

    logger.info("Data validation completed successfully.")


if __name__ == "__main__":
    main()
