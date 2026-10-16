"""
Test that the requirements dry‑run script produces an output containing the
phrase “Successfully installed”.  This validates that the pinned dependencies
resolve without conflict.
"""
import re
from pathlib import Path

from llmxive_toolkit import paths


def test_requirements_check_output():
    """
    Run the ``check_requirements.py`` script (imported as a module) and
    verify that the generated results file includes a success message.
    """
    # Import the script to execute its main routine
    import importlib.util
    import sys

    script_path = Path(__file__).parents[2] / "code" / "check_requirements.py"
    spec = importlib.util.spec_from_file_location("check_requirements", script_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["check_requirements"] = module
    spec.loader.exec_module(module)  # runs the script

    # The script writes to results/requirements_check.txt
    output_path = paths.results("requirements_check.txt")
    assert output_path.is_file(), f"Expected output file {output_path} not found"

    content = output_path.read_text(encoding="utf-8")
    # Pip dry‑run prints a line like “Successfully installed …”
    assert re.search(r"Successfully installed", content, re.IGNORECASE), (
        "Pip dry‑run did not report successful installation"
    )