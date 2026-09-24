import json
import math
import random
import string
from pathlib import Path
from typing import Any, Dict, List, Tuple

# Standard library imports sorted alphabetically
import hashlib
import logging
import os
import sys
import time
import uuid

# Third-party imports sorted alphabetically
import numpy as np

# Local imports sorted alphabetically
from utils.entropy import calculate_shannon_entropy, clamp_entropy, entropy_per_token
from utils.heuristics import calculate_composite_density, calculate_technical_token_ratio

# Constants
DEFAULT_SEED = 42
MIN_DENSITY = 0.0
MAX_DENSITY = 1.0
DENSITY_TOLERANCE = 0.01
EVIDENCE_BLOCK_PREFIX = "[CRITICAL_EVIDENCE]"
EVIDENCE_BLOCK_SUFFIX = "[/CRITICAL_EVIDENCE]"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


def generate_text_block(density_target: float, length: int = 1000, seed: int = DEFAULT_SEED) -> str:
    """
    Generate a text block with approximate semantic density.
    
    Args:
        density_target: Target density value (0.0 to 1.0)
        length: Approximate length of the text block in characters
        seed: Random seed for reproducibility
        
    Returns:
        Generated text block string
    """
    random.seed(seed)
    np.random.seed(seed)
    
    # Simple heuristic: higher density -> more technical terms
    # This is a simplified model for synthetic data generation
    technical_terms = [
        "search_context", "retrieval_window", "semantic_density", "agent_state",
        "trajectory_log", "masking_policy", "evidence_turn", "focus_decay",
        "stale_observation", "retention_limit", "critical_evidence",
        "heuristic_solver", "logistic_function", "regime_map"
    ]
    
    common_words = [
        "the", "a", "is", "was", "are", "were", "be", "been", "being",
        "have", "has", "had", "do", "does", "did", "will", "would", "could",
        "should", "may", "might", "must", "shall", "can", "need", "dare",
        "ought", "used", "to", "of", "in", "for", "on", "with", "at", "by",
        "from", "up", "about", "into", "over", "after", "and", "but", "or",
        "not", "nor", "yet", "so", "as", "if", "when", "than", "because",
        "while", "although", "though", "since", "unless", "until", "where",
        "whereas", "whether", "which", "who", "whom", "whose", "why"
    ]
    
    text_parts = []
    current_density = 0.0
    
    # Generate words until we reach approximate length
    while sum(len(p) for p in text_parts) < length:
        # Decide whether to use a technical term based on target density
        if random.random() < density_target and technical_terms:
            word = random.choice(technical_terms)
        else:
            word = random.choice(common_words)
        
        # Add punctuation occasionally
        if random.random() < 0.1:
            word += random.choice(['.', ',', ';', ':', '?', '!'])
        
        text_parts.append(word)
    
    return ' '.join(text_parts)[:length]


def inject_critical_evidence(text: str, evidence_index: int, density_boost: float = 0.5) -> str:
    """
    Inject critical evidence block into the text at a specific turn index.
    
    Args:
        text: Original text
        evidence_index: Index of the turn where evidence should be injected
        density_boost: Additional density to apply to the evidence block
        
    Returns:
        Text with injected evidence
    """
    evidence_marker = f"{EVIDENCE_BLOCK_PREFIX}turn_{evidence_index}{EVIDENCE_BLOCK_SUFFIX}"
    return f"{text} {evidence_marker}"


def clamp_density(value: float, min_val: float = MIN_DENSITY, max_val: float = MAX_DENSITY) -> float:
    """
    Clamp density value to valid range.
    
    Args:
        value: Density value to clamp
        min_val: Minimum allowed value
        max_val: Maximum allowed value
        
    Returns:
        Clamped density value
    """
    if value < min_val:
        logger.warning(f"Density value {value} below minimum {min_val}, clamping to {min_val}")
        return min_val
    if value > max_val:
        logger.warning(f"Density value {value} above maximum {max_val}, clamping to {max_val}")
        return max_val
    return value


