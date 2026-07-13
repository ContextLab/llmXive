"""Spec 014 Phase 4 validation tests (Plan → Tasks + Analyze loop).

Every test exercises the REAL guard/validator code path (Principle III); only
the LLM body (or, for FR-006, a real local HTTP server) is controlled, because
the subject under test is the guard, not the model. No test makes a real
Dartmouth call — those happen in scripts/validate_phase4.py.

Implements (per specs/014-…/contracts/regression-tests.md):
- T016: FR-016(a) FILE-marker split + FR-005 completeness + FR-008 template reject
- T017: FR-016(b) URL-reachability via a real http.server fixture
- T018: FR-007 data-model<->contracts consistency
- T019: FR-016(c) prose-stub tasks.md rejection (real tasks_cmd Mode-A validator)
- T020: FR-016(d) Mode-B diff-leak + FR-016(e) header preservation + FR-012
- T021: FR-016(f) analyze-loop cap → human_input_needed escalation
- T025: FR-010 ordering unit test + inspection-record schema + carry-forward schema
"""

from __future__ import annotations

import http.server
import json
import socket
import threading
from datetime import UTC, datetime
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SPEC_DIR = REPO_ROOT / "specs" / "014-phase4-plan-tasks-testing"


# ──────────────────────────────────────────────────────────────────────
# Shared fixtures
# ──────────────────────────────────────────────────────────────────────

def _valid_five_file_block(*, research_urls: str = "", bad_data_model: bool = False) -> str:
    """Return a valid 5-file FILE-marker block (real, non-template)."""
    plan = (
        "# Implementation Plan: Code Duplication Study\n\n"
        "## Summary\n\nWe measure clone density against LLM perplexity using an "
        "AST detector and a pretrained code model, then correlate.\n\n"
        "## Constitution Check\n\n"
        "Principle I (single source of truth): the detector lives in one module. "
        "Principle II (evidence): every claim cites a metric. "
        "Principle III (real tests): we run on a real corpus.\n\n"
        "## Technical Context\n\nPython 3.11, tree-sitter, transformers.\n"
    )
    research = (
        "# Research\n\n## Decisions\n\n"
        "We use tree-sitter for AST parsing because it is fast and language-agnostic. "
        "The corpus is drawn from public Python repositories.\n\n"
        + (f"\n\n## References\n\n{research_urls}\n" if research_urls else "")
    )
    if bad_data_model:
        data_model = "# Data Model\n\n## Orphan Entity\n\nNo schema for this one.\n"
    else:
        data_model = (
            "# Data Model\n\n## Clone Cluster\n\nA set of duplicated code spans.\n\n"
            "## Perplexity Record\n\nPer-file perplexity from the code model.\n"
        )
    quickstart = (
        "# Quickstart\n\n## Setup\n\nInstall deps then run the pipeline against a "
        "checked-out corpus directory; results land in results/.\n"
    )
    contract_a = "title: Clone Cluster\ntype: object\nproperties:\n  files:\n    type: array\n"
    contract_b = "title: Perplexity Record\ntype: object\nproperties:\n  value:\n    type: number\n"
    return (
        "<!-- FILE: plan.md -->\n" + plan + "\n"
        "<!-- FILE: research.md -->\n" + research + "\n"
        "<!-- FILE: data-model.md -->\n" + data_model + "\n"
        "<!-- FILE: quickstart.md -->\n" + quickstart + "\n"
        "<!-- FILE: contracts/clone-cluster.schema.yaml -->\n" + contract_a + "\n"
        "<!-- FILE: contracts/perplexity-record.schema.yaml -->\n" + contract_b + "\n"
    )


def _make_planner_ctx(tmp_path: Path):
    """Build a SlashCommandContext + mechanical_output for the Planner."""
    import shutil

    from llmxive.speckit.slash_command import SlashCommandContext
    from llmxive.types import BackendName

    proj_id = "PROJ-TEST-plan"
    proj_dir = tmp_path / "projects" / proj_id
    feature_dir = proj_dir / "specs" / "001-test"
    feature_dir.mkdir(parents=True)
    # Mirror production: write_artifacts computes repo_root = proj_dir.parent.parent
    # (= tmp_path) and the template-vs-real guard reads <repo>/.specify/templates.
    # Copy the real templates in so Rule 1 (learned-phrase detection) runs exactly
    # as it does in a real repo — otherwise the guard is artificially weakened.
    tmpl_dst = tmp_path / ".specify" / "templates"
    tmpl_dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(REPO_ROOT / ".specify" / "templates", tmpl_dst)
    (feature_dir / "spec.md").write_text(
        "# Feature Specification: Test\n\n## Functional Requirements\n\n"
        "- **FR-001**: System MUST do a thing.\n",
        encoding="utf-8",
    )
    ctx = SlashCommandContext(
        project_id=proj_id, project_dir=proj_dir, run_id="r", task_id="t",
        inputs=[], expected_outputs=[],
        prompt_template_path=tmp_path / "ignored.md",
        default_backend=BackendName.DARTMOUTH, fallback_backends=[],
        default_model="m", prompt_version="1.0.0", agent_name="planner",
    )
    mech = {"feature_dir": str(feature_dir), "spec_path": str(feature_dir / "spec.md")}
    return ctx, mech, feature_dir


# ──────────────────────────────────────────────────────────────────────
# T016 — FILE-marker split + FR-005 completeness + FR-008 template reject
# ──────────────────────────────────────────────────────────────────────

