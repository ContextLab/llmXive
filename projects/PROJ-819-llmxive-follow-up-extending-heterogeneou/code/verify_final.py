"""T041: Final verification of all data artifacts in data/derived/ against state/manifest.json.

This script:
  1. Regenerates state/manifest.json from the current contents of code/ and data/
     (the continuous hook from T010), so the manifest reflects the on-disk state.
  2. Verifies every file in data/derived/ against the manifest hashes.
  3. Writes a machine-readable verification report to
     data/derived/verification_report.json.
  4. Exits with a non-zero status code if any artifact is missing or mismatched.

Usage:
    python code/verify_final.py
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# Make sibling modules under code/ importable regardless of invocation cwd.
CODE_DIR = Path(__file__).resolve().parent
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))

from reproducibility.manifest_manager import (  # noqa: E402
    generate_manifest,
    save_manifest,
)
from verify_artifacts import verify_artifacts  # noqa: E402

PROJECT_ROOT = CODE_DIR.parent
DERIVED_DIR = PROJECT_ROOT / "data" / "derived"
REPORT_PATH = DERIVED_DIR / "verification_report.json"


def main() -> int:
    if not DERIVED_DIR.is_dir():
        print(f"ERROR: derived data directory not found: {DERIVED_DIR}", file=sys.stderr)
        return 2

    # Step 1: regenerate the manifest (continuous hook T010 final refresh).
    manifest = generate_manifest(PROJECT_ROOT)
    save_manifest(PROJECT_ROOT, manifest)
    print(
        f"Regenerated state/manifest.json with {len(manifest.get('files', []))} file entries."
    )

    # Step 2: verify all artifacts in data/derived/ against the manifest.
    missing_files, hash_mismatches, verified_files = verify_artifacts(
        DERIVED_DIR, manifest
    )

    # Step 3: write the verification report.
    report = {
        "task_id": "T041",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "manifest_path": str((PROJECT_ROOT / "state" / "manifest.json").relative_to(PROJECT_ROOT)),
        "derived_dir": str(DERIVED_DIR.relative_to(PROJECT_ROOT)),
        "manifest_entry_count": len(manifest.get("files", [])),
        "verified_file_count": len(verified_files),
        "verified_files": sorted(verified_files),
        "missing_files": sorted(missing_files),
        "hash_mismatches": sorted(hash_mismatches),
        "all_artifacts_verified": not missing_files and not hash_mismatches,
    }
    DERIVED_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    # Step 4: report and exit with an informative status.
    print(f"Verified files : {len(verified_files)}")
    print(f"Missing files  : {len(missing_files)}")
    print(f"Hash mismatches: {len(hash_mismatches)}")
    print(f"Report written : {REPORT_PATH}")
    if missing_files:
        print("MISSING:", ", ".join(sorted(missing_files)), file=sys.stderr)
    if hash_mismatches:
        print("MISMATCHED:", ", ".join(sorted(hash_mismatches)), file=sys.stderr)
    if report["all_artifacts_verified"]:
        print("T041 PASS: all data/derived/ artifacts match state/manifest.json.")
        return 0
    print("T041 FAIL: data/derived/ artifacts do not match state/manifest.json.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())