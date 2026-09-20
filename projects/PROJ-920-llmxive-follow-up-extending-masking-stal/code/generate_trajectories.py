import json
import math
import random
import string
from pathlib import Path
from typing import List, Dict, Any, Tuple

import sys
import os

# Add parent directory to path to allow imports from utils if needed
# though this task focuses on generation logic
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.utils.entropy import calculate_shannon_entropy, clamp_entropy, entropy_per_token
from code.utils.heuristics import calculate_technical_token_ratio, calculate_composite_density

# Constants for trajectory generation
NUM_TRAJECTORIES = 500
DENSITY_LEVELS = ['low', 'medium', 'high']
MIN_TURNS = 10
MAX_TURNS = 50
EVIDENCE_TURNS_PERCENTAGE = 0.2  # 20% of turns will contain critical evidence

# Technical token list as defined in heuristics.py requirements
TECHNICAL_TOKENS = [
    'search_context', 'retrieval_window', 'semantic_density', 'agent_state',
    'trajectory_log', 'masking_policy', 'evidence_turn', 'focus_decay',
    'stale_observation', 'retention_limit', 'critical_evidence',
    'heuristic_solver', 'logistic_function', 'regime_map'
]

def generate_text_block(target_density: float, length: int, include_technical: bool = False) -> str:
    """
    Generate a text block with a target Shannon entropy per token.
    This is a simulation approach: we generate text and adjust complexity.
    Since exact entropy control is hard, we generate text with specific
    character distributions to approximate the target density.
    """
    if length <= 0:
        return ""

    # Base alphabet
    base_chars = string.ascii_lowercase + string.digits
    # High entropy chars (more variety)
    high_entropy_chars = base_chars + string.ascii_uppercase + string.punctuation + ' '

    # Adjust character selection probability based on target density
    # Lower density -> more repetitive (lower entropy)
    # Higher density -> more varied (higher entropy)
    # Normalize target_density to a probability factor (assuming max entropy ~ 6 bits for our char set)
    if target_density <= 0:
        target_density = 0.01 # Clamp to avoid zero issues

    # Simple heuristic: use a weighted selection
    # If target is low, use mostly base_chars. If high, use high_entropy_chars.
    # We map target_density (approx 0-5 bits) to a weight.
    weight_high = min(1.0, target_density / 4.0)
    
    text_chars = []
    for _ in range(length):
        if include_technical and random.random() < 0.05: # 5% chance of technical token
            token = random.choice(TECHNICAL_TOKENS)
            text_chars.append(token)
        else:
            if random.random() < weight_high:
                char = random.choice(high_entropy_chars)
            else:
                char = random.choice(base_chars)
            text_chars.append(char)
    
    # Join and ensure we have a string
    text = "".join(text_chars)
    return text

def inject_critical_evidence(text: str, evidence_turn_index: int, total_turns: int) -> str:
    """
    Inject a specific critical evidence marker into the text.
    This simulates the 'critical evidence' turn in the trajectory.
    """
    marker = f"[CRITICAL_EVIDENCE_TURN_{evidence_turn_index}]"
    # Insert marker at a specific position relative to the text length
    insert_pos = int(len(text) * (evidence_turn_index / total_turns))
    return text[:insert_pos] + marker + text[insert_pos:]

def clamp_density(value: float) -> float:
    """
    Clamp density values to a valid range to prevent zero or negative density.
    Implements the edge case requirement for FR-008.
    """
    if value <= 0:
        return 0.01 # Minimum non-zero density
    return value

def validate_density_computation(text: str, expected_density: float, tolerance: float = 0.01) -> bool:
    """
    Validate that the computed density of the generated text matches the expected density.
    Returns True if within tolerance, False otherwise.
    """
    if not text:
        return False
    
    # Calculate entropy per token (bytes)
    computed_density = entropy_per_token(text)
    
    # Check if within tolerance
    return abs(computed_density - expected_density) <= tolerance

def generate_trajectory(trajectory_id: int, density_level: str, total_turns: int) -> Dict[str, Any]:
    """
    Generate a single trajectory with controlled density and critical evidence.
    """
    # Map density level to target entropy
    if density_level == 'low':
        target_density = 1.5
    elif density_level == 'medium':
        target_density = 3.0
    elif density_level == 'high':
        target_density = 4.5
    else:
        target_density = 3.0 # Default

    # Ensure we have a reasonable number of turns
    if total_turns < MIN_TURNS:
        total_turns = MIN_TURNS

    turns = []
    evidence_turn_index = -1

    # Determine if this trajectory has critical evidence
    has_evidence = random.random() < EVIDENCE_TURNS_PERCENTAGE
    
    if has_evidence:
        evidence_turn_index = random.randint(0, total_turns - 1)

    for turn_idx in range(total_turns):
        # Generate text for this turn
        # Adjust length to vary entropy slightly per turn but keep average near target
        turn_length = random.randint(50, 200)
        turn_text = generate_text_block(target_density, turn_length, include_technical=(turn_idx % 3 == 0))

        # Inject evidence if this is the designated turn
        if turn_idx == evidence_turn_index:
            turn_text = inject_critical_evidence(turn_text, evidence_turn_index, total_turns)
            # Recalculate density for this specific turn to ensure it's recorded correctly
            # Note: Injecting text changes entropy, so we re-calc
            pass

        # Calculate actual density for this turn
        actual_density = entropy_per_token(turn_text)
        actual_density = clamp_density(actual_density)

        turns.append({
            "turn_index": turn_idx,
            "text": turn_text,
            "density": actual_density,
            "is_critical_evidence": (turn_idx == evidence_turn_index)
        })

    # Calculate overall trajectory density (average of turn densities)
    trajectory_density = sum(t["density"] for t in turns) / len(turns) if turns else 0.0
    trajectory_density = clamp_density(trajectory_density)

    return {
        "trajectory_id": trajectory_id,
        "density_level": density_level,
        "target_density": target_density,
        "actual_trajectory_density": trajectory_density,
        "total_turns": total_turns,
        "evidence_turn_index": evidence_turn_index if has_evidence else -1,
        "has_critical_evidence": has_evidence,
        "turns": turns
    }

def main():
    """
    Main entry point to generate 500 trajectories and save to data/raw/.
    """
    output_dir = Path("data/raw")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = output_dir / "trajectories.json"
    
    trajectories = []
    
    print(f"Generating {NUM_TRAJECTORIES} trajectories...")
    
    for i in range(NUM_TRAJECTORIES):
        # Distribute density levels roughly evenly
        density_level = DENSITY_LEVELS[i % len(DENSITY_LEVELS)]
        total_turns = random.randint(MIN_TURNS, MAX_TURNS)
        
        trajectory = generate_trajectory(i, density_level, total_turns)
        trajectories.append(trajectory)
        
        # Optional: Progress indicator
        if (i + 1) % 100 == 0:
            print(f"Generated {i + 1}/{NUM_TRAJECTORIES} trajectories.")

    # Write to JSON
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(trajectories, f, indent=2)
    
    print(f"Successfully generated {len(trajectories)} trajectories.")
    print(f"Output saved to: {output_file.absolute()}")
    
    # Verification: Check a sample
    if trajectories:
        sample = trajectories[0]
        print(f"Sample trajectory ID: {sample['trajectory_id']}, Density: {sample['actual_trajectory_density']:.4f}")

if __name__ == "__main__":
    main()
