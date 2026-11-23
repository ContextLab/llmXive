"""Verify that the project's requirements can be installed and match exact versions.

This script performs two checks:
1. Runs `pip install -r requirements.txt` and ensures it exits with code 0.
2. Retrieves the list of installed packages via `pip list --format=json` and
   verifies that each package specified in `requirements.txt` is present with
   the exact pinned version.

If any check fails, the script exits with a non‑zero status and prints a
concise error message. Successful execution prints a short confirmation.
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple

def parse_requirements(req_path: Path) -> List[Tuple[str, str]]:
    """Parse a requirements.txt file returning a list of (package, version)."""
    reqs = []
    for line in req_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "==" not in line:
            raise ValueError(f"Requirement line not pinned with '==': {line}")
        pkg, ver = line.split("==", 1)
        reqs.append((pkg.strip().lower(), ver.strip()))
    return reqs

def get_installed_packages() -> Dict[str, str]:
    """Return a mapping of installed package name -> version using pip list --format=json."""
    result = subprocess.run(
        [sys.executable, "-m", "pip", "list", "--format=json"],
        capture_output=True,
        text=True,
        check=True,
    )
    packages = json.loads(result.stdout)
    return {pkg["name"].lower(): pkg["version"] for pkg in packages}

def main() -> int:
    project_root = Path(__file__).resolve().parent.parent
    req_path = project_root / "requirements.txt"

    # 1. Install requirements
    print("Installing requirements from", req_path)
    install_cmd = [sys.executable, "-m", "pip", "install", "-r", str(req_path)]
    try:
        subprocess.run(install_cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ pip install failed with exit code {e.returncode}")
        return 1

    # 2. Verify installed versions
    required = parse_requirements(req_path)
    installed = get_installed_packages()

    mismatches = []
    for pkg, req_ver in required:
        installed_ver = installed.get(pkg)
        if installed_ver is None:
            mismatches.append(f"{pkg}: not installed")
        elif installed_ver != req_ver:
            mismatches.append(f"{pkg}: required {req_ver}, installed {installed_ver}")

    if mismatches:
        print("❌ Version mismatches detected:")
        for msg in mismatches:
            print("   -", msg)
        return 1

    print("✅ All requirements installed with exact pinned versions.")
    return 0

if __name__ == "__main__":
    sys.exit(main())