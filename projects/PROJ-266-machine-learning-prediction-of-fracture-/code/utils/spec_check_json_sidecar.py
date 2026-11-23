"""
T006c: Verify that spec.md does NOT require a JSON side-car file for each image.

This script checks the project's spec.md file to ensure it does not mandate
JSON side-car files for image data, confirming the CSV-only input requirement.

Verification command:
! grep -q "JSON sidecar" spec.md && echo "Spec JSON side‑car requirement verified"
"""
import sys
from pathlib import Path

def verify_no_json_sidecar_requirement(spec_path: Path) -> bool:
    """
    Verify that the spec file does not contain the phrase 'JSON sidecar'.
    
    Args:
        spec_path: Path to the spec.md file.
        
    Returns:
        True if 'JSON sidecar' is NOT found (requirement satisfied),
        False if 'JSON sidecar' IS found (requirement violated).
        
    Raises:
        FileNotFoundError: If spec_path does not exist.
    """
    if not spec_path.exists():
        raise FileNotFoundError(f"Spec file not found: {spec_path}")
    
    content = spec_path.read_text(encoding="utf-8")
    
    # Check for the forbidden phrase
    if "JSON sidecar" in content:
        return False
    
    return True

def main() -> int:
    """
    Main entry point for the verification script.
    
    Returns:
        0 if verification passes (JSON sidecar requirement NOT found),
        1 if verification fails (JSON sidecar requirement IS found).
    """
    # Locate spec.md in the project root
    project_root = Path(__file__).resolve().parent.parent.parent
    spec_path = project_root / "spec.md"
    
    try:
        if verify_no_json_sidecar_requirement(spec_path):
            print("Spec JSON side‑car requirement verified")
            return 0
        else:
            print("ERROR: Spec.md contains a requirement for JSON sidecar files.")
            print("This violates the CSV-only input assumption.")
            return 1
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())