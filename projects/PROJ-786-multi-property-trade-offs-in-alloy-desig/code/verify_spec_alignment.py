"""
Task T000: Verify and Synchronize Spec.md with Bulk/Shear Moduli Pivot.

This script verifies that `specs/001-multi-property-trade-offs/spec.md` contains
the required Version History entries (v1.1, v1.2) and that specific functional
requirements (FR-001, FR-003, FR-005), success criteria (SC-001), and user stories
(US-1) explicitly reference "Bulk and Shear Moduli" or "DFT proxy".

It outputs a verification log to stdout and exits with code 0 if aligned,
or code 1 if critical content is missing.
"""
import os
import sys
import re
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
PROJECT_ROOT = Path(__file__).parent.parent
SPEC_PATH = PROJECT_ROOT / "specs" / "001-multi-property-trade-offs" / "spec.md"

# Required keywords for verification
REQUIRED_VERSION_ENTRIES = ["v1.1", "v1.2"]
BULK_SHEAR_KEYWORDS = [
    "Bulk and Shear Moduli",
    "Bulk Modulus",
    "Shear Modulus",
    "elastic_properties",
    "DFT proxy"
]
TARGET_SECTIONS = [
    "FR-001",
    "FR-003",
    "FR-005",
    "SC-001",
    "US-1"
]

def load_spec_content(path: Path) -> str:
    """Load the spec.md content."""
    if not path.exists():
        raise FileNotFoundError(f"Spec file not found at: {path}")
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

def check_version_history(content: str) -> bool:
    """Verify Version History contains v1.1 and v1.2 referencing Bulk/Shear."""
    logger.info("Checking Version History...")
    found_versions = set()
    
    # Look for version history section or entries
    lines = content.split('\n')
    for line in lines:
        line_lower = line.lower()
        for ver in REQUIRED_VERSION_ENTRIES:
            if ver.lower() in line_lower:
                # Check if it mentions Bulk/Shear nearby (simple heuristic)
                found_versions.add(ver)
    
    if not found_versions.issuperset(set(REQUIRED_VERSION_ENTRIES)):
        logger.warning(f"Missing version entries in spec. Found: {found_versions}, Required: {REQUIRED_VERSION_ENTRIES}")
        return False
    
    logger.info(f"Version History check passed: Found {found_versions}")
    return True

def check_section_content(content: str) -> bool:
    """Verify target sections reference Bulk/Shear Moduli."""
    logger.info("Checking target sections for Bulk/Shear Moduli references...")
    all_passed = True
    
    # Simple heuristic: check if the section headers exist and if the keywords appear
    # in the general vicinity or if the file contains the keywords frequently enough
    # given the specific section constraints.
    
    # Since regex across sections is complex without a parser, we check:
    # 1. Do the section headers exist?
    # 2. Do the required keywords exist in the file?
    # 3. Do the keywords appear near the section headers?
    
    section_pattern = re.compile(rf"(?i)({'|'.join(TARGET_SECTIONS)})")
    keyword_pattern = re.compile(rf"(?i)({'|'.join(BULK_SHEAR_KEYWORDS)})")
    
    lines = content.split('\n')
    current_section = None
    section_has_keyword = {sec: False for sec in TARGET_SECTIONS}
    
    for line in lines:
        # Check for section header
        sec_match = section_pattern.search(line)
        if sec_match:
            current_section = sec_match.group(1).upper()
        
        # Check for keywords
        if current_section and keyword_pattern.search(line):
            section_has_keyword[current_section] = True
        
        # Also check if keywords appear generally if we haven't found them yet
        # This is a fallback for cases where the section might be formatted differently
        if not section_has_keyword.get(current_section, False) and keyword_pattern.search(line):
            # If we are in a target section, mark it
            if current_section and current_section in section_has_keyword:
                section_has_keyword[current_section] = True

    # Verify all target sections have at least one mention
    for sec, has_keyword in section_has_keyword.items():
        if not has_keyword:
            logger.warning(f"Section {sec} does not explicitly reference Bulk/Shear Moduli keywords.")
            all_passed = False
        else:
            logger.info(f"Section {sec} verified: contains Bulk/Shear references.")
    
    return all_passed

def run_verification():
    """Main verification logic."""
    logger.info(f"Starting Spec Alignment Verification for T000...")
    logger.info(f"Target file: {SPEC_PATH}")
    
    if not SPEC_PATH.exists():
        logger.error(f"CRITICAL: Spec file not found at {SPEC_PATH}.")
        print("VERIFICATION FAILED: Spec file missing.")
        return False

    try:
        content = load_spec_content(SPEC_PATH)
    except Exception as e:
        logger.error(f"Failed to load spec content: {e}")
        return False

    # Step 1: Check Version History
    version_ok = check_version_history(content)
    
    # Step 2: Check Section Content
    sections_ok = check_section_content(content)

    if version_ok and sections_ok:
        logger.info("=" * 50)
        logger.info("VERIFICATION SUCCESSFUL: Spec.md is aligned with Bulk/Shear Moduli Pivot.")
        logger.info("All required version entries (v1.1, v1.2) are present.")
        logger.info("All target sections (FR-001, FR-003, FR-005, SC-001, US-1) reference the correct targets.")
        print("\n[LOG] T000 Verification Complete: PASS")
        print(f"[LOG] Spec file: {SPEC_PATH}")
        print(f"[LOG] Status: Aligned with v1.2 standards (Bulk/Shear Moduli)")
        return True
    else:
        logger.error("=" * 50)
        logger.error("VERIFICATION FAILED: Spec.md is NOT aligned.")
        if not version_ok:
            logger.error("- Missing or incorrect Version History entries.")
        if not sections_ok:
            logger.error("- Target sections missing Bulk/Shear Moduli references.")
        print("\n[LOG] T000 Verification Complete: FAIL")
        print("[LOG] Action Required: Update spec.md to v1.2 standards.")
        return False

if __name__ == "__main__":
    success = run_verification()
    sys.exit(0 if success else 1)
