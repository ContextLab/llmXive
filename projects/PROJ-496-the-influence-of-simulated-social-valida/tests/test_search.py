"""
Tests for the dataset search and categorization logic (User Story 1).
"""
import pytest
from pathlib import Path
import sys
import json
from unittest.mock import patch, MagicMock

# Ensure we can import from the project code directory
# The test runner or CI should set the path, but we add a fallback for local execution
# Project root is 2 levels up from tests/test_search.py
project_root = Path(__file__).parent.parent
code_dir = project_root / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from search import categorize_dataset, search_openneuro


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


@patch('search.requests.post')
def test_integration_openneuro_api_query(mock_post):
    """
    Integration test for OpenNeuro API query logic.
    Mocks the API response to verify the search function correctly parses
    and returns dataset candidates.
    """
    # Mock API response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "data": {
            "datasets": [
                {
                    "id": "ds000001",
                    "label": "Social EEG Study",
                    "description": "A study on social feedback and anxiety.",
                    "task": ["feedback"]
                },
                {
                    "id": "ds000002",
                    "label": "Memory Task",
                    "description": "Simple memory task.",
                    "task": ["memory"]
                }
            ]
        }
    }
    mock_post.return_value = mock_response

    # Execute search
    results = search_openneuro(
        modalities=["EEG"],
        keywords=["social", "anxiety"]
    )

    # Verify API was called
    mock_post.assert_called_once()

    # Verify results contain the expected dataset (ds000001)
    assert len(results) >= 1
    dataset_ids = [d["id"] for d in results]
    assert "ds000001" in dataset_ids, "Expected ds000001 in results"
    assert "ds000002" not in dataset_ids, "ds000002 should not be in results (no social/anxiety)"

    # Verify structure of returned item
    found_ds = next(d for d in results if d["id"] == "ds000001")
    assert found_ds["label"] == "Social EEG Study"
    assert "description" in found_ds