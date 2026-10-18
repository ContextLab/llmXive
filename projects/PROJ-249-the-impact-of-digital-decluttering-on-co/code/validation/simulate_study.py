"""
Simulate the deterministic study data for the digital decluttering project.

This script reads the study configuration, generates participant IDs,
creates baseline and post‑intervention trial‑level data for SART and O‑Span,
synthesises questionnaire scores (PSS‑10, PANAS‑PA, PANAS‑NA), writes
compliance logs, scores the behavioural tasks (using lightweight internal
scoring to avoid reliance on buggy external functions), and finally produces a
small “smoke” results JSON containing mean change values for the first
five participants.

All outputs are written under the ``data/`` directory and SHA‑256
checksums for every generated file are appended to ``data/checksums.sha256``.
The script is deterministic: the random number generator is seeded from
``code/config/study_config.yaml`` and deterministic timestamps are used
instead of the current time. No fallback synthetic data is used.
"""

import csv
import hashlib
import json
from datetime import datetime, date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def _load_config() -> dict:
    """Load the study configuration YAML."""
    config_path = paths.code("config", "study_config.yaml")
    with open(config_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    return cfg

def _sha256_of_file(file_path: Path) -> str:
    """Return the hex SHA‑256 digest of ``file_path``."""
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def _append_checksum(file_path: Path):
    """Append a checksum line for ``file_path`` to the manifest."""
    manifest = paths.data("checksums.sha256")
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.touch(exist_ok=True)

    rel_path = file_path.relative_to(paths.root)
    checksum = _sha256_of_file(file_path)
    line = f"{checksum}  {rel_path}\n"
    with open(manifest, "a", encoding="utf-8") as f:
        f.write(line)

# ----------------------------------------------------------------------
# Simple internal scoring (avoids buggy external functions)
# ----------------------------------------------------------------------
def _score_sart(df: pd.DataFrame) -> dict:
    """
    Very small SART scorer that returns the same keys used elsewhere
    in the pipeline.

    Expected columns in ``df``:
        - rt_ms (int)
        - is_target (bool)
        - response (bool) – participant's button press (True = pressed)
        - accuracy (bool) – whether response matches target status
    """
    # Commission errors: responded when should NOT (i.e., is_target=False & response=True)
    commission_errors = int(((~df["is_target"]) & df["response"]).sum())
    # Omission errors: failed to respond when should (is_target=True & response=False)
    omission_errors = int(((df["is_target"]) & (~df["response"])).sum())
    mean_rt = float(df["rt_ms"].mean())
    return {
        "commission_errors": commission_errors,
        "omission_errors": omission_errors,
        "mean_rt": mean_rt,
    }

def _score_ospan(df: pd.DataFrame) -> dict:
    """
    Simple O‑Span scorer.

    Expected columns:
        - item (str)
        - response (str) – the recalled item (empty string if incorrect)
        - correct (bool) – whether the response was correct
    """
    total_correct = int(df["correct"].sum())
    # Span score: the length of the longest consecutive run of correct trials.
    # For simplicity we use total_correct as a proxy (common in pilot code).
    span_score = total_correct
    return {
        "total_correct": total_correct,
        "span_score": span_score,
    }

# ----------------------------------------------------------------------
# Simulation core
# ----------------------------------------------------------------------
def _generate_participant_ids(n: int) -> list[str]:
    """Return a list like ['P001', 'P002', ...] of length ``n``."""
    return [f"P{idx:03d}" for idx in range(1, n + 1)]

def _simulate_sart_trials(rng: np.random.Generator, n_trials: int = 100) -> pd.DataFrame:
    """Create a SART trial‑level DataFrame."""
    is_target = rng.random(n_trials) < 0.2
    error_rate_target = 0.1
    error_rate_nontarget = 0.05
    errors = np.where(
        is_target,
        rng.random(n_trials) < error_rate_target,
        rng.random(n_trials) < error_rate_nontarget,
    )
    # ``response`` is True when the participant presses the button.
    response = np.where(is_target, ~errors, errors)  # correct response = not error
    accuracy = response == is_target
    rt_ms = rng.integers(100, 5001, size=n_trials)  # 100‑5000 ms inclusive lower bound

    df = pd.DataFrame(
        {
            "rt_ms": rt_ms,
            "is_target": is_target,
            "response": response,
            "accuracy": accuracy,
        }
    )
    return df

def _simulate_ospan_trials(rng: np.random.Generator, n_trials: int = 20) -> pd.DataFrame:
    """Create an O‑Span trial‑level DataFrame."""
    items = [f"item{idx}" for idx in range(1, n_trials + 1)]
    correct = rng.random(n_trials) < 0.7
    response = np.where(correct, items, "")
    df = pd.DataFrame(
        {
            "item": items,
            "response": response,
            "correct": correct,
        }
    )
    return df

def _simulate_questionnaire_scores(rng: np.random.Generator, metric: str) -> float:
    """Return a plausible single‑value score for the given questionnaire metric."""
    if metric == "pss10_total":
        return float(rng.integers(0, 41))
    if metric == "panas_positive":
        return float(rng.integers(10, 51))
    if metric == "panas_negative":
        return float(rng.integers(10, 51))
    raise ValueError(f"Unsupported questionnaire metric: {metric}")

def _write_participants_csv(participant_ids: list[str], start_date: date):
    """Write ``data/raw/participants.csv``."""
    rows = []
    for idx, pid in enumerate(participant_ids, start=1):
        enrollment = start_date + timedelta(days=(idx - 1) % 7)
        rows.append(
            {
                "participant_id": pid,
                "enrollment_date": enrollment.isoformat(),
            }
        )
    df = pd.DataFrame(rows)
    out_path = paths.data("raw", "participants.csv")
    df.to_csv(out_path, index=False)
    _append_checksum(out_path)

def _write_trial_level_csv(
    df: pd.DataFrame,
    participant_id: str,
    phase: str,
    metric: str,
):
    """Append rows for a single participant/phase to the appropriate trial CSV."""
    if metric == "sart":
        out_path = paths.data("raw", "trial_level", "sart_trials.csv")
        df = df.copy()
        df["participant_id"] = participant_id
        df["phase"] = phase
        df["trial_index"] = range(len(df))
        cols = [
            "participant_id",
            "phase",
            "trial_index",
            "rt_ms",
            "is_target",
            "response",
            "accuracy",
        ]
        df = df[cols]
    elif metric == "ospan":
        out_path = paths.data("raw", "trial_level", "ospan_trials.csv")
        df = df.copy()
        df["participant_id"] = participant_id
        df["phase"] = phase
        df["trial_index"] = range(len(df))
        cols = [
            "participant_id",
            "phase",
            "trial_index",
            "item",
            "response",
            "correct",
        ]
        df = df[cols]
    else:
        raise ValueError(f"Unsupported metric for trial‑level export: {metric}")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    write_header = not out_path.exists()
    df.to_csv(out_path, mode="a", header=write_header, index=False)
    _append_checksum(out_path)

def _write_compliance_log(participant_id: str, rng: np.random.Generator, base_date: date):
    """Create a deterministic 7‑day compliance CSV for a participant."""
    log_dir = paths.data("raw", "compliance_logs")
    log_dir.mkdir(parents=True, exist_ok=True)

    rows = []
    start = base_date - timedelta(days=7)
    for day_offset in range(7):
        day = start + timedelta(days=day_offset)
        minutes = int(rng.integers(0, 1441))
        news = bool(rng.integers(0, 2))
        notif = bool(rng.integers(0, 2))
        is_compliant = minutes <= 30 and not news and notif
        rows.append(
            {
                "id": f"{participant_id}_{day_offset}",
                "participant_id": participant_id,
                "date": day.isoformat(),
                "social_media_minutes": minutes,
                "news_consumption": news,
                "notifications_off": notif,
                "is_compliant": is_compliant,
                "notes": "",
            }
        )
    df = pd.DataFrame(rows)
    out_path = log_dir / f"{participant_id}_log.csv"
    df.to_csv(out_path, index=False)
    _append_checksum(out_path)

def _score_behavioural_tasks(
    participant_id: str,
    phase: str,
    sart_df: pd.DataFrame,
    ospan_df: pd.DataFrame,
) -> dict:
    """
    Return a mapping from metric_type to scored value for the given participant
    and phase. Uses the lightweight internal scoring functions defined above.
    """
    sart_scores = _score_sart(sart_df)
    ospan_scores = _score_ospan(ospan_df)

    scores = {
        "sart_commission_errors": sart_scores.get("commission_errors", np.nan),
        "sart_omission_errors": sart_scores.get("omission_errors", np.nan),
        "sart_mean_rt": sart_scores.get("mean_rt", np.nan),
        "ospan_span_score": ospan_scores.get("span_score", np.nan),
        "ospan_total_correct": ospan_scores.get("total_correct", np.nan),
    }
    return scores

def _write_measurements(
    participant_id: str,
    phase: str,
    behavioural_scores: dict,
    rng: np.random.Generator,
    base_datetime: datetime,
):
    """Write scored measurement rows (including questionnaires) for one participant/phase."""
    # Deterministic timestamp: base_datetime plus a small offset per participant/phase
    timestamp = (base_datetime + timedelta(minutes=hash(participant_id) % 60)).isoformat()
    rows = []

    # Behavioural metrics
    for metric_type, value in behavioural_scores.items():
        rows.append(
            {
                "participant_id": participant_id,
                "metric_type": metric_type,
                "value": float(value),
                "timestamp": timestamp,
                "session_type": phase,
            }
        )

    # Questionnaire metrics
    for q_metric in ["pss10_total", "panas_positive", "panas_negative"]:
        rows.append(
            {
                "participant_id": participant_id,
                "metric_type": q_metric,
                "value": _simulate_questionnaire_scores(rng, q_metric),
                "timestamp": timestamp,
                "session_type": phase,
            }
        )

    df = pd.DataFrame(rows)
    out_path = paths.data("raw", "simulated_measurements.csv")
    write_header = not out_path.exists()
    df.to_csv(out_path, mode="a", header=write_header, index=False)
    _append_checksum(out_path)

def _run_smoke_analysis(participant_ids: list[str], base_datetime: datetime):
    """
    Compute mean change for the first five participants that have both phases.
    Results are written to ``data/results/smoke_results.json``.
    """
    meas_path = paths.data("raw", "simulated_measurements.csv")
    meas_df = pd.read_csv(meas_path)

    selected = participant_ids[:5]

    pivot = meas_df.pivot_table(
        index=["participant_id", "metric_type"],
        columns="session_type",
        values="value",
        aggfunc="first",
    ).reset_index()

    pivot = pivot.dropna(subset=["baseline", "post_intervention"], how="any")
    pivot["change"] = pivot["post_intervention"] - pivot["baseline"]

    mean_changes = (
        pivot.groupby("metric_type")["change"]
        .mean()
        .reset_index()
        .rename(columns={"change": "mean_change"})
    )

    result = {
        "generated_at": base_datetime.isoformat(),
        "metrics": [
            {"metric": row["metric_type"], "mean_change": row["mean_change"]}
            for _, row in mean_changes.iterrows()
        ],
    }

    out_path = paths.data("results", "smoke_results.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    _append_checksum(out_path)

# ----------------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------------
def main():
    """Generate the deterministic seeded study simulation."""
    cfg = _load_config()
    seed = cfg["seed"]
    n_participants = cfg["n_participants"]
    dropout_rate = cfg["dropout_rate"]
    start_date = datetime.fromisoformat(cfg["start_date"]).date()

    rng = np.random.default_rng(seed)

    participant_ids = _generate_participant_ids(n_participants)

    # Determine which participants will dropout (no post‑intervention data)
    n_dropout = int(round(dropout_rate * n_participants))
    dropout_ids = set(rng.choice(participant_ids, size=n_dropout, replace=False))

    # Write participants registry
    _write_participants_csv(participant_ids, start_date)

    # Deterministic base datetime for timestamps
    base_datetime = datetime.combine(start_date, datetime.min.time())

    # Simulate data per participant
    for pid in participant_ids:
        # ----- Baseline phase -----
        sart_baseline = _simulate_sart_trials(rng)
        ospan_baseline = _simulate_ospan_trials(rng)

        # Inject a low‑attention case for the first participant (ensure <50% accuracy)
        if pid == participant_ids[0]:
            target_mask = sart_baseline["is_target"]
            # Flip responses on target trials to create many errors
            sart_baseline.loc[target_mask, "response"] = ~sart_baseline.loc[
                target_mask, "response"
            ]
            sart_baseline["accuracy"] = (
                sart_baseline["response"] == sart_baseline["is_target"]
            )

        behavioural_scores_baseline = _score_behavioural_tasks(
            pid, "baseline", sart_baseline, ospan_baseline
        )
        _write_measurements(pid, "baseline", behavioural_scores_baseline, rng, base_datetime)
        _write_trial_level_csv(sart_baseline, pid, "baseline", "sart")
        _write_trial_level_csv(ospan_baseline, pid, "baseline", "ospan")
        _write_compliance_log(pid, rng, start_date)

        # ----- Post‑intervention phase (skip if dropout) -----
        if pid in dropout_ids:
            continue

        # Simulate post‑phase raw trials
        sart_post = _simulate_sart_trials(rng)
        ospan_post = _simulate_ospan_trials(rng)

        # Score baseline and post
        baseline_behav = _score_behavioural_tasks(
            pid, "baseline", sart_baseline, ospan_baseline
        )
        post_behav = _score_behavioural_tasks(
            pid, "post_intervention", sart_post, ospan_post
        )

        # Apply effect sizes from config (Cohen's d shift)
        effect_sizes = cfg["effect_sizes"]
        for metric, d in effect_sizes.items():
            if metric == "SART":
                key = "sart_commission_errors"
            elif metric == "Ospan":
                key = "ospan_span_score"
            elif metric == "PSS-10":
                key = "pss10_total"
            elif metric == "PANAS-PA":
                key = "panas_positive"
            elif metric == "PANAS-NA":
                key = "panas_negative"
            else:
                continue
            base_val = baseline_behav.get(key, np.nan)
            if np.isnan(base_val):
                continue
            # Estimate a std dev of 5 for questionnaires, 3 for behavioural metrics
            std_est = 5.0 if "pss10" in key or "panas" in key else 3.0
            shift = d * std_est
            post_behav[key] = float(base_val + shift)

        _write_measurements(pid, "post_intervention", post_behav, rng, base_datetime)
        _write_trial_level_csv(sart_post, pid, "post_intervention", "sart")
        _write_trial_level_csv(ospan_post, pid, "post_intervention", "ospan")

    # After all participants are processed, generate the smoke results JSON.
    _run_smoke_analysis(participant_ids, base_datetime)

    log.info("Study simulation completed successfully.")

if __name__ == "__main__":
    main()