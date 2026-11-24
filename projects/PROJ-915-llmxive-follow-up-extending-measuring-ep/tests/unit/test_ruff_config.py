"""Unit tests for the ruff lint configuration (T003a)."""

import tomllib
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RUFF_CONFIG = PROJECT_ROOT / "code" / ".ruff.toml"


class TestRuffConfig(unittest.TestCase):
    """Confirm the expected settings in code/.ruff.toml."""

    def setUp(self) -> None:
        self.assertTrue(RUFF_CONFIG.exists(), f"Missing {RUFF_CONFIG}")
        with open(RUFF_CONFIG, "rb") as f:
            self.config = tomllib.load(f)

    def test_max_line_length_is_100(self) -> None:
        self.assertEqual(self.config["line-length"], 100)

    def test_target_version_py311(self) -> None:
        self.assertEqual(self.config["target-version"], "py311")

    def test_flake8_annotations_enabled(self) -> None:
        self.assertIn("ANN", self.config["lint"]["select"])

    def test_init_py_ignored(self) -> None:
        per_file = self.config["lint"]["per-file-ignores"]
        self.assertIn("__init__.py", per_file)
        self.assertIn("ALL", per_file["__init__.py"])

    def test_core_rule_sets_selected(self) -> None:
        select = self.config["lint"]["select"]
        for rule in ("E", "W", "F", "I", "ANN"):
            self.assertIn(rule, select)


if __name__ == "__main__":
    unittest.main()