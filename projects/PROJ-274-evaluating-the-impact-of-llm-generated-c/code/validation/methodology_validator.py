"""
Methodology Validator for T070c.
Verifies that research.md adheres to the 'Critical Methodological Shift':
1. Pre-specified Welch's ANOVA is the ONLY primary test.
2. The 'decision tree' for test selection is REMOVED/REJECTED.
3. Assumption tests (Levene/Shapiro) are for POST-HOC diagnostics ONLY.
"""
import os
import sys
import json
import logging
from pathlib import Path

# Configure logging to file and stdout
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)

def validate_research_content(research_path: Path) -> dict:
    """
    Scans research.md for forbidden keywords and required assertions.
    Returns a validation result dictionary.
    """
    if not research_path.exists():
        raise FileNotFoundError(f"Research file not found: {research_path}")

    content = research_path.read_text(encoding='utf-8').lower()

    # Forbidden patterns indicating the old 'decision tree' approach is still present
    forbidden_patterns = [
        "decision tree",
        "assumption-based selection",
        "conditional logic",
        "if normality then t-test else",
        "if homogeneity then anova else",
        "test selection based on"
    ]

    # Required patterns indicating the new 'Critical Methodological Shift'
    required_patterns = [
        "welch's anova",
        "pre-specified",
        "primary test",
        "post-hoc",
        "diagnostics only"
    ]

    found_forbidden = []
    for pattern in forbidden_patterns:
        if pattern in content:
            # Check if it's explicitly rejected (e.g., "decision tree is REMOVED")
            # Simple heuristic: if the pattern appears near "removed", "rejected", or "not used"
            # For strictness, we flag if it appears as a directive.
            # We will assume if the word exists without explicit negation context, it's a risk.
            # However, the task requires us to assert they are absent OR explicitly marked as rejected.
            # Let's look for the pattern without common negation words nearby.
            if not any(neg in content[content.find(pattern)-50:content.find(pattern)+50] for neg in ["removed", "rejected", "not used", "ignored", "avoid"]):
                found_forbidden.append(pattern)

    found_required = []
    for pattern in required_patterns:
        if pattern in content:
            found_required.append(pattern)

    is_valid = len(found_forbidden) == 0 and len(found_required) >= 3

    result = {
        "status": "valid" if is_valid else "invalid",
        "research_file": str(research_path),
        "forbidden_patterns_found": found_forbidden,
        "required_patterns_found": found_required,
        "message": "Methodology adheres to Critical Shift." if is_valid else "Methodology violates Critical Shift or lacks required assertions."
    }

    return result

def main():
    """
    Entry point for T070c.
    1. Reads specs/001-evaluating-the-impact-of-llm-generated-c/research.md
    2. Validates content.
    3. Writes state/methodology_validation.json.
    4. If valid, creates state/methodology_valid.lock.
    """
    # Determine project root relative to this script
    # Script is at: code/validation/methodology_validator.py
    # Project root is typically 2 levels up or we use the env var if set
    # Assuming standard structure: code/validation/... -> root is parent of code
    current_dir = Path(__file__).resolve().parent
    project_root = current_dir.parent.parent

    research_file = project_root / "specs" / "001-evaluating-the-impact-of-llm-generated-c" / "research.md"
    output_dir = project_root / "state"
    output_file = output_dir / "methodology_validation.json"
    lock_file = output_dir / "methodology_valid.lock"

    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Validating research file: {research_file}")
    
    try:
        result = validate_research_content(research_file)
        
        # Write validation result
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2)
        logger.info(f"Validation result written to {output_file}")

        if result["status"] == "valid":
            # Create lock file
            with open(lock_file, 'w', encoding='utf-8') as f:
                f.write("Methodology validated successfully.\n")
            logger.info(f"Lock file created: {lock_file}")
            logger.info("Validation PASSED. Proceeding to next tasks.")
            sys.exit(0)
        else:
            logger.error("Validation FAILED. Pipeline must abort.")
            logger.error(f"Reason: {result['message']}")
            logger.error(f"Forbidden patterns found: {result['forbidden_patterns_found']}")
            sys.exit(1)

    except FileNotFoundError as e:
        logger.error(f"Critical Error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during validation: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()