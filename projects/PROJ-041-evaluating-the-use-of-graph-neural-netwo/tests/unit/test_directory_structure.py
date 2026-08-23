import os
import pytest

def test_required_directories_exist():
    """Verify that all required project directories exist."""
    required_dirs = [
        "code/data",
        "code/models",
        "code/analysis",
        "code/utils",
        "data/raw",
        "data/processed",
        "data/results",
        "tests",
        "tests/integration",
        "tests/unit",
    ]

    for d in required_dirs:
        assert os.path.isdir(d), f"Directory {d} does not exist"

def test_create_directories_script_runs():
    """Verify the create_directories script runs without error."""
    from code.scripts.create_directories import main
    # This should not raise an exception
    main()