"""
Research File Verification Module.

This module provides functionality to verify the existence and readability
of the research document required for the project.
"""
import os
from pathlib import Path
from typing import Optional


class ResearchVerificationError(Exception):
    """Custom exception for research verification failures."""
    pass


def verify_research_file(file_path: Optional[str] = None) -> bool:
    """
    Verify that the research file exists and is readable.

    This function checks for the existence of the research.md file at the
    specified path (or the default project path if none is provided).
    It also verifies that the file is readable.

    Args:
        file_path: Optional path to the research file. If None, uses the
                   default path: specs/PROJ-308-001-quantifying-entanglement/research.md

    Returns:
        bool: True if the file exists and is readable.

    Raises:
        ResearchVerificationError: If the file does not exist or is not readable.
    """
    if file_path is None:
        # Default path relative to project root
        project_root = Path(__file__).parent.parent
        file_path = project_root / "specs" / "PROJ-308-001-quantifying-entanglement" / "research.md"
    else:
        file_path = Path(file_path)

    if not file_path.exists():
        raise ResearchVerificationError(
            f"Research file not found: {file_path}. "
            "This file is required for the project. Please ensure Phase 0 (T000) "
            "has been completed to generate the research document."
        )

    if not os.access(file_path, os.R_OK):
        raise ResearchVerificationError(
            f"Research file exists but is not readable: {file_path}. "
            "Please check file permissions."
        )

    # Additional check: ensure file is not empty
    if file_path.stat().st_size == 0:
        raise ResearchVerificationError(
            f"Research file is empty: {file_path}. "
            "The file must contain the research document generated in Phase 0."
        )

    return True
