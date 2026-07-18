"""
Pytest configuration and fixtures for the project.
"""
import sys
from pathlib import Path

# Ensure the project root is in the path for all tests
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Optional: Add common fixtures here if needed across all test suites