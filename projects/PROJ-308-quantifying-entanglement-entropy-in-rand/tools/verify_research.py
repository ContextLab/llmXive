"""
Verification script for research.md
Ensures the research document contains all required sections and content.
"""
import os
import sys
from pathlib import Path
from typing import Optional

# Add project root to path for imports
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from code.verify_research import verify_research_file, ResearchVerificationError

def main():
    """Main entry point for the verification script."""
    # Default path relative to project root
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