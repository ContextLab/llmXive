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

from llmxive_toolkit import paths
from code.utils.entropy import entropy_per_token
from code.utils.heuristics import calculate_composite_density, calculate_technical_token_ratio

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
    paths.code("config").mkdir(parents=True, exist_ok=True)

def load_terms() -> List[str]:
    """Load technical terms from the JSON config."""
    path = paths.code("config", "density_terms.json")
    if not path.exists():
        logger.warning("density_terms.json not found, using empty list.")
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        logger.error(f"Error loading terms: {e}")
        return []

def generate_generic_text(length: int = 200) -> str:
    """Generate a non-critical turn – simple low-entropy filler."""
    filler = "The search continues. Looking for more information. "
    return (filler * (length // len(filler) + 1))[:length]

def generate_text_for_target_entropy(target_entropy: float, terms: List[str]) -> str:
    """
    Produce a text block whose entropy per token is close to target_entropy.
    Iteratively adjusts alphabet size to converge on the target.
    """
    # Entropy per token approx log2(|alphabet|)
    S = int(round(2**target_entropy))
    chars = string.ascii_letters + string.digits + string.punctuation + " "
    alphabet = random.sample(chars, min(S, len(chars)))
    
    length = 200
    for _ in range(200):
      # Generate text from current alphabet
      text_list = random.choices(alphabet, k=length)
      
      # Inject some technical terms to ensure ratio is non-zero if terms exist
      if terms:
          for _ in range(3):
              pos = random.randint(0, length - 1)
              term = random.choice(terms)
              # We replace one char with a char from the term to avoid shifting indices
              text_list[pos] = term[0] if term else ' '
      
      text = "".join(text_list)
      actual = entropy_per_token(text)
      
      if abs(actual - target_entropy) <= 0.01:
          return text
      
      # Adjust alphabet size to nudge entropy
      if actual < target_entropy:
          if len(alphabet) < len(chars):
              # Add a character not currently in the alphabet
              remaining = [c for c in chars if c not in alphabet]
              if remaining:
                  alphabet.append(random.choice(remaining))
      else:
          if len(alphabet) > 1:
              alphabet.pop()
    
    # Fallback to last generated text if convergence fails
    return "".join(text_list)

def build_turn(turn_index: int, is_critical: bool, target_entropy: float, terms: List[str]) -> Dict[str, Any]:
    """Create a single turn dictionary including the required entropy_per_token."""
    if is_critical:
        text = generate_text_for_target_entropy(target_entropy, terms)
    else:
        text = generate_generic_text()
    
    return {
        "turn_index": turn_index,
        "text": text,
        "is_critical": is_critical,
        "entropy_per_token": entropy_per_token(text)
    }

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=500)
    parser.add_argument("--num-trajectories", type=int, dest="count", default=500, help="Alias for --count")
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
    
    for i in range(args.count):
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
        
        # Use the project API for composite density and technical ratio
        final_density = calculate_composite_density(crit_text, terms)
        tech_ratio = calculate_technical_token_ratio(crit_text, set(terms))
        
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

    # Enforce bin constraints: abort with error INSUFFICIENT_SAMPLES_PER_BIN
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