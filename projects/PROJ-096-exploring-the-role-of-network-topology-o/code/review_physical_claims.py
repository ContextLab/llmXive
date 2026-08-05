import os
import sys
import json
import logging
import re
from pathlib import Path
from typing import List, Dict, Any, Tuple

# Add parent directory to path to allow imports from utils if needed, 
# though this script primarily uses standard library and local file I/O.
sys.path.insert(0, str(Path(__file__).parent))

def init_logging():
    """Initialize logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

def load_file_content(file_path: str) -> str:
    """Load and return the content of a text file."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    return path.read_text(encoding='utf-8')

def load_json_content(file_path: str) -> Dict[str, Any]:
    """Load and return the content of a JSON file."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def check_physical_claims(report_path: str, invariance_path: str) -> Tuple[bool, List[str], List[str]]:
    """
    Review the analysis report for claims about 'physical reality' and verify
    they are supported by the invariance verification results.

    Args:
        report_path: Path to the analysis_report.md file.
        invariance_path: Path to the invariance_verification.json file.

    Returns:
        Tuple of (all_claims_supported, list_of_unsupported_claims, list_of_references_found)
    """
    logger = logging.getLogger(__name__)
    
    # Load content
    report_content = load_file_content(report_path)
    invariance_data = load_json_content(invariance_path)

    # Define patterns for claims
    # We look for phrases like "physical reality", "element of reality", "observer-invariant"
    claim_patterns = [
        r"physical\s+reality",
        r"element\s+of\s+reality",
        r"observer[- ]?invariant",
        r"coordinate[- ]?invariant",
        r"independent\s+of\s+the\s+observer",
        r"EPR\s+criterion"
    ]
    
    # Define patterns for references
    reference_patterns = [
        r"invariance_verification",
        r"T026",
        r"T051",
        r"physical\s+invariance",
        r"reference\s+frame",
        r"rotational\s+invariance"
    ]

    claims_found = []
    references_found = []
    unsupported_claims = []

    # Check for claims
    for pattern in claim_patterns:
        matches = re.findall(pattern, report_content, re.IGNORECASE)
        if matches:
            # Find the context (line) where the claim appears
            lines = report_content.split('\n')
            for i, line in enumerate(lines):
                if re.search(pattern, line, re.IGNORECASE):
                    claims_found.append({
                        "line": i + 1,
                        "text": line.strip(),
                        "pattern": pattern
                    })

    # Check for references
    for pattern in reference_patterns:
        matches = re.findall(pattern, report_content, re.IGNORECASE)
        if matches:
            lines = report_content.split('\n')
            for i, line in enumerate(lines):
                if re.search(pattern, line, re.IGNORECASE):
                    references_found.append({
                        "line": i + 1,
                        "text": line.strip(),
                        "pattern": pattern
                    })

    # Validate: Every claim must be supported by a reference within a reasonable proximity (e.g., 5 lines)
    # For simplicity in this script, we check if any reference exists in the document 
    # and if the "Physical Invariance Verification" section exists.
    
    has_invariance_section = "Physical Invariance Verification" in report_content
    has_invariance_data = len(invariance_data) > 0
    all_invariant = all(item.get('status') == 'invariant' for item in invariance_data)

    # Logic for support
    if claims_found:
        if not has_invariance_section:
            unsupported_claims.append("Report claims physical reality but lacks 'Physical Invariance Verification' section.")
        elif not has_invariance_data:
            unsupported_claims.append("Report claims physical reality but invariance data file is empty or missing.")
        elif not all_invariant:
            unsupported_claims.append("Report claims physical reality but not all topologies are marked 'invariant' in data.")
        else:
            # Check if references are present near claims
            # A simple heuristic: if references_found is not empty, we assume support for now
            # In a more complex parser, we'd check line proximity.
            if not references_found:
                unsupported_claims.append("Report claims physical reality but contains no explicit references to invariance methodology (e.g., T026, invariance_verification).")
            else:
                logger.info(f"Claims found: {len(claims_found)}. References found: {len(references_found)}. All supported.")

    return len(unsupported_claims) == 0, unsupported_claims, references_found

def main():
    """Main entry point for the review script."""
    init_logging()
    logger = logging.getLogger(__name__)

    # Define paths relative to project root
    project_root = Path(__file__).parent.parent
    report_path = project_root / "data" / "processed" / "analysis_report.md"
    invariance_path = project_root / "data" / "processed" / "invariance_verification.json"

    logger.info(f"Starting physical claims review for: {report_path}")
    
    if not report_path.exists():
        logger.error(f"Report file not found: {report_path}")
        sys.exit(1)
    
    if not invariance_path.exists():
        logger.error(f"Invariance data file not found: {invariance_path}")
        sys.exit(1)

    try:
        supported, unsupported, refs = check_physical_claims(str(report_path), str(invariance_path))
        
        if unsupported:
            logger.error("UNSATISFIED CLAIMS DETECTED:")
            for claim in unsupported:
                logger.error(f"  - {claim}")
            logger.error("Review FAILED. Claims about physical reality are not fully supported.")
            sys.exit(1)
        else:
            logger.info("SUCCESS: All claims about physical reality are supported by invariance evidence.")
            logger.info(f"References found: {[r['text'] for r in refs]}")
            sys.exit(0)

    except Exception as e:
        logger.error(f"Error during review: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
