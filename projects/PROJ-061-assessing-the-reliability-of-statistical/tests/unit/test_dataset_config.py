import pytest
from code.config import verify_dataset_distribution, DATASET_LIST

def test_dataset_distribution():
    """Test that the dataset list has the correct distribution."""
    assert verify_dataset_distribution() is True, "Dataset distribution is incorrect."
    
def test_dataset_count():
    """Test the total number of datasets."""
    assert len(DATASET_LIST) == 10, "There should be exactly 10 datasets."

def test_dataset_types():
    """Test that all datasets have a valid outcome_type."""
    valid_types = {"continuous", "count", "binary"}
    for ds in DATASET_LIST:
        assert ds.get("outcome_type") in valid_types, f"Invalid outcome_type for {ds['id']}"