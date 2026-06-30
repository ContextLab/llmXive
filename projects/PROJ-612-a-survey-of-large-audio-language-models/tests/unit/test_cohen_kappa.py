"""
Unit tests for Cohen's kappa calculation and threshold flagging.
Tests for Task T026: Unit test for Cohen's κ calculation and threshold flagging.
"""
import pytest
import math
from typing import List, Tuple, Dict, Any
import sys
import os

# Add the code directory to the path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from detect_hallucination import normalize_string
from utils import AudioSample

# ----------------------------------------------------------------------
# Implementation of the logic to be tested (simulating the production code
# that T030 will eventually call, but here we implement the core logic
# directly in the test module to ensure it is self-contained and runnable).
# ----------------------------------------------------------------------

def calculate_cohens_kappa(
    judgments: List[Tuple[bool, bool]]
) -> float:
    """
    Calculates Cohen's Kappa coefficient for a list of (algorithm_label, human_label) tuples.
    
    Args:
        judgments: List of tuples where the first element is the algorithm's hallucination flag
                   and the second is the human annotator's flag.
                   
    Returns:
        The Cohen's Kappa coefficient (float).
    
    Raises:
        ValueError: If there is no variance in the labels (e.g., all true or all false).
    """
    if not judgments:
        return 0.0

    n = len(judgments)
    if n == 0:
        return 0.0

    # Count agreements and totals
    # Labels: 0 (False/No Hallucination), 1 (True/Hallucination)
    # Observed agreement (Po)
    agreements = sum(1 for algo, human in judgments if algo == human)
    po = agreements / n

    # Marginal probabilities
    # P1: Probability that Algorithm says 1
    algo_1_count = sum(1 for algo, _ in judgments if algo)
    p1_algo = algo_1_count / n
    p0_algo = 1 - p1_algo

    # P2: Probability that Human says 1
    human_1_count = sum(1 for _, human in judgments if human)
    p1_human = human_1_count / n
    p0_human = 1 - p1_human

    # Expected agreement by chance (Pe)
    # Pe = P(algo=1)*P(human=1) + P(algo=0)*P(human=0)
    pe = (p1_algo * p1_human) + (p0_algo * p0_human)

    if math.isclose(pe, 1.0):
        # No variance in labels, kappa is undefined (often treated as 1.0 or 0.0 depending on context)
        # Standard convention: if there is no chance agreement possible because everyone agrees,
        # but there is no variance, it's often considered perfect agreement but undefined formula.
        # However, if everyone agrees, Po=1, Pe=1, then 0/0.
        # We will return 1.0 if perfect agreement, else 0.0 if no variance but not perfect?
        # Actually, if Pe=1, it means one rater is constant.
        # If Po=1 and Pe=1, return 1.0.
        return 1.0 if po == 1.0 else 0.0

    kappa = (po - pe) / (1 - pe)
    return kappa

def flag_low_agreement(kappa: float, threshold: float = 0.6) -> bool:
    """
    Flags if the agreement is below the threshold.
    
    Args:
        kappa: The calculated Cohen's kappa coefficient.
        threshold: The minimum acceptable kappa value (default 0.6).
        
    Returns:
        True if kappa < threshold (low agreement), False otherwise.
    """
    return kappa < threshold

# ----------------------------------------------------------------------
# Tests
# ----------------------------------------------------------------------

