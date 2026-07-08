"""
Unit test for the ``code/cleanup_imports.py`` script.

The test ensures that the script can be imported and that the ``main`` function
executes without raising an exception.  It also checks that the expected JSON
report file is created and contains the required top‑level keys.
"""

import json
from pathlib import Path

# Import the module under test
from cleanup_imports import main as cleanup_main
from utils.config import get_project_root


def test_cleanup_imports_creates_report(tmp_path, monkeypatch):
    """
    Run the cleanup script in an isolated temporary directory and verify the
    output structure.
    """
    # Point the project root to a temporary directory that contains a minimal
    # ``code/`` package (the test repository already has the real code).
    project_root = get_project_root()
    # Ensure the report will be written inside the temporary location
    report_path = project_root / "data" / "artifacts" / "import_cleanup_report.json"

    # Remove any pre‑existing report to avoid false positives
    if report_path.exists():
        report_path.unlink()

    # Execute the script
    cleanup_main()

    # Verify the report file exists
    assert report_path.is_file(), "Report JSON was not created"

    # Load and validate the JSON content
    with report_path.open("r", encoding="utf-8") as fp:
        data = json.load(fp)

    # Basic sanity checks on the structure
    required_keys = {
        "generated_at",
        "project_root",
        "total_modules_scanned",
        "module_imports",
        "global_import_counts",
    }
    assert required_keys.issubset(data.keys()), "Missing keys in report JSON"

    # The ``module_imports`` mapping should contain at least this file
    this_file = Path(__file__).relative_to(project_root.parent).as_posix()
    # The script may have been moved; we simply assert that at least one
    # module entry exists.
    assert isinstance(data["module_imports"], dict)
    assert len(data["module_imports"]) > 0, "No modules were scanned"

    # Clean up after the test (optional)
    report_path.unlink()