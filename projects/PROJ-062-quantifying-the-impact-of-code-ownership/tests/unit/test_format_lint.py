"""
Unit tests for the format and lint script logic.
Verifies that the script structure is valid and imports correctly.
"""
import sys
from pathlib import Path

# Add project root to path to allow imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

def test_import_format_lint():
    """Test that the format_and_lint module can be imported."""
    try:
        from scripts.format_and_lint import run_command, main
        assert callable(run_command)
        assert callable(main)
    except ImportError as e:
        raise AssertionError(f"Failed to import scripts.format_and_lint: {e}")

def test_run_command_logic():
    """Test the run_command helper with a simple echo command."""
    from scripts.format_and_lint import run_command
    
    # Test a successful command
    success = run_command([sys.executable, "-c", "print('hello')"], "Test Echo")
    assert success is True

    # Test a failing command
    success = run_command([sys.executable, "-c", "raise SystemExit(1)"], "Test Fail")
    assert success is False
