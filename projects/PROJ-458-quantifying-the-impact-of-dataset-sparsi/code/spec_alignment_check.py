"""
Spec Alignment Check Module.

This module verifies that the project's specification document (spec.md)
aligns with the required deviations mandated by the plan, specifically
regarding Linear Mixed-Effects Modeling (LMM) in FR-006.
"""
import os
import sys
import json
from pathlib import Path

from utils.logging import get_logger

logger = get_logger(__name__)

def load_spec_content(spec_path: str = "specs/001-quantifying-the-impact-of-dataset-sparsity/spec.md") -> str:
    """
    Load the content of the spec.md file.

    Args:
        spec_path: Relative path to the spec.md file from project root.

    Returns:
        The full text content of the spec file.

    Raises:
        FileNotFoundError: If the spec file does not exist.
    """
    full_path = Path(spec_path)
    if not full_path.exists():
        raise FileNotFoundError(f"Spec file not found at {full_path}")
    
    with open(full_path, "r", encoding="utf-8") as f:
        return f.read()

def check_fr006_alignment(spec_content: str) -> bool:
    """
    Verify that FR-006 in the spec explicitly mentions 'Linear Mixed-Effects Modeling (LMM)'.

    The Plan mandates a deviation from the original Spec (which might have said ANOVA)
    to use LMM for handling nested data structures. This function checks for the
    presence of the required terminology.

    Args:
        spec_content: The full text of spec.md.

    Returns:
        True if FR-006 mentions LMM, False otherwise.
    """
    # Check for the specific required phrase
    required_phrases = [
        "Linear Mixed-Effects Modeling",
        "Linear Mixed-Effects",
        "LMM",
        "Mixed-Effects Model"
    ]
    
    # Look for FR-006 context specifically
    # We search for the section containing FR-006 and check for LMM mentions nearby
    lines = spec_content.split('\n')
    fr006_section = []
    in_fr006 = False
    
    for i, line in enumerate(lines):
        if "FR-006" in line or "FR006" in line:
            in_fr006 = True
        if in_fr006:
            fr006_section.append(line)
            # Stop when we hit the next FR or a major section break
            if (line.strip().startswith("FR-00") or line.strip().startswith("##")) and len(fr006_section) > 1:
                if "FR-00" in line and "FR-006" not in line:
                    break
    
    fr006_text = " ".join(fr006_section).lower()
    
    # Check if any of the required phrases are present in the FR-006 section
    found = any(phrase.lower() in fr006_text for phrase in required_phrases)
    
    return found

def main():
    """
    Main entry point for the spec alignment check.
    
    Reads spec.md, verifies FR-006 alignment with LMM requirement,
    and logs the result.
    """
    spec_path = "specs/001-quantifying-the-impact-of-dataset-sparsity/spec.md"
    
    try:
        content = load_spec_content(spec_path)
        aligned = check_fr006_alignment(content)
        
        if aligned:
            logger.info("PASS: FR-006 correctly specifies 'Linear Mixed-Effects Modeling (LMM)'.")
            result = {"status": "PASS", "feature": "FR-006", "requirement": "LMM", "details": "Spec explicitly mentions LMM."}
        else:
            logger.error("FAIL: FR-006 does not specify 'Linear Mixed-Effects Modeling (LMM)'.")
            result = {"status": "FAIL", "feature": "FR-006", "requirement": "LMM", "details": "Spec does not mention LMM."}
        
        # Write result to data/results directory
        output_dir = Path("data/results")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / "spec_alignment_fr006.json"
        
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)
        
        logger.info(f"Alignment check result written to {output_file}")
        
        return 0 if aligned else 1
        
    except FileNotFoundError as e:
        logger.error(f"Spec file not found: {e}")
        return 1
    except Exception as e:
        logger.error(f"Error during alignment check: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
