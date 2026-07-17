import json
import math
import random
import string
from pathlib import Path
from typing import List, Dict, Any, Tuple

# Standard library imports
import argparse
import sys

# Third-party imports
import numpy as np

# Local imports
from utils.heuristics import calculate_composite_density


def generate_text_block(length: int, density_target: float) -> str:
    """
    Generate a text block of approximate length with semantic density
    tuned towards the target.
    
    Args:
        length: Target number of characters.
        density_target: Target density value (0.0 to 1.0).
        
    Returns:
        A generated text string.
    """
    # Simple heuristic: vary content based on density target
    # Low density: more common words, simpler structure
    # High density: more technical words, complex structure
    
    if density_target < 0.3:
        words = ["the", "a", "is", "it", "and", "to", "of", "in", "for", "on"]
        template = " ".join(random.choices(words, k=length // 4))
    elif density_target < 0.7:
        words = ["algorithm", "data", "model", "system", "process", "result", "input", "output"]
        template = " ".join(random.choices(words, k=length // 5))
    else:
        words = ["neural", "gradient", "backpropagation", "optimization", "loss", "epoch", "batch"]
        template = " ".join(random.choices(words, k=length // 6))
        
    # Ensure we hit length roughly
    if len(template) < length:
        template += " " * (length - len(template))
    elif len(template) > length:
        template = template[:length]
        
    return template


def inject_critical_evidence(text: str, evidence_turn: int, total_turns: int) -> Tuple[str, int]:
    """
    Inject a critical evidence marker into the text at a specific turn.
    
    Args:
        text: The base text to inject into.
        evidence_turn: The turn index where evidence should be injected.
        total_turns: Total number of turns in the trajectory.
        
    Returns:
        Tuple of (modified_text, evidence_turn_index).
    """
    if evidence_turn < 0 or evidence_turn >= total_turns:
        evidence_turn = total_turns // 2
        
    # Inject a marker that represents critical evidence
    marker = f"\n[CRITICAL_EVIDENCE_TURN_{evidence_turn}]\n"
    segments = text.split("\n")
    
    # Ensure we have enough segments
    while len(segments) <= evidence_turn:
        segments.append("placeholder")
        
    segments[evidence_turn] = marker + segments[evidence_turn]
    return "\n".join(segments), evidence_turn


def clamp_density(value: float, min_val: float = 0.0, max_val: float = 1.0) -> float:
    """
    Clamp a density value to the specified range.
    
    Args:
        value: The value to clamp.
        min_val: Minimum allowed value.
        max_val: Maximum allowed value.
        
    Returns:
        The clamped value.
    """
    return max(min_val, min(max_val, value))


def validate_density_computation(text: str, expected_density: float, tolerance: float = 0.01) -> bool:
    """
    Validate that the computed density matches the expected density within tolerance.
    
    Args:
        text: The text to compute density for.
        expected_density: The expected density value.
        tolerance: Allowed deviation.
        
    Returns:
        True if density is within tolerance, False otherwise.
    """
    if not text:
        return expected_density == 0.0
        
    computed = calculate_composite_density(text)
    return abs(computed - expected_density) <= tolerance


def generate_trajectory(
    trajectory_id: int,
    density_level: str,
    total_turns: int = 50,
    evidence_turn: int = None,
    seed: int = None
) -> Dict[str, Any]:
    """
    Generate a single trajectory with controlled density and critical evidence.
    
    Args:
        trajectory_id: Unique identifier for the trajectory.
        density_level: 'low', 'medium', or 'high'.
        total_turns: Number of turns in the trajectory.
        evidence_turn: Turn index for critical evidence (random if None).
        seed: Random seed for reproducibility.
        
    Returns:
        A dictionary containing the trajectory data.
    """
    if seed is not None:
        random.seed(seed)
        np.random.seed(seed)
        
    # Map density level to target values
    density_map = {
        'low': 0.2,
        'medium': 0.5,
        'high': 0.8
    }
    target_density = density_map.get(density_level, 0.5)
    
    # Generate text
    text_length = 1000 + random.randint(0, 500)
    base_text = generate_text_block(text_length, target_density)
    
    # Handle evidence turn
    if evidence_turn is None:
        evidence_turn = random.randint(0, total_turns - 1)
        
    # Inject evidence
    final_text, actual_evidence_turn = inject_critical_evidence(
        base_text, evidence_turn, total_turns
    )
    
    # Compute actual density
    actual_density = calculate_composite_density(final_text)
    actual_density = clamp_density(actual_density)
    
    # Validate
    is_valid = validate_density_computation(final_text, target_density)
    
    return {
        "trajectory_id": trajectory_id,
        "density_level": density_level,
        "target_density": target_density,
        "actual_density": actual_density,
        "total_turns": total_turns,
        "critical_evidence_turn": actual_evidence_turn,
        "text": final_text,
        "is_valid": is_valid
    }


def main():
    """Main entry point for trajectory generation."""
    parser = argparse.ArgumentParser(description="Generate synthetic search trajectories.")
    parser.add_argument(
        "--output", "-o",
        type=str,
        default="data/raw/trajectories.json",
        help="Output JSON file path"
    )
    parser.add_argument(
        "--count", "-n",
        type=int,
        default=500,
        help="Number of trajectories to generate (FR-001)"
    )
    parser.add_argument(
        "--seed", "-s",
        type=int,
        default=42,
        help="Random seed for reproducibility"
    )
    
    args = parser.parse_args()
    
    # Ensure output directory exists
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    trajectories = []
    density_levels = ['low', 'medium', 'high']
    
    for i in range(args.count):
        # Cycle through density levels
        level = density_levels[i % 3]
        traj = generate_trajectory(
            trajectory_id=i,
            density_level=level,
            seed=args.seed + i
        )
        trajectories.append(traj)
        
        # Progress report
        if (i + 1) % 100 == 0:
            print(f"Generated {i + 1}/{args.count} trajectories...")
    
    # Write output
    output_data = {
        "metadata": {
            "total_trajectories": len(trajectories),
            "density_levels": density_levels,
            "generation_seed": args.seed
        },
        "trajectories": trajectories
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
        
    print(f"Successfully generated {len(trajectories)} trajectories to {output_path}")
    
    # File size check (FR-001: ≤ 100 MB)
    file_size = output_path.stat().st_size
    if file_size > 100 * 1024 * 1024:
        print(f"WARNING: Output file size ({file_size} bytes) exceeds 100 MB limit")
    else:
        print(f"Output file size: {file_size} bytes (≤ 100 MB limit)")


if __name__ == "__main__":
    main()