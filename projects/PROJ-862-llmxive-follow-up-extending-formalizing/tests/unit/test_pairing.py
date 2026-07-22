import pytest
import json
import os
import tempfile
from code.data_loader import pair_questions_by_task_type, save_pairing_config, load_pairing_config

class TestPairingLogic:
    def test_pair_questions_sequential(self):
        """Test sequential pairing of items within a task type."""
        grouped_data = [
            {
                "task_type": "math",
                "items": [
                    {"id": 1, "question": "What is 2+2?"},
                    {"id": 2, "question": "What is 3+3?"},
                    {"id": 3, "question": "What is 4+4?"},
                    {"id": 4, "question": "What is 5+5?"}
                ]
            }
        ]
        
        result = pair_questions_by_task_type(grouped_data, pair_strategy="sequential")
        
        assert len(result["pairs"]) == 2
        assert result["metadata"]["total_pairs"] == 2
        
        # Check first pair
        pair_0 = result["pairs"][0]
        assert pair_0["pair_id"] == "pair_000000"
        assert pair_0["task_type"] == "math"
        assert pair_0["item_a"]["id"] == 1
        assert pair_0["item_b"]["id"] == 2
        
        # Check second pair
        pair_1 = result["pairs"][1]
        assert pair_1["pair_id"] == "pair_000001"
        assert pair_1["item_a"]["id"] == 3
        assert pair_1["item_b"]["id"] == 4

    def test_pair_questions_multiple_types(self):
        """Test pairing across multiple task types."""
        grouped_data = [
            {
                "task_type": "math",
                "items": [
                    {"id": 1, "q": "A"},
                    {"id": 2, "q": "B"}
                ]
            },
            {
                "task_type": "logic",
                "items": [
                    {"id": 3, "q": "C"},
                    {"id": 4, "q": "D"},
                    {"id": 5, "q": "E"},
                    {"id": 6, "q": "F"}
                ]
            }
        ]
        
        result = pair_questions_by_task_type(grouped_data)
        
        assert result["metadata"]["total_pairs"] == 3
        assert result["metadata"]["task_type_stats"]["math"]["pairs_created"] == 1
        assert result["metadata"]["task_type_stats"]["logic"]["pairs_created"] == 2

    def test_save_and_load_pairing_config(self):
        """Test saving and loading pairing config to/from JSON."""
        grouped_data = [
            {
                "task_type": "test",
                "items": [
                    {"id": 1},
                    {"id": 2}
                ]
            }
        ]
        pairs_result = pair_questions_by_task_type(grouped_data)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "pairing_config.json")
            save_pairing_config(pairs_result, output_path)
            
            assert os.path.exists(output_path)
            
            loaded = load_pairing_config(output_path)
            
            assert loaded["metadata"]["total_pairs"] == 1
            assert loaded["pairs"][0]["pair_id"] == "pair_000000"

    def test_odd_number_of_items(self):
        """Test behavior when a task type has an odd number of items."""
        grouped_data = [
            {
                "task_type": "odd",
                "items": [
                    {"id": 1},
                    {"id": 2},
                    {"id": 3}
                ]
            }
        ]
        
        result = pair_questions_by_task_type(grouped_data)
        
        # Should only pair the first two, leaving the third unpaired
        assert result["metadata"]["total_pairs"] == 1
        assert result["pairs"][0]["item_a"]["id"] == 1
        assert result["pairs"][0]["item_b"]["id"] == 2
