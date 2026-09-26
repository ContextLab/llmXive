"""
T057: Associational Framing Audit

Scans the paper draft (specs/001-predict-solder-hardness/paper_draft.md) for causal language
in the Discussion section. Raises FramingViolationError if violations are found.
"""
import os
import sys
import re
import logging
from pathlib import Path
from typing import List, Tuple, Optional

# Add project root to path for imports if running as script
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.logging_config import get_logger

logger = get_logger(__name__)

# Path configuration
PAPER_DRAFT_PATH = project_root / "specs" / "001-predict-solder-hardness" / "paper_draft.md"
DISCUSSION_HEADER = "## Discussion"

# Causal language patterns (case-insensitive)
CAUSAL_PATTERNS = [
    r'\bcauses?\b',
    r'\bdrives?\b',
    r'\beffects?\b',
    r'\bimpact\s+on\b', # "impact on" often implies causality in this context
    r'\binfluences?\b',
    r'\bdetermines?\b',
    r'\bresults\s+in\b',
    r'\bleads\s+to\b',
    r'\bcontributes\s+to\b', # Ambiguous, but flagged for review
    r'\bcaus(al|ality)\b',
    r'\battributed\s+to\b',
    r'\broot\s+cause\b',
    r'\bmechanism(s)?\s+of\s+action\b', # Often implies direct causal mechanism
]

class FramingViolationError(Exception):
    """Raised when causal language is detected in the Discussion section."""
    pass

def load_paper_draft(path: Path) -> str:
    """Load the paper draft content."""
    if not path.exists():
        raise FileNotFoundError(f"Paper draft not found at: {path}")
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

def extract_discussion_section(content: str) -> Optional[str]:
    """
    Extract the content of the Discussion section.
    Assumes Markdown format with '## Discussion' header.
    """
    lines = content.split('\n')
    in_discussion = False
    discussion_lines = []
    
    for line in lines:
        if line.strip().startswith(DISCUSSION_HEADER):
            in_discussion = True
            continue
        
        if in_discussion:
            # Check if we hit the next major section (starts with ##)
            if line.strip().startswith('##'):
                break
            discussion_lines.append(line)
    
    if in_discussion:
        return '\n'.join(discussion_lines)
    return None

def scan_for_causal_language(text: str, patterns: List[str]) -> List[Tuple[str, str]]:
    """
    Scan text for causal language patterns.
    Returns a list of (matched_phrase, context_line) tuples.
    """
    violations = []
    for line in text.split('\n'):
        for pattern in patterns:
            matches = re.finditer(pattern, line, re.IGNORECASE)
            for match in matches:
                violations.append((match.group(), line.strip()))
    return violations

def audit_framing(draft_path: Optional[Path] = None) -> bool:
    """
    Main audit logic.
    
    Args:
        draft_path: Optional path to the paper draft. Defaults to standard location.
        
    Returns:
        True if no violations found.
        
    Raises:
        FramingViolationError: If causal language is detected.
        FileNotFoundError: If the draft file is missing.
    """
    path = draft_path or PAPER_DRAFT_PATH
    logger.info(f"Starting framing audit on: {path}")
    
    content = load_paper_draft(path)
    discussion_text = extract_discussion_section(content)
    
    if not discussion_text:
        logger.warning("No '## Discussion' section found in paper draft.")
        # Depending on strictness, this might be a failure, but we'll warn and pass
        # if the section is missing entirely.
        return True
    
    violations = scan_for_causal_language(discussion_text, CAUSAL_PATTERNS)
    
    if violations:
        error_msg = [
            f"FRAMING VIOLATION DETECTED: Found {len(violations)} instance(s) of causal language in Discussion section."
        ]
        for phrase, context in violations:
            error_msg.append(f"  - Found '{phrase}' in: {context}")
        error_msg.append("\nPlease rephrase to use associational language (e.g., 'associated with', 'correlated with', 'predicts').")
        
        raise FramingViolationError("\n".join(error_msg))
    
    logger.info("Framing audit PASSED: No causal language detected in Discussion section.")
    return True

def main():
    """Entry point for the script."""
    try:
        success = audit_framing()
        if success:
            print("Audit Result: PASSED")
            sys.exit(0)
    except FramingViolationError as e:
        print("Audit Result: FAILED")
        print(str(e))
        sys.exit(1)
    except FileNotFoundError as e:
        print(f"Audit Result: ERROR - {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Audit Result: ERROR - Unexpected error: {e}")
        logger.exception("Unexpected error during audit")
        sys.exit(1)

if __name__ == "__main__":
    main()