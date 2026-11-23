import os
import sys
from pathlib import Path
from typing import Optional

def verify_wilcoxon_requirement(spec_path: Optional[Path] = None) -> bool:
    """
    Verify that spec.md requires a Wilcoxon signed-rank test.
    Returns True if the requirement is found, False otherwise.
    """
    if spec_path is None:
        # Default location relative to project root
        spec_path = Path("spec.md")
    
    if not spec_path.exists():
        print(f"ERROR: Spec file not found at {spec_path}")
        return False
    
    try:
        content = spec_path.read_text()
        if "Wilcoxon signed-rank test" in content:
            print("Spec Grad-CAM requirement verified")
            return True
        else:
            print("ERROR: Wilcoxon signed-rank test requirement not found in spec.md")
            return False
    except Exception as e:
        print(f"ERROR: Failed to read spec file: {e}")
        return False

def verify_gradcam_requirement(spec_path: Optional[Path] = None) -> bool:
    """
    Verify that spec.md requires Grad-CAM heatmaps for FR-006/FR-007.
    Returns True if the requirement is found, False otherwise.
    """
    if spec_path is None:
        # Default location relative to project root
        spec_path = Path("spec.md")
    
    if not spec_path.exists():
        print(f"ERROR: Spec file not found at {spec_path}")
        return False
    
    try:
        content = spec_path.read_text()
        if "Grad-CAM" in content:
            print("Spec Grad-CAM requirement verified")
            return True
        else:
            print("ERROR: Grad-CAM requirement not found in spec.md")
            return False
    except Exception as e:
        print(f"ERROR: Failed to read spec file: {e}")
        return False

def main():
    """
    Main entry point to verify Grad-CAM requirement in spec.md.
    """
    spec_path = Path("spec.md")
    if not spec_path.exists():
        print(f"ERROR: Spec file not found at {spec_path}")
        sys.exit(1)
    
    # Verify Grad-CAM requirement
    if not verify_gradcam_requirement(spec_path):
        sys.exit(1)
    
    sys.exit(0)

if __name__ == "__main__":
    main()
