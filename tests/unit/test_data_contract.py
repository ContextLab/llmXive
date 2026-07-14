"""Real (no-mock) tests for the cross-script DATA-schema contract self-heal.

These build a synthetic tmp project on disk — a real producer script, a real
consumer script, and a real artifact with a real header — then drive the detector
+ renderer end to end. The VERIFICATION test runs the detector against PROJ-262's
REAL recorded failures and REAL code/results (read-only) to prove the implementer
would now SEE the trivial column-rename it has been thrashing on for 12 rounds.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from llmxive.execution.data_contract import (
    accumulate_data_contract_issues,
    find_data_contract_issues,
    render_data_contract_feedback,
    reopen_targets,
)


def _make_project(tmp_path: Path) -> Path:
    """Producer writes [seed, model_type, MAE, RMSE]; consumer needs [mae, rmse, model]."""
    proj = tmp_path / "PROJ-999-x"
    (proj / "code").mkdir(parents=True)
    (proj / "results").mkdir(parents=True)
    (proj / "results" / "metrics.csv").write_text(
        "seed,model_type,MAE,RMSE\n0,RF,0.11,0.22\n", encoding="utf-8"
    )
    (proj / "code" / "generate_metrics.py").write_text(
        "import csv\n"
        "fieldnames = ['seed', 'model_type', 'MAE', 'RMSE']\n"
        "with open('results/metrics.csv', 'w', newline='') as f:\n"
        "    w = csv.DictWriter(f, fieldnames=fieldnames)\n"
        "    w.writeheader()\n",
        encoding="utf-8",
    )
    (proj / "code" / "make_plots.py").write_text(
        "import pandas as pd\n"
        "def load_metrics(p):\n"
        "    df = pd.read_csv('results/metrics.csv')\n"
        "    expected = {'seed', 'model', 'mae', 'rmse'}\n"
        "    missing = expected - set(df.columns)\n"
        "    if missing:\n"
        "        raise ValueError(f'Metrics CSV missing columns: {missing}')\n",
        encoding="utf-8",
    )
    return proj


def test_detects_file_reads_real_header_and_reports_rename_diff(tmp_path) -> None:
    proj = _make_project(tmp_path)
    failures = [
        'File "/runner/code/make_plots.py", line 3, in load_metrics\n'
        "    df = pd.read_csv('results/metrics.csv')\n"
        "ValueError: Metrics CSV missing columns: {'rmse', 'model', 'mae'}"
    ]
    issues = find_data_contract_issues(proj, failures)
    assert len(issues) == 1
    iss = issues[0]

    # Found the data file from the failing consumer's source.
    assert iss.data_file == "results/metrics.csv"
    # Read the REAL header off disk (the producer actually ran).
    assert iss.actual == ["seed", "model_type", "MAE", "RMSE"]
    # Parsed the consumer's required columns (no stray f-string placeholder).
    assert set(iss.required) == {"mae", "rmse", "model"}
    # Producer (writer) is found and is a reopen target.
    assert "code/generate_metrics.py" in iss.producers
    assert "code/make_plots.py" in iss.consumers
    # Precise actual->required rename mapping (case + model_type alias).
    assert iss.rename_map() == {"MAE": "mae", "RMSE": "rmse", "model_type": "model"}

    # The producer is a reopen target (path + stem).
    targets = reopen_targets(issues)
    assert "code/generate_metrics.py" in targets
    assert "generate_metrics" in targets

    fb = render_data_contract_feedback(issues)
    assert "results/metrics.csv" in fb
    assert "[seed, model_type, MAE, RMSE]" in fb           # actual
    assert "MAE -> mae" in fb and "model_type -> model" in fb  # rename diff
    assert "generate_metrics.py" in fb                     # named producer
    assert "PRODUCER" in fb


def test_missing_intermediate_file_points_at_producer(tmp_path) -> None:
    """A FileNotFoundError on an intermediate file points at the script that
    should WRITE it, and treats the consumers as cascade victims."""
    proj = tmp_path / "PROJ-998-x"
    (proj / "code").mkdir(parents=True)
    (proj / "code" / "compute_sig.py").write_text(
        "import csv\n"
        "with open('results/significance.csv', 'w') as f:\n"
        "    csv.writer(f).writerow(['metric', 'p_value'])\n",
        encoding="utf-8",
    )
    (proj / "code" / "summarize.py").write_text(
        "import csv\n"
        "with open('results/significance.csv') as f:\n"
        "    rows = list(csv.DictReader(f))\n",
        encoding="utf-8",
    )
    failures = [
        "python code/summarize.py -> rc=1\n"
        "FileNotFoundError: CSV file not found: results/significance.csv"
    ]
    issues = find_data_contract_issues(proj, failures)
    sig = [i for i in issues if i.data_file == "results/significance.csv"]
    assert sig, "intermediate file not detected"
    iss = sig[0]
    assert iss.missing_file is True
    assert iss.actual is None  # never written this run
    assert "code/compute_sig.py" in iss.producers  # the script that must write it

    fb = render_data_contract_feedback(issues)
    assert "results/significance.csv" in fb
    assert "MISSING" in fb
    assert "compute_sig.py" in fb        # producer to fix
    assert "CASCADE" in fb               # consumers are cascade victims
    # Producer is a reopen target.
    assert "code/compute_sig.py" in reopen_targets(issues)


def test_keyerror_is_detected_as_required_column(tmp_path) -> None:
    proj = _make_project(tmp_path)
    failures = [
        'File "/runner/code/make_plots.py", line 3\n'
        "    df['rmse']\n"
        "KeyError: 'rmse'"
    ]
    issues = find_data_contract_issues(proj, failures)
    assert issues and "rmse" in issues[0].required
    assert issues[0].actual == ["seed", "model_type", "MAE", "RMSE"]


def test_no_false_positive_without_a_data_error(tmp_path) -> None:
    proj = _make_project(tmp_path)
    # A plain syntax/runtime error with no data-schema signal → no issues.
    failures = ["python code/make_plots.py -> rc=1\nSyntaxError: invalid syntax"]
    assert find_data_contract_issues(proj, failures) == []
    assert render_data_contract_feedback([]) == ""


def test_fstring_placeholder_is_not_a_column(tmp_path) -> None:
    """The traceback carries the SOURCE line ``...columns: {missing}`` alongside the
    resolved set; ``missing`` must NOT be parsed as a column name."""
    proj = _make_project(tmp_path)
    failures = [
        'File "/runner/code/make_plots.py", line 7, in load_metrics\n'
        '    raise ValueError(f"Metrics CSV missing required columns: {missing}")\n'
        "ValueError: Metrics CSV missing required columns: {'mae', 'model', 'rmse'}"
    ]
    issues = find_data_contract_issues(proj, failures)
    assert issues
    assert "missing" not in issues[0].required
    assert set(issues[0].required) == {"mae", "model", "rmse"}


def test_cumulative_ledger_persists_contracts(tmp_path) -> None:
    """Mirror shared_contract anti-thrash: a contract flagged in round N is still
    rendered in round N+1 even if that round's failures don't mention it."""
    proj = _make_project(tmp_path)
    mem = proj / ".specify" / "memory"
    mem.mkdir(parents=True)
    failures = [
        'File "/runner/code/make_plots.py", line 3\n'
        "ValueError: Metrics CSV missing columns: {'rmse', 'model', 'mae'}"
    ]
    round1 = find_data_contract_issues(proj, failures)
    acc1 = accumulate_data_contract_issues(mem, proj, round1)
    assert any(i.data_file == "results/metrics.csv" for i in acc1)
    assert (mem / "data_contract_ledger.json").is_file()

    # Round 2 sees a DIFFERENT, empty failure set — the metrics contract must
    # still be carried forward (not dropped) so the implementer keeps satisfying it.
    acc2 = accumulate_data_contract_issues(mem, proj, [])
    metrics = [i for i in acc2 if i.data_file == "results/metrics.csv"]
    assert metrics, "ledger dropped a previously-seen contract (thrash regression)"
    assert set(metrics[0].required) == {"mae", "rmse", "model"}
    assert metrics[0].actual == ["seed", "model_type", "MAE", "RMSE"]


def test_json_schema_top_level_keys(tmp_path) -> None:
    """Real schema reading also works for a JSON intermediate (top-level keys)."""
    proj = tmp_path / "PROJ-997-x"
    (proj / "code").mkdir(parents=True)
    (proj / "results").mkdir(parents=True)
    (proj / "results" / "attributions.json").write_text(
        json.dumps({"gnn": [1, 2], "rf": [3, 4]}), encoding="utf-8"
    )
    (proj / "code" / "reader.py").write_text(
        "import json\n"
        "d = json.load(open('results/attributions.json'))\n"
        "d['model']\n",
        encoding="utf-8",
    )
    failures = [
        'File "/x/code/reader.py", line 3\nKeyError: \'model\''
    ]
    issues = find_data_contract_issues(proj, failures)
    attr = [i for i in issues if i.data_file == "results/attributions.json"]
    assert attr
    assert attr[0].actual == ["gnn", "rf"]
    assert "model" in attr[0].required


# ---------------------------------------------------------------------------
# VERIFICATION against the REAL PROJ-262 evidence (READ-ONLY; never modifies it).
# Proves the implementer would now SEE the trivial fix it thrashed on for 12 rounds.
# ---------------------------------------------------------------------------
#: The REAL PROJ-262 evidence — its failing run's ``failures``, its analysis code, and
#: the ``results/metrics.csv`` it produced — FROZEN under tests/fixtures/proj262/.
#:
#: This used to read the LIVE project tree and ``state/execution_status/PROJ-262…json``.
#: The pipeline rewrites BOTH on every execution attempt, so the evidence moved
#: underneath the test: PROJ-262's newer failures stopped mentioning ``metrics.csv``
#: and its consumers stopped requiring ``mae/rmse/model``, and the test failed while
#: the detector it guards was perfectly fine. A regression test must not depend on
#: mutable production state. The evidence is unchanged and still REAL (captured
#: verbatim from the failing run at 404a05f434) — it is simply no longer a moving
#: target. Every assertion below is untouched.
_FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"
_PROJ_262 = _FIXTURES / "proj262"
_FAILURES_262 = _FIXTURES / "proj262_execution_failures.json"


@pytest.mark.skipif(
    not (_PROJ_262.is_dir() and _FAILURES_262.is_file()),
    reason="PROJ-262 evidence not present in this checkout",
)
def test_proj262_real_failures_surface_the_metrics_csv_rename() -> None:
    failures = json.loads(_FAILURES_262.read_text(encoding="utf-8"))["failures"]
    issues = find_data_contract_issues(_PROJ_262, failures)

    metrics = [i for i in issues if i.data_file == "results/metrics.csv"]
    assert metrics, "did not detect results/metrics.csv from the real failures"
    iss = metrics[0]
    # The REAL on-disk header (read from the actual committed file).
    assert iss.actual == ["seed", "model_type", "MAE", "RMSE"]
    # The columns the real consumers require.
    assert set(iss.required) == {"mae", "rmse", "model"}
    # The exact rename the implementer must apply in the producer.
    assert iss.rename_map() == {"MAE": "mae", "RMSE": "rmse", "model_type": "model"}
    # The real producer is among the scripts to edit / re-open.
    assert "code/generate_metrics.py" in iss.producers
    assert "code/generate_metrics.py" in reopen_targets(issues)

    fb = render_data_contract_feedback(issues)
    assert "results/metrics.csv" in fb
    assert "[seed, model_type, MAE, RMSE]" in fb       # producer's real header
    assert "[rmse, model, mae]" in fb or "[mae, rmse, model]" in fb \
        or all(c in fb for c in ("mae", "rmse", "model"))
    assert "MAE -> mae" in fb and "RMSE -> rmse" in fb and "model_type -> model" in fb
    assert "generate_metrics.py" in fb

    # The cascade FileNotFoundError on significance.csv is also surfaced.
    sig = [i for i in issues if i.data_file == "results/significance.csv"]
    assert sig and sig[0].missing_file is True
