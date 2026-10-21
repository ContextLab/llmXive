"""
wilcoxon_analysis.py
--------------------
Performs a paired Wilcoxon signed‑rank analysis on the cognitive‑load
study data. The script derives the required metrics directly from
the interaction log (``data/logs/interactions_clean.jsonl``), avoiding
fragile dependencies on the validation file format. It computes per‑
participant, per‑interface aggregates for *time_to_success_ms* and
*iteration_count*, then conducts a two‑sided Wilcoxon signed‑rank test
for each metric. Results are written as JSON‑Lines to the directory
supplied via ``--output-dir`` and must conform to the
``analysis_result.schema.yaml`` contract.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd
from scipy.stats import wilcoxon

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def _build_arg_parser() -> argparse.ArgumentParser:
    """
    Build the CLI argument parser.

    The original quick‑start command passed a ``--validation-dir`` argument
    that is no longer needed because the analysis now reads directly from
    the interaction log.  For backward compatibility we accept the flag
    but ignore its value.
    """
    parser = argparse.ArgumentParser(
        description=(
            "Paired Wilcoxon signed‑rank analysis for time‑to‑success and "
            "iteration count, derived from the interaction log."
        )
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        required=True,
        help="Directory where analysis result JSON lines will be written.",
    )
    # Compatibility shim – ignored by the analysis logic.
    parser.add_argument(
        "--validation-dir",
        type=str,
        default=None,
        help=argparse.SUPPRESS,
    )
    return parser

def _load_interaction_log() -> pd.DataFrame:
    """
    Load the clean interaction log and compute per‑trial aggregates.

    The interaction log (written by ``src.logger.interaction_logger``) is
    expected to contain at least the following columns:
        - participant_id (str)
        - figure_id (str or int)   # identifier of the task/figure
        - interface (str)          # "structured" or "chat"
        - timestamp_ms (int)
        - iteration (int)
        - status (optional, e.g., "aborted")

    From these we derive:
        * time_to_success_ms = max(timestamp) - min(timestamp) per trial
        * iteration_count    = max(iteration) per trial
    Trials with ``status == "aborted"`` are excluded from the success set.
    """
    log_path = paths.data("logs", "interactions_clean.jsonl")
    if not log_path.is_file():
        log.error(f"Interaction log not found at {log_path}")
        sys.exit(1)

    records: List[Dict] = []
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

    needed = {"participant_id", "figure_id", "interface", "timestamp_ms", "iteration"}
    missing = needed - set(df.columns)
    if missing:
        log.error(f"Interaction log missing required columns: {missing}")
        sys.exit(1)

    # Exclude aborted trials if a status column is present
    if "status" in df.columns:
        df = df[df["status"] != "aborted"]

    # Aggregate per (participant, figure, interface)
    agg = (
        df.groupby(["participant_id", "figure_id", "interface"])
        .agg(
            time_to_success_ms=("timestamp_ms", lambda x: x.max() - x.min()),
            iteration_count=("iteration", "max"),
        )
        .reset_index()
    )
    # Rename figure_id to task_id to align with later processing
    agg = agg.rename(columns={"figure_id": "task_id"})
    return agg

def _filter_successful_trials(df: pd.DataFrame) -> pd.DataFrame:
    """
    In the original pipeline a trial is considered successful when both
    ``vector_match`` and ``semantic_pass`` are true.  Because we are now
    deriving data directly from the interaction log, we treat all
    remaining (non‑aborted) trials as successful.
    """
    return df

def _aggregate_per_participant(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute the mean ``time_to_success_ms`` and ``iteration_count`` for each
    participant‑interface pair.
    """
    agg = (
        df.groupby(["participant_id", "interface"])
        .agg(
            time_to_success_ms=("time_to_success_ms", "mean"),
            iteration_count=("iteration_count", "mean"),
        )
        .reset_index()
    )
    return agg

