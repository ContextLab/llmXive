"""
Pytest configuration and fixtures.
"""
import pytest
import sys
from pathlib import Path

# Ensure code directory is in path
sys.path.insert(0, str(Path(__file__).parent.parent))