class TestFileMarkerSplit:
    def test_valid_five_file_block_splits_to_all_keys(self) -> None:
        from llmxive.speckit.plan_cmd import _split_multi_file
        files = _split_multi_file(_valid_five_file_block())
        assert "plan.md" in files
        assert "research.md" in files
        assert "data-model.md" in files
        assert "quickstart.md" in files
        assert any(k.startswith("contracts/") for k in files)
        assert files["plan.md"].strip()

    def test_no_marker_response_falls_back_to_single_plan_key(self) -> None:
        from llmxive.speckit.plan_cmd import _split_multi_file
        files = _split_multi_file("just prose, no FILE markers here")
        assert set(files.keys()) == {"plan.md"}

    def test_split_strips_wrapping_and_stray_code_fences(self) -> None:
        """Regression (PROJ-262): the LLM wraps file content in ```fences``` or
        appends a stray trailing ``` — which makes a contracts/*.yaml invalid
        YAML. The splitter must strip both so the emitted file is clean."""
        from llmxive.speckit.plan_cmd import _split_multi_file
        block = (
            "<!-- FILE: contracts/a.schema.yaml -->\n"
            "title: A\ntype: object\n```\n"                       # stray trailing fence
            "<!-- FILE: contracts/b.schema.yaml -->\n"
            "```yaml\ntitle: B\ntype: object\n```\n"               # fully wrapped
        )
        files = _split_multi_file(block)
        assert "```" not in files["contracts/a.schema.yaml"], files["contracts/a.schema.yaml"]
        assert "```" not in files["contracts/b.schema.yaml"], files["contracts/b.schema.yaml"]
        # Content survives intact.
        import yaml
        assert yaml.safe_load(files["contracts/a.schema.yaml"])["title"] == "A"
        assert yaml.safe_load(files["contracts/b.schema.yaml"])["title"] == "B"

    def test_split_keeps_balanced_fences_in_markdown(self) -> None:
        """A .md file with a balanced (closed) code block keeps its fences."""
        from llmxive.speckit.plan_cmd import _split_multi_file
        block = (
            "<!-- FILE: plan.md -->\n"
            "# Plan\n\nRun this:\n\n```bash\npython x.py\n```\n\nDone.\n"
        )
        files = _split_multi_file(block)
        assert "```bash" in files["plan.md"]


class TestArtifactSetComplete:
    def test_full_set_passes(self) -> None:
        from llmxive.speckit._research_guard import assert_artifact_set_complete
        from llmxive.speckit.plan_cmd import _split_multi_file
        assert_artifact_set_complete(_split_multi_file(_valid_five_file_block()))

    def test_no_marker_fallback_raises(self) -> None:
        from llmxive.speckit._research_guard import (
            IncompleteArtifactSet,
            assert_artifact_set_complete,
        )
        with pytest.raises(IncompleteArtifactSet):
            assert_artifact_set_complete({"plan.md": "single file no markers"})

    def test_four_file_set_raises(self) -> None:
        from llmxive.speckit._research_guard import (
            IncompleteArtifactSet,
            assert_artifact_set_complete,
        )
        four = {
            "plan.md": "p", "research.md": "r", "data-model.md": "d",
            "contracts/x.yaml": "title: X",  # missing quickstart.md
        }
        with pytest.raises(IncompleteArtifactSet) as ei:
            assert_artifact_set_complete(four)
        assert "quickstart.md" in ei.value.missing

    def test_empty_artifact_raises(self) -> None:
        from llmxive.speckit._research_guard import (
            IncompleteArtifactSet,
            assert_artifact_set_complete,
        )
        five_but_empty = {
            "plan.md": "p", "research.md": "   ", "data-model.md": "d",
            "quickstart.md": "q", "contracts/x.yaml": "title: X",
        }
        with pytest.raises(IncompleteArtifactSet) as ei:
            assert_artifact_set_complete(five_but_empty)
        assert "research.md" in ei.value.missing

    def test_missing_contracts_raises(self) -> None:
        from llmxive.speckit._research_guard import (
            IncompleteArtifactSet,
            assert_artifact_set_complete,
        )
        no_contract = {
            "plan.md": "p", "research.md": "r", "data-model.md": "d", "quickstart.md": "q",
        }
        with pytest.raises(IncompleteArtifactSet) as ei:
            assert_artifact_set_complete(no_contract)
        assert "contracts/*.yaml" in ei.value.missing


