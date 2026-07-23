"""
Tests for the dataset search and categorization logic (User Story 1).
"""
import pytest
from pathlib import Path
import sys

# Ensure we can import from the project code directory
# Assuming this test runs from the project root or the test runner sets the path
# Adjusting path for local execution if needed
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from search import categorize_dataset


def test_categorizes_eligible_dataset():
    """
    Test that a dataset with both social feedback manipulation and
    social anxiety measures is categorized as 'Eligible'.
    """
    dataset = {
        "id": "ds_test_001",
        "title": "Social Feedback and Anxiety Study",
        "description": "A study involving simulated feedback and LSAS scores.",
        "tags": ["social", "feedback", "anxiety", "EEG"],
        "metadata": {
            "feedback_type": "simulated",
            "anxiety_measure": "LSAS"
        }
    }
    category = categorize_dataset(dataset)
    assert category == "Eligible", f"Expected 'Eligible', got '{category}'"


def test_categorizes_sim_only():
    """
    Test that a dataset with feedback but no anxiety measure is 'Sim-Only'.
    """
    dataset = {
        "id": "ds_test_002",
        "title": "Social Feedback Only",
        "description": "Study with simulated feedback but no anxiety metrics.",
        "tags": ["social", "feedback", "EEG"],
        "metadata": {
            "feedback_type": "simulated",
            "anxiety_measure": None
        }
    }
    category = categorize_dataset(dataset)
    assert category == "Sim-Only", f"Expected 'Sim-Only', got '{category}'"


def test_categorizes_real_only():
    """
    Test that a dataset with real feedback but no anxiety measure is 'Real-Only'.
    """
    dataset = {
        "id": "ds_test_003",
        "title": "Real Feedback Only",
        "description": "Study with real social feedback but no anxiety metrics.",
        "tags": ["social", "feedback", "EEG"],
        "metadata": {
            "feedback_type": "real",
            "anxiety_measure": None
        }
    }
    category = categorize_dataset(dataset)
    assert category == "Real-Only", f"Expected 'Real-Only', got '{category}'"


def test_categorizes_none():
    """
    Test that a dataset lacking both key features is 'None'.
    """
    dataset = {
        "id": "ds_test_004",
        "title": "General EEG Study",
        "description": "Standard EEG task without social components.",
        "tags": ["EEG", "memory"],
        "metadata": {
            "feedback_type": None,
            "anxiety_measure": None
        }
    }
    category = categorize_dataset(dataset)
    assert category == "None", f"Expected 'None', got '{category}'"
