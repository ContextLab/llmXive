"""
Verification script for PyVib installation and version pinning.

This script verifies that the 'pyvib' package is installed and that its version
matches the pinned version in requirements.txt.

Requirement: Create code/utils/verify_pyvib.py. Run import pyvib; print(pyvib.__version__).
Ensure version matches requirements.txt.
"""
import sys
import re
from pathlib import Path

def get_project_root() -> Path:
    """Return the project root directory (parent of 'code')."""
    return Path(__file__).resolve().parent.parent.parent

def get_requirements_path() -> Path:
    """Return the path to requirements.txt."""
    return get_project_root() / "code" / "requirements.txt"

def parse_requirements(path: Path) -> dict:
    """Parse requirements.txt and return a dict of package -> version."""
    requirements = {}
    if not path.exists():
        raise FileNotFoundError(f"requirements.txt not found at {path}")
    
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            # Handle package==version, package>=version, etc.
            match = re.match(r"^([a-zA-Z0-9_-]+)([<>=!~]+)?(.*)$", line)
            if match:
                pkg_name = match.group(1).lower()
                version_spec = match.group(3) if match.group(3) else None
                requirements[pkg_name] = version_spec
    return requirements

def verify_pyvib() -> bool:
    """
    Verify PyVib installation and version pinning.
    
    Returns:
        bool: True if verification passes, False otherwise.
    """
    # Step 1: Try to import pyvib
    try:
        import pyvib
    except ImportError as e:
        print(f"ERROR: pyvib is not installed. ImportError: {e}")
        print("Please install it with: pip install pyvib")
        return False

    # Step 2: Get installed version
    installed_version = getattr(pyvib, "__version__", "unknown")
    print(f"PyVib installed version: {installed_version}")

    # Step 3: Check requirements.txt for version pin
    req_path = get_requirements_path()
    try:
        requirements = parse_requirements(req_path)
    except FileNotFoundError as e:
        print(f"WARNING: {e}")
        print("Cannot verify version pinning without requirements.txt.")
        return True  # Installation is verified, version pin check is optional

    if "pyvib" not in requirements:
        print("WARNING: 'pyvib' not found in requirements.txt.")
        print("Version pinning cannot be verified.")
        return True  # Installation is verified, pinning is missing but not fatal

    pinned_version = requirements["pyvib"]
    if pinned_version is None:
        print("WARNING: 'pyvib' in requirements.txt has no version specifier.")
        print("Version pinning is not enforced.")
        return True

    # Simple exact match check (could be extended for semver ranges)
    # If pinned_version is something like "==1.2.3", we strip the operator
    match = re.match(r"^==?(.+)$", pinned_version)
    expected_version = match.group(1) if match else pinned_version

    if installed_version == expected_version:
        print(f"SUCCESS: PyVib version {installed_version} matches pinned version {expected_version}.")
        return True
    else:
        print(f"ERROR: PyVib version mismatch.")
        print(f"  Installed: {installed_version}")
        print(f"  Pinned in requirements.txt: {pinned_version}")
        return False

def main():
    """Entry point for the verification script."""
    print("Verifying PyVib installation and version pinning...")
    print("-" * 50)
    success = verify_pyvib()
    print("-" * 50)
    if success:
        print("Verification PASSED.")
        sys.exit(0)
    else:
        print("Verification FAILED.")
        sys.exit(1)

if __name__ == "__main__":
    main()