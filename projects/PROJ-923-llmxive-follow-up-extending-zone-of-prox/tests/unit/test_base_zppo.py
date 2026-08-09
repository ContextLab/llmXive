"""
Unit tests for static NCQ generation logic in base_zppo.py.

This module validates the correctness of the static Negative Candidate-included 
Question (NCQ) generation logic as required for User Story 1 (US1).

Tests verify:
1. Correct construction of NCQ prompts from questions and negative candidates.
2. Handling of edge cases (empty candidates, single candidate).
3. Integration with the StateStore for recording generation metadata.
"""

import pytest
import os
import sys
import tempfile
import json

# Add project root to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from typing import List, Dict, Any, Optional
from dataclasses import dataclass

# Import project utilities and models
from utils.seeds import set_global_seed, get_seed
from utils.logging import get_logger, configure_logging
from models.state_store import StateStore, CycleRecord
from contracts.rollout_log import RolloutLogSchema

# Import the module under test (we will create a minimal mock for the loop logic)
# Since base_zppo.py is not yet implemented (T014), we implement the specific 
# logic function here for testing purposes to ensure the logic is correct 
# before the full loop implementation.
# The actual implementation in T014 must match this logic.

@dataclass
class QuestionData:
    question_id: str
    question_text: str
    ground_truth: str
    negative_candidates: List[str]
    task_type: str = "mmlu"

@dataclass
class NCQResult:
    prompt: str
    question_id: str
    candidates_included: List[str]
    candidate_count: int

def generate_static_ncq_prompt(
    question: QuestionData,
    candidates: Optional[List[str]] = None,
    template_id: str = "default"
) -> NCQResult:
    """
    Static NCQ Generator Logic (to be implemented in base_zppo.py).
    
    Generates a prompt that includes the question and a set of negative candidates.
    This function is the core logic being tested.
    
    Args:
        question: The QuestionData object containing the query and ground truth.
        candidates: Optional list of specific candidates to include. If None, 
                    uses all negative_candidates from the question.
        template_id: Identifier for the prompt template (default: "default").
        
    Returns:
        NCQResult containing the generated prompt and metadata.
        
    Raises:
        ValueError: If candidates list is empty after filtering (unless fallback logic is added).
    """
    # Use all negative candidates if none specified
    if candidates is None:
        candidates = question.negative_candidates
    
    # Ensure we have candidates to include
    if not candidates:
        # Fallback: If no candidates provided, we must fail loudly or use a minimal set.
        # For static baseline, we assume the data generator ensures at least one candidate.
        # If this happens, it's a data error.
        raise ValueError(f"No negative candidates provided for question {question.question_id}. "
                       f"Static NCQ generation requires at least one negative candidate.")
    
    # Construct the prompt
    # Template: "Question: {text}\nOptions: {candidates}\nGround Truth Hint: {truth}"
    # Note: In ZPPO, the "Ground Truth Hint" is usually NOT included in the prompt 
    # sent to the student, but might be used for validation. 
    # The prompt should be: "Question: {text}\nCandidates: {list}"
    
    candidates_str = "\n".join([f"- {c}" for c in candidates])
    prompt = f"Question: {question.question_text}\n\nNegative Candidates:\n{candidates_str}"
    
    return NCQResult(
        prompt=prompt,
        question_id=question.question_id,
        candidates_included=candidates,
        candidate_count=len(candidates)
    )

def test_static_ncq_basic_generation():
    """Test basic NCQ generation with standard inputs."""
    set_global_seed(42)
    logger = get_logger("test_base_zppo")
    
    q = QuestionData(
        question_id="mmlu_001",
        question_text="What is the capital of France?",
        ground_truth="Paris",
        negative_candidates=["London", "Berlin", "Madrid"],
        task_type="mmlu"
    )
    
    result = generate_static_ncq_prompt(q)
    
    assert result.question_id == "mmlu_001"
    assert result.candidate_count == 3
    assert "London" in result.candidates_included
    assert "Berlin" in result.candidates_included
    assert "Madrid" in result.candidates_included
    assert "Question: What is the capital of France?" in result.prompt
    assert "Negative Candidates:" in result.prompt
    assert "- London" in result.prompt
    
    logger.info(f"Generated prompt:\n{result.prompt}")

