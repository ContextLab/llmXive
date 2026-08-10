"""
Tests package for llmXive Follow-up: Extending Improved Large Language Diffusion Models.

This package contains all unit, integration, and contract tests for the project.
Tests are organized by user story and feature area.
"""

import os
import sys
from pathlib import Path

# Ensure the code root is in the path for imports
code_root = Path(__file__).parent.parent
if str(code_root) not in sys.path:
    sys.path.insert(0, str(code_root))

__all__ = []
