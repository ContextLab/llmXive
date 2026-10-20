"""
Unit test for the bootstrap script (T001).
"""
import importlib
from pathlib import Path
from llmxive_toolkit import paths

# Import the bootstrap module
bootstrap = importlib.import_module("code.bootstrap")

EXPECTED_REQUIREMENTS = [
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
    Run the bootstrap main() and verify the resulting filesystem state.
    """
    # Patch paths to use a temporary directory
    monkeypatch.setattr(paths, "root", Path(tmp_path))
    monkeypatch.setattr(paths, "code", lambda *parts: Path(tmp_path, "code", *parts))
    monkeypatch.setattr(paths, "data", lambda *parts: Path(tmp_path, "data", *parts))
    monkeypatch.setattr(paths, "docs", lambda *parts: Path(tmp_path, "docs", *parts))

    # Execute bootstrap
    rc = bootstrap.main()
    assert rc == 0, "bootstrap.main() should return 0"

    # Verify directories
    expected_dirs = [
        Path(tmp_path, "code"),
        Path(tmp_path, "data", "raw"),
        Path(tmp_path, "data", "interim"),
        Path(tmp_path, "data", "processed"),
        Path(tmp_path, "logs"),
        Path(tmp_path, "code", "tests"),
        Path(tmp_path, "docs"),
    ]
    for d in expected_dirs:
        assert d.is_dir(), f"Missing required directory: {d}"

    # Verify requirements.txt
    req_path = Path(tmp_path, "requirements.txt")
    assert req_path.is_file(), "requirements.txt missing at root"
    content = req_path.read_text()
    for req in EXPECTED_REQUIREMENTS:
        assert req in content, f"Requirement {req} missing from requirements.txt"

    # Verify quickstart.md
    qs_path = Path(tmp_path, "quickstart.md")
    assert qs_path.is_file(), "quickstart.md missing"
    qs_content = qs_path.read_text()
    assert "python -m code.main --stage smoke" in qs_content, "Entry point command missing in quickstart.md"