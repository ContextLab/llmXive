"""
wilcoxon_analysis.py
--------------------
Performs the main statistical analysis for the cognitive‑load study.
It reads the interaction log (``data/logs/interactions_clean.jsonl`` or
``data/logs/interactions.jsonl``), aggregates per‑participant metrics,
runs appropriate paired tests (Wilcoxon signed‑rank or paired t‑test
depending on normality), applies Bonferroni correction, computes effect
sizes, bootstraps a 95 % confidence interval for the *median* difference,
and fits an exploratory linear mixed‑effects model with ``expertise_level``
as a fixed covariate.

The results are written as JSON‑Lines to ``outputs/analysis_results.jsonl``
and must conform to ``specs/001-llmxive-follow-up-extending-crafter-a-mu/contracts/analysis_result.schema.yaml``.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import pandas as pd
from scipy.stats import shapiro, ttest_rel, wilcoxon
import statsmodels.formula.api as smf

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def _build_arg_parser() -> argparse.ArgumentParser:
    """
    Build the CLI argument parser.

    ``--validation-dir`` and ``--log-dir`` are accepted for backward
    compatibility but are ignored – the analysis now derives everything
    directly from the interaction log.
    """
    parser = argparse.ArgumentParser(
        description=(
            "Statistical analysis for the structured‑vs‑chat cognitive‑load study."
        )
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        required=True,
        help="Directory where analysis result JSON‑lines will be written.",
    )
    parser.add_argument(
        "--validation-dir",
        type=str,
        default=None,
        help=argparse.SUPPRESS,
    )
    # Compatibility arguments – they are parsed but not used.
    parser.add_argument(
        "--log-dir",
        type=str,
        default=None,
        help=argparse.SUPPRESS,
    )
    return parser

def _determine_log_path(log_dir_arg: Optional[str]) -> Path:
    """
    Determine which interaction‑log file to read.

    The pipeline historically wrote ``interactions_clean.jsonl``.
    Some earlier runs produced ``interactions.jsonl``.  This helper
    prefers the cleaned file but falls back gracefully.
    """
    default_dir = paths.data("logs")
    log_dir = Path(log_dir_arg) if log_dir_arg else default_dir

    candidates = [
        log_dir / "interactions_clean.jsonl",
        log_dir / "interactions.jsonl",
    ]
    for candidate in candidates:
        if candidate.is_file():
            return candidate

    # If none exist, raise a clear error – the caller can decide.
    log.error(f"No interaction log found in {log_dir}. Tried: {candidates}")
    sys.exit(1)

def _load_interaction_log(log_dir_arg: Optional[str] = None) -> pd.DataFrame:
    """
    Load the interaction log written by ``src.logger.interaction_logger``.
    Expected columns (at minimum):
        participant_id  (str)
        figure_id       (str or int)
        interface       (str) – ``structured`` or ``chat``
        timestamp_ms    (int)
        iteration       (int)
        status          (optional, e.g. ``aborted``)
        subjective_load (optional, float 0‑100)
        expertise_level (optional, str/int)

    The function aggregates raw edit records into per‑trial
    ``time_to_success_ms`` and ``iteration_count`` values.
    """
    log_path = _determine_log_path(log_dir_arg)

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

    # ------------------------------------------------------------------
    # Normalise column names – older logs may use slightly different names.
    # ------------------------------------------------------------------
    column_map = {}
    if "task_id" in df.columns and "figure_id" not in df.columns:
        column_map["task_id"] = "figure_id"
    if "mode" in df.columns and "interface" not in df.columns:
        column_map["mode"] = "interface"
    if "participant" in df.columns and "participant_id" not in df.columns:
        column_map["participant"] = "participant_id"
    if column_map:
        df = df.rename(columns=column_map)

    # Verify required columns
    required = {"participant_id", "figure_id", "interface", "timestamp_ms", "iteration"}
    missing = required - set(df.columns)
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
            subjective_load=("subjective_load", "first"),
            expertise_level=("expertise_level", "first"),
        )
        .reset_index()
    )
    # Rename figure_id to task_id for downstream consistency
    agg = agg.rename(columns={"figure_id": "task_id"})
    return agg

def _aggregate_per_participant(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute the *mean* metric per participant‑interface pair.
    """
    agg = (
        df.groupby(["participant_id", "interface"])
        .agg(
            time_to_success_ms=("time_to_success_ms", "mean"),
            iteration_count=("iteration_count", "mean"),
            subjective_load=("subjective_load", "mean"),
            expertise_level=("expertise_level", "first"),
        )
        .reset_index()
    )
    return agg

