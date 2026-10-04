"""
T036: SPEC VERIFICATION SCRIPT

Verifies that spec.md contains the required amendments:
1. Exclusion of ChestX-ray14 (FR-003/US-2)
2. Native 1024x1024 ground truth (FR-004)
3. Paired t-test/Wilcoxon (SC-004)

Raises RuntimeError if any required text block is missing.
Writes a verification log to data/results/spec_verification_log.txt on success.
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

# Define required text blocks (keywords/phrases to search for)
REQUIRED_AMENDMENTS = [
    {
        "id": "FR-003/US-2",
        "description": "Exclusion of ChestX-ray14",
        "keywords": [
            "ChestX-ray14",
            "exclusion",
            "Decision Record 001"
        ]
    },
    {
        "id": "FR-004",
        "description": "Native 1024x1024 ground truth",
        "keywords": [
            "1024x1024",
            "native",
            "ground truth",
            "Decision Record 002"
        ]
    },
    {
        "id": "SC-004",
        "description": "Paired t-test/Wilcoxon",
        "keywords": [
            "paired t-test",
            "Wilcoxon",
            "signed-rank",
            "SC-004"
        ]
    }
]

def find_spec_file() -> Path:
    """Locate spec.md in the project root or specs directory."""
    possible_paths = [
        Path("specs/spec.md"),
        Path("spec.md"),
        Path("docs/spec.md"),
        Path("project/spec.md")
    ]
    
    for path in possible_paths:
        if path.exists():
            logger.info(f"Found spec.md at: {path}")
            return path
    
    raise FileNotFoundError(
        "Could not locate spec.md. Please ensure it exists in the project root "
        "or specs/ directory."
    )

def verify_amendments(spec_path: Path) -> Tuple[bool, List[str]]:
    """
    Verify that spec.md contains all required amendments.
    
    Returns:
        Tuple of (all_present, list_of_missing_amendments)
    """
    missing = []
    
    try:
        with open(spec_path, 'r', encoding='utf-8') as f:
            content = f.read().lower()
    except Exception as e:
        raise RuntimeError(f"Failed to read spec.md: {e}")
    
    for amendment in REQUIRED_AMENDMENTS:
        found = False
        # Check if at least one keyword from the set is present
        for keyword in amendment["keywords"]:
            if keyword.lower() in content:
                found = True
                break
        
        if not found:
            missing.append(
                f"{amendment['id']} ({amendment['description']}): "
                f"Missing keywords {amendment['keywords']}"
            )
    
    return len(missing) == 0, missing

def write_verification_log(spec_path: Path, success: bool, missing: List[str]):
    """Write verification results to data/results/spec_verification_log.txt."""
    log_dir = Path("data/results")
    log_dir.mkdir(parents=True, exist_ok=True)
    
    log_path = log_dir / "spec_verification_log.txt"
    
    with open(log_path, 'w', encoding='utf-8') as f:
        f.write("SPEC VERIFICATION LOG\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"Spec file: {spec_path}\n")
        f.write(f"Verification status: {'PASSED' if success else 'FAILED'}\n\n")
        
        if success:
            f.write("All required amendments found:\n")
            for amendment in REQUIRED_AMENDMENTS:
                f.write(f"  ✓ {amendment['id']}: {amendment['description']}\n")
        else:
            f.write("Missing amendments:\n")
            for item in missing:
                f.write(f"  ✗ {item}\n")
        
        f.write("\nVerification completed at: ")
        from datetime import datetime
        f.write(datetime.now().isoformat())
    
    logger.info(f"Verification log written to: {log_path}")

def verify_spec_amendments() -> bool:
    """
    Main verification function.
    
    Returns:
        True if all amendments are present, False otherwise.
        
    Raises:
        RuntimeError: If any required amendment is missing.
    """
    logger.info("Starting spec.md verification for T036...")
    
    # Locate spec.md
    spec_path = find_spec_file()
    
    # Verify amendments
    success, missing = verify_amendments(spec_path)
    
    # Write log
    write_verification_log(spec_path, success, missing)
    
    if not success:
        error_msg = (
            "SPEC VERIFICATION FAILED: The following required amendments are missing "
            "from spec.md:\n" + "\n".join(f"  - {m}" for m in missing) + "\n\n"
            "Please update spec.md to include these amendments before proceeding."
        )
        logger.error(error_msg)
        raise RuntimeError(error_msg)
    
    logger.info("SPEC VERIFICATION PASSED: All required amendments are present.")
    return True

def main():
    """Entry point for the script."""
    try:
        verify_spec_amendments()
        print("✓ T036 Spec Verification: PASSED")
        sys.exit(0)
    except RuntimeError as e:
        print(f"✗ T036 Spec Verification: FAILED")
        print(f"  Reason: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"✗ T036 Spec Verification: ERROR")
        print(f"  Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()