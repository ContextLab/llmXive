"""
Unit tests for Confidence-Adaptive Pruning (CAP) logic, specifically focusing on edge cases.

This module tests:
1. The fallback mechanism when ALL candidates are pruned (high confidence).
2. The empty prompt fallback generally.
3. Boundary conditions for confidence thresholds.
"""
import pytest
import numpy as np
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

# Import from the project's API surface
from models.state_store import CycleRecord, StateStore
from models.student_sim import StudentState, SimulatedStudent
from utils.seeds import set_global_seed
from utils.logging import get_logger

logger = get_logger(__name__)

# Mock classes to simulate the CAP logic for testing without full loop dependencies
@dataclass
class MockCandidate:
    id: str
    text: str
    confidence_history: List[float]

class MockCAPClassifier:
    """
    Simplified classifier for testing edge cases.
    Implements the logic described in T021/T022:
    - Rejected: mean < 0.1
    - Fluctuating: 0.1 <= mean <= 0.9
    - Accepted (Mastered): mean > 0.9
    """
    def __init__(self, threshold_low: float = 0.1, threshold_high: float = 0.9):
        self.threshold_low = threshold_low
        self.threshold_high = threshold_high
    
    def classify_candidate(self, history: List[float]) -> str:
        if not history:
            return "fluctuating" # Default if no history
        mean_conf = np.mean(history)
        if mean_conf < self.threshold_low:
            return "rejected"
        elif mean_conf > self.threshold_high:
            return "accepted"
        else:
            return "fluctuating"
    
    def get_pruned_candidates(self, candidates: List[MockCandidate]) -> List[MockCandidate]:
        """Returns candidates that are NOT 'accepted' (mastered)."""
        pruned = []
        for cand in candidates:
            status = self.classify_candidate(cand.confidence_history)
            if status != "accepted":
                pruned.append(cand)
        return pruned

class MockNCQGenerator:
    """
    Simulates the Dynamic NCQ Generator from T022.
    Enforces FR-007 (min threshold) and the "All Pruned" fallback.
    """
    def __init__(self, min_candidates: int = 1):
        self.min_candidates = min_candidates
    
    def generate_prompt(self, candidates: List[MockCandidate], 
                        pruned_candidates: List[MockCandidate]) -> str:
        """
        Generates the NCQ prompt string.
        Implements the fallback logic:
        - If pruned_candidates is empty (all were accepted/mastered), 
          revert to the full set to avoid an empty prompt.
        """
        active_set = pruned_candidates
        
        # Edge Case: All candidates pruned (empty set)
        if not active_set:
            logger.warning("All candidates pruned due to high confidence. Reverting to full set.")
            active_set = candidates
        
        # Edge Case: Fallback to minimum set if active_set is still too small (though unlikely if we revert to full)
        if len(active_set) < self.min_candidates:
            logger.warning(f"Active set size {len(active_set)} < min {self.min_candidates}. Reverting to full set.")
            active_set = candidates
        
        # Construct prompt text
        prompt_parts = [f"Question: {c.text}"]
        for i, c in enumerate(active_set):
            prompt_parts.append(f"Candidate {i}: {c.text}")
        
        return "\n".join(prompt_parts)

def test_all_candidates_pruned_fallback():
    """
    Test T020 requirement: Verify that if ALL candidates are pruned 
    (due to high confidence), the system defaults to the full set.
    """
    # Setup: Create candidates with confidence > 0.9 (Mastered)
    # If all are > 0.9, they are all "accepted" and thus "pruned" from the prompt
    candidates = [
        MockCandidate(id="c1", text="Q1", confidence_history=[0.95, 0.96, 0.98]),
        MockCandidate(id="c2", text="Q2", confidence_history=[0.99, 0.99, 0.99]),
        MockCandidate(id="c3", text="Q3", confidence_history=[0.92, 0.94, 0.93]),
    ]
    
    classifier = MockCAPClassifier(threshold_low=0.1, threshold_high=0.9)
    generator = MockNCQGenerator(min_candidates=1)
    
    # Execute: Get pruned list (should be empty because all are 'accepted')
    pruned = classifier.get_pruned_candidates(candidates)
    
    assert len(pruned) == 0, "Expected all candidates to be pruned (mastered)"
    
    # Execute: Generate prompt (should trigger fallback to full set)
    prompt = generator.generate_prompt(candidates, pruned)
    
    # Verify: Prompt must contain all original candidates
    assert "Q1" in prompt, "Fallback failed: Q1 missing from prompt"
    assert "Q2" in prompt, "Fallback failed: Q2 missing from prompt"
    assert "Q3" in prompt, "Fallback failed: Q3 missing from prompt"
    
    # Verify: The prompt length should correspond to the full set size
    # (Simple check: if we see all 3, the fallback worked)
    assert prompt.count("Candidate") == 3, f"Expected 3 candidates in prompt after fallback, got {prompt.count('Candidate')}"
    logger.info("Test passed: All candidates pruned fallback works correctly.")

