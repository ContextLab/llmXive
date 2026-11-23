"""
Verification script for Spec Amendments T061, T062, and T063.

This script checks if the spec.md file has been updated to reflect:
- T061: Removal of Last.fm references (FR-001, FR-009)
- T062: Replacement of Sensitivity Sweep with Cook's Distance
- T063: Adjustment of SC-001 to MPD-only denominator

It exits with code 0 if all checks pass, or 1 if any check fails.
"""
import os
import sys
import logging
from pathlib import Path

from utils import setup_logging, get_logger


def setup_logging():
    """Configure logging for the verification script."""
    return setup_logging("verify_spec_amendments_log.txt", level=logging.INFO)


def check_amendment_t061(spec_content: str, logger: logging.Logger) -> bool:
    """
    Check if T061 (Last.fm removal) has been applied.

    Verifies that references to Last.fm 1-Billion Listening Events
    and Last.fm ingestion requirements (FR-001, FR-009) have been removed
    or explicitly marked as waived/omitted in favor of MPD-only.

    Args:
        spec_content: The full text of spec.md.
        logger: Logger instance.

    Returns:
        True if Last.fm references are appropriately removed/waived, False otherwise.
    """
    logger.info("Checking T061: Last.fm removal...")

    # Indicators that the amendment is applied:
    # 1. Explicit mention of the waiver/amendment
    # 2. Absence of active Last.fm ingestion requirements
    has_waiver_mention = (
        "spec_amendment_lastfm.md" in spec_content or
        "Last.fm waiver" in spec_content or
        "MPD-only" in spec_content
    )

    # Check for active, unwaived Last.fm requirements
    # We look for patterns that imply Last.fm is MANDATORY without a waiver
    active_lastfm_requirements = [
        "Last.fm 1-Billion Listening Events",
        "fetch Last.fm",
        "Last.fm data is MANDATORY",
        "Last.fm ingestion is MANDATORY"
    ]

    # If we find active requirements AND no waiver mention, it's a failure
    found_active = False
    for req in active_lastfm_requirements:
        if req in spec_content:
            # Check if it's in a context of a waiver (e.g., "Mandatory UNLESS waiver")
            # A simple heuristic: if the line contains "Mandatory" and "waiver" nearby, it's okay.
            # But if it's just "Mandatory", it's a fail.
            if "waiver" not in spec_content.lower():
                found_active = True
                logger.warning(f"Found active Last.fm requirement without waiver context: {req}")
                break

    if found_active and not has_waiver_mention:
        logger.error("T061 FAILED: Last.fm is still marked as mandatory without waiver documentation.")
        return False

    if has_waiver_mention:
        logger.info("T061 PASSED: Last.fm waiver/amendment is documented.")
        return True

    # If no active requirements found and no waiver mention, it might be implicitly removed.
    # We assume if there are no active "Mandatory" claims, it's passed.
    logger.info("T061 PASSED: No active Last.fm mandatory requirements found.")
    return True


