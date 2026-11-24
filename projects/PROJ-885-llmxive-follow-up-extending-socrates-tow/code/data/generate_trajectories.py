"""T001: Generate conflict trajectories with targeted oversampling (FR-001 / US-1).

Implements the synthetic conflict-trajectory generation layer mandated by the
feature specification (US-1: "The system MUST generate synthetic conflict
dialogue trajectories ... oversampling scenarios with 'high emotional
reactivity' and 'diverse cultural identity' attributes"). All randomness is
seeded for reproducibility (Constitution I). The reported statistics in
generation_stats.json are real measurements computed from the generated
dataset on disk, not invented values.

Outputs:
  data/processed/trajectories.json       - list of schema-compliant trajectories
  data/processed/generation_stats.json   - measured generation statistics
"""

import argparse
import json
import random
import sys
import uuid
from pathlib import Path
from typing import Dict, List, Optional

import jsonschema
import yaml

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# --- Configuration constants ---
TARGET_COUNT = 500
HIGH_EMOTION_THRESHOLD = 0.7
MIN_DIVERSE_TAG_COUNT = 3  # >=3 distinct cultural tags counts as "diverse cultural identity"
RANDOM_SEED = 42

# Axis allocation for targeted oversampling (fractions sum to 1.0).
# Guarantees the high-difficulty union (high emotion OR diverse cultural)
# is ~60% of the dataset, comfortably above the FR-001 requirement of >=40%.
AXIS_ALLOCATION = {
    "high_emotion_only": 0.25,
    "high_cultural_only": 0.25,
    "both_high": 0.10,
    "neutral": 0.40,
}

CULTURAL_TAG_POOL = [
    "collectivist", "individualist", "high-context-communication",
    "low-context-communication", "monochronic", "polychronic",
    "hierarchical-authority", "egalitarian", "face-saving",
    "direct-feedback", "religious-traditional", "secular",
]

HIGH_EMOTION_TEMPLATES = [
    "I can't believe you said that in front of everyone — it was completely unacceptable.",
    "You never listen to what matters to me, and I am tired of being dismissed.",
    "Every time we try to settle this, you change the rules. I am furious.",
    "This is the last straw; I have been patient for months and nothing has changed.",
    "How dare you question my commitment to this team after everything I sacrificed.",
    "I am so angry right now I can barely think straight about this proposal.",
]

CULTURAL_FRICTION_TEMPLATES = [
    "In my community, addressing an elder that way is deeply disrespectful.",
    "Our traditions require consensus before such a decision — you are skipping that entirely.",
    "You keep dismissing practices that are central to how my family has always done things.",
    "That phrasing carries a very different weight in my culture than you seem to realize.",
    "My background values indirect disagreement; your bluntness feels like an insult.",
    "This schedule ignores obligations that my culture treats as non-negotiable.",
]

NEUTRAL_TEMPLATES = [
    "I see your point; can we go through the budget line by line together?",
    "Let me make sure I understand your concern before we decide anything.",
    "What would a workable compromise look like from your side?",
    "I think we agree on the goal even if we differ on the method.",
    "Could we table this item and revisit it once we have the full report?",
    "That is a fair concern — here is the data I was basing my suggestion on.",
]

RESOLUTION_TEMPLATES = {
    "high_emotion_only": (
        "Both parties acknowledge the emotional impact of the conflict, agree to a "
        "cooling-off protocol before substantive discussion, and commit to a structured "
        "agenda that addresses each stated grievance with concrete corrective actions."
    ),
    "high_cultural_only": (
        "Both parties agree to engage a culturally informed mediation process, adopt "
        "communication norms that respect both cultural frameworks, and document shared "
        "terms of reference that honor each side's traditions while advancing the joint goal."
    ),
    "both_high": (
        "Both parties de-escalate the emotional intensity through validated acknowledgment, "
        "then adopt a culturally inclusive mediation framework with explicit norms from both "
        "traditions and a jointly owned, time-bound action plan."
    ),
    "neutral": (
        "Both parties agree on a factual summary of the disagreement, split the outstanding "
        "issues into resolvable sub-items, and adopt a written action plan with shared "
        "responsibilities and follow-up checkpoints."
    ),
}


def find_dataset_schema() -> Path:
    """Locate contracts/dataset.schema.yaml inside the project tree."""
    candidates = [
        paths.root / "contracts" / "dataset.schema.yaml",
        *sorted((paths.root / "specs").glob("*/contracts/dataset.schema.yaml")),
    ]
    for c in candidates:
        if c.is_file():
            return c
    raise FileNotFoundError(
        "contracts/dataset.schema.yaml not found under the project root; "
        "cannot validate generated trajectories."
    )


def sample_axis(rng: random.Random) -> str:
    r = rng.random()
    cumulative = 0.0
    for axis, frac in AXIS_ALLOCATION.items():
        cumulative += frac
        if r < cumulative:
            return axis
    return "neutral"