def test_empty_prompt_fallback_general():
    """
    Test T020 requirement: General empty prompt fallback.
    Simulates a scenario where the pruned list is explicitly empty 
    (e.g., from a bug or external logic) and ensures the generator recovers.
    """
    candidates = [
        MockCandidate(id="c1", text="Q1", confidence_history=[0.5]),
    ]
    
    # Manually pass an empty list to simulate the "all pruned" state
    empty_pruned_list: List[MockCandidate] = []
    
    generator = MockNCQGenerator(min_candidates=1)
    
    prompt = generator.generate_prompt(candidates, empty_pruned_list)
    
    # Verify: The prompt should contain the original candidate
    assert "Q1" in prompt, "General empty fallback failed"
    assert len(prompt) > 0, "Prompt should not be empty"
    logger.info("Test passed: General empty prompt fallback works correctly.")

def test_mixed_confidence_no_fallback():
    """
    Verify that the fallback does NOT trigger when there are valid candidates to show.
    """
    candidates = [
        MockCandidate(id="c1", text="Q1", confidence_history=[0.95]), # Mastered -> Pruned
        MockCandidate(id="c2", text="Q2", confidence_history=[0.50]), # Fluctuating -> Kept
        MockCandidate(id="c3", text="Q3", confidence_history=[0.05]), # Rejected -> Kept
    ]
    
    classifier = MockCAPClassifier(threshold_low=0.1, threshold_high=0.9)
    generator = MockNCQGenerator(min_candidates=1)
    
    pruned = classifier.get_pruned_candidates(candidates)
    
    # Only c1 should be removed
    assert len(pruned) == 2, f"Expected 2 candidates kept, got {len(pruned)}"
    assert pruned[0].id == "c2"
    assert pruned[1].id == "c3"
    
    prompt = generator.generate_prompt(candidates, pruned)
    
    # Verify: Q1 should NOT be in the prompt (it was mastered)
    # Note: Depending on exact logic, "Mastered" might mean "remove from prompt".
    # The prompt should contain Q2 and Q3.
    assert "Q2" in prompt, "Q2 should be in prompt"
    assert "Q3" in prompt, "Q3 should be in prompt"
    # Q1 is the mastered one, so it should be absent in the pruned set logic
    # (Assuming "pruned" means "removed from prompt" in the context of the generator)
    # However, the fallback logic only triggers if the list is EMPTY.
    # Since we have 2 items, no fallback happens.
    assert prompt.count("Candidate") == 2, "Expected 2 candidates, fallback should not trigger"
    logger.info("Test passed: Mixed confidence correctly avoids fallback.")

def test_boundary_conditions():
    """
    Test exact boundary values for confidence thresholds.
    """
    # Thresholds: Low=0.1, High=0.9
    # < 0.1 -> Rejected
    # 0.1 - 0.9 -> Fluctuating
    # > 0.9 -> Accepted (Mastered)
    
    classifier = MockCAPClassifier(threshold_low=0.1, threshold_high=0.9)
    
    # Test exactly 0.1
    status_low = classifier.classify_candidate([0.1])
    assert status_low == "fluctuating", f"0.1 should be fluctuating, got {status_low}"
    
    # Test exactly 0.9
    status_high = classifier.classify_candidate([0.9])
    assert status_high == "fluctuating", f"0.9 should be fluctuating, got {status_high}"
    
    # Test 0.1 - epsilon
    status_below = classifier.classify_candidate([0.0999])
    assert status_below == "rejected", f"0.0999 should be rejected"
    
    # Test 0.9 + epsilon
    status_above = classifier.classify_candidate([0.9001])
    assert status_above == "accepted", f"0.9001 should be accepted"
    
    logger.info("Test passed: Boundary conditions handled correctly.")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])