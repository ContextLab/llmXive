"""
CLI entry point for verifying the existence and readability of the research document.

This script implements Task T013: Verify Research File.
It checks that `specs/PROJ-308-001-quantifying-entanglement/research.md` exists
and is readable. It aborts with a clear error if the file is missing or unreadable.
"""

import sys
from pathlib import Path

# Define the expected path relative to the project root
# The project root is assumed to be the directory containing 'code/', 'data/', etc.
RESEARCH_FILE_PATH = Path("specs/PROJ-308-001-quantifying-entanglement/research.md")

def verify_research_file():
    """
    Verify that the research file exists and is readable.
    
    Returns:
        bool: True if the file exists and is readable, False otherwise.
        
    Raises:
        FileNotFoundError: If the research file is missing.
        PermissionError: If the research file exists but is not readable.
    """
    if not RESEARCH_FILE_PATH.exists():
        raise FileNotFoundError(
            f"Research file missing: {RESEARCH_FILE_PATH}. "
            "Task T013 verification failed. "
            "Please ensure Phase 0 (T000) has generated the research.md file."
        )
    
    if not RESEARCH_FILE_PATH.is_file():
        raise FileNotFoundError(
            f"Path exists but is not a file: {RESEARCH_FILE_PATH}. "
            "Task T013 verification failed."
        )
    
    try:
        # Attempt to open and read the file to ensure readability
        with open(RESEARCH_FILE_PATH, 'r', encoding='utf-8') as f:
            content = f.read()
            if not content.strip():
                raise ValueError(f"Research file is empty: {RESEARCH_FILE_PATH}")
            print(f"✓ Research file verified: {RESEARCH_FILE_PATH} ({len(content)} bytes)")
            return True
    except PermissionError as e:
        raise PermissionError(
            f"Research file exists but is not readable: {RESEARCH_FILE_PATH}. "
            "Task T013 verification failed."
        ) from e
    except Exception as e:
        raise RuntimeError(
            f"Error reading research file: {RESEARCH_FILE_PATH}. {str(e)}"
        ) from e

def main():
    """Main entry point for the CLI."""
    try:
        verify_research_file()
        print("SUCCESS: Research file verification passed.")
        return 0
    except (FileNotFoundError, PermissionError, RuntimeError, ValueError) as e:
        print(f"FAILURE: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
