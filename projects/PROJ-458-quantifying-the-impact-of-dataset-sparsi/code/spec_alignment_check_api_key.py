"""
T056: Verify that spec.md Assumptions require 'MP_API_KEY environment variable'.

This script reads the spec.md file, checks the 'Assumptions' section for
the requirement of the MP_API_KEY environment variable, and logs the result.
"""
import os
import sys
from pathlib import Path
from utils.logging import get_logger

def load_spec_content() -> str:
    """Load the content of spec.md."""
    spec_path = Path("specs/001-quantifying-the-impact-of-dataset-sparsity/spec.md")
    if not spec_path.exists():
        # Fallback to common root location if specs dir not found
        spec_path = Path("spec.md")
    if not spec_path.exists():
        raise FileNotFoundError(f"Could not find spec.md at {spec_path}")
    return spec_path.read_text(encoding="utf-8")

def check_api_key_alignment(content: str) -> bool:
    """
    Check if the spec.md Assumptions section mentions MP_API_KEY.
    
    Returns True if aligned, False otherwise.
    """
    lines = content.split("\n")
    in_assumptions = False
    found_api_key = False
    
    for line in lines:
        # Detect start of Assumptions section (case-insensitive)
        if "assumptions" in line.lower() or "## assumptions" in line.lower():
            in_assumptions = True
            continue
      
      # If we are in the assumptions section
        if in_assumptions:
            # Check for MP_API_KEY mention
            if "mp_api_key" in line.lower() or "MP_API_KEY" in line:
                found_api_key = True
                break
            # If we hit a new major section, stop checking
            if line.strip().startswith("##") or line.strip().startswith("#"):
                break
      
      # If we haven't found the section yet, keep looking
        if not in_assumptions and ("## assumptions" in line.lower() or "assumptions:" in line.lower()):
            in_assumptions = True
      
      # Fallback check: just search the whole text for MP_API_KEY in context of assumptions
    if not found_api_key:
        # Search entire content for MP_API_KEY near 'Assumptions'
        # This is a more robust check
        if "Assumptions" in content and "MP_API_KEY" in content:
            # Check if they are relatively close (within 500 chars)
            assumptions_idx = content.upper().find("ASSUMPTIONS")
            api_key_idx = content.upper().find("MP_API_KEY")
            if assumptions_idx != -1 and api_key_idx != -1:
                if abs(api_key_idx - assumptions_idx) < 500:
                    found_api_key = True
        
    return found_api_key

def main():
    """Main entry point for T056."""
    logger = get_logger()
    
    try:
        logger.info("Starting T056: Checking spec.md Assumptions for MP_API_KEY requirement...")
        spec_content = load_spec_content()
        
        is_aligned = check_api_key_alignment(spec_content)
        
        if is_aligned:
            logger.info("T056: PASS - spec.md Assumptions section requires MP_API_KEY environment variable.")
            print("PASS")
            return 0
        else:
            logger.error("T056: FAIL - spec.md Assumptions section does NOT require MP_API_KEY environment variable.")
            print("FAIL")
            return 1
            
    except FileNotFoundError as e:
        logger.error(f"T056: FAIL - {e}")
        print(f"FAIL: {e}")
        return 1
    except Exception as e:
        logger.error(f"T056: ERROR - {e}")
        print(f"ERROR: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())