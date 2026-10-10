"""
T036: SPEC VERIFICATION

Verifies that spec.md contains the required amendments:
  - Exclusion of ChestX-ray14 (FR-003/US-2)
  - Native 1024x1024 ground truth (FR-004)
  - Paired t-test/Wilcoxon signed-rank test (SC-004)

Raises RuntimeError if any required text block is missing.
Writes a verification log to data/results/spec_verification_log.json.
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REQUIRED_STRINGS = [
    "ChestX-ray14 is excluded",
    "native 1024x1024 ground truth",
    "Paired t-test or Wilcoxon signed-rank test",
]

SPEC_CANDIDATES = [
    Path("specs/001-viq-resolution-invariance/spec.md"),
    Path("specs/001-viq-resolution-invariance-llmxive-follow-up-extending-viq-text-ali/spec.md"),
    Path("spec.md"),
]

LOG_PATH = Path("data/results/spec_verification_log.json")


def find_spec() -> Path:
    for candidate in SPEC_CANDIDATES:
        if candidate.is_file():
            return candidate
    raise RuntimeError(
        "spec.md not found. Searched: "
        + ", ".join(str(c) for c in SPEC_CANDIDATES)
    )


def verify(spec_path: Path) -> dict:
    text = spec_path.read_text(encoding="utf-8")
    checks = {}
    missing = []
    for required in REQUIRED_STRINGS:
        present = required in text
        checks[required] = present
        if not present:
            missing.append(required)
    if missing:
        raise RuntimeError(
            "spec.md is missing required amendment text blocks: "
            + "; ".join(missing)
        )
    return checks


def main() -> int:
    spec_path = find_spec()
    checks = verify(spec_path)

    log = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "spec_path": str(spec_path),
        "status": "PASS",
        "required_strings": checks,
    }

    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_PATH, "w", encoding="utf-8") as f:
        json.dump(log, f, indent=2)

    print(f"SPEC VERIFICATION PASSED: {spec_path}")
    for s, ok in checks.items():
        print(f"  [OK] {s}")
    print(f"Verification log written to {LOG_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())