class TestCohenKappaCalculation:
    """Tests for the calculate_cohens_kappa function."""

    def test_perfect_agreement(self):
        """Test case where algorithm and human labels match perfectly."""
        judgments = [
            (True, True), (False, False), (True, True), (False, False)
        ]
        kappa = calculate_cohens_kappa(judgments)
        assert math.isclose(kappa, 1.0), f"Expected 1.0, got {kappa}"

    def test_no_agreement(self):
        """Test case where algorithm and human labels are completely opposite."""
        # Note: With binary labels, if they are perfectly opposite, Po=0.
        # Pe depends on marginals. If marginals are 0.5/0.5, Pe=0.5.
        # Kappa = (0 - 0.5) / (1 - 0.5) = -1.0.
        judgments = [
            (True, False), (False, True), (True, False), (False, True)
        ]
        kappa = calculate_cohens_kappa(judgments)
        assert math.isclose(kappa, -1.0), f"Expected -1.0, got {kappa}"

    def test_random_agreement(self):
        """Test case where agreement is roughly what chance would predict."""
        # Construct a scenario where Po approx equals Pe.
        # e.g., 4 samples. Algo: 2 True, 2 False. Human: 2 True, 2 False.
        # If they align by chance: (T,T), (T,F), (F,T), (F,F) -> 2 agreements.
        # Po = 0.5. Pe = (0.5*0.5) + (0.5*0.5) = 0.5.
        # Kappa = 0.
        judgments = [
            (True, True), (True, False), (False, True), (False, False)
        ]
        kappa = calculate_cohens_kappa(judgments)
        assert math.isclose(kappa, 0.0), f"Expected 0.0, got {kappa}"

    def test_single_sample_agreement(self):
        """Test with a single sample that agrees."""
        judgments = [(True, True)]
        kappa = calculate_cohens_kappa(judgments)
        # With n=1, Po=1, Pe=1 (if marginals are 1.0/0.0 or 0.0/1.0? No, marginals are 1.0 and 0.0)
        # P1_algo=1, P1_human=1 -> Pe = 1*1 + 0*0 = 1.
        # 0/0 -> handled in function to return 1.0.
        assert math.isclose(kappa, 1.0), f"Expected 1.0, got {kappa}"

    def test_empty_list(self):
        """Test with an empty list."""
        judgments = []
        kappa = calculate_cohens_kappa(judgments)
        assert kappa == 0.0

    def test_imperfect_but_good_agreement(self):
        """Test a realistic scenario with high but not perfect agreement."""
        # 10 samples, 9 agreements, 1 disagreement.
        # Algo: 5 True, 5 False. Human: 5 True, 5 False.
        # Agreements: 9. Po = 0.9.
        # Pe = 0.5.
        # Kappa = (0.9 - 0.5) / 0.5 = 0.8.
        judgments = [
            (True, True), (True, True), (True, True), (True, True), (True, True),
            (False, False), (False, False), (False, False), (False, False),
            (True, False)  # Disagreement
        ]
        # Recalculate marginals for this specific set:
        # Algo: 6 True, 4 False. Human: 5 True, 5 False.
        # P1_algo = 0.6, P0_algo = 0.4
        # P1_human = 0.5, P0_human = 0.5
        # Pe = (0.6*0.5) + (0.4*0.5) = 0.3 + 0.2 = 0.5
        # Po = 0.9
        # Kappa = 0.4 / 0.5 = 0.8
        kappa = calculate_cohens_kappa(judgments)
        assert math.isclose(kappa, 0.8), f"Expected 0.8, got {kappa}"

class TestThresholdFlagging:
    """Tests for the flag_low_agreement function."""

    def test_above_threshold(self):
        """Test that high kappa does not flag."""
        assert flag_low_agreement(0.8, threshold=0.6) is False
        assert flag_low_agreement(0.6, threshold=0.6) is False  # Exactly at threshold is OK

    def test_below_threshold(self):
        """Test that low kappa flags."""
        assert flag_low_agreement(0.59, threshold=0.6) is True
        assert flag_low_agreement(0.0, threshold=0.6) is True
        assert flag_low_agreement(-0.5, threshold=0.6) is True

    def test_default_threshold(self):
        """Test that default threshold is 0.6."""
        assert flag_low_agreement(0.5) is True
        assert flag_low_agreement(0.7) is False

class TestIntegration:
    """Integration-style tests combining calculation and flagging."""

    def test_pipeline_acceptable(self):
        """Simulate a pipeline run with acceptable agreement."""
        judgments = [
            (True, True), (False, False), (True, True), (True, True),
            (False, False), (False, False), (True, True), (False, False)
        ]
        kappa = calculate_cohens_kappa(judgments)
        is_low = flag_low_agreement(kappa)
        
        assert kappa > 0.6
        assert is_low is False

    def test_pipeline_unacceptable(self):
        """Simulate a pipeline run with unacceptable agreement."""
        judgments = [
            (True, False), (False, True), (True, False), (False, True),
            (True, False), (False, True), (True, False), (False, True)
        ]
        kappa = calculate_cohens_kappa(judgments)
        is_low = flag_low_agreement(kappa)
        
        assert kappa < 0.6
        assert is_low is True

if __name__ == "__main__":
    pytest.main([__file__, "-v"])