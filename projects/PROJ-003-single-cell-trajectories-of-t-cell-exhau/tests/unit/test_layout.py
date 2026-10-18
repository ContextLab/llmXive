"""T001 verification: required layout, placeholder file, quickstart command."""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def test_data_results_placeholder_exists():
    gitkeep = PROJECT_ROOT / "data" / "results" / ".gitkeep"
    assert gitkeep.is_file(), "data/results/.gitkeep placeholder is missing"


def test_required_directories_exist():
    for sub in (
        "data/raw",
        "data/processed",
        "data/results/fork_points",
        "data/results/validation",
        "data/results/report",
        "logs",
    ):
        assert (PROJECT_ROOT / sub).is_dir(), f"missing directory: {sub}"


def test_quickstart_documents_run_all_command():
    quickstart = PROJECT_ROOT / "quickstart.md"
    assert quickstart.is_file(), "quickstart.md is missing"
    text = quickstart.read_text()
    assert "python -m code.run_all" in text
    assert "Usage example" in text or "usage example" in text.lower()


def test_lint_evidence_written():
    lint_log = PROJECT_ROOT / "logs" / "lint.txt"
    assert lint_log.is_file(), "logs/lint.txt is missing"
    text = lint_log.read_text()
    assert "ruff exit code: 0" in text
    assert "black exit code: 0" in text
