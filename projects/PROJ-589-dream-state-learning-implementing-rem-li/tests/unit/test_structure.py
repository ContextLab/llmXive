"""
Unit tests to verify the project directory structure has been created correctly.
"""
import os
import pytest

# Define expected directories relative to project root
EXPECTED_DIRS = [
    "code",
    "code/models",
    "code/data",
    "code/utils",
    "code/eval",
    "code/scripts",
    "tests",
    "tests/unit",
    "tests/integration",
    "tests/contract",
    "data",
    "data/raw",
    "data/checkpoints",
    "data/results",
    "data/logs",
]

@pytest.fixture
def project_root():
    # Assume tests are run from the project root or we derive it
    # If running from tests/unit, go up two levels
    current = os.path.dirname(os.path.abspath(__file__))
    # Heuristic: look for 'code' folder to find root
    while current != os.path.dirname(current):
        if os.path.isdir(os.path.join(current, "code")) and \
           os.path.isdir(os.path.join(current, "tests")) and \
           os.path.isdir(os.path.join(current, "data")):
            return current
        current = os.path.dirname(current)
    # Fallback: assume cwd is root
    return os.getcwd()

def test_all_directories_exist(project_root):
    """Verify all required directories exist."""
    missing = []
    for dir_name in EXPECTED_DIRS:
        full_path = os.path.join(project_root, dir_name)
        if not os.path.isdir(full_path):
            missing.append(dir_name)

    if missing:
        pytest.fail(f"The following directories are missing: {', '.join(missing)}")

def test_data_subdirectories_exist(project_root):
    """Verify specific data subdirectories exist."""
    required_data_dirs = [
        "data/raw",
        "data/checkpoints",
        "data/results",
        "data/logs"
    ]
    missing = []
    for dir_name in required_data_dirs:
        full_path = os.path.join(project_root, dir_name)
        if not os.path.isdir(full_path):
            missing.append(dir_name)

    if missing:
        pytest.fail(f"Missing data subdirectories: {', '.join(missing)}")