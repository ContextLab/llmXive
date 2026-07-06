"""
Script to verify and ensure requirements.txt contains pinned versions for reproducibility.
This task verifies T002's work and ensures all dependencies are pinned.
"""
import os
import re
import sys
from pathlib import Path

REQUIRED_PACKAGES = {
    "numpy": "1.26.4",
    "pandas": "2.2.1",
    "scipy": "1.12.0",
    "scikit-learn": "1.4.1.post1",
    "cmdstanpy": "1.2.0",
    "matplotlib": "3.8.3",
    "seaborn": "0.13.2",
    "pyyaml": "6.0.1",
    "pytest": "8.1.1",
    "black": "24.3.0",
    "flake8": "7.0.0",
}

def verify_requirements(root_dir: str) -> bool:
    """Verify requirements.txt has all required packages pinned."""
    req_path = Path(root_dir) / "requirements.txt"
    
    if not req_path.exists():
        print("ERROR: requirements.txt not found")
        return False

    with open(req_path, "r") as f:
        content = f.read()

    missing = []
    unpinned = []
    
    for package, expected_version in REQUIRED_PACKAGES.items():
        # Check if package exists in requirements.txt
        pattern = rf"^{re.escape(package)}=="
        if not re.search(pattern, content, re.MULTILINE | re.IGNORECASE):
            missing.append(package)
            continue
        
        # Check if version is pinned (==)
        version_pattern = rf"^{re.escape(package)}==(\d+\.\d+[^,\n]*)"
        match = re.search(version_pattern, content, re.MULTILINE | re.IGNORECASE)
        if not match:
            unpinned.append(package)
        else:
            current_version = match.group(1)
            if current_version != expected_version:
                print(f"INFO: {package} version {current_version} found (expected {expected_version})")

    if missing:
        print(f"ERROR: Missing packages in requirements.txt: {', '.join(missing)}")
        return False
    
    if unpinned:
        print(f"ERROR: Unpinned packages in requirements.txt: {', '.join(unpinned)}")
        return False

    print("SUCCESS: All required packages are present and pinned in requirements.txt")
    return True

def main():
    root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    success = verify_requirements(root_dir)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()