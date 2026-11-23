"""Unit tests for the linting/formatting configuration (Task T003)."""
import subprocess
import sys
from pathlib import Path
import tomllib
import unittest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PYPROJECT = PROJECT_ROOT / "pyproject.toml"
LINT_SCRIPT = PROJECT_ROOT / "scripts" / "lint.sh"


class TestLintConfig(unittest.TestCase):
    def test_pyproject_exists_and_is_valid_toml(self):
        self.assertTrue(PYPROJECT.is_file(), "pyproject.toml must exist")
        with open(PYPROJECT, "rb") as f:
            data = tomllib.load(f)
        self.assertIsInstance(data, dict)

    def test_ruff_config_present(self):
        with open(PYPROJECT, "rb") as f:
            data = tomllib.load(f)
        self.assertIn("tool", data)
        self.assertIn("ruff", data["tool"])
        ruff = data["tool"]["ruff"]
        self.assertEqual(ruff.get("target-version"), "py311")
        self.assertGreater(ruff.get("line-length", 0), 0)
        self.assertIn("lint", ruff)
        self.assertIn("select", ruff["lint"])
        self.assertIn("E", ruff["lint"]["select"])
        self.assertIn("F", ruff["lint"]["select"])

    def test_black_config_present(self):
        with open(PYPROJECT, "rb") as f:
            data = tomllib.load(f)
        self.assertIn("tool", data)
        self.assertIn("black", data["tool"])
        black = data["tool"]["black"]
        self.assertEqual(black.get("target-version"), ["py311"])
        self.assertGreater(black.get("line-length", 0), 0)

    def test_black_and_ruff_line_lengths_agree(self):
        with open(PYPROJECT, "rb") as f:
            data = tomllib.load(f)
        self.assertEqual(
            data["tool"]["ruff"]["line-length"],
            data["tool"]["black"]["line-length"],
        )

    def test_lint_script_exists_and_is_executable_content(self):
        self.assertTrue(LINT_SCRIPT.is_file(), "scripts/lint.sh must exist")
        content = LINT_SCRIPT.read_text(encoding="utf-8")
        self.assertIn("ruff", content)
        self.assertIn("black", content)
        self.assertIn("set -euo pipefail", content)

    def test_lint_script_is_valid_bash_syntax(self):
        result = subprocess.run(
            ["bash", "-n", str(LINT_SCRIPT)],
            capture_output=True,
            text=True,
        )
        self.assertEqual(
            result.returncode,
            0,
            f"lint.sh has invalid bash syntax: {result.stderr}",
        )


if __name__ == "__main__":
    unittest.main()
