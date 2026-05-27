"""Task 7 (dataset-resolver): the Planner prompt cites ONLY verified URLs.

Offline + deterministic: the network-hitting ``resolve_datasets`` is stubbed
with ``monkeypatch`` to a fixed ``ResolvedDatasets``, so this test asserts the
wiring (block rendered into the user message) without any real network call.
"""
from __future__ import annotations


def test_build_prompt_injects_verified_datasets(tmp_path, monkeypatch):
    import llmxive.speckit.plan_cmd as plan_cmd
    from llmxive.librarian.dataset_resolver import ResolvedDatasets, ResolvedIntent

    fake = ResolvedDatasets(datasets=[ResolvedIntent(
        "QM9", "verified",
        candidates=[{"url": "https://huggingface.co/datasets/qm9", "source": "huggingface",
                     "format": "parquet", "relevance": 0.9,
                     "sample_check": {"downloaded_bytes": 10, "parsed": True}}],
        candidates_tried=[])])
    monkeypatch.setattr(plan_cmd, "resolve_datasets", lambda *a, **k: fake)
    # The system prompt is irrelevant here (we assert on the user message only),
    # and the real planner.md lives in the source repo, not under tmp_path's
    # synthetic repo root — stub it like the phase4 planner tests do.
    monkeypatch.setattr(plan_cmd, "render_prompt", lambda *a, **k: "stub system prompt")

    proj = tmp_path / "projects" / "PROJ-X"
    fdir = proj / "specs" / "001-x"
    fdir.mkdir(parents=True)
    (fdir / "spec.md").write_text("- **FR-001**: download the QM9 dataset (DOI: 10.1038/sdata.2014.22)\n")
    (proj / ".specify" / "memory").mkdir(parents=True)
    (proj / ".specify" / "memory" / "constitution.md").write_text("# C\n")
    (proj / ".specify" / "templates").mkdir(parents=True)
    (proj / ".specify" / "templates" / "plan-template.md").write_text("# Plan template\n")

    from llmxive.speckit.slash_command import SlashCommandContext
    from llmxive.types import BackendName
    ctx = SlashCommandContext(project_id="PROJ-X", project_dir=proj, run_id="r", task_id="t",
        inputs=[], expected_outputs=[], prompt_template_path=tmp_path / "x.md",
        default_backend=BackendName.DARTMOUTH, fallback_backends=[], default_model="m",
        prompt_version="1.0.0", agent_name="planner")
    mech = {"feature_dir": str(fdir), "spec_path": str(fdir / "spec.md")}

    msgs = plan_cmd.PlannerAgent().build_prompt(ctx, mech)
    user = msgs[-1].content
    assert "Verified datasets" in user
    assert "https://huggingface.co/datasets/qm9" in user
