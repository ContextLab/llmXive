"""
Integration test for the full SN1 rate constant prediction pipeline.
This test verifies the end-to-end flow of the entire pipeline.

Note: This is a duplicate of code/tests/integration/test_full_pipeline.py
to satisfy the test path convention.
"""
import pytest
import sys
from pathlib import Path

# Import the actual test from code directory
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from tests.integration.test_full_pipeline import TestFullPipeline

# Re-export the test class
TestFullPipeline = TestFullPipeline