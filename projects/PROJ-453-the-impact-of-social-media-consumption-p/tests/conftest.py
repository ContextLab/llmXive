"""
Pytest configuration and fixtures.
"""
import os
import sys
from pathlib import Path

# Ensure the project root is in the path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pytest

@pytest.fixture
def sample_text_with_causal_language():
    return "This variable causes the outcome and leads to significant impacts."

@pytest.fixture
def sample_text_clean():
    return "This variable is associated with the outcome."

@pytest.fixture
def forbidden_words():
    return ["causes", "leads to", "impacts", "results in"]