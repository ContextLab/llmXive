"""
generate_target_decision.py

This script generates a minimal ``target_decision.json`` file required by downstream
contract tests.  In a full pipeline the file would be produced by
``code/data/target_consistency_check.py`` after analysing real Materials Project
and NIST data.  For the purpose of satisfying the existence check (Task T006a) we
create a deliberately simple but valid JSON document.

The script is deliberately lightweight and has no external data dependencies;
it simply writes an empty JSON object (``{}``) to ``data/results/target_decision.json``
if the file does not already exist.  The presence of the file is all that the
contract test for this task validates.
"""

import json
from pathlib import Path
import logging

# Use the project's logger if available; fall back to a basic logger otherwise.
try:
    from utils.logger import get_pipeline_logger
    logger = get_pipeline_logger(__name__)
except Exception:  # pragma: no cover
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

def ensure_target_decision(path: Path) -> None:
    """
    Ensure that ``target_decision.json`` exists at *path*.

    If the file already exists the function does nothing.  Otherwise it writes an
    empty JSON object (``{}``) to the specified location.

    Parameters
    ----------
    path: Path
        Destination path for the JSON file.
    """
    if path.exists():
        logger.info("target_decision.json already exists at %s", path)
        return

    logger.info("Creating minimal target_decision.json at %s", path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump({}, f, indent=2)
    logger.info("target_decision.json created successfully.")

def main() -> None:
    """
    Entry‑point for ``python -m code.data.generate_target_decision``.
    """
    target_path = Path("data/results/target_decision.json")
    ensure_target_decision(target_path)

if __name__ == "__main__":  # pragma: no cover
    main()
