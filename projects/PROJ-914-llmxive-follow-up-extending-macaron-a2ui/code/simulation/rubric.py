from typing import Optional, Dict, Any
import logging
from config import RANDOM_SEED
import random

def calculate_latency_penalty(latency_seconds: float, max_latency: float = 2.0) -> float:
    """
    Calculate latency penalty as defined in SC-002.
    penalty = 1 - min(1, latency / max_latency)
    Returns a value between 0 and 1.
    """
    if max_latency <= 0:
        return 0.0
    ratio = latency_seconds / max_latency
    penalty = 1.0 - min(1.0, ratio)
    return max(0.0, penalty)

def calculate_alignment_score(
    intent_match: float,
    latency_penalty: float,
    ui_completeness: float
) -> float:
    """
    Calculate the Human-Agent Alignment score.
    score = 0.4 * intent_match + 0.3 * (1 - latency_penalty) + 0.3 * ui_completeness
    Note: The rubric uses (1 - latency_penalty) as the positive term.
    """
    # latency_penalty is already calculated as a "loss" (0 to 1)
    # The formula in SC-002 says: 0.3 * (1 - latency_penalty)
    # If latency_penalty is 0 (perfect), term is 0.3. If 1 (max loss), term is 0.
    
    # However, calculate_latency_penalty returns: 1 - min(1, latency/max)
    # So if latency=0, penalty=1. If latency=max, penalty=0.
    # This seems inverted relative to the formula "1 - penalty".
    # Let's re-read SC-002: "latency_penalty = 1 - min(1, latency / 2.0)"
    # So if latency=0, penalty=1. If latency=2, penalty=0.
    # Formula: 0.3 * (1 - penalty). If penalty=1, term=0. If penalty=0, term=0.3.
    # This matches: high latency -> high penalty -> low score contribution.
    
    # Wait, if penalty = 1 - min(...), then:
    # latency=0 -> min(0)=0 -> penalty=1. Term = 0.3 * (1-1) = 0.
    # latency=2 -> min(1)=1 -> penalty=0. Term = 0.3 * (1-0) = 0.3.
    # This implies high latency (2s) gives HIGHER score than 0s?
    # That contradicts "latency penalty".
    
    # Let's assume the formula in SC-002 meant:
    # score = 0.4 * intent + 0.3 * (1 - normalized_latency) + ...
    # Where normalized_latency = min(1, latency/2.0).
    # If latency=0, normalized=0, term=0.3.
    # If latency=2, normalized=1, term=0.
    
    # The provided function calculate_latency_penalty returns 1 - normalized.
    # So if we want (1 - normalized), we just use the return value of calculate_latency_penalty?
    # No, calculate_latency_penalty returns (1 - normalized).
    # So (1 - penalty) would be (1 - (1 - normalized)) = normalized.
    # That would mean high latency (normalized=1) -> term=0.3. Low latency (normalized=0) -> term=0.
    # That is definitely wrong for a penalty.
    
    # Correction: The formula in SC-002 is likely:
    # score = 0.4 * intent + 0.3 * (1 - (latency/2.0)) + ...
    # Which is 0.3 * (1 - normalized_latency).
    # If we define `latency_penalty` as `normalized_latency`, then it's 0.3 * (1 - penalty).
    # But the function name `calculate_latency_penalty` implies it returns the penalty amount.
    # If penalty = normalized_latency, then:
    # latency=0 -> penalty=0 -> term=0.3.
    # latency=2 -> penalty=1 -> term=0.
    # This makes sense.
    
    # However, the implementation of calculate_latency_penalty is:
    # penalty = 1 - min(1, latency/2.0).
    # This returns 1 when latency=0, and 0 when latency=2.
    # This is the REVERSE of a standard penalty.
    # Let's assume the formula in SC-002 meant:
    # score = 0.4 * intent + 0.3 * (latency_penalty) + ...
    # where latency_penalty is the function defined (1 - norm).
    # Then latency=0 -> penalty=1 -> term=0.3.
    # latency=2 -> penalty=0 -> term=0.
    # This makes sense.
    
    # So the formula in the docstring might be slightly misleading if interpreted strictly.
    # We will use: score = 0.4 * intent + 0.3 * (1 - min(1, latency/2.0)) + 0.3 * ui
    # Which is exactly 0.4 * intent + 0.3 * (calculate_latency_penalty) + 0.3 * ui
    
    term_latency = 0.3 * latency_penalty
    return 0.4 * intent_match + term_latency + 0.3 * ui_completeness

def score_interaction(interaction: Dict[str, Any]) -> float:
    """Score a single interaction based on the rubric."""
    intent = interaction.get('intent_match', 0.0)
    latency = interaction.get('latency_seconds', 0.0)
    ui_comp = interaction.get('ui_completeness', 0.0)
    
    lat_pen = calculate_latency_penalty(latency)
    return calculate_alignment_score(intent, lat_pen, ui_comp)

def main():
    # Test
    print(f"Latency Penalty (0s): {calculate_latency_penalty(0.0)}")
    print(f"Latency Penalty (1s): {calculate_latency_penalty(1.0)}")
    print(f"Latency Penalty (2s): {calculate_latency_penalty(2.0)}")
    print(f"Score (1, 0s, 1): {score_interaction({'intent_match': 1, 'latency_seconds': 0, 'ui_completeness': 1})}")

if __name__ == "__main__":
    main()
