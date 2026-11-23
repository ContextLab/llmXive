import pytest
import os
import sys
import json
import csv
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path if running standalone
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from dataset.loader import (
    filter_progressive_constraints, 
    save_filtered_dataset, 
    verify_progressive_constraints,
    generate_synthetic_proxy
)
from config import Paths

class TestFilterLogic:
    
    def test_filter_excludes_less_than_five(self):
        """Test that tasks with < 5 constraints are excluded."""
        data = [
            {"task_id": "t1", "progressive_constraints": ["c1", "c2", "c3", "c4"]}, # 4
            {"task_id": "t2", "progressive_constraints": ["c1", "c2", "c3", "c4", "c5"]}, # 5
            {"task_id": "t3", "progressive_constraints": ["c1", "c2", "c3", "c4", "c5", "c6"]}, # 6
            {"task_id": "t4", "progressive_constraints": []}, # 0
        ]
        
        filtered = filter_progressive_constraints(data, min_constraints=5)
        
        assert len(filtered) == 2
        assert filtered[0]["task_id"] == "t2"
        assert filtered[1]["task_id"] == "t3"
        
    def test_constraint_count_calculation(self):
        """Test that constraint_count is correctly calculated as len(progressive_constraints)."""
        data = [
            {
                "task_id": "t1", 
                "progressive_constraints": ["c1", "c2", "c3", "c4", "c5", "c6", "c7"]
            }
        ]
        
        filtered = filter_progressive_constraints(data, min_constraints=5)
        
        assert len(filtered) == 1
        assert filtered[0]["constraint_count"] == 7
        assert filtered[0]["progressive_constraints"] == ["c1", "c2", "c3", "c4", "c5", "c6", "c7"]

    def test_filter_with_raw_prompt(self):
        """Test that raw_prompt is preserved."""
        data = [
            {
                "task_id": "t1",
                "raw_prompt": "This is a test prompt.",
                "progressive_constraints": ["c1", "c2", "c3", "c4", "c5"]
            }
        ]
        
        filtered = filter_progressive_constraints(data, min_constraints=5)
        
        assert len(filtered) == 1
        assert filtered[0]["raw_prompt"] == "This is a test prompt."

class TestSaveFilteredDataset:
    
    def test_save_creates_csv_with_correct_schema(self, tmp_path):
        """Test that save_filtered_dataset creates a CSV with the required columns."""
        data = [
            {
                "task_id": "t1",
                "raw_prompt": "Prompt 1",
                "progressive_constraints": ["c1", "c2", "c3", "c4", "c5"],
                "constraint_count": 5
            }
        ]
        
        output_path = tmp_path / "test_output.csv"
        save_filtered_dataset(data, output_path)
        
        assert output_path.exists()
        
        with open(output_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
            assert len(rows) == 1
            row = rows[0]
            
            # Check columns
            assert 'task_id' in row
            assert 'raw_prompt' in row
            assert 'progressive_constraints' in row
            assert 'constraint_count' in row
            
            # Check values
            assert row['task_id'] == 't1'
            assert row['raw_prompt'] == 'Prompt 1'
            assert row['constraint_count'] == '5'
            # Constraints should be a JSON string
            assert json.loads(row['progressive_constraints']) == ["c1", "c2", "c3", "c4", "c5"]

    def test_save_non_zero_row_count(self, tmp_path):
        """Test that the output file has non-zero rows if input is valid."""
        data = [
            {"task_id": f"t{i}", "raw_prompt": f"P{i}", "progressive_constraints": ["c"]*6, "constraint_count": 6}
            for i in range(10)
        ]
        
        output_path = tmp_path / "multi.csv"
        save_filtered_dataset(data, output_path)
        
        with open(output_path, 'r') as f:
            reader = csv.reader(f)
            header = next(reader)
            rows = list(reader)
            
            assert len(rows) == 10

class TestVerifyProgressiveConstraints:
    
    def test_verify_true(self):
        data = [{"task_id": "1", "progressive_constraints": []}]
        assert verify_progressive_constraints(data) is True
        
    def test_verify_false_missing_field(self):
        data = [{"task_id": "1", "other_field": []}]
        assert verify_progressive_constraints(data) is False
        
    def test_verify_false_empty_list(self):
        data = []
        assert verify_progressive_constraints(data) is False

class TestSyntheticProxy:
    
    def test_proxy_generation(self, tmp_path):
        """Test that synthetic proxy is generated with correct structure."""
        output_path = tmp_path / "proxy.jsonl"
        data = generate_synthetic_proxy(output_path)
        
        assert len(data) == 100
        assert output_path.exists()
        
        # Check structure of first item
        item = data[0]
        assert "task_id" in item
        assert "raw_prompt" in item
        assert "progressive_constraints" in item
        assert "metadata" in item
        
        # Check constraints count is between 3 and 8
        count = len(item["progressive_constraints"])
        assert 3 <= count <= 8

if __name__ == "__main__":
    pytest.main([__file__, "-v"])