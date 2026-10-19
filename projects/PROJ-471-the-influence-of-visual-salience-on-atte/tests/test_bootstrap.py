"""
Unit test for the bootstrap script (T001).

The test runs the bootstrap entry point and then checks that:
* All required directories exist, including the top-level ``logs/``
  directory required by the task description.
* ``requirements.txt`` exists (both at the project root and mirrored
  in ``code/``) and contains the pinned dependency list.
"""
import importlib
from pathlib import Path

from llmxive_toolkit import paths

# Import the bootstrap module without executing the script's __main__ block
bootstrap = importlib.import_module("code.bootstrap")

EXPECTED_REQUIREMENTS = [
    "python==3.11",
    "torch==2.2.0",
    "statsmodels>=0.14.0",
    "ultralytics>=8.0.0",
    "detectron2>=0.7",
    "pandas>=2.2.0",
    "numpy>=1.26.0",
    "scikit-image>=0.22.0",
    "scikit-learn>=1.3.0",
    "pingouin>=0.5.4",
    "opencv-python>=4.8.0",
]

def test_bootstrap_creates_layout_and_requirements(tmp_path, monkeypatch):
    """
    Run the bootstrap ``main`` function and verify side-effects.
    """
    # Monkey-patch the llmxive_toolkit.paths helpers to point inside the
    # temp dir so the test does not touch the real project tree.
    monkeypatch.setattr(paths, "root", Path(tmp_path))
    monkeypatch.setattr(paths, "code", lambda *parts: Path(tmp_path, "code", *parts))
    monkeypatch.setattr(paths, "data", lambda *parts: Path(tmp_path, "data", *parts))
    monkeypatch.setattr(paths, "docs", lambda *parts: Path(tmp_path, "docs", *parts))

    # Run bootstrap
    rc = bootstrap.main()
    assert rc == 0, "bootstrap main() must return exit code 0"

    # Expected directories
    expected_dirs = [
        paths.code(),
        paths.data("raw"),
        paths.data("interim"),
        paths.data("processed"),
        paths.data("results"),
        paths.root / "logs",   # top-level logs/ required by T001
        paths.code("tests"),
        paths.docs(),
    ]

    for d in expected_dirs:
        assert d.is_dir(), f"Expected directory {d} to exist after bootstrap"

    # Check requirements.txt at the project root
    req_path = paths.root / "requirements.txt"
    assert req_path.is_file(), "requirements.txt should be created at the project root"

    content = req_path.read_text()
    for line in EXPECTED_REQUIREMENTS:
        assert line in content, f"Pinned dependency missing from requirements.txt: {line}"

    # Mirrored copy inside code/
    code_req = paths.code("requirements.txt")
    assert code_req.is_file(), "code/requirements.txt mirror should exist"
    assert code_req.read_text() == content, "code/requirements.txt must match the root file"