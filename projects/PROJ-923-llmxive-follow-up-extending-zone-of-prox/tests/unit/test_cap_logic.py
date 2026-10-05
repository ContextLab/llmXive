"""
Unit tests for Confidence-Adaptive Pruning (CAP) logic edge cases.

This file extends the existing test suite to specifically verify:
1. Fallback to full set when ALL candidates are pruned (high confidence).
2. Fallback to full set when pruning results in an empty set.
3. Handling of the first cycle (no history).
4. Handling of consistently rejected vs accepted candidates.
"""

import pytest
import numpy as np
from typing import List, Dict, Any, Set, Optional
from dataclasses import dataclass

# Import from the project's models module
from models.cap_classifier import ConfidenceStats, classify_confidence, CAPClassifier
from utils.state_store import CycleRecord
from utils.noise import inject_noise
from utils.seeds import get_rng


class TestCAPClassifierEdgeCases:
    """Test suite for CAPClassifier edge cases and fallback mechanisms."""

    def setup_method(self):
        """Set up test fixtures."""
        self.seed = 42
        self.rng = get_rng(self.seed)
        
        # Thresholds defined in FR-003
        self.threshold_low = 0.1
        self.threshold_high = 0.9

    def test_all_candidates_pruned_high_confidence(self):
        """
        Verify that if ALL candidates are pruned due to high confidence (>0.9),
        the system defaults to the full set to avoid empty prompts (FR-007).
        """
        # Create a CAPClassifier instance
        classifier = CAPClassifier(
            threshold_low=self.threshold_low,
            threshold_high=self.threshold_high
        )

        # Simulate a scenario where all candidates have consistently high confidence
        # This would normally result in ALL being classified as 'accepted' and pruned
        candidates = [f"candidate_{i}" for i in range(5)]
        
        # Create historical data where every candidate has mean > 0.9
        # We'll simulate this by manually setting the history
        history = {}
        for candidate in candidates:
            # Create a list of high confidence scores
            scores = [0.95, 0.96, 0.98, 0.97, 0.99]
            history[candidate] = scores
        
        # Update the classifier's internal state
        classifier.history = history

        # Get the pruned set
        pruned_set = classifier.get_candidates_for_prompt(candidates)
        
        # Assert that the fallback mechanism triggered and returned the full set
        assert len(pruned_set) == len(candidates), (
            f"Expected full set fallback when all candidates are pruned, "
            f"but got {len(pruned_set)} candidates. Pruned set: {pruned_set}"
        )
        assert pruned_set == set(candidates), (
            f"Expected full set {set(candidates)}, but got {pruned_set}"
        )

    def test_all_candidates_pruned_low_confidence(self):
        """
        Verify that if ALL candidates are pruned due to low confidence (<0.1),
        the system defaults to the full set to avoid empty prompts (FR-007).
        """
        classifier = CAPClassifier(
            threshold_low=self.threshold_low,
            threshold_high=self.threshold_high
        )

        candidates = [f"candidate_{i}" for i in range(5)]
        
        # Create historical data where every candidate has consistently low confidence
        history = {}
        for candidate in candidates:
            scores = [0.05, 0.03, 0.08, 0.02, 0.04]
            history[candidate] = scores
        
        classifier.history = history

        pruned_set = classifier.get_candidates_for_prompt(candidates)
        
        # Assert fallback to full set
        assert len(pruned_set) == len(candidates), (
            f"Expected full set fallback when all candidates are pruned (low conf), "
            f"but got {len(pruned_set)} candidates"
        )
        assert pruned_set == set(candidates)

    def test_mixed_confidence_normal_pruning(self):
        """
        Verify normal pruning behavior:
        - Consistently rejected (<0.1) -> pruned
        - Consistently accepted (>0.9) -> pruned
        - Fluctuating ([0.1, 0.9]) -> kept
        """
        classifier = CAPClassifier(
            threshold_low=self.threshold_low,
            threshold_high=self.threshold_high
        )

        candidates = [
            "rejected_candidate",    # Should be pruned (low conf)
            "accepted_candidate",    # Should be pruned (high conf)
            "fluctuating_candidate"  # Should be kept
        ]

        history = {
            "rejected_candidate": [0.05, 0.03, 0.08, 0.02, 0.04],
            "accepted_candidate": [0.95, 0.96, 0.98, 0.97, 0.99],
            "fluctuating_candidate": [0.5, 0.6, 0.4, 0.7, 0.55]
        }

        classifier.history = history

        pruned_set = classifier.get_candidates_for_prompt(candidates)
        
        # Only the fluctuating candidate should remain
        expected = {"fluctuating_candidate"}
        assert pruned_set == expected, (
            f"Expected {expected}, but got {pruned_set}"
        )

    def test_empty_history_first_cycle(self):
        """
        Verify handling of the first cycle where no history exists.
        The system should return the full set of candidates.
        """
        classifier = CAPClassifier(
            threshold_low=self.threshold_low,
            threshold_high=self.threshold_high
        )
        
        # Ensure history is empty (first cycle)
        classifier.history = {}
        
        candidates = [f"candidate_{i}" for i in range(5)]
        
        pruned_set = classifier.get_candidates_for_prompt(candidates)
        
        # First cycle should return full set
        assert pruned_set == set(candidates), (
            f"Expected full set on first cycle, but got {pruned_set}"
        )

    def test_partial_pruning_results_in_empty_set(self):
        """
        Verify edge case where pruning logic results in an empty set
        (e.g., all candidates are either consistently rejected or accepted).
        The system must fallback to the full set.
        """
        classifier = CAPClassifier(
            threshold_low=self.threshold_low,
            threshold_high=self.threshold_high
        )

        candidates = [
            "rejected_1", "rejected_2",
            "accepted_1", "accepted_2"
        ]

        history = {
            "rejected_1": [0.05, 0.03],
            "rejected_2": [0.08, 0.02],
            "accepted_1": [0.95, 0.96],
            "accepted_2": [0.98, 0.97]
        }

        classifier.history = history

        pruned_set = classifier.get_candidates_for_prompt(candidates)
        
        # Should fallback to full set because no fluctuating candidates exist
        assert len(pruned_set) == len(candidates), (
            f"Expected full set fallback when no fluctuating candidates, "
            f"but got {len(pruned_set)} candidates"
        )
        assert pruned_set == set(candidates)

    def test_single_candidate_fluctuating(self):
        """
        Verify behavior with a single fluctuating candidate.
        Should be kept without triggering fallback.
        """
        classifier = CAPClassifier(
            threshold_low=self.threshold_low,
            threshold_high=self.threshold_high
        )

        candidates = ["only_candidate"]
        history = {
            "only_candidate": [0.5, 0.6, 0.4, 0.7, 0.55]
        }

        classifier.history = history

        pruned_set = classifier.get_candidates_for_prompt(candidates)
        
        assert pruned_set == {"only_candidate"}

    def test_single_candidate_consistently_accepted(self):
        """
        Verify behavior with a single consistently accepted candidate.
        Should trigger fallback to full set (which is just itself).
        """
        classifier = CAPClassifier(
            threshold_low=self.threshold_low,
            threshold_high=self.threshold_high
        )

        candidates = ["only_candidate"]
        history = {
            "only_candidate": [0.95, 0.96, 0.98]
        }

        classifier.history = history

        pruned_set = classifier.get_candidates_for_prompt(candidates)
        
        # Fallback to full set (which is the single candidate)
        assert pruned_set == {"only_candidate"}

    def test_confidence_classification_thresholds(self):
        """
        Unit test for the classify_confidence helper function
        to ensure thresholds are applied correctly.
        """
        # Test rejected (< 0.1)
        assert classify_confidence(0.05) == "rejected"
        assert classify_confidence(0.09) == "rejected"
        assert classify_confidence(0.099) == "rejected"

        # Test accepted (> 0.9)
        assert classify_confidence(0.91) == "accepted"
        assert classify_confidence(0.99) == "accepted"
        assert classify_confidence(0.999) == "accepted"

        # Test fluctuating (0.1 to 0.9 inclusive)
        assert classify_confidence(0.1) == "fluctuating"
        assert classify_confidence(0.5) == "fluctuating"
        assert classify_confidence(0.9) == "fluctuating"

        # Edge case: exactly 0.1 and 0.9
        assert classify_confidence(0.1) == "fluctuating"
        assert classify_confidence(0.9) == "fluctuating"

    def test_noise_injection_does_not_break_fallback(self):
        """
        Verify that noise injection (FR-008) does not cause the fallback
        mechanism to fail unexpectedly.
        """
        classifier = CAPClassifier(
            threshold_low=self.threshold_low,
            threshold_high=self.threshold_high
        )

        candidates = [f"candidate_{i}" for i in range(5)]
        
        # Create history with borderline values that might cross thresholds with noise
        history = {}
        for candidate in candidates:
            # Start with values near the threshold
            base_scores = [0.09, 0.11, 0.08, 0.12, 0.10]
            noisy_scores = []
            for score in base_scores:
                noisy = inject_noise(score, sigma=0.05, rng=self.rng)
                noisy_scores.append(noisy)
            history[candidate] = noisy_scores

        classifier.history = history

        # This should not raise an exception and should return a valid set
        pruned_set = classifier.get_candidates_for_prompt(candidates)
        
        # The set should be non-empty (either pruned set or fallback)
        assert len(pruned_set) > 0, (
            "Pruned set should never be empty due to fallback mechanism"
        )
        assert pruned_set.issubset(set(candidates))

    def test_large_candidate_pool_fallback(self):
        """
        Verify fallback works correctly with a large pool of candidates.
        """
        classifier = CAPClassifier(
            threshold_low=self.threshold_low,
            threshold_high=self.threshold_high
        )

        # Create 100 candidates, all consistently accepted
        candidates = [f"candidate_{i}" for i in range(100)]
        history = {
            cand: [0.95] * 5 for cand in candidates
        }

        classifier.history = history

        pruned_set = classifier.get_candidates_for_prompt(candidates)
        
        # Should fallback to full set of 100
        assert len(pruned_set) == 100
        assert pruned_set == set(candidates)

    def test_empty_candidate_list(self):
        """
        Verify behavior when the input candidate list is empty.
        Should return an empty set.
        """
        classifier = CAPClassifier(
            threshold_low=self.threshold_low,
            threshold_high=self.threshold_high
        )
        
        candidates = []
        pruned_set = classifier.get_candidates_for_prompt(candidates)
        
        assert pruned_set == set()
        assert len(pruned_set) == 0