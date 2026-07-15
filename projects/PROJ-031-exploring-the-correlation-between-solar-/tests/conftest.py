"""
Pytest configuration and shared fixtures for the project.
"""
import os
import sys
from pathlib import Path

# Ensure the code directory is in the Python path for imports
# This allows tests to import from code/ modules directly
PROJECT_ROOT = Path(__file__).resolve().parent
CODE_DIR = PROJECT_ROOT / "code"

if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))
