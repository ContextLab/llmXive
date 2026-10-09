"""T080: Resolve T050/T051 contradiction.

Verifies that T070's removal validation correctly confirms the absence of
T050/T051 (GAM / compliance-scan) artifacts, and that the "REDO"
instruction is satisfied by this validation rather than by re-implementing
the removed tasks. If T070's validation is missing or reports FAIL, this
script re-runs an independent scan of the codebase and data/processed/
for T050/T051-related artifacts and records the outcome.

Output: data/processed/t080_removal_verification.json
"""

import json
import logging
import re
import sys
from pathlib import Path
from typing import Any, Dict, List

from utils.config import get_project_root, get_path, ensure_dir

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# Artifact filename patterns associated with the removed T050/T051 tasks
# (GAM analysis and compliance scan artifacts).
T050_T051_ARTIFACT_PATTERNS: List[str] = [
    r"gam",
    r"compliance_scan",
    r"nonlinearity_test",
    r"t050",
    r"t051",
]

# Code patterns that would indicate production of T050/T051 artifacts.
T050_T051_CODE_PATTERNS: List[str] = [
    r"gam_results",
    r"compliance_scan",
    r"fit_gam_model\(",
    r"nonlinearity_p_value",
]


def scan_processed_artifacts(processed_dir: Path) -> List[str]:
    """Scan data/processed/ for artifact files tied to T050/T051."""
    violations: List[str] = []
    if not processed_dir.is_dir():
        return violations
    for entry in sorted(processed_dir.iterdir()):
        if not entry.is_file():
            continue
        name_lower = entry.name.lower()
        for pattern in T050_T051_ARTIFACT_PATTERNS:
            if re.search(pattern, name_lower):
                violations.append(str(entry))
                break
    return violations


def scan_code_references(code_dir: Path) -> List[str]:
    """Scan code/ for logic that writes T050/T051 artifacts."""
    violations: List[str] = []
    if not code_dir.is_dir():
        return violations
    for py_file in sorted(code_dir.rglob("*.py")):
        try:
            text = py_file.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for pattern in T050_T051_CODE_PATTERNS:
            if re.search(pattern, text):
                # Allow the historical fit_gam module itself to exist as
                # dead code only if it is never invoked to write
                # artifacts; flag any writer of T050/T051 outputs.
                violations.append(f"{py_file} (pattern: {pattern})")
    return violations


def load_t070_result(processed_dir: Path) -> Dict[str, Any]:
    """Load T070's removal_validation.json if present."""
    path = processed_dir / "removal_validation.json"
    if not path.is_file():
        return {"exists": False}
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        data["exists"] = True
        return data
    except (json.JSONDecodeError, OSError) as exc:
        return {"exists": True, "parse_error": str(exc)}


def run() -> int:
    """Execute the T080 verification and write the report artifact."""
    root = get_project_root()
    processed_dir = get_path("data/processed")
    ensure_dir(processed_dir)
    code_dir = root / "code"

    t070 = load_t070_result(processed_dir)
    artifact_violations = scan_processed_artifacts(processed_dir)
    code_violations = scan_code_references(code_dir)

    t070_pass = bool(t070.get("exists") and t070.get("status") == "PASS")
    independent_pass = not artifact_violations and not code_violations

    if t070_pass and independent_pass:
        status = "PASS"
        conclusion = (
            "T070 correctly validates the absence of T050/T051 artifacts; "
            "the REDO instruction is satisfied by this validation and no "
            "re-implementation of the removed tasks is required."
        )
        action_taken = "none"
    elif not t070.get("exists"):
        status = "FAIL"
        conclusion = (
            "T070 output data/processed/removal_validation.json is missing; "
            "the removal validation must be re-run (T070) before T080 can pass."
        )
        action_taken = "flagged_missing_t070_output"
    elif not independent_pass:
        status = "FAIL"
        conclusion = (
            "Independent scan found T050/T051-related artifacts or code "
            "references despite T070 reporting PASS; the validation logic "
            "must be re-implemented or the artifacts removed."
        )
        action_taken = "independent_rescan_performed"
    else:
        status = "FAIL"
        conclusion = (
            "T070 reported a non-PASS status; the removal validation "
            "requires attention before T080 can pass."
        )
        action_taken = "flagged_t070_failure"

    report: Dict[str, Any] = {
        "task_id": "T080",
        "status": status,
        "t070_result": t070,
        "independent_scan": {
            "artifact_violations": artifact_violations,
            "code_violations": code_violations,
            "pass": independent_pass,
        },
        "action_taken": action_taken,
        "conclusion": conclusion,
        "redo_instruction_satisfied": status == "PASS",
    }

    out_path = Path(processed_dir) / "t080_removal_verification.json"
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2)
    logger.info("T080 verification status: %s", status)
    logger.info("Report written to %s", out_path)

    if status != "PASS":
        logger.error(conclusion)
        return 1
    return 0


def main() -> int:
    """Entry point returning a process status code."""
    return run()


if __name__ == "__main__":
    sys.exit(main())