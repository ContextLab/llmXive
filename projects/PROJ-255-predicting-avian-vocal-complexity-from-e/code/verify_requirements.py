"""
Task T002b: Verify requirements.txt content and installation success.

This script verifies that requirements.txt exists, contains the exact list
of dependencies specified in T002a, and that 'pip install -r requirements.txt'
succeeds without errors.
"""
import os
import sys
import subprocess
import tempfile
from pathlib import Path

# Exact list from T002a
EXPECTED_PACKAGES = [
    "librosa==0.10.1",
    "statsmodels==0.14.0",
    "osmnx==1.8.0",
    "geopy==2.4.0",
    "pandas==2.1.0",
    "scikit-learn==1.3.0",
    "matplotlib==3.8.0",
    "seaborn==0.13.0",
    "requests==2.31.0",
    "datasets==2.14.0",
    "pytest==7.4.0",
    "pyyaml==6.0.1"
]

def get_project_root() -> Path:
    """Get the project root directory."""
    # Assume this script is in code/ directory
    return Path(__file__).parent.parent

def verify_requirements_file(root: Path) -> bool:
    """Verify requirements.txt exists and contains expected packages."""
    req_file = root / "requirements.txt"
    
    if not req_file.exists():
        print(f"ERROR: requirements.txt not found at {req_file}")
        return False
    
    with open(req_file, 'r') as f:
        content = f.read().strip()
    
    lines = [line.strip() for line in content.split('\n') if line.strip() and not line.startswith('#')]
    
    if len(lines) != len(EXPECTED_PACKAGES):
        print(f"ERROR: requirements.txt has {len(lines)} lines, expected {len(EXPECTED_PACKAGES)}")
        print(f"Found: {lines}")
        print(f"Expected: {EXPECTED_PACKAGES}")
        return False
    
    for expected, found in zip(EXPECTED_PACKAGES, lines):
        if expected != found:
            print(f"ERROR: Mismatch found")
            print(f"Expected: {expected}")
            print(f"Found: {found}")
            return False
    
    print("SUCCESS: requirements.txt content matches expected list exactly")
    return True

def install_requirements(root: Path) -> bool:
    """Install requirements and verify success."""
    req_file = root / "requirements.txt"
    
    print(f"Installing requirements from {req_file}...")
    
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", str(req_file)],
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        if result.returncode != 0:
            print(f"ERROR: pip install failed with return code {result.returncode}")
            print(f"STDOUT: {result.stdout}")
            print(f"STDERR: {result.stderr}")
            return False
        
        print("SUCCESS: pip install completed without errors")
        return True
        
    except subprocess.TimeoutExpired:
        print("ERROR: pip install timed out")
        return False
    except Exception as e:
        print(f"ERROR: Exception during pip install: {e}")
        return False

def verify_installed_packages() -> bool:
    """Verify all expected packages are installed with correct versions."""
    print("Verifying installed packages...")
    
    # Get pip list
    result = subprocess.run(
        [sys.executable, "-m", "pip", "list", "--format=freeze"],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        print(f"ERROR: pip list failed: {result.stderr}")
        return False
    
    installed = {}
    for line in result.stdout.strip().split('\n'):
        if '==' in line:
            pkg, ver = line.split('==', 1)
            installed[pkg.lower()] = ver
    
    all_ok = True
    for expected in EXPECTED_PACKAGES:
        pkg, ver = expected.split('==', 1)
        pkg_lower = pkg.lower()
        
        if pkg_lower not in installed:
            print(f"ERROR: Package {pkg} not installed")
            all_ok = False
        elif installed[pkg_lower] != ver:
            print(f"ERROR: {pkg} version mismatch")
            print(f"  Expected: {ver}")
            print(f"  Found: {installed[pkg_lower]}")
            all_ok = False
        else:
            print(f"OK: {pkg}=={ver}")
    
    return all_ok

def main():
    """Main entry point for verification."""
    root = get_project_root()
    print(f"Project root: {root}")
    
    # Step 1: Verify requirements.txt content
    if not verify_requirements_file(root):
        print("FAILED: requirements.txt verification failed")
        sys.exit(1)
    
    # Step 2: Install requirements
    if not install_requirements(root):
        print("FAILED: requirements installation failed")
        sys.exit(1)
    
    # Step 3: Verify installed packages
    if not verify_installed_packages():
        print("FAILED: installed packages verification failed")
        sys.exit(1)
    
    print("\n" + "="*50)
    print("T002b VERIFICATION SUCCESSFUL")
    print("="*50)
    print("requirements.txt content: VERIFIED")
    print("pip install: SUCCESSFUL")
    print("installed packages: VERIFIED")
    sys.exit(0)

if __name__ == "__main__":
    main()
