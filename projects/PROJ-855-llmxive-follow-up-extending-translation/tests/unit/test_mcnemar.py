"""
Unit test for McNemar's test implementation in evaluate.py.
"""

import pytest
import numpy as np
from evaluate import mcnemar_test

def test_mcnemar_perfect_agreement():
    """Test when both models have identical predictions."""
    labels = np.array([1, 0, 1, 0, 1])
    preds1 = np.array([1, 0, 1, 0, 1])
    preds2 = np.array([1, 0, 1, 0, 1])

    result = mcnemar_test(preds1, preds2, labels)
    # b and c should be 0
    assert result["contingency_table"]["model1_correct_model2_incorrect"] == 0
    assert result["contingency_table"]["model1_incorrect_model2_correct"] == 0
    assert result["p_value"] == 1.0

def test_mcnemar_complete_disagreement():
    """Test when models always disagree on the correct label."""
    labels = np.array([1, 0, 1, 0, 1])
    preds1 = np.array([1, 1, 1, 1, 1]) # Model1 is always correct for 1, wrong for 0
    preds2 = np.array([0, 0, 0, 0, 0]) # Model2 is always wrong for 1, correct for 0

    # Actually, let's make it simpler:
    # preds1: [1, 0, 1, 0, 1] -> all correct
    # preds2: [0, 1, 0, 1, 0] -> all wrong
    preds1 = np.array([1, 0, 1, 0, 1])
    preds2 = np.array([0, 1, 0, 1, 0])

    result = mcnemar_test(preds1, preds2, labels)
    # b = 0 (Model1 correct, Model2 incorrect) -> 0
    # c = 5 (Model1 incorrect, Model2 correct) -> 5
    # But wait, in this case, Model1 is always correct, Model2 is always wrong.
    # So b = 0, c = 5.
    assert result["contingency_table"]["model1_correct_model2_incorrect"] == 0
    assert result["contingency_table"]["model1_incorrect_model2_correct"] == 5

def test_mcnemar_partial_disagreement():
    """Test with some disagreement."""
    labels = np.array([1, 0, 1, 0, 1, 0, 1, 0])
    preds1 = np.array([1, 0, 1, 1, 1, 0, 0, 0]) # Correct: 0,1,2,5,7 -> 5/8
    preds2 = np.array([1, 1, 0, 1, 1, 1, 0, 0]) # Correct: 0,3,4,6,7 -> 5/8

    # Let's compute manually:
    # idx: 0 1 2 3 4 5 6 7
    # lab: 1 0 1 0 1 0 1 0
    # p1 : 1 0 1 1 1 0 0 0
    # p2 : 1 1 0 1 1 1 0 0
    # c1 : T T T F T T F T
    # c2 : T F F T T F T T
    # b (c1=T, c2=F): idx 1, 2 -> 2
    # c (c1=F, c2=T): idx 3, 6 -> 2

    result = mcnemar_test(preds1, preds2, labels)
    assert result["contingency_table"]["model1_correct_model2_incorrect"] == 2
    assert result["contingency_table"]["model1_incorrect_model2_correct"] == 2

def test_mcnemar_zero_discordant():
    """Test when there are no discordant pairs."""
    labels = np.array([1, 0, 1, 0])
    preds1 = np.array([1, 0, 1, 0])
    preds2 = np.array([1, 0, 1, 0])

    result = mcnemar_test(preds1, preds2, labels)
    assert result["p_value"] == 1.0
