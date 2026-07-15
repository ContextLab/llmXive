"""D11 — the planner runs PROACTIVE strong discovery at plan time.

Locks ``plan_cmd.PlannerAgent.mechanical_step``: it invokes the same
records+field HARD-verifier the execution stage uses (``discover_data_source``
via ``ensure_discovered_source``), sharing the SAME on-disk cache
(``.specify/memory/discovered_data_source.yaml``), and surfaces the verified
source to the planner prompt — instead of only the weak reachability resolver.
It degrades gracefully offline (never crashes a plan run) and writes no dead
weak-manifest.

Only the discovery + LLM-distill boundaries and the setup-plan script runner are
stubbed; the wiring under test (shared cache, block rendering) runs for real.
"""
from __future__ import annotations

from pathlib import Path

import yaml

import llmxive.execution.data_source as ds
import llmxive.librarian.data_source_discovery as dsd
import llmxive.speckit.plan_cmd as plan_cmd
from llmxive.librarian.data_source_discovery import VerifiedSource
from llmxive.librarian.dataset_resolver import ResolvedDatasets
from llmxive.speckit.plan_cmd import PlannerAgent
from llmxive.speckit.slash_command import SlashCommandContext
from llmxive.types import BackendName


def _make_ctx(project_id: str, proj: Path, tmp_path: Path) -> SlashCommandContext:
    return SlashCommandContext(
        project_id=project_id, project_dir=proj, run_id="r", task_id="t",
        inputs=[], expected_outputs=[], prompt_template_path=tmp_path / "x.md",
        default_backend=BackendName.DARTMOUTH, fallback_backends=[],
        default_model="m", prompt_version="1.0.0", agent_name="planner",
    )


def test_mechanical_step_uses_strong_discovery_and_shares_cache(tmp_path, monkeypatch):
    proj = tmp_path / "projects" / "PROJ-STRONG"
    fdir = proj / "specs" / "001-x"
    fdir.mkdir(parents=True)
    (fdir / "spec.md").write_text("- **FR-001**: load the KnotInfo dataset\n")

    monkeypatch.setattr(PlannerAgent, "_feature_dir", lambda self, ctx: fdir)
    monkeypatch.setattr(plan_cmd, "run_script", lambda *a, **k: {"ok": True})
    # Weak resolver contributes nothing here (avoid network); the strong verified
    # discovery is the path under test.
    monkeypatch.setattr(
        plan_cmd, "resolve_datasets", lambda *a, **k: ResolvedDatasets(datasets=[])
    )

    calls: list[str] = []

    def fake_discover(intent, required_fields=None):
        calls.append(intent)
        return VerifiedSource(
            kind="pypi_package", ref="database-knotinfo",
            access_python="import database_knotinfo", record_count=250,
            sample_fields=["crossing_number"], field_coverage=1.0,
        )

    monkeypatch.setattr(dsd, "discover_data_source", fake_discover)
    monkeypatch.setattr(
        ds, "_distill_data_need", lambda raw: ("knotinfo dataset", ["crossing_number"])
    )

    ctx = _make_ctx("PROJ-STRONG", proj, tmp_path)
    mech = PlannerAgent().mechanical_step(ctx)

    # Proactive strong discovery actually ran at plan time.
    assert calls, "discover_data_source was not invoked at plan time"
    # It shares the SAME execution cache on disk.
    cache = proj / ".specify" / "memory" / "discovered_data_source.yaml"
    assert cache.exists()
    assert yaml.safe_load(cache.read_text())["status"] == "verified"
    # The verified source is surfaced to the planner block.
    assert "database-knotinfo" in mech["dataset_block"]
    # No dead weak-manifest was written (D7).
    assert not (proj / ".specify" / "memory" / "resolved_datasets.yaml").exists()


def test_execution_reads_the_plan_time_cache(tmp_path, monkeypatch):
    """The execution backstop reuses the plan-time verified record (shared cache)
    without re-discovering."""
    proj = tmp_path / "projects" / "PROJ-SHARE"
    fdir = proj / "specs" / "001-x"
    fdir.mkdir(parents=True)
    (fdir / "spec.md").write_text("- **FR-001**: load the KnotInfo dataset\n")

    monkeypatch.setattr(PlannerAgent, "_feature_dir", lambda self, ctx: fdir)
    monkeypatch.setattr(plan_cmd, "run_script", lambda *a, **k: {"ok": True})
    monkeypatch.setattr(
        plan_cmd, "resolve_datasets", lambda *a, **k: ResolvedDatasets(datasets=[])
    )
    calls: list[int] = []
    monkeypatch.setattr(
        dsd, "discover_data_source",
        lambda intent, required_fields=None: (calls.append(1), VerifiedSource(
            kind="pypi_package", ref="database-knotinfo",
            access_python="import database_knotinfo", record_count=250,
            sample_fields=["crossing_number"], field_coverage=1.0,
        ))[1],
    )
    monkeypatch.setattr(
        ds, "_distill_data_need", lambda raw: ("knotinfo dataset", ["crossing_number"])
    )

    ctx = _make_ctx("PROJ-SHARE", proj, tmp_path)
    PlannerAgent().mechanical_step(ctx)          # plan time: discovers + caches
    rec = ds.ensure_discovered_source(proj)      # execution backstop: reads cache
    assert rec["status"] == "verified" and rec["ref"] == "database-knotinfo"
    assert len(calls) == 1  # execution reused the plan-time cache, no re-discovery


def test_plan_time_block_degrades_offline(tmp_path, monkeypatch):
    proj = tmp_path / "projects" / "PROJ-OFF"
    proj.mkdir(parents=True)

    def boom(project_dir):
        raise RuntimeError("offline / no backend")

    monkeypatch.setattr(ds, "ensure_discovered_source", boom)
    # Must not raise — a plan run never crashes on data discovery.
    assert PlannerAgent._plan_time_discovered_block(proj) == ""
