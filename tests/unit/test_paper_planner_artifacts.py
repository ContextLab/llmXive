"""Real paper paths must hold the reviewed plan and survive rejected retries."""

import json
import shutil
import subprocess
from datetime import UTC, datetime
from pathlib import Path

import pytest

from llmxive.backends.base import ChatResponse
from llmxive.speckit._research_guard import IncompleteArtifactSet, InconsistentDataModel
from llmxive.speckit.paper_plan_cmd import PaperPlannerAgent
from llmxive.state import project as store
from llmxive.types import Project, Stage
from tests.unit.test_plan_revision_loop import (
    _BAD_CONTRACT_MULTI_DOC,
    _FakeBackend,
    _make_planner_ctx,
    _valid_five_file_block,
)


def paper_context(tmp_path):
    ctx, _, old = _make_planner_ctx(tmp_path)
    ctx.project_id = "PROJ-901-paper-plan"
    feature = ctx.project_dir / "paper/specs/001-paper"
    feature.mkdir(parents=True)
    shutil.copyfile(old / "spec.md", feature / "spec.md")
    root = Path(__file__).resolve().parents[2]
    shutil.copytree(root / ".specify", ctx.project_dir / "paper/.specify")
    mech = {"feature_dir": str(feature), "spec_path": str(feature / "spec.md")}
    return ctx, mech, feature


@pytest.mark.parametrize("metadata", ["missing", "stale", "ambiguous"])
def test_paper_setup_uses_stored_feature_and_keeps_other_plans(tmp_path, metadata):
    ctx, _, feature = paper_context(tmp_path)
    subprocess.run(["git", "init", "-q", "-b", "main", str(tmp_path)], check=True)
    now = datetime.now(UTC)
    store.save(
        Project(
            id=ctx.project_id,
            title="paper",
            field="mathematics",
            current_stage=Stage.PAPER_CLARIFIED,
            created_at=now,
            updated_at=now,
            speckit_paper_dir=str(feature.relative_to(tmp_path)),
        ),
        repo_root=tmp_path,
    )
    other = feature.parent / (
        "001-duplicate" if metadata == "ambiguous" else "999-stale"
    )
    other.mkdir()
    (other / "plan.md").write_text("Other plan remains intact\n")
    if metadata == "stale":
        (ctx.project_dir / "paper/.specify/feature.json").write_text(
            json.dumps({"feature_directory": str(other)})
        )
    agent = PaperPlannerAgent()
    output = agent.mechanical_step(ctx)
    assert Path(output["script_result"]["SPECS_DIR"]).resolve() == feature.resolve()
    original = "# Existing paper plan\nUse validated figures and retain the finite-range limitation.\n"
    (feature / "plan.md").write_text(original)
    (feature / "quickstart.md").write_text("latexmk -pdf main.tex\n")
    output = agent.mechanical_step(ctx)
    assert (feature / "plan.md").read_text() == original
    assert (other / "plan.md").read_text() == "Other plan remains intact\n"
    prompt = agent.build_prompt(ctx, output)[-1].content
    assert original in prompt
    assert "latexmk -pdf main.tex" in prompt
    assert agent.claim_stage_label() is None  # paper claims retain full verification


def test_nested_model_feature_is_refused_before_any_write(tmp_path, monkeypatch):
    ctx, mech, feature = paper_context(tmp_path)
    monkeypatch.setattr("llmxive.backends.router.make_backend", lambda _: None)
    monkeypatch.setattr(PaperPlannerAgent, "_run_paper_plan_panel", lambda *args: None)
    response = _valid_five_file_block().replace(
        "FILE: ", "FILE: specs/002-invented-paper/"
    )
    with pytest.raises(IncompleteArtifactSet):
        PaperPlannerAgent().write_artifacts(
            ctx, mech, ChatResponse(text=response, model="m", backend="dartmouth")
        )
    assert not (feature / "specs").exists()
    assert not (feature / "plan.md").exists()


def test_rejected_paper_revision_restores_previous_bytes(tmp_path, monkeypatch):
    ctx, mech, feature = paper_context(tmp_path)
    monkeypatch.setattr("llmxive.backends.router.make_backend", lambda _: None)
    monkeypatch.setattr(PaperPlannerAgent, "_run_paper_plan_panel", lambda *args: None)
    prior = {
        "plan.md": b"Previous scientifically reviewed plan\n",
        "contracts/clone-cluster.schema.yaml": b"title: Previous\n",
    }
    for rel, data in prior.items():
        p = feature / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)
    with pytest.raises(InconsistentDataModel):
        PaperPlannerAgent().write_artifacts(
            ctx,
            mech,
            ChatResponse(
                text=_valid_five_file_block(bad_contract=_BAD_CONTRACT_MULTI_DOC),
                model="m",
                backend="dartmouth",
            ),
        )
    for rel, data in prior.items():
        assert (feature / rel).read_bytes() == data
    assert not (feature / "research.md").exists()


def test_paper_retry_corrects_paths_then_reviews_canonical_artifacts(
    tmp_path, monkeypatch
):
    ctx, mech, feature = paper_context(tmp_path)
    backend = _FakeBackend([_valid_five_file_block()])
    monkeypatch.setattr("llmxive.backends.router.make_backend", lambda _: backend)
    reviewed = []

    def panel(self, ctx, feature, repo):
        reviewed.append(feature)
        assert (feature / "plan.md").read_text().startswith("# Implementation Plan:")
        assert (feature / "contracts/clone-cluster.schema.yaml").is_file()

    monkeypatch.setattr(PaperPlannerAgent, "_run_paper_plan_panel", panel)
    response = _valid_five_file_block().replace(
        "FILE: ", "FILE: specs/002-invented-paper/"
    )
    outputs = PaperPlannerAgent().write_artifacts(
        ctx, mech, ChatResponse(text=response, model="m", backend="dartmouth")
    )
    assert len(backend.calls) == 1
    assert "IncompleteArtifactSet" in backend.calls[0]["messages"][-1].content
    assert reviewed == [feature]
    assert len(outputs) == 6
    assert not (feature / "specs").exists()


@pytest.mark.parametrize("escape", ["../../outside.md", "absolute"])
def test_paper_artifact_escape_is_refused_and_existing_bytes_restored(
    tmp_path, monkeypatch, escape
):
    ctx, mech, feature = paper_context(tmp_path)
    monkeypatch.setattr("llmxive.backends.router.make_backend", lambda _: None)
    monkeypatch.setattr(PaperPlannerAgent, "_run_paper_plan_panel", lambda *args: None)
    (feature / "plan.md").write_bytes(b"Preserved original\n")
    if escape == "absolute":
        escape = str(tmp_path / "outside.md")
    response = (
        _valid_five_file_block() + f"\n<!-- FILE: {escape} -->\nEscaped document\n"
    )
    with pytest.raises(ValueError):
        PaperPlannerAgent().write_artifacts(
            ctx, mech, ChatResponse(text=response, model="m", backend="dartmouth")
        )
    assert (feature / "plan.md").read_bytes() == b"Preserved original\n"