def validate_density_computation(text: str, expected_density: float, tolerance: float = DENSITY_TOLERANCE) -> bool:
    """
    Validate that computed density matches expected density within tolerance.
    
    Args:
        text: Text to analyze
        expected_density: Expected density value
        tolerance: Acceptable tolerance for density difference
        
    Returns:
        True if density is within tolerance, False otherwise
    """
    computed_density = entropy_per_token(text)
    diff = abs(computed_density - expected_density)
    
    if diff > tolerance:
        logger.warning(
            f"Density mismatch: expected {expected_density:.4f}, "
            f"computed {computed_density:.4f}, diff {diff:.4f}"
        )
        return False
    
    return True


def generate_trajectory(
    trajectory_id: str,
    density_level: str,
    evidence_turn_index: int,
    total_turns: int,
    seed: int = DEFAULT_SEED
) -> Dict[str, Any]:
    """
    Generate a single synthetic trajectory with controlled density.
    
    Args:
        trajectory_id: Unique identifier for the trajectory
        density_level: 'low', 'medium', or 'high'
        evidence_turn_index: Index of the turn containing critical evidence
        total_turns: Total number of turns in the trajectory
        seed: Random seed for reproducibility
        
    Returns:
        Dictionary containing trajectory data
    """
    # Map density levels to target values
    density_map = {
        'low': 0.2,
        'medium': 0.5,
        'high': 0.8
    }
    
    if density_level not in density_map:
        raise ValueError(f"Invalid density level: {density_level}. Must be one of {list(density_map.keys())}")
    
    target_density = density_map[density_level]
    
    # Generate text for each turn
    turns = []
    for turn_idx in range(total_turns):
        # Adjust density for evidence turn
        if turn_idx == evidence_turn_index:
            turn_density = min(target_density + 0.3, 1.0)
        else:
            turn_density = target_density
        
        turn_text = generate_text_block(
            density_target=turn_density,
            length=500 + random.randint(0, 200),
            seed=seed + turn_idx
        )
        
        # Inject evidence if this is the evidence turn
        if turn_idx == evidence_turn_index:
            turn_text = inject_critical_evidence(turn_text, evidence_turn_index)
        
        turns.append({
            'turn_index': turn_idx,
            'text': turn_text,
            'density': entropy_per_token(turn_text)
        })
    
    # Calculate overall trajectory density
    all_text = ' '.join([t['text'] for t in turns])
    overall_density = entropy_per_token(all_text)
    
    return {
        'trajectory_id': trajectory_id,
        'density_level': density_level,
        'target_density': target_density,
        'actual_density': overall_density,
        'evidence_turn_index': evidence_turn_index,
        'total_turns': total_turns,
        'is_critical': True,
        'turns': turns,
        'metadata': {
            'generated_at': time.strftime('%Y-%m-%d %H:%M:%S'),
            'seed': seed,
            'version': '1.0'
        }
    }


def main():
    """
    Main function to generate synthetic trajectories.
    """
    logger.info("Starting synthetic trajectory generation...")
    
    # Configuration
    num_trajectories = 500
    output_path = Path("data/raw/synthetic_trajectories.json")
    total_turns = 20
    seeds = [DEFAULT_SEED + i for i in range(num_trajectories)]
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Density distribution: 30% low, 40% medium, 30% high
    density_levels = ['low'] * 150 + ['medium'] * 200 + ['high'] * 150
    random.shuffle(density_levels)
    
    trajectories = []
    
    for i in range(num_trajectories):
        seed = seeds[i]
        density_level = density_levels[i]
        evidence_turn = random.randint(5, 15)  # Evidence somewhere in the middle
        
        trajectory = generate_trajectory(
            trajectory_id=f"traj_{i:04d}",
            density_level=density_level,
            evidence_turn_index=evidence_turn,
            total_turns=total_turns,
            seed=seed
        )
        
        trajectories.append(trajectory)
        
        if (i + 1) % 100 == 0:
            logger.info(f"Generated {i + 1}/{num_trajectories} trajectories")
    
    # Write to JSON
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(trajectories, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Successfully generated {num_trajectories} trajectories")
    logger.info(f"Output saved to: {output_path}")
    
    # Validation summary
    density_counts = {}
    for traj in trajectories:
        level = traj['density_level']
        density_counts[level] = density_counts.get(level, 0) + 1
    
    logger.info("Density distribution:")
    for level, count in sorted(density_counts.items()):
        logger.info(f"  {level}: {count} trajectories")
    
    return trajectories


if __name__ == "__main__":
    main()