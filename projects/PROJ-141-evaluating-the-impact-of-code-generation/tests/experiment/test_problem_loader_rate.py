"""
Test suite for problem loading rate verification (T015a).
Tests FR-001: ≥95% problem loading rate.
"""
import pytest
import os
import sys
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
from experiment.problem_loader import verify_loading_rate, load_all_problems, SAMPLE_SIZE

class TestProblemLoadingRate:
    """Tests for problem loading rate verification."""
    
    def test_verify_loading_rate_with_real_data(self, tmp_path):
        """
        Test that verify_loading_rate works with real dataset structure.
        This test creates a mock dataset and verifies the rate calculation.
        """
        # Create mock dataset structure
        humaneval_dir = tmp_path / "data" / "humaneval"
        humaneval_dir.mkdir(parents=True)
        
        # Create valid HumanEval problems
        valid_problems = []
        for i in range(100):
            valid_problems.append({
                'task': f"Task {i}",
                'prompt': f"Problem description {i}",
                'canonical_solution': f"def solution_{i}(): pass"
            })
        
        # Add a few invalid problems to simulate real-world issues
        valid_problems.append({
            'task': "Task 100",
            # Missing prompt - should fail
        })
        
        # Save to JSON
        json_path = humaneval_dir / "human_eval.json"
        with open(json_path, 'w') as f:
            json.dump(valid_problems, f)
        
        # Mock the path
        with patch('experiment.problem_loader.HUMAN_EVAL_DIR', humaneval_dir):
            # Run verification with small sample
            rate, successes, total = verify_loading_rate(sample_size=50)
            
            # Should have high success rate (at least 49/50 = 98%)
            assert rate >= 0.95, f"Success rate {rate} is below 95% threshold"
            assert successes >= 49, f"Expected at least 49 successes, got {successes}"
            assert total == 50, f"Expected 50 total attempts, got {total}"
    
    def test_verify_loading_rate_empty_dataset(self, tmp_path):
        """Test behavior when dataset is empty."""
        humaneval_dir = tmp_path / "data" / "humaneval"
        humaneval_dir.mkdir(parents=True)
        
        # Create empty JSON file
        json_path = humaneval_dir / "human_eval.json"
        with open(json_path, 'w') as f:
            json.dump([], f)
        
        with patch('experiment.problem_loader.HUMAN_EVAL_DIR', humaneval_dir):
            with patch('experiment.problem_loader.CODEFORCES_DIR', tmp_path / "data" / "codeforces"):
                with pytest.raises(FileNotFoundError):
                    verify_loading_rate()
    
    def test_verify_loading_rate_mixed_validity(self, tmp_path):
        """Test with a mix of valid and invalid problems."""
        humaneval_dir = tmp_path / "data" / "humaneval"
        humaneval_dir.mkdir(parents=True)
        
        # Create 90 valid, 10 invalid problems
        problems = []
        for i in range(90):
            problems.append({
                'task': f"Valid {i}",
                'prompt': f"Valid prompt {i}",
                'canonical_solution': f"def sol_{i}(): pass"
            })
        
        for i in range(90, 100):
            problems.append({
                'task': f"Invalid {i}",
                # Missing required fields
            })
        
        json_path = humaneval_dir / "human_eval.json"
        with open(json_path, 'w') as f:
            json.dump(problems, f)
        
        with patch('experiment.problem_loader.HUMAN_EVAL_DIR', humaneval_dir):
            with patch('experiment.problem_loader.CODEFORCES_DIR', tmp_path / "data" / "codeforces"):
                # Sample all 100 problems
                rate, successes, total = verify_loading_rate(sample_size=100)
                
                # Expected: 90/100 = 90% success rate
                assert rate == 0.90, f"Expected 90% success rate, got {rate}"
                assert successes == 90
                assert total == 100
    
    def test_verify_loading_rate_threshold_boundary(self, tmp_path):
        """Test exact boundary at 95% threshold."""
        humaneval_dir = tmp_path / "data" / "humaneval"
        humaneval_dir.mkdir(parents=True)
        
        # Create exactly 95 valid, 5 invalid problems
        problems = []
        for i in range(95):
            problems.append({
                'task': f"Valid {i}",
                'prompt': f"Valid prompt {i}",
                'canonical_solution': f"def sol_{i}(): pass"
            })
        
        for i in range(95, 100):
            problems.append({
                'task': f"Invalid {i}",
            })
        
        json_path = humaneval_dir / "human_eval.json"
        with open(json_path, 'w') as f:
            json.dump(problems, f)
        
        with patch('experiment.problem_loader.HUMAN_EVAL_DIR', humaneval_dir):
            with patch('experiment.problem_loader.CODEFORCES_DIR', tmp_path / "data" / "codeforces"):
                rate, successes, total = verify_loading_rate(sample_size=100)
                
                assert rate == 0.95, f"Expected exactly 95% success rate, got {rate}"
                assert successes == 95
                assert total == 100

if __name__ == "__main__":
    pytest.main([__file__, "-v"])