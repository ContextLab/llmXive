"""No pipeline lane may clone the repository's whole history.

`fetch-depth: 0` on a ~9 GB repository with 14k commits eats a lane's budget
before it does any work. The personality lane had it, and the 2026-10-09 audit
recorded run 37957247536 spending its entire 15-minute cap on the clone. Every
ordinary lane (maintenance, submission-intake, paper-compile) uses depth 1, and
the shared commit helper fetches newer main itself before its rebase-retry.
"""

from __future__ import annotations

import yaml

from llmxive.config import repo_root

WORKFLOWS = repo_root() / ".github" / "workflows"


def _checkout_steps():
    for path in sorted(WORKFLOWS.glob("*.yml")):
        workflow = yaml.safe_load(path.read_text(encoding="utf-8"))
        for job_name, job in (workflow.get("jobs") or {}).items():
            for step in job.get("steps", []):
                if str(step.get("uses", "")).startswith("actions/checkout"):
                    yield path.name, job_name, (step.get("with") or {})


def test_no_lane_clones_full_history():
    offenders = [
        f"{name}:{job}"
        for name, job, options in _checkout_steps()
        if options.get("fetch-depth") is not None and int(options["fetch-depth"]) == 0
    ]
    assert not offenders, f"full-history checkout(s): {offenders}"


def test_the_personality_lane_checks_out_shallow():
    """The lane the audit caught, named explicitly so a revert is visible."""
    depths = [
        options.get("fetch-depth")
        for name, _job, options in _checkout_steps()
        if name == "pipeline-personality.yml"
    ]
    assert depths, "pipeline-personality.yml has no checkout step"
    assert all(d is not None and int(d) == 1 for d in depths), depths
