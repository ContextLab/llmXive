"""
Script to validate that quickstart.md enforces the full-environment re-execution baseline.
The validation MUST FAIL if the quickstart.md allows a "static-only shortcut".
"""
import sys
from pathlib import Path

def validate_quickstart():
    """
    Validates the quickstart.md file for compliance with the full-environment re-execution baseline.
    
    Requirements:
    1. Must exist at docs/quickstart.md
    2. Must NOT contain phrases indicating a "static-only" or "shortcut" mode.
    3. Must explicitly mention "full-environment", "re-execution", or "dynamic execution".
    4. Must provide steps for data download and model training (not just static analysis).
    """
    docs_dir = Path("docs")
    quickstart_path = docs_dir / "quickstart.md"

    if not quickstart_path.exists():
        print("ERROR: docs/quickstart.md does not exist.")
        return False

    content = quickstart_path.read_text(encoding="utf-8").lower()

    # Forbidden patterns indicating a shortcut or static-only approach
    forbidden_patterns = [
        "static-only shortcut",
        "static-only mode",
        "skip dynamic execution",
        "bypass re-execution",
        "shortcut mode",
        "static analysis only",
        "no execution required"
    ]

    for pattern in forbidden_patterns:
        if pattern in content:
            print(f"ERROR: Found forbidden pattern '{pattern}' in quickstart.md. "
                  "This violates the full-environment re-execution baseline.")
            return False

    # Required patterns indicating compliance
    required_patterns = [
        "full-environment",
        "re-execution",
        "dynamic execution",
        "run baseline",
        "execute tests"
    ]

    found_required = False
    for pattern in required_patterns:
        if pattern in content:
            found_required = True
            break

    if not found_required:
        print("ERROR: quickstart.md does not explicitly enforce full-environment re-execution. "
              "It must contain references to 'full-environment', 're-execution', or 'dynamic execution'.")
        return False

    # Check for specific steps: download, setup, train/execute
    has_download = "download" in content or "fetch" in content
    has_setup = "setup" in content or "install" in content or "environment" in content
    has_execute = "run" in content or "execute" in content or "train" in content

    if not (has_download and has_setup and has_execute):
        print("ERROR: quickstart.md is missing required steps for download, setup, and execution.")
        return False

    print("SUCCESS: quickstart.md correctly enforces the full-environment re-execution baseline.")
    return True

if __name__ == "__main__":
    success = validate_quickstart()
    sys.exit(0 if success else 1)
