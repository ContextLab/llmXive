"""
Unit tests for response metrics simulation module.
"""
import pytest
import os
import sys
import json
import tempfile
import shutil
import csv
import math
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / 'code'))

from simulate.response_metrics import (
    simulate_response_time,
    simulate_comprehension_rating,
    validate_response_time_distribution,
    generate_response_metrics
)

class TestResponseTimeSimulation:
    """Tests for response time simulation function."""

    def test_response_time_range(self):
        """Response times should be within valid bounds."""
        for _ in range(100):
            rt = simulate_response_time(0.5, 'neural', seed=42)
            assert 0.5 <= rt <= 60.0, f"Response time {rt} out of bounds"

    def test_response_time_by_condition(self):
        """Different conditions should produce different base times."""
        neural_rt = simulate_response_time(0.0, 'neural', seed=123)
        symbolic_rt = simulate_response_time(0.0, 'symbolic', seed=123)
        neuro_symbolic_rt = simulate_response_time(0.0, 'neuro_symbolic', seed=123)

        # Symbolic should generally be slower than neural
        assert symbolic_rt >= neural_rt - 1.0, "Symbolic should be slower"

    def test_response_time_difficulty(self):
        """Higher difficulty should increase response time."""
        rt_easy = simulate_response_time(0.1, 'neural', seed=456)
        rt_hard = simulate_response_time(0.9, 'neural', seed=456)

        assert rt_hard >= rt_easy, "Harder problems should take longer"

    def test_response_time_deterministic(self):
        """Same seed should produce same result."""
        rt1 = simulate_response_time(0.5, 'neural', seed=999)
        rt2 = simulate_response_time(0.5, 'neural', seed=999)
        assert rt1 == rt2, "Response time should be deterministic with same seed"

class TestComprehensionRatingSimulation:
    """Tests for comprehension rating simulation function."""

    def test_comprehension_range(self):
        """Comprehension ratings should be 1-5."""
        for _ in range(100):
            rating = simulate_comprehension_rating('neural', 0.5, seed=42)
            assert 1 <= rating <= 5, f"Rating {rating} out of bounds"

    def test_comprehension_by_condition(self):
        """Neuro-symbolic should have higher comprehension ratings."""
        neural_ratings = [simulate_comprehension_rating('neural', 0.5, seed=i) for i in range(100)]
        neuro_symbolic_ratings = [simulate_comprehension_rating('neuro_symbolic', 0.5, seed=i) for i in range(100)]

        neural_mean = sum(neural_ratings) / len(neural_ratings)
        neuro_symbolic_mean = sum(neuro_symbolic_ratings) / len(neuro_symbolic_ratings)

        assert neuro_symbolic_mean >= neural_mean, "Neuro-symbolic should have higher comprehension"

    def test_comprehension_difficulty(self):
        """Higher difficulty should decrease comprehension."""
        rating_easy = simulate_comprehension_rating('neural', 0.1, seed=789)
        rating_hard = simulate_comprehension_rating('neural', 0.9, seed=789)

        assert rating_hard <= rating_easy, "Harder problems should have lower comprehension"

    def test_comprehension_deterministic(self):
        """Same seed should produce same result."""
        rating1 = simulate_comprehension_rating('neural', 0.5, seed=999)
        rating2 = simulate_comprehension_rating('neural', 0.5, seed=999)
        assert rating1 == rating2, "Comprehension rating should be deterministic"

class TestResponseTimeDistributionValidation:
    """Tests for distribution validation function."""

    def test_valid_distribution(self):
        """Distribution with no large gaps should pass."""
        times = [1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0]
        is_valid, stats = validate_response_time_distribution(times)
        assert is_valid
        assert stats['max_gap'] <= 5.0

    def test_invalid_distribution(self):
        """Distribution with large gaps should fail."""
        times = [1.0, 1.5, 2.0, 10.0, 10.5]  # Gap of 8.0 between 2.0 and 10.0
        is_valid, stats = validate_response_time_distribution(times)
        assert not is_valid
        assert stats['max_gap'] > 5.0

    def test_empty_list(self):
        """Empty list should pass validation."""
        is_valid, stats = validate_response_time_distribution([])
        assert is_valid

    def test_single_element(self):
        """Single element list should pass validation."""
        is_valid, stats = validate_response_time_distribution([5.0])
        assert is_valid

    def test_stats_computation(self):
        """Stats should be computed correctly."""
        times = [1.0, 2.0, 3.0, 4.0, 5.0]
        is_valid, stats = validate_response_time_distribution(times)

        assert stats['count'] == 5
        assert stats['min'] == 1.0
        assert stats['max'] == 5.0
        assert abs(stats['mean'] - 3.0) < 0.001
        assert stats['median'] == 3.0

class TestGenerateResponseMetrics:
    """Tests for metrics generation function."""

    def test_adds_fields(self):
        """Should add response_time_seconds and comprehension_rating."""
        logs = [
            {'problem_id': 'p1', 'condition': 'neural', 'difficulty': 0.5, 'correct': True},
            {'problem_id': 'p2', 'condition': 'symbolic', 'difficulty': 0.3, 'correct': False}
        ]

        updated = generate_response_metrics(logs, seed=42)

        assert 'response_time_seconds' in updated[0]
        assert 'comprehension_rating' in updated[0]
        assert 'response_time_seconds' in updated[1]
        assert 'comprehension_rating' in updated[1]

    def test_preserves_original_data(self):
        """Should preserve all original fields."""
        logs = [
            {'problem_id': 'p1', 'condition': 'neural', 'difficulty': 0.5, 'extra_field': 'value'}
        ]

        updated = generate_response_metrics(logs, seed=42)

        assert updated[0]['problem_id'] == 'p1'
        assert updated[0]['condition'] == 'neural'
        assert updated[0]['extra_field'] == 'value'

    def test_deterministic_generation(self):
        """Same seed should produce same results."""
        logs = [
            {'problem_id': 'p1', 'condition': 'neural', 'difficulty': 0.5},
            {'problem_id': 'p2', 'condition': 'symbolic', 'difficulty': 0.3}
        ]

        updated1 = generate_response_metrics(logs, seed=123)
        updated2 = generate_response_metrics(logs, seed=123)

        assert updated1[0]['response_time_seconds'] == updated2[0]['response_time_seconds']
        assert updated1[0]['comprehension_rating'] == updated2[0]['comprehension_rating']

    def test_integration_with_csv(self):
        """Test full pipeline with CSV file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_file = os.path.join(tmpdir, 'input.csv')
            output_file = os.path.join(tmpdir, 'output.csv')

            # Create input CSV
            with open(input_file, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=['problem_id', 'condition', 'difficulty', 'correct'])
                writer.writeheader()
                writer.writerow({'problem_id': 'p1', 'condition': 'neural', 'difficulty': 0.5, 'correct': 'True'})
                writer.writerow({'problem_id': 'p2', 'condition': 'symbolic', 'difficulty': 0.3, 'correct': 'False'})

            # Load and process
            logs = []
            with open(input_file, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    row['difficulty'] = float(row['difficulty'])
                    row['correct'] = row['correct'] == 'True'
                    logs.append(row)

            updated = generate_response_metrics(logs, seed=42)

            # Write output
            with open(output_file, 'w', newline='') as f:
                fieldnames = list(updated[0].keys())
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(updated)

            # Verify output
            assert os.path.exists(output_file)
            with open(output_file, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                assert len(rows) == 2
                assert 'response_time_seconds' in rows[0]
                assert 'comprehension_rating' in rows[0]