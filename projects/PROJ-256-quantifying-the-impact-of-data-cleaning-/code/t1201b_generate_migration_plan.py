"""
T1201b – Generate migration plan for identified `t0*.py` scripts.

This script discovers all legacy `t0*.py` files in the ``code/`` directory,
creates a simple migration plan that maps each legacy script to a target
module (``cleaning.py``, ``analysis.py`` or ``reporting.py``) based on
heuristics derived from the filename, and writes the plan to both a JSON
file and a human‑readable Markdown report.

The plan is intended to be consumed by downstream verification tasks
(e.g. T1201b verification) and by developers when performing the actual
migration.

The script can be executed directly::

    python code/t1201b_generate_migration_plan.py

It will produce:

* ``data/processed/migration_plan.json`` – machine‑readable plan.
* ``reports/migration_plan.md`` – a concise markdown summary.
"""

import json
import logging
from pathlib import Path
from typing import List, Dict

# The audit module provides the utility to locate all legacy scripts.
from audit_t0_files import find_t0_files


LOGGER = logging.getLogger(__name__)


def _determine_target_module(t0_path: Path) -> str:
    """
    Very simple heuristic to decide which modern module a legacy script
    should be merged into.

    The heuristic is based on substrings that commonly appear in the
    legacy filenames:

    * ``clean`` or ``impute`` → ``cleaning.py``
    * ``analysis`` or ``baseline`` → ``analysis.py``
    * otherwise → ``reporting.py``

    The function returns the *relative* path to the target module inside
    the ``code/`` package.
    """
    name = t0_path.name.lower()
    if "clean" in name or "impute" in name or "outlier" in name:
        return "code/cleaning.py"
    if "analysis" in name or "baseline" in name or "t012" in name:
        return "code/analysis.py"
    # Default fallback – most reporting‑related scripts end up in reporting.py
    return "code/reporting.py"


def generate_migration_plan(t0_files: List[Path]) -> List[Dict[str, str]]:
    """
    Build a migration plan data structure.

    Each entry is a mapping with the following keys:

    * ``legacy_file`` – path to the original ``t0*.py`` script (relative to the
      repository root).
    * ``target_module`` – the module that should receive the logic.
    * ``notes`` – a short placeholder note that can be expanded by developers.
    """
    plan = []
    for fp in t0_files:
        target = _determine_target_module(fp)
        entry = {
            "legacy_file": str(fp),
            "target_module": target,
            "notes": "TODO: migrate logic from legacy script to target module."
        }
        plan.append(entry)
    return plan


def write_plan_json(plan: List[Dict[str, str]], output_path: Path) -> None:
    """
    Serialise the migration plan to JSON.  The output directory is created
    automatically if it does not exist.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(plan, f, indent=2, sort_keys=False)
    LOGGER.info("Migration plan written to JSON: %s", output_path)


def write_plan_markdown(plan: List[Dict[str, str]], output_path: Path) -> None:
    """
    Produce a short markdown summary of the migration plan.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        f.write("# Migration Plan for legacy `t0*.py` scripts\n\n")
        f.write(
            "The following table lists every legacy script discovered in the "
            "`code/` directory and the target module where its functionality "
            "should be migrated.\n\n"
        )
        f.write("| Legacy script | Target module | Notes |\n")
        f.write("|---|---|---|\n")
        for entry in plan:
            f.write(
                f"| `{entry['legacy_file']}` | `{entry['target_module']}` | {entry['notes']} |\n"
            )
    LOGGER.info("Migration plan written to Markdown: %s", output_path)


def main() -> None:
    """
    Entry‑point for the script.

    1. Discover all ``t0*.py`` files.
    2. Generate the migration plan.
    3. Persist the plan as JSON and Markdown.
    """
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    # Step 1 – locate legacy scripts.
    t0_files = find_t0_files()
    if not t0_files:
        LOGGER.warning("No `t0*.py` files were found – nothing to migrate.")
        return

    # Step 2 – build the plan.
    plan = generate_migration_plan(t0_files)

    # Step 3 – write artefacts.
    json_path = Path("data/processed/migration_plan.json")
    md_path = Path("reports/migration_plan.md")
    write_plan_json(plan, json_path)
    write_plan_markdown(plan, md_path)

    LOGGER.info("Migration plan generation completed successfully.")


if __name__ == "__main__":
    main()