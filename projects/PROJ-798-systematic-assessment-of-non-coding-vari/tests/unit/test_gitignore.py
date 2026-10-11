"""Tests for the repository .gitignore exclusion patterns (T002)."""

import subprocess
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
GITIGNORE = PROJECT_ROOT / ".gitignore"

EXPECTED_PATTERNS = [
    "data/raw/*",
    "!data/raw/checksums.json",
    "!data/raw/source_log.txt",
    "data/derived/*",
    "__pycache__/",
    ".env",
]

def _check_ignore(path: str) -> int:
    """Return the exit code of `git check-ignore <path>` from the repo root."""
    result = subprocess.run(
        ["git", "check-ignore", "-q", path],
        cwd=str(PROJECT_ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return result.returncode

class TestGitignore(unittest.TestCase):
    def test_gitignore_exists(self):
        self.assertTrue(GITIGNORE.is_file(), ".gitignore missing at repo root")

    def test_gitignore_contains_required_patterns(self):
        content = GITIGNORE.read_text(encoding="utf-8")
        lines = [ln.strip() for ln in content.splitlines()]
        for pattern in EXPECTED_PATTERNS:
            self.assertIn(pattern, lines, f"missing pattern: {pattern}")

    def test_raw_data_files_are_ignored(self):
        for path in [
            "data/raw/snps_raw.vcf.gz",
            "data/raw/hg38.fa",
            "data/raw/jaspar_pwms.json",
        ]:
            self.assertEqual(
                _check_ignore(path),
                0,
                f"expected {path} to be ignored (exit 0)",
            )

    def test_whitelisted_files_are_not_ignored(self):
        for path in [
            "data/raw/checksums.json",
            "data/raw/source_log.txt",
        ]:
            self.assertEqual(
                _check_ignore(path),
                1,
                f"expected {path} NOT to be ignored (exit 1)",
            )

    def test_derived_and_cache_are_ignored(self):
        for path in [
            "data/derived/filtered_snps.parquet",
            "code/__pycache__/fetch_dbsnp.cpython-311.pyc",
            ".env",
        ]:
            self.assertEqual(
                _check_ignore(path),
                0,
                f"expected {path} to be ignored (exit 0)",
            )

if __name__ == "__main__":
    unittest.main()