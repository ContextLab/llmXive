"""A project may not own a platform directory, and a shadow is never evidence.

Reproduces the PROJ-9999 totient canary's step-15 kickback (2026-10-10). A
generated task, `code/run_t004_finalize.py`, was authored to record artifact
hashes "into state/projects/PROJ-9999-totient-canary.yaml". It ran with the
project as its working directory, so the path resolved INSIDE the project:

    projects/PROJ-9999-totient-canary/state/projects/PROJ-9999-totient-canary.yaml

Canonical `state/projects/<id>.yaml` still read `artifact_hashes: {}`. Eight
minutes later the JSON was regenerated, the shadow's hash went stale, and the
verifier — which resolves a task's paths relative to the project — read the
shadow, compared its stale hash to the live file, rejected the task, exhausted
the cap and kicked the project back to `clarified`. Two consecutive runs ended
that way.
"""

from __future__ import annotations

import pytest

from llmxive.agents.task_verifier import (
    _artifact_valid,
    _deterministic_verdict,
    gather_evidence,
)
from llmxive.execution.platform_paths import (
    is_project_dir,
    platform_shadow,
    shadow_dirs,
    shadow_feedback,
)

#: The real shadow path from the canary, plus the other platform roots.
SHADOWS = [
    ("state/projects/PROJ-9999-totient-canary.yaml", "state"),
    ("state/claims/registry.json", "state"),
    (".github/workflows/pages.yml", ".github"),
    ("./state/projects/x.yaml", "state"),
]

#: Paths a research project legitimately owns.
OWNED = [
    "data/totient_tv_results.json",
    "figures/tv_vs_N.png",
    "code/totient_analysis.py",
    "code/test_totient.py",
    "paper/source/main.tex",
    "specs/001-totient-canary/contracts/tv-results.schema.yaml",
    "tests/test_analysis.py",
    "scripts/run.sh",
    "docs/notes.md",
    "requirements.txt",
    # A project legitimately has these; tasks name them relative to `code/`, so
    # treating them as platform-owned broke a real previously-fixed behaviour.
    "src/utils/sieve.py",
    "agents/simulation_agent.py",
    "eval/score.py",
]


@pytest.mark.parametrize("rel,owned", SHADOWS, ids=[s[0] for s in SHADOWS])
def test_platform_roots_are_recognized(rel, owned):
    assert platform_shadow(rel) == owned


@pytest.mark.parametrize("rel", OWNED)
def test_project_owned_paths_are_not_shadows(rel):
    assert platform_shadow(rel) is None


@pytest.mark.parametrize("rel", ["", "   ", ".", "./"])
def test_empty_paths_are_not_shadows(rel):
    assert platform_shadow(rel) is None


def test_the_rule_applies_only_inside_a_project(tmp_path):
    project = tmp_path / "projects" / "PROJ-1-x"
    project.mkdir(parents=True)
    assert is_project_dir(project)
    # The platform's OWN Spec Kit features are verified the same way, and there a
    # task naming src/llmxive/... is entirely legitimate.
    plain = tmp_path / "somewhere" / "else"
    plain.mkdir(parents=True)
    assert not is_project_dir(plain)


def _canary(tmp_path):
    """The canary's exact shape: a real artifact plus a stale state shadow."""
    project = tmp_path / "projects" / "PROJ-9999-totient-canary"
    (project / "data").mkdir(parents=True)
    (project / "data" / "totient_tv_results.json").write_text(
        '{"rows": [{"N": 1000, "p": 7}]}', encoding="utf-8",
    )
    shadow = project / "state" / "projects"
    shadow.mkdir(parents=True)
    (shadow / "PROJ-9999-totient-canary.yaml").write_text(
        "artifact_hashes:\n"
        "  data/totient_tv_results.json: 525a82c9d492b89024997672ba332aaa\n",
        encoding="utf-8",
    )
    return project


def test_a_shadow_is_never_valid_evidence(tmp_path):
    project = _canary(tmp_path)
    assert _artifact_valid(project, "data/totient_tv_results.json") is True
    assert _artifact_valid(project, "state/projects/PROJ-9999-totient-canary.yaml") is False


