"""T002: Generate the Held-Out Test Set (5000 sessions, seed=43, perturbed distribution).

Structural Diversity Strategy (Plan Phase 0): the held-out set uses a distinct
random seed (43) and a perturbed distribution with ``variance_multiplier=1.5``
applied to sequence length and tool repetition, ensuring distributional shift
relative to the training set (seed=42) and variance in the outcome variable.

Outputs:
  - data/held_out/session_XXXXX.json  (5000 files)
  - data/raw/logs/trace_integrity.log (appended integrity records)
"""
import json
import math
from collections import Counter

import numpy as np

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# --- Configuration (mirrors code/config.py T006 constraints) ---
HOLDOUT_SEED = 43
HOLDOUT_COUNT = 5000
HOLDOUT_VARIANCE_MULTIPLIER = 1.5
MIN_LENGTH = 5
MAX_LENGTH = 20

TOOL_ARGUMENTS = {
    "insert_text": ["x", "y", "length"],
    "insert_image": ["x", "y", "width", "height"],
    "insert_chart": ["x", "y", "width", "height"],
    "format_text": ["font_size", "x", "y"],
    "resize_element": ["width", "height"],
    "delete_element": ["element_id"],
    "update_layout": ["margin", "padding"],
    "apply_theme": ["hue", "saturation"],
}
TOOL_TYPES = sorted(TOOL_ARGUMENTS.keys())

# Baseline repeat probability from the training distribution; scaled by the
# variance multiplier to perturb tool repetition in the held-out set.
BASELINE_REPEAT_PROB = 0.30
PERTURBED_REPEAT_PROB = min(0.9, BASELINE_REPEAT_PROB * HOLDOUT_VARIANCE_MULTIPLIER)


def perturbed_length(rng: np.random.Generator) -> int:
    """Sample a sequence length with 1.5x spread around the baseline midpoint.

    Baseline lengths are uniform on [5, 20] (midpoint 12.5). The perturbed
    distribution stretches deviations from the midpoint by the variance
    multiplier, pushing mass toward the extremes while staying in bounds.
    """
    base = rng.integers(MIN_LENGTH, MAX_LENGTH + 1)
    stretched = 12.5 + (base - 12.5) * HOLDOUT_VARIANCE_MULTIPLIER
    return int(min(MAX_LENGTH, max(MIN_LENGTH, round(stretched))))


def generate_tool_sequence(rng: np.random.Generator, length: int):
    """Generate a tool sequence with elevated repetition probability."""
    tools = []
    for i in range(length):
        if i > 0 and rng.random() < PERTURBED_REPEAT_PROB:
            tools.append(tools[-1])
        else:
            tools.append(TOOL_TYPES[int(rng.integers(0, len(TOOL_TYPES)))])
    return tools


def build_calls(rng: np.random.Generator, tools):
    calls = []
    for step, tool in enumerate(tools):
        args = {
            name: round(float(rng.uniform(0.0, 100.0)), 4)
            for name in TOOL_ARGUMENTS[tool]
        }
        calls.append({"step": step, "tool": tool, "arguments": args})
    return calls


def compute_metrics(tools, calls):
    """Compute structural metrics from the exact values stored in the trace.

    - sequence_entropy: Shannon entropy (natural log) of the tool distribution.
    - tool_repetition_freq: 1 - unique_tools / sequence_length.
    - arg_semantic_variance: population variance of all argument values.
    """
    n = len(tools)
    counts = Counter(tools)
    entropy = -sum((c / n) * math.log(c / n) for c in counts.values())
    repetition = 1.0 - (len(counts) / n)
    values = [v for call in calls for v in call["arguments"].values()]
    if not values:
        raise ValueError("trace has no argument values")
    variance = float(np.var(np.asarray(values, dtype=float)))
    return {
        "sequence_entropy": round(entropy, 6),
        "tool_repetition_freq": round(repetition, 6),
        "arg_semantic_variance": round(variance, 6),
    }


def main() -> int:
    rng = np.random.default_rng(HOLDOUT_SEED)
    held_out_dir = paths.data("held_out")
    log_path = paths.data("raw", "logs", "trace_integrity.log")

    written = 0
    with open(log_path, "a", encoding="utf-8") as log_file:
        for idx in range(HOLDOUT_COUNT):
            length = perturbed_length(rng)
            tools = generate_tool_sequence(rng, length)
            calls = build_calls(rng, tools)
            metrics = compute_metrics(tools, calls)

            dominant_tool = Counter(tools).most_common(1)[0][0]
            session = {
                "trace_id": f"held_out_{HOLDOUT_SEED}_{idx:05d}",
                "dataset_split": "held_out",
                "seed": HOLDOUT_SEED,
                "sequence_length": length,
                "tool_sequence": tools,
                "calls": calls,
                "structural_metrics": metrics,
                "final_state": {
                    "dominant_tool": dominant_tool,
                    "slide_element_count": int(rng.integers(2, 10)),
                    "layout_hash": f"{HOLDOUT_SEED}-{idx}-{dominant_tool}",
                },
                "variance_multiplier": HOLDOUT_VARIANCE_MULTIPLIER,
            }
            out_file = held_out_dir / f"session_{idx:05d}.json"
            with open(out_file, "w", encoding="utf-8") as f:
                json.dump(session, f, indent=2)
            written += 1

            # Trace integrity record (Constitution Principle VI)
            log_file.write(
                f"{session['trace_id']} | split=held_out | seed={HOLDOUT_SEED} | "
                f"len={length} | tools={','.join(tools)} | "
                f"arg_semantic_variance={metrics['arg_semantic_variance']} | "
                f"sequence_entropy={metrics['sequence_entropy']} | "
                f"tool_repetition_freq={metrics['tool_repetition_freq']}\n"
            )
            if written % 1000 == 0:
                log_file.flush()
                log.info("Generated %d / %d held-out sessions", written, HOLDOUT_COUNT)

    # Fail-loud verification: every declared output file must exist on disk.
    files = sorted(held_out_dir.glob("session_*.json"))
    if len(files) != HOLDOUT_COUNT:
        raise RuntimeError(
            f"Expected {HOLDOUT_COUNT} held-out session files, found {len(files)}"
    )
    for p in files:
        if p.stat().st_size == 0:
            raise RuntimeError(f"Held-out session file is empty: {p}")

    log.info(
        "T002 complete: %d held-out sessions written to %s (seed=%d, "
        "variance_multiplier=%.1f)",
        HOLDOUT_COUNT, held_out_dir, HOLDOUT_SEED, HOLDOUT_VARIANCE_MULTIPLIER,
    )
    print(f"Wrote {HOLDOUT_COUNT} held-out sessions to {held_out_dir}")
    print(f"Appended integrity records to {log_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())