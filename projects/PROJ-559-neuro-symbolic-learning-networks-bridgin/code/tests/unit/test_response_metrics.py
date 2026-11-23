import pytest
import os
import sys
import json
import tempfile
import shutil
import pandas as pd
from typing import List, Dict, Any

# Add code directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from simulate.response_metrics import (
    simulate_response_time,
    simulate_comprehension_rating,
    validate_response_time_distribution,
    generate_response_metrics
)

class TestResponseTimeSimulation:
    """Tests for response time simulation logic."""

    def test_simulate_response_time_bounds(self):
        """Test that response times stay within specified bounds."""
        for _ in range(100):
            rt = simulate_response_time(base_time=5.0, std_dev=1.0, min_time=1.0, max_time=10.0)
            assert 1.0 <= rt <= 10.0, f"Response time {rt} out of bounds"

    def test_simulate_response_time_distribution(self):
        """Test that response times follow expected distribution."""
        times = [simulate_response_time(base_time=5.0, std_dev=1.0) for _ in range(1000)]
        mean_rt = sum(times) / len(times)
        assert 4.0 <= mean_rt <= 6.0, f"Mean response time {mean_rt} not in expected range"

    def test_simulate_response_time_reproducibility(self):
        """Test that response time simulation is reproducible with seed."""
        rt1 = simulate_response_time(base_time=5.0, seed=42)
        rt2 = simulate_response_time(base_time=5.0, seed=42)
        assert rt1 == rt2, "Response time simulation not reproducible with seed"

class TestComprehensionRatingSimulation:
    """Tests for comprehension rating simulation logic."""

    def test_simulate_comprehension_rating_range(self):
        """Test that comprehension ratings are within 1-5."""
        for _ in range(100):
            rating = simulate_comprehension_rating()
            assert 1 <= rating <= 5, f"Rating {rating} out of range"

    def test_simulate_comprehension_rating_distribution(self):
        """Test that comprehension ratings follow expected distribution."""
        ratings = [simulate_comprehension_rating() for _ in range(1000)]
        # Check that higher ratings are more common
        avg_rating = sum(ratings) / len(ratings)
        assert 3.0 <= avg_rating <= 4.0, f"Average rating {avg_rating} not in expected range"

    def test_simulate_comprehension_rating_reproducibility(self):
        """Test that comprehension rating simulation is reproducible with seed."""
        rating1 = simulate_comprehension_rating(seed=42)
        rating2 = simulate_comprehension_rating(seed=42)
        assert rating1 == rating2, "Comprehension rating simulation not reproducible with seed"

class TestResponseTimeDistributionValidation:
    """Tests for response time distribution validation."""

    def test_validate_distribution_no_gaps(self):
        """Test validation with no gaps > 5s."""
        times = [1.0, 2.0, 3.0, 4.0, 5.0]
        is_valid, stats = validate_response_time_distribution(times, max_gap=5.0)
        assert is_valid, "Valid distribution marked as invalid"
        assert stats['max_observed_gap'] <= 5.0

    def test_validate_distribution_with_gaps(self):
        """Test validation with gaps > 5s."""
        times = [1.0, 2.0, 10.0, 11.0]  # Gap of 8.0 between 2.0 and 10.0
        is_valid, stats = validate_response_time_distribution(times, max_gap=5.0)
        assert not is_valid, "Invalid distribution marked as valid"
        assert stats['max_observed_gap'] > 5.0

    def test_validate_distribution_empty(self):
        """Test validation with empty list."""
        is_valid, stats = validate_response_time_distribution([], max_gap=5.0)
        assert not is_valid
        assert 'error' in stats

class TestGenerateResponseMetrics:
    """Tests for the main response metrics generation function."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.input_path = os.path.join(self.temp_dir, 'input_logs.csv')
        self.output_path = os.path.join(self.temp_dir, 'output_logs.csv')
        
        # Create sample simulation logs
        sample_logs = [
            {'student_id': 'STU-001', 'condition': 'neural', 'problem_id': 'P1', 'correct': 1},
            {'student_id': 'STU-002', 'condition': 'symbolic', 'problem_id': 'P1', 'correct': 0},
            {'student_id': 'STU-003', 'condition': 'neuro_symbolic', 'problem_id': 'P1', 'correct': 1}
        ]
        df = pd.DataFrame(sample_logs)
        df.to_csv(self.input_path, index=False)

    def teardown_method(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)

    def test_generate_metrics_creates_output(self):
        """Test that generate_response_metrics creates output file."""
        df = pd.read_csv(self.input_path)
        logs = df.to_dict('records')
        output_path = generate_response_metrics(logs, self.output_path, seed=42)
        
        assert os.path.exists(output_path), "Output file not created"
        assert os.path.exists(self.output_path), "Output file not created at expected path"

    def test_generate_metrics_adds_fields(self):
        """Test that response times and comprehension ratings are added."""
        df = pd.read_csv(self.input_path)
        logs = df.to_dict('records')
        generate_response_metrics(logs, self.output_path, seed=42)
        
        result_df = pd.read_csv(self.output_path)
        assert 'rt_seconds' in result_df.columns, "rt_seconds column missing"
        assert 'comprehension_rating' in result_df.columns, "comprehension_rating column missing"

    def test_generate_metrics_validation_file(self):
        """Test that validation stats file is created."""
        df = pd.read_csv(self.input_path)
        logs = df.to_dict('records')
        generate_response_metrics(logs, self.output_path, seed=42)
        
        validation_path = self.output_path.replace('.csv', '_validation.json')
        assert os.path.exists(validation_path), "Validation stats file not created"
        
        with open(validation_path, 'r') as f:
            stats = json.load(f)
        
        assert 'max_observed_gap' in stats
        assert 'mean_rt' in stats
        assert 'is_valid' in stats

    def test_generate_metrics_distribution_constraint(self):
        """Test that distribution constraint is checked."""
        df = pd.read_csv(self.input_path)
        logs = df.to_dict('records')
        generate_response_metrics(logs, self.output_path, seed=42)
        
        validation_path = self.output_path.replace('.csv', '_validation.json')
        with open(validation_path, 'r') as f:
            stats = json.load(f)
        
        # The generated data should satisfy the constraint (no gaps > 5s)
        assert stats['is_valid'], "Generated data violates distribution constraint"

    def test_generate_metrics_reproducibility(self):
        """Test that generation is reproducible with seed."""
        df = pd.read_csv(self.input_path)
        logs = df.to_dict('records')
        
        generate_response_metrics(logs, self.output_path, seed=42)
        result1 = pd.read_csv(self.output_path)
        
        # Remove output file
        os.remove(self.output_path)
        if os.path.exists(self.output_path.replace('.csv', '_validation.json')):
            os.remove(self.output_path.replace('.csv', '_validation.json'))
        
        generate_response_metrics(logs, self.output_path, seed=42)
        result2 = pd.read_csv(self.output_path)
        
        # Compare
        pd.testing.assert_frame_equal(result1, result2)