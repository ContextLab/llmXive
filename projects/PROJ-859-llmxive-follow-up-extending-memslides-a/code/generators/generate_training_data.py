"""T001: Generate Synthetic Training Data.

Generates 5000 multi-turn revision sessions for the Training Set using
seed=42 and standard parameters (tool_types, min_length=5, max_length=20).
Output: data/training/*.json
Constraint: logs exact tool sequences and argument variances to
data/raw/logs/trace_integrity.log.
"""
import argparse
import json
import math
import sys
from collections import Counter
from pathlib import Path

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# Standard parameters per T006 / tasks.md T001
TRAINING_SEED = 42
SESSION_COUNT = 5000
MIN_LENGTH = 5
MAX_LENGTH = 20
TOOL_TYPES = [
    "insert_chart",
    "format_text",
    "insert_text",
    "delete_element",
    "update_layout",
    "apply_theme",
    "insert_image",
    "resize_element",
]
# Numeric argument fields per tool type (MemSlides-style slide editing args)
ARG_FIELDS = {
    "insert_chart": ["x", "y", "width", "height", "data_points"],
    "format_text": ["font_size", "x", "y"],
    "insert_text": ["x", "y", "length"],
    "delete_element": ["element_id"],
    "update_layout": ["margin", "padding"],
    "apply_theme": ["hue", "saturation"],
    "insert_image": ["x", "y", "width", "height"],
    "resize_element": ["width", "height"],
}

import random


def _shannon_entropy(tool_sequence):
    counts = Counter(tool_sequence)
    n = len(tool_sequence)
    return -sum((c / n) * math.log(c / n) for c in counts.values())


def _repetition_freq(tool_sequence):
    n = len(tool_sequence)
    return 1.0 - (len(set(tool_sequence)) / n)


def _arg_variance(calls):
    values = []
    for call in calls:
        values.extend(float(v) for v in call["arguments"].values())
    if not values:
        raise ValueError("no numeric arguments in trace")
    mean = sum(values) / len(values)
    return sum((v - mean) ** 2 for v in values) / len(values)


def generate_session(rng, index, seed):
    length = rng.randint(MIN_LENGTH, MAX_LENGTH)
    # Mix of uniform tool choice and repeated "habit" runs to create
    # diversity in entropy and repetition across sessions.
    tool_sequence = []
    while len(tool_sequence) < length:
        if rng.random() < 0.35:
            tool = rng.choice(TOOL_TYPES)
            run_len = rng.randint(2, 4)
            tool_sequence.extend([tool] * min(run_len, length - len(tool_sequence)))
        else:
            tool_sequence.append(rng.choice(TOOL_TYPES))
    calls = []
    for step, tool in enumerate(tool_sequence):
        args = {f: round(rng.uniform(0.0, 100.0), 4) for f in ARG_FIELDS[tool]}
        calls.append({"step": step, "tool": tool, "arguments": args})
    entropy = _shannon_entropy(tool_sequence)
    repetition = _repetition_freq(tool_sequence)
    variance = _arg_variance(calls)
    dominant = Counter(tool_sequence).most_common(1)[0][0]
    final_state = {
        "dominant_tool": dominant,
        "slide_element_count": len(set(tool_sequence)) * rng.randint(1, 3),
        "layout_hash": f"{seed}-{index}-{dominant}",
    }
    trace = {
        "trace_id": f"training_{seed}_{index:05d}",
        "dataset_split": "training",
        "seed": seed,
        "sequence_length": length,
        "tool_sequence": tool_sequence,
        "calls": calls,
        "structural_metrics": {
            "sequence_entropy": round(entropy, 6),
            "tool_repetition_freq": round(repetition, 6),
            "arg_semantic_variance": round(variance, 6),
        },
        "final_state": final_state,
    }
    return trace


def main():
    parser = argparse.ArgumentParser(description="Generate synthetic training data (T001)")
    parser.add_argument("--count", type=int, default=SESSION_COUNT)
    parser.add_argument("--seed", type=int, default=TRAINING_SEED)
    parser.add_argument("--output-dir", type=str, default=None)
    parser.add_argument("--log-path", type=str, default=None)
    args = parser.parse_args()

    output_dir = Path(args.output_dir) if args.output_dir else paths.data("training")
    log_path = Path(args.log_path) if args.log_path else paths.data("raw", "logs", "trace_integrity.log")
    output_dir.mkdir(parents=True, exist_ok=True)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    rng = random.Random(args.seed)
    written = 0
    with open(log_path, "a", encoding="utf-8") as integrity_log:
        integrity_log.write(
            f"# T001 training generation: seed={args.seed} count={args.count} "
            f"min_length={MIN_LENGTH} max_length={MAX_LENGTH}\n"
        )
        for i in range(1, args.count + 1):
            trace = generate_session(rng, i, args.seed)
            out_file = output_dir / f"session_{i:05d}.json"
            with open(out_file, "w", encoding="utf-8") as fh:
                json.dump(trace, fh, indent=2)
            written += 1
            m = trace["structural_metrics"]
            integrity_log.write(
                "trace_id={} seed={} split={} sequence=[{}] arg_variance={:.6f} "
                "entropy={:.6f} repetition={:.6f} length={}\n".format(
                    trace["trace_id"],
                    args.seed,
                    trace["dataset_split"],
                    ",".join(trace["tool_sequence"]),
                    m["arg_semantic_variance"],
                    m["sequence_entropy"],
                    m["tool_repetition_freq"],
                    trace["sequence_length"],
                )
            )
    if written != args.count:
        log.error("expected %d sessions, wrote %d", args.count, written)
        sys.exit(1)
    # Fail-loud verification: every file exists and parses.
    for i in range(1, args.count + 1):
        f = output_dir / f"session_{i:05d}.json"
        if not f.exists() or f.stat().st_size == 0:
            log.error("missing or empty session file: %s", f)
            sys.exit(1)
        with open(f, "r", encoding="utf-8") as fh:
            json.load(fh)
    if not log_path.exists() or log_path.stat().st_size == 0:
        log.error("trace integrity log missing or empty: %s", log_path)
        sys.exit(1)
    print(
        f"T001 complete: wrote {written} training sessions to {output_dir}; "
        f"integrity log at {log_path}"
    )


if __name__ == "__main__":
    main()