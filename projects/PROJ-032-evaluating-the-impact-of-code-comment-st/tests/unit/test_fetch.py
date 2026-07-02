"""
Unit tests for the fetch module (User Story 1).
Specifically tests T010a and T010b regarding candidate retrieval and fallback logic.
"""
import pytest
import sys
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

# Ensure the code directory is in the path for imports
project_root = Path(__file__).resolve().parent.parent.parent
code_path = project_root / "code"
if str(code_path) not in sys.path:
    sys.path.insert(0, str(code_path))

# Import the function to be tested
# We assume fetch.py exists as per T012 implementation context.
# If T012 is not yet done, this import will fail, which is expected behavior 
# until the implementation task is completed.
try:
    from fetch import get_candidates
except ImportError:
    # In a strict CI environment, we might want to fail hard here.
    # However, for the purpose of this test file existence, we define a stub 
    # that will be replaced by the real module when T012 is run.
    # This allows the test file to be syntactically valid and loadable.
    def get_candidates():
        return []

class TestGetCandidates:
    """Tests for the get_candidates function."""

    @patch('fetch.requests.get')
    def test_get_candidates_returns_ids(self, mock_get):
        """
        T010a: Verify that get_candidates returns a list of repository IDs.
        This test mocks the HuggingFace API response to ensure the function
        correctly parses and returns a list of 500 candidate IDs.
        """
        # Mock the API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        
        # Simulate a list of 500 repo objects from HuggingFace
        # The API usually returns a list of dicts with 'id' or 'repo_id'
        mock_data = [{"id": f"repo_{i}", "stars": 150} for i in range(500)]
        mock_response.json.return_value = mock_data
        
        mock_get.return_value = mock_response

        # Call the function
        result = get_candidates()

        # Assertions
        assert isinstance(result, list), "Result should be a list"
        assert len(result) == 500, f"Expected 500 candidates, got {len(result)}"
        
        # Verify all items are strings (IDs)
        for item in result:
            assert isinstance(item, str), f"Expected string ID, got {type(item)}"
            assert item.startswith("repo_"), f"ID format unexpected: {item}"

        # Verify the correct URL was called (optional but good practice)
        mock_get.assert_called_once()

    @patch('fetch.requests.get')
    def test_get_candidates_fallback(self, mock_get):
        """
        T010b: Verify that get_candidates falls back to a local list if the API is unreachable.
        
        This test simulates a network failure (e.g., ConnectionError or generic Exception)
        when calling the HuggingFace API and asserts that the function catches the error
        and returns a valid fallback list of candidate IDs instead of crashing.
        """
        # Mock a network error to simulate unreachable API
        mock_get.side_effect = Exception("Connection refused: Unable to reach HuggingFace API")

        # Call the function
        # We expect this to NOT raise an exception but return a fallback list
        result = get_candidates()

        # Assertions: 
        # 1. Result must be a list
        assert isinstance(result, list), "Fallback result should be a list"
        
        # 2. The fallback logic (in fetch.py) should return a non-empty list of at least one candidate
        #    to ensure the pipeline can proceed with some data, even if not the full 500.
        #    The task description says "Return list of 500 candidate IDs" on success, 
        #    but on fallback it implies a local list. We assert it's a list of strings.
        assert len(result) > 0, "Fallback list should contain at least one candidate ID"
        
        for item in result:
            assert isinstance(item, str), f"Fallback item must be a string ID, got {type(item)}"

    def test_get_candidates_handles_empty_response(self):
        """
        Test that an empty API response returns an empty list.
        """
        with patch('fetch.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = []
            mock_get.return_value = mock_response

            result = get_candidates()

            assert result == []
            assert isinstance(result, list)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])