def build_dialogue(axis: str, rng: random.Random) -> List[str]:
    """Build a dialogue history whose turn mix reflects the target axis."""
    n_turns = rng.randint(6, 12)
    if axis == "high_emotion_only":
        pool_weights = [(HIGH_EMOTION_TEMPLATES, 0.7), (NEUTRAL_TEMPLATES, 0.3)]
    elif axis == "high_cultural_only":
        pool_weights = [(CULTURAL_FRICTION_TEMPLATES, 0.7), (NEUTRAL_TEMPLATES, 0.3)]
    elif axis == "both_high":
        pool_weights = [
            (HIGH_EMOTION_TEMPLATES, 0.4),
            (CULTURAL_FRICTION_TEMPLATES, 0.4),
            (NEUTRAL_TEMPLATES, 0.2),
        ]
    else:
        pool_weights = [(NEUTRAL_TEMPLATES, 1.0)]

    turns = []
    for i in range(n_turns):
        r = rng.random()
        cumulative = 0.0
        chosen_pool = NEUTRAL_TEMPLATES
        for pool, weight in pool_weights:
            cumulative += weight
            if r < cumulative:
                chosen_pool = pool
                break
        speaker = "Party A" if i % 2 == 0 else "Party B"
        turns.append(f"{speaker}: {rng.choice(chosen_pool)}")
    return turns


def build_trajectory(axis: str, rng: random.Random) -> Dict:
    """Generate one schema-compliant trajectory for the given axis."""
    if axis in ("high_emotion_only", "both_high"):
        emotional_score = round(rng.uniform(0.75, 0.95), 3)
    else:
        emotional_score = round(rng.uniform(0.10, 0.55), 3)

    if axis in ("high_cultural_only", "both_high"):
        n_tags = rng.randint(MIN_DIVERSE_TAG_COUNT, 5)
    else:
        n_tags = rng.randint(1, 2)
    cultural_tags = rng.sample(CULTURAL_TAG_POOL, n_tags)

    return {
        "trajectory_id": str(uuid.uuid4()),
        "dialogue_history": build_dialogue(axis, rng),
        "emotional_reactivity_score": emotional_score,
        "cultural_identity_tags": cultural_tags,
        "ideal_resolution": RESOLUTION_TEMPLATES[axis],
    }


def is_high_emotion(traj: Dict) -> bool:
    return traj["emotional_reactivity_score"] >= HIGH_EMOTION_THRESHOLD


def is_diverse_cultural(traj: Dict) -> bool:
    return len(set(traj["cultural_identity_tags"])) >= MIN_DIVERSE_TAG_COUNT


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Generate conflict trajectories with targeted oversampling (T001)."
    )
    parser.add_argument("--oversample-high-emotion", action="store_true",
                        help="Oversample the high-emotional-reactivity axis (FR-001).")
    parser.add_argument("--oversample-diverse-cultural", action="store_true",
                        help="Oversample the diverse-cultural-identity axis (FR-001).")
    parser.add_argument("--num-trajectories", type=int, default=TARGET_COUNT,
                        help="Total number of trajectories to generate.")
    parser.add_argument("--seed", type=int, default=RANDOM_SEED,
                        help="Random seed for reproducibility.")
    args = parser.parse_args(argv)

    rng = random.Random(args.seed)

    # Fail loudly if oversampling was not requested — the FR-001 check
    # downstream depends on the targeted allocation.
    if not (args.oversample_high_emotion or args.oversample_diverse_cultural):
        log.error(
            "No oversampling flag provided. Run with --oversample-high-emotion "
            "--oversample-diverse-cultural to satisfy FR-001."
        )
        return 2

    log.info(
        "Generating %d trajectories (seed=%d, high-emotion=%s, diverse-cultural=%s)",
        args.num_trajectories, args.seed,
        args.oversample_high_emotion, args.oversample_diverse_cultural,
    )

    trajectories = [build_trajectory(sample_axis(rng), rng)
                    for _ in range(args.num_trajectories)]

    # --- Measure real statistics from the generated data on disk ---
    high_emotion_count = sum(1 for t in trajectories if is_high_emotion(t))
    high_cultural_count = sum(1 for t in trajectories if is_diverse_cultural(t))
    high_difficulty_count = sum(
        1 for t in trajectories if is_high_emotion(t) or is_diverse_cultural(t)
    )
    total_count = len(trajectories)
    oversampling_ratio = high_difficulty_count / total_count if total_count else 0.0

    if oversampling_ratio < 0.40:
        log.error(
            "FR-001 violation: oversampling_ratio=%.3f < 0.40. Refusing to write "
            "outputs; regenerate with a different seed.", oversampling_ratio
        )
        return 3

    # --- Validate every trajectory against the dataset contract ---
    schema_path = find_dataset_schema()
    with open(schema_path, "r", encoding="utf-8") as f:
        schema = yaml.safe_load(f)
    for i, traj in enumerate(trajectories):
        try:
            jsonschema.validate(traj, schema)
        except jsonschema.ValidationError as e:
            log.error("Trajectory %d failed schema validation: %s", i, e.message)
            return 4
    log.info("All %d trajectories validate against %s", total_count, schema_path)

    # --- Write outputs ---
    traj_path = paths.data("processed", "trajectories.json")
    with open(traj_path, "w", encoding="utf-8") as f:
        json.dump(trajectories, f, indent=2)

    stats = {
        "total_count": total_count,
        "high_emotion_count": high_emotion_count,
        "high_cultural_count": high_cultural_count,
        "oversampling_ratio": round(oversampling_ratio, 4),
        "underpowered_flag": total_count < 500,
    }
    stats_path = paths.data("processed", "generation_stats.json")
    with open(stats_path, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2)

    log.info("Wrote %s (%d trajectories)", traj_path, total_count)
    log.info("Wrote %s: %s", stats_path, stats)
    return 0


if __name__ == "__main__":
    sys.exit(main())