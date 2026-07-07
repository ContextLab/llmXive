import json
import os
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple

# Adjust import based on project structure provided in API surface
# The API surface shows: from ..config import ...
# Assuming this file is at code/src/data/quality_check.py
try:
    from ..config import FD_THRESHOLD, HIGH_MOTION_PERCENTAGE_THRESHOLD, MIN_SAMPLE_SIZE, DATA_DIR
except ImportError:
    # Fallback for direct execution or different import context
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from config import FD_THRESHOLD, HIGH_MOTION_PERCENTAGE_THRESHOLD, MIN_SAMPLE_SIZE, DATA_DIR

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_motion_json(json_path: Path) -> Dict[str, Any]:
    """Load motion parameters from a JSON sidecar file."""
    if not json_path.exists():
        raise FileNotFoundError(f"Motion JSON file not found: {json_path}")
    
    with open(json_path, 'r') as f:
        return json.load(f)

def calculate_fd(motion_params: List[float]) -> float:
    """
    Calculate Framewise Displacement (FD) from motion parameters.
    Motion params: [trans_x, trans_y, trans_z, rot_x, rot_y, rot_z]
    FD = |dx| + |dy| + |dz| + |drot_x| + |drot_y| + |drot_z|
    Note: Rotations are in radians. For small angles, 1 rad ≈ 57.3 deg.
    Standard FD (Power et al., 2012) converts rotation to mm using radius ~50mm.
    FD = |dx| + |dy| + |dz| + 50 * (|drot_x| + |drot_y| + |drot_z|)
    """
    if len(motion_params) != 6:
        raise ValueError(f"Expected 6 motion parameters, got {len(motion_params)}")
    
    # Calculate differences between consecutive volumes
    diffs = [abs(motion_params[i] - motion_params[i-1]) for i in range(1, len(motion_params))]
    
    # Translational differences (indices 0, 1, 2)
    trans_diffs = diffs[:3]
    
    # Rotational differences (indices 3, 4, 5) converted to mm (radius ~50mm)
    rot_diffs = [d * 50.0 for d in diffs[3:]]
    
    return sum(trans_diffs) + sum(rot_diffs)

def compute_subject_fd(json_path: Path) -> Tuple[float, int, int]:
    """
    Compute FD for a subject's time series.
    Returns: (mean_fd, n_high_motion_volumes, n_total_volumes)
    """
    data = load_motion_json(json_path)
    
    # Handle different BIDS structures for motion parameters
    # Look for 'repetitions' or 'volumes' or similar keys
    if 'repetitions' in data:
        motion_data = data['repetitions']
    elif 'volumes' in data:
        motion_data = data['volumes']
    elif 'bold' in data and 'repetitions' in data['bold']:
        motion_data = data['bold']['repetitions']
    else:
        # Try to find any key that looks like motion data (list of lists)
        for key, value in data.items():
            if isinstance(value, list) and len(value) > 0 and isinstance(value[0], list):
                motion_data = value
                break
        else:
            raise ValueError(f"Could not find motion data in {json_path}. Keys: {list(data.keys())}")
    
    n_total_volumes = len(motion_data)
    if n_total_volumes == 0:
        return 0.0, 0, 0
    
    fd_values = []
    for i in range(1, n_total_volumes):
        try:
            params = motion_data[i]
            # Ensure we have 6 parameters, pad if necessary
            if len(params) < 6:
                params = params + [0.0] * (6 - len(params))
            fd = calculate_fd(params)
            fd_values.append(fd)
        except Exception as e:
            logger.warning(f"Error calculating FD for volume {i}: {e}")
            continue
    
    if not fd_values:
        return 0.0, 0, n_total_volumes
    
    mean_fd = sum(fd_values) / len(fd_values)
    n_high_motion = sum(1 for fd in fd_values if fd > FD_THRESHOLD)
    
    return mean_fd, n_high_motion, n_total_volumes

def find_motion_jsons(subject_dir: Path) -> List[Path]:
    """Find all motion parameter JSON files for a subject."""
    json_files = []
    for root, dirs, files in os.walk(subject_dir):
        for file in files:
            if file.endswith('.json') and 'motion' in file.lower():
                json_files.append(Path(root) / file)
    return json_files

