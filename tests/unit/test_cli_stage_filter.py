"""`--stage` takes a pipeline Stage value (project STATE), not a step name.

A manual ``workflow_dispatch`` that picked a step-name from the old dropdown
(e.g. ``speckit_implement``) hard-failed with a bare ``invalid --stage`` + exit 2
and no hint about what IS accepted — because the CLI validates ``--stage`` against
the ``Stage`` enum (project states), a different vocabulary from the step names the
dropdown offered. The error is now actionable (it lists every accepted Stage), and
the workflow input is free-text Stage rather than a step-name dropdown.
"""
from __future__ import annotations

from types import SimpleNamespace

import yaml

from llmxive.cli import _cmd_run
from llmxive.config import repo_root
from llmxive.types import Stage


def _args(stage: str) -> SimpleNamespace:
    return SimpleNamespace(agent=None, stage=stage, project=None, max_tasks=1)


def test_invalid_stage_error_lists_accepted_stage_values(capsys):
    rc = _cmd_run(_args("speckit_implement"))
    assert rc == 2
    err = capsys.readouterr().err
    assert "invalid --stage 'speckit_implement'" in err
    # The hint must name the REAL accepted values so a maintainer can self-correct.
    for s in (Stage.IN_PROGRESS, Stage.RESEARCH_REVIEW, Stage.PAPER_DRAFTING_INIT):
        assert s.value in err


def test_pipeline_workflow_stage_input_is_freetext_stage_not_step_dropdown():
    wf = repo_root() / ".github" / "workflows" / "llmxive-pipeline.yml"
    d = yaml.safe_load(wf.read_text(encoding="utf-8"))
    # PyYAML parses the bare ``on:`` key as the boolean True (YAML 1.1 truthy word).
    stage = d[True]["workflow_dispatch"]["inputs"]["stage"]
    assert stage["type"] == "string"
    # No step-name dropdown that would feed the CLI an invalid --stage value.
    assert "options" not in stage
