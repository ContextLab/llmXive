import os
import sys
import logging
from pathlib import Path

def verify_spec_state() -> bool:
    """
    Verify that specs/001-social-support-resilience/spec.md contains the
    required deprecation/revision blocks for FR-001/FR-002 and SC-001.
    
    Returns True if verified, False otherwise.
    """
    spec_path = Path("specs/001-social-support-resilience/spec.md")
    
    if not spec_path.exists():
        logging.error(f"Spec file not found at {spec_path}")
        return False
    
    content = spec_path.read_text()
    
    # Check for FR-001/FR-002 deprecation/removal markers
    # Accepting both "REMOVED" and "DEPRECATED" labels
    fr_deprecated = (
        "FR-001" in content and ("REMOVED" in content or "DEPRECATED" in content)
    ) or (
        "FR-002" in content and ("REMOVED" in content or "DEPRECATED" in content)
    )
    
    # Check for SC-001 revision marker
    sc_revised = "SC-001" in content and "REVISED" in content
    
    if not (fr_deprecated and sc_revised):
        logging.error("Spec state mismatch: Required deprecation/revision blocks not found.")
        logging.error(f"  FR-001/FR-002 deprecated: {fr_deprecated}")
        logging.error(f"  SC-001 revised: {sc_revised}")
        return False
    
    logging.info("Spec state verified as per Plan requirements.")
    return True

def main():
    """Entry point for verification."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    success = verify_spec_state()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
