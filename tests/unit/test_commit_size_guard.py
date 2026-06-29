"""The commit-and-push CI helper must DROP any file >95MB before committing.

GitHub's pre-receive hook hard-rejects files >100MB, which fails the ENTIRE push
and loses the advance worker's whole tick (observed live: a 260MB pii_findings.csv
+ a 221MB raw CSV declined the push). Real git, real bare origin, end-to-end.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "ci" / "commit-and-push.sh"


def _git(args: list[str], cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)


def test_oversized_file_dropped_small_result_pushed(tmp_path: Path) -> None:
    origin = tmp_path / "origin.git"
    work = tmp_path / "work"
    subprocess.run(["git", "init", "--bare", "-q", str(origin)], check=True)
    subprocess.run(["git", "clone", "-q", str(origin), str(work)], check=True)
    _git(["config", "user.email", "t@t.t"], work)
    _git(["config", "user.name", "t"], work)
    # seed origin/main
    (work / "README.md").write_text("seed\n")
    _git(["add", "-A"], work)
    _git(["commit", "-qm", "seed"], work)
    _git(["branch", "-M", "main"], work)
    _git(["push", "-q", "origin", "main"], work)

    # a small real result + an oversized regenerable data artifact
    (work / "small_result.md").write_text("real analysis result\n")
    (work / "big.csv").write_bytes(b"\0" * (100 * 1024 * 1024))  # 100MiB > 95MB

    r = subprocess.run(["bash", str(SCRIPT), "test: tick"],
                       cwd=work, capture_output=True, text=True)
    assert r.returncode == 0, f"push should succeed; stderr:\n{r.stderr}"

    files = _git(["ls-tree", "-r", "--name-only", "origin/main"], work).stdout
    assert "small_result.md" in files, files       # the real result is persisted
    assert "big.csv" not in files, files           # the oversized blob is dropped
    assert "SKIP oversized" in r.stderr             # and the skip is logged, never silent
