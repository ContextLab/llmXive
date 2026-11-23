"""
Generates synthetic search trajectories with controlled semantic density.

The script streams each trajectory as a JSON‑Lines record to keep RAM usage
low (≤ 2 GB). It balances the design across three density levels (low,
medium, high) and enforces a minimum of 150 trajectories per level.

CLI usage (as referenced in quickstart.md):

    python code/generate_trajectories.py \\
        --num-trajectories 500 \\
        --seed 42 \\
        --output data/raw/trajectories.jsonl
"""

import argparse
import json
import logging
import random
import string
import sys
from pathlib import Path
from typing import Any, Dict, List

from llmxive_toolkit import paths
from code.utils.entropy import entropy_per_token
from code.utils.heuristics import (
    calculate_composite_density,
    calculate_technical_token_ratio,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Target entropy (bits per token) for each density level
DENSITY_CONFIG = {
    "low": {"target_entropy": 1.5, "min_samples": 150},
    "medium": {"target_entropy": 3.0, "min_samples": 150},
    "high": {"target_entropy": 4.5, "min_samples": 150},
}


def ensure_config_directory() -> None:
    """Ensure the config directory exists."""
    paths.code("config").mkdir(parents=True, exist_ok=True)


def load_terms() -> List[str]:
    """
    Load technical terms from the JSON config.

    The file may contain either a list of terms or a mapping; in the latter
    case we fall back to using the keys as the term list.
    """
    path = paths.code("config", "density_terms.json")
    if not path.exists():
        logger.warning("density_terms.json not found, using empty list.")
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            # Legacy format: keys are the terms
            return list(data.keys())
        logger.error(
            "density_terms.json has unexpected format; expected list or dict."
        )
        return []
    except (json.JSONDecodeError, IOError) as e:
        logger.error(f"Error loading terms: {e}")
        return []


def generate_generic_text(length: int = 200) -> str:
    """Generate a low‑entropy filler turn."""
    filler = "The search continues. Looking for more information. "
    return (filler * (length // len(filler) + 1))[:length]


def generate_text_for_target_entropy(target_entropy: float, terms: List[str]) -> str:
    """
    Produce a text block whose entropy per token is close to target_entropy.
    Adjusts the alphabet size iteratively. If technical terms are provided,
    they are injected to ensure a non‑zero technical token ratio.
    """
    # Approximate required alphabet size: entropy ≈ log2(|alphabet|)
    alphabet_size = max(2, int(round(2 ** target_entropy)))
    chars = string.ascii_letters + string.digits + string.punctuation + " "
    # Ensure we never exceed the available character set
    alphabet = random.sample(chars, min(alphabet_size, len(chars)))

    length = 200
    best_text = ""
    best_diff = float("inf")

    for _ in range(250):  # limited iterations to keep runtime bounded
        text_chars = random.choices(alphabet, k=length)

        # Inject a few technical terms (if any) to keep the ratio > 0
        if terms:
            for _ in range(3):
                pos = random.randint(0, length - 1)
                term = random.choice(terms)
                # Replace a single character with the first character of the term
                text_chars[pos] = term[0] if term else " "

        text = "".join(text_chars)
        actual = entropy_per_token(text)

        diff = abs(actual - target_entropy)
        if diff < best_diff:
            best_diff = diff
            best_text = text

        if diff <= 0.01:
            return text

        # Adjust alphabet size based on whether we are above or below target
        if actual < target_entropy and len(alphabet) < len(chars):
            # Add a new character to increase entropy
            remaining = [c for c in chars if c not in alphabet]
            if remaining:
                alphabet.append(random.choice(remaining))
        elif actual > target_entropy and len(alphabet) > 2:
            # Remove a character to decrease entropy
            alphabet.pop()

    # Return the best attempt if perfect convergence wasn't reached
    return best_text


def build_turn(
    turn_index: int,
    is_critical: bool,
    target_entropy: float,
    terms: List[str],
) -> Dict[str, Any]:
    """Create a turn dictionary with required metadata."""
    if is_critical:
        text = generate_text_for_target_entropy(target_entropy, terms)
    else:
        text = generate_generic_text()
    return {
        "turn_index": turn_index,
        "text": text,
        "is_critical": is_critical,
        "entropy_per_token": entropy_per_token(text),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic trajectories.")
    parser.add_argument(
        "--num-trajectories",
        type=int,
        default=500,
        help="Total number of trajectories to generate.",
    )
    # Backward‑compatible alias
    parser.add_argument(
        "--count",
        type=int,
        default=None,
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility.",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/raw/trajectories.jsonl",
        help="Path to the output JSON‑Lines file.",
    )
    args = parser.parse_args()

    # Resolve possible alias usage
    total_trajectories = args.num_trajectories if args.count is None else args.count
    random.seed(args.seed)
    ensure_config_directory()
    terms = load_terms()

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Prepare counters for density levels
    levels = list(DENSITY_CONFIG.keys())
    counts = {lvl: 0 for lvl in levels}

    with open(output_path, "w", encoding="utf-8") as out_f:
        for i in range(total_trajectories):
            # Cycle through levels to keep balance
            lvl = levels[i % len(levels)]
            counts[lvl] += 1
            cfg = DENSITY_CONFIG[lvl]
            target_entropy = cfg["target_entropy"]

            # Random trajectory length between 5 and 15 turns
            T = random.randint(5, 15)
            crit_idx = random.randint(0, T - 1)

            turns = [
                build_turn(t_idx, t_idx == crit_idx, target_entropy, terms)
                for t_idx in range(T)
            ]

            crit_text = turns[crit_idx]["text"]
            actual_entropy = entropy_per_token(crit_text)
            final_density = calculate_composite_density(crit_text, terms)
            tech_ratio = calculate_technical_token_ratio(crit_text, set(terms))

            trajectory = {
                "trajectory_id": f"traj_{i:03d}",
                "turns": turns,
                "critical_evidence_turn": crit_idx,
                "density_level": lvl,
                "target_entropy": target_entropy,
                "actual_entropy": actual_entropy,
                "technical_token_ratio": tech_ratio,
                "final_density": final_density,
                "is_last_turn": crit_idx == (T - 1),
            }

            # Write as a single JSON line
            out_f.write(json.dumps(trajectory, ensure_ascii=False))
            out_f.write("\n")

    # Verify bin constraints
    for lvl, cfg in DENSITY_CONFIG.items():
        if counts[lvl] < cfg["min_samples"]:
            logger.error(
                f"INSUFFICIENT_SAMPLES_PER_BIN: {lvl} has {counts[lvl]} (< {cfg['min_samples']})"
            )
            sys.exit(1)

    file_size_mb = output_path.stat().st_size / (1024 * 1024)
    logger.info(f"Generated {total_trajectories} trajectories.")
    logger.info(f"File size: {file_size_mb:.2f} MB")
    logger.info(f"Bin counts: {counts}")


if __name__ == "__main__":
    main()
