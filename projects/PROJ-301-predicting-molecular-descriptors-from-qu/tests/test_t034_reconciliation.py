"""
Test for Task T034: Reconcile run-book vs implementation for code/03_feature_extraction.py.

This test verifies:
1. code/03_feature_extraction.py exists.
2. docs/quickstart.md references code/03_feature_extraction.py.
3. The script can be imported without errors.
"""

import os
import subprocess
import pytest
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
CODE_DIR = PROJECT_ROOT / "code"
DOCS_DIR = PROJECT_ROOT / "docs"

def test_script_exists():
    """Verify that code/03_feature_extraction.py exists."""
    script_path = CODE_DIR / "03_feature_extraction.py"
    assert script_path.exists(), f"Script {script_path} does not exist"

def test_quickstart_references_script():
    """Verify that docs/quickstart.md references code/03_feature_extraction.py."""
    quickstart_path = DOCS_DIR / "quickstart.md"
    assert quickstart_path.exists(), f"Quickstart file {quickstart_path} does not exist"

    content = quickstart_path.read_text()
    assert "03_feature_extraction" in content, (
        f"docs/quickstart.md does not reference '03_feature_extraction'. "
        f"Please add the command 'python code/03_feature_extraction.py' to the quickstart guide."
    )

def test_script_imports_correctly():
    """Verify that code/03_feature_extraction.py can be imported without errors."""
    # Add project root to sys.path
    sys_path = str(PROJECT_ROOT)
    if sys_path not in __import__("sys").path:
        __import__("sys").path.insert(0, sys_path)

    try:
        # Attempt to import the module
        import code_03_feature_extraction
        assert hasattr(code_03_feature_extraction, "main"), (
            "code_03_feature_extraction.py must define a 'main' function"
        )
    except ImportError as e:
        pytest.fail(f"Failed to import code_03_feature_extraction.py: {e}")

def test_script_execution_entry_point():
    """Verify that the script has a valid entry point (sys.exit(main()))."""
    script_path = CODE_DIR / "03_feature_extraction.py"
    content = script_path.read_text()

    # Check for the standard entry point pattern
    assert 'if __name__ == "__main__":' in content, (
        "Script must have 'if __name__ == \"__main__\":' block"
    )
    assert "sys.exit(main())" in content or "main()" in content, (
        "Script must call main() in the entry point block"
    )

def test_grep_verification():
    """
    Run the exact verification command from the task description:
    grep -r "03_feature_extraction" docs/quickstart.md
    """
    quickstart_path = DOCS_DIR / "quickstart.md"
    if not quickstart_path.exists():
        pytest.fail("docs/quickstart.md not found")

    result = subprocess.run(
        ["grep", "-r", "03_feature_extraction", str(quickstart_path)],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True
    )

    assert result.returncode == 0, (
        f"grep command failed. Output: {result.stdout}, Error: {result.stderr}. "
        f"Ensure '03_feature_extraction' is mentioned in docs/quickstart.md."
    )

def test_ls_verification():
    """
    Run the exact verification command from the task description:
    ls code/03_feature_extraction.py
    """
    script_path = CODE_DIR / "03_feature_extraction.py"
    assert script_path.exists(), (
        f"Script {script_path} not found. Ensure code/03_feature_extraction.py exists."
    )