"""T003: verify package boilerplate imports cleanly."""
import importlib
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def test_import_code_package():
    # Ensure the project root is on sys.path so `import code`
    # resolves to the project package (not the stdlib module).
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))
    mod = importlib.import_module("code")
    assert mod is not None
    assert mod.__version__ == "0.1.0"


def test_import_tests_package():
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))
    tests = importlib.import_module("tests")
    assert tests is not None
