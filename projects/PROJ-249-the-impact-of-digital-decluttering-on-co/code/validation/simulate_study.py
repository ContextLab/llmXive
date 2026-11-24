"""
Simulate a fully‑scored study dataset for the digital decluttering project.

This script creates deterministic, reproducible simulated data conforming to
the `contracts/dataset.schema.yaml` JSON‑Schema.  All files are written under
the `data/` folder using the `llmxive_toolkit.paths` helpers, and a SHA‑256
manifest (`data/checksums.sha256`) is generated for every artifact.

Expected outputs (all under `data/raw/`):
  - participants_simulated.csv
  - trial_level/sart_trials_sim.csv
  - trial_level/ospan_trials_sim.csv
  - measurement_records_sim.csv
  - compliance_logs_sim/   (seven daily CSVs per participant)

The script can be invoked directly:
    python code/validation/simulate_study.py
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

def _write_checksum(file_path: Path, manifest_path: Path):
    """Append a checksum line for ``file_path`` to ``manifest_path``."""
    rel_path = file_path.relative_to(paths.root)
    checksum = _sha256_of_file(file_path)
    line = f"{checksum}  {rel_path}\n"
    with open(manifest_path, "a", encoding="utf-8") as f:
        f.write(line)

# ----------------------------------------------------------------------
# Scoring utilities (lightweight, deterministic)
# ----------------------------------------------------------------------
def _score_sart(df: pd.DataFrame) -> dict:
    """
    Simple SART scorer returning commission/omission errors,
    mean response time and a quality flag.
    """
    commission_errors = int(((~df["is_target"]) & df["response"]).sum())
    omission_errors = int(((df["is_target"]) & (~df["response"])).sum())
    mean_rt = float(df["rt_ms"].mean())

    # Accuracy = proportion of correct responses
    accuracy = float(((df["response"] == df["is_target"])).mean())
    quality_flag = "valid" if accuracy >= 0.5 else "low_attention"

    return {
        "commission_errors": commission_errors,
        "omission_errors": omission_errors,
        "mean_rt": mean_rt,
        "quality_flag": quality_flag,
    }

def _score_ospan(df: pd.DataFrame) -> dict:
    """
    Simple O‑Span scorer.  For the simulated data we treat the total
    number of correct recalls as the span score.
    """
    total_correct = int(df["correct"].sum())
    # In this simplified version the span score equals total correct.
    span_score = total_correct
    quality_flag = "valid"  # O‑Span does not have a low‑attention flag here.
    return {
        "total_correct": total_correct,
        "span_score": span_score,
        "quality_flag": quality_flag,
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
    rt_ms = rng.integers(100, 5001, size=n_trials)  # inclusive lower bound

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

def _simulate_questionnaire_score(rng: np.random.Generator, metric: str) -> float:
    """Generate a plausible score for the given questionnaire metric."""
    if metric == "pss10_total":
        return float(rng.integers(0, 41))
    if metric == "panas_positive":
        return float(rng.integers(10, 51))
    if metric == "panas_negative":
        return float(rng.integers(10, 51))
    raise ValueError(f"Unsupported questionnaire metric: {metric}")

# ----------------------------------------------------------------------
# Writing helpers – each run overwrites for determinism
# ----------------------------------------------------------------------
def _write_participants(participant_ids: list[str], start_date: date, manifest_path: Path):
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
    out_path = paths.data("raw", "participants_simulated.csv")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)
    _write_checksum(out_path, manifest_path)

def _write_trial_level_files(
    sart_rows: list[dict],
    ospan_rows: list[dict],
    manifest_path: Path,
):
    # SART
    sart_path = paths.data("raw", "trial_level", "sart_trials_sim.csv")
    sart_path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(sart_rows).to_csv(sart_path, index=False)
    _write_checksum(sart_path, manifest_path)

    # OSPAN
    ospan_path = paths.data("raw", "trial_level", "ospan_trials_sim.csv")
    ospan_path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(ospan_rows).to_csv(ospan_path, index=False)
    _write_checksum(ospan_path, manifest_path)

def _write_compliance_logs(
    participant_ids: list[str],
    rng: np.random.Generator,
    start_date: date,
    manifest_path: Path,
):
    log_dir = paths.data("raw", "compliance_logs_sim")
    log_dir.mkdir(parents=True, exist_ok=True)
    for pid in participant_ids:
        rows = []
        # Compliance period: 7 days prior to participant enrollment
        base = start_date - timedelta(days=7)
        for day_offset in range(7):
            day = base + timedelta(days=day_offset)
            minutes = int(rng.integers(0, 1441))
            news = bool(rng.integers(0, 2))
            notif = bool(rng.integers(0, 2))
            is_compliant = minutes <= 30 and not news and notif
            rows.append(
                {
                    "id": f"{pid}_{day_offset}",
                    "participant_id": pid,
                    "date": day.isoformat(),
                    "social_media_minutes": minutes,
                    "news_consumption": news,
                    "notifications_off": notif,
                    "is_compliant": is_compliant,
                    "notes": "",
                }
            )
        df = pd.DataFrame(rows)
        out_path = log_dir / f"{pid}_log.csv"
        df.to_csv(out_path, index=False)
        _write_checksum(out_path, manifest_path)

def _write_measurement_records(
    measurement_rows: list[dict],
    manifest_path: Path,
):
    out_path = paths.data("raw", "measurement_records_sim.csv")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(measurement_rows).to_csv(out_path, index=False)
    _write_checksum(out_path, manifest_path)

# ----------------------------------------------------------------------
# Scoring wrapper (behavioural tasks)
# ----------------------------------------------------------------------
def _score_behavioural_tasks(
    sart_df: pd.DataFrame,
    ospan_df: pd.DataFrame,
) -> dict:
    """
    Return a mapping from internal metric identifiers to scored values
    together with their quality flags for a single participant / phase.
    """
    sart_scores = _score_sart(sart_df)
    ospan_scores = _score_ospan(ospan_df)

    return {
        "sart_commission_errors": (
            sart_scores["commission_errors"],
            sart_scores["quality_flag"],
        ),
        "sart_omission_errors": (
            sart_scores["omission_errors"],
            sart_scores["quality_flag"],
        ),
        "sart_mean_rt": (
            sart_scores["mean_rt"],
            sart_scores["quality_flag"],
        ),
        "ospan_span_score": (
            ospan_scores["span_score"],
            ospan_scores["quality_flag"],
        ),
        "ospan_total_correct": (
            ospan_scores["total_correct"],
            ospan_scores["quality_flag"],
        ),
    }

# ----------------------------------------------------------------------
# Smoke analysis (tiny summary printed to stdout)
# ----------------------------------------------------------------------
def _run_smoke_analysis(
    measurements: pd.DataFrame,
    participant_ids: list[str],
    base_datetime: datetime,
    manifest_path: Path,
):
    selected = participant_ids[:5]

    pivot = measurements.pivot_table(
        index=["participant_id", "metric_type"],
        columns="phase",
        values="value",
        aggfunc="first",
    ).reset_index()

    pivot = pivot.dropna(subset=["baseline", "post"], how="any")
    pivot["change"] = pivot["post"] - pivot["baseline"]
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
            if row["metric_type"] in selected  # just a tiny sanity check
        ],
    }

    out_path = paths.data("results", "smoke_results.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    _write_checksum(out_path, manifest_path)

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
    effect_sizes = cfg.get("effect_sizes", {})

    rng = np.random.default_rng(seed)

    # Prepare checksum manifest – start fresh each run for determinism
    manifest_path = paths.data("checksums.sha256")
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text("", encoding="utf-8")

    participant_ids = _generate_participant_ids(n_participants)

    # Determine dropout participants
    n_dropout = int(round(dropout_rate * n_participants))
    dropout_ids = set(rng.choice(participant_ids, size=n_dropout, replace=False))

    # Containers for accumulating rows
    sart_rows = []
    ospan_rows = []
    measurement_rows = []

    # Write participants registry
    _write_participants(participant_ids, start_date, manifest_path)

    # Write compliance logs (independent of dropout)
    _write_compliance_logs(participant_ids, rng, start_date, manifest_path)

    # Deterministic base datetime for timestamps
    base_datetime = datetime.combine(start_date, datetime.min.time())

    for idx, pid in enumerate(participant_ids):
        # ---------- Baseline ----------
        sart_baseline = _simulate_sart_trials(rng)
        ospan_baseline = _simulate_ospan_trials(rng)

        # Inject low‑attention case for first participant (trigger flag)
        if idx == 0:
            target_mask = sart_baseline["is_target"]
            sart_baseline.loc[target_mask, "response"] = ~sart_baseline.loc[
                target_mask, "response"
            ]
            sart_baseline["accuracy"] = (
                sart_baseline["response"] == sart_baseline["is_target"]
            )

        baseline_scores = _score_behavioural_tasks(sart_baseline, ospan_baseline)

        # Timestamp for this participant (deterministic)
        timestamp = (base_datetime + timedelta(minutes=idx * 10)).isoformat()

        # Record baseline measurement rows (behavioural)
        for metric_key, (value, qflag) in baseline_scores.items():
            measurement_rows.append(
                {
                    "id": f"{pid}_baseline_{metric_key}",
                    "participant_id": pid,
                    "phase": "baseline",
                    "metric_type": metric_key,
                    "value": float(value),
                    "timestamp": timestamp,
                    "quality_flag": qflag,
                }
            )
        # Record baseline questionnaire rows
        for q_metric in ["pss10_total", "panas_positive", "panas_negative"]:
            measurement_rows.append(
                {
                    "id": f"{pid}_baseline_{q_metric}",
                    "participant_id": pid,
                    "phase": "baseline",
                    "metric_type": q_metric,
                    "value": _simulate_questionnaire_score(rng, q_metric),
                    "timestamp": timestamp,
                    "quality_flag": "valid",
                }
            )

        # Append trial‑level rows for baseline
        for trial_idx, row in sart_baseline.iterrows():
            sart_rows.append(
                {
                    "participant_id": pid,
                    "phase": "baseline",
                    "trial_index": int(trial_idx),
                    "rt_ms": int(row["rt_ms"]),
                    "is_target": bool(row["is_target"]),
                    "response": bool(row["response"]),
                    "accuracy": bool(row["accuracy"]),
                }
            )
        for trial_idx, row in ospan_baseline.iterrows():
            ospan_rows.append(
                {
                    "participant_id": pid,
                    "phase": "baseline",
                    "trial_index": int(trial_idx),
                    "item": row["item"],
                    "response": row["response"],
                    "correct": bool(row["correct"]),
                }
            )

        # ---------- Post‑intervention ----------
        if pid in dropout_ids:
            # Skip post‑phase for dropout participants
            continue

        sart_post = _simulate_sart_trials(rng)
        ospan_post = _simulate_ospan_trials(rng)

        post_scores = _score_behavioural_tasks(sart_post, ospan_post)

        # Apply effect‑size shifts as defined in the config
        for metric_key, d in effect_sizes.items():
            mapping = {
                "SART": "sart_commission_errors",
                "Ospan": "ospan_span_score",
                "PSS-10": "pss10_total",
                "PANAS-PA": "panas_positive",
                "PANAS-NA": "panas_negative",
            }
            internal_key = mapping.get(metric_key)
            if internal_key and internal_key in post_scores:
                base_val, _ = baseline_scores.get(internal_key, (np.nan, "valid"))
                if not np.isnan(base_val):
                    # Simple std‑dev estimate (3 for behavioural, 5 for questionnaires)
                    std_est = 5.0 if "pss10" in internal_key or "panas" in internal_key else 3.0
                    shift = d * std_est
                    post_scores[internal_key] = (float(base_val + shift), post_scores[internal_key][1])

        # Record post measurement rows (behavioural)
        for metric_key, (value, qflag) in post_scores.items():
            measurement_rows.append(
                {
                    "id": f"{pid}_post_{metric_key}",
                    "participant_id": pid,
                    "phase": "post",
                    "metric_type": metric_key,
                    "value": float(value),
                    "timestamp": timestamp,
                    "quality_flag": qflag,
                }
            )
        # Record post questionnaire rows
        for q_metric in ["pss10_total", "panas_positive", "panas_negative"]:
            measurement_rows.append(
                {
                    "id": f"{pid}_post_{q_metric}",
                    "participant_id": pid,
                    "phase": "post",
                    "metric_type": q_metric,
                    "value": _simulate_questionnaire_score(rng, q_metric),
                    "timestamp": timestamp,
                    "quality_flag": "valid",
                }
            )

        # Append trial‑level rows for post
        for trial_idx, row in sart_post.iterrows():
            sart_rows.append(
                {
                    "participant_id": pid,
                    "phase": "post",
                    "trial_index": int(trial_idx),
                    "rt_ms": int(row["rt_ms"]),
                    "is_target": bool(row["is_target"]),
                    "response": bool(row["response"]),
                    "accuracy": bool(row["accuracy"]),
                }
            )
        for trial_idx, row in ospan_post.iterrows():
            ospan_rows.append(
                {
                    "participant_id": pid,
                    "phase": "post",
                    "trial_index": int(trial_idx),
                    "item": row["item"],
                    "response": row["response"],
                    "correct": bool(row["correct"]),
                }
            )

    # Write accumulated trial‑level files (overwrites any previous content)
    _write_trial_level_files(sart_rows, ospan_rows, manifest_path)

    # Write all measurement records
    _write_measurement_records(measurement_rows, manifest_path)

    # Load measurements into DataFrame for smoke analysis
    meas_df = pd.read_csv(paths.data("raw", "measurement_records_sim.csv"))

    # Run a tiny smoke analysis for the first five participants
    _run_smoke_analysis(meas_df, participant_ids, base_datetime, manifest_path)

    log.info("Study simulation completed successfully.")
    print("Simulation complete. Generated files:")
    print("- participants_simulated.csv")
    print("- trial_level/sart_trials_sim.csv")
    print("- trial_level/ospan_trials_sim.csv")
    print("- measurement_records_sim.csv")
    print("- compliance_logs_sim/ (one CSV per participant)")
    print("- results/smoke_results.json")
    print("- data/checksums.sha256")

if __name__ == "__main__":
    main()
