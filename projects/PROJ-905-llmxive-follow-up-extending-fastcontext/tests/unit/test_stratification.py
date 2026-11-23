import csv
import os
import tempfile
from pathlib import Path

import pytest

# Import the function under test from the project's code module
from code.stratification import split_repos

# Fixture: sample_scores_csv
# Creates a temporary CSV file with n=10 rows, scores ranging from low to high
@pytest.fixture
def sample_scores_csv():
    """
    Creates a temporary CSV file with 10 repositories and varying regularity scores.
    The scores are designed to range from low to high to test the 50/50 split logic.
    """
    data = [
        {"repo_id": "repo_001", "regularity_score": 0.10},
        {"repo_id": "repo_002", "regularity_score": 0.20},
        {"repo_id": "repo_003", "regularity_score": 0.30},
        {"repo_id": "repo_004", "regularity_score": 0.40},
        {"repo_id": "repo_005", "regularity_score": 0.50},
        {"repo_id": "repo_006", "regularity_score": 0.60},
        {"repo_id": "repo_007", "regularity_score": 0.70},
        {"repo_id": "repo_008", "regularity_score": 0.80},
        {"repo_id": "repo_009", "regularity_score": 0.90},
        {"repo_id": "repo_010", "regularity_score": 1.00},
    ]

    # Create a temporary file
    temp_fd, temp_path = tempfile.mkstemp(suffix=".csv")
    try:
        with os.fdopen(temp_fd, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["repo_id", "regularity_score"])
            writer.writeheader()
            writer.writerows(data)
        yield temp_path
    finally:
        # Cleanup: remove the temporary file after the test
        if os.path.exists(temp_path):
            os.remove(temp_path)

class TestStratification:
    def test_stratification_splits_50_50_by_regular_score(
        self, sample_scores_csv
    ):
        """
        Test that split_repos correctly divides the dataset into two equal halves
        based on the regularity_score.
        
        Given a CSV with 10 repositories:
        - The top 5 (scores 0.60 to 1.00) should be in the 'regular' set.
        - The bottom 5 (scores 0.10 to 0.50) should be in the 'irregular' set.
        """
        # Call the function
        regular_set, irregular_set = split_repos(sample_scores_csv)

        # Assert that both sets are lists
        assert isinstance(regular_set, list)
        assert isinstance(irregular_set, list)

        # Assert that the split is 50/50 (n=10 -> 5 and 5)
        assert len(regular_set) == 5, f"Expected 5 regular repos, got {len(regular_set)}"
        assert len(irregular_set) == 5, f"Expected 5 irregular repos, got {len(irregular_set)}"

        # Verify the content of the sets
        # Extract repo_ids for easier checking
        regular_ids = [item["repo_id"] for item in regular_set]
        irregular_ids = [item["repo_id"] for item in irregular_set]

        # The top 5 scores (0.60, 0.70, 0.80, 0.90, 1.00) correspond to repo_006 to repo_010
        expected_regular_ids = ["repo_006", "repo_007", "repo_008", "repo_009", "repo_010"]
        
        # The bottom 5 scores (0.10, 0.20, 0.30, 0.40, 0.50) correspond to repo_001 to repo_005
        expected_irregular_ids = ["repo_001", "repo_002", "repo_003", "repo_004", "repo_005"]

        # Check that the sets contain the correct repositories
        # Using set equality to ignore order if the implementation sorts differently,
        # though split_repos usually preserves order or sorts by score.
        assert set(regular_ids) == set(expected_regular_ids), \
            f"Regular set mismatch. Expected {expected_regular_ids}, got {regular_ids}"
        
        assert set(irregular_ids) == set(expected_irregular_ids), \
            f"Irregular set mismatch. Expected {expected_irregular_ids}, got {irregular_ids}"

        # Verify that no repo is in both sets
        assert len(set(regular_ids).intersection(set(irregular_ids))) == 0, \
            "A repository cannot be in both the regular and irregular sets."

        # Verify that the union of both sets equals the total input count
        assert len(set(regular_ids).union(set(irregular_ids))) == 10, \
            "The union of regular and irregular sets must contain all input repositories."