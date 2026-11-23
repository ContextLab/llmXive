"""Ensure run_pipeline.sh carries the executable bit (T002).

The platform materializes file contents without preserving POSIX modes,
so this small setup script restores the executable permission on the
orchestration script. Idempotent; exits non-zero if the target is missing.
"""
import stat
import sys
from pathlib import Path


def main() -> int:
    project_root = Path(__file__).resolve().parents[2]
    script = project_root / "run_pipeline.sh"
    if not script.is_file():
        print(f"ERROR: {script} not found", file=sys.stderr)
        return 1
    mode = script.stat().st_mode
    new_mode = mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH
    if new_mode != mode:
        script.chmod(new_mode)
        print(f"Set executable bit on {script}")
    else:
        print(f"{script} is already executable")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
