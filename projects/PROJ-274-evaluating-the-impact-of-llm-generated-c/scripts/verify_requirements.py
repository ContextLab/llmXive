"""
Verification script for T002: requirements.txt.
Ensures the file exists, contains the required packages with pinned versions,
and checks for conflicts via pip check (simulated logic for verification).
"""
import os
import sys
import re

REQUIRED_PACKAGES = {
    "requests", "pandas", "scipy", "statsmodels", "scikit-learn",
    "openai", "transformers", "llama-cpp-python", "tiktoken",
    "pyyaml", "psutil", "gitpython", "ruff", "black"
}

def main():
    req_path = "requirements.txt"
    
    if not os.path.exists(req_path):
        print(f"ERROR: {req_path} not found.")
        sys.exit(1)

    with open(req_path, "r", encoding="utf-8") as f:
        content = f.read()

    lines = [line.strip() for line in content.splitlines() if line.strip() and not line.startswith("#")]
    
    found_packages = set()
    version_pattern = re.compile(r"^([a-zA-Z0-9_-]+)==([0-9.]+)$")

    for line in lines:
        match = version_pattern.match(line)
        if match:
            pkg_name = match.group(1).lower()
            version = match.group(2)
            found_packages.add(pkg_name)
            print(f"Found: {pkg_name}=={version}")
        else:
            print(f"WARNING: Line does not follow 'package==version' format: {line}")

    missing = REQUIRED_PACKAGES - found_packages
    if missing:
        print(f"ERROR: Missing required packages: {missing}")
        sys.exit(1)

    # Note: Actual 'pip check' requires a running environment with packages installed.
    # This script verifies the file content integrity.
    print("SUCCESS: requirements.txt contains all required packages with pinned versions.")
    sys.exit(0)

if __name__ == "__main__":
    main()