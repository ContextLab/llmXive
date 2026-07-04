"""
Test suite for the Atmospheric River Gravity Correlation project.

This package contains contract tests, integration tests, and unit tests
for validating the data pipeline, statistical analysis, and visualization
components of the research.
"""

# Import common test utilities if needed
from pathlib import Path

# Define project root for test data access
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
CODE_DIR = PROJECT_ROOT / "code"
OUTPUT_DIR = PROJECT_ROOT / "output"
CONTRACTS_DIR = PROJECT_ROOT / "contracts"

__all__ = ["PROJECT_ROOT", "DATA_DIR", "CODE_DIR", "OUTPUT_DIR", "CONTRACTS_DIR"]
