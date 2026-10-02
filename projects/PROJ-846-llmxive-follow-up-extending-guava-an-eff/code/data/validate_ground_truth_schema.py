import json
import sys
import os
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add project root to path for imports if running as script
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.errors import DatasetUnavailableError
from utils.config import get_path

# Define the expected schema structure based on Guava dataset conventions
# and the project's data models (SymbolicObservation, Trajectory)
REQUIRED_TOP_LEVEL_KEYS = {"trajectories", "metadata"}
REQUIRED_TRAJECTORY_KEYS = {"trajectory_id", "frames", "task_description", "success"}
REQUIRED_FRAME_KEYS = {"frame_id", "timestamp", "objects", "image_path"}
REQUIRED_OBJECT_KEYS = {"object_id", "class_label", "bbox", "centroid"}

def load_ground_truth(file_path: str) -> Dict[str, Any]:
    """Load the ground truth JSON file."""
    if not os.path.exists(file_path):
        raise DatasetUnavailableError(f"Ground truth file not found: {file_path}")
    
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise DatasetUnavailableError(f"Invalid JSON in ground truth file: {e}")

def validate_structure(data: Dict[str, Any]) -> List[str]:
    """
    Validate the structure of the ground truth data against the expected schema.
    Returns a list of validation errors.
    """
    errors = []

    # Check top-level keys
    if not isinstance(data, dict):
        errors.append("Root element must be a JSON object.")
        return errors

    missing_top_keys = REQUIRED_TOP_LEVEL_KEYS - set(data.keys())
    if missing_top_keys:
        errors.append(f"Missing top-level keys: {missing_top_keys}")

    if "trajectories" not in data:
        return errors # Cannot validate further without trajectories

    if not isinstance(data["trajectories"], list):
        errors.append("'trajectories' must be a list.")
        return errors

    # Validate each trajectory
    for i, traj in enumerate(data["trajectories"]):
        traj_id = traj.get("trajectory_id", f"index_{i}")
        
        if not isinstance(traj, dict):
            errors.append(f"Trajectory {i} ({traj_id}) is not an object.")
            continue

        missing_traj_keys = REQUIRED_TRAJECTORY_KEYS - set(traj.keys())
        if missing_traj_keys:
            errors.append(f"Trajectory {traj_id} missing keys: {missing_traj_keys}")

        # Validate frames if present
        if "frames" in traj:
            if not isinstance(traj["frames"], list):
                errors.append(f"Trajectory {traj_id}: 'frames' must be a list.")
            else:
                for j, frame in enumerate(traj["frames"]):
                    if not isinstance(frame, dict):
                        errors.append(f"Trajectory {traj_id}, Frame {j}: Frame is not an object.")
                        continue
                    
                    missing_frame_keys = REQUIRED_FRAME_KEYS - set(frame.keys())
                    if missing_frame_keys:
                        errors.append(f"Trajectory {traj_id}, Frame {j}: Missing keys {missing_frame_keys}")
                    
                    # Validate objects if present
                    if "objects" in frame:
                        if not isinstance(frame["objects"], list):
                            errors.append(f"Trajectory {traj_id}, Frame {j}: 'objects' must be a list.")
                        else:
                            for k, obj in enumerate(frame["objects"]):
                                if not isinstance(obj, dict):
                                    errors.append(f"Trajectory {traj_id}, Frame {j}, Object {k}: Object is not an object.")
                                    continue
                                
                                missing_obj_keys = REQUIRED_OBJECT_KEYS - set(obj.keys())
                                if missing_obj_keys:
                                    errors.append(f"Trajectory {traj_id}, Frame {j}, Object {k}: Missing keys {missing_obj_keys}")

                                # Validate bbox structure (list of 4 floats/integers)
                                if "bbox" in obj:
                                    bbox = obj["bbox"]
                                    if not isinstance(bbox, list) or len(bbox) != 4:
                                        errors.append(f"Trajectory {traj_id}, Frame {j}, Object {k}: 'bbox' must be a list of 4 coordinates.")
                                    
                                # Validate centroid structure
                                if "centroid" in obj:
                                    centroid = obj["centroid"]
                                    if not isinstance(centroid, list) or len(centroid) != 2:
                                        errors.append(f"Trajectory {traj_id}, Frame {j}, Object {k}: 'centroid' must be a list of 2 coordinates.")

    return errors

def validate_ground_truth_schema(file_path: str) -> bool:
    """
    Main entry point to validate the ground truth annotations file.
    Returns True if valid, raises DatasetUnavailableError if invalid or missing.
    """
    try:
        data = load_ground_truth(file_path)
    except DatasetUnavailableError:
        # Re-raise to ensure the pipeline fails loudly as per requirements
        raise

    errors = validate_structure(data)
    
    if errors:
        error_msg = "Ground truth schema validation failed:\n" + "\n".join(f"  - {e}" for e in errors)
        raise DatasetUnavailableError(error_msg)

    print(f"Ground truth schema validation successful for {file_path}")
    return True

def main():
    """CLI entry point."""
    # Determine the path based on project configuration
    # The task description says: data/raw/guava/ground_truth_annotations.json
    gt_path = get_path("data/raw/guava/ground_truth_annotations.json")
    
    print(f"Validating ground truth schema at: {gt_path}")
    
    try:
        success = validate_ground_truth_schema(gt_path)
        if success:
            sys.exit(0)
    except DatasetUnavailableError as e:
        print(f"VALIDATION FAILED: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"UNEXPECTED ERROR: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()