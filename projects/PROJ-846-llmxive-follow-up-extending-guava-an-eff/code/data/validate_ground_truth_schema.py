"""
Task T021: Validate the integrity of ground_truth_annotations.json against its schema.

This script loads the ground truth annotations file downloaded in T020,
validates its structure against the expected schema, and writes a validation
report to data/artifacts/gt_schema_validation.json.

Expected Schema (derived from Guava dataset structure):
- Top-level: List of trajectory objects
- Each trajectory:
  - trajectory_id: str
  - frames: List of frame objects
    - frame_id: str
    - timestamp: float (optional)
    - objects: List of object annotations
      - object_id: str
      - class_label: str
      - bounding_box: [x_min, y_min, x_max, y_max] (list of 4 floats)
      - visible: bool (optional)
"""
import json
import sys
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from utils.errors import DatasetUnavailableError

# Import from existing API surface
from data.models import SymbolicObservation, Trajectory, TaskOutcome, PerceptionLog

def load_ground_truth(file_path: Path) -> Any:
    """Load ground truth JSON file."""
    if not file_path.exists():
        raise DatasetUnavailableError(f"Ground truth file not found: {file_path}")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except json.JSONDecodeError as e:
        raise DatasetUnavailableError(f"Invalid JSON in ground truth file: {e}")

def validate_structure(data: Any) -> Dict[str, Any]:
    """
    Validate the structure of ground truth annotations.
    
    Returns a validation report with:
    - is_valid: bool
    - errors: List[str]
    - warnings: List[str]
    - statistics: Dict[str, Any]
    """
    errors = []
    warnings = []
    
    # Check if data is a list (expected format: list of trajectories)
    if not isinstance(data, list):
        errors.append(f"Expected top-level list, got {type(data).__name__}")
        return {
            "is_valid": False,
            "errors": errors,
            "warnings": warnings,
            "statistics": {}
        }
    
    if len(data) == 0:
        warnings.append("Ground truth file is empty (no trajectories)")
        return {
            "is_valid": True,
            "errors": errors,
            "warnings": warnings,
            "statistics": {
                "total_trajectories": 0,
                "total_frames": 0,
                "total_objects": 0
            }
        }
    
    # Validate each trajectory
    total_frames = 0
    total_objects = 0
    
    for idx, trajectory in enumerate(data):
        if not isinstance(trajectory, dict):
            errors.append(f"Trajectory {idx}: Expected dict, got {type(trajectory).__name__}")
            continue
        
        # Check required fields
        if "trajectory_id" not in trajectory:
            errors.append(f"Trajectory {idx}: Missing 'trajectory_id'")
        elif not isinstance(trajectory["trajectory_id"], str):
            errors.append(f"Trajectory {idx}: 'trajectory_id' must be a string")
        
        if "frames" not in trajectory:
            errors.append(f"Trajectory {idx} (id: {trajectory.get('trajectory_id', 'unknown')}): Missing 'frames'")
            continue
        
        if not isinstance(trajectory["frames"], list):
            errors.append(f"Trajectory {idx}: 'frames' must be a list")
            continue
        
        # Validate frames
        for frame_idx, frame in enumerate(trajectory["frames"]):
            if not isinstance(frame, dict):
                errors.append(f"Trajectory {idx}, Frame {frame_idx}: Expected dict, got {type(frame).__name__}")
                continue
            
            if "frame_id" not in frame:
                errors.append(f"Trajectory {idx}, Frame {frame_idx}: Missing 'frame_id'")
            
            # Validate objects if present
            if "objects" in frame:
                if not isinstance(frame["objects"], list):
                    errors.append(f"Trajectory {idx}, Frame {frame_idx}: 'objects' must be a list")
                    continue
                
                for obj_idx, obj in enumerate(frame["objects"]):
                    if not isinstance(obj, dict):
                        errors.append(f"Trajectory {idx}, Frame {frame_idx}, Object {obj_idx}: Expected dict")
                        continue
                    
                    # Check required object fields
                    required_obj_fields = ["object_id", "class_label", "bounding_box"]
                    for field in required_obj_fields:
                        if field not in obj:
                            errors.append(f"Trajectory {idx}, Frame {frame_idx}, Object {obj_idx}: Missing '{field}'")
                    
                    # Validate bounding_box format
                    if "bounding_box" in obj:
                        bbox = obj["bounding_box"]
                        if not isinstance(bbox, list) or len(bbox) != 4:
                            errors.append(f"Trajectory {idx}, Frame {frame_idx}, Object {obj_idx}: 'bounding_box' must be a list of 4 floats")
                        else:
                            try:
                                # Ensure all coordinates are numeric
                                coords = [float(x) for x in bbox]
                                # Check for valid coordinate ordering (x_min <= x_max, y_min <= y_max)
                                if coords[0] > coords[2] or coords[1] > coords[3]:
                                    warnings.append(
                                        f"Trajectory {idx}, Frame {frame_idx}, Object {obj_idx}: "
                                        f"Invalid bounding box coordinates (x_min > x_max or y_min > y_max)"
                                    )
                            except (ValueError, TypeError):
                                errors.append(
                                    f"Trajectory {idx}, Frame {frame_idx}, Object {obj_idx}: "
                                    f"'bounding_box' contains non-numeric values"
                                )
                    
                    total_objects += 1
            
            total_frames += 1
    
    is_valid = len(errors) == 0
    
    return {
        "is_valid": is_valid,
        "errors": errors,
        "warnings": warnings,
        "statistics": {
            "total_trajectories": len(data),
            "total_frames": total_frames,
            "total_objects": total_objects
        }
    }

