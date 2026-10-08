"""
Task T036: SPEC VERIFICATION
Verifies that spec.md contains the required amendments per the project plan.
"""
import os
import sys
import logging
from pathlib import Path
from typing import List, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def find_spec_file() -> Path:
    """Locate the spec.md file in the project root or specs directory."""
    possible_paths = [
        Path("spec.md"),
        Path("specs/spec.md"),
        Path("specs/001-viq-resolution-invariance/spec.md"),
        Path("../spec.md"),
        Path("../../spec.md")
    ]

    for path in possible_paths:
        if path.exists():
            logger.info(f"Found spec.md at: {path.resolve()}")
            return path.resolve()

    raise FileNotFoundError(
        "Could not find spec.md in standard locations. "
        "Please ensure the file exists in the project root or specs directory."
    )

def verify_amendments(spec_path: Path) -> List[Tuple[str, bool]]:
    """
    Verify that the spec.md file contains the required amendment text blocks.

    Required strings (per task description):
    1. "ChestX-ray14 is excluded"
    2. "native 1024x1024 ground truth"
    3. "Paired t-test or Wilcoxon signed-rank test"

    Returns:
        List of tuples (description, passed)
    """
    required_strings = [
        ("ChestX-ray14 exclusion (FR-003)", "ChestX-ray14 is excluded"),
        ("Native 1024x1024 ground truth (FR-004)", "native 1024x1024 ground truth"),
        ("Paired test methodology (SC-004)", "Paired t-test or Wilcoxon signed-rank test")
    ]

    results = []
    try:
        content = spec_path.read_text(encoding='utf-8')
    except Exception as e:
        logger.error(f"Failed to read spec.md: {e}")
        raise

    for description, target_string in required_strings:
        found = target_string.lower() in content.lower()
        results.append((description, found))
        if found:
            logger.info(f"✓ Found: {description}")
        else:
            logger.error(f"✗ Missing: {description} (searched for: '{target_string}')")

    return results

def write_verification_log(
    spec_path: Path,
    results: List[Tuple[str, bool]],
    log_path: Path
) -> None:
    """Write a verification log to disk."""
    all_passed = all(passed for _, passed in results)
    status = "PASSED" if all_passed else "FAILED"

    with open(log_path, 'w', encoding='utf-8') as f:
        f.write(f"# Spec Verification Log\n")
        f.write(f"**Spec File**: {spec_path}\n")
        f.write(f"**Status**: {status}\n")
        f.write(f"**Timestamp**: {Path(__file__).parent.name}\n\n")
        f.write("## Verification Results\n\n")

        for desc, passed in results:
            status_icon = "✅" if passed else "❌"
            f.write(f"- {status_icon} {desc}\n")

        f.write("\n## Summary\n")
        if all_passed:
            f.write("All required amendments are present in spec.md.\n")
        else:
            f.write("CRITICAL: One or more required amendments are missing.\n")
            f.write("The project cannot proceed until spec.md is updated.\n")

    logger.info(f"Verification log written to: {log_path}")

def verify_spec_amendments() -> bool:
    """
    Main entry point for spec verification.

    Returns:
        True if all amendments are present, False otherwise.
    """
    try:
        spec_path = find_spec_file()
    except FileNotFoundError as e:
        logger.error(str(e))
        return False

    results = verify_amendments(spec_path)
    write_verification_log(spec_path, results, Path("data/results/spec_verification.log"))

    all_passed = all(passed for _, passed in results)
    return all_passed

def main():
    """CLI entry point."""
    logger.info("Starting Spec Verification (Task T036)...")
    success = verify_spec_amendments()

    if success:
        logger.info("SUCCESS: All spec amendments verified.")
        sys.exit(0)
    else:
        logger.error("FAILURE: Spec verification failed. Required amendments missing.")
        logger.error("Please update spec.md with the required text blocks.")
        sys.exit(1)

if __name__ == "__main__":
    main()
