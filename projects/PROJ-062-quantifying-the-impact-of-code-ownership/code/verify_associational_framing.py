"""
Verification script to ensure all findings in the final report are framed
as associational rather than causal, complying with FR-010 and Plan requirements.
"""
import json
import sys
import re
from pathlib import Path
from typing import List, Tuple, Dict, Any

# Import from existing project config
try:
    from config import get_output_dir
except ImportError:
    # Fallback for direct execution
    from pathlib import Path
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    from config import get_output_dir

from utils.logging_utils import get_logger

logger = get_logger(__name__)

# Keywords that imply causality (forbidden in findings/conclusions)
CAUSAL_KEYWORDS = [
    r'\bcaus(?:e|s|ed|ing|ation|al)\b',
    r'\binfluen(?:ce|es|enced|encing)\b',
    r'\bdetermine[sd]?\b',
    r'\bdrive[sd]?\b',
    r'\bimpact[sd]?\b', # "Impact" is in title but often implies causality in text
    r'\bprove[sd]?\b',
    r'\bestablish[esd]?\b',
    r'\bguarantee[sd]?\b',
    r'\bresult[sd]?\b',
    r'\bcontribute[sd]?\b', # Often implies causality
    r'\blead[sd]?\b',
    r'\btrigger[sd]?\b',
    r'\bforce[sd]?\b',
    r'\bcausality\b',
    r'\bcausal\b',
]

# Keywords that imply association/correlation (required or allowed)
ASSOCIATIONAL_KEYWORDS = [
    r'\bassociat(?:ion|ed|ing|ions)\b',
    r'\bcorrelat(?:ion|ed|ing|ions)\b',
    r'\bassociational\b',
    r'\bcorrelational\b',
    r'\brelationship\b',
    r'\blink(?:age|ed|s)?\b',
    r'\bconnection\b',
    r'\bpattern\b',
    r'\btrend\b',
    r'\bobserve[sd]?\b',
    r'\bindicate[sd]?\b',
    r'\bsuggest[sd]?\b',
    r'\bshow[sd]?\b',
    r'\breflect[sd]?\b',
    r'\bcorrespond(?:s|ing|ence)?\b',
]

# Specific phrases that must appear or be absent
REQUIRED_FRAMING_PHRASES = [
    r'\bassociational\s+rather\s+than\s+causal\b',
    r'\bassociational\s+finding\b',
    r'\bcorrelational\s+evidence\b',
    r'\bdoes\s+not\s+imply\s+causation\b',
    r'\bno\s+causal\s+inference\b',
]

def check_framing_in_text(text: str, context: str = "") -> List[Dict[str, Any]]:
    """
    Analyze a text block for causal language and associational framing.
    Returns a list of violations.
    """
    violations = []
    text_lower = text.lower()

    # Check for forbidden causal keywords
    for pattern in CAUSAL_KEYWORDS:
        matches = re.finditer(pattern, text_lower)
        for match in matches:
            # Get a snippet around the match
            start = max(0, match.start() - 30)
            end = min(len(text), match.end() + 30)
            snippet = text[start:end].replace('\n', ' ').strip()
            
            violations.append({
                "type": "causal_language",
                "pattern": pattern,
                "match": match.group(),
                "snippet": snippet,
                "context": context,
                "severity": "high"
            })

    # Check for required associational phrasing (if this is a conclusion/finding)
    # We don't fail if these are missing in the whole text, but we flag if the text
    # looks like a conclusion and lacks them.
    is_conclusion = "conclusion" in context.lower() or "finding" in context.lower() or "summary" in context.lower()
    
    if is_conclusion:
        has_associational = False
        for pattern in ASSOCIATIONAL_KEYWORDS:
            if re.search(pattern, text_lower):
                has_associational = True
                break
        
        if not has_associational:
            violations.append({
                "type": "missing_associational_framing",
                "message": "Conclusion/Finding section lacks associational language.",
                "context": context,
                "severity": "medium"
            })

    return violations

def verify_final_report(report_path: Path) -> Tuple[bool, List[Dict[str, Any]]]:
    """
    Verify the final report JSON for associational framing.
    Returns (success, list_of_violations).
    """
    if not report_path.exists():
        return False, [{"type": "file_not_found", "path": str(report_path), "severity": "critical"}]

    try:
        with open(report_path, 'r', encoding='utf-8') as f:
            report = json.load(f)
    except json.JSONDecodeError as e:
        return False, [{"type": "json_error", "message": str(e), "severity": "critical"}]

    violations = []

    # Check metadata for explicit framing statement
    metadata = report.get("metadata", {})
    framing_statement = metadata.get("framing", "")
    
    if "associational" not in framing_statement.lower():
        violations.append({
            "type": "missing_framing_statement",
            "message": "Metadata 'framing' field does not explicitly mention 'associational'.",
            "severity": "high"
        })
    
    # Check specific sections that typically contain findings
    sections_to_check = [
        "findings",
        "conclusions",
        "summary",
        "results",
        "discussion"
    ]

    for section in sections_to_check:
        if section in report:
            section_content = report[section]
            if isinstance(section_content, str):
                text_to_check = section_content
                context = f"Section: {section}"
            elif isinstance(section_content, dict):
                # Flatten dict to string for checking
                text_to_check = json.dumps(section_content)
                context = f"Section: {section} (dict)"
            elif isinstance(section_content, list):
                text_to_check = " ".join([str(item) for item in section_content])
                context = f"Section: {section} (list)"
            else:
                continue

            section_violations = check_framing_in_text(text_to_check, context)
            violations.extend(section_violations)

    # Check the entire report as a fallback
    full_text = json.dumps(report)
    full_violations = check_framing_in_text(full_text, "Full Report")
    # Filter out duplicates if a violation was already caught in a specific section
    existing_snippets = {v.get("snippet") for v in violations}
    for v in full_violations:
        if v.get("snippet") not in existing_snippets:
            violations.append(v)

    return len(violations) == 0, violations

def main():
    """
    Main entry point to verify the final report.
    """
    output_dir = get_output_dir()
    report_path = Path(output_dir) / "results" / "final_report.json"
    
    logger.info(f"Checking associational framing in: {report_path}")
    
    success, violations = verify_final_report(report_path)
    
    if success:
        logger.info("SUCCESS: Final report is correctly framed as associational.")
        return 0
    else:
        logger.error("FAILURE: Final report contains causal language or lacks associational framing.")
        logger.error(f"Found {len(violations)} violation(s):")
        
        for i, v in enumerate(violations, 1):
            severity = v.get("severity", "unknown").upper()
            v_type = v.get("type", "unknown")
            msg = v.get("message", v.get("match", v.get("snippet", "No details")))
            ctx = v.get("context", "")
            
            logger.error(f"{i}. [{severity}] {v_type}: {msg}")
            if ctx:
                logger.error(f"   Context: {ctx}")
        
        return 1

if __name__ == "__main__":
    sys.exit(main())
