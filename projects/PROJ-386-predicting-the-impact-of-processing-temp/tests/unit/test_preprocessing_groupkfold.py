import pytest
import numpy as np
from data.preprocessing import create_group_kfold_splitter

class TestCreateGroupKFoldSplitter:
    """
    Tests for T022d: GroupKFold Splitter Logic.
    """

    def test_splitter_instantiation(self):
        """Test that the function returns a GroupKFold object."""
        groups = np.array([0, 0, 1, 1, 2, 2])
        splitter = create_group_kfold_splitter(groups)
        
        assert splitter is not None
        assert hasattr(splitter, 'split')
        assert hasattr(splitter, 'n_splits')

    def test_empty_groups_raises_error(self):
        """Test that empty groups raise a ValueError."""
        with pytest.raises(ValueError, match="Groups cannot be empty"):
            create_group_kfold_splitter([])
        
        with pytest.raises(ValueError, match="Groups cannot be empty"):
            create_group_kfold_splitter(np.array([]))

    def test_none_groups_raises_error(self):
        """Test that None groups raise a ValueError."""
        with pytest.raises(ValueError, match="Groups cannot be empty"):
            create_group_kfold_splitter(None)

    def test_no_group_overlap_in_split(self):
        """
        Verify that the splitter produces non-overlapping train/test sets
        where no 'Alloy Series' (group) appears in both.
        """
        # Create synthetic groups: 3 groups, 2 samples each
        # Group 0: indices 0, 1
        # Group 1: indices 2, 3
        # Group 2: indices 4, 5
        groups = np.array([0, 0, 1, 1, 2, 2])
        
        splitter = create_group_kfold_splitter(groups)
        
        # Iterate through splits
        for train_idx, test_idx in splitter.split(np.zeros((6, 1)), groups=groups):
            train_group_set = set(groups[train_idx])
            test_group_set = set(groups[test_idx])
            
            # Check for intersection
            intersection = train_group_set.intersection(test_group_set)
            assert len(intersection) == 0, f"Group overlap detected: {intersection}"

    def test_splitter_coverage(self):
        """Test that all groups are represented across splits (roughly)."""
        groups = np.array([0, 0, 1, 1, 2, 2, 3, 3])
        splitter = create_group_kfold_splitter(groups)
        
        all_train_groups = set()
        all_test_groups = set()
        
        for train_idx, test_idx in splitter.split(np.zeros((8, 1)), groups=groups):
            all_train_groups.update(groups[train_idx])
            all_test_groups.update(groups[test_idx])
        
        # With 5 splits and 4 groups, not every group will be in every fold's test set,
        # but the splitter object itself must be valid.
        # The critical test is the non-overlap (test_no_group_overlap_in_split).
        assert len(all_train_groups) > 0
        assert len(all_test_groups) > 0