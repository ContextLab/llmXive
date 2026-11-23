"""Validation of linting/formatting configuration for T003.

Can be run standalone (``python code/tests/test_lint_config.py``) or via
pytest. Validates that the flake8 and black configuration files exist in
``code/`` and parse correctly.
"""

import configparser
import sys
import tomllib
from pathlib import Path

CODE_DIR = Path(__file__).resolve().parent.parent
FLAKE8_CONFIG = CODE_DIR / ".flake8"
PYPROJECT_CONFIG = CODE_DIR / "pyproject.toml"
LINT_SCRIPT = CODE_DIR / "lint.sh"


def test_flake8_config_exists_and_parses():
    assert FLAKE8_CONFIG.is_file(), f"missing {FLAKE8_CONFIG}"
    parser = configparser.ConfigParser()
    parser.read(FLAKE8_CONFIG)
    assert parser.has_section("flake8"), "flake8 config missing [flake8] section"
    assert parser.get("flake8", "max-line-length") == "100"
    excluded = parser.get("flake8", "exclude")
    assert "venv" in excluded and "__pycache__" in excluded


def test_black_config_exists_and_parses():
    assert PYPROJECT_CONFIG.is_file(), f"missing {PYPROJECT_CONFIG}"
    with open(PYPROJECT_CONFIG, "rb") as fh:
        data = tomllib.load(fh)
    tool = data.get("tool", {})
    assert "black" in tool, "pyproject.toml missing [tool.black] section"
    black_cfg = tool["black"]
    assert black_cfg.get("line-length") == 100
    assert black_cfg.get("target-version") == ["py311"]


def test_lint_script_exists():
    assert LINT_SCRIPT.is_file(), f"missing {LINT_SCRIPT}"
    text = LINT_SCRIPT.read_text()
    assert "set -euo pipefail" in text, "lint.sh must fail loudly (set -e)"
    assert "flake8" in text and "black" in text


def main():
    tests = [
        test_flake8_config_exists_and_parses,
        test_black_config_exists_and_parses,
        test_lint_script_exists,
    ]
    failures = 0
    for test in tests:
        try:
            test()
            print(f"PASS: {test.__name__}")
        except AssertionError as exc:
            failures += 1
            print(f"FAIL: {test.__name__}: {exc}", file=sys.stderr)
    if failures:
        print(f"{failures} lint-config check(s) failed", file=sys.stderr)
        sys.exit(1)
    print("All lint configuration checks passed.")


if __name__ == "__main__":
    main()