"""
Unit tests for T002: Verify requirements.txt validity and importability.
"""
import subprocess
import sys
import os
import tempfile
import importlib.util
from pathlib import Path

import pytest


def test_requirements_file_exists():
    """Assert that code/requirements.txt exists at the project root."""
    project_root = Path(__file__).parent.parent.parent
    req_file = project_root / "code" / "requirements.txt"
    assert req_file.exists(), f"requirements.txt not found at {req_file}"


def test_requirements_syntax_valid():
    """Assert that requirements.txt can be parsed without syntax errors."""
    project_root = Path(__file__).parent.parent.parent
    req_file = project_root / "code" / "requirements.txt"

    with open(req_file, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # Filter out comments and empty lines
    packages = [
        line.strip()
        for line in lines
        if line.strip() and not line.strip().startswith("#")
    ]

    assert len(packages) > 0, "requirements.txt is empty or contains only comments"

    # Basic validation: each line should look like a package specifier
    for pkg in packages:
        # Allow comments, empty lines, and standard package specifiers
        # We don't do a full PEP 508 parse here, just a sanity check
        assert " " not in pkg or pkg.startswith("-"), f"Invalid package line: {pkg}"


def test_core_dependencies_present():
    """Assert that core dependencies required by the project are listed."""
    project_root = Path(__file__).parent.parent.parent
    req_file = project_root / "code" / "requirements.txt"

    with open(req_file, "r", encoding="utf-8") as f:
        content = f.read().lower()

    required_packages = [
        "pandas",
        "scikit-learn",
        "shap",
        "magpie",
        "datasets",
        "numpy",
        "scipy",
        "pyyaml",
        "cvxpy",
    ]

    for pkg in required_packages:
        assert pkg in content, f"Required package '{pkg}' not found in requirements.txt"


@pytest.mark.integration
def test_install_requirements_in_venv():
    """
    Create a temporary virtual environment, install requirements, and verify
    that the core packages can be imported.
    """
    project_root = Path(__file__).parent.parent.parent
    req_file = project_root / "code" / "requirements.txt"

    with tempfile.TemporaryDirectory() as tmp_dir:
        venv_path = Path(tmp_dir) / "venv"

        # Create virtual environment
        subprocess.run(
            [sys.executable, "-m", "venv", str(venv_path)],
            check=True,
            capture_output=True,
        )

        # Determine pip path
        if os.name == "nt":
            pip_path = venv_path / "Scripts" / "pip"
            python_path = venv_path / "Scripts" / "python"
        else:
            pip_path = venv_path / "bin" / "pip"
            python_path = venv_path / "bin" / "python"

        # Upgrade pip
        subprocess.run(
            [str(python_path), "-m", "pip", "install", "--upgrade", "pip"],
            check=True,
            capture_output=True,
        )

        # Install requirements
        result = subprocess.run(
            [str(pip_path), "install", "-r", str(req_file)],
            check=False,
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            pytest.fail(
                f"pip install failed:\nSTDOUT: {result.stdout}\nSTDERR: {result.stderr}"
            )

        # Verify imports of core packages
        core_packages = [
            "pandas",
            "sklearn",
            "shap",
            "magpie",
            "datasets",
            "numpy",
            "scipy",
            "yaml",
            "cvxpy",
        ]

        for pkg in core_packages:
            import_cmd = [str(python_path), "-c", f"import {pkg}"]
            result = subprocess.run(
                import_cmd, check=False, capture_output=True, text=True
            )
            if result.returncode != 0:
                pytest.fail(
                    f"Failed to import '{pkg}':\n{result.stderr}"
                )