"""
mean_wilcoxon_analysis.py
-------------------------

Computes a mean‑based paired Wilcoxon signed‑rank test for the
cognitive‑load study.  The script reads the clean interaction log
(``data/logs/interactions_clean.jsonl``), aggregates per‑participant
mean metrics for each interface, and then performs a Wilcoxon test on
the paired differences of those means.

The primary metric of interest is ``time_to_success_ms`` (latency),
but the script can be instructed to analyse ``iteration_count`` via
the ``--metric`` flag.

The result is written as a single JSON‑Lines record to the directory
supplied via ``--output-dir``.  The output file is named
``mean_wilcoxon_results.jsonl`` and contains the fields:

    - mean_structured
    - mean_chat
    - wilcoxon_stat
    - p_value
    - effect_size_r

All calculations are performed on real data; no synthetic or
fabricated values are introduced.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict

import numpy as np
import pandas as pd
from scipy.stats import wilcoxon

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Mean‑based paired Wilcoxon analysis. "
            "Aggregates per‑participant means for the chosen metric "
            "and tests the paired difference between the structured "
            "and chat interfaces."
        )
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        required=True,
        help="Directory where the JSON‑Lines result will be written.",
    )
    parser.add_argument(
        "--metric",
        type=str,
        choices=["time_to_success_ms", "iteration_count"],
        default="time_to_success_ms",
        help="Metric to analyse (default: time_to_success_ms).",
    )
    return parser

def _load_interaction_log() -> pd.DataFrame:
    """
    Load the clean interaction log and compute per‑trial aggregates.

    Returns a DataFrame with columns:
        participant_id, figure_id, interface, timestamp_ms, iteration
    """
    log_path = paths.data("logs", "interactions_clean.jsonl")
    if not log_path.is_file():
        log.error(f"Interaction log not found at {log_path}")
        sys.exit(1)

    records = []
    with log_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError as exc:
                log.warning(f"Skipping malformed JSON line: {exc}")
                continue
            records.append(rec)

    if not records:
        log.error("Interaction log is empty.")
        sys.exit(1)

    df = pd.DataFrame.from_records(records)

    required = {
        "participant_id",
        "figure_id",
        "interface",
        "timestamp_ms",
        "iteration",
    }
    missing = required - set(df.columns)
    if missing:
        log.error(f"Interaction log missing required columns: {missing}")
        sys.exit(1)

    # Drop aborted trials if present
    if "status" in df.columns:
        df = df[df["status"] != "aborted"]

    return df

def _aggregate_means(df: pd.DataFrame, metric: str) -> pd.DataFrame:
    """
    From per‑interaction records, compute per‑trial aggregates
    (time_to_success_ms and iteration_count) and then per‑participant
    means for the requested metric.
    """
    # Compute per‑trial aggregates
    trial_agg = (
        df.groupby(["participant_id", "figure_id", "interface"])
        .agg(
            time_to_success_ms=("timestamp_ms", lambda x: x.max() - x.min()),
            iteration_count=("iteration", "max"),
        )
        .reset_index()
    )

    # Select the metric column
    metric_col = metric

    # Compute per‑participant mean for each interface
    participant_means = (
        trial_agg.groupby(["participant_id", "interface"])
        .agg({metric_col: "mean"})
        .reset_index()
    )
    return participant_means

def _pivot_to_wide(df_means: pd.DataFrame, metric: str) -> pd.DataFrame:
    """
    Convert long format (participant_id, interface, metric) to wide
    format with one row per participant and separate columns for each
    interface.
    """
    wide = df_means.pivot(index="participant_id", columns="interface", values=metric)
    wide = wide.dropna()  # keep participants that have both interfaces
    # Rename columns for clarity
    wide = wide.rename(columns={"structured": "structured", "chat": "chat"})
    return wide

def _wilcoxon_test(diff: pd.Series) -> Dict[str, float]:
    """
    Perform a two‑sided Wilcoxon signed‑rank test on the series of
    differences (structured - chat). Returns statistic and p‑value.
    """
    stat, p = wilcoxon(diff, zero_method="pratt", alternative="two-sided")
    return {"statistic": float(stat), "p_value": float(p), "n": int(diff.shape[0])}

def _effect_size_r(statistic: float, n: int) -> float:
    """
    Compute the rank‑siserial correlation (r) effect size from the
    Wilcoxon statistic.
    """
    mu = n * (n + 1) / 4.0
    sigma = np.sqrt(n * (n + 1) * (2 * n + 1) / 24.0)
    if sigma == 0:
        return 0.0
    z = (statistic - mu) / sigma
    r = z / np.sqrt(n)
    return float(r)

def main() -> int:
    parser = _build_arg_parser()
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Load interaction log
    df = _load_interaction_log()

    # 2. Aggregate per‑participant means for the chosen metric
    df_means = _aggregate_means(df, args.metric)

    # 3. Pivot to wide format (one row per participant)
    df_wide = _pivot_to_wide(df_means, args.metric)

    if df_wide.empty:
        log.error("No participants have data for both interfaces.")
        return 1

    # 4. Compute paired differences (structured - chat)
    diff = df_wide["structured"] - df_wide["chat"]

    # 5. Perform Wilcoxon test
    wilcoxon_res = _wilcoxon_test(diff)

    # 6. Compute effect size r
    r = _effect_size_r(wilcoxon_res["statistic"], wilcoxon_res["n"])

    # 7. Compute overall means for each interface
    mean_structured = float(df_wide["structured"].mean())
    mean_chat = float(df_wide["chat"].mean())

    result = {
        "mean_structured": mean_structured,
        "mean_chat": mean_chat,
        "wilcoxon_stat": wilcoxon_res["statistic"],
        "p_value": wilcoxon_res["p_value"],
        "effect_size_r": r,
    }

    output_path = output_dir / "mean_wilcoxon_results.jsonl"
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(result, f)
        f.write("\n")

    log.info(f"Mean‑based Wilcoxon analysis completed. Results written to {output_path}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
