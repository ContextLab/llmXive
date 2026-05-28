"""Unit tests for the implementer failsafe diagnostic mode
(spec 015 T042 / FR-034).

Verifies the classifier's pattern catalogue + the Concern synthesis +
the round-trip from FailureClassification → KickbackRecord → adapter."""

from __future__ import annotations

from pathlib import Path

import yaml

from llmxive.agents.implementer_diagnostics import (
    FailureClass,
    classify_failure,
    failure_to_concern,
    synth_kickback_from_failure,
)
from llmxive.convergence.revision_adapter import kickback_to_revision_spec
from llmxive.convergence.types import Severity


class TestClassifyFailureBrokenLatex:
    def test_classifies_undefined_control_sequence(self) -> None:
        log = """
        ! Undefined control sequence.
        l.12 \\foobar
        """
        c = classify_failure(log)
        assert c.cls == FailureClass.BROKEN_LATEX
        assert c.suggested_severity == Severity.METHODOLOGY

    def test_classifies_emergency_stop(self) -> None:
        log = "Emergency stop.\nl.34 Whatever."
        c = classify_failure(log)
        assert c.cls == FailureClass.BROKEN_LATEX
        assert c.suggested_severity == Severity.METHODOLOGY

    def test_classifies_lualatex_exit(self) -> None:
        log = "lualatex failed: exit code 1"
        c = classify_failure(log)
        assert c.cls == FailureClass.BROKEN_LATEX


class TestClassifyFailureMissingTool:
    def test_classifies_module_not_found(self) -> None:
        log = "ModuleNotFoundError: No module named 'matplotlib'"
        c = classify_failure(log)
        assert c.cls == FailureClass.MISSING_TOOL
        assert c.suggested_severity == Severity.SCIENCE


class TestClassifyFailureModelError:
    def test_classifies_timeout(self) -> None:
        log = "TimeoutError: read timed out"
        c = classify_failure(log)
        assert c.cls == FailureClass.MODEL_ERROR
        assert c.suggested_severity == Severity.SCIENCE

    def test_classifies_rate_limit(self) -> None:
        log = "HTTP 429: rate-limit exceeded"
        c = classify_failure(log)
        assert c.cls == FailureClass.MODEL_ERROR

    def test_classifies_context_length(self) -> None:
        log = "context_length_exceeded: 32k tokens > 8k budget"
        c = classify_failure(log)
        assert c.cls == FailureClass.MODEL_ERROR


class TestClassifyFailureParseError:
    def test_classifies_json_decode_error(self) -> None:
        log = "json.decoder.JSONDecodeError: Expecting value at line 1"
        c = classify_failure(log)
        assert c.cls == FailureClass.PARSE_ERROR
        assert c.suggested_severity == Severity.METHODOLOGY

    def test_classifies_no_match(self) -> None:
        log = "no-match: search string not found"
        c = classify_failure(log)
        assert c.cls == FailureClass.PARSE_ERROR

    def test_classifies_did_not_emit_parseable_json(self) -> None:
        log = "LLM did not emit a parseable JSON edit"
        c = classify_failure(log)
        assert c.cls == FailureClass.PARSE_ERROR


class TestClassifyFailureUnknown:
    def test_blank_log_is_unknown(self) -> None:
        c = classify_failure("")
        assert c.cls == FailureClass.UNKNOWN
        assert c.suggested_severity == Severity.FATAL

    def test_random_garbage_is_unknown(self) -> None:
        c = classify_failure("zylophone purplebagel quasimodorant")
        assert c.cls == FailureClass.UNKNOWN


class TestFailureToConcernSynthesis:
    def test_concern_carries_classification_label(self) -> None:
        cls = classify_failure("! LaTeX Error: somthing")
        concern = failure_to_concern(
            cls, artifact_path="projects/PROJ-100-test/paper/source/main.tex",
        )
        assert "[failsafe-diagnostic:broken_latex]" in concern.text
        assert concern.severity == Severity.METHODOLOGY
        assert concern.artifact == "projects/PROJ-100-test/paper/source/main.tex"
        assert concern.reviewer == "implementer_diagnostics"

    def test_unknown_refuses_to_synthesize(self) -> None:
        cls = classify_failure("")
        import pytest
        with pytest.raises(ValueError, match="UNKNOWN"):
            failure_to_concern(cls, artifact_path="x")

    def test_deterministic_id_for_same_evidence(self) -> None:
        cls1 = classify_failure("! LaTeX Error: missing $")
        cls2 = classify_failure("! LaTeX Error: missing $")
        c1 = failure_to_concern(cls1, artifact_path="x")
        c2 = failure_to_concern(cls2, artifact_path="x")
        assert c1.id == c2.id


class TestRoundTripThroughAdapter:
    """The diagnostic mode's round-trip MUST produce a real
    auto-revisions round dir the next implementer pass can pick up."""

    def test_synth_kickback_writes_round_dir(self, tmp_path: Path) -> None:
        log = "! LaTeX Error: Something is broken"
        cls = classify_failure(log)
        kb = synth_kickback_from_failure(
            cls,
            project_id="PROJ-100-test",
            artifact_path="projects/PROJ-100-test/paper/source/main.tex",
            round_num=5,
        )
        spec_dir = kickback_to_revision_spec(
            kb, project_id="PROJ-100-test", repo_root=tmp_path, round_num=5,
        )
        assert spec_dir.name == "round-5"
        # The diagnosed problem surfaces as a task.
        tasks = (spec_dir / "tasks.md").read_text()
        assert "failsafe-diagnostic" in tasks
        assert "broken_latex" in tasks

    def test_result_yaml_records_diagnosis(self, tmp_path: Path) -> None:
        log = "ModuleNotFoundError: No module named 'numpy'"
        cls = classify_failure(log)
        kb = synth_kickback_from_failure(
            cls,
            project_id="PROJ-100-test",
            artifact_path="projects/PROJ-100-test/paper/source/main.tex",
            round_num=2,
        )
        spec_dir = kickback_to_revision_spec(
            kb, project_id="PROJ-100-test", repo_root=tmp_path, round_num=2,
        )
        result = yaml.safe_load((spec_dir / "result.yaml").read_text())
        assert result["worst_severity"] == "science"  # MISSING_TOOL → SCIENCE
        assert "implementer failsafe diagnostic: missing_tool" in result["kickback_reason"]
