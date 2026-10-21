"""T002 verification: requirements.txt exists with exact pins and
run_pipeline.sh exists and is executable."""
import os
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def test_requirements_present():
    req = PROJECT_ROOT / "requirements.txt"
    assert req.is_file(), f"requirements.txt missing at {req}"
    content = req.read_text(encoding="utf-8")
    assert content.strip(), "requirements.txt is empty"
    # Every non-comment, non-empty line must be an exact pin (==).
    dep_lines = [
        line.strip()
        for line in content.splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]
    assert dep_lines, "requirements.txt contains no dependencies"
    pin_re = re.compile(r"^[A-Za-z0-9_.\-]+==[0-9][^\s]*$")
    unpinned = [l for l in dep_lines if not pin_re.match(l)]
    assert not unpinned, f"Unpinned dependencies found: {unpinned}"

def test_run_pipeline_executable():
    script = PROJECT_ROOT / "run_pipeline.sh"
    assert script.is_file(), f"run_pipeline.sh missing at {script}"
    assert os.access(script, os.X_OK), "run_pipeline.sh is not executable"
    shebang = script.read_text(encoding="utf-8").splitlines()[0]
    assert shebang.startswith("#!"), "run_pipeline.sh lacks a shebang"