import sys
from pathlib import Path

def verify_wilcoxon_requirement() -> bool:
    """
    Verify that spec.md requires a Wilcoxon signed-rank test for FR-005.
    
    Returns:
        bool: True if the requirement is found, False otherwise.
    """
    project_root = Path(__file__).resolve().parent.parent.parent
    spec_path = project_root / "spec.md"
    
    if not spec_path.exists():
        print(f"ERROR: {spec_path} not found.", file=sys.stderr)
        return False
    
    content = spec_path.read_text()
    target_phrase = "Wilcoxon signed-rank test"
    
    if target_phrase in content:
        return True
    
    return False

def main() -> int:
    """
    Entry point for verification script.
    
    Returns:
        int: 0 if verification passes, 1 otherwise.
    """
    if verify_wilcoxon_requirement():
        print("Spec Wilcoxon requirement verified")
        return 0
    else:
        print("ERROR: Spec Wilcoxon requirement NOT found.", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
