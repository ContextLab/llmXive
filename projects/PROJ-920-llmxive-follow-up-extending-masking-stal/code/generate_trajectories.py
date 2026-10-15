import json
import random
import string
import argparse
import logging
import sys
from pathlib import Path
from typing import List, Dict, Any

# Import from existing utils
from utils.entropy import entropy_per_token, clamp_entropy
from utils.heuristics import calculate_technical_token_ratio, calculate_composite_density

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# Constants & configuration
# ----------------------------------------------------------------------
DEFAULT_TRAJECTORY_COUNT = 500
MIN_SAMPLES_PER_BIN = 150               # per spec requirement
MAX_FILE_SIZE_BYTES = 100 * 1024 * 1024  # 100 MiB
DENSITY_LEVELS = ["low", "medium", "high"]
# Target **entropy per token** values (bits/token) for each density level
TARGET_ENTROPIES = {
    "low": 2.0,
    "medium": 3.5,
    "high": 4.5
}
# Number of turns per trajectory (synthetic, fixed)
TURNS_PER_TRAJECTORY = 10

# Paths
CONFIG_DIR = Path("code/config")
TERMS_FILE = CONFIG_DIR / "density_terms.json"
DEFAULT_OUTPUT_FILE = Path("data/raw/trajectories.json")

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def ensure_config_directory() -> None:
    """Make sure the config directory exists."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

def load_terms() -> List[str]:
    """Load technical terms from the JSON config."""
    if not TERMS_FILE.exists():
        logger.error(f"Technical terms file not found at {TERMS_FILE}")
        sys.exit(1)
    try:
        with open(TERMS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        terms = data.get("terms", [])
        if not isinstance(terms, list):
            logger.error("Terms file must contain a list under the key 'terms'.")
            sys.exit(1)
        return terms
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse terms file: {e}")
        sys.exit(1)

def generate_generic_text(length: int = 200) -> str:
    """Generate a non‑critical turn – simple low‑entropy filler."""
    return "generic turn text " * (length // 20)

def _alphabet_for_target(target_entropy: float) -> List[str]:
    """
    Choose an alphabet size that yields an entropy close to the target.
    Entropy per token ≈ log2(|alphabet|) when characters are chosen uniformly.
    """
    if target_entropy <= 2.5:
        # ~2 bits → alphabet size 4
        return list('abcd')
    elif target_entropy <= 4.0:
        # ~3.5 bits → alphabet size ~12
        return list('abcdefghijkl')
    else:
        # ~4.5 bits → alphabet size ~23–26 (use full lowercase alphabet)
        return list(string.ascii_lowercase)

def generate_text_for_target_entropy(target_entropy: float, terms: List[str]) -> str:
    """
    Produce a text block whose *entropy per token* is close to ``target_entropy``.
    The method selects an alphabet whose theoretical entropy approximates the
    target and samples uniformly until the measured entropy falls within tolerance.
    """
    tolerance = 0.01
    alphabet = _alphabet_for_target(target_entropy)
    length = 200  # fixed length used elsewhere

    for _ in range(20):
        txt = ''.join(random.choices(alphabet, k=length))
        ent = entropy_per_token(txt)
        if abs(ent - target_entropy) <= tolerance:
            return txt
    # Fallback: return the last generated string even if tolerance not met
    return txt

def build_turn(turn_index: int, is_critical: bool, target_entropy: float,
               terms: List[str]) -> Dict[str, Any]:
    """Create a single turn dictionary adhering to the schema."""
    if is_critical:
        text = generate_text_for_target_entropy(target_entropy, terms)
    else:
        text = generate_generic_text()
    # Compute metrics
    entropy = entropy_per_token(text)
    tech_ratio = calculate_technical_token_ratio(text, set(terms))
    # Clamp entropy just in case (entropy_per_token already handles empty strings)
    entropy = clamp_entropy(entropy)
    return {
        "turn_index": turn_index,
        "text": text,
        "is_critical": is_critical,
        "entropy_per_token": float(entropy),
        "technical_token_ratio": float(tech_ratio)
    }

def compute_final_density(entropy: float, tech_ratio: float) -> float:
    """Composite density as defined by FR‑008, clamped to [0, 1]."""
    raw = 0.6 * entropy + 0.4 * tech_ratio
    return max(0.0, min(1.0, raw))

# ----------------------------------------------------------------------
# Main generation routine
# ----------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate synthetic trajectories with controlled semantic density."
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility"
    )
    # Accept both the historic '--count' flag and the newer '--num-trajectories'
    parser.add_argument(
        "--count",
        type=int,
        default=None,
        help=argparse.SUPPRESS
    )
    parser.add_argument(
        "--num-trajectories",
        type=int,
        default=None,
        help="Number of trajectories to generate (overrides --count)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=str(DEFAULT_OUTPUT_FILE),
        help="Path to write the generated trajectories JSON"
    )
    args = parser.parse_args()

    # Resolve the trajectory count (prefer the explicit '--num-trajectories')
    traj_count = args.num_trajectories or args.count or DEFAULT_TRAJECTORY_COUNT
    if traj_count <= 0:
        logger.error("Trajectory count must be positive.")
        sys.exit(1)

    logger.info(f"Generating {traj_count} trajectories (seed={args.seed})")
    random.seed(args.seed)

    # Ensure config directory and load technical terms
    ensure_config_directory()
    terms = load_terms()
    if not terms:
        logger.error("Technical terms list is empty – cannot compute density.")
        sys.exit(1)

    # Distribute trajectories across density levels as evenly as possible
    count_per_level = traj_count // len(DENSITY_LEVELS)
    remainder = traj_count % len(DENSITY_LEVELS)
    level_counts = {lvl: count_per_level for lvl in DENSITY_LEVELS}
    for i in range(remainder):
        level_counts[DENSITY_LEVELS[i]] += 1

    # Container for all trajectories
    all_trajectories: List[Dict[str, Any]] = []

    # Generation loop
    traj_id = 0
    for level in DENSITY_LEVELS:
        target_entropy = TARGET_ENTROPIES[level]
        for _ in range(level_counts[level]):
            evidence_turn = random.randint(0, TURNS_PER_TRAJECTORY - 1)
            turns: List[Dict[str, Any]] = []
            # Build each turn
            for idx in range(TURNS_PER_TRAJECTORY):
                is_critical = (idx == evidence_turn)
                turn = build_turn(
                    turn_index=idx,
                    is_critical=is_critical,
                    target_entropy=target_entropy,
                    terms=terms
                )
                turns.append(turn)

            # Compute final density using the *critical* turn's metrics
            crit_turn = turns[evidence_turn]
            final_density = compute_final_density(
                crit_turn["entropy_per_token"],
                crit_turn["technical_token_ratio"]
            )

            trajectory = {
                "trajectory_id": f"traj_{traj_id}",
                "turns": turns,
                "critical_evidence_turn": evidence_turn,
                "density_level": level,
                "target_entropy": float(target_entropy),
                "actual_entropy": float(crit_turn["entropy_per_token"]),
                "technical_token_ratio": float(crit_turn["technical_token_ratio"]),
                "final_density": float(final_density)
            }
            all_trajectories.append(trajectory)
            traj_id += 1

    # ------------------------------------------------------------------
    # Validation of bin counts
    # ------------------------------------------------------------------
    bin_counts = {lvl: 0 for lvl in DENSITY_LEVELS}
    for traj in all_trajectories:
        bin_counts[traj["density_level"]] += 1

    logger.info("Density bin distribution:")
    for lvl in DENSITY_LEVELS:
        cnt = bin_counts[lvl]
        logger.info(f"  {lvl}: {cnt}")
        if cnt < MIN_SAMPLES_PER_BIN:
            logger.error(
                f"INSUFFICIENT_SAMPLES_PER_BIN: {lvl} has only {cnt} samples "
                f"(minimum required {MIN_SAMPLES_PER_BIN})"
            )
            sys.exit(1)

    # ------------------------------------------------------------------
    # Write output file
    # ------------------------------------------------------------------
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(all_trajectories, f, indent=2)
    except Exception as e:
        logger.error(f"Failed to write trajectories JSON: {e}")
        sys.exit(1)

    # Verify file size constraint
    file_size = output_path.stat().st_size
    logger.info(f"Wrote {len(all_trajectories)} trajectories to {output_path}")
    logger.info(f"File size: {file_size / (1024 * 1024):.2f} MiB")
    if file_size > MAX_FILE_SIZE_BYTES:
        logger.error(
            f"File size exceeds limit of 100 MiB (actual: {file_size} bytes)."
        )
        sys.exit(1)

    logger.info("Trajectory generation completed successfully.")

if __name__ == "__main__":
    main()