"""Every suite the repository has must be RUN by a workflow, and gate a merge.

Two coverage holes found 2026-10-10, both of the same shape — a check that
exists but nothing executes:

* **No workflow ran ruff.** 96 errors had accumulated across `src/` and
  `tests/` while every agent linted only its own changed files by hand.
* **No workflow ran `tests/integration`.** That is how the SC-008 README
  regression from #1545 survived: the test asserting it was never executed.

A job that runs but is absent from the gate's `needs` reports a result nobody
acts on, so both the step and its place in the gate are pinned here.
"""

from __future__ import annotations

import subprocess
import sys

import pytest
import yaml

from llmxive.config import repo_root

WORKFLOW = repo_root() / ".github/workflows/llmxive-real-call-tests.yml"


@pytest.fixture(scope="module")
def jobs() -> dict:
    return yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))["jobs"]


def _runs(job: dict) -> list[str]:
    return [str(step.get("run", "")) for step in job.get("steps", [])]


def test_a_workflow_runs_ruff_over_every_linted_tree(jobs):
    commands = [run for job in jobs.values() for run in _runs(job)]
    lint = [c for c in commands if c.strip().startswith("ruff check")]
    assert lint, "no job runs ruff"
    checked = set(lint[0].split()[2:])
    assert {"src", "tests"} <= checked, f"ruff must cover src and tests: {checked}"


def test_lint_runs_before_the_minutes_long_suites(jobs):
    """Seconds of linting must not wait behind seven minutes of tests."""
    runs = _runs(jobs["offline"])
    lint_at = next(i for i, c in enumerate(runs) if c.strip().startswith("ruff check"))
    suite_at = next(i for i, c in enumerate(runs) if c.strip().startswith("pytest"))
    assert lint_at < suite_at


def test_a_job_runs_the_integration_suite(jobs):
    commands = [run for job in jobs.values() for run in _runs(job)]
    assert any("pytest tests/integration" in c for c in commands), (
        "tests/integration is run by no job"
    )


def test_the_integration_job_checks_out_what_that_suite_needs(jobs):
    """It needs /.claude/ and /projects/*/specs/, which the fast gate omits."""
    checkout = next(
        step for step in jobs["integration"]["steps"]
        if "sparse-checkout" in str(step.get("with", {}))
    )
    paths = str(checkout["with"]["sparse-checkout"]).split()
    assert "/.claude/" in paths
    assert "/projects/*/specs/" in paths
    # And the fast gate must NOT have grown them (that is #1557's trimming).
    offline_checkout = next(
        step for step in jobs["offline"]["steps"]
        if "sparse-checkout" in str(step.get("with", {}))
    )
    offline_paths = str(offline_checkout["with"]["sparse-checkout"]).split()
    assert "/projects/*/specs/" not in offline_paths


def test_the_gate_requires_the_integration_job(jobs):
    gate = next(j for j in jobs.values() if "gate" in str(j.get("name", "")).lower())
    assert "integration" in gate["needs"], (
        "a job absent from the gate's needs reports a result nobody acts on"
    )
    enforcement = "\n".join(_runs(gate))
    assert "'integration'" in enforcement, "the gate must assert its result"


def test_the_linted_trees_are_actually_clean():
    """The gate is only worth adding if it passes right now."""
    done = subprocess.run(
        [sys.executable, "-m", "ruff", "check", "--no-cache", "src", "tests", "scripts", "eval"],
        cwd=repo_root(), capture_output=True, text=True, timeout=300,
    )
    assert done.returncode == 0, done.stdout + done.stderr
