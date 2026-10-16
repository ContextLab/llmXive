"""T001: verify the project directory skeleton exists."""
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def test_required_directories_exist():
    for rel in [
        "code",
        "data/raw",
        "data/processed",
        "data/results",
        "tests",
    ]:
        assert (PROJECT_ROOT / rel).is_dir(), f"missing directory: {rel}"


def test_code_init_exists():
    init = PROJECT_ROOT / "code" / "__init__.py"
    assert init.is_file()
    assert init.stat().st_size > 0


def test_gitignore_exists():
    gi = PROJECT_ROOT / ".gitignore"
    assert gi.is_file()
    content = gi.read_text()
    assert "__pycache__/" in content
    assert "venv/" in content