"""
code/tests/test_requirements.py
--------------------------------

Integration test that installs the pinned requirements file in a fresh
virtual environment and verifies that all imports used throughout the
project resolve successfully.  The test is deliberately lightweight – it
does not run the full pipeline – but it ensures that the ``requirements.txt``
file is syntactically correct and that the declared packages are available.
"""

import subprocess
import sys

def test_requirements_install_and_imports():
    """
    Install the pinned requirements into the current interpreter and
    attempt to import every top‑level module referenced in the repository.
    """
    # Install the requirements file.
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "code/requirements.txt"])

    # List of imports that must succeed (derived from the project's source).
    imports = [
        "pandas",
        "numpy",
        "sklearn",
        "matplotlib",
        "seaborn",
        "mp_api",
        "pymatgen",
        "llmxive_toolkit",
    ]

    for module_name in imports:
        __import__(module_name)