def test_a_shadow_is_not_quoted_as_evidence(tmp_path):
    project = _canary(tmp_path)
    task = ("T004 Export `data/totient_tv_results.json` and record hashes in "
            "`state/projects/PROJ-9999-totient-canary.yaml`.")
    evidence = gather_evidence(project, task)
    assert "PLATFORM-OWNED PATH" in evidence
    assert "shadows `state/`" in evidence
    # The stale hash must never reach the verifier as a fact about the project.
    assert "525a82c9" not in evidence
    # The real artifact is still quoted.
    assert "totient_tv_results.json" in evidence


def test_a_task_writing_platform_state_is_rejected_with_the_reason(tmp_path):
    project = _canary(tmp_path)
    task = ("T004 Produce `data/totient_tv_results.json` and write artifact "
            "hashes into `state/projects/PROJ-9999-totient-canary.yaml`.")
    verdict, reason = _deterministic_verdict(project, task)
    assert verdict == "reject"
    assert "platform-owned" in reason.lower()
    assert "state/" in reason
    # Actionable, not a bare "missing": it says what to do instead.
    assert "project-owned" in reason.lower()


def test_an_ordinary_task_is_unaffected(tmp_path):
    project = _canary(tmp_path)
    verdict, _reason = _deterministic_verdict(
        project, "T002 Produce `data/totient_tv_results.json` with the census.",
    )
    assert verdict is None, "a project-owned task still goes to the semantic verifier"


def test_a_run_that_left_a_shadow_is_told_about_it(tmp_path):
    project = _canary(tmp_path)
    assert shadow_dirs(project) == ["state"]
    feedback = shadow_feedback(project)
    assert "`state/`" in feedback
    assert "data/" in feedback and "figures/" in feedback
    assert "verification time" in feedback


def test_a_clean_project_gets_no_shadow_feedback(tmp_path):
    project = tmp_path / "projects" / "PROJ-2-y"
    (project / "data").mkdir(parents=True)
    (project / ".specify" / "memory").mkdir(parents=True)
    assert shadow_dirs(project) == []
    assert shadow_feedback(project) == ""


def test_the_execution_feedback_file_carries_the_shadow_section(tmp_path):
    """End to end through the real feedback writer."""
    from llmxive.execution.analysis_runner import AnalysisRunResult
    from llmxive.execution.stage import _write_execution_feedback

    project = _canary(tmp_path)
    mem = project / ".specify" / "memory"
    mem.mkdir(parents=True)
    res = AnalysisRunResult(ok=False, reason="a command failed",
                            declared_missing=[], artifacts_produced=[])
    _write_execution_feedback(mem, res, failures=["python code/x.py -> rc=1\nboom"])
    written = (mem / "execution_feedback.md").read_text(encoding="utf-8")
    assert "Platform-owned paths written inside the project" in written
    assert "`state/`" in written


# --- the authoring prompts must forbid it at the source ------------------

_PROMPTS = __import__("pathlib").Path(__file__).resolve().parents[2] / "agents" / "prompts"


@pytest.mark.parametrize("prompt", ["tasker.md", "paper_tasker.md"])
def test_the_tasker_prompts_forbid_writing_platform_state(prompt):
    """Prevention, not only detection: the task must never be authored.

    The deterministic guard rejects such a task and the run feedback asks for the
    step to be dropped, but on re-plan the tasker would write it again unless the
    authoring contract forbids it.
    """
    text = (_PROMPTS / prompt).read_text(encoding="utf-8").lower()
    assert "project-owned paths" in text
    assert "state/" in text
    assert "verification time" in text


def test_containment_is_reported_before_a_malformed_artifact(tmp_path):
    """Precedence: a shadow is the more fundamental defect.

    `test_yaml_artifact_validation` used to model a project writing
    `state/projects/<id>.yaml` as if that were legitimate, and asserted the
    "invalid YAML" rejection. Both defects are real; the containment one is
    reported, because fixing the YAML would leave the shadow — and the shadow is
    what rejects honest work later.
    """
    project = tmp_path / "projects" / "PROJ-test"
    manifest = project / "state" / "projects" / "PROJ-test.yaml"
    manifest.parent.mkdir(parents=True)
    manifest.write_text("git_commit: abc\\nfiles:\\n  x: y\\n", encoding="utf-8")
    verdict, reason = _deterministic_verdict(
        project, "T001 Generate state/projects/PROJ-test.yaml",
    )
    assert verdict == "reject"
    assert "platform-owned" in reason.lower()
    assert "invalid" not in reason, "the containment defect is the one reported"
