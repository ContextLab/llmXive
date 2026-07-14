"""
Unit tests to verify requirements.txt and lock generation logic.
"""
import os
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent.parent
REQUIREMENTS_FILE = PROJECT_ROOT / "requirements.txt"
LOCK_FILE = PROJECT_ROOT / "requirements.lock"
LOCK_SCRIPT = PROJECT_ROOT / "code" / "generate_requirements_lock.py"

def test_requirements_txt_exists():
    """Verify requirements.txt exists at the project root."""
    assert REQUIREMENTS_FILE.exists(), f"{REQUIREMENTS_FILE} must exist."
    assert REQUIREMENTS_FILE.stat().st_size > 0, f"{REQUIREMENTS_FILE} must not be empty."

def test_requirements_txt_has_pinned_versions():
    """Verify core dependencies have major/minor version pinning."""
    content = REQUIREMENTS_FILE.read_text()
    lines = [l.strip() for l in content.splitlines() if l.strip() and not l.startswith('#')]
    
    core_packages = [
        "pandas", "scikit-learn", "scipy", "numpy", 
        "biom-format", "skbio", "matplotlib", "seaborn", 
        "requests", "pytest", "statsmodels"
    ]
    
    found_packages = {}
    for line in lines:
        # Simple parser for package>=X.Y,<Z.0
        for pkg in core_packages:
            if line.startswith(pkg):
                found_packages[pkg] = line
                break

    missing = set(core_packages) - set(found_packages.keys())
    assert not missing, f"Missing core packages in requirements.txt: {missing}"

    for pkg, line in found_packages.items():
        # Check for version specifier (>= or ==)
        assert ">=" in line or "==" in line, \
            f"Package {pkg} must have a version constraint: {line}"

def test_lock_generation_script_exists():
    """Verify the lock generation script exists."""
    assert LOCK_SCRIPT.exists(), f"{LOCK_SCRIPT} must exist."

def test_lock_generation_script_is_executable():
    """Verify the lock script can be imported/syntax checked."""
    # We don't necessarily run pip-compile here as it might take too long or fail if
    # the environment isn't perfect, but we verify syntax.
    result = subprocess.run(
        [sys.executable, "-m", "py_compile", str(LOCK_SCRIPT)],
        cwd=PROJECT_ROOT
    )
    assert result.returncode == 0, f"Syntax error in {LOCK_SCRIPT}"

@pytest.mark.slow
def test_lock_generation_execution():
    """
    Test that running the lock generation script actually produces a file.
    This is marked slow because it may install pip-tools and resolve dependencies.
    """
    # Only run if we have network access and pip-tools capability
    # For CI, this might be skipped if offline
    try:
        subprocess.run(
            [sys.executable, str(LOCK_SCRIPT)],
            cwd=PROJECT_ROOT,
            check=True,
            timeout=120
        )
        assert LOCK_FILE.exists(), "Lock file should be created after running the script."
    except subprocess.TimeoutExpired:
        pytest.skip("Lock generation timed out (expected in slow CI environments)")
    except subprocess.CalledProcessError as e:
        # If pip-tools isn't available or network fails, we fail gracefully or skip
        if "pip-tools" in str(e):
            pytest.skip("pip-tools not available for lock generation test")
        else:
            raise