def _pivot_wide(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convert long format (participant, interface) to wide format with
    separate columns for each interface.
    """
    wide = df.pivot(index="participant_id", columns="interface")
    # Flatten MultiIndex columns
    wide.columns = ["_".join(col).strip() for col in wide.columns.values]
    wide = wide.dropna()  # keep participants with data for both interfaces
    return wide

def _normality_test(series: pd.Series) -> bool:
    """
    Return ``True`` if the series passes the Shapiro‑Wilk normality test
    (p > 0.05).
    """
    if len(series) < 3:
        # Not enough data to assess normality – fall back to non‑parametric.
        return False
    stat, p = shapiro(series)
    return p > 0.05

def _paired_t_test(diff: pd.Series) -> Dict:
    """
    Perform a paired t‑test on the difference series.
    Returns statistic, p‑value and Cohen's d.
    """
    t_stat, p_val = ttest_rel(diff + 0, np.zeros_like(diff))
    # Cohen's d for paired samples: mean(diff) / std(diff)
    d = diff.mean() / diff.std(ddof=1) if diff.std(ddof=1) != 0 else 0.0
    return {"statistic": float(t_stat), "p_value": float(p_val), "cohen_d": float(d), "test": "paired_t"}

def _wilcoxon_test(diff: pd.Series) -> Dict:
    """
    Perform a two‑sided Wilcoxon signed‑rank test.
    Returns statistic, p‑value and rank‑siserial r.
    """
    stat, p = wilcoxon(diff, zero_method="pratt", alternative="two-sided")
    n = diff.shape[0]
    # Rank‑siserial correlation
    mu = n * (n + 1) / 4.0
    sigma = np.sqrt(n * (n + 1) * (2 * n + 1) / 24.0)
    if sigma == 0:
        r = 0.0
    else:
        z = (stat - mu) / sigma
        r = z / np.sqrt(n)
    return {
        "statistic": float(stat),
        "p_value": float(p),
        "effect_size_r": float(r),
        "test": "wilcoxon",
    }

def _bootstrap_median_ci(diff: pd.Series, n_boot: int = 1000, seed: int = 42) -> (float, float):
    """
    Bootstrap a 95 % confidence interval for the *median* difference.
    """
    rng = np.random.default_rng(seed)
    medians = []
    arr = diff.values
    for _ in range(n_boot):
        sample = rng.choice(arr, size=len(arr), replace=True)
        medians.append(np.median(sample))
    lower = np.percentile(medians, 2.5)
    upper = np.percentile(medians, 97.5)
    return float(lower), float(upper)

def _fit_mixed_effects(df_wide: pd.DataFrame, metric: str) -> Optional[Dict]:
    """
    Fit an exploratory linear mixed‑effects model:

        metric ~ interface + expertise_level + (1 | participant_id)

    Returns a dictionary with the fixed‑effect coefficient for ``interface``
    and its p‑value, or ``None`` if the required columns are missing.
    """
    # Ensure the necessary columns exist
    required_cols = {
        f"{metric}_structured",
        f"{metric}_chat",
        "expertise_level_structured",
        "expertise_level_chat",
    }
    if not required_cols.issubset(set(df_wide.columns)):
        log.warning(f"Mixed‑effects model skipped for {metric}: missing columns.")
        return None

    # Reshape to long format for statsmodels
    long_df = pd.DataFrame({
        "participant_id": np.repeat(df_wide.index.values, 2),
        "interface": np.tile([0, 1], len(df_wide)),  # 0 = chat, 1 = structured
        metric: np.concatenate([df_wide[f"{metric}_chat"].values,
                                df_wide[f"{metric}_structured"].values]),
        "expertise_level": np.concatenate([df_wide["expertise_level_chat"].values,
                                          df_wide["expertise_level_structured"].values]),
    })

    # Drop rows with missing data
    long_df = long_df.dropna(subset=[metric, "expertise_level"])

    # Encode interface as categorical (statsmodels handles automatically)
    try:
        model = smf.mixedlm(
            f"{metric} ~ interface + expertise_level",
            long_df,
            groups=long_df["participant_id"]
        )
        result = model.fit()
    except Exception as exc:
        log.warning(f"Mixed‑effects model failed for {metric}: {exc}")
        return None

    coef = result.params.get("interface")
    pval = result.pvalues.get("interface")
    return {"interface_coef": float(coef) if coef is not None else None,
            "interface_p": float(pval) if pval is not None else None,
            "model_summary": result.summary().as_text()}

def _analyze_metric(df_wide: pd.DataFrame, metric: str) -> Dict:
    """
    Perform the full analysis pipeline for a single metric.
    Returns a dictionary that conforms to the ``AnalysisResult`` schema.
    """
    col_struct = f"{metric}_structured"
    col_chat = f"{metric}_chat"

    if col_struct not in df_wide.columns or col_chat not in df_wide.columns:
        log.error(f"Required columns missing for metric {metric}: {col_struct}, {col_chat}")
        sys.exit(1)

    # Paired differences (structured - chat)
    diff = df_wide[col_struct] - df_wide[col_chat]

    # Normality check
    use_ttest = _normality_test(diff)

    if use_ttest:
        test_res = _paired_t_test(diff)
    else:
        test_res = _wilcoxon_test(diff)

    # Bonferroni correction (three metrics total → α = 0.025 per metric)
    p_corrected = min(test_res["p_value"] * 3, 1.0)

    # Effect size handling
    if test_res["test"] == "wilcoxon":
        effect_size = test_res.get("effect_size_r")
    else:
        effect_size = test_res.get("cohen_d")

    # Bootstrap CI for median difference
    ci_low, ci_high = _bootstrap_median_ci(diff)

    # Mixed‑effects model (optional)
    mixed = _fit_mixed_effects(df_wide, metric)

    result = {
        "metric": metric,
        "test_used": test_res["test"],
        "statistic": test_res["statistic"],
        "p_value_raw": test_res["p_value"],
        "p_value_corrected": p_corrected,
        "effect_size": effect_size,
        "ci_95_lower": ci_low,
        "ci_95_upper": ci_high,
        "n_participants": int(diff.shape[0]),
    }

    if mixed is not None:
        result["mixed_effects"] = mixed

    return result

def main() -> int:
    parser = _build_arg_parser()
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Load interaction log and compute per‑trial aggregates
    df_trials = _load_interaction_log(args.log_dir)

    if df_trials.empty:
        log.error("No trial data available after loading interaction log.")
        return 1

    # 2. Aggregate per participant / interface
    df_agg = _aggregate_per_participant(df_trials)

    # 3. Pivot to wide format (one row per participant)
    df_wide = _pivot_wide(df_agg)

    if df_wide.empty:
        log.error("No participants have data for both interfaces.")
        return 1

    # 4. Analyse each metric
    results: List[Dict] = []
    for metric in ["time_to_success_ms", "iteration_count", "subjective_load"]:
        res = _analyze_metric(df_wide, metric)
        results.append(res)

    # 5. Write results as JSON‑Lines
    out_path = output_dir / "analysis_results.jsonl"
    with out_path.open("w", encoding="utf-8") as f:
        for rec in results:
            json.dump(rec, f)
            f.write("\n")

    log.info(f"Statistical analysis completed. Results written to {out_path}")
    return 0

if __name__ == "__main__":
    sys.exit(main())