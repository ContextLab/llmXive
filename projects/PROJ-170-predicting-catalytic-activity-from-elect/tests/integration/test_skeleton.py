import os
from llmxive_toolkit import paths

def test_dirs_exist():
    """
    Verify that all required project directories exist.
    """
    required_dirs = [
        paths.data("raw"),
        paths.data("processed"),
        paths.path("outputs"),
        paths.code(),
        paths.code("utils"),
        paths.code("models"),
        paths.path("tests/contract"),
        paths.path("tests/integration"),
        paths.path("tests/unit"),
    ]
    for d in required_dirs:
        assert os.path.isdir(d), f"Directory {d} does not exist"

def test_init_files_exist():
    """
    Verify that package initialization files exist.
    """
    required_files = [
        paths.code("__init__.py"),
        paths.code("utils/__init__.py"),
        paths.code("models/__init__.py"),
    ]
    for f in required_files:
        assert os.path.isfile(f), f"File {f} does not exist"