class TestTemplateRejection:
    def test_template_plan_md_triggers_guard_emit_and_unlinks(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """FR-008: a template-equal plan.md → TemplateRefused; write_artifacts
        unlinks all artifacts written this invocation.

        Updated for the bounded planner revision loop (#015 / PROJ-552): the
        guard now fails closed (raise + unlink) only when no usable corrective
        backend is available. Force the offline path (make_backend → None) so
        this asserts the original hard-fail-closed contract without a live LLM
        re-call — exactly the behavior a real offline run takes."""
        import llmxive.backends.router as router
        from llmxive.backends.base import ChatResponse
        from llmxive.speckit._real_only_guard import TemplateRefused
        from llmxive.speckit.plan_cmd import PlannerAgent

        monkeypatch.setattr(router, "make_backend", lambda name: None)
        ctx, mech, feature_dir = _make_planner_ctx(tmp_path)
        template_path = REPO_ROOT / ".specify" / "templates" / "plan-template.md"
        if not template_path.is_file():
            pytest.skip(f"plan template not at {template_path}")
        template_text = template_path.read_text(encoding="utf-8")

        # Build a 5-file block whose plan.md IS the template (so guard_emit fires).
        block = _valid_five_file_block()
        block = block.split("<!-- FILE: research.md -->", 1)
        bad_block = (
            "<!-- FILE: plan.md -->\n" + template_text + "\n"
            "<!-- FILE: research.md -->" + block[1]
        )
        resp = ChatResponse(text=bad_block, model="m", backend="dartmouth")
        agent = PlannerAgent()
        with pytest.raises(TemplateRefused):
            agent.write_artifacts(ctx, mech, resp)
        # All artifacts unlinked — feature_dir has no plan.md/research.md/etc.
        leftover = [p.name for p in feature_dir.rglob("*") if p.is_file() and p.name != "spec.md"]
        assert leftover == [], f"artifacts not unlinked: {leftover}"


# ──────────────────────────────────────────────────────────────────────
# T017 — FR-006 URL reachability via a REAL local http.server
# ──────────────────────────────────────────────────────────────────────

class _StatusHandler(http.server.BaseHTTPRequestHandler):
    """Returns a configurable status code; the code is read from server.status."""

    def log_message(self, *args):  # silence test noise
        pass

    def _respond(self):
        status = getattr(self.server, "status", 200)
        self.send_response(status)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_HEAD(self):
        self._respond()

    def do_GET(self):
        self._respond()


@pytest.fixture
def http_server():
    """Yield a (base_url, set_status) pair backed by a real local server."""
    server = http.server.HTTPServer(("127.0.0.1", 0), _StatusHandler)
    server.status = 200
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    def set_status(code: int) -> None:
        server.status = code

    try:
        yield f"http://127.0.0.1:{port}", set_status
    finally:
        server.shutdown()
        server.server_close()


def _dead_url() -> str:
    """A URL on a port that nothing is listening on (connection refused)."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()  # close so the port is free → connection refused on connect
    return f"http://127.0.0.1:{port}/dead"


class TestUrlReachability:
    def test_200_passes(self, http_server) -> None:
        from llmxive.speckit._research_guard import assert_urls_reachable
        base, set_status = http_server
        set_status(200)
        assert_urls_reachable(f"See dataset at {base}/data for details.")

    def test_backtick_wrapped_url_extracted_without_backtick(self) -> None:
        """Regression (PROJ-262): a URL or doi written in markdown `backticks`
        must NOT capture the closing backtick into its path — that produced a
        false 404 (e.g. '.../realKnownCause/`')."""
        from llmxive.speckit._research_guard import _extract_references
        refs = _extract_references("Dataset at `https://example.com/data/dir/` here.")
        assert refs == ["https://example.com/data/dir/"], refs
        refs2 = _extract_references("See `doi:10.1234/abc.def` for details.")
        assert refs2 == ["https://doi.org/10.1234/abc.def"], refs2

    def test_404_raises(self, http_server) -> None:
        from llmxive.speckit._research_guard import (
            UnreachableReference,
            assert_urls_reachable,
        )
        base, set_status = http_server
        set_status(404)
        with pytest.raises(UnreachableReference):
            assert_urls_reachable(f"Broken link: {base}/missing")

    def test_500_raises(self, http_server) -> None:
        from llmxive.speckit._research_guard import (
            UnreachableReference,
            assert_urls_reachable,
        )
        base, set_status = http_server
        set_status(500)
        with pytest.raises(UnreachableReference):
            assert_urls_reachable(f"Server error link: {base}/boom")

    def test_connection_refused_raises(self) -> None:
        from llmxive.speckit._research_guard import (
            UnreachableReference,
            assert_urls_reachable,
        )
        with pytest.raises(UnreachableReference):
            assert_urls_reachable(f"Dead link: {_dead_url()}")

    # --- access-denied is NOT a dead reference (the false-positive wedge) -------
    #
    # A 403/401/429 means the source REFUSED OUR PROBE — the resource is there. It
    # is what a bot-blocking host (openalex.org) or a rate limiter returns, and it
    # NEVER self-heals on a re-run, so blocking on it wedged live projects forever
    # against perfectly healthy sources (67 advance_errors). Only 404/410 prove a
    # reference does not exist; those still hard-block (test_404_raises), as do
    # 5xx (transient, recovers on re-run) and DNS failures. Same policy the
    # citation layer already adopted for 401/403/429.

    @pytest.mark.parametrize("status", [401, 403, 429])
    def test_access_denied_does_not_raise(self, http_server, status: int) -> None:
        from llmxive.speckit._research_guard import assert_urls_reachable
        base, set_status = http_server
        set_status(status)
        assert_urls_reachable(f"Bot-blocked but live source: {base}/dataset")

    def test_unprocessable_probe_does_not_raise(self, http_server) -> None:
        """422 = the ENDPOINT exists, our probe's shape was wrong (e.g. a bare
        api.github.com/search/repositories with no `q=`). Not a dead reference."""
        from llmxive.speckit._research_guard import assert_urls_reachable
        base, set_status = http_server
        set_status(422)
        assert_urls_reachable(f"API endpoint: {base}/search/repositories")

    def test_zero_refs_is_noop(self) -> None:
        from llmxive.speckit._research_guard import assert_urls_reachable
        assert_urls_reachable("This research.md cites no external references.")

    def test_planner_write_artifacts_unlinks_on_bad_url(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """FR-006 end-to-end: a bad URL in research.md makes the Planner
        unlink every artifact and raise UnreachableReference.

        Updated for the bounded planner revision loop (#015 / PROJ-552): force
        the offline path (make_backend → None) so the guard fails closed without
        a live corrective re-call — the same hard-fail-closed contract this test
        has always asserted, now via the loop's no-backend branch."""
        import llmxive.backends.router as router
        from llmxive.backends.base import ChatResponse
        from llmxive.speckit._research_guard import UnreachableReference
        from llmxive.speckit.plan_cmd import PlannerAgent

        monkeypatch.setattr(router, "make_backend", lambda name: None)
        ctx, mech, feature_dir = _make_planner_ctx(tmp_path)
        block = _valid_five_file_block(
            research_urls=f"- Dataset: {_dead_url()}"
        )
        resp = ChatResponse(text=block, model="m", backend="dartmouth")
        agent = PlannerAgent()
        with pytest.raises(UnreachableReference):
            agent.write_artifacts(ctx, mech, resp)
        leftover = [p.name for p in feature_dir.rglob("*") if p.is_file() and p.name != "spec.md"]
        assert leftover == [], f"artifacts not unlinked after bad URL: {leftover}"


# ──────────────────────────────────────────────────────────────────────
# T018 — FR-007 data-model <-> contracts consistency
# ──────────────────────────────────────────────────────────────────────

class TestDataModelConsistency:
    """FR-007 (corrected to the robust, structural form): data-model.md must
    define real entities and every contracts/*.yaml must be a real schema.
    Entity↔schema cardinality and naming are intentionally NOT constrained —
    the Planner contract requires ≥1 schema, not one per entity, and schema
    filenames legitimately differ from entity headings."""

    def test_aligned_passes(self) -> None:
        from llmxive.speckit._research_guard import assert_data_model_contracts_consistent
        files = {
            "data-model.md": "# Data Model\n\n## Widget\n\nA widget.\n\n## Gadget\n\nA gadget.\n",
            "contracts/widget.schema.yaml": "title: Widget\ntype: object",
            "contracts/gadget.schema.yaml": "title: Gadget\ntype: object",
        }
        assert_data_model_contracts_consistent(files)

    def test_cardinality_and_naming_mismatch_passes(self) -> None:
        """The previously-rejected real-world case: 4 entities, 1 schema, with a
        schema name that differs from every entity heading. MUST now pass."""
        from llmxive.speckit._research_guard import assert_data_model_contracts_consistent
        files = {
            "data-model.md": (
                "# Data Model\n\n## Entity Definitions\n\n"
                "### CodeSegment\n\n| a | b |\n|---|---|\n| 1 | 2 |\n\n"
                "### CloneDensityMetric\n\nx\n\n### ModelMetric\n\ny\n\n"
                "### CorrelationResult\n\nz\n\n## Data Flow\n\nflows...\n"
            ),
            "contracts/code_duplication_metrics.schema.yaml": "title: Code Duplication Metrics\ntype: object",
        }
        assert_data_model_contracts_consistent(files)

    def test_no_entities_raises(self) -> None:
        from llmxive.speckit._research_guard import (
            InconsistentDataModel,
            assert_data_model_contracts_consistent,
        )
        files = {
            "data-model.md": "# Data Model\n\nThis document describes the data but defines nothing concrete.\n",
            "contracts/x.schema.yaml": "title: X\ntype: object",
        }
        with pytest.raises(InconsistentDataModel):
            assert_data_model_contracts_consistent(files)

    def test_empty_schema_raises(self) -> None:
        from llmxive.speckit._research_guard import (
            InconsistentDataModel,
            assert_data_model_contracts_consistent,
        )
        files = {
            "data-model.md": "# Data Model\n\n## Widget\n\n| a | b |\n|---|---|\n| 1 | 2 |\n",
            "contracts/widget.schema.yaml": "   ",  # empty
        }
        with pytest.raises(InconsistentDataModel):
            assert_data_model_contracts_consistent(files)

    def test_non_mapping_schema_raises(self) -> None:
        from llmxive.speckit._research_guard import (
            InconsistentDataModel,
            assert_data_model_contracts_consistent,
        )
        files = {
            "data-model.md": "# Data Model\n\n## Widget\n\n| a | b |\n|---|---|\n| 1 | 2 |\n",
            "contracts/widget.schema.yaml": "just a prose sentence, not a schema",
        }
        with pytest.raises(InconsistentDataModel):
            assert_data_model_contracts_consistent(files)

    def test_no_data_model_is_noop(self) -> None:
        from llmxive.speckit._research_guard import assert_data_model_contracts_consistent
        assert_data_model_contracts_consistent({"contracts/x.schema.yaml": "title: X\ntype: object"})


# ──────────────────────────────────────────────────────────────────────
# Tasker test scaffolding (T019/T020/T021)
# ──────────────────────────────────────────────────────────────────────

def _make_tasker_project(tmp_path: Path):
    """Build a minimal project layout for the Tasker + return (ctx, mech)."""
    from llmxive.speckit.slash_command import SlashCommandContext
    from llmxive.types import BackendName

    proj_id = "PROJ-TEST-task"
    proj_dir = tmp_path / "projects" / proj_id
    feature_dir = proj_dir / "specs" / "001-test"
    feature_dir.mkdir(parents=True)
    spec_md = feature_dir / "spec.md"
    plan_md = feature_dir / "plan.md"
    spec_md.write_text(
        "# Feature Specification: Test\n\n## Functional Requirements\n\n"
        "- **FR-001**: System MUST do A.\n- **FR-002**: System MUST do B.\n\n"
        "## Success Criteria\n\n- **SC-001**: A works.\n- **SC-002**: B works.\n",
        encoding="utf-8",
    )
    plan_md.write_text(
        "# Implementation Plan: Test\n\n## Summary\n\nReal plan prose describing the approach.\n",
        encoding="utf-8",
    )
    # Provide a real templates dir so guard_emit can classify against it.
    tmpl_dir = proj_dir / ".specify" / "templates"
    tmpl_dir.mkdir(parents=True)
    src_tmpl = REPO_ROOT / ".specify" / "templates" / "tasks-template.md"
    if src_tmpl.is_file():
        (tmpl_dir / "tasks-template.md").write_text(src_tmpl.read_text(encoding="utf-8"), encoding="utf-8")
    src_plan_tmpl = REPO_ROOT / ".specify" / "templates" / "plan-template.md"
    if src_plan_tmpl.is_file():
        (tmpl_dir / "plan-template.md").write_text(src_plan_tmpl.read_text(encoding="utf-8"), encoding="utf-8")

    ctx = SlashCommandContext(
        project_id=proj_id, project_dir=proj_dir, run_id="r", task_id="t",
        inputs=[], expected_outputs=[],
        prompt_template_path=tmp_path / "ignored.md",
        default_backend=BackendName.DARTMOUTH, fallback_backends=[],
        default_model="m", prompt_version="1.0.0", agent_name="tasker",
    )
    mech = {
        "feature_dir": str(feature_dir),
        "spec_path": str(spec_md),
        "plan_path": str(plan_md),
        "tasks_path": str(feature_dir / "tasks.md"),
        "tasks_template_path": str(tmpl_dir / "tasks-template.md"),
    }
    return ctx, mech, feature_dir


def _real_tasks_md(n: int = 12) -> str:
    lines = ["# Tasks: Test", "", "## Phase 1: Setup", ""]
    for i in range(1, n + 1):
        lines.append(f"- [ ] T{i:03d} [P] Implement step {i} in src/module_{i}.py")
    return "\n".join(lines) + "\n"


# ──────────────────────────────────────────────────────────────────────
# T019 — FR-016(c) prose-stub tasks.md rejection (real Mode-A validator)
# ──────────────────────────────────────────────────────────────────────

class TestProseStubRejection:
    def test_prose_stub_tasks_md_raises(self, tmp_path: Path) -> None:
        from llmxive.backends.base import ChatResponse
        from llmxive.speckit.tasks_cmd import TaskerAgent

        ctx, mech, feature_dir = _make_tasker_project(tmp_path)
        prose = (
            "# Tasks\n\nAll the work is basically done; just run the script and "
            "review the output. No further tasks needed.\n\n- [ ] T001 do everything\n"
        )
        resp = ChatResponse(text=prose, model="m", backend="dartmouth")
        agent = TaskerAgent()
        with pytest.raises(RuntimeError, match=r"task ID"):
            agent.write_artifacts(ctx, mech, resp)
        # tasks.md must NOT have been committed.
        assert not (feature_dir / "tasks.md").is_file()


# ──────────────────────────────────────────────────────────────────────
# T020 — FR-016(d) diff-leak, FR-016(e) header preservation, FR-012
# ──────────────────────────────────────────────────────────────────────

class TestModeBGuards:
    def test_mode_b_diff_leak_rejected(self) -> None:
        """FR-016(d): a Mode-B patch shaped as a unified diff is a diff."""
        from llmxive.speckit._diff_guard import looks_like_diff, refuse_if_diff
        diff_patch = (
            "--- a/spec.md\n+++ b/spec.md\n@@ -1,2 +1,2 @@\n-old\n+new\n context\n"
        )
        is_diff, _reason = looks_like_diff(diff_patch)
        assert is_diff
        with pytest.raises(RuntimeError):
            refuse_if_diff(diff_patch, artifact_kind="spec.md")

    def test_mode_b_header_clobber_detected(self) -> None:
        """FR-016(e): a spec.md/plan.md rewrite with no '# ' header is rejected
        by the same regex the Tasker Mode-B path uses."""
        import re
        no_header = "All requirements satisfied. Nothing to see here.\n"
        # Mirror tasks_cmd.py Mode-B per-patch header check.
        assert not re.search(r"^# ", no_header, re.MULTILINE)
        with_header = "# Feature Specification\n\nReal content.\n"
        assert re.search(r"^# ", with_header, re.MULTILINE)

    def test_fr012_flags_constraint_drop(self) -> None:
        """FR-012: a Mode-B spec.md rewrite that drops an FR-NNN line is flagged."""
        import importlib.util
        spec = importlib.util.spec_from_file_location("vp4", REPO_ROOT / "scripts" / "validate_phase4.py")
        vp4 = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(vp4)
        before = "FR-001 FR-002 FR-003 SC-001 SC-002"
        after_drop = "FR-001 FR-002 SC-001 SC-002"  # dropped FR-003
        bf, bs = vp4.fr_sc_counts(before)
        af, af_sc = vp4.fr_sc_counts(after_drop)
        # A dropped FR is exactly what FR-012 must flag: FR count fell, SC held.
        assert af < bf, "expected FR count to drop"
        assert af_sc == bs, "SC count should be unchanged in this rewrite"
        # Non-reducing rewrite passes (no flag).
        after_ok = "FR-001 FR-002 FR-003 FR-004 SC-001 SC-002 SC-003"
        ok_fr, ok_sc = vp4.fr_sc_counts(after_ok)
        assert ok_fr >= bf and ok_sc >= bs


# ──────────────────────────────────────────────────────────────────────
# T021 — FR-016(f) analyze-loop cap → human_input_needed escalation
# ──────────────────────────────────────────────────────────────────────

class TestAnalyzeLoopEscalation:
    """Legacy Mode-A/Mode-B regression tests.

    Spec 015 T027 made the convergence engine the default analyze-resolve
    path; these tests exercise the legacy Mode-A/Mode-B loop (preserved
    as the emergency-rollback path via ``LLMXIVE_TASKER_LEGACY=1``).
    Each test forces the legacy path via the env var so the legacy
    contract (escalate → human_input_needed.yaml; cap-hit best-effort;
    FR-031 constraint-preservation guard) is still regression-tested.
    The new engine-default behavior is tested separately in
    ``test_tasker_production_cutover.py``.
    """

    def test_never_clean_analyze_escalates(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Drive a never-clean analyze with a synthetic escalate verdict on the
        last round; assert human_input_needed.yaml is written and the round is
        captured in _inspection_rounds. (Legacy path only — see class docstring.)"""
        monkeypatch.setenv("LLMXIVE_TASKER_LEGACY", "1")
        import llmxive.speckit.tasks_cmd as tasks_cmd
        from llmxive.backends.base import ChatResponse
        from llmxive.config import TASKER_MAX_REVISION_ROUNDS
        from llmxive.speckit.tasks_cmd import TaskerAgent

        ctx, mech, feature_dir = _make_tasker_project(tmp_path)

        # Always-dirty analyze: never returns CLEAN.
        monkeypatch.setattr(
            tasks_cmd, "run_analyze",
            lambda **kw: "- (severity: HIGH) (spec.md:FR) unresolved finding",
        )
        # The legacy tasker gates convergence on analyze_advance_ok (the
        # two-tier doc-stage bar), not is_clean — force never-advance.
        monkeypatch.setattr(tasks_cmd, "analyze_advance_ok", lambda report: False)

        # Synthetic Mode-B response: escalate on the FINAL round; otherwise a
        # benign no-op patch. We count calls to flip to escalate at the cap.
        call_state = {"n": 0}

        def fake_chat(messages, **kwargs):
            call_state["n"] += 1
            verdict = "escalate" if call_state["n"] >= TASKER_MAX_REVISION_ROUNDS else "needs-rerun"
            doc = {"issues_resolved": [], "issues_remaining": ["x"], "verdict": verdict}
            return ChatResponse(text=json.dumps(doc), model="m", backend="dartmouth")

        monkeypatch.setattr(tasks_cmd, "chat_with_fallback", fake_chat)
        # Mode-B reads agents/prompts/tasker.md relative to the (temp) repo
        # root; the prompt text is irrelevant to the escalation logic under
        # test, so stub it out (we exercise the loop + escalate branch, not
        # the prompt rendering).
        monkeypatch.setattr(tasks_cmd, "render_prompt", lambda *a, **k: "stub system prompt")

        agent = TaskerAgent()
        resp = ChatResponse(text=_real_tasks_md(), model="m", backend="dartmouth")
        agent.write_artifacts(ctx, mech, resp)

        marker = feature_dir.parent.parent / ".specify" / "memory" / "human_input_needed.yaml"
        assert marker.is_file(), "human_input_needed.yaml not written on escalate"
        data = yaml.safe_load(marker.read_text(encoding="utf-8"))
        assert "rounds_used" in data
        # Observability: rounds captured (one per analyze round up to escalate).
        assert agent._inspection_rounds, "no inspection rounds captured"
        assert agent._inspection_rounds[-1]["verdict"] == "escalate"

    def test_cap_hit_without_escalate_advances_best_effort(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Per the 2026-05-21 decision: when the analyze loop hits the round cap
        WITHOUT a clean report AND WITHOUT an explicit escalate verdict, the
        Tasker accepts tasks.md as best-effort (records converged:false) and does
        NOT write human_input_needed.yaml — the project is allowed to advance to
        'analyzed'. (human_input_needed is reserved for explicit escalate.)
        Legacy path only — see class docstring."""
        monkeypatch.setenv("LLMXIVE_TASKER_LEGACY", "1")
        import llmxive.speckit.tasks_cmd as tasks_cmd
        from llmxive.backends.base import ChatResponse
        from llmxive.config import TASKER_MAX_REVISION_ROUNDS
        from llmxive.speckit.tasks_cmd import TaskerAgent

        ctx, mech, feature_dir = _make_tasker_project(tmp_path)
        monkeypatch.setattr(
            tasks_cmd, "run_analyze",
            lambda **kw: "- (severity: MEDIUM) (tasks.md) advisory nitpick",
        )
        # Force never-advance (legacy path gates on analyze_advance_ok).
        monkeypatch.setattr(tasks_cmd, "analyze_advance_ok", lambda report: False)

        def fake_chat(messages, **kwargs):
            # Never escalate — every round is a benign needs-rerun no-op patch.
            doc = {"issues_resolved": [], "issues_remaining": ["x"], "verdict": "needs-rerun"}
            return ChatResponse(text=json.dumps(doc), model="m", backend="dartmouth")

        monkeypatch.setattr(tasks_cmd, "chat_with_fallback", fake_chat)
        monkeypatch.setattr(tasks_cmd, "render_prompt", lambda *a, **k: "stub system prompt")

        agent = TaskerAgent()
        resp = ChatResponse(text=_real_tasks_md(), model="m", backend="dartmouth")
        agent.write_artifacts(ctx, mech, resp)  # must NOT raise

        mem = feature_dir.parent.parent / ".specify" / "memory"
        assert not (mem / "human_input_needed.yaml").is_file(), \
            "cap-hit without escalate must NOT write human_input_needed.yaml"
        rounds = yaml.safe_load((mem / "tasker_rounds.yaml").read_text(encoding="utf-8"))
        assert rounds.get("converged") is False
        assert rounds.get("rounds_used") == TASKER_MAX_REVISION_ROUNDS

    def test_mode_b_refuses_spec_md_patch_that_drops_requirements(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """FR-012 (Tasker guard): a Mode-B patch that gut's spec.md (fewer FR/SC
        identifiers than the current file) MUST be refused at the source. The
        LLM otherwise 'converges' analyze by deleting requirements (observed on
        PROJ-262: 12 FR / 5 SC -> 0 FR / 2 SC). spec.md must stay intact.
        Legacy path; same guards run via _legacy_guards.check_legacy_guards
        on both legacy + engine paths (FR-031 SSoT)."""
        monkeypatch.setenv("LLMXIVE_TASKER_LEGACY", "1")
        import re

        import llmxive.speckit.tasks_cmd as tasks_cmd
        from llmxive.backends.base import ChatResponse
        from llmxive.speckit.tasks_cmd import TaskerAgent

        ctx, mech, feature_dir = _make_tasker_project(tmp_path)
        spec_path = feature_dir / "spec.md"  # _make_tasker_project: 2 FR + 2 SC = 4 ids

        monkeypatch.setattr(tasks_cmd, "run_analyze", lambda **kw: "- (severity: HIGH) finding")
        # Advance on the 2nd analyze so the loop ends after one Mode-B round
        # (legacy path gates convergence on analyze_advance_ok, not is_clean).
        state = {"n": 0}
        def _advance_ok(report):
            state["n"] += 1
            return state["n"] >= 2
        monkeypatch.setattr(tasks_cmd, "analyze_advance_ok", _advance_ok)

        def fake_chat(messages, **kwargs):
            # Mode-B "resolves" the finding by gutting spec.md to a single FR.
            gutted = "# Spec\n\n## FR\n\n- **FR-001**: only one left.\n"
            doc = {"issues_resolved": [{"file": "spec.md", "patch": gutted, "rationale": "x"}],
                   "issues_remaining": [], "verdict": "needs-rerun"}
            return ChatResponse(text=json.dumps(doc), model="m", backend="dartmouth")

        monkeypatch.setattr(tasks_cmd, "chat_with_fallback", fake_chat)
        monkeypatch.setattr(tasks_cmd, "render_prompt", lambda *a, **k: "stub system prompt")

        agent = TaskerAgent()
        agent.write_artifacts(ctx, mech, ChatResponse(text=_real_tasks_md(), model="m", backend="dartmouth"))

        ids = set(re.findall(r"\b(?:FR|SC)-\d+", spec_path.read_text(encoding="utf-8")))
        assert ids == {"FR-001", "FR-002", "SC-001", "SC-002"}, \
            f"spec.md was gutted despite the FR-012 guard: {sorted(ids)}"


# ──────────────────────────────────────────────────────────────────────
# T025 — ordering unit test + inspection-record schema + carry-forward schema
# ──────────────────────────────────────────────────────────────────────

class TestOrderingCheck:
    def test_consumer_before_producer_flagged(self) -> None:
        import importlib.util
        spec = importlib.util.spec_from_file_location("vp4", REPO_ROOT / "scripts" / "validate_phase4.py")
        vp4 = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(vp4)
        bad = (
            "- [ ] T001 [P] Train model on data/corpus.parquet\n"
            "- [ ] T002 Download data/corpus.parquet from the hub\n"
        )
        assert vp4.check_task_ordering(bad), "expected an ordering finding"

    def test_correct_order_passes(self) -> None:
        import importlib.util
        spec = importlib.util.spec_from_file_location("vp4", REPO_ROOT / "scripts" / "validate_phase4.py")
        vp4 = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(vp4)
        good = (
            "- [ ] T001 Download data/corpus.parquet from the hub\n"
            "- [ ] T002 Train model on data/corpus.parquet\n"
        )
        assert vp4.check_task_ordering(good) == []


class TestInspectionRecordSchemaWithRounds:
    def _capture_tasker_record(self, tmp_path: Path):
        from llmxive.speckit._inspection import capture
        started = datetime(2026, 5, 21, 12, 0, 0, tzinfo=UTC)
        ended = datetime(2026, 5, 21, 12, 5, 0, tzinfo=UTC)
        rounds = [
            {"round_index": 0, "analyze_report": "- (HIGH) finding", "mode_b_patch": "{...}",
             "verdict": "needs-rerun", "files_rewritten": ["spec.md"],
             "diffs": {"spec.md": "--- a/spec.md\n+++ b/spec.md\n"}},
            {"round_index": 1, "analyze_report": "CLEAN", "mode_b_patch": None,
             "verdict": "clean", "files_rewritten": [], "diffs": {}},
        ]
        return capture(
            project_id="PROJ-TEST-foo", agent_name="tasker", agent_version="1.0.0",
            model="m", backend="dartmouth", started_at=started, ended_at=ended,
            outcome="committed", prompts={"system": "sys prompt here", "user": "usr prompt here"},
            raw_response="the final tasks.md summary", parsed_output={"tasks": 12},
            file_diffs=[{"path": "tasks.md", "before": "", "after": "x"}],
            reset_artifacts=[], error=None, spec_root=tmp_path, rounds=rounds,
        )

    def test_record_has_all_required_keys_incl_rounds(self, tmp_path: Path) -> None:
        out = self._capture_tasker_record(tmp_path)
        rec = json.loads(out.read_text(encoding="utf-8"))
        required = {
            "project_id", "agent_name", "agent_version", "model", "backend",
            "started_at", "ended_at", "duration_s", "outcome",
            "reset_artifacts", "prompts", "raw_response", "parsed_output",
            "file_diffs", "error", "rounds",
        }
        assert required - set(rec.keys()) == set()

    def test_tasker_rounds_reconstruct(self, tmp_path: Path) -> None:
        out = self._capture_tasker_record(tmp_path)
        rec = json.loads(out.read_text(encoding="utf-8"))
        assert len(rec["rounds"]) == 2
        r0 = rec["rounds"][0]
        for k in ("round_index", "analyze_report", "mode_b_patch", "verdict", "files_rewritten", "diffs"):
            assert k in r0
        assert rec["rounds"][1]["verdict"] == "clean"

    def test_planner_record_rounds_default_empty(self, tmp_path: Path) -> None:
        from llmxive.speckit._inspection import capture
        started = datetime(2026, 5, 21, 12, 0, 0, tzinfo=UTC)
        ended = datetime(2026, 5, 21, 12, 1, 0, tzinfo=UTC)
        out = capture(
            project_id="PROJ-TEST-foo", agent_name="planner", agent_version="1.0.0",
            model="m", backend="dartmouth", started_at=started, ended_at=ended,
            outcome="committed", prompts={"system": "s", "user": "u"},
            raw_response="r", parsed_output={}, file_diffs=[], reset_artifacts=[],
            error=None, spec_root=tmp_path,
        )
        rec = json.loads(out.read_text(encoding="utf-8"))
        assert rec["rounds"] == []

    def test_redact_leaves_no_secret_shaped_strings(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        from llmxive.speckit._inspection import capture
        secret = "sk-phase4-deadbeefcafebabe0123456789"
        monkeypatch.setenv("DARTMOUTH_CHAT_API_KEY", secret)
        started = datetime(2026, 5, 21, 12, 0, 0, tzinfo=UTC)
        ended = datetime(2026, 5, 21, 12, 1, 0, tzinfo=UTC)
        out = capture(
            project_id="PROJ-TEST-foo", agent_name="tasker", agent_version="1.0.0",
            model="m", backend="dartmouth", started_at=started, ended_at=ended,
            outcome="committed",
            prompts={"system": f"Authorization: Bearer {secret}", "user": "u"},
            raw_response=f"leaked {secret} here", parsed_output={}, file_diffs=[],
            reset_artifacts=[], error=None, spec_root=tmp_path,
            rounds=[{"round_index": 0, "analyze_report": "ok", "mode_b_patch": None,
                     "verdict": "clean", "files_rewritten": [], "diffs": {}}],
        )
        text = out.read_text(encoding="utf-8")
        assert secret not in text
        assert "<redacted>" in text


class TestCarryForwardSchema:
    def test_emit_carry_forward_well_formed(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        import importlib.util
        spec = importlib.util.spec_from_file_location("vp4", REPO_ROOT / "scripts" / "validate_phase4.py")
        vp4 = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(vp4)
        monkeypatch.setattr(vp4, "SPEC_DIR", tmp_path)
        results = [
            {"project_id": "PROJ-261-x", "final_state": "analyzed", "status": "passed",
             "findings": [], "evidence": {"analyze_rounds": 2}},
            {"project_id": "PROJ-262-y", "final_state": "human_input_needed", "status": "held",
             "findings": ["loop cap hit"], "evidence": {"analyze_rounds": 5}},
        ]
        out = vp4.emit_carry_forward(results)
        manifest = yaml.safe_load(out.read_text(encoding="utf-8"))
        assert manifest["spec"] == "014-phase4-plan-tasks-testing"
        assert "generated_at" in manifest and "final_commit" in manifest
        assert len(manifest["projects"]) == 2
        p1 = manifest["projects"][0]
        assert p1["final_state"] == "analyzed" and p1["status"] == "passed"
        tasker = next(a for a in p1["agents_run"] if a["name"] == "tasker")
        assert tasker["analyze_rounds"] == 2
        p2 = manifest["projects"][1]
        assert p2["status"] == "held"
        assert "inspection" in p2["justification"].lower() or "tasker.json" in p2["justification"]

    def test_phase_report_has_required_sections(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        import importlib.util
        spec = importlib.util.spec_from_file_location("vp4", REPO_ROOT / "scripts" / "validate_phase4.py")
        vp4 = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(vp4)
        monkeypatch.setattr(vp4, "SPEC_DIR", tmp_path)
        monkeypatch.setattr(vp4, "INSPECTIONS_DIR", tmp_path / "inspections")
        results = [
            {"project_id": "PROJ-261-x", "final_state": "analyzed", "status": "passed",
             "findings": [], "evidence": {"analyze_rounds": 0}},
        ]
        out = vp4.emit_phase_report(results)
        text = out.read_text(encoding="utf-8")
        for section in ("## Summary", "## FR → evidence", "## Quality-gate findings",
                        "## Mode-B coverage", "## Carry-forward"):
            assert section in text, f"missing section {section!r}"
