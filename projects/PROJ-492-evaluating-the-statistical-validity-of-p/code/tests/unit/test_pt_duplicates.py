"""
Unit test to ensure there are no duplicated PT### entries in the audit package.
The check_pt_duplicates script returns exit code 0 when no duplicates are found.
"""
import importlib

def test_no_pt_duplicates():
    """Import the duplicate‑check module and verify it exits cleanly."""
    module = importlib.import_module("code.src.audit.check_pt_duplicates")
    exit_code = module.main()
    assert exit_code == 0, f"PT duplicate check failed with exit code {exit_code}"