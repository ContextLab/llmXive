import json
import os
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple

import numpy as np

# Import config for thresholds and paths
import src.config as config

logger = logging.getLogger(__name__)

# Constants
FD_THRESHOLD_MM = 0.5
MAX_HIGH_MOTION_PCT = 0.10
MIN_SAMPLE_SIZE = 20


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


def calculate_fd(motion_params: Dict[str, Any]) -> List[float]:
    """
    Calculate Framewise Displacement (FD) from motion parameters.
    
    FD is calculated as the sum of absolute differences of motion parameters
    across consecutive timepoints (power method).
    
    Args:
        motion_params: Dictionary containing 'trans_x', 'trans_y', 'trans_z',
                     'rot_x', 'rot_y', 'rot_z' lists.
                     
    Returns:
        List of FD values for each timepoint (length = N-1).
    """
    if not all(key in motion_params for key in ['trans_x', 'trans_y', 'trans_z', 'rot_x', 'rot_y', 'rot_z']):
        raise ValueError("Motion parameters missing required keys.")
    
    trans_x = np.array(motion_params['trans_x'])
    trans_y = np.array(motion_params['trans_y'])
    trans_z = np.array(motion_params['trans_z'])
    rot_x = np.array(motion_params['rot_x'])
    rot_y = np.array(motion_params['rot_y'])
    rot_z = np.array(motion_params['rot_z'])
    
    # Convert rotation to mm (assuming 50mm radius, standard approximation)
    rot_radius = 50.0
    
    # Calculate differences
    diff_trans = np.abs(np.diff(trans_x)) + np.abs(np.diff(trans_y)) + np.abs(np.diff(trans_z))
    diff_rot = np.abs(np.diff(rot_x)) * rot_radius + np.abs(np.diff(rot_y)) * rot_radius + np.abs(np.diff(rot_z)) * rot_radius
    
    fd = diff_trans + diff_rot
    return fd.tolist()


def compute_subject_fd(subject_motion_jsons: List[Path]) -> Tuple[List[float], int]:
    """
    Compute FD for a subject across all their runs.
    
    Args:
        subject_motion_jsons: List of paths to motion JSON files for the subject.
        
    Returns:
        Tuple of (list of all FD values, total number of volumes).
    """
    all_fd = []
    total_volumes = 0
    
    for json_path in subject_motion_jsons:
        try:
            motion_data = load_motion_json(json_path)
            fd_values = calculate_fd(motion_data)
            all_fd.extend(fd_values)
            # Total volumes is number of FD values + 1 (since FD is diff)
            # But we count the actual volumes from the JSON if available, otherwise estimate
            if 'RepetitionTime' in motion_data and 'total_volume_count' in motion_data:
                total_volumes += motion_data['total_volume_count']
            else:
                # Estimate: FD count + 1 per run
                total_volumes += len(fd_values) + 1
        except (FileNotFoundError, json.JSONDecodeError, ValueError) as e:
            logger.error(f"Failed to process {json_path}: {e}")
            raise
            
    return all_fd, total_volumes


def find_motion_jsons(data_root: Path) -> Dict[str, List[Path]]:
    """
    Find all motion JSON files organized by subject.
    
    Args:
        data_root: Root directory of the BIDS dataset.
        
    Returns:
        Dictionary mapping subject IDs to lists of motion JSON paths.
    """
    subject_map = {}
    
    # Look for *.json files that contain motion parameters
    # Typically found in sub-*/func/*_bold.json or sub-*/func/*_regressors.json
    for json_file in data_root.rglob("*.json"):
        # Check if this is a motion-related JSON
        # We assume it contains motion parameters if it has the required keys
        try:
            with open(json_file, 'r') as f:
                data = json.load(f)
            
            if any(key in data for key in ['trans_x', 'trans_y', 'trans_z', 'rot_x', 'rot_y', 'rot_z']):
                # Extract subject ID from path
                # Path format: .../sub-<label>/...
                parts = json_file.parts
                sub_idx = None
                for i, part in enumerate(parts):
                    if part.startswith('sub-'):
                        sub_idx = i
                        break
                
                if sub_idx is not None:
                    subject_id = parts[sub_idx]
                    if subject_id not in subject_map:
                        subject_map[subject_id] = []
                    subject_map[subject_id].append(json_file)
        except (json.JSONDecodeError, IOError):
            continue
            
    return subject_map


def run_quality_check(data_root: Path, output_manifest_path: Path) -> Dict[str, Any]:
    """
    Run quality check on the dataset.
    
    Computes FD for all subjects, excludes those with >10% high-motion volumes,
    logs exclusion counts, and halts if remaining sample size < 20.
    
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
    
    included_subjects = []
    excluded_subjects = []
    manifest_data = {
        "total_subjects": total_subjects,
        "included": [],
        "excluded": [],
        "exclusion_reasons": {},
        "sample_size": 0
    }
    
    for subject_id, json_paths in subject_motion_map.items():
        try:
            fd_values, total_vols = compute_subject_fd(json_paths)
            
            if total_vols == 0:
                logger.warning(f"Subject {subject_id}: No volumes found, excluding.")
                excluded_subjects.append(subject_id)
                manifest_data["exclusion_reasons"][subject_id] = "No volumes"
                continue
                
            high_motion_count = sum(1 for fd in fd_values if fd > FD_THRESHOLD_MM)
            high_motion_pct = high_motion_count / len(fd_values) if len(fd_values) > 0 else 0
            
            if high_motion_pct > MAX_HIGH_MOTION_PCT:
                logger.info(f"Subject {subject_id}: Excluded. High motion: {high_motion_pct:.2%} ({high_motion_count}/{len(fd_values)})")
                excluded_subjects.append(subject_id)
                manifest_data["exclusion_reasons"][subject_id] = f"High motion: {high_motion_pct:.2%}"
            else:
                logger.info(f"Subject {subject_id}: Included. High motion: {high_motion_pct:.2%}")
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
    manifest_data["sample_size"] = remaining_count
    manifest_data["total_subjects"] = total_subjects
    manifest_data["excluded_count"] = len(excluded_subjects)
    manifest_data["included_count"] = remaining_count
    
    logger.info(f"Quality check complete. Included: {remaining_count}, Excluded: {len(excluded_subjects)}")
    
    if remaining_count < MIN_SAMPLE_SIZE:
        error_msg = f"CRITICAL: Remaining sample size ({remaining_count}) is below minimum threshold (n ≥ {MIN_SAMPLE_SIZE}). Halting execution."
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


def main():
    """Main entry point for quality check script."""
    logging.basicConfig(level=logging.INFO)
    
    # Use config paths
    data_root = Path(config.RAW_DATA_DIR)
    output_manifest = Path(config.QUALITY_MANIFEST_PATH)
    
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