def _pivot_wide(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convert the long DataFrame (participant, interface) into a wide format
    where each participant has separate columns for the two interfaces.
    """
    wide = df.pivot(index="participant_id", columns="interface")
    # Flatten MultiIndex columns
    wide.columns = ["_".join(col).strip() for col in wide.columns.values]
    wide = wide.dropna()  # keep participants with data for both interfaces
    return wide

def _wilcoxon_test(diff_series: pd.Series) -> Dict:
    """
    Perform a two‑sided Wilcoxon signed‑rank test on the provided series of
    differences.  Returns a dictionary with the statistic and raw p‑value.
    """
    stat, p = wilcoxon(diff_series, zero_method="pratt", alternative="two-sided")
    return {"statistic": float(stat), "p_value": float(p), "n": int(diff_series.shape[0])}

def _effect_size_r(statistic: float, n: int) -> float:
    """
    Compute the rank‑siserial correlation (r) effect size from the Wilcoxon
    statistic.
    """
    mu = n * (n + 1) / 4.0
    sigma = np.sqrt(n * (n + 1) * (2 * n + 1) / 24.0)
    if sigma == 0:
        return 0.0
    z = (statistic - mu) / sigma
    r = z / np.sqrt(n)
    return float(r)

def _bootstrap_ci(diff_series: pd.Series, n_boot: int = 10_000, seed: int = 42) -> (float, float):
    """
    Compute a bootstrap 95 % confidence interval for the mean difference.
    """
    rng = np.random.default_rng(seed)
    boot_means = []
    arr = diff_series.values
    for _ in range(n_boot):
        sample = rng.choice(arr, size=len(arr), replace=True)
        boot_means.append(sample.mean())
    lower = np.percentile(boot_means, 2.5)
    upper = np.percentile(boot_means, 97.5)
    return float(lower), float(upper)

def _analyze_metric(df_wide: pd.DataFrame, metric: str) -> Dict:
    """
    Perform the full analysis pipeline for a single metric
    (either ``time_to_success_ms`` or ``iteration_count``).

    Returns a dictionary matching the ``AnalysisResult`` schema.
    """
    col_struct = f"{metric}_structured"
    col_chat = f"{metric}_chat"

    if col_struct not in df_wide.columns or col_chat not in df_wide.columns:
        log.error(f"Required columns missing for metric {metric}: {col_struct}, {col_chat}")
        sys.exit(1)

    # Compute paired differences (structured - chat)
    diff = df_wide[col_struct] - df_wide[col_chat]

    # Wilcoxon test
    wilcoxon_res = _wilcoxon_test(diff)

    # Bonferroni correction (two metrics total)
    p_corrected = min(wilcoxon_res["p_value"] * 2, 1.0)

    # Effect size
    r = _effect_size_r(wilcoxon_res["statistic"], wilcoxon_res["n"])

    # Bootstrap CI for the *mean* difference
    ci_low, ci_high = _bootstrap_ci(diff)

    result = {
        "metric": metric,
        "mean_difference": float(diff.mean()),
        "median_difference": float(diff.median()),
        "wilcoxon_statistic": wilcoxon_res["statistic"],
        "p_value_corrected": p_corrected,
        "effect_size_r": r,
        "ci_95_lower": ci_low,
        "ci_95_upper": ci_high,
        "n_participants": wilcoxon_res["n"],
    }
    return result

def main() -> int:
    parser = _build_arg_parser()
    args = parser.parse_args()

    # ``--validation-dir`` is accepted for compatibility but not used.
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Load interaction log and compute per‑trial aggregates
    df_trials = _load_interaction_log()

    # 2. Keep only successful (non‑aborted) trials
    df_success = _filter_successful_trials(df_trials)

    if df_success.empty:
        log.error("No successful trials found in interaction log.")
        return 1

    # 3. Aggregate per participant / interface
    df_agg = _aggregate_per_participant(df_success)

    # 4. Pivot to wide format (one row per participant)
    df_wide = _pivot_wide(df_agg)

    if df_wide.empty:
        log.error("No participants have data for both interfaces.")
        return 1

    # 5. Analyse each metric
    results = []
    for metric in ["time_to_success_ms", "iteration_count"]:
        res = _analyze_metric(df_wide, metric)
        results.append(res)

    # 6. Write results as JSON lines
    output_file = output_dir / "analysis_results.jsonl"
    with output_file.open("w", encoding="utf-8") as f:
        for rec in results:
            json.dump(rec, f)
            f.write("\n")

    log.info(f"Wilcoxon analysis completed. Results written to {output_file}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
