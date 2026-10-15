"""
Generates synthetic search trajectories with controlled semantic density.

This script produces a dataset where 'critical evidence' is injected at a specific turn.
The evidence block is generated to target a specific entropy per token, which
determines the density level (low, medium, high).
"""

import json
import random
import string
import argparse
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List

from code.utils.entropy import entropy_per_token
from code.utils.heuristics import calculate_composite_density

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Constants for density bins (target entropy bits/token)
# Low: ~1.5, Medium: ~3.0, High: ~4.5
DENSITY_CONFIG = {
    "low": {"target_entropy": 1.5, "min_samples": 150},
    "medium": {"target_entropy": 3.0, "min_samples": 150},
    "high": {"target_entropy": 4.5, "min_samples": 150},
}

def ensure_config_directory() -> None:
    """Ensure the config directory exists."""
    Path("code/config").mkdir(parents=True, exist_ok=True)

def load_terms() -> List[str]:
    """Load technical terms from the JSON config."""
    path = Path("code/config/density_terms.json")
    if not path.exists():
        logger.warning("density_terms.json not found, using empty list.")
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def generate_generic_text(length: int = 200) -> str:
    """Generate a non-critical turn – simple low-entropy filler."""
    # Repetitive text to keep entropy low
    filler = "The search continues. Looking for more information. "
    return (filler * (length // len(filler) + 1))[:length]

def _alphabet_for_target(target_entropy: float) -> List[str]:
    """
    Choose an alphabet size that yields an entropy close to the target.
    Entropy per token ≈ log2(|alphabet|) when characters are chosen uniformly.
    """
    size = int(round(2**target_entropy))
    # Use a mix of characters to avoid encoding issues
    chars = string.ascii_letters + string.digits + string.punctuation + " "
    if size > len(chars):
        # Expand alphabet if target is very high (unlikely for these targets)
        return list(chars)
    return random.sample(chars, size)

def generate_text_for_target_entropy(target_entropy: float, terms: List[str]) -> str:
    """
    Produce a text block whose entropy per token is close to target_entropy.
    """
    alphabet = _alphabet_for_target(target_entropy)
    # Mix in some technical terms to ensure technical_token_ratio is non-zero
    # but primarily drive entropy via the alphabet size.
    text_parts = []
    length = 200
    
    # Inject a few technical terms randomly
    if terms:
        for _ in range(5):
            text_parts.append(random.choice(terms))
    
    # Fill the rest with alphabet sampling
    while sum(len(p) for p in text_parts) < length:
        text_parts.append(random.choice(alphabet))
    
    text = "".join(text_parts)[:length]
    
    # Verify and iterate if not within tolerance (±0.05 for generator, 
    # the validator is stricter at 0.01, so we iterate until it's very close).
    for _ in range(100):
        actual = entropy_per_token(text)
        if abs(actual - target_entropy) <= 0.01:
            break
        # Adjust slightly: if too low, increase alphabet; if too high, decrease.
        if actual < target_entropy:
            alphabet.append(random.choice(string.ascii_letters))
        else:
            if len(alphabet) > 1:
                alphabet.pop()
        
        text_parts = [random.choice(alphabet) for _ in range(length)]
        if terms:
            # Re-inject terms
            for i in range(5):
                text_parts[random.randint(0, length-1)] = random.choice(terms)[0]
        text = "".join(text_parts)
        
    return text

def build_turn(turn_index: int, is_critical: bool, target_entropy: float, terms: List[str]) -> Dict[str, Any]:
    """Create a single turn dictionary."""
    if is_critical:
        text = generate_text_for_target_entropy(target_entropy, terms)
    else:
        text = generate_generic_text()
    
    return {
        "turn_index": turn_index,
        "text": text,
        "is_critical": is_critical
    }

def compute_final_density(entropy: float, tech_ratio: float) -> float:
    """Composite density as defined by FR-008, clamped to [0, 1]."""
    # Formula: 0.6 * entropy + 0.4 * tech_ratio
    # Note: entropy is typically 0-8, so we normalize it or use the 
    # composite formula and clamp as requested.
    density = (0.6 * entropy) + (0.4 * tech_ratio)
    return max(0.0, min(1.0, density / 8.0)) # Normalize by max possible entropy 8

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--num-trajectories", type=int, default=500)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", type=str, default="data/raw/trajectories.json")
    args = parser.parse_args()

    random.seed(args.seed)
    ensure_config_directory()
    terms = load_terms()
    
    trajectories = []
    levels = list(DENSITY_CONFIG.keys())
    
    # Balance trajectories across bins
    counts = {lvl: 0 for lvl in levels}
    
    for i in range(args.num_trajectories):
        # Cycle through density levels to ensure balance
        lvl = levels[i % len(levels)]
        counts[lvl] += 1
        
        config = DENSITY_CONFIG[lvl]
        target_entropy = config["target_entropy"]
        
        # Trajectory length T between 5 and 15
        T = random.randint(5, 15)
        crit_idx = random.randint(0, T - 1)
        
        turns = []
        for turn_idx in range(T):
            turns.append(build_turn(turn_idx, turn_idx == crit_idx, target_entropy, terms))
        
        # Metadata for the critical block
        crit_text = turns[crit_idx]["text"]
        actual_entropy = entropy_per_token(crit_text)
        
        # Calculate tech ratio
        words = crit_text.split()
        tech_count = sum(1 for w in words if any(t in w for t in terms))
        tech_ratio = tech_count / len(words) if words else 0.0
        
        final_density = compute_final_density(actual_entropy, tech_ratio)
        
        trajectories.append({
            "trajectory_id": f"traj_{i:03d}",
            "turns": turns,
            "critical_evidence_turn": crit_idx,
            "density_level": lvl,
            "target_entropy": target_entropy,
            "actual_entropy": actual_entropy,
            "technical_token_ratio": tech_ratio,
            "final_density": final_density,
            "is_last_turn": (crit_idx == T - 1)
        })

    # Enforce bin constraints
    for lvl, count in counts.items():
        if count < DENSITY_CONFIG[lvl]["min_samples"]:
            logger.error(f"INSUFFICIENT_SAMPLES_PER_BIN: {lvl} has {count}")
            sys.exit(1)

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(trajectories, f, indent=2)
    
    file_size_mb = out_path.stat().st_size / (1024 * 1024)
    logger.info(f"Generated {len(trajectories)} trajectories. File size: {file_size_mb:.2f} MB")
    logger.info(f"Bin counts: {counts}")

if __name__ == "__main__":
    main()
