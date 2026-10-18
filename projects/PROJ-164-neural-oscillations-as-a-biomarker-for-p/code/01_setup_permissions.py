"""T001b: Conditional Permission Setting on data/raw.

Sets restricted write permissions (chmod 555) on data/raw ONLY if the
pipeline mode is 'Data Insufficient' or 'Underpowered'. If the mode is
'Primary', permissions are set to 755 so that T013 (data download) can
write into the directory.

The mode is read from the verified source manifest
(data/verified_source_manifest.json, field "mode_flag") produced by
T011/T012. Evidence of the applied permissions is written to
state/projects/permissions_report.json.
"""

import json
import logging
import os
import stat
import sys
from datetime import datetime, timezone
from pathlib import Path

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

RESTRICTED_MODE = 0o555  # read-execute only
PRIMARY_MODE = 0o755     # owner may write (T013 needs this)

def _load_mode_flag(manifest_path: Path) -> str:
    """Read the mode_flag from the verified source manifest.

    Raises loudly if the manifest is missing or malformed — no silent
    fallback, since permission policy depends on the verified mode.
    """
    if not manifest_path.is_file():
        raise FileNotFoundError(
          f"Verified source manifest not found at {manifest_path}; "
          "run T011/T012 before setting permissions."
      )
    with open(manifest_path, "r", encoding="utf-8") as fh:
        manifest = json.load(fh)
    mode = manifest.get("mode_flag")
    if not mode:
        raise ValueError(
          f"Manifest at {manifest_path} has no 'mode_flag' field; "
          "cannot determine permission policy."
      )
    return str(mode)

def _current_mode(path: Path) -> int:
    return stat.S_IMODE(path.stat().st_mode)

def set_restricted_permissions() -> Path:
    """Apply the conditional permission policy to data/raw.

    Returns the path of the evidence report written to
    state/projects/permissions_report.json.
    """
    raw_dir = paths.data("raw")
    if not raw_dir.is_dir():
        raise FileNotFoundError(f"data/raw directory does not exist: {raw_dir}")

    manifest_path = paths.data("verified_source_manifest.json")
    mode_flag = _load_mode_flag(manifest_path)

    before = _current_mode(raw_dir)
    if mode_flag in ("Data Insufficient", "Underpowered"):
        target = RESTRICTED_MODE
        log.info(
            "Mode '%s': setting data/raw to read-execute only (chmod 555).",
            mode_flag,
        )
    elif mode_flag == "Primary":
        target = PRIMARY_MODE
        log.info(
            "Mode 'Primary': ensuring data/raw is writable (chmod 755) "
            "so T013 can download data."
        )
    else:
        raise ValueError(f"Unknown mode_flag '{mode_flag}' in manifest.")

    os.chmod(raw_dir, target)
    after = _current_mode(raw_dir)

    report = {
        "task_id": "T001b",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "directory": str(raw_dir),
        "mode_flag": mode_flag,
        "permissions_before": format(before, "3o"),
        "permissions_after": format(after, "3o"),
        "policy_applied": (
            "restricted (555)" if target == RESTRICTED_MODE else "writable (755)"
        ),
        "manifest": str(manifest_path),
    }

    report_path = paths.path("state", "projects", "permissions_report.json")
    with open(report_path, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2)
    log.info("Permissions report written to %s", report_path)

    if after != target:
        raise RuntimeError(
          f"Failed to apply target permissions {format(target, '3o')} "
          f"to {raw_dir} (got {format(after, '3o')})."
      )
    return report_path

def main() -> int:
    try:
        report_path = set_restricted_permissions()
    except Exception as exc:  # fail loudly
        log.error("T001b failed: %s", exc)
        return 1
    print(f"T001b complete; evidence at {report_path}")
    return 0

if __name__ == "__main__":
    sys.exit(main())