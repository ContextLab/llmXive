import os
import re

REQUIRED_PACKAGES = [
    "datasets",
    "transformers",
    "scikit-learn",
    "statsmodels",
    "pandas",
    "pyyaml",
    "pytest",
    "huggingface_hub",
    "ruff",
]


def test_requirements_content():
    """
    Verify that requirements.txt exists and contains all required packages
    with version pinning (e.g., ==).
    """
    requirements_path = os.path.join("code", "requirements.txt")
    assert os.path.isfile(requirements_path), f"requirements.txt not found at {requirements_path}"

    with open(requirements_path, "r", encoding="utf-8") as f:
        content = f.read()

    lines = [line.strip() for line in content.splitlines() if line.strip() and not line.startswith("#")]

    # Check for each required package
    for package in REQUIRED_PACKAGES:
        # Construct regex to match package name with version pinning (e.g., package==1.0.0)
        # Allow for optional extras like package[extra]==1.0.0
        pattern = rf"^{re.escape(package)}(\[.*?\])?==.*$"
        found = False
        for line in lines:
            if re.match(pattern, line, re.IGNORECASE):
                found = True
                break
        assert found, f"Required package '{package}' with version pinning (==) not found in requirements.txt"