def check_amendment_t062(spec_content: str, logger: logging.Logger) -> bool:
    """
    Check if T062 (Cook's Distance replacement) has been applied.

    Verifies that the "Sensitivity Sweep" (FR-006) has been replaced or
    supplemented by Cook's Distance analysis, and that the amendment
    spec_amendment_fr006.md is referenced.

    Args:
        spec_content: The full text of spec.md.
        logger: Logger instance.

    Returns:
        True if Cook's Distance is present and Sensitivity Sweep is waived/replaced, False otherwise.
    """
    logger.info("Checking T062: Cook's Distance replacement...")

    has_cooks = "Cook's Distance" in spec_content or "Cooks Distance" in spec_content
    has_waiver_ref = "spec_amendment_fr006.md" in spec_content or "FR-006 waiver" in spec_content

    # Check if Sensitivity Sweep is still the ONLY robustness check
    has_sensitivity = "Sensitivity Sweep" in spec_content or "sensitivity sweep" in spec_content

    if not has_cooks:
        logger.error("T062 FAILED: Cook's Distance analysis is not mentioned in spec.md.")
        return False

    if has_sensitivity and not has_waiver_ref:
        logger.warning("T062 WARNING: Sensitivity Sweep is mentioned but Cook's Distance replacement waiver is not explicit.")
        # If Cook's is present, we assume it's the replacement, but warn if sensitivity is still there without context.
        # However, the task requires the replacement to be applied.
        if "replaced by" in spec_content.lower() or "instead of" in spec_content.lower():
            logger.info("T062 PASSED: Cook's Distance is present as replacement.")
            return True
        else:
            logger.error("T062 FAILED: Sensitivity Sweep is still primary; Cook's Distance not clearly established as replacement.")
            return False

    if has_waiver_ref or (has_cooks and not has_sensitivity):
        logger.info("T062 PASSED: Cook's Distance is present and/or Sensitivity Sweep waiver is documented.")
        return True

    logger.error("T062 FAILED: Cannot confirm Cook's Distance replacement.")
    return False


def check_amendment_t063(spec_content: str, logger: logging.Logger) -> bool:
    """
    Check if T063 (SC-001 adjustment) has been applied.

    Verifies that Success Criterion SC-001 denominator is adjusted to MPD tracks only.

    Args:
        spec_content: The full text of spec.md.
        logger: Logger instance.

    Returns:
        True if SC-001 is adjusted to MPD-only, False otherwise.
    """
    logger.info("Checking T063: SC-001 adjustment...")

    has_mpdenom = (
        "MPD-only denominator" in spec_content or
        "MPD tracks only" in spec_content or
        "SC-001 adjusted to MPD" in spec_content
    )

    # Check for old SC-001 definition (e.g., referencing Last.fm in denominator)
    has_old_denom = (
        "Last.fm tracks" in spec_content and "denominator" in spec_content
    )

    if has_mpdenom:
        logger.info("T063 PASSED: SC-001 is adjusted to MPD-only denominator.")
        return True

    if has_old_denom:
        logger.error("T063 FAILED: SC-001 still references Last.fm in denominator.")
        return False

    # If neither, check if SC-001 is mentioned at all
    if "SC-001" in spec_content:
        logger.warning("T063 WARNING: SC-001 is mentioned but MPD-only adjustment is not explicit.")
        # If the text doesn't mention Last.fm in denominator, we might assume it's updated,
        # but strict compliance requires explicit mention.
        # Let's be strict: if it doesn't say MPD-only, it's a fail for this check.
        logger.error("T063 FAILED: SC-001 adjustment to MPD-only is not explicitly stated.")
        return False

    logger.warning("T063 WARNING: SC-001 is not mentioned in spec.md.")
    # If SC-001 is not mentioned, we can't verify the amendment.
    return False


def main():
    """Main entry point for the verification script."""
    logger = setup_logging()
    logger.info("Starting spec amendment verification...")

    spec_path = Path("specs/001-genre-evolution/spec.md")

    if not spec_path.exists():
        logger.error(f"spec.md not found at {spec_path}.")
        sys.exit(1)

    try:
        with open(spec_path, "r", encoding="utf-8") as f:
            spec_content = f.read()
    except Exception as e:
        logger.error(f"Failed to read spec.md: {e}")
        sys.exit(1)

    results = {
        "T061": check_amendment_t061(spec_content, logger),
        "T062": check_amendment_t062(spec_content, logger),
        "T063": check_amendment_t063(spec_content, logger)
    }

    logger.info("Verification complete.")
    all_passed = all(results.values())

    if all_passed:
        logger.info("All spec amendments (T061, T062, T063) are verified.")
        sys.exit(0)
    else:
        failed_tasks = [k for k, v in results.items() if not v]
        logger.error(f"Verification FAILED for: {', '.join(failed_tasks)}")
        sys.exit(1)


if __name__ == "__main__":
    main()