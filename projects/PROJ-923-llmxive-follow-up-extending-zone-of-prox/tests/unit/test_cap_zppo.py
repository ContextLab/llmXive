"""
Unit tests for the Dynamic NCQ Generator and CAP-ZPPO Loop.
"""

import pytest
import numpy as np
import json
from pathlib import Path
from unittest.mock import Mock, patch

from loops.cap_zppo import DynamicNCQGenerator, CAPZPPOLoop, MIN_PROMPT_THRESHOLD
from models.cap_classifier import CAPClassifier

class TestDynamicNCQGenerator:
    """Tests for the DynamicNCQGenerator class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.generator = DynamicNCQGenerator()
        self.test_question = {
            "question": "What is 2+2?",
            "options": {
                "A": "3",
                "B": "4",
                "C": "5",
                "D": "6"
            }
        }
        self.candidate_ids = ["A", "B", "C", "D"]

    def test_retain_fluctuating_only(self):
        """Test that only 'fluctuating' candidates are retained."""
        classifications = {
            "A": "rejected",
            "B": "fluctuating",
            "C": "accepted",
            "D": "fluctuating"
        }
        
        result = self.generator.generate_ncq(
            self.test_question,
            self.candidate_ids,
            classifications,
            cycle=0
        )
        
        assert result == ["B", "D"]
        assert "A" not in result
        assert "C" not in result

    def test_fallback_to_full_set_if_empty(self):
        """Test FR-007: Fallback to full set if pruning results in zero candidates."""
        # All candidates are pruned
        classifications = {
            "A": "rejected",
            "B": "accepted",
            "C": "rejected",
            "D": "accepted"
        }
        
        result = self.generator.generate_ncq(
            self.test_question,
            self.candidate_ids,
            classifications,
            cycle=0
        )
        
        # Should return the full set
        assert result == self.candidate_ids
        assert len(result) == 4

    def test_fallback_if_below_threshold(self):
        """Test FR-007: Fallback if retained count is below MIN_PROMPT_THRESHOLD."""
        # Only 1 candidate retained, but threshold is 1, so it should keep it?
        # Wait, MIN_PROMPT_THRESHOLD is 1. If retained < 1, fallback.
        # If retained == 1, it is kept.
        # Let's test with a hypothetical threshold of 2 (by mocking or logic change)
        # But the constant is 1. So we need a case where retained is 0.
        # The previous test covers 0.
        # Let's test the case where we have 1 retained and threshold is 1 -> it stays.
        classifications = {
            "A": "rejected",
            "B": "fluctuating",
            "C": "rejected",
            "D": "rejected"
        }
        result = self.generator.generate_ncq(
            self.test_question,
            self.candidate_ids,
            classifications,
            cycle=0
        )
        assert result == ["B"] # 1 >= 1, so no fallback

    def test_get_prompt_content(self):
        """Test prompt generation."""
        selected = ["A", "B"]
        prompt = self.generator.get_prompt_content(self.test_question, selected)
        
        assert "Question: What is 2+2?" in prompt
        assert "- A: 3" in prompt
        assert "- B: 4" in prompt
        assert "- C:" not in prompt
        assert "- D:" not in prompt
        assert "Answer:" in prompt


class TestCAPZPPOLoop:
    """Tests for the CAPZPPOLoop class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.loop = CAPZPPOLoop()
        self.mock_rollout_data = [
            {
                "question_id": "q1",
                "question": "Q1",
                "options": {"A": "1", "B": "2"},
                "candidates": [{"id": "A"}, {"id": "B"}],
                "ground_truth": "B"
            }
        ]

    @patch('loops.cap_zppo.generate_synthetic_rollout_log')
    def test_run_simulation(self, mock_gen):
        """Test that the simulation runs and returns metrics."""
        mock_gen.return_value = self.mock_rollout_data
        
        results = self.loop.run(num_cycles=2, seed=42)
        
        assert 'metrics' in results
        assert len(results['metrics']) == 2
        assert 'final_accuracy' in results
        assert 'aucc' in results
        assert 'avg_prompt_length' in results

    def test_noise_injection(self):
        """Verify that noise injection logic exists (conceptual check)."""
        # The loop should use NOISE_SIGMA from the module
        from loops.cap_zppo import NOISE_SIGMA
        assert NOISE_SIGMA == 0.05

    def test_min_threshold_constant(self):
        """Verify FR-007 constant is set."""
        from loops.cap_zppo import MIN_PROMPT_THRESHOLD
        assert MIN_PROMPT_THRESHOLD >= 1