"""
Unit tests for response metrics simulation and validation.
"""
import pytest
import os
import sys
import json
import random
from typing import Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from code.simulate.response_metrics import (
    simulate_response_time,
    simulate_comprehension_rating,
    validate_response_time_distribution,
    generate_response_metrics,
    MAX_GAP_SECONDS,
    MIN_RESPONSE_TIME,
    MAX_RESPONSE_TIME,
    COMPREHENSION_MIN,
    COMPREHENSION_MAX
)

class TestResponseTimeSimulation:
    """Tests for response time simulation logic."""

    def test_response_time_bounds(self):
        """Test that response times are within valid bounds."""
        for _ in range(100):
            rt = simulate_response_time(0.5, 0.5)
            assert MIN_RESPONSE_TIME <= rt <= MAX_RESPONSE_TIME, \
                f"Response time {rt} out of bounds [{MIN_RESPONSE_TIME}, {MAX_RESPONSE_TIME}]"

    def test_knowledge_effect(self):
        """Test that higher knowledge leads to faster response times."""
        low_knowledge_rt = simulate_response_time(0.2, 0.5, seed=42)
        high_knowledge_rt = simulate_response_time(0.8, 0.5, seed=42)
        assert high_knowledge_rt <= low_knowledge_rt, \
            f"High knowledge ({high_knowledge_rt}) should be faster than low knowledge ({low_knowledge_rt})"

    def test_difficulty_effect(self):
        """Test that higher difficulty leads to slower response times."""
        easy_rt = simulate_response_time(0.5, 0.2, seed=42)
        hard_rt = simulate_response_time(0.5, 0.8, seed=42)
        assert hard_rt >= easy_rt, \
            f"Hard problem ({hard_rt}) should be slower than easy problem ({easy_rt})"

    def test_deterministic_with_seed(self):
        """Test that same seed produces same results."""
        rt1 = simulate_response_time(0.5, 0.5, seed=123)
        rt2 = simulate_response_time(0.5, 0.5, seed=123)
        assert rt1 == rt2, f"Same seed should produce same result: {rt1} != {rt2}"

class TestComprehensionRatingSimulation:
    """Tests for comprehension rating simulation logic."""

    def test_rating_bounds(self):
        """Test that ratings are within 1-5 range."""
        for _ in range(100):
            rating = simulate_comprehension_rating(0.5, 0.5, 5.0)
            assert COMPREHENSION_MIN <= rating <= COMPREHENSION_MAX, \
                f"Rating {rating} out of bounds [{COMPREHENSION_MIN}, {COMPREHENSION_MAX}]"
            assert isinstance(rating, int), f"Rating should be integer, got {type(rating)}"

    def test_knowledge_effect_on_rating(self):
        """Test that higher knowledge leads to higher ratings."""
        low_knowledge_rating = simulate_comprehension_rating(0.2, 0.5, 5.0, seed=42)
        high_knowledge_rating = simulate_comprehension_rating(0.8, 0.5, 5.0, seed=42)
        assert high_knowledge_rating >= low_knowledge_rating, \
            f"High knowledge ({high_knowledge_rating}) should have >= rating than low knowledge ({low_knowledge_rating})"

    def test_difficulty_effect_on_rating(self):
        """Test that higher difficulty leads to lower ratings."""
        easy_rating = simulate_comprehension_rating(0.5, 0.2, 5.0, seed=42)
        hard_rating = simulate_comprehension_rating(0.5, 0.8, 5.0, seed=42)
        assert easy_rating >= hard_rating, \
            f"Easy problem ({easy_rating}) should have >= rating than hard problem ({hard_rating})"

    def test_response_time_effect_on_rating(self):
        """Test that extreme response times affect ratings."""
        normal_rating = simulate_comprehension_rating(0.5, 0.5, 5.0, seed=42)
        too_fast_rating = simulate_comprehension_rating(0.5, 0.5, 0.5, seed=42)
        too_slow_rating = simulate_comprehension_rating(0.5, 0.5, 35.0, seed=42)
        
        # Extreme times should generally result in lower ratings
        assert too_fast_rating <= normal_rating or too_slow_rating <= normal_rating, \
            "Extreme response times should not increase rating significantly"

class TestDistributionValidation:
    """Tests for response time distribution validation."""

    def test_valid_distribution(self):
        """Test validation passes for distribution with small gaps."""
        response_times = [1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0]
        result = validate_response_time_distribution(response_times)
        assert result["valid"] is True, f"Valid distribution should pass: {result}"
        assert result["max_gap"] <= MAX_GAP_SECONDS

    def test_invalid_distribution(self):
        """Test validation fails for distribution with large gaps."""
        response_times = [1.0, 2.0, 3.0, 10.0, 11.0]  # Gap of 7 seconds
        result = validate_response_time_distribution(response_times)
        assert result["valid"] is False, f"Invalid distribution should fail: {result}"
        assert result["max_gap"] > MAX_GAP_SECONDS

    def test_insufficient_data(self):
        """Test validation handles insufficient data points."""
        result = validate_response_time_distribution([1.0])
        assert result["valid"] is True, "Single point should be considered valid"
        
        result = validate_response_time_distribution([])
        assert result["valid"] is True, "Empty list should be considered valid"

    def test_gap_calculation(self):
        """Test that gaps are calculated correctly."""
        response_times = [1.0, 3.0, 6.0]  # Gaps: 2.0, 3.0
        result = validate_response_time_distribution(response_times)
        assert result["max_gap"] == 3.0, f"Max gap should be 3.0, got {result['max_gap']}"
        assert result["total_gaps"] == 2, f"Should have 2 gaps, got {result['total_gaps']}"

class TestGenerateResponseMetrics:
    """Tests for the main metrics generation function."""

    def test_full_generation(self):
        """Test complete metrics generation for student-problem pair."""
        student = {"knowledge": 0.7, "id": "test_student"}
        problem = {"difficulty": 0.4, "id": "test_problem"}
        
        metrics = generate_response_metrics(student, problem, seed=42)
        
        assert "response_time" in metrics, "Missing response_time"
        assert "comprehension_rating" in metrics, "Missing comprehension_rating"
        
        rt = metrics["response_time"]
        rating = metrics["comprehension_rating"]
        
        assert MIN_RESPONSE_TIME <= rt <= MAX_RESPONSE_TIME, f"RT out of bounds: {rt}"
        assert COMPREHENSION_MIN <= rating <= COMPREHENSION_MAX, f"Rating out of bounds: {rating}"
        assert isinstance(rating, int), f"Rating should be integer: {type(rating)}"

    def test_deterministic_generation(self):
        """Test that same inputs with same seed produce identical results."""
        student = {"knowledge": 0.6, "id": "student"}
        problem = {"difficulty": 0.3, "id": "problem"}
        
        metrics1 = generate_response_metrics(student, problem, seed=999)
        metrics2 = generate_response_metrics(student, problem, seed=999)
        
        assert metrics1 == metrics2, f"Same seed should produce same metrics: {metrics1} != {metrics2}"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
