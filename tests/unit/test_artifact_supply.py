"""Spec-015 production bug fix: panels were emitting "X not provided"
concerns because the engine was supplied only the primary artifact,
not the sentinel ``__X__`` keys each reviser reads via
``artifacts.get("__X__", "")``.

These tests pin the contract three ways:

1. **Engine-bridge fail-loud (FR-049)** —
   :func:`llmxive.convergence.project_runner.run_engine_for_project`
   MUST raise ``ValueError`` when called with ``require_full_extra_inputs``
   True and a stage's required sentinel keys are missing from
   ``extra_inputs``. The error message MUST name the missing keys and
   the stage.

2. **Calibration runner** — the spec-015 calibration harness
   (``scripts/run_calibration.py``) MUST build an artifacts dict that
   contains every sentinel key the stage's reviser reads, so the
   calibration panel sees coherent upstream context rather than
   reporting "spec.md not provided" on every entry (the symptom that
   surfaced this bug).

3. **Paper-implement production path** —
   :class:`llmxive.speckit.paper_implement_cmd.PaperImplementerAgent`
   MUST load the real on-disk paper artifacts (paper spec/plan/tasks,
   results.md, constitution.md) and forward them as the sentinel
   ``__X__`` keys the :class:`PaperImplementReviser` consults.

The supply contract lives in
:data:`llmxive.convergence.project_runner._REQUIRED_EXTRA_INPUTS_PER_STAGE`
— these tests reference that table to stay in sync with the source of
truth.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from llmxive.convergence.project_runner import (
    _REQUIRED_EXTRA_INPUTS_PER_STAGE,
    run_engine_for_project,
)
from llmxive.convergence.types import ReviewSpec


def _make_stub_spec(stage: str) -> ReviewSpec:
    """Build a minimal ReviewSpec for testing the fail-loud guard.

    The guard runs BEFORE the engine, so the spec doesn't need real
    reviewers/reviser — only ``stage`` + ``exempt=False``."""
    return ReviewSpec(
        stage=stage,
        artifacts=[],
        reviewers=[],
        reviser=None,
        kickback_routing={},
        overflow_goal="extract every constraint",
        advance_stage="next",
        constitution_input=True,
        max_rounds=3,
    )


# --- Contract: required sentinel keys per stage --------------------------


def test_required_extra_inputs_table_covers_every_reviewable_stage() -> None:
    """The contract table MUST mention every stage that has a reviser.

    If a new stage is added without an entry in the table the engine
    silently won't enforce the fail-loud check for it — which is the
    very bug the table exists to prevent."""
    expected_stages = {
        "clarified", "planned", "tasked", "research_review",
        "paper_clarified", "paper_planned", "paper_tasked", "paper_review",
    }
    assert set(_REQUIRED_EXTRA_INPUTS_PER_STAGE) == expected_stages


def test_required_keys_for_tasked_stage_match_tasks_reviser_contract() -> None:
    """The 'tasked' stage's required keys MUST match what TasksReviser
    actually reads via ``artifacts.get("__X__", "")`` (see
    ``llmxive.convergence.revisers.tasks_reviser``)."""
    expected = {
        "__analyze_report__", "__prior_reviews__", "__constitution__",
        "__comments_block__", "__spec_md__", "__plan_md__",
    }
    assert _REQUIRED_EXTRA_INPUTS_PER_STAGE["tasked"] == expected


def test_required_keys_for_paper_review_match_paper_implement_reviser() -> None:
    """The 'paper_review' stage's required keys MUST match what
    PaperImplementReviser reads (see
    ``llmxive.convergence.revisers.paper_implement_reviser``)."""
    expected = {
        "__paper_spec_md__", "__paper_plan_md__", "__results_md__",
        "__tasks_md__", "__constitution__", "__comments_block__",
    }
    assert _REQUIRED_EXTRA_INPUTS_PER_STAGE["paper_review"] == expected


# --- Engine bridge fail-loud check ---------------------------------------


def test_run_engine_for_project_raises_when_required_keys_missing(
    tmp_path: Path,
) -> None:
    """FR-049 fail-loud: missing sentinel keys MUST raise ValueError.

    The error message MUST name the missing keys (so the operator can
    fix the call site) and the stage (so the operator can look up the
    contract)."""
    spec = _make_stub_spec("tasked")
    with pytest.raises(ValueError) as exc_info:
        run_engine_for_project(
            spec=spec,
            artifact_paths={},
            extra_inputs={"__constitution__": "C"},  # missing 5 others
            repo_root=tmp_path,
        )
    msg = str(exc_info.value)
    assert "tasked" in msg
    # Every missing key MUST be named so the operator knows what to add.
    for key in (
        "__analyze_report__", "__prior_reviews__",
        "__comments_block__", "__spec_md__", "__plan_md__",
    ):
        assert key in msg


def test_run_engine_for_project_accepts_when_all_keys_present_even_empty(
    tmp_path: Path,
) -> None:
    """Empty string is OK — the reviser handles ``""`` gracefully.

    What MUST NOT be OK is a silently-missing key (the reviser's
    ``artifacts.get("__X__", "")`` fallback would mask the absence,
    and the panel emits "X not provided" concerns)."""
    spec = _make_stub_spec("planned")
    extras = {
        "__constitution__": "",
        "__comments_block__": "",
        "__spec_md__": "",
    }
    # The fail-loud guard MUST NOT raise. We then bail before the
    # actual engine call by checking that the function got past the
    # guard — easiest signal is that it tries to call run_convergence
    # on a spec with no reviser, which raises a DIFFERENT error from
    # inside the engine, not the ValueError our guard raises.
    with pytest.raises(Exception) as exc_info:
        run_engine_for_project(
            spec=spec,
            artifact_paths={},
            extra_inputs=extras,
            repo_root=tmp_path,
        )
    msg = str(exc_info.value)
    # The guard's error message MUST NOT have fired.
    assert "requires sentinel keys" not in msg


def test_run_engine_for_project_constitution_kwarg_backfills_extra_inputs(
    tmp_path: Path,
) -> None:
    """When ``constitution=`` is passed but ``__constitution__`` isn't in
    extra_inputs, the kwarg MUST backfill the key. This matters because
    the calibration harness loads the constitution from disk and forwards
    it via the kwarg — without the backfill, the fail-loud guard would
    reject it even though the operator did supply the constitution."""
    spec = _make_stub_spec("planned")
    # __constitution__ is INTENTIONALLY omitted from extras — the
    # kwarg should backfill it.
    extras = {"__comments_block__": "", "__spec_md__": ""}
    with pytest.raises(Exception) as exc_info:
        run_engine_for_project(
            spec=spec,
            artifact_paths={},
            extra_inputs=extras,
            repo_root=tmp_path,
            constitution="Principle V: real-call testing.",
        )
    # The guard's error message MUST NOT have fired (constitution
    # was supplied via kwarg).
    assert "requires sentinel keys" not in str(exc_info.value)


def test_run_engine_for_project_opt_out_with_require_full_extra_inputs_false(
    tmp_path: Path,
) -> None:
    """Tests that legitimately exercise a partial fixture (e.g. only
    the project_runner mechanics, not the reviser's full contract)
    can opt out via ``require_full_extra_inputs=False``."""
    spec = _make_stub_spec("tasked")
    # No extras at all — opt-out path MUST NOT raise the guard's
    # ValueError. It will fail later for a different reason (no
    # reviser on the spec), but that's not what we're testing.
    with pytest.raises(Exception) as exc_info:
        run_engine_for_project(
            spec=spec,
            artifact_paths={},
            extra_inputs=None,
            repo_root=tmp_path,
            require_full_extra_inputs=False,
        )
    assert "requires sentinel keys" not in str(exc_info.value)


# --- Calibration runner artifact dict ------------------------------------


def test_calibration_runner_supports_every_stage_artifact_dict() -> None:
    """The calibration runner's _supporting_artifacts_for_stage helper
    MUST return a dict containing every sentinel key the stage's
    reviser reads, for every stage the runner exposes.

    Without this the calibration panels emit "X not provided" concerns
    that look like real findings — the spec-015 calibration repro
    symptom."""
    import importlib.util
    import sys
    spec = importlib.util.spec_from_file_location(
        "run_calibration_mod",
        Path(__file__).resolve().parents[2] / "scripts" / "run_calibration.py",
    )
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    # @dataclass needs the module registered in sys.modules so it can
    # resolve forward references on the class body.
    sys.modules["run_calibration_mod"] = mod
    try:
        spec.loader.exec_module(mod)
    finally:
        sys.modules.pop("run_calibration_mod", None)

    # Stage name in the runner → ReviewSpec.stage in the engine contract.
    # The runner uses friendly names ('spec' / 'plan' / 'tasks') while
    # the contract table uses engine stage names ('clarified' / 'planned'
    # / 'tasked'). This mapping mirrors what build_*_reviewspec does.
    stage_map = {
        "spec": "clarified",
        "plan": "planned",
        "tasks": "tasked",
        "paper_spec": "paper_clarified",
        "paper_plan": "paper_planned",
        "paper_tasks": "paper_tasked",
        "paper_implement": "paper_review",
    }
    for runner_stage, engine_stage in stage_map.items():
        extras = mod._supporting_artifacts_for_stage(runner_stage)
        required = _REQUIRED_EXTRA_INPUTS_PER_STAGE[engine_stage]
        missing = required - set(extras)
        assert not missing, (
            f"calibration runner _supporting_artifacts_for_stage({runner_stage!r}) "
            f"missing required keys {missing!r} for engine stage {engine_stage!r}"
        )


def test_calibration_runner_constitution_loaded_for_every_stage() -> None:
    """Every stage's supporting-artifacts dict MUST include
    ``__constitution__`` — otherwise plan/tasks/research/paper panels
    can't honor Principle V (real-call testing) constitution checks
    during calibration."""
    import importlib.util
    import sys
    spec = importlib.util.spec_from_file_location(
        "run_calibration_mod",
        Path(__file__).resolve().parents[2] / "scripts" / "run_calibration.py",
    )
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    # @dataclass needs the module registered in sys.modules so it can
    # resolve forward references on the class body.
    sys.modules["run_calibration_mod"] = mod
    try:
        spec.loader.exec_module(mod)
    finally:
        sys.modules.pop("run_calibration_mod", None)
    for stage in ("spec", "plan", "tasks", "paper_spec",
                  "paper_plan", "paper_tasks", "paper_implement"):
        extras = mod._supporting_artifacts_for_stage(stage)
        assert "__constitution__" in extras, (
            f"stage {stage!r} missing __constitution__ key"
        )


# --- Paper-implement production path -------------------------------------


def test_paper_implementer_gathers_extras_with_every_contract_key(
    tmp_path: Path,
) -> None:
    """``PaperImplementerAgent._gather_paper_extras`` MUST return a
    dict containing every key in
    :data:`_REQUIRED_EXTRA_INPUTS_PER_STAGE['paper_review']`,
    even when the underlying files don't exist.

    This is the production-path fix: previously the agent only loaded
    .tex files via ``_gather_paper_artifacts`` and never supplied the
    sentinel ``__X__`` keys, causing the 12-panel to emit
    'paper spec.md not provided' / 'constitution.md not provided'
    concerns on every paper-implement run."""
    from llmxive.speckit.paper_implement_cmd import (
        _PAPER_IMPLEMENT_EXTRA_KEYS,
        PaperImplementerAgent,
    )

    # Build a fake project layout. None of the upstream files exist
    # — the test is that _gather_paper_extras ALWAYS returns every
    # contract key (empty string for missing files).
    project_dir = tmp_path / "projects" / "PROJ-000-test"
    feature_dir = project_dir / "paper" / "specs" / "000-test"
    feature_dir.mkdir(parents=True)

    agent = PaperImplementerAgent()
    extras = agent._gather_paper_extras(project_dir, feature_dir)

    # Every contract key MUST be present.
    required = _REQUIRED_EXTRA_INPUTS_PER_STAGE["paper_review"]
    assert set(extras) == required
    # And the local SSoT constant MUST mirror the engine contract.
    assert set(_PAPER_IMPLEMENT_EXTRA_KEYS) == required
    # Every value is a string (no None — fail-loud needs explicit empty).
    for k, v in extras.items():
        assert isinstance(v, str), f"key {k} not a string: {v!r}"


def test_paper_implementer_extras_load_real_files_when_present(
    tmp_path: Path,
) -> None:
    """When the upstream files exist on disk, their content MUST be
    loaded into the corresponding sentinel keys (no silent skip)."""
    from llmxive.speckit.paper_implement_cmd import PaperImplementerAgent

    project_dir = tmp_path / "projects" / "PROJ-001-real"
    paper_dir = project_dir / "paper"
    feature_dir = paper_dir / "specs" / "000-real"
    feature_dir.mkdir(parents=True)
    # Production reads constitution from project_dir/.specify/memory/
    # (per the speckit convention) — NOT under paper_dir. Create the
    # correct parent so the test's write_text() works.
    (project_dir / ".specify" / "memory").mkdir(parents=True)

    # Write real file content for each upstream artifact.
    (feature_dir / "spec.md").write_text("# real paper spec\n")
    (feature_dir / "plan.md").write_text("# real paper plan\n")
    (feature_dir / "tasks.md").write_text("# real paper tasks\n")
    (paper_dir / "results.md").write_text("# real results\n")
    (project_dir / ".specify" / "memory" / "constitution.md").write_text(
        "Principle V: real-call testing.\n",
    )

    agent = PaperImplementerAgent()
    extras = agent._gather_paper_extras(project_dir, feature_dir)

    assert extras["__paper_spec_md__"] == "# real paper spec\n"
    assert extras["__paper_plan_md__"] == "# real paper plan\n"
    assert extras["__tasks_md__"] == "# real paper tasks\n"
    assert extras["__results_md__"] == "# real results\n"
    assert extras["__constitution__"] == "Principle V: real-call testing.\n"
    assert extras["__comments_block__"] == ""  # legitimately empty
