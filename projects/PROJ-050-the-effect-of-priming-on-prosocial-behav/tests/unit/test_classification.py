"""
Unit tests for the thread classification logic in code/01_ingest.py.
Verifies that the regex-based priming classification correctly identifies 
'Prime' vs 'Control' threads based on titles.
"""
import pytest
import sys
import importlib
from pathlib import Path

# Add project root to path to allow importing from the code package
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Using importlib because the module name '01_ingest' starts with a digit,
# which is a SyntaxError for standard 'import' statements.
ingest_module = importlib.import_module("code.01_ingest")
classify_thread = ingest_module.classify_thread

@pytest.mark.parametrize("title, expected", [
    ("Can you help me with this?", "Prime"),
    ("Thank you for the support!", "Prime"),
    ("I need some support with my project", "Prime"),
    ("Please take care of the environment", "Prime"),
    ("HELP ME NOW", "Prime"),  # Case-insensitivity check
    ("support and care for all", "Prime"),
    ("Just a random discussion about cats", "Control"),
    ("The weather is nice today", "Control"),
    ("A title without keywords", "Control"),
])
def test_classify_thread_text(title, expected):
    """Verify that specific keywords trigger 'Prime' classification."""
    assert classify_thread({"title": title}) == expected

def test_classify_thread_missing_title():
    """Verify that a record missing the 'title' key defaults to 'Control'."""
    assert classify_thread({}) == "Control"

def test_classify_thread_none_title():
    """Verify that a record with title=None defaults to 'Control'."""
    assert classify_thread({"title": None}) == "Control"

def test_classify_thread_non_string_title():
    """Verify that a non-string title defaults to 'Control'."""
    assert classify_thread({"title": 12345}) == "Control"
