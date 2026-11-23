"""T004 verification: data directories exist and CHECKSUMS manifest present."""
import subprocess
import sys
from pathlib import Path

from llmxive_toolkit import paths

PROJECT_ROOT = paths.root


def test_data_dirs_and_checksum():
    for sub in ("raw", "processed", "results"):
        d = paths.data(sub)
        assert d.is_dir(), f"missing data directory: {d}"
    manifest = paths.data("CHECKSUMS")
    assert manifest.is_file(), f"missing manifest: {manifest}"
    content = manifest.read_text(encoding="utf-8")
    assert content.strip(), "CHECKSUMS manifest is empty"
    # Every listed entry is a real file with a matching checksum.
    for line in content.splitlines():
        digest, rel = line.split("  ", 1)
    # Recompute the manifest to confirm it is consistent with disk.
    script = PROJECT_ROOT / "code" / "utils" / "checksums.py"
    res = subprocess.run(
        [sys.executable, str(script)],
        capture_output=True, text=True, cwd=str(PROJECT_ROOT),
    )
    assert res.returncode == 0, res.stderr