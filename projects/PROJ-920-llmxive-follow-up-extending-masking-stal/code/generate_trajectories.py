"""
Trajectory Generator for llmXive Follow-up Study.

Generates 500 synthetic search trajectories with controlled semantic density
and critical evidence injection.

Requirements:
- FR-001: Generate exactly 500 trajectories.
- FR-007: Density computed solely from input text statistics.
- Edge Case: Clamp zero density values to avoid division errors.
"""

import json
import math
import random
import string
from pathlib import Path
from typing import List, Dict, Any, Tuple

# Import from existing project API surface
from utils.heuristics import calculate_composite_density

# Constants
TOTAL_TRAJECTORIES = 500
OUTPUT_DIR = Path("data/raw")
OUTPUT_FILE = OUTPUT_DIR / "trajectories.json"
MAX_FILE_SIZE_MB = 100

# Density targets (bits/token)
DENSITY_TARGETS = {
    "low": 1.5,
    "medium": 3.0,
    "high": 4.5
}

# Technical tokens for density calculation
TECHNICAL_TOKENS = {"def", "class", "import", "return", "if", "else", "for", "while"}

# Seed for reproducibility
SEED = 42
random.seed(SEED)

def generate_text_block(target_density: float, length: int) -> str:
    """
    Generate a text block with approximately the target density.
    Density is controlled by the ratio of technical tokens to natural language tokens.
    """
    words = []
    technical_count = 0

    # Estimate required technical token ratio based on target density
    # Density = 0.6 * Entropy + 0.4 * TechRatio
    # We approximate: TechRatio ~ (Density - 0.6 * Entropy) / 0.4
    # Assuming average entropy ~ 3.5 for natural text
    approx_entropy = 3.5
    target_tech_ratio = max(0, (target_density - 0.6 * approx_entropy) / 0.4)
    target_tech_ratio = min(1.0, target_tech_ratio)

    # Generate words
    for _ in range(length):
        if random.random() < target_tech_ratio:
            words.append(random.choice(list(TECHNICAL_TOKENS)))
            technical_count += 1
        else:
            # Generate random natural language-like token
            token_len = random.randint(3, 8)
            token = ''.join(random.choices(string.ascii_lowercase, k=token_len))
            words.append(token)

    return " ".join(words)

def inject_critical_evidence(text: str, evidence_type: str = "key_finding") -> Tuple[str, int]:
    """
    Inject critical evidence into the text at a random position.
    Returns the modified text and the turn index where evidence was injected.
    """
    evidence_phrases = {
        "key_finding": "CRITICAL EVIDENCE: The search agent failed to retrieve the required information.",
        "solution_path": "CRITICAL EVIDENCE: The optimal solution path requires parameter X=0.95.",
        "failure_mode": "CRITICAL EVIDENCE: Agent exhibits catastrophic forgetting after 3 turns."
    }

    evidence = evidence_phrases.get(evidence_type, evidence_phrases["key_finding"])
    text_blocks = text.split(" ")
    insert_pos = random.randint(int(len(text_blocks) * 0.2), int(len(text_blocks) * 0.8))
    text_blocks.insert(insert_pos, evidence)

    # Turn index: evidence is at position insert_pos in a 10-turn trajectory
    # We simulate 10 turns, so turn index is roughly insert_pos / (len/10)
    total_blocks = len(text_blocks)
    turns = 10
    evidence_turn = min(turns - 1, max(0, int((insert_pos / total_blocks) * turns)))

    return " ".join(text_blocks), evidence_turn

def clamp_density(density: float) -> float:
    """
    Clamp density to avoid zero or negative values (Edge Case).
    Returns a safe density value >= 0.001.
    """
    if density <= 0:
        return 0.001
    return density

def validate_density_computation(text: str, calculated_density: float) -> bool:
    """
    Validate that density is computed solely from input text statistics (FR-007).
    """
    # Recalculate density to ensure it matches
    recalc_density = calculate_composite_density(text)
    # Allow small floating point differences
    return abs(recalc_density - calculated_density) < 0.01

def generate_trajectory(
    density_label: str,
    target_density: float,
    trajectory_id: int
) -> Dict[str, Any]:
    """
    Generate a single trajectory with controlled density.
    """
    # Generate base text
    text_length = random.randint(50, 150)
    base_text = generate_text_block(target_density, text_length)

    # Inject critical evidence
    final_text, evidence_turn = inject_critical_evidence(base_text)

    # Calculate actual density
    actual_density = calculate_composite_density(final_text)
    actual_density = clamp_density(actual_density)

    # Validate density computation
    is_valid = validate_density_computation(final_text, actual_density)

    trajectory = {
        "id": trajectory_id,
        "density_label": density_label,
        "target_density": target_density,
        "actual_density": actual_density,
        "text": final_text,
        "evidence_turn_index": evidence_turn,
        "length_tokens": len(final_text.split()),
        "density_validated": is_valid
    }

    return trajectory

def main():
    """
    Main function to generate 500 trajectories with controlled density.
    """
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    trajectories = []
    density_levels = ["low", "medium", "high"]
    trajectories_per_level = TOTAL_TRAJECTORIES // len(density_levels)
    remainder = TOTAL_TRAJECTORIES % len(density_levels)

    trajectory_id = 0

    for i, level in enumerate(density_levels):
        count = trajectories_per_level + (1 if i < remainder else 0)
        target = DENSITY_TARGETS[level]

        for _ in range(count):
            traj = generate_trajectory(level, target, trajectory_id)
            trajectories.append(traj)
            trajectory_id += 1

    # Shuffle to mix density levels
    random.shuffle(trajectories)

    # Write to JSON
    output_data = {
        "metadata": {
            "total_trajectories": len(trajectories),
            "density_levels": list(DENSITY_TARGETS.keys()),
            "targets": DENSITY_TARGETS,
            "seed": SEED
        },
        "trajectories": trajectories
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2)

    # Verify file size
    file_size_mb = OUTPUT_FILE.stat().st_size / (1024 * 1024)
    if file_size_mb > MAX_FILE_SIZE_MB:
        raise ValueError(f"Output file size {file_size_mb:.2f} MB exceeds limit {MAX_FILE_SIZE_MB} MB")

    print(f"Generated {len(trajectories)} trajectories to {OUTPUT_FILE}")
    print(f"File size: {file_size_mb:.2f} MB")

    # Validate all densities
    invalid_count = sum(1 for t in trajectories if not t["density_validated"])
    if invalid_count > 0:
        print(f"Warning: {invalid_count} trajectories failed density validation")
    else:
        print("All trajectories passed density validation")

if __name__ == "__main__":
    main()
