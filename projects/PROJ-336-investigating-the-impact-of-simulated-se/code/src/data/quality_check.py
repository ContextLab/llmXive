import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple, Union

import numpy as np

# Import config for thresholds and paths
import src.config as config

logger = logging.getLogger(__name__)

# Constants derived from config
FD_THRESHOLD_MM = config.FD_THRESHOLD
MAX_HIGH_MOTION_PCT = config.HIGH_MOTION_PERCENTAGE_THRESHOLD
MIN_SAMPLE_SIZE = config.MIN_SAMPLE_SIZE

def load_motion_json(json_path: Path) -> Dict[str, Any]:
    """
    Load a motion JSON sidecar file.

    Args:
        json_path: Path to the JSON file.

    Returns:
        Dictionary containing motion parameters.

    Raises:
        FileNotFoundError: If the JSON file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    if not json_path.exists():
        raise FileNotFoundError(f"Motion JSON file not found: {json_path}")

    with open(json_path, 'r') as f:
        return json.load(f)


def calculate_fd(motion_params: Union[Dict[str, Any], Path]) -> List[float]:
    """
    Calculate Framewise Displacement (FD) from motion parameters.

    This function accepts either a dictionary of motion parameters
    or a Path to a JSON side‑car file. If a Path is supplied, the JSON
    is loaded automatically.

    FD is calculated as the sum of absolute differences of motion
    parameters across consecutive timepoints (Power et al. method).

    Args:
        motion_params: Either a dict containing 'trans_x', 'trans_y',
                       'trans_z', 'rot_x', 'rot_y', 'rot_z' lists,
                       or a Path to a JSON file with those keys.

    Returns:
        List of FD values for each timepoint (length = N‑1).
    """
    if isinstance(motion_params, Path):
        motion_params = load_motion_json(motion_params)

    required_keys = ['trans_x', 'trans_y', 'trans_z',
                     'rot_x', 'rot_y', 'rot_z']
    if not all(key in motion_params for key in required_keys):
        raise ValueError("Motion parameters missing required keys.")

    trans_x = np.array(motion_params['trans_x'])
    trans_y = np.array(motion_params['trans_y'])
    trans_z = np.array(motion_params['trans_z'])
    rot_x = np.array(motion_params['rot_x'])
    rot_y = np.array(motion_params['rot_y'])
    rot_z = np.array(motion_params['rot_z'])

    # Convert rotation to mm assuming a 50 mm head radius
    rot_radius = 50.0

    diff_trans = (np.abs(np.diff(trans_x)) +
                  np.abs(np.diff(trans_y)) +
                  np.abs(np.diff(trans_z)))
    diff_rot = (np.abs(np.diff(rot_x)) * rot_radius +
                np.abs(np.diff(rot_y)) * rot_radius +
                np.abs(np.diff(rot_z)) * rot_radius)

    fd = diff_trans + diff_rot
    # Insert a leading 0 so the FD list length matches the number of volumes
    fd_list = [0.0] + fd.tolist()
    return fd_list


def compute_subject_fd(
    subject_motion_jsons: Union[List[Path], Path],
    threshold: float | None = None
) -> Tuple[Any, int]:
    """
    Compute FD statistics for a subject.

    If ``threshold`` is ``None`` (default), the function returns a tuple
    ``(fd_values, total_volumes)`` where ``fd_values`` is a list of all
    FD values across the subject's runs.

    If a numeric ``threshold`` is supplied, the function returns
    ``(high_motion_count, total_volumes)`` where ``high_motion_count`` is
    the number of volumes whose FD exceeds the threshold.

    Args:
        subject_motion_jsons: A list of Paths to motion JSON files for the
                             subject, or a single Path.
        threshold: Optional FD threshold (in mm) for counting high‑motion
                   volumes.

    Returns:
        Tuple containing either (fd list, total volumes) or
        (high‑motion count, total volumes) depending on ``threshold``.
    """
    if isinstance(subject_motion_jsons, Path):
        json_paths = [subject_motion_jsons]
    else:
        json_paths = subject_motion_jsons

    all_fd: List[float] = []
    total_volumes = 0

    for json_path in json_paths:
        motion_data = load_motion_json(json_path)
        fd_values = calculate_fd(motion_data)
        all_fd.extend(fd_values)

        # Determine number of volumes for this run
        if 'total_volume_count' in motion_data:
            total_volumes += int(motion_data['total_volume_count'])
        else:
            # Infer from one of the motion parameter arrays
            for key in ['trans_x', 'trans_y', 'trans_z',
                        'rot_x', 'rot_y', 'rot_z']:
                if key in motion_data and isinstance(motion_data[key], list):
                    total_volumes += len(motion_data[key])
                    break

    if threshold is not None:
        high_motion_count = sum(1 for fd in all_fd if fd > threshold)
        return high_motion_count, total_volumes

    return all_fd, total_volumes


def find_motion_jsons(data_root: Path) -> Dict[str, List[Path]]:
    """
    Find all motion JSON files organized by subject.

    Args:
        data_root: Root directory of the BIDS dataset.

    Returns:
        Dictionary mapping subject IDs to lists of motion JSON paths.
    """
    subject_map: Dict[str, List[Path]] = {}

    for json_file in data_root.rglob("*.json"):
        try:
            with open(json_file, 'r') as f:
                data = json.load(f)

            if any(key in data for key in
                   ['trans_x', 'trans_y', 'trans_z',
                    'rot_x', 'rot_y', 'rot_z']):
                parts = json_file.parts
                sub_idx = None
                for i, part in enumerate(parts):
                    if part.startswith('sub-'):
                        sub_idx = i
                        break
                if sub_idx is not None:
                    subject_id = parts[sub_idx]
                    subject_map.setdefault(subject_id, []).append(json_file)
        except (json.JSONDecodeError, OSError):
            continue

    return subject_map


def run_quality_check(data_root: Path, output_manifest_path: Path) -> Dict[str, Any]:
    """
    Run quality check on the dataset.

    Computes FD for all subjects, excludes those with >10 % high‑motion
    volumes, logs exclusion counts, and halts if remaining sample size
    < 20.

    Args:
        data_root: Root directory of the BIDS dataset.
        output_manifest_path: Path to save the exclusion manifest JSON.

    Returns:
        Dictionary containing the exclusion manifest data.

    Raises:
        ValueError: If the remaining sample size is below the minimum threshold.
    """
    logger.info(f"Starting quality check on dataset: {data_root}")

    subject_motion_map = find_motion_jsons(data_root)
    total_subjects = len(subject_motion_map)
    logger.info(f"Found {total_subjects} subjects with motion data.")

    included_subjects: List[str] = []
    excluded_subjects: List[str] = []
    manifest_data: Dict[str, Any] = {
        "total_subjects": total_subjects,
        "included": [],
        "excluded": [],
        "exclusion_reasons": {},
        "sample_size": 0
    }

    for subject_id, json_paths in subject_motion_map.items():
        try:
            fd_values, total_vols = compute_subject_fd(json_paths)  # returns fd list

            if total_vols == 0:
                logger.warning(f"Subject {subject_id}: No volumes found, excluding.")
                excluded_subjects.append(subject_id)
                manifest_data["exclusion_reasons"][subject_id] = "No volumes"
                continue

            high_motion_count = sum(1 for fd in fd_values if fd > FD_THRESHOLD_MM)
            high_motion_pct = (high_motion_count / len(fd_values)
                               if len(fd_values) > 0 else 0.0)

            if high_motion_pct > MAX_HIGH_MOTION_PCT:
                logger.info(
                    f"Subject {subject_id}: Excluded. High motion: "
                    f"{high_motion_pct:.2%} ({high_motion_count}/{len(fd_values)})"
                )
                excluded_subjects.append(subject_id)
                manifest_data["exclusion_reasons"][subject_id] = (
                    f"High motion: {high_motion_pct:.2%}"
                )
            else:
                logger.info(
                    f"Subject {subject_id}: Included. High motion: {high_motion_pct:.2%}"
                )
                included_subjects.append(subject_id)
                manifest_data["included"].append({
                    "subject_id": subject_id,
                    "total_volumes": total_vols,
                    "high_motion_count": high_motion_count,
                    "high_motion_pct": high_motion_pct,
                    "mean_fd": float(np.mean(fd_values))
                })

        except Exception as e:
            logger.error(f"Subject {subject_id}: Error processing - {e}")
            excluded_subjects.append(subject_id)
            manifest_data["exclusion_reasons"][subject_id] = f"Error: {str(e)}"

    remaining_count = len(included_subjects)
    manifest_data.update({
        "sample_size": remaining_count,
        "excluded_count": len(excluded_subjects),
        "included_count": remaining_count
    })

    logger.info(
        f"Quality check complete. Included: {remaining_count}, "
        f"Excluded: {len(excluded_subjects)}"
    )

    if remaining_count < MIN_SAMPLE_SIZE:
        error_msg = (
            f"CRITICAL: Remaining sample size ({remaining_count}) is below "
            f"minimum threshold (n ≥ {MIN_SAMPLE_SIZE}). Halting execution."
        )
        logger.error(error_msg)
        raise ValueError(error_msg)

    # Save manifest
    save_manifest(manifest_data, output_manifest_path)

    return manifest_data


def save_manifest(manifest_data: Dict[str, Any], output_path: Path) -> None:
    """
    Save the exclusion manifest to a JSON file.

    Args:
        manifest_data: Dictionary containing the manifest data.
        output_path: Path to save the JSON file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(manifest_data, f, indent=2)
    logger.info(f"Exclusion manifest saved to {output_path}")


def main() -> int:
    """Main entry point for quality check script."""
    logging.basicConfig(level=logging.INFO)

    # Define paths based on config
    data_root = config.DATA_DIR / "raw"
    output_manifest = config.DATA_DIR / "quality" / "exclusion_manifest.json"

    if not data_root.exists():
        logger.error(f"Data root directory does not exist: {data_root}")
        print(f"Error: Data root directory not found: {data_root}")
        print("Please ensure the dataset has been downloaded to the configured path.")
        return 1

    try:
        run_quality_check(data_root, output_manifest)
        print(f"Quality check completed successfully. Manifest saved to {output_manifest}")
        return 0
    except ValueError as e:
        print(f"Quality check failed: {e}")
        return 1
    except Exception as e:
        logger.exception(f"Unexpected error during quality check: {e}")
        print(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    exit(main())