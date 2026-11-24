"""
test_audit_imports.py

Simple import sanity test for the audit package.
Ensures that all top‑level modules can be imported without errors,
satisfying the “ensure all imports work” part of T001.
"""
import importlib
import sys
from pathlib import Path

# List of modules that should be importable from the audit package
MODULES = [
    "code.src.audit.curate_corpus",
    "code.src.audit.fetcher",
    "code.src.audit.ingestor",
    "code.src.audit.run_audit",
    "code.src.audit.provenance_archiver",
    "code.src.audit.bias_adjustment",
    # Add any additional core modules here as they become available
]

def test_imports():
    """
    Attempt to import each module; the test fails if any ImportError occurs.
    """
    for module_name in MODULES:
        try:
            importlib.import_module(module_name)
        except Exception as exc:
            # Provide a clear message for debugging
            raise AssertionError(f"Failed to import {module_name}: {exc}") from exc

if __name__ == "__main__":
    # Allow running the test directly without pytest
    try:
        test_imports()
        print("All audit modules imported successfully.")
    except AssertionError as e:
        sys.exit(str(e))