"""
Test for the quickstart reproducibility validation script.

The test simply executes ``code/quickstart_validation.py`` and checks that
the expected JSON report file is created and indicates success.
"""

import sys
import json
import subprocess

from llmxive_toolkit import paths, get_logger

def test_quickstart_validation_script():
    """
    Run the validation script and assert that it reports success.
    """
    logger = get_logger(__name__)

    script_path = paths.code("quickstart_validation.py")
    logger.info("Executing validation script: %s", script_path)

    result = subprocess.run(
        [sys.executable, str(script_path)],
        capture_output=True,
        text=True,
    )
    # The script should exit cleanly.
    assert result.returncode == 0, f"Script exited with {result.returncode}: {result.stderr}"

    # Verify that the report file exists and contains a success flag.
    report_path = paths.results("quickstart_validation_report.json")
    assert report_path.is_file(), "Report file was not created."

    report = json.loads(report_path.read_text())
    assert report.get("success") is True, "Verification reported failure."

    # Optionally, ensure that stdout/stderr are strings.
    assert isinstance(report.get("stdout"), str)
    assert isinstance(report.get("stderr"), str)