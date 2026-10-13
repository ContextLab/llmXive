"""
T014: Authoritative FR-001 oversampling verification.

Reads data/processed/trajectories.json and data/processed/generation_stats.json
produced by T001, independently recomputes the high-difficulty fraction
(high emotional reactivity OR diverse cultural identity), and writes
data/results/oversampling_report.json.

Fails loudly (non-zero exit) if:
  - either input file is missing or malformed,
  - the recomputed oversampling_ratio < 0.40 (FR-001 violation).

No fallback, no synthetic substitute.
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

FR001_MIN_RATIO = 0.40
HIGH_EMOTION_SCORE_THRESHOLD = 0.7
DIVERSE_TAG_MIN_COUNT = 2

HIGH_EMOTION_TOKENS = {"high", "highly_reactive", "highly-reactive", "high_reactivity"}
DIVERSE_CULTURAL_TOKENS = {"highly_diverse", "highly-diverse", "highly_diverse_cultural",
                           "diverse", "high_diversity", "highlydiverse"}


def load_json(path: Path) -> Any:
    """Load a JSON file, failing loudly if missing or malformed."""
    if not path.exists():
        raise FileNotFoundError(f"Required input file missing: {path}")
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Malformed JSON in {path}: {e}")


def _matches(value: str, tokens: set) -> bool:
    v = str(value).strip().lower()
    return v in tokens or any(t in v for t in tokens)


def is_high_emotion(traj: Dict[str, Any]) -> bool:
    """Independently determine whether a trajectory is high emotional reactivity."""
    # Form 1: top-level numeric score (dataset.schema.yaml style)
    score = traj.get("emotional_reactivity_score")
    if isinstance(score, (int, float)):
        return float(score) >= HIGH_EMOTION_SCORE_THRESHOLD
    # Form 2: metadata enum (generator.py style)
    meta = traj.get("metadata") or {}
    if isinstance(meta, dict):
        er = meta.get("emotional_reactivity")
        if er is not None:
            return _matches(er, HIGH_EMOTION_TOKENS)
    # Form 3: top-level string field
    er = traj.get("emotional_reactivity")
    if isinstance(er, str):
        return _matches(er, HIGH_EMOTION_TOKENS)
    raise ValueError(
        f"Trajectory {traj.get('trajectory_id', '<unknown>')} has no usable "
        "emotional reactivity field (expected emotional_reactivity_score, "
        "metadata.emotional_reactivity, or emotional_reactivity)"
    )


def is_diverse_cultural(traj: Dict[str, Any]) -> bool:
    """Independently determine whether a trajectory has diverse cultural identity."""
    # Form 1: top-level tag list (dataset.schema.yaml style)
    tags = traj.get("cultural_identity_tags")
    if isinstance(tags, list):
        return len(tags) >= DIVERSE_TAG_MIN_COUNT
    # Form 2: metadata enum (generator.py style)
    meta = traj.get("metadata") or {}
    if isinstance(meta, dict):
        ci = meta.get("cultural_identity")
        if ci is not None:
            return _matches(ci, DIVERSE_CULTURAL_TOKENS)
    # Form 3: top-level string field
    ci = traj.get("cultural_identity")
    if isinstance(ci, str):
        return _matches(ci, DIVERSE_CULTURAL_TOKENS)
    raise ValueError(
        f"Trajectory {traj.get('trajectory_id', '<unknown>')} has no usable "
        "cultural identity field (expected cultural_identity_tags, "
        "metadata.cultural_identity, or cultural_identity)"
    )


def recompute_high_difficulty(trajectories: List[Dict[str, Any]]) -> Tuple[int, int, int, int]:
    """Return (total, high_emotion_count, high_cultural_count, high_difficulty_count)."""
    if not isinstance(trajectories, list) or not trajectories:
        raise ValueError("trajectories.json must be a non-empty JSON list")
    total = 0
    high_emotion = 0
    high_cultural = 0
    high_difficulty = 0
    for i, traj in enumerate(trajectories):
        if not isinstance(traj, dict):
            raise ValueError(f"trajectories[{i}] is not a JSON object")
        if not traj.get("trajectory_id"):
            raise ValueError(f"trajectories[{i}] is missing trajectory_id")
        total += 1
        he = is_high_emotion(traj)
        hc = is_diverse_cultural(traj)
        high_emotion += int(he)
        high_cultural += int(hc)
        high_difficulty += int(he or hc)
    return total, high_emotion, high_cultural, high_difficulty


def verify(
    trajectories_path: Path = None,
    stats_path: Path = None,
    report_path: Path = None,
) -> Dict[str, Any]:
    """Run the full FR-001 verification and return the report dict."""
    if trajectories_path is None:
        trajectories_path = paths.data("processed", "trajectories.json")
    if stats_path is None:
        stats_path = paths.data("processed", "generation_stats.json")
    if report_path is None:
        report_path = paths.data("results", "oversampling_report.json")

    # --- Load and validate inputs (fail loudly) ---
    trajectories = load_json(trajectories_path)
    stats = load_json(stats_path)
    if not isinstance(stats, dict):
        raise ValueError(f"{stats_path} must contain a JSON object")
    for key in ("total_count", "high_emotion_count", "high_cultural_count", "oversampling_ratio"):
        if key not in stats:
            raise ValueError(f"{stats_path} is missing required key '{key}'")
        if not isinstance(stats[key], (int, float)) or isinstance(stats[key], bool):
            raise ValueError(f"{stats_path} key '{key}' is not numeric")

    # --- Independent recomputation ---
    total, he, hc, hd = recompute_high_difficulty(trajectories)
    ratio = hd / total if total > 0 else 0.0
    passes = ratio >= FR001_MIN_RATIO

    # Cross-check against the generator's own statistics (informational).
    stats_total = int(stats["total_count"])
    stats_ratio = float(stats["oversampling_ratio"])
    consistent_counts = stats_total == total
    consistent_ratio = abs(stats_ratio - ratio) <= 0.05

    report = {
        "total_count": total,
        "high_difficulty_count": hd,
        "high_emotion_count": he,
        "high_cultural_count": hc,
        "oversampling_ratio": round(ratio, 4),
        "passes_fr001": passes,
        "fr001_min_ratio": FR001_MIN_RATIO,
        "generation_stats_consistent": bool(consistent_counts and consistent_ratio),
        "generation_stats_total_count": stats_total,
        "generation_stats_oversampling_ratio": stats_ratio,
        "trajectories_path": str(trajectories_path),
        "stats_path": str(stats_path),
    }

    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    log.info("Oversampling report written to %s", report_path)
    return report


def main() -> int:
    try:
        report = verify()
    except (FileNotFoundError, ValueError) as e:
        log.error("FR-001 verification failed: %s", e)
        return 1

    log.info("total_count=%d high_difficulty_count=%d oversampling_ratio=%.4f passes_fr001=%s",
             report["total_count"], report["high_difficulty_count"],
             report["oversampling_ratio"], report["passes_fr001"])

    if not report["passes_fr001"]:
        log.error(
            "FR-001 VIOLATION: recomputed oversampling_ratio %.4f < %.2f "
            "(high-difficulty trajectories: %d / %d)",
            report["oversampling_ratio"], FR001_MIN_RATIO,
            report["high_difficulty_count"], report["total_count"],
        )
        return 1
    if not report["generation_stats_consistent"]:
        log.warning(
            "Note: generation_stats.json disagrees with independent recomputation "
            "(stats: total=%d ratio=%.4f; recomputed: total=%d ratio=%.4f)",
            report["generation_stats_total_count"],
            report["generation_stats_oversampling_ratio"],
            report["total_count"], report["oversampling_ratio"],
        )
    log.info("FR-001 check PASSED: oversampling_ratio %.4f >= %.2f",
             report["oversampling_ratio"], FR001_MIN_RATIO)
    return 0


if __name__ == "__main__":
    sys.exit(main())
