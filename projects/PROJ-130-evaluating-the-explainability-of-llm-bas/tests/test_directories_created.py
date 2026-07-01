import os
import pytest

def test_required_directories_exist():
    """Verify that the project structure directories exist after setup."""
    required_dirs = [
        "data",
        "data/defects4j",
        "code",
        "code/utils",
        "code/models",
        "explanations",
        "state",
        "tests",
    ]

    missing = []
    for d in required_dirs:
        if not os.path.exists(d):
            missing.append(d)

    assert not missing, f"The following required directories are missing: {missing}"