"""T044b: Verification helper for the detect-secrets baseline.

Loads `.secrets.baseline` from the project root and confirms it is a
genuine detect-secrets baseline (contains `plugins_used` and `results`
keys). Exits non-zero with a clear message if the file is missing or
malformed, so a failed generation can never pass silently.
"""

import json
import sys
from pathlib import Path


def verify_baseline(baseline_path: Path) -> bool:
    """Return True if the file is a valid detect-secrets baseline."""
    if not baseline_path.is_file():
        print(f"ERROR: baseline file not found at {baseline_path}", file=sys.stderr)
        return False

    try:
        with open(baseline_path) as f:
            baseline = json.load(f)
    except json.JSONDecodeError as e:
        print(f"ERROR: baseline file is not valid JSON: {e}", file=sys.stderr)
        return False

    missing = [k for k in ("plugins_used", "results") if k not in baseline]
    if missing:
        print(
            f"ERROR: baseline missing required keys: {missing}",
            file=sys.stderr,
        )
        return False

    n_files = len(baseline["results"])
    n_secrets = sum(len(v) for v in baseline["results"].values())
    print(
        f"Baseline OK: {n_files} file(s) scanned, "
        f"{n_secrets} potential secret(s) recorded for audit."
    )
    return True


def main() -> int:
    project_root = Path(__file__).resolve().parents[2]
    baseline_path = project_root / ".secrets.baseline"
    return 0 if verify_baseline(baseline_path) else 1


if __name__ == "__main__":
    sys.exit(main())