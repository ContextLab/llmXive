"""Create the project directory skeleton for PROJ-756.

Creates project-owned directories (data/, code/, tests/, artifacts/,
results/, logs/) with placeholder files (__init__.py, .gitkeep, run.sh).
This version deliberately does NOT create a project-local state/ directory:
state/ is platform-owned and the platform derives artifact hashes at
verification time, so a project-local copy would be a rejected shadow.
Any stale project-local state/ shadow from a previous run is removed.
"""

import shutil
import sys
from pathlib import Path

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

PROJECT_NAME = "PROJ-756-assessing-dataset-imbalance-effects-on-m"

DIRECTORIES = [
    "data/raw",
    "data/processed",
    "data/synthetic",
    "code",
    "tests",
    "tests/unit",
    "tests/contract",
    "tests/integration",
    "artifacts",
    "results",
    "logs",
]

RUN_SH = "\n".join(
    [
        "#!/usr/bin/env bash",
        "# Placeholder runner for the PROJ-756 imbalance-effects pipeline.",
        "# The full pipeline entry point is: python -m code.main --full-pipeline",
        "set -e",
        'echo "PROJ-756 skeleton created. Run: python -m code.main --full-pipeline"',
        "",
    ]
)


def main() -> None:
    root = paths.root
    log.info("Project root: %s", root)

    # Remove any platform-owned shadow directory created by earlier runs.
    shadow_state = root / "state"
    if shadow_state.exists():
        log.warning(
            "Removing project-local state/ shadow directory (platform-owned): %s",
            shadow_state,
        )
        shutil.rmtree(shadow_state)

    for rel in DIRECTORIES:
        d = root / rel
        d.mkdir(parents=True, exist_ok=True)
        log.info("Ensured directory: %s", d)

    # Placeholder __init__.py files for importable packages.
    for rel in ["code", "tests", "tests/unit", "tests/contract", "tests/integration"]:
        init = root / rel / "__init__.py"
        if not init.exists():
            init.write_text(
                "# Package marker for PROJ-756 skeleton.\n",
                encoding="utf-8",
            )
            log.info("Created: %s", init)

    # .gitkeep placeholders in data/artifact directories that git ignores.
    for rel in [
        "data/raw",
        "data/processed",
        "data/synthetic",
        "artifacts",
        "results",
        "logs",
    ]:
        keep = root / rel / ".gitkeep"
        if not keep.exists():
            keep.write_text("", encoding="utf-8")
            log.info("Created: %s", keep)

    # Placeholder run.sh at the project root.
    run_sh = root / "run.sh"
    run_sh.write_text(RUN_SH, encoding="utf-8")
    run_sh.chmod(0o755)
    log.info("Created: %s", run_sh)

    # Sanity check: every declared directory exists and no state/ remains.
    missing = [rel for rel in DIRECTORIES if not (root / rel).is_dir()]
    if missing:
        log.error("Missing directories after skeleton creation: %s", missing)
        sys.exit(1)
    if (root / "state").exists():
        log.error("state/ shadow still present; refusing to succeed.")
        sys.exit(1)

    log.info("Project skeleton for %s created successfully.", PROJECT_NAME)


if __name__ == "__main__":
    main()