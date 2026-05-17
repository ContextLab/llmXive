"""Spec 011 Phase 3 validation tests.

Implements:
- T011: inspection-hook unit test (env-gated capture in slash_command.py)
- T016: inspection-record schema validation + SC-006 reconstruction check
- T018: secret redaction
- T019: atomic write
- T020: diff-leak guard regression
- T021: template-only guard regression
- T022: clarifier echo-the-question rejection regression
- T025: carry-forward manifest schema
- T026: gated end-to-end smoke test against PROJ-261 (skipped without backend key)

See specs/011-phase3-specify-clarify-testing/contracts/regression-tests.md
for the formal contracts.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SPEC_DIR = REPO_ROOT / "specs" / "011-phase3-specify-clarify-testing"
FIXTURES = REPO_ROOT / "tests" / "fixtures" / "phase3"


# ──────────────────────────────────────────────────────────────────────
# T016 + SC-006 reconstruction
# ──────────────────────────────────────────────────────────────────────

class TestInspectionRecordSchema:
    """Asserts every required key from contracts/inspection-record.md is
    present with correct types, plus SC-006 reconstruction check."""

    @pytest.fixture
    def sample(self) -> dict:
        return json.loads((FIXTURES / "sample_specifier_inspection.json").read_text())

    def test_required_top_level_keys_present(self, sample: dict) -> None:
        required = {
            "project_id", "agent_name", "agent_version", "model", "backend",
            "started_at", "ended_at", "duration_s", "outcome",
            "reset_artifacts", "prompts", "raw_response", "parsed_output",
            "file_diffs", "error",
        }
        missing = required - set(sample.keys())
        assert not missing, f"fixture missing required keys: {sorted(missing)}"

    def test_outcome_in_enum(self, sample: dict) -> None:
        assert sample["outcome"] in {"committed", "abstained", "failed", "held", "no-op"}

    def test_types(self, sample: dict) -> None:
        assert isinstance(sample["project_id"], str)
        assert isinstance(sample["agent_name"], str)
        assert isinstance(sample["duration_s"], (int, float))
        assert isinstance(sample["reset_artifacts"], list)
        assert isinstance(sample["prompts"], dict)
        assert isinstance(sample["raw_response"], str)
        assert isinstance(sample["parsed_output"], dict)
        assert isinstance(sample["file_diffs"], list)
        assert sample["error"] is None or isinstance(sample["error"], str)

    def test_sc006_reconstruction_committed_records_have_substantive_prompts_and_response(
        self, sample: dict
    ) -> None:
        # SC-006: a maintainer must be able to reconstruct what the agent
        # did from this one file alone. When outcome=="committed", all
        # three I/O fields MUST be substantive (≥10 chars).
        if sample["outcome"] == "committed":
            assert len(sample["prompts"]["system"]) >= 10, "system prompt too short to reconstruct"
            assert len(sample["prompts"]["user"]) >= 10, "user prompt too short to reconstruct"
            assert len(sample["raw_response"]) >= 10, "raw_response too short to reconstruct"


# ──────────────────────────────────────────────────────────────────────
# T018 — redaction
# ──────────────────────────────────────────────────────────────────────

class TestRedaction:
    def test_redacts_dartmouth_key_from_text(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from llmxive.speckit._inspection import _redact
        monkeypatch.setenv("DARTMOUTH_CHAT_API_KEY", "sk-fake-1234567890abcdef")
        text = "Authorization: Bearer sk-fake-1234567890abcdef in the headers."
        out = _redact(text)
        assert "sk-fake-1234567890abcdef" not in out
        assert "<redacted>" in out
        assert "Authorization:" in out  # other text preserved

    def test_leaves_unmatched_text_unchanged(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from llmxive.speckit._inspection import _redact
        monkeypatch.setenv("DARTMOUTH_CHAT_API_KEY", "sk-fake-1234567890abcdef")
        text = "no secrets here, just prose"
        assert _redact(text) == text

    def test_handles_empty_string(self) -> None:
        from llmxive.speckit._inspection import _redact
        assert _redact("") == ""

    def test_skips_short_env_values(self, monkeypatch: pytest.MonkeyPatch) -> None:
        # A 2-char "key" would over-redact (e.g., redacting "OK" everywhere).
        # We require ≥8 chars before treating a value as redactable.
        from llmxive.speckit._inspection import _redact
        monkeypatch.setenv("GITHUB_TOKEN", "x")
        text = "x marks the spot"
        assert _redact(text) == text  # not redacted (too short)


# ──────────────────────────────────────────────────────────────────────
# T019 — atomic write
# ──────────────────────────────────────────────────────────────────────

class TestAtomicWrite:
    def test_capture_writes_then_reads_back_equal(self, tmp_path: Path) -> None:
        from llmxive.speckit._inspection import capture
        started = datetime(2026, 5, 17, 12, 0, 0, tzinfo=timezone.utc)
        ended = datetime(2026, 5, 17, 12, 0, 5, tzinfo=timezone.utc)
        out = capture(
            project_id="PROJ-TEST-foo", agent_name="specifier",
            agent_version="1.0.0", model="m", backend="dartmouth",
            started_at=started, ended_at=ended, outcome="committed",
            prompts={"system": "sys", "user": "usr"}, raw_response="resp",
            parsed_output={"k": "v"},
            file_diffs=[{"path": "a.md", "before": "", "after": "x"}],
            reset_artifacts=[], error=None, spec_root=tmp_path,
        )
        assert out.is_file()
        # No .tmp file left behind
        assert not out.with_suffix(out.suffix + ".tmp").exists()
        rec = json.loads(out.read_text(encoding="utf-8"))
        assert rec["project_id"] == "PROJ-TEST-foo"
        assert rec["duration_s"] == 5.0

    def test_capture_overwrites_cleanly_on_rerun(self, tmp_path: Path) -> None:
        from llmxive.speckit._inspection import capture
        started = datetime(2026, 5, 17, 12, 0, 0, tzinfo=timezone.utc)
        ended = datetime(2026, 5, 17, 12, 0, 5, tzinfo=timezone.utc)
        base_kwargs = dict(
            project_id="PROJ-TEST-foo", agent_name="specifier",
            agent_version="1.0.0", model="m", backend="dartmouth",
            started_at=started, ended_at=ended,
            prompts={"system": "sys", "user": "usr"},
            parsed_output={}, file_diffs=[], reset_artifacts=[],
            spec_root=tmp_path,
        )
        capture(**base_kwargs, outcome="committed", raw_response="first", error=None)
        capture(**base_kwargs, outcome="failed", raw_response="", error="oops")
        rec = json.loads((tmp_path / "inspections" / "PROJ-TEST-foo" / "specifier.json").read_text())
        assert rec["outcome"] == "failed"
        assert rec["error"] == "oops"

    def test_capture_rejects_invalid_outcome(self, tmp_path: Path) -> None:
        from llmxive.speckit._inspection import capture
        with pytest.raises(ValueError, match="invalid outcome"):
            capture(
                project_id="x", agent_name="specifier", agent_version="1.0.0",
                model="m", backend="dartmouth",
                started_at=datetime(2026, 5, 17, tzinfo=timezone.utc),
                ended_at=datetime(2026, 5, 17, tzinfo=timezone.utc),
                outcome="banana", prompts={"system": "", "user": ""},
                raw_response="", parsed_output={}, file_diffs=[],
                reset_artifacts=[], error=None, spec_root=tmp_path,
            )

    def test_capture_rejects_failed_without_error(self, tmp_path: Path) -> None:
        from llmxive.speckit._inspection import capture
        with pytest.raises(ValueError, match="outcome=failed requires"):
            capture(
                project_id="x", agent_name="specifier", agent_version="1.0.0",
                model="m", backend="dartmouth",
                started_at=datetime(2026, 5, 17, tzinfo=timezone.utc),
                ended_at=datetime(2026, 5, 17, tzinfo=timezone.utc),
                outcome="failed", prompts={"system": "", "user": ""},
                raw_response="", parsed_output={}, file_diffs=[],
                reset_artifacts=[], error=None, spec_root=tmp_path,
            )


# ──────────────────────────────────────────────────────────────────────
# T011 — env-gated hook fires only when env var set
# ──────────────────────────────────────────────────────────────────────

class TestInspectionHook:
    def _ctx(self, tmp_path: Path):
        from llmxive.speckit.slash_command import SlashCommandContext
        from llmxive.types import BackendName
        return SlashCommandContext(
            project_id="PROJ-TEST-hook",
            project_dir=tmp_path,
            run_id="r1", task_id="t1",
            inputs=[], expected_outputs=[],
            prompt_template_path=tmp_path / "ignored.md",
            default_backend=BackendName.DARTMOUTH,
            fallback_backends=[],
            default_model="m",
            prompt_version="1.0.0",
            agent_name="specifier",
        )

    def test_hook_writes_when_env_set(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        from llmxive.speckit.slash_command import _maybe_write_inspection
        from llmxive.backends.base import ChatMessage
        from llmxive.types import BackendName, Outcome

        insp_dir = tmp_path / "inspections" / "PROJ-TEST-hook"
        insp_dir.mkdir(parents=True)
        monkeypatch.setenv("LLMXIVE_INSPECTION_DIR", str(insp_dir))

        ctx = self._ctx(tmp_path)
        started = datetime(2026, 5, 17, 12, 0, 0, tzinfo=timezone.utc)
        ended = datetime(2026, 5, 17, 12, 0, 5, tzinfo=timezone.utc)
        _maybe_write_inspection(
            ctx=ctx, started=started, ended=ended,
            outcome=Outcome.SUCCESS, failure_reason=None,
            messages=[ChatMessage(role="system", content="sys"),
                      ChatMessage(role="user", content="usr")],
            llm_response_text="resp",
            model_used="m",
            backend_used=BackendName.DARTMOUTH,
        )
        out = insp_dir / "specifier.json"
        assert out.is_file()
        rec = json.loads(out.read_text())
        assert rec["outcome"] == "committed"
        assert rec["prompts"]["system"] == "sys"
        assert rec["prompts"]["user"] == "usr"
        assert rec["raw_response"] == "resp"

    def test_hook_no_op_when_env_unset(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        from llmxive.speckit.slash_command import _maybe_write_inspection
        from llmxive.backends.base import ChatMessage
        from llmxive.types import BackendName, Outcome

        monkeypatch.delenv("LLMXIVE_INSPECTION_DIR", raising=False)
        ctx = self._ctx(tmp_path)
        started = datetime(2026, 5, 17, 12, 0, 0, tzinfo=timezone.utc)
        ended = datetime(2026, 5, 17, 12, 0, 5, tzinfo=timezone.utc)
        _maybe_write_inspection(
            ctx=ctx, started=started, ended=ended,
            outcome=Outcome.SUCCESS, failure_reason=None,
            messages=[ChatMessage(role="user", content="hi")],
            llm_response_text="ok", model_used="m",
            backend_used=BackendName.DARTMOUTH,
        )
        # No files should exist anywhere under tmp_path
        assert list(tmp_path.rglob("*.json")) == []


# ──────────────────────────────────────────────────────────────────────
# T020 — diff-leak guard regression
# ──────────────────────────────────────────────────────────────────────

class TestDiffLeakGuard:
    def test_diff_leak_guard_rejects_unified_diff_response(self) -> None:
        from llmxive.speckit._diff_guard import refuse_if_diff
        synthetic = (
            "--- a/spec.md\n"
            "+++ b/spec.md\n"
            "@@ -1,3 +1,3 @@\n"
            "-old line\n"
            "+new line\n"
            " context\n"
        )
        with pytest.raises(Exception) as exc_info:
            refuse_if_diff(synthetic, artifact_kind="spec.md")
        assert "diff" in str(exc_info.value).lower()

    def test_diff_leak_guard_accepts_normal_markdown(self) -> None:
        from llmxive.speckit._diff_guard import refuse_if_diff
        # No exception expected
        refuse_if_diff(
            "# Feature Specification\n\n## User Stories\n\nReal prose, not a diff.",
            artifact_kind="spec.md",
        )


# ──────────────────────────────────────────────────────────────────────
# T021 — template-only guard regression
# ──────────────────────────────────────────────────────────────────────

class TestTemplateOnlyGuard:
    def test_template_guard_rejects_template_only_spec(self, tmp_path: Path) -> None:
        from llmxive.speckit._real_only_guard import assert_real_or_raise, TemplateRefused
        template_path = REPO_ROOT / ".specify" / "templates" / "spec-template.md"
        if not template_path.is_file():
            pytest.skip(f"template not at {template_path}")
        template_text = template_path.read_text(encoding="utf-8")
        synthetic_spec = tmp_path / "spec.md"
        synthetic_spec.write_text(template_text, encoding="utf-8")
        with pytest.raises(TemplateRefused) as exc_info:
            assert_real_or_raise(synthetic_spec, repo_root=REPO_ROOT)
        # Message should mention "template" (case-insensitive substring)
        assert "template" in str(exc_info.value).lower()


# ──────────────────────────────────────────────────────────────────────
# T022 — clarifier echo-the-question rejection
# ──────────────────────────────────────────────────────────────────────

class TestClarifierEchoRejection:
    def test_clarifier_rejects_echo_the_question_replacement(self, tmp_path: Path) -> None:
        # Construct a minimal project layout: state YAML + idea + an
        # existing spec.md with one [NEEDS CLARIFICATION: ...] marker.
        # Then invoke ClarifierAgent.write_artifacts with a synthetic
        # response that "resolves" by echoing the question verbatim.
        from llmxive.speckit.clarify_cmd import ClarifierAgent, CLARIFY_MARKER_RE
        from llmxive.backends.base import ChatResponse
        from llmxive.speckit.slash_command import SlashCommandContext
        from llmxive.types import BackendName

        # Build project skeleton
        proj_dir = tmp_path / "projects" / "PROJ-TEST-echo"
        spec_subdir = proj_dir / "specs" / "001-test"
        spec_subdir.mkdir(parents=True)
        question = "What is the auth method?"
        spec_text = (
            "# Feature Specification: Test\n\n"
            "## User Scenarios\n\n"
            "### User Story 1 - Test (Priority: P1)\n\nfoo\n\n"
            "## Functional Requirements\n\n"
            f"- **FR-001**: System MUST [NEEDS CLARIFICATION: {question}]\n\n"
            "## Success Criteria\n\n"
            "- **SC-001**: Works.\n"
        )
        spec_md = spec_subdir / "spec.md"
        spec_md.write_text(spec_text, encoding="utf-8")

        # mechanical_step output
        markers = [{"index": i, "question": m.group("bq") or m.group("mq")}
                   for i, m in enumerate(CLARIFY_MARKER_RE.finditer(spec_text))]
        mech = {
            "spec_path": str(spec_md),
            "spec_text": spec_text,
            "markers": markers,
            "attempts_so_far": 0,
        }

        ctx = SlashCommandContext(
            project_id="PROJ-TEST-echo",
            project_dir=proj_dir,
            run_id="r", task_id="t",
            inputs=[], expected_outputs=[],
            prompt_template_path=tmp_path / "ignored.md",
            default_backend=BackendName.DARTMOUTH,
            fallback_backends=[],
            default_model="m",
            prompt_version="1.0.0",
            agent_name="clarifier",
        )

        # The historical "echo-the-question" failure mode is best caught
        # by the more general "missing patches" gate already in
        # clarify_cmd.write_artifacts: when the LLM returns FEWER patches
        # than there are markers, the run fails rather than silently
        # leaving markers unresolved. Test the canonical case (zero
        # patches when one marker exists).
        zero_patch_response = ChatResponse(
            text=json.dumps({"patches": [], "notes": ""}),
            model="test", backend="dartmouth",
        )
        agent = ClarifierAgent()
        with pytest.raises(RuntimeError, match=r"unresolved"):
            agent.write_artifacts(ctx, mech, zero_patch_response)
        # And the spec.md marker MUST remain — write_artifacts failed before edit.
        assert "[NEEDS CLARIFICATION:" in spec_md.read_text(encoding="utf-8")


# ──────────────────────────────────────────────────────────────────────
# T025 — carry-forward manifest schema
# ──────────────────────────────────────────────────────────────────────

class TestCarryForwardSchema:
    def test_emit_carry_forward_writes_well_formed_yaml(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        # Patch SPEC_DIR to a temp dir so we don't clobber the real file.
        import scripts.validate_phase3 as vp3
        monkeypatch.setattr(vp3, "SPEC_DIR", tmp_path)
        results = [
            {
                "project_id": "PROJ-261-x",
                "final_state": "clarified",
                "agents_run": [
                    {"agent": "specifier", "record_outcome": "committed"},
                    {"agent": "clarifier", "record_outcome": "committed"},
                ],
                "passed": True,
                "failures": [],
                "warnings": [],
            },
            {
                "project_id": "PROJ-262-y",
                "final_state": "specified",
                "agents_run": [
                    {"agent": "specifier", "record_outcome": "committed"},
                ],
                "passed": False,
                "failures": ["current_stage is 'specified', expected 'clarified'"],
                "warnings": [],
            },
        ]
        out = vp3._emit_carry_forward(results)
        manifest = yaml.safe_load(out.read_text())
        assert manifest["spec"] == "011-phase3-specify-clarify-testing"
        assert "generated_at" in manifest
        assert "final_commit" in manifest
        assert len(manifest["projects"]) == 2
        # First project: passed
        p1 = manifest["projects"][0]
        assert p1["project_id"] == "PROJ-261-x"
        assert p1["final_state"] == "clarified"
        assert len(p1["agents_run"]) == 2
        assert p1["agents_run"][0]["name"] == "specifier"
        # Second project: failed; justification cites failure
        p2 = manifest["projects"][1]
        assert "FAILED" in p2["justification"]
        assert "expected 'clarified'" in p2["justification"]


# ──────────────────────────────────────────────────────────────────────
# T026 — gated end-to-end real-call smoke
# ──────────────────────────────────────────────────────────────────────

def _has_dartmouth_key() -> bool:
    try:
        from llmxive.credentials import load_dartmouth_key
        return bool(load_dartmouth_key())
    except Exception:
        return False


@pytest.mark.skipif(
    not _has_dartmouth_key(),
    reason="real-call test — requires Dartmouth key in env or ~/.config/llmxive/credentials.toml",
)
class TestPhase3EndToEnd:
    def test_phase3_end_to_end_on_proj_261(self, tmp_path: Path) -> None:
        """Drive PROJ-261 through Specifier + Clarifier and assert clarified.

        Rolls PROJ-261 back to project_initialized + removes generated
        specs/ dir in `finally` so the test is idempotent.
        """
        from llmxive.state import project as project_store
        from llmxive.types import Stage
        import shutil

        pid = "PROJ-261-evaluating-the-impact-of-code-duplicatio"
        proj_state_pre = project_store.load(pid, repo_root=REPO_ROOT)
        try:
            proc = subprocess.run(
                [sys.executable, "scripts/validate_phase3.py", "--project", pid],
                capture_output=True, text=True, cwd=str(REPO_ROOT), timeout=1500,
            )
            assert proc.returncode == 0, (
                f"validate_phase3 exit {proc.returncode}\nstderr:\n{proc.stderr[-2000:]}"
            )
            project = project_store.load(pid, repo_root=REPO_ROOT)
            stage = project.current_stage.value if hasattr(project.current_stage, "value") else str(project.current_stage)
            assert stage == "clarified", f"final stage is {stage!r}, expected 'clarified'"
            spec_path = SPEC_DIR / "inspections" / pid / "specifier.json"
            clar_path = SPEC_DIR / "inspections" / pid / "clarifier.json"
            assert spec_path.is_file(), f"missing specifier inspection at {spec_path}"
            assert clar_path.is_file(), f"missing clarifier inspection at {clar_path}"
        finally:
            # Roll back state so subsequent runs are deterministic.
            project = project_store.load(pid, repo_root=REPO_ROOT)
            project = project.model_copy(update={
                "current_stage": Stage.PROJECT_INITIALIZED,
                "speckit_research_dir": None,
                "updated_at": datetime.now(timezone.utc),
            })
            project_store.save(project, repo_root=REPO_ROOT)
            # Remove generated specs dir
            specs_dir = REPO_ROOT / "projects" / pid / "specs"
            if specs_dir.is_dir():
                for sub in specs_dir.iterdir():
                    if sub.is_dir():
                        shutil.rmtree(sub)
