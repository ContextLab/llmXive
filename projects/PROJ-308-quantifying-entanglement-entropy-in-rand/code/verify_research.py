"""
Verification script for research.md
Ensures the research document contains all required sections and content.
"""
import os
import sys
from pathlib import Path
from typing import Optional

class ResearchVerificationError(Exception):
    """Custom exception for research verification failures."""
    pass

def verify_research_file(file_path: str) -> bool:
    """
    Verify that the research file exists and contains required sections.

    Args:
        file_path: Path to the research.md file

    Returns:
        True if verification passes, False otherwise

    Raises:
        ResearchVerificationError: If the file is missing or required content is absent
    """
    path = Path(file_path)

    # Check if file exists
    if not path.exists():
        raise ResearchVerificationError(f"Research file not found: {file_path}")

    # Read file content
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Required sections to check
    required_sections = [
        "Scaling Ansatz",
        "Hypothesis",
        "Refael-Moore",
        "Physical Review Letters",
        "207204",
        "c_{\\text{eff}}",
        "log L",
        "Area Law",
        "localized",
        "critical"
    ]

    missing_sections = []
    for section in required_sections:
        if section not in content:
            missing_sections.append(section)

    if missing_sections:
        raise ResearchVerificationError(
            f"Research file missing required sections: {', '.join(missing_sections)}"
        )

    # Verify specific patterns
    import re

    # Check for scaling ansatz pattern
    if not re.search(r'S\(L\).*=.*c.*log.*L', content, re.IGNORECASE):
        raise ResearchVerificationError("Scaling ansatz pattern not found")

    # Check for hypothesis pattern
    if not re.search(r'S\(L\).*propto.*L.*alpha', content, re.IGNORECASE):
        raise ResearchVerificationError("Hypothesis pattern not found")

    # Check for Refael-Moore citation
    if not re.search(r'Refael.*Moore.*Phys.*Rev.*Lett', content, re.IGNORECASE):
        raise ResearchVerificationError("Refael-Moore citation not found")

    print("Research verification passed successfully.")
    return True

def main():
    """Main entry point for the verification script."""
    # Default path
    default_path = "specs/PROJ-308-001-quantifying-entanglement/research.md"

    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    else:
        file_path = default_path

    try:
        verify_research_file(file_path)
        print(f"✓ Verification successful for: {file_path}")
        sys.exit(0)
    except ResearchVerificationError as e:
        print(f"✗ Verification failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
