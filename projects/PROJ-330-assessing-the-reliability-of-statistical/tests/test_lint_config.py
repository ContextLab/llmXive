"""Tests for T003: linting (flake8) and formatting (black) configuration."""

from pathlib import Path

CODE_DIR = Path(__file__).resolve().parents[1] / "code"


def test_flake8_config_exists():
    flake8_cfg = CODE_DIR / ".flake8"
    assert flake8_cfg.is_file(), f"Missing {flake8_cfg}"
    content = flake8_cfg.read_text()
    assert "[flake8]" in content
    assert "max-line-length" in content


def test_flake8_line_length_matches_black():
    flake8_cfg = (CODE_DIR / ".flake8").read_text()
    black_cfg = (CODE_DIR / "pyproject.toml").read_text()
    assert "max-line-length = 88" in flake8_cfg
    assert "line-length = 88" in black_cfg


def test_black_config_exists():
    pyproject = CODE_DIR / "pyproject.toml"
    assert pyproject.is_file(), f"Missing {pyproject}"
    content = pyproject.read_text()
    assert "[tool.black]" in content
    assert "py311" in content
