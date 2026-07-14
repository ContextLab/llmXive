"""Deterministic HOLLOW-RESULTS gate.

The execution gate asked only "did a file appear?" (``bool(produced)``) and never
looked INSIDE it. So PROJ-179 — a study of metacognitive awareness — reached
``research_complete`` having run on the IRIS FLOWER dataset and written:

    data/results/primary_analysis.json   {"correlation_coefficient": null,
                                          "p_value": null, "ci_lower": null,
                                          "ci_upper": null}
    data/results/correlation_metrics.json {"d_prime": NaN, "metacognitive_score": 0.0}
    data/results/robustness_analysis.json []
    data/validation_report.json           {"status": "PASS"}

Every headline number is null, NaN, or empty — and it self-certified PASS. Files
existed, so the gate said ok. A result that is null/NaN/empty is not a measurement;
these must be a hard gate failure, exactly like fabrication.

The bar is HIGH PRECISION — honest work must never be blocked. A zero, a negative
number, a legitimately-absent optional field, and a non-numeric report are all fine.
"""

from __future__ import annotations

import json
from pathlib import Path

from llmxive.execution.hollow_guard import find_hollow_results


def _proj(tmp_path: Path, files: dict[str, str]) -> Path:
    for rel, body in files.items():
        f = tmp_path / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(body, encoding="utf-8")
    return tmp_path


# --- must FLAG (these are the real PROJ-179 artifacts) -------------------------

def test_flags_all_null_primary_result(tmp_path: Path) -> None:
    p = _proj(tmp_path, {"data/results/primary_analysis.json": json.dumps(
        {"correlation_coefficient": None, "p_value": None,
         "ci_lower": None, "ci_upper": None})})
    found = find_hollow_results(p, ["data/results/primary_analysis.json"])
    assert found, "an all-null primary result is not a measurement"
    assert "primary_analysis.json" in found[0]


def test_flags_nan_metric(tmp_path: Path) -> None:
    p = _proj(tmp_path, {"data/results/correlation_metrics.json":
                         '{"metacognitive_score": 0.0, "d_prime": NaN, "n_train": 105}'})
    found = find_hollow_results(p, ["data/results/correlation_metrics.json"])
    assert found and "d_prime" in found[0], found


def test_flags_empty_results_container(tmp_path: Path) -> None:
    p = _proj(tmp_path, {"data/results/robustness_analysis.json": "[]"})
    found = find_hollow_results(p, ["data/results/robustness_analysis.json"])
    assert found and "empty" in found[0].lower(), found


def test_flags_header_only_csv(tmp_path: Path) -> None:
    p = _proj(tmp_path, {"data/results/trials.csv": "participant_id,confidence\n"})
    found = find_hollow_results(p, ["data/results/trials.csv"])
    assert found, "a CSV with no data rows carries no measurement"


def test_flags_entirely_empty_column(tmp_path: Path) -> None:
    """PROJ-179's `confidence_rating` — the study's KEY measure — was blank in every
    row, yet the run passed."""
    p = _proj(tmp_path, {"data/derived/trial_data.csv":
                         "participant_id,response,confidence_rating\n"
                         "P1,3.5,\nP2,3.0,\nP3,2.5,\n"})
    found = find_hollow_results(p, ["data/derived/trial_data.csv"])
    assert found and "confidence_rating" in found[0], found


# --- must NOT flag (honest results) -------------------------------------------

def test_accepts_real_metrics(tmp_path: Path) -> None:
    p = _proj(tmp_path, {"data/results/primary_analysis.json": json.dumps(
        {"correlation_coefficient": -0.42, "p_value": 0.003, "n": 150})})
    assert find_hollow_results(p, ["data/results/primary_analysis.json"]) == []


def test_accepts_zero_and_negative_values(tmp_path: Path) -> None:
    """0.0 and negatives are REAL measurements — never confuse them with missing."""
    p = _proj(tmp_path, {"data/results/effects.json": json.dumps(
        {"effect_size": 0.0, "delta": -1.5})})
    assert find_hollow_results(p, ["data/results/effects.json"]) == []


def test_accepts_non_numeric_report(tmp_path: Path) -> None:
    """A textual report has no metrics to be hollow — not our business."""
    p = _proj(tmp_path, {"data/results/notes.json": json.dumps(
        {"dataset": "openneuro-ds000117", "status": "complete"})})
    assert find_hollow_results(p, ["data/results/notes.json"]) == []


def test_accepts_populated_csv(tmp_path: Path) -> None:
    p = _proj(tmp_path, {"data/results/trials.csv":
                         "id,rt,confidence\n1,0.42,3\n2,0.51,4\n"})
    assert find_hollow_results(p, ["data/results/trials.csv"]) == []


def test_ignores_raw_inputs_and_figures(tmp_path: Path) -> None:
    """Only RESULT artifacts are judged; an input file or a PNG is not a metric."""
    p = _proj(tmp_path, {"data/raw/input.csv": "a,b\n", "data/results/f.png": "x"})
    assert find_hollow_results(p, ["data/raw/input.csv", "data/results/f.png"]) == []


# --- durable evidence: a run whose every output is gitignored proves nothing -----

def _git_repo(tmp_path: Path) -> Path:
    import subprocess
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    (tmp_path / ".gitignore").write_text(
        "projects/*/data/raw/*\nprojects/*/data/processed/*\n", encoding="utf-8"
    )
    return tmp_path


def test_flags_run_whose_only_artifact_is_gitignored(tmp_path: Path) -> None:
    """PROJ-256: its ONE artifact was data/processed/*.json — gitignored, so nothing
    was committed and the empirical contribution evaporated. It still advanced."""
    from llmxive.execution.hollow_guard import find_no_durable_evidence

    repo = _git_repo(tmp_path)
    pdir = repo / "projects" / "PROJ-256-x"
    (pdir / "data" / "processed").mkdir(parents=True)
    (pdir / "data" / "processed" / "null_fpr_metrics.json").write_text('{"fpr": 0.05}')
    found = find_no_durable_evidence(
        pdir, ["data/processed/null_fpr_metrics.json"], repo_root=repo
    )
    assert found and "no durable evidence" in found[0].lower(), found


def test_accepts_a_committed_result_alongside_ignored_caches(tmp_path: Path) -> None:
    from llmxive.execution.hollow_guard import find_no_durable_evidence

    repo = _git_repo(tmp_path)
    pdir = repo / "projects" / "PROJ-777-x"
    (pdir / "data" / "processed").mkdir(parents=True)
    (pdir / "data" / "results").mkdir(parents=True)
    (pdir / "data" / "processed" / "cache.json").write_text("{}")
    (pdir / "data" / "results" / "primary.json").write_text('{"r": -0.42}')
    assert find_no_durable_evidence(
        pdir,
        ["data/processed/cache.json", "data/results/primary.json"],
        repo_root=repo,
    ) == []


def test_durability_probe_fails_open_outside_git(tmp_path: Path) -> None:
    """A bad probe must never block honest work."""
    from llmxive.execution.hollow_guard import find_no_durable_evidence

    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "x.json").write_text("{}")
    assert find_no_durable_evidence(tmp_path, ["data/x.json"], repo_root=tmp_path) == []
