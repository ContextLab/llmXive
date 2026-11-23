"""
Test suite for llmXive Follow-up: Extending Improved Large Language Diffusion Models.

This package contains all unit, integration, and contract tests for the project.
Tests are organized by user story and component.
"""

import os
import sys

# Ensure the code root is in the path for imports during testing
code_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if code_root not in sys.path:
    sys.path.insert(0, code_root)
