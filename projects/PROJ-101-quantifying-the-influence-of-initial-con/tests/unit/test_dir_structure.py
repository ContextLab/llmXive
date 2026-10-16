"""
Unit test that verifies the directory‑structure script creates the expected
layout and writes ``data/dir_structure.txt`` containing all required entries.
The test imports and runs the script directly, then checks the file contents.
"""

import importlib.util
from pathlib import Path


def _load_and_run_script() -> Path:
    """
    Load ``code/create_dir_structure.py`` as a module and execute its ``main``
    function. Returns the path to the generated ``dir_structure.txt`` file.
    """
    script_path = Path(__file__).resolve().parents[2] / "code" / "create_dir_structure.py"
    spec = importlib.util.spec_from_file_location("create_dir_structure", script_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None, "Failed to locate loader for script"
    spec.loader.exec_module(module)
    # Run the script's entry point
    module.main()
    # Path to the output file (project‑owned location)
    return Path(__file__).resolve().parents[2] / "data" / "dir_structure.txt"


def test_dir_structure_file_created_and_correct() -> None:
    """
    The test ensures:
    1. ``dir_structure.txt`` exists after the script runs.
    2. Its contents include each of the nine required directories.
    """
    out_path = _load_and_run_script()
    assert out_path.is_file(), f"Expected file {out_path} to exist"

    content = out_path.read_text().splitlines()
    # Normalise lines (strip trailing spaces)
    content = [line.strip() for line in content if line.strip()]

    required = [
        "code",
        "code/simulation",
        "code/analysis",
        "code/utils",
        "tests/unit",
        "tests/integration",
        "data/raw",
        "data/processed",
        "state",
    ]

    for req in required:
        # Each top‑level directory should appear as a line in the file
        assert any(line == req or line.startswith(f"{req}/") for line in content), (
            f"Directory '{req}' not found in dir_structure.txt"
        )