"""
Unit test for the deterministic synthetic base generator.

The test runs the ``generate_base.py`` script with a fixed seed and
verifies that:
  * The script exits with status code 0.
  * The output CSV exists.
  * It contains exactly 20 rows (excluding the header).
  * The column names are exactly ``study_id, effect, se, n``.
"""
import subprocess
import sys
from pathlib import Path

import pytest

@pytest.mark.timeout(60)
def test_generate_base(tmp_path, monkeypatch):
    # Ensure the repository root is on the import path.
    repo_root = Path(__file__).resolve().parents[2]
    monkeypatch.syspath_prepend(str(repo_root))

    out_file = tmp_path / "base_template.csv"
    result = subprocess.run(
        [sys.executable, "code/scripts/generate_base.py",
         "--seed", "42",
         "--out", str(out_file)],
        cwd=repo_root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    assert result.returncode == 0, f"Script failed: {result.stderr}"
    assert out_file.is_file(), "Output CSV was not created"

    # Verify CSV structure.
    with out_file.open("r", encoding="utf-8") as f:
        lines = f.readlines()
    header = lines[0].strip()
    assert header == "study_id,effect,se,n", "Incorrect CSV header"
    assert len(lines) == 21, "CSV should contain 20 data rows + header"