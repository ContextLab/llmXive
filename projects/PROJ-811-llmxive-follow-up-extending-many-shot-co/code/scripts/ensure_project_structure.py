"""
Ensure the on-disk project structure matches the "Project Structure" section
of plan.md for projects/PROJ-811-llmxive-follow-up-extending-many-shot-co/.

Actions (idempotent):
1. Create the required directory tree:
   data/raw, data/processed, data/results, artifacts,
   code/src, code/tests (with .gitkeep markers so empty dirs persist).
2. Relocate a stray repository-root `tests/` directory into `code/tests/`
   (plan.md requires tests under code/tests/).
3. Remove project-owned extra top-level entries that are NOT part of the
   plan.md tree and duplicate existing canonical artifacts:
   - root-level `requirements.txt` (canonical manifest is code/requirements.txt)
   - root-level `pyproject.toml` (packaging lives in code/setup.py)
   - `config/`, `docs/`, `figures/`, `idea/` directories (not in plan tree)
Platform/runtime state (`.runtime-home/`, `.specify/`, `specs/`) and the
canonical `code/`, `data/`, `artifacts/` trees are never touched destructively.
"""
import logging
import shutil
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Project root: this file lives at <root>/code/scripts/ensure_project_structure.py
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Directories required by plan.md "Project Structure"
REQUIRED_DIRS = [
    "data/raw",
    "data/processed",
    "data/results",
    "artifacts",
    "code/src",
    "code/tests",
]

# Project-owned extras not in the plan.md tree (removed only when present).
EXTRA_TOP_LEVEL = ["config", "docs", "figures", "idea"]


def ensure_dirs() -> None:
    """Create every required directory from plan.md, with .gitkeep markers."""
    for rel in REQUIRED_DIRS:
        d = PROJECT_ROOT / rel
        d.mkdir(parents=True, exist_ok=True)
        keep = d / ".gitkeep"
        if not any(p for p in d.iterdir() if p.name != ".gitkeep"):
            keep.touch(exist_ok=True)
        logger.info(f"Ensured directory: {d.relative_to(PROJECT_ROOT)}")


def relocate_root_tests() -> None:
    """Move a stray root-level tests/ directory into code/tests/."""
    root_tests = PROJECT_ROOT / "tests"
    code_tests = PROJECT_ROOT / "code" / "tests"
    if not root_tests.is_dir():
        logger.info("No stray root-level tests/ directory found.")
        return

    code_tests.mkdir(parents=True, exist_ok=True)
    for item in sorted(root_tests.iterdir()):
        dest = code_tests / item.name
        if dest.exists():
            logger.warning(
                f"Skipping {item.name}: already exists in code/tests/."
            )
            continue
        shutil.move(str(item), str(dest))
        logger.info(
            f"Moved {item.name} -> code/tests/{item.name}"
        )
    # Remove the now-empty root tests dir (and any leftover empty subdirs)
    for sub in sorted(root_tests.rglob("*"), reverse=True):
        if sub.is_dir() and not any(sub.iterdir()):
            sub.rmdir()
    if not any(root_tests.iterdir()):
        root_tests.rmdir()
        logger.info("Removed empty root-level tests/ directory.")
    else:
        logger.warning(
            "Root tests/ directory not empty after relocation; left in place."
        )


def remove_duplicate_manifests() -> None:
    """Remove root-level requirements.txt / pyproject.toml duplicates.

    The canonical dependency manifest is code/requirements.txt (T002) and
    packaging lives in code/setup.py; a root-level copy is a competing
    manifest and is not part of the plan.md tree.
    """
    canonical_req = PROJECT_ROOT / "code" / "requirements.txt"
    for name in ("requirements.txt", "pyproject.toml"):
        target = PROJECT_ROOT / name
        if not target.exists():
            continue
        if name == "requirements.txt" and not canonical_req.exists():
            logger.warning(
                "code/requirements.txt missing; keeping root requirements.txt."
            )
            continue
        target.unlink()
        logger.info(f"Removed duplicate root-level {name}.")


def remove_extra_dirs() -> None:
    """Remove project-owned top-level directories not in the plan.md tree."""
    for name in EXTRA_TOP_LEVEL:
        target = PROJECT_ROOT / name
        if target.is_dir():
            shutil.rmtree(target)
            logger.info(f"Removed extra top-level directory: {name}/")


def verify() -> bool:
    """Verify the plan.md tree now exists on disk."""
    ok = True
    for rel in REQUIRED_DIRS:
        if not (PROJECT_ROOT / rel).is_dir():
            logger.error(f"MISSING required directory: {rel}")
            ok = False
    if (PROJECT_ROOT / "tests").is_dir():
        logger.error("Root-level tests/ still present.")
        ok = False
    for name in ("requirements.txt", "pyproject.toml"):
        if (PROJECT_ROOT / name).exists():
            logger.error(f"Root-level {name} still present.")
            ok = False
    for name in EXTRA_TOP_LEVEL:
        if (PROJECT_ROOT / name).is_dir():
            logger.error(f"Extra directory {name}/ still present.")
            ok = False
    return ok


def main() -> int:
    logger.info(f"Project root: {PROJECT_ROOT}")
    ensure_dirs()
    relocate_root_tests()
    remove_duplicate_manifests()
    remove_extra_dirs()
    if verify():
        logger.info("Project structure matches plan.md. OK")
        return 0
    logger.error("Project structure verification FAILED.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
