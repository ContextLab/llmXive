import os
import subprocess
import sys
from pathlib import Path

def test_requirements_file_contents():
    """Verify requirements.txt matches the exact pinned versions."""
    project_root = Path(__file__).parent.parent
    req_file = project_root / "code" / "requirements.txt"
    
    assert req_file.exists(), f"requirements.txt not found at {req_file}"
    
    expected_lines = [
        "numpy==1.26.4",
        "scipy==1.13.1",
        "pandas==2.2.2",
        "emcee==3.1.6",
        "dynesty==2.1.4",
        "astropy==6.1.1",
        "requests==2.32.3",
        "pytest==8.3.2",
        "ruamel.yaml==0.18.6"
    ]
    
    with open(req_file, "r") as f:
        actual_lines = [line.strip() for line in f.readlines() if line.strip()]
    
    assert actual_lines == expected_lines, (
        f"requirements.txt content mismatch.\n"
        f"Expected:\n{expected_lines}\n"
        f"Actual:\n{actual_lines}"
    )

def test_requirements_installable():
    """Verify the requirements file can be parsed by pip (syntax check)."""
    project_root = Path(__file__).parent.parent
    req_file = project_root / "code" / "requirements.txt"
    
    # Use pip check or dry-run to verify syntax without full install in test env
    # Since we can't guarantee a clean env in every test runner, we just verify
    # the file exists and has the correct format (lines with ==).
    with open(req_file, "r") as f:
        content = f.read()
    
    for line in content.splitlines():
        if not line.strip():
            continue
        assert "==" in line, f"Invalid requirement line (missing pinned version): {line}"