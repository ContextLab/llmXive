import sys
from pathlib import Path

def verify_iou_threshold_not_defined(spec_path: str = "spec.md") -> bool:
    """
    Verify that SC-003 does not define a hard IoU threshold.
    
    Checks that the spec file does not contain patterns like "mean_iou >"
    which would indicate a hardcoded threshold requirement.
    
    Args:
        spec_path: Path to the specification file (relative to project root)
        
    Returns:
        True if no hard IoU threshold is found, False otherwise.
        
    Raises:
        FileNotFoundError: If the spec file does not exist.
    """
    path = Path(spec_path)
    if not path.exists():
        raise FileNotFoundError(f"Specification file not found: {spec_path}")
        
    content = path.read_text()
    
    # Check for patterns indicating a hard IoU threshold
    # We look for "mean_iou >" or similar strict threshold definitions
    if "mean_iou >" in content:
        return False
    if "mean_iou>=" in content:
        return False
    if "iou_threshold >" in content:
        return False
        
    return True

def main():
    """
    Main entry point for the verification script.
    Prints verification result and exits with appropriate code.
    """
    spec_file = "spec.md"
    
    try:
        is_valid = verify_iou_threshold_not_defined(spec_file)
        
        if is_valid:
            print("Spec IoU threshold not defined")
            sys.exit(0)
        else:
            print("ERROR: Spec defines a hard IoU threshold (e.g., 'mean_iou >')")
            sys.exit(1)
            
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        sys.exit(2)
    except Exception as e:
        print(f"ERROR: Unexpected error during verification: {e}")
        sys.exit(3)

if __name__ == "__main__":
    main()