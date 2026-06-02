"""Unit tests for the verified-facts feedback helper (trustworthiness Phase 2).

Covers ``load_verified_facts`` / ``render_verified_facts_block`` plus the
wiring into each generation agent's USER prompt: the specifier, the spec/plan
convergence revisers, and the planner. Deterministic — no model calls.

The single load-bearing fact across these tests is the OEIS-verified prime-knot
count (9988) that the agents must cite instead of re-inventing a fabrication.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from llmxive.claims.verified_facts_prompt import (
    load_verified_facts,
    render_verified_facts_block,
)

_VALUE = "9988"
_SOURCE_ID = "A002863"
_URL = "https://oeis.org/A002863"
_SUBJECT_KEY = "13|crossing knots number prime"

_RECONCILE_INSTRUCTION = "MUST NOT invent a reconciliation"


def _write_facts(project_dir: Path, payload: dict[str, Any]) -> None:
    mem = project_dir / ".specify" / "memory"
    mem.mkdir(parents=True, exist_ok=True)
    (mem / "verified_facts.yaml").write_text(
        yaml.safe_dump(payload, sort_keys=True), encoding="utf-8"
    )


def _one_fact_payload() -> dict[str, Any]:
    # Exactly the shape claims.service._persist_verified_facts writes.
    return {
        _SUBJECT_KEY: {
            "value": _VALUE,
            "source_id": _SOURCE_ID,
            "url": _URL,
            "quote": "... 2176, 9988, 46972 ... (sequence A002863 in the OEIS).",
        }
    }


# --- render_verified_facts_block -------------------------------------------


class TestRenderBlock:
    def test_block_contains_value_source_url_and_instruction(self) -> None:
        facts = load_facts_from_payload(_one_fact_payload())
        block = render_verified_facts_block(facts)
        assert _VALUE in block
        assert _SOURCE_ID in block
        assert _URL in block
        # The anti-rationalization instruction must be present verbatim.
        assert _RECONCILE_INSTRUCTION in block
        # The human-readable subject keywords surface (not the raw '|' key).
        assert "prime" in block and "crossing" in block

    def test_empty_facts_renders_empty_string(self) -> None:
        assert render_verified_facts_block([]) == ""

    def test_multiple_facts_each_rendered(self) -> None:
        payload = _one_fact_payload()
        payload["12|crossing knots number prime"] = {
            "value": "2176",
            "source_id": _SOURCE_ID,
            "url": _URL,
            "quote": "",
        }
        block = render_verified_facts_block(
            load_facts_from_payload(payload)
        )
        assert "9988" in block
        assert "2176" in block


# --- load_verified_facts ----------------------------------------------------


class TestLoadFacts:
    def test_reads_persisted_file(self, tmp_path: Path) -> None:
        _write_facts(tmp_path, _one_fact_payload())
        facts = load_verified_facts(tmp_path)
        assert len(facts) == 1
        fact = facts[0]
        assert fact["value"] == _VALUE
        assert fact["source_id"] == _SOURCE_ID
        assert fact["url"] == _URL
        assert "prime" in fact["subject"]

    def test_missing_file_returns_empty(self, tmp_path: Path) -> None:
        assert load_verified_facts(tmp_path) == []

    def test_none_project_dir_returns_empty(self) -> None:
        assert load_verified_facts(None) == []

    def test_corrupt_file_returns_empty_no_raise(self, tmp_path: Path) -> None:
        mem = tmp_path / ".specify" / "memory"
        mem.mkdir(parents=True, exist_ok=True)
        # Unparseable YAML (unterminated flow mapping).
        (mem / "verified_facts.yaml").write_text(
            "{ this: is: not: valid: yaml ::: [", encoding="utf-8"
        )
        assert load_verified_facts(tmp_path) == []

    def test_non_dict_payload_returns_empty(self, tmp_path: Path) -> None:
        mem = tmp_path / ".specify" / "memory"
        mem.mkdir(parents=True, exist_ok=True)
        (mem / "verified_facts.yaml").write_text(
            "- just\n- a\n- list\n", encoding="utf-8"
        )
        assert load_verified_facts(tmp_path) == []

    def test_entry_without_value_skipped(self, tmp_path: Path) -> None:
        _write_facts(
            tmp_path,
            {"5|some subject": {"source_id": "X", "url": "u", "quote": ""}},
        )
        assert load_verified_facts(tmp_path) == []


def load_facts_from_payload(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Helper: round-trip a payload through load_verified_facts via a temp dir."""
    import tempfile

    with tempfile.TemporaryDirectory() as td:
        proj = Path(td)
        _write_facts(proj, payload)
        return load_verified_facts(proj)


