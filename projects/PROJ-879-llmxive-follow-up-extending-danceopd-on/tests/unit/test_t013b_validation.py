import pytest
import pandas as pd
import numpy as np
import json
import tempfile
import os
from pathlib import Path

# Import the functions we are testing
# Assuming the module is code/00_data_extraction.py
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from utils.config import get_config
# We need to import the specific functions. Since they are in 00_data_extraction.py
# we import them directly.
from importlib import import_module
import importlib.util

# Load the module dynamically to avoid import conflicts if needed
spec = importlib.util.spec_from_file_location("data_extraction", os.path.join(os.path.dirname(__file__), '..', '..', 'code', '00_data_extraction.py'))
de_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(de_module)

validate_routing_labels = de_module.validate_routing_labels
filter_valid_rows = de_module.filter_valid_rows
write_exclusion_log = de_module.write_exclusion_log
get_known_expert_ids = de_module.get_known_expert_ids

class TestT013bValidation:
    
    def test_get_known_expert_ids(self):
        """Test that known expert IDs are returned correctly."""
        ids = get_known_expert_ids()
        assert isinstance(ids, list)
        assert len(ids) > 0
        # Check that they are strings
        for id in ids:
            assert isinstance(id, str)
            assert id.startswith("expert_") or "expert" in id

    def test_validate_routing_labels_all_valid(self):
        """Test validation when all labels are valid."""
        known_ids = ["expert_a", "expert_b"]
        df = pd.DataFrame({
            "routing_label": ["expert_a", "expert_b", "expert_a"]
        })
        
        mask = validate_routing_labels(df, known_ids)
        
        assert all(mask)
        assert len(mask) == 3

    def test_validate_routing_labels_some_invalid(self):
        """Test validation when some labels are invalid."""
        known_ids = ["expert_a", "expert_b"]
        df = pd.DataFrame({
            "routing_label": ["expert_a", "expert_c", "expert_b", "undefined"]
        })
        
        mask = validate_routing_labels(df, known_ids)
        
        # First and third should be True, second and fourth False
        expected = [True, False, True, False]
        assert list(mask) == expected

    def test_validate_routing_labels_all_invalid(self):
        """Test validation when all labels are invalid."""
        known_ids = ["expert_a", "expert_b"]
        df = pd.DataFrame({
            "routing_label": ["expert_c", "expert_d", "expert_e"]
        })
        
        mask = validate_routing_labels(df, known_ids)
        
        assert not any(mask)
        assert len(mask) == 3

    def test_filter_valid_rows(self):
        """Test that filter_valid_rows correctly removes invalid rows."""
        known_ids = ["expert_a", "expert_b"]
        df = pd.DataFrame({
            "routing_label": ["expert_a", "expert_c", "expert_b"],
            "value": [1, 2, 3]
        })
        
        mask = validate_routing_labels(df, known_ids)
        filtered_df = filter_valid_rows(df, mask)
        
        assert len(filtered_df) == 2
        assert list(filtered_df['routing_label']) == ["expert_a", "expert_b"]
        assert list(filtered_df['value']) == [1, 3]

    def test_write_exclusion_log(self):
        """Test that exclusion log is written correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = os.path.join(tmpdir, "exclusion_log.json")
            count = 5
            reason = "test_reason"
            
            write_exclusion_log(count, reason, log_path)
            
            assert os.path.exists(log_path)
            
            with open(log_path, 'r') as f:
                log_data = json.load(f)
            
            assert log_data['count'] == count
            assert log_data['reason'] == reason
            assert 'timestamp' in log_data

    def test_integration_validation_and_filtering(self):
        """Integration test: validate and filter a mixed dataset."""
        known_ids = ["expert_text_to_image", "expert_editing"]
        
        # Create a dataset with 1000 valid rows and 100 invalid rows
        valid_labels = ["expert_text_to_image"] * 500 + ["expert_editing"] * 500
        invalid_labels = ["undefined_path"] * 100
        
        all_labels = valid_labels + invalid_labels
        # Shuffle to mix them (optional, but good for testing)
        np.random.seed(42)
        np.random.shuffle(all_labels)
        
        df = pd.DataFrame({
            "routing_label": all_labels,
            "other_data": range(1100)
        })
        
        mask = validate_routing_labels(df, known_ids)
        filtered_df = filter_valid_rows(df, mask)
        
        assert len(filtered_df) == 1000
        assert len(df) == 1100
        
        # Check that all labels in filtered_df are valid
        assert all(filtered_df['routing_label'].isin(known_ids))

    def test_empty_dataframe(self):
        """Test validation on an empty dataframe."""
        known_ids = ["expert_a"]
        df = pd.DataFrame(columns=["routing_label"])
        
        mask = validate_routing_labels(df, known_ids)
        
        assert len(mask) == 0
        assert mask.sum() == 0

    def test_unknown_label_not_in_known_ids(self):
        """Test that a completely unknown label is filtered out."""
        known_ids = ["expert_a", "expert_b"]
        df = pd.DataFrame({
            "routing_label": ["expert_unknown"]
        })
        
        mask = validate_routing_labels(df, known_ids)
        
        assert mask.sum() == 0