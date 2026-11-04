"""
Cleanup script for task T001.

- Moves the legacy utility scripts (run_lint.py, run_quickstart_validation.py)
  from the top‑level ``code/`` directory into ``code/scripts/``.
- Deletes every orphaned ``t*.py`` experiment script that may remain in the
  repository after the migration.
- Ensures a ``code/scripts/`` directory exists.
- Updates ``.gitignore`` to exclude temporary ``t*.py`` files and common
  scratch/tmp patterns.
"""

import sys
from pathlib import Path

def _move_legacy_script(src: Path, dst_dir: Path):
    """Move a legacy script into the ``scripts`` folder if it exists."""
    if src.is_file():
        dst_dir.mkdir(parents=True, exist_ok=True)
        dst = dst_dir / src.name
        # ``Path.replace`` overwrites the destination atomically.
        src.replace(dst)

def _delete_t_scripts(root: Path):
    """Delete all ``t*.py`` files anywhere under the project root."""
    for path in root.rglob("t*.py"):
        try:
            path.unlink()
        except Exception as exc:
            print(f"Warning: could not delete {path}: {exc}", file=sys.stderr)

def _update_gitignore(root: Path):
    """Append hygiene patterns to ``.gitignore`` if they are missing."""
    gitignore = root / ".gitignore"
    patterns = [
        "t*.py",          # orphaned experiment scripts
        "*.scratch",      # temporary scratch files
        "*.tmp",          # generic temporary files
        "__pycache__/",   # compiled Python caches
    ]
    existing = set()
    if gitignore.is_file():
        existing = {line.strip() for line in gitignore.read_text().splitlines() if line.strip()}
    with gitignore.open("a") as fh:
        for pat in patterns:
            if pat not in existing:
                fh.write(pat + "\n")

def main():
    project_root = Path(__file__).resolve().parents[2]  # <project>/code/scripts/ -> <project>
    # 1. Move legacy utility scripts.
    legacy_dir = project_root / "code"
    scripts_dir = legacy_dir / "scripts"
    for script_name in ("run_lint.py", "run_quickstart_validation.py"):
        _move_legacy_script(legacy_dir / script_name, scripts_dir)

    # 2. Delete all orphaned t*.py experiment scripts.
    _delete_t_scripts(project_root)

    # 3. Ensure the ``code/scripts/`` directory exists (already handled by move).
    scripts_dir.mkdir(parents=True, exist_ok=True)

    # 4. Update .gitignore with hygiene patterns.
    _update_gitignore(project_root)

    print("Filesystem hygiene completed.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