# --- wiring: specifier ------------------------------------------------------


def _make_ctx(project_id: str, project_dir: Path):
    from llmxive.speckit.slash_command import SlashCommandContext
    from llmxive.types import BackendName

    return SlashCommandContext(
        project_id=project_id,
        project_dir=project_dir,
        run_id="r",
        task_id="t",
        inputs=[],
        expected_outputs=[],
        prompt_template_path=project_dir / "x.md",
        default_backend=BackendName.DARTMOUTH,
        fallback_backends=[],
        default_model="m",
        prompt_version="1.0.0",
        agent_name="agent",
    )


def _seed_specify_project(tmp_path: Path, *, with_facts: bool) -> Path:
    proj = tmp_path / "projects" / "PROJ-K"
    (proj / "idea").mkdir(parents=True)
    (proj / "idea" / "idea.md").write_text(
        "# Idea\n\nResearch question: how complex are knot diagrams?\n",
        encoding="utf-8",
    )
    (proj / ".specify" / "templates").mkdir(parents=True)
    (proj / ".specify" / "templates" / "spec-template.md").write_text(
        "# Spec template\n", encoding="utf-8"
    )
    fdir = proj / "specs" / "001-k"
    fdir.mkdir(parents=True)
    if with_facts:
        _write_facts(proj, _one_fact_payload())
    return proj


class TestSpecifierWiring:
    def test_facts_present_block_in_user_prompt(
        self, tmp_path: Path, monkeypatch
    ) -> None:
        import llmxive.speckit.specify_cmd as specify_cmd

        monkeypatch.setattr(
            specify_cmd, "render_prompt", lambda *a, **k: "stub system"
        )
        proj = _seed_specify_project(tmp_path, with_facts=True)
        fdir = proj / "specs" / "001-k"
        ctx = _make_ctx("PROJ-K", proj)
        mech = {
            "BRANCH_NAME": "001-k",
            "FEATURE_NUM": "001",
            "FEATURE_DIR": str(fdir),
        }
        msgs = specify_cmd.SpecifierAgent().build_prompt(ctx, mech)
        user = msgs[-1].content
        assert _VALUE in user
        assert _RECONCILE_INSTRUCTION in user

    def test_no_facts_baseline_unchanged(
        self, tmp_path: Path, monkeypatch
    ) -> None:
        import llmxive.speckit.specify_cmd as specify_cmd

        monkeypatch.setattr(
            specify_cmd, "render_prompt", lambda *a, **k: "stub system"
        )
        proj = _seed_specify_project(tmp_path, with_facts=False)
        fdir = proj / "specs" / "001-k"
        ctx = _make_ctx("PROJ-K", proj)
        mech = {
            "BRANCH_NAME": "001-k",
            "FEATURE_NUM": "001",
            "FEATURE_DIR": str(fdir),
        }
        user = specify_cmd.SpecifierAgent().build_prompt(ctx, mech)[-1].content
        assert "VERIFIED FACTS" not in user
        assert _RECONCILE_INSTRUCTION not in user


# --- wiring: planner --------------------------------------------------------


def _seed_plan_project(tmp_path: Path, *, with_facts: bool) -> Path:
    proj = tmp_path / "projects" / "PROJ-K"
    fdir = proj / "specs" / "001-k"
    fdir.mkdir(parents=True)
    (fdir / "spec.md").write_text("- **FR-001**: do a thing\n", encoding="utf-8")
    (proj / ".specify" / "memory").mkdir(parents=True)
    (proj / ".specify" / "memory" / "constitution.md").write_text(
        "# C\n", encoding="utf-8"
    )
    (proj / ".specify" / "templates").mkdir(parents=True)
    (proj / ".specify" / "templates" / "plan-template.md").write_text(
        "# Plan template\n", encoding="utf-8"
    )
    if with_facts:
        _write_facts(proj, _one_fact_payload())
    return proj


