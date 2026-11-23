"""Tests for the T001 project skeleton: directories, config, lint log."""

from llmxive_toolkit import paths

from code.config import BATCH_SIZE, FD_THRESHOLD, SEED, STEP_SEC, WINDOW_SEC


def test_required_directories_exist():
    for d in [
        "code",
        "data/raw",
        "data/processed",
        "data/results",
        "figures",
        "docs",
        "tests",
    ]:
        assert (paths.root / d).is_dir(), f"Missing directory: {d}"


def test_config_constants():
    assert SEED == 42
    assert WINDOW_SEC == 60
    assert STEP_SEC == 1
    assert FD_THRESHOLD == 0.2
    assert BATCH_SIZE == 20


def test_requirements_manifest_exists():
    req = paths.root / "requirements.txt"
    assert req.is_file()
    text = req.read_text(encoding="utf-8")
    for pkg in ["numpy", "pandas", "nibabel", "nilearn", "ruff"]:
        assert pkg in text, f"{pkg} missing from requirements.txt"


def test_ruff_log_reports_no_errors():
    log = paths.data("logs", "ruff.log")
    assert log.is_file(), "data/logs/ruff.log not found — run code/lint_setup.py"
    content = log.read_text(encoding="utf-8")
    assert "No errors" in content, f"Lint log does not confirm a clean run:\n{content}"