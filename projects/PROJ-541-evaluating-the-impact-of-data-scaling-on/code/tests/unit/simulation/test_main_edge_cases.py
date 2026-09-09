"""
Tests for T028d: Iteration Logic Enforcement.
Verifies that the simulation fails if time limit is hit before target iterations.
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
import time

# Add code to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from main import enforce_iteration_logic, TARGET_ITERATIONS, MAX_RUNTIME_SECONDS


class TestIterationLogic:
    
    def test_target_iterations_is_10k(self):
        """Asserts target is 10k."""
        assert TARGET_ITERATIONS == 10000

    def test_continues_under_time_and_under_iterations(self):
        """Should return True if time is low and iterations are low."""
        # 1 hour passed, 100 iterations done
        result = enforce_iteration_logic(elapsed_time=3600, current_iterations=100)
        assert result is True

    def test_fails_if_time_limit_hit_before_iterations(self):
        """Should raise RuntimeError if time > 5.5h and iterations < 10k."""
        # 6 hours passed, 100 iterations done
        with pytest.raises(RuntimeError) as exc_info:
            enforce_iteration_logic(elapsed_time=6 * 3600, current_iterations=100)
        
        assert "FIDELITY VIOLATION" in str(exc_info.value)
        assert "Insufficient iterations" in str(exc_info.value)

    def test_stops_if_time_limit_hit_after_iterations(self):
        """Should return False (stop) if time > 5.5h but iterations >= 10k."""
        # 6 hours passed, 10000 iterations done
        result = enforce_iteration_logic(elapsed_time=6 * 3600, current_iterations=10000)
        assert result is False

    def test_continues_if_time_limit_not_reached(self):
        """Should return True if time < 5.5h regardless of iterations (as long as < target)."""
        # 5 hours passed, 9999 iterations done
        result = enforce_iteration_logic(elapsed_time=5 * 3600, current_iterations=9999)
        assert result is True

    def test_stops_if_target_reached(self):
        """Should return False if iterations >= target."""
        result = enforce_iteration_logic(elapsed_time=100, current_iterations=10000)
        assert result is False
        
        result = enforce_iteration_logic(elapsed_time=100, current_iterations=10001)
        assert result is False
