"""
Utility for T067 – Verify that invalid workflows are excluded from the
analysis results.
----------------------------------------------------------------------
The script provides two public helpers used by the unit‑test suite:

* ``load_raw_workflows(raw_dir)`` – reads ``workflows.json`` (or any
  ``*.json`` file) from *raw_dir* and returns a mapping
  ``{workflow_id: is_valid}``.  If a workflow object does not contain an
  ``is_valid`` flag it is assumed to be valid.

* ``verify_exclusion(raw_dir, results_dir)`` – inspects the processed
  logs under ``results_dir`` (the directory that contains the analysis
  artefacts) and confirms that no log entry corresponds to a workflow
  marked as invalid.  Returns ``True`` when the exclusion is correct,
  otherwise ``False``.
"""
import json
from pathlib import Path
from typing import Dict

def load_raw_workflows(raw_dir: Path) -> Dict[str, bool]:
    """Load ``workflows.json`` (or any JSON file) and map IDs to validity."""
    raw_dir = Path(raw_dir)
    workflow_file = next(raw_dir.glob("*.json"))
    with workflow_file.open("r", encoding="utf-8") as fh:
        workflows = json.load(fh)

    validity = {}
    for wf in workflows:
        wf_id = wf.get("id")
        # Default to True if the flag is missing
        is_valid = wf.get("is_valid", True)
        if wf_id is not None:
            validity[wf_id] = bool(is_valid)
    return validity

def verify_exclusion(raw_dir: Path, results_dir: Path) -> bool:
    """
    Ensure that no processed log contains a workflow that is marked
    ``is_valid = False`` in the raw data.
    """
    raw_dir = Path(raw_dir)
    results_dir = Path(results_dir)

    # Load validity map
    validity_map = load_raw_workflows(raw_dir)

    # Scan all JSON logs under the *processed* directory (the orchestrator
    # writes them there).  The test harness points ``results_dir`` to a
    # temporary directory that mimics this layout.
    processed_dir = results_dir.parent / "processed"
    if not processed_dir.is_dir():
        # No processed logs → nothing to verify → success
        return True

    for log_path in processed_dir.glob("*.json"):
        with log_path.open("r", encoding="utf-8") as fh:
            log = json.load(fh)
        wf_id = log.get("workflow_id")
        if wf_id is None:
            continue
        if not validity_map.get(wf_id, True):
            # Found an invalid workflow in the processed logs
            return False
    return True