def test_static_ncq_partial_candidates():
    """Test NCQ generation with a subset of candidates."""
    set_global_seed(42)
    
    q = QuestionData(
        question_id="mmlu_002",
        question_text="Which planet is known as the Red Planet?",
        ground_truth="Mars",
        negative_candidates=["Venus", "Jupiter", "Saturn", "Mercury"],
        task_type="mmlu"
    )
    
    subset = ["Venus", "Saturn"]
    result = generate_static_ncq_prompt(q, candidates=subset)
    
    assert result.candidate_count == 2
    assert result.candidates_included == subset
    assert "Jupiter" not in result.prompt
    assert "Mercury" not in result.prompt

def test_static_ncq_single_candidate():
    """Test NCQ generation with exactly one candidate."""
    set_global_seed(42)
    
    q = QuestionData(
        question_id="mmlu_003",
        question_text="What is 2+2?",
        ground_truth="4",
        negative_candidates=["5"],
        task_type="math"
    )
    
    result = generate_static_ncq_prompt(q)
    
    assert result.candidate_count == 1
    assert result.candidates_included == ["5"]
    assert "- 5" in result.prompt

def test_static_ncq_empty_candidates_raises():
    """Test that empty candidates list raises ValueError."""
    set_global_seed(42)
    
    q = QuestionData(
        question_id="mmlu_004",
        question_text="Test question",
        ground_truth="A",
        negative_candidates=[],
        task_type="mmlu"
    )
    
    with pytest.raises(ValueError, match="No negative candidates provided"):
        generate_static_ncq_prompt(q)

def test_static_ncq_with_state_store():
    """Test that NCQ generation can be recorded in StateStore."""
    set_global_seed(42)
    
    # Create a temporary directory for the test state store
    with tempfile.TemporaryDirectory() as tmpdir:
        store = StateStore(project_root=tmpdir, experiment_id="test_exp_001")
        
        q = QuestionData(
            question_id="mmlu_005",
            question_text="Test question for state store",
            ground_truth="X",
            negative_candidates=["Y", "Z"],
            task_type="mmlu"
        )
        
        result = generate_static_ncq_prompt(q)
        
        # Simulate recording this as part of a cycle
        record = CycleRecord(
            cycle_id=1,
            question_id=q.question_id,
            prompt=result.prompt,
            candidates_used=result.candidates_included,
            student_response="Y", # Mock response
            is_correct=False,
            confidence=0.5,
            prompt_length=len(result.prompt)
        )
        
        store.add_record(record)
        
        # Verify the record was stored
        history = store.get_history()
        assert len(history) == 1
        assert history[0].question_id == q.question_id
        assert history[0].candidate_count == len(result.candidates_included)

def test_static_ncq_prompt_format_consistency():
    """Test that the prompt format is consistent across different inputs."""
    set_global_seed(42)
    
    q1 = QuestionData(
        question_id="q1",
        question_text="A",
        ground_truth="1",
        negative_candidates=["2", "3"]
    )
    
    q2 = QuestionData(
        question_id="q2",
        question_text="B",
        ground_truth="4",
        negative_candidates=["5"]
    )
    
    r1 = generate_static_ncq_prompt(q1)
    r2 = generate_static_ncq_prompt(q2)
    
    # Both should follow the same structure
    assert r1.prompt.startswith("Question: ")
    assert r2.prompt.startswith("Question: ")
    assert "Negative Candidates:" in r1.prompt
    assert "Negative Candidates:" in r2.prompt
    assert "- " in r1.prompt
    assert "- " in r2.prompt

def test_static_ncq_ground_truth_not_in_prompt():
    """Verify that ground truth is NOT included in the generated prompt (static baseline)."""
    set_global_seed(42)
    
    q = QuestionData(
        question_id="q_gt",
        question_text="What is the answer?",
        ground_truth="CorrectAnswer",
        negative_candidates=["Wrong1", "Wrong2"]
    )
    
    result = generate_static_ncq_prompt(q)
    
    # The prompt should NOT contain the ground truth
    assert "CorrectAnswer" not in result.prompt
    # But it should contain the candidates
    assert "Wrong1" in result.prompt
    assert "Wrong2" in result.prompt