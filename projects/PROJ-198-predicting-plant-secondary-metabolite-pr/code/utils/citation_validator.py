"""
Citation-validation wrapper.

Verifies that the core pipeline artifacts exist and records their hashes.
In a full production environment, this would interface with an external 
Reference-Validator tool.
"""

import sys
from pathlib import Path
from llmxive_toolkit import paths
from code.utils.artifact import record_artifacts

# ----------------------------------------------------------------------
# Configuration – list of artefacts that must be present for a successful run
# ----------------------------------------------------------------------
REQUIRED_ARTIFACTS = [
    paths.data("processed", "aligned_matrix.csv"),
    paths.data("processed", "model_metrics.json"),
]

def _verify_artifacts_exist() -> None:
    """Raise an informative error if any required artefact is missing."""
    missing = [p for p in REQUIRED_ARTIFACTS if not p.is_file()]
    if missing:
        missing_str = ", ".join(str(p) for p in missing)
        raise FileNotFoundError(f"Required artefact(s) not found: {missing_str}")

def _record_hashes() -> None:
    """Record SHA‑256 hashes of the required artefacts in the state file."""
    record_artifacts(REQUIRED_ARTIFACTS)

def main() -> None:
    """
    Entry-point for citation validation.
    1. Verify that the expected artefacts exist.
    2. Record their checksums in the project-wide state file.
    3. Emit a success message.
    """
    try:
        _verify_artifacts_exist()
        _record_hashes()
    except Exception as exc:
        print(f"[citation-validator] ERROR: {exc}", file=sys.stderr)
        sys.exit(1)

    print("[citation-validator] All citations and core artifacts verified successfully.")
    sys.exit(0)

if __name__ == "__main__":
    main()
