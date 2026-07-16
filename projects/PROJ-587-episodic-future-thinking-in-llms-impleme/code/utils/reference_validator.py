"""
Reference Validator for Constitution Principle II.

This module validates that the implementation plan (`plan.md`) contains
the required citations and references to foundational literature and
specific artifacts as mandated by the project's constitutional principles.
"""

import os
import re
import sys
from pathlib import Path
from typing import List, Dict, Tuple, Optional

# Configuration: Required patterns for citations in the plan
# These correspond to the "Cellular Alphabet" and "Statistical Retrieval"
# distinctions raised by reviewers (e.g., Kandel, Krakauer).
REQUIRED_CITATION_PATTERNS = [
    r"Kandel",           # Eric Kandel - Synaptic basis of memory
    r"Krakauer",         # David Krakauer - Entropy/Negotiation
    r"Kahneman",         # Daniel Kahneman - System 1/2, WYSIATI
    r"Tversky",          # Amos Tversky - Heuristics
    r"ALFWorld",         # Dataset reference
    r"TextWorld",        # Dataset reference
    r"FAISS",            # Retrieval mechanism
    r"Constitution.*Principle", # Internal constitutional references
]

# Configuration: Required file references
REQUIRED_FILE_REFS = [
    r"specs/001-episodic-future-thinking",
    r"data-model\.md",
    r"plan\.md",
]

class ReferenceValidationError(Exception):
    """Raised when citation or reference validation fails."""
    pass


def load_plan_content(plan_path: Path) -> str:
    """
    Load the content of the implementation plan.

    Args:
        plan_path: Path to the plan.md file.

    Returns:
        The full text content of the plan.

    Raises:
        FileNotFoundError: If the plan file does not exist.
    """
    if not plan_path.exists():
        raise FileNotFoundError(f"Plan file not found: {plan_path}")
    return plan_path.read_text(encoding="utf-8")


def extract_citations(text: str) -> List[str]:
    """
    Extract potential citation mentions from text.
    Looks for capitalized names followed by potential context or just capitalized names
    in specific contexts.

    Args:
        text: The text to scan.

    Returns:
        A list of matched citation strings.
    """
    # Simple heuristic: Look for capitalized words that might be names
    # or specific keywords defined in the project context.
    # A more robust NLP approach could be used, but regex suffices for
    # the constitutional requirement of "mentioning" the key figures.
    pattern = r"\b(Kandel|Krakauer|Kahneman|Tversky|ALFWorld|TextWorld|FAISS|Constitution)\b"
    matches = re.findall(pattern, text, re.IGNORECASE)
    return matches


def extract_file_references(text: str) -> List[str]:
    """
    Extract file path references from text.

    Args:
        text: The text to scan.

    Returns:
        A list of matched file path strings.
    """
    # Matches paths like specs/001-episodic-future-thinking, data-model.md, etc.
    pattern = r"[\w/-]+\.\w+|specs/[\w/-]+"
    matches = re.findall(pattern, text)
    return matches


def validate_citations(text: str, required_patterns: List[str]) -> Tuple[bool, List[str]]:
    """
    Validate that the text contains all required citation patterns.

    Args:
        text: The text to validate.
        required_patterns: List of regex patterns that must be found.

    Returns:
        Tuple of (is_valid, list_of_missing_patterns).
    """
    missing = []
    for pattern in required_patterns:
        if not re.search(pattern, text, re.IGNORECASE):
            missing.append(pattern)
    return len(missing) == 0, missing


def validate_plan_references(text: str, required_refs: List[str]) -> Tuple[bool, List[str]]:
    """
    Validate that the text references required project files.

    Args:
        text: The text to validate.
        required_refs: List of regex patterns for file paths.

    Returns:
        Tuple of (is_valid, list_of_missing_refs).
    """
    missing = []
    for pattern in required_refs:
        if not re.search(pattern, text, re.IGNORECASE):
            missing.append(pattern)
    return len(missing) == 0, missing


def pre_commit_hook(plan_path: Optional[Path] = None) -> int:
    """
    Entry point for the pre-commit hook.

    Validates the plan.md file against constitutional requirements.
    Exits with code 1 if validation fails, 0 otherwise.

    Args:
        plan_path: Optional override for the plan path. Defaults to 'plan.md'
                   in the project root.

    Returns:
        Exit code (0 for success, 1 for failure).
    """
    if plan_path is None:
        # Default to plan.md in the project root (relative to code/ or root?)
        # Based on tasks.md, plan.md is at the project root.
        # We assume the script is run from the project root or code/ directory.
        # Let's try relative to current working directory first, then project root.
        cwd = Path.cwd()
        potential_paths = [
            cwd / "plan.md",
            cwd.parent / "plan.md",
            Path("plan.md")
        ]
        found = False
        for p in potential_paths:
            if p.exists():
                plan_path = p
                found = True
                break
        
        if not found:
            print("ERROR: Could not locate plan.md. Ensure you are in the project root or specify --path.")
            return 1

    try:
        content = load_plan_content(plan_path)
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        return 1

    # Validate Citations
    citations_valid, missing_citations = validate_citations(content, REQUIRED_CITATION_PATTERNS)
    if not citations_valid:
        print("❌ Citation Validation Failed:")
        for pattern in missing_citations:
            print(f"   - Missing reference to: {pattern}")
        print("\nConstitution Principle II requires explicit citations to foundational works (Kandel, Krakauer, etc.) and data sources.")
        return 1

    # Validate File References
    refs_valid, missing_refs = validate_plan_references(content, REQUIRED_FILE_REFS)
    if not refs_valid:
        print("❌ File Reference Validation Failed:")
        for pattern in missing_refs:
            print(f"   - Missing reference to: {pattern}")
        print("\nConstitution Principle II requires references to core specification artifacts.")
        return 1

    print("✅ Constitution Principle II Validation Passed.")
    print(f"   - Verified citations for: {', '.join(REQUIRED_CITATION_PATTERNS)}")
    print(f"   - Verified file references for: {', '.join(REQUIRED_FILE_REFS)}")
    return 0


def main():
    """Command-line entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate plan.md for Constitution Principle II")
    parser.add_argument("--path", type=Path, help="Path to plan.md")
    args = parser.parse_args()

    exit_code = pre_commit_hook(args.path)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()