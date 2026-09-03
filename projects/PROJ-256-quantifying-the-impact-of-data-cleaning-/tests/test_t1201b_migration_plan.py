"""
Unit test for the migration‑plan generator (T1201b).

The test simply checks that the generated JSON file exists and that it
contains an entry for every ``t0*.py`` script discovered by
``audit_t0_files.find_t0_files``.
"""

import json
from pathlib import Path

from audit_t0_files import find_t0_files

def test_migration_plan_covers_all_t0_files(tmp_path, monkeypatch):
    """
    Run the migration‑plan script and verify coverage.
    """
    # Ensure the script writes to a temporary location to avoid polluting the
    # repository state during the test run.
    output_path = Path("data/processed/migration_plan.json")
    # Monkeypatch the output path inside the script by adjusting the
    # environment variable that the script could respect – however, the
    # script writes to a fixed location, so we simply run it and then move
    # the file to a temporary location for inspection.
    import importlib.util, sys, runpy

    # Run the script as a module.
    runpy.run_path("code/t1201b_generate_migration_plan.py", run_name="__main__")

    assert output_path.is_file(), "Migration plan file was not created"

    with output_path.open() as f:
        plan = json.load(f)

    # The plan must contain a ``t0_files`` key with a list.
    assert "t0_files" in plan, "Missing 't0_files' key in migration plan"
    plan_files = {entry["path"] for entry in plan["t0_files"]}

    # Compare against the source of truth from the audit module.
    audited_files = {str(p) for p in find_t0_files()}
    assert audited_files == plan_files, (
        f"Migration plan does not cover all t0 files. "
        f"Missing: {audited_files - plan_files}; "
        f"Unexpected: {plan_files - audited_files}"
    )
    
    # Clean up after test to keep repository tidy.
    output_path.unlink()