def validate_ground_truth_schema(file_path: Path, output_path: Path) -> Dict[str, Any]:
    """
    Main validation function.
    
    Args:
        file_path: Path to ground_truth_annotations.json
        output_path: Path to write validation report
    
    Returns:
        Validation report dictionary
    """
    print(f"Loading ground truth from: {file_path}")
    data = load_ground_truth(file_path)
    
    print("Validating structure...")
    report = validate_structure(data)
    
    # Add metadata
    report["source_file"] = str(file_path)
    report["validation_status"] = "PASSED" if report["is_valid"] else "FAILED"
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write report
    print(f"Writing validation report to: {output_path}")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    
    # Print summary
    print("\n" + "="*60)
    print("GROUND TRUTH SCHEMA VALIDATION REPORT")
    print("="*60)
    print(f"Source: {file_path}")
    print(f"Status: {'PASSED' if report['is_valid'] else 'FAILED'}")
    print(f"Trajectories: {report['statistics'].get('total_trajectories', 0)}")
    print(f"Frames: {report['statistics'].get('total_frames', 0)}")
    print(f"Objects: {report['statistics'].get('total_objects', 0)}")
    
    if report['errors']:
        print(f"\nErrors ({len(report['errors'])}):")
        for err in report['errors'][:5]:  # Show first 5 errors
            print(f"  - {err}")
        if len(report['errors']) > 5:
            print(f"  ... and {len(report['errors']) - 5} more errors")
    
    if report['warnings']:
        print(f"\nWarnings ({len(report['warnings'])}):")
        for warn in report['warnings'][:5]:
            print(f"  - {warn}")
        if len(report['warnings']) > 5:
            print(f"  ... and {len(report['warnings']) - 5} more warnings")
    
    print("="*60)
    
    return report

def main():
    """Main entry point for T021."""
    # Define paths
    project_root = Path(__file__).resolve().parent.parent.parent
    ground_truth_path = project_root / "data" / "raw" / "guava" / "ground_truth_annotations.json"
    output_path = project_root / "data" / "artifacts" / "gt_schema_validation.json"
    
    try:
        report = validate_ground_truth_schema(ground_truth_path, output_path)
        
        # Exit with appropriate code
        if report["is_valid"]:
            print("\nValidation PASSED.")
            sys.exit(0)
        else:
            print("\nValidation FAILED. Check errors above.")
            sys.exit(1)
            
    except DatasetUnavailableError as e:
        print(f"\nERROR: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\nUNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()