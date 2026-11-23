"""
Verification script for T042c:
Verify that spec.md requires Grad-CAM heatmaps for FR-006/FR-007.
"""
import sys
from pathlib import Path

def main() -> int:
    project_root = Path(__file__).resolve().parent.parent.parent
    spec_path = project_root / "spec.md"

    if not spec_path.exists():
        print(f"ERROR: spec.md not found at {spec_path}", file=sys.stderr)
        return 1

    content = spec_path.read_text()

    if "Grad-CAM" in content:
        print("Spec Grad-CAM requirement verified")
        return 0
    else:
        print("ERROR: spec.md does not contain 'Grad-CAM'", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
