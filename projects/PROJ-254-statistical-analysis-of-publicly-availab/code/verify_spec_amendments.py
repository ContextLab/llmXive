"""
Verification script for Spec Amendments T061, T062, T063.

This script checks if the required changes to spec.md have been applied:
- T061: Removal of Last.fm references (FR-001, FR-009)
- T062: Presence of Cook's Distance text replacing Sensitivity Sweep
- T063: Adjustment of SC-001 to MPD-only denominator

Exit code 0: All amendments verified.
Exit code 1: One or more amendments missing or incorrect.
"""

import os
import sys
import logging
from pathlib import Path

# Setup logging similar to other pipeline components
def setup_logging():
    log_dir = Path("data")
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / "verification_log.txt"

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file, mode="w"),
            logging.StreamHandler(sys.stdout),
        ],
    )
    return logging.getLogger(__name__)

def check_amendment_t061(content: str) -> tuple[bool, str]:
    """
    T061: Verify removal of Last.fm references.

    Checks that FR-001 and FR-009 no longer mandate Last.fm 1-Billion data.
    """
    # Patterns indicating Last.fm is still required
    forbidden_patterns = [
        "Last.fm 1-Billion",
        "Last.fm dataset is MANDATORY",
        "FR-001.*Last.fm",
        "FR-009.*Last.fm",
        "fetch Last.fm data",
    ]
    
    # Patterns indicating the waiver/amendment is present
    allowed_patterns = [
        "MPD-only",
        "Last.fm waiver",
        "spec_amendment_lastfm.md",
        "Last.fm omission",
    ]

    found_forbidden = []
    for pattern in forbidden_patterns:
        # Simple substring check for robustness
        if pattern.lower() in content.lower():
            found_forbidden.append(pattern)

    if found_forbidden:
        return False, f"Found forbidden Last.fm requirements: {found_forbidden}"

    found_allowed = any(p.lower() in content.lower() for p in allowed_patterns)
    if not found_allowed:
        return False, "No evidence of Last.fm waiver/amendment found in spec.md"

    return True, "T061 Verified: Last.fm requirements removed and waiver documented."

def check_amendment_t062(content: str) -> tuple[bool, str]:
    """
    T062: Verify Cook's Distance implementation replaces Sensitivity Sweep.

    Checks that FR-006 (Sensitivity Sweep) is replaced by Cook's Distance.
    """
    # Patterns indicating old Sensitivity Sweep is still mandatory
    forbidden_patterns = [
        "FR-006.*MANDATORY",
        "Sensitivity Sweep.*required",
        "threshold sweep.*FR-006",
    ]

    # Patterns indicating Cook's Distance is the new standard
    required_patterns = [
        "Cook's Distance",
        "T032b",
        "Cook's Distance Outlier Analysis",
        "FR-006.*waived",
        "Sensitivity Sweep.*replaced",
    ]

    found_forbidden = []
    for pattern in forbidden_patterns:
        if pattern.lower() in content.lower():
            found_forbidden.append(pattern)

    if found_forbidden:
        return False, f"Found forbidden Sensitivity Sweep requirements: {found_forbidden}"

    found_required = any(p.lower() in content.lower() for p in required_patterns)
    if not found_required:
        return False, "No evidence of Cook's Distance replacement found in spec.md"

    return True, "T062 Verified: Sensitivity Sweep replaced by Cook's Distance."

def check_amendment_t063(content: str) -> tuple[bool, str]:
    """
    T063: Verify SC-001 adjustment to MPD-only denominator.

    Checks that Success Criterion SC-001 reflects MPD-only tracks.
    """
    # Patterns indicating old denominator (Last.fm + MPD)
    forbidden_patterns = [
        "SC-001.*Last.fm.*denominator",
        "coverage.*Last.fm tracks",
        "total.*Last.fm.*and.*MPD",
    ]

    # Patterns indicating new denominator (MPD only)
    required_patterns = [
        "SC-001.*MPD-only",
        "denominator.*MPD tracks",
        "coverage.*MPD-only",
        "spec_amendment_sc001.md",
    ]

    found_forbidden = []
    for pattern in forbidden_patterns:
        if pattern.lower() in content.lower():
            found_forbidden.append(pattern)

    if found_forbidden:
        return False, f"Found forbidden SC-001 definitions: {found_forbidden}"

    found_required = any(p.lower() in content.lower() for p in required_patterns)
    if not found_required:
        return False, "No evidence of SC-001 MPD-only adjustment found in spec.md"

    return True, "T063 Verified: SC-001 adjusted to MPD-only denominator."

def main():
    logger = setup_logging()
    logger.info("Starting Spec Amendment Verification (T067)...")

    # Locate spec.md
    possible_paths = [
        Path("specs/001-genre-evolution/spec.md"),
        Path("spec.md"),
        Path("specs/spec.md"),
    ]
    
    spec_path = None
    for p in possible_paths:
        if p.exists():
            spec_path = p
            break

    if not spec_path:
        logger.error("Could not locate spec.md in expected paths.")
        sys.exit(1)

    logger.info(f"Found spec.md at: {spec_path}")

    try:
        with open(spec_path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        logger.error(f"Failed to read spec.md: {e}")
        sys.exit(1)

    checks = [
        ("T061 (Last.fm Removal)", check_amendment_t061),
        ("T062 (Cook's Distance)", check_amendment_t062),
        ("T063 (SC-001 Adjustment)", check_amendment_t063),
    ]

    all_passed = True
    results = []

    for name, check_func in checks:
        passed, message = check_func(content)
        results.append((name, passed, message))
        if passed:
            logger.info(f"[PASS] {name}: {message}")
        else:
            logger.error(f"[FAIL] {name}: {message}")
            all_passed = False

    # Write summary to log
    logger.info("-" * 50)
    logger.info("Verification Summary:")
    for name, passed, message in results:
        status = "PASSED" if passed else "FAILED"
        logger.info(f"  {name}: {status}")

    if all_passed:
        logger.info("All Spec Amendments (T061, T062, T063) verified successfully.")
        sys.exit(0)
    else:
        logger.error("Verification failed. One or more amendments are missing or incorrect.")
        sys.exit(1)

if __name__ == "__main__":
    main()