"""
Unit tests for the ConsensusGapEvaluator.
"""

import pytest
from models.evaluator import ConsensusGapEvaluator, EvaluationResult


@pytest.fixture
def evaluator():
    return ConsensusGapEvaluator(use_simple_heuristic=True)


def test_extract_topic_resource_allocation(evaluator):
    """Test topic extraction for resource allocation conflicts."""
    text = "We need to divide the budget fairly between the two departments."
    topic = evaluator._extract_topic(text)
    assert topic == "resource_allocation"


def test_extract_topic_communication_breakdown(evaluator):
    """Test topic extraction for communication breakdowns."""
    text = "I feel like you are not listening to what I am saying."
    topic = evaluator._extract_topic(text)
    assert topic == "communication_breakdown"


def test_extract_topic_goal_conflict(evaluator):
    """Test topic extraction for goal conflicts."""
    text = "Our objectives for this project are completely different."
    topic = evaluator._extract_topic(text)
    assert topic == "goal_conflict"


def test_extract_topic_value_clash(evaluator):
    """Test topic extraction for value clashes."""
    text = "This goes against our core cultural values."
    topic = evaluator._extract_topic(text)
    assert topic == "value_clash"


def test_extract_topic_default(evaluator):
    """Test default topic extraction."""
    text = "We have a disagreement that needs to be resolved."
    topic = evaluator._extract_topic(text)
    assert topic == "default"


def test_keyword_score_resolution(evaluator):
    """Test that resolution keywords lead to low gap scores."""
    text = "I agree with your proposal and we can find a mutual solution."
    score = evaluator._calculate_keyword_score(text)
    # Resolution keywords should result in low gap (high consensus)
    assert score < 0.5


def test_keyword_score_escalation(evaluator):
    """Test that escalation keywords lead to high gap scores."""
    text = "I refuse to accept this and will fight for my position."
    score = evaluator._calculate_keyword_score(text)
    # Escalation keywords should result in high gap
    assert score > 0.5


def test_keyword_score_neutral(evaluator):
    """Test neutral text results in moderate gap score."""
    text = "The meeting is scheduled for tomorrow at 10 AM."
    score = evaluator._calculate_keyword_score(text)
    # No keywords should result in ~0.5
    assert 0.4 <= score <= 0.6


def test_evaluate_turn_valid(evaluator):
    """Test evaluation of a valid turn with resolution keywords."""
    result = evaluator.evaluate_turn(
        trajectory_id="T001",
        turn_index=0,
        turn_text="I understand your perspective and we can compromise."
    )

    assert result.is_valid is True
    assert result.consensus_gap_score < 0.5
    assert result.trajectory_id == "T001"
    assert result.turn_index == 0


def test_evaluate_turn_empty(evaluator):
    """Test evaluation of an empty turn."""
    result = evaluator.evaluate_turn(
        trajectory_id="T001",
        turn_index=0,
        turn_text=""
    )

    assert result.is_valid is False
    assert result.consensus_gap_score == 1.0
    assert "Invalid or empty turn text" in result.error_message


def test_evaluate_trajectory(evaluator):
    """Test evaluation of a full trajectory."""
    trajectory_data = {
        "trajectory_id": "T002",
        "turns": [
            {"text": "I disagree with your approach."},
            {"text": "Let's find a mutual agreement."},
            {"text": "I refuse to compromise."}
        ]
    }

    results = evaluator.evaluate_trajectory(trajectory_data)

    assert len(results) == 3
    assert results[0].trajectory_id == "T002"
    assert results[1].consensus_gap_score < 0.5  # Resolution
    assert results[2].consensus_gap_score > 0.5  # Escalation


def test_calculate_trajectory_aggregate(evaluator):
    """Test aggregate score calculation."""
    results = [
        EvaluationResult("T003", 0, 0.8, "", "", "default", True),
        EvaluationResult("T003", 1, 0.2, "", "", "default", True),
        EvaluationResult("T003", 2, 0.5, "", "", "default", True)
    ]

    avg = evaluator.calculate_trajectory_aggregate(results)
    assert avg == pytest.approx(0.5)


def test_calculate_trajectory_aggregate_empty(evaluator):
    """Test aggregate score with no valid results."""
    results = [
        EvaluationResult("T004", 0, 1.0, "", "", "default", False, "Error")
    ]

    avg = evaluator.calculate_trajectory_aggregate(results)
    assert avg == 1.0