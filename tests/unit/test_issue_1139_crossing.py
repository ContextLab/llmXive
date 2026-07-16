"""Issue #1139 — the missing HAPPY-PATH crossing contract.

Round 1's audit noted: "negative-path tests lack end-to-end success contracts
(paper completion, plan-time data provenance, ... transition closure)" and NO
organically-advanced project had ever crossed `in_progress → research_complete`.

This is that missing contract: a CORRECT, CPU-tractable simulation study runs its
real analysis end-to-end, produces real (measured, non-fabricated, non-hollow)
artifacts, passes the backend-independent semantic gate, and `_decide_next_stage`
advances it to RESEARCH_COMPLETE. Real venv + real numpy/scipy, no mocks.

Marked slow (installs numpy+scipy). Run: `pytest -m slow tests/unit/test_issue_1139_crossing.py`.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from llmxive.execution.stage import execute_and_gate
from llmxive.pipeline import graph
from llmxive.state import execution_status as es
from llmxive.state import project as ps
from llmxive.types import Project, Stage


@pytest.mark.slow
def test_correct_simulation_study_crosses_to_research_complete(tmp_path: Path) -> None:
    pid = "PROJ-999-monte-carlo-type-i-error"
    pdir = tmp_path / "projects" / pid
    (pdir / "code").mkdir(parents=True)
    (pdir / "idea").mkdir(parents=True)
    (pdir / "specs" / "001-mc").mkdir(parents=True)
    (tmp_path / "state" / "execution_status").mkdir(parents=True)

    # A genuine simulation-methodology study: F2 authorizes its own data-gen.
    (pdir / "idea" / "idea.md").write_text(
        "# Type I error of the t-test under normality\n"
        "A Monte Carlo simulation study: generate data under the null hypothesis "
        "and estimate the Type I error rate of the two-sample t-test.\n",
        encoding="utf-8",
    )
    # A REAL simulation — the reported rate is MEASURED (counted), not RNG-drawn.
    (pdir / "code" / "main.py").write_text(
        "import json, os\n"
        "import numpy as np\n"
        "from scipy import stats\n"
        "os.makedirs('data/results', exist_ok=True)\n"
        "rng = np.random.default_rng(0)\n"
        "N, iters, alpha = 30, 5000, 0.05\n"
        "false_pos = 0\n"
        "for _ in range(iters):\n"
        "    a = rng.normal(0, 1, N); b = rng.normal(0, 1, N)  # both under the null\n"
        "    _, p = stats.ttest_ind(a, b)\n"
        "    if p < alpha: false_pos += 1\n"
        "rate = false_pos / iters  # MEASURED, not drawn\n"
        "json.dump({'type_i_error_rate': rate, 'iters': iters, 'alpha': alpha},\n"
        "          open('data/results/type1_error.json', 'w'), indent=2)\n"
        "print('measured type-I error rate =', rate)\n",
        encoding="utf-8",
    )
    (pdir / "code" / "requirements.txt").write_text("numpy\nscipy\n", encoding="utf-8")
    (pdir / "specs" / "001-mc" / "quickstart.md").write_text(
        "# Quickstart\n```bash\ncd code\npython main.py\n```\n", encoding="utf-8"
    )
    (pdir / "specs" / "001-mc" / "tasks.md").write_text(
        "- [X] T001 Implement the Monte Carlo simulation in `code/main.py`\n"
        "- [X] T002 Produce `data/results/type1_error.json`\n",
        encoding="utf-8",
    )

    now = datetime.now(UTC)
    proj = Project(
        id=pid, title="MC Type I error", field="statistics",
        current_stage=Stage.IN_PROGRESS, created_at=now, updated_at=now,
        artifact_hashes={}, speckit_research_dir=f"projects/{pid}/specs/001-mc",
    )
    ps.save(proj, repo_root=tmp_path)

    assert es.is_ok(pid, repo_root=tmp_path) is False
    ok = execute_and_gate(pdir, repo_root=tmp_path)
    assert ok is True, "a correct simulation must pass the execution gate"
    assert es.is_ok(pid, repo_root=tmp_path) is True

    rec = es.load(pid, repo_root=tmp_path)
    assert "data/results/type1_error.json" in (rec.get("artifacts") or [])
    assert not rec.get("failures"), "no command should have failed"

    nxt = graph._decide_next_stage(proj, pdir, repo_root=tmp_path)
    assert nxt == Stage.RESEARCH_COMPLETE, (
        f"a correct, gated simulation must cross to research_complete, got {nxt}"
    )
