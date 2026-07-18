"""
Pytest configuration and fixtures for integration tests.
"""
import os
import sys
from pathlib import Path

# Ensure code directory is in path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root / "code"))