def run_quality_check(data_dir: Path = None) -> Dict[str, Any]:
    """
    Run quality check on all subjects in the data directory.
    Returns a manifest of included/excluded subjects.
    """
    if data_dir is None:
        data_dir = DATA_DIR / "openneuro"
    
    if not data_dir.exists():
        logger.error(f"Data directory not found: {data_dir}")
        return {"included": [], "excluded": [], "error": "Data directory not found"}
    
    manifest = {
        "included": [],
        "excluded": [],
        "total_subjects": 0,
        "high_motion_excluded": 0,
        "missing_data_excluded": 0
    }
    
    # Find all subject directories
    subjects = [d for d in data_dir.iterdir() if d.is_dir() and d.name.startswith('sub-')]
    manifest["total_subjects"] = len(subjects)
    
    logger.info(f"Found {len(subjects)} subjects to process")
    
    for subject_dir in subjects:
        subject_id = subject_dir.name
        json_files = find_motion_jsons(subject_dir)
        
        if not json_files:
            logger.warning(f"No motion JSON found for {subject_id}, excluding")
            manifest["excluded"].append({
                "subject_id": subject_id,
                "reason": "missing_motion_data"
            })
            manifest["missing_data_excluded"] += 1
            continue
        
        try:
            # Process each JSON file (could be multiple runs)
            total_high_motion = 0
            total_volumes = 0
            max_high_motion_pct = 0
            
            for json_file in json_files:
                mean_fd, n_high, n_total = compute_subject_fd(json_file)
                total_high_motion += n_high
                total_volumes += n_total
                
                if n_total > 0:
                  high_motion_pct = n_high / n_total
                  if high_motion_pct > max_high_motion_pct:
                      max_high_motion_pct = high_motion_pct
                
                logger.info(f"  {subject_id} ({json_file.name}): Mean FD={mean_fd:.3f}, High Motion={n_high}/{n_total} ({high_motion_pct:.1%})")
            
            # Check exclusion criteria
            if max_high_motion_pct > HIGH_MOTION_PERCENTAGE_THRESHOLD:
                logger.warning(f"Excluding {subject_id}: High motion ({max_high_motion_pct:.1%} > {HIGH_MOTION_PERCENTAGE_THRESHOLD:.1%})")
                manifest["excluded"].append({
                    "subject_id": subject_id,
                    "reason": "high_motion",
                    "high_motion_percentage": max_high_motion_pct
                })
                manifest["high_motion_excluded"] += 1
            else:
                logger.info(f"Including {subject_id}")
                manifest["included"].append({
                    "subject_id": subject_id,
                    "mean_fd": mean_fd,
                    "high_motion_percentage": max_high_motion_pct
                })
                
        except Exception as e:
            logger.error(f"Error processing {subject_id}: {e}")
            manifest["excluded"].append({
                "subject_id": subject_id,
                "reason": "processing_error",
                "error": str(e)
            })
            manifest["missing_data_excluded"] += 1
    
    # Log exclusion counts
    logger.info(f"Quality Check Summary: {len(manifest['included'])} included, {len(manifest['excluded'])} excluded")
    logger.info(f"  High motion exclusions: {manifest['high_motion_excluded']}")
    logger.info(f"  Missing data exclusions: {manifest['missing_data_excluded']}")
    
    # Check minimum sample size
    if len(manifest["included"]) < MIN_SAMPLE_SIZE:
        error_msg = f"CRITICAL: Remaining sample size ({len(manifest['included'])}) is below minimum threshold ({MIN_SAMPLE_SIZE}). Halting execution."
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    return manifest

def save_manifest(manifest: Dict[str, Any], output_path: Path = None):
    """Save the exclusion manifest to a JSON file."""
    if output_path is None:
        output_path = DATA_DIR / "exclusion_manifest.json"
    
    with open(output_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    
    logger.info(f"Exclusion manifest saved to {output_path}")

def main():
    """Main entry point for quality check."""
    logger.info("Starting quality check...")
    try:
        manifest = run_quality_check()
        save_manifest(manifest)
        logger.info("Quality check completed successfully.")
    except ValueError as e:
        logger.error(str(e))
        raise
    except Exception as e:
        logger.error(f"Unexpected error during quality check: {e}")
        raise

if __name__ == "__main__":
    main()