class TestPlannerWiring:
    def test_facts_present_block_in_user_prompt(
        self, tmp_path: Path, monkeypatch
    ) -> None:
        import llmxive.speckit.plan_cmd as plan_cmd

        monkeypatch.setattr(
            plan_cmd, "render_prompt", lambda *a, **k: "stub system"
        )
        # Avoid any network in the dataset resolver.
        monkeypatch.setattr(
            plan_cmd, "resolve_datasets", lambda *a, **k: None
        )
        monkeypatch.setattr(
            plan_cmd, "render_planner_block", lambda *a, **k: ""
        )
        proj = _seed_plan_project(tmp_path, with_facts=True)
        fdir = proj / "specs" / "001-k"
        ctx = _make_ctx("PROJ-K", proj)
        mech = {
            "feature_dir": str(fdir),
            "spec_path": str(fdir / "spec.md"),
            "dataset_block": "",
        }
        user = plan_cmd.PlannerAgent().build_prompt(ctx, mech)[-1].content
        assert _VALUE in user
        assert _RECONCILE_INSTRUCTION in user

    def test_no_facts_baseline_unchanged(
        self, tmp_path: Path, monkeypatch
    ) -> None:
        import llmxive.speckit.plan_cmd as plan_cmd

        monkeypatch.setattr(
            plan_cmd, "render_prompt", lambda *a, **k: "stub system"
        )
        monkeypatch.setattr(
            plan_cmd, "resolve_datasets", lambda *a, **k: None
        )
        monkeypatch.setattr(
            plan_cmd, "render_planner_block", lambda *a, **k: ""
        )
        proj = _seed_plan_project(tmp_path, with_facts=False)
        fdir = proj / "specs" / "001-k"
        ctx = _make_ctx("PROJ-K", proj)
        mech = {
            "feature_dir": str(fdir),
            "spec_path": str(fdir / "spec.md"),
            "dataset_block": "",
        }
        user = plan_cmd.PlannerAgent().build_prompt(ctx, mech)[-1].content
        assert "VERIFIED FACTS" not in user
        assert _RECONCILE_INSTRUCTION not in user


# --- wiring: spec reviser ---------------------------------------------------

_REPO_ROOT = Path(__file__).resolve().parents[2]


def _seed_reviser_repo(tmp_path: Path, *, with_facts: bool) -> Path:
    """Build a tmp repo root that resolves BOTH the real prompt templates
    (via a symlink to the source ``agents/`` dir) AND a seeded project dir,
    mirroring production where ``repo_root`` holds both. Returns the repo root.
    """
    repo = tmp_path / "repo"
    repo.mkdir()
    # Real prompt templates so render_prompt resolves without a model call.
    (repo / "agents").symlink_to(_REPO_ROOT / "agents")
    proj = repo / "projects" / "PROJ-K"
    proj.mkdir(parents=True)
    if with_facts:
        _write_facts(proj, _one_fact_payload())
    return repo


class TestSpecReviserWiring:
    def _build_messages(self, repo_root: Path):
        from llmxive.convergence.revisers.spec_reviser import (
            SpecReviser,
            _SpecBundle,
        )

        reviser = SpecReviser(
            backend=object(),
            repo_root=repo_root,
            project_id="PROJ-K",
        )
        bundle = _SpecBundle(
            spec_md="# Spec\n- FR-001: count prime knots.\n",
            idea_md="",
            comments_block="",
            spec_template="",
        )
        return reviser._build_messages(
            bundle, [], "projects/PROJ-K/specs/001-k/spec.md"
        )

    def test_facts_present_block_in_user_message(self, tmp_path: Path) -> None:
        repo = _seed_reviser_repo(tmp_path, with_facts=True)
        msgs = self._build_messages(repo)
        user = msgs[-1].content
        assert _VALUE in user
        assert _RECONCILE_INSTRUCTION in user

    def test_no_facts_baseline_unchanged(self, tmp_path: Path) -> None:
        repo = _seed_reviser_repo(tmp_path, with_facts=False)
        user = self._build_messages(repo)[-1].content
        assert "VERIFIED FACTS" not in user
        assert _RECONCILE_INSTRUCTION not in user


class TestPlanReviserWiring:
    def _build_messages(self, repo_root: Path):
        from llmxive.convergence.revisers.plan_reviser import PlanReviser

        reviser = PlanReviser(
            backend=object(),
            repo_root=repo_root,
            project_id="PROJ-K",
        )
        return reviser._build_messages(
            plan_artifacts={
                "projects/PROJ-K/specs/001-k/plan.md": "# Plan\n- count prime knots.\n"
            },
            source_spec="# Spec\n- FR-001: count prime knots.\n",
            constitution="# C\n",
            comments_block="",
            concerns=[],
        )

    def test_facts_present_block_in_user_message(self, tmp_path: Path) -> None:
        repo = _seed_reviser_repo(tmp_path, with_facts=True)
        user = self._build_messages(repo)[-1].content
        assert _VALUE in user
        assert _RECONCILE_INSTRUCTION in user

    def test_no_facts_baseline_unchanged(self, tmp_path: Path) -> None:
        repo = _seed_reviser_repo(tmp_path, with_facts=False)
        user = self._build_messages(repo)[-1].content
        assert "VERIFIED FACTS" not in user
        assert _RECONCILE_INSTRUCTION not in user
