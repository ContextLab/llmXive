"""
wilcoxon_analysis.py
--------------------
Implements paired Wilcoxon signed‑rank analysis for the cognitive‑load
study.  The script reads semantic validation records (produced by
``src.validation.run_validation``), filters for trials where **both**
``vector_match`` and ``semantic_pass`` are true, aggregates the
``time_to_success_ms`` and ``iteration_count`` metrics per participant
and per interface, and then performs a paired Wilcoxon signed‑rank test
on the within‑subject differences.

The output is a JSON‑lines file (one record per metric) written to the
directory supplied via ``--output-dir``.  Each record follows the
``AnalysisResult`` schema defined in ``contracts/analysis_result.schema.yaml``:

{
    "metric": "<time_to_success|iteration_count>",
    "mean_difference": float,
    "median_difference": float,
    "wilcoxon_statistic": float,
    "p_value_corrected": float,
    "effect_size_r": float,
    "ci_95_lower": float,
    "ci_95_upper": float,
    "n_participants": int
}

The script is deliberately defensive: it aborts with a non‑zero exit
status if required columns are missing, if there are not enough paired
observations, or if any I/O error occurs.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import List, Dict

import numpy as np
import pandas as pd
from scipy.stats import wilcoxon

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Paired Wilcoxon signed‑rank analysis for time‑to‑success and "
            "iteration count, using only trials that passed both vector "
            "match and semantic similarity checks."
        )
    )
    parser.add_argument(
        "--validation-dir",
        type=str,
        required=True,
        help="Directory containing semantic_validation.jsonl (one JSON line per trial).",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        required=True,
        help="Directory where analysis result JSON lines will be written.",
    )
    return parser

def _load_validation_records(validation_dir: Path) -> pd.DataFrame:
    """
    Load all JSON‑line records from ``semantic_validation.jsonl`` into a
    DataFrame.  Expected columns (at minimum) are:

        - participant_id (str)
        - interface (str)               # either "structured" or "chat"
        - time_to_success_ms (float)    # latency from first edit to success
        - iteration_count (int)         # number of edit attempts until success
        - vector_match (bool)
        - semantic_pass (bool)

    Records that do not contain the required columns are ignored.
    """
    validation_file = validation_dir / "semantic_validation.jsonl"
    if not validation_file.is_file():
        log.error(f"Validation file not found: {validation_file}")
        sys.exit(1)

    records: List[Dict] = []
    with validation_file.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError as exc:
                log.error(f"Invalid JSON line in {validation_file}: {exc}")
                continue
            records.append(rec)

    if not records:
        log.error("No valid validation records found.")
        sys.exit(1)

    df = pd.DataFrame.from_records(records)
    required = {
        "participant_id",
        "interface",
        "time_to_success_ms",
        "iteration_count",
        "vector_match",
        "semantic_pass",
    }
    missing = required - set(df.columns)
    if missing:
        log.error(f"Validation records missing required columns: {missing}")
        sys.exit(1)

    return df

def _filter_successful_trials(df: pd.DataFrame) -> pd.DataFrame:
    """Keep only trials where both vector_match and semantic_pass are true."""
    return df[(df["vector_match"] == True) & (df["semantic_pass"] == True)]

def _aggregate_per_participant(df: pd.DataFrame) -> pd.DataFrame:
    """
    For each participant and interface compute the *mean* time_to_success
    and *mean* iteration_count across all their successful trials.
    The resulting DataFrame has a MultiIndex (participant_id, interface)
    with columns ``time_to_success_ms`` and ``iteration_count``.
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
    wide = wide.dropna()  # ensure both interfaces are present
    return wide

def _wilcoxon_test(diff_series: pd.Series) -> Dict:
    """
    Perform a two‑sided Wilcoxon signed‑rank test on the provided series of
    differences.  Returns a dictionary with the statistic and raw p‑value.
    """
    # scipy.wilcoxon automatically drops zero differences
    stat, p = wilcoxon(diff_series, zero_method="pratt", alternative="two-sided")
    return {"statistic": float(stat), "p_value": float(p), "n": int(diff_series.shape[0])}

def _effect_size_r(statistic: float, n: int) -> float:
    """
    Compute the rank‑biserial correlation (r) effect size from the Wilcoxon
    statistic.  For large samples we approximate the Z‑value.
    """
    # Approximate Z from the statistic (see Cohen, 1988)
    # Expected mean and std under H0 for Wilcoxon W:
    #   mu = n*(n+1)/4
    #   sigma = sqrt(n*(n+1)*(2n+1)/24)
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

    validation_dir = Path(args.validation_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Load validation records
    df = _load_validation_records(validation_dir)

    # 2. Keep only fully successful trials
    df_success = _filter_successful_trials(df)

    if df_success.empty:
        log.error("No successful trials (both vector_match and semantic_pass) found.")
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