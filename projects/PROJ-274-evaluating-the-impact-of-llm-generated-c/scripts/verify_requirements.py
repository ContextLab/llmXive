"""
Verification script for T002: requirements.txt
Ensures all required packages are present with pinned versions.
"""
import os
import sys
import subprocess

REQUIRED_PACKAGES = [
    "requests",
    "pandas",
    "scipy",
    "statsmodels",
    "scikit-learn",
    "openai",
    "transformers",
    "llama-cpp-python",
    "tiktoken",
    "pyyaml",
    "psutil",
    "gitpython",
    "ruff",
    "black",
]

def main():
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    req_path = os.path.join(root_dir, "requirements.txt")

    if not os.path.exists(req_path):
        print(f"ERROR: {req_path} not found.")
        sys.exit(1)

    with open(req_path, "r", encoding="utf-8") as f:
        content = f.read()

    lines = [line.strip() for line in content.splitlines() if line.strip() and not line.startswith("#")]

    found_packages = {}
    for line in lines:
        if "==" in line:
            pkg, ver = line.split("==", 1)
            found_packages[pkg.lower()] = ver
        else:
            print(f"WARNING: Package '{line}' does not have a pinned version (==).")

    missing = []
    for pkg in REQUIRED_PACKAGES:
        if pkg.lower() not in found_packages:
            missing.append(pkg)

    if missing:
        print(f"ERROR: Missing pinned versions for: {missing}")
        sys.exit(1)

    print("SUCCESS: All required packages are present with pinned versions.")
    print("Running 'pip check' to verify no conflicts...")
    
    try:
        result = subprocess.run(
            ["pip", "check"],
            cwd=root_dir,
            capture_output=True,
            text=True,
            timeout=60
        )
        if result.returncode == 0:
            print("SUCCESS: pip check passed. No dependency conflicts found.")
            sys.exit(0)
        else:
            print(f"ERROR: pip check failed with output:\n{result.stdout}\n{result.stderr}")
            sys.exit(1)
    except subprocess.TimeoutExpired:
        print("ERROR: pip check timed out.")
        sys.exit(1)
    except FileNotFoundError:
        print("WARNING: 'pip' command not found. Skipping conflict check.")
        sys.exit(0)

if __name__ == "__main__":
    main()