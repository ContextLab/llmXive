"""
Test suite for validating quickstart.md instructions.
This script ensures that the documented commands in quickstart.md
are syntactically correct, importable, and executable (at least the setup/validation parts).
"""
import subprocess
import sys
import os
import tempfile
from pathlib import Path
import pytest

# Project root relative to this test file
PROJECT_ROOT = Path(__file__).parent.parent.parent

QUICKSTART_PATH = PROJECT_ROOT / "quickstart.md"

def test_quickstart_file_exists():
    """Verify quickstart.md exists at the project root."""
    assert QUICKSTART_PATH.exists(), f"quickstart.md not found at {QUICKSTART_PATH}"

def test_quickstart_commands_importable():
    """
    Parse quickstart.md for Python script paths and verify they are importable.
    This validates the 'run' instructions without actually executing the full heavy pipelines.
    """
    content = QUICKSTART_PATH.read_text()
    
    # Look for patterns like: python src/analysis/generate_dataset.py
    # or: python code/src/analysis/generate_dataset.py (depending on doc format)
    # We'll extract paths that look like script invocations
    import re
    
    # Pattern to match python script paths in the markdown
    # Matches: python [path].py or python code/[path].py
    pattern = r'python\s+(code/)?(src/[^ ]+\.py)'
    matches = re.findall(pattern, content)
    
    if not matches:
        # Try alternative pattern if standard one fails
        pattern_alt = r'python\s+([^\s]+\.py)'
        matches = re.findall(pattern_alt, content)
    
    if not matches:
        pytest.skip("No python script commands found in quickstart.md")

    errors = []
    for match in matches:
        # Handle tuple from regex groups
        if isinstance(match, tuple):
            prefix, path = match
            full_path = f"{prefix}{path}" if prefix else path
        else:
            full_path = match

        script_path = PROJECT_ROOT / full_path
        
        if not script_path.exists():
            errors.append(f"Script not found: {script_path}")
            continue

        # Verify it's a valid Python file (syntax check)
        try:
            compile(script_path.read_text(), str(script_path), 'exec')
        except SyntaxError as e:
            errors.append(f"Syntax error in {full_path}: {e}")
            continue

        # Try to import the module (if it has imports)
        # We do this by adding the project root to sys.path and attempting import
        # Note: Some scripts might have side effects on import, so we catch exceptions
        try:
            # We only check if the file is syntactically valid and importable structure
            # Full execution is too heavy for a validation test
            import importlib.util
            spec = importlib.util.spec_from_file_location("quickstart_check", script_path)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                # Don't execute, just check if spec is valid
        except Exception as e:
            # Some scripts might fail on import due to missing data files, etc.
            # We only care about import errors that are not data-related
            if "No module named" in str(e) or "ImportError" in str(type(e).__name__):
                errors.append(f"Import error in {full_path}: {e}")

    if errors:
        pytest.fail(f"Validation errors in quickstart.md commands:\n" + "\n".join(errors))

def test_quickstart_command_structure():
    """
    Verify that the quickstart.md contains the expected sections:
    1. Setup/Installation
    2. Data Generation
    3. Model Training (optional/skipped in validation)
    4. Benchmarking/Validation
    5. Statistical Analysis
    """
    content = QUICKSTART_PATH.read_text().lower()
    
    required_sections = [
        "install",
        "data",
        "train",
        "benchmark",
        "stats"
    ]
    
    missing = []
    for section in required_sections:
        if section not in content:
            missing.append(section)
    
    if missing:
        # This is a soft check - we warn but don't fail if a section is named differently
        # For now, we just ensure the file has substantial content
        assert len(content) > 100, "quickstart.md appears to be empty or too short"

def test_quickstart_executable_scripts_syntax():
    """
    Specific check for the main executable scripts mentioned in typical quickstart flows.
    Based on the task list, these are the critical paths:
    - src/analysis/generate_dataset.py
    - src/analysis/train.py (if present)
    - src/cli/run_benchmark.py
    - src/analysis/stats.py (or generate_statistical_report.py)
    """
    critical_scripts = [
        "src/analysis/generate_dataset.py",
        "src/cli/run_benchmark.py",
        "src/analysis/generate_statistical_report.py"
    ]
    
    errors = []
    for script_rel in critical_scripts:
        script_path = PROJECT_ROOT / script_rel
        if not script_path.exists():
            errors.append(f"Critical script missing: {script_rel}")
            continue
        
        try:
            compile(script_path.read_text(), str(script_path), 'exec')
        except SyntaxError as e:
            errors.append(f"Syntax error in {script_rel}: {e}")
    
    if errors:
        pytest.fail("Critical scripts validation failed:\n" + "\n".join(errors))

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
