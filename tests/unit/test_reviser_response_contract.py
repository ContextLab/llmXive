"""Unit tests for the shared delimited reviser-response contract.

These exercise ``_reviser_response.parse_reviser_response`` directly — the
robustness fix for the spec-015 convergence-reviser bug where embedding a
large document as a JSON STRING value crashed ``json.loads`` on a single
unescaped quote inside the body (observed live:
``Expecting ',' delimiter ... char 19455``).

Two contracts are covered:

* the NEW delimited format (``===BEGIN_ARTIFACT <path>=== ... ===END_ARTIFACT===``)
  with a document body full of quotes / ``$`` / backslashes / newlines that
  WOULD have broken a bare ``json.loads`` of an embedded JSON string; and
* the LEGACY ``new_*_md`` / ``updated_artifacts`` JSON, which must still parse.
"""

from __future__ import annotations

import json

import pytest

from llmxive.convergence.revisers._reviser_response import (
    RESPONSE_FORMAT_BLOCK,
    build_concern_responses,
    parse_reviser_response,
)
from llmxive.convergence.types import Concern, Severity

# A body that is hostile to JSON-string embedding: unescaped double quotes,
# a literal backslash, a ``$`` (LaTeX-ish), and multiple newlines.
_HOSTILE_BODY = (
    "# Spec\n\n"
    'He said "this is fine" and then wrote $E = mc^2$.\n'
    "A path: C:\\Users\\x and a regex: \\d+ matches digits.\n\n"
    '## Section with a "quoted heading"\n'
    "- bullet with trailing backslash \\\n"
    "Done.\n"
)


def _concerns() -> list[Concern]:
    return [
        Concern(
            id="C1", reviewer="testability", severity=Severity.WRITING,
            artifact="specs/000-x/spec.md", location="X", text="fix X",
        ),
        Concern(
            id="C2", reviewer="scope", severity=Severity.REQUIREMENT,
            artifact="specs/000-x/spec.md", location="Y", text="fix Y",
        ),
    ]


def test_delimited_extracts_body_that_would_break_json_loads():
    """The hostile body, if embedded as a JSON string and json.loads'd raw,
    would crash. The delimited contract takes it VERBATIM — no escaping."""
    path = "specs/000-x/spec.md"
    # Prove the precondition: the hostile body embedded naively (unescaped)
    # into a JSON string literal is NOT valid JSON.
    naive = '{"new_spec_md": "' + _HOSTILE_BODY + '"}'
    with pytest.raises(json.JSONDecodeError):
        json.loads(naive)

    reply = (
        "```json\n"
        '{"responses": [{"concern_id": "C1", "response": "did X", '
        '"what_changed": "edited", "artifacts_changed": ["' + path + '"]}]}\n'
        "```\n\n"
        f"===BEGIN_ARTIFACT {path}===\n"
        f"{_HOSTILE_BODY}\n"
        "===END_ARTIFACT===\n"
    )
    artifacts, responses = parse_reviser_response(reply, expected_artifacts=[path])
    assert artifacts == {path: _HOSTILE_BODY}
    assert responses == [
        {
            "concern_id": "C1",
            "response": "did X",
            "what_changed": "edited",
            "artifacts_changed": [path],
        }
    ]


def test_delimited_multiple_artifacts():
    reply = (
        "```json\n{\"responses\": []}\n```\n"
        "===BEGIN_ARTIFACT a/plan.md===\nplan body\nline2\n===END_ARTIFACT===\n"
        "===BEGIN_ARTIFACT a/research.md===\nresearch body\n===END_ARTIFACT===\n"
    )
    artifacts, responses = parse_reviser_response(
        reply, expected_artifacts=["a/plan.md", "a/research.md"]
    )
    assert artifacts == {
        "a/plan.md": "plan body\nline2",
        "a/research.md": "research body",
    }
    assert responses == []


def test_delimited_tolerates_two_equals_delimiter_run():
    """Regression (PROJ-552 plan-stage kickback loop): reasoning models emit the
    ``=`` run NON-deterministically as two or three. The strict 3-``=`` regex
    extracted ZERO artifacts whenever a sample used two → the entire revision was
    discarded, every concern padded ``<missing>``, and the plan panel kicked back.
    The delimiter must tolerate ``={2,}``. Body mirrors the real PROJ-552 schema
    (``["number", "null"]`` — JSON-hostile, taken verbatim by the delimited form)."""
    path = "specs/004-x/contracts/knot_record.schema.yaml"
    body = 'type: ["number", "null"]\nminimum: 0'
    reply = (
        '```json\n{"responses": [{"concern_id": "C1", "response": "fixed", '
        '"what_changed": "edited schema", "artifacts_changed": ["' + path + '"]}]}\n'
        "```\n\n"
        f"==BEGIN_ARTIFACT {path}==\n{body}\n==END_ARTIFACT==\n"
    )
    artifacts, responses = parse_reviser_response(reply, expected_artifacts=[path])
    assert artifacts == {path: body}
    assert responses and responses[0]["concern_id"] == "C1"


def test_delimited_tolerates_mixed_equals_runs_in_one_reply():
    """Two artifacts in one reply, one framed with two ``=`` and one with three —
    both must extract (the model is not internally consistent within a reply)."""
    reply = (
        '```json\n{"responses": []}\n```\n'
        "==BEGIN_ARTIFACT a/plan.md==\nplan body\n==END_ARTIFACT==\n"
        "===BEGIN_ARTIFACT a/research.md===\nresearch body\n===END_ARTIFACT===\n"
    )
    artifacts, _responses = parse_reviser_response(
        reply, expected_artifacts=["a/plan.md", "a/research.md"]
    )
    assert artifacts == {"a/plan.md": "plan body", "a/research.md": "research body"}


def test_delimited_responses_parse_leniently_with_raw_newline():
    """A change-log JSON with a raw (unescaped) newline inside a string value
    must still parse via the lenient repair path."""
    path = "specs/000-x/spec.md"
    reply = (
        '```json\n{"responses": [{"concern_id": "C1", "response": "line one\n'
        'line two", "what_changed": "x", "artifacts_changed": []}]}\n```\n'
        f"===BEGIN_ARTIFACT {path}===\nbody\n===END_ARTIFACT===\n"
    )
    artifacts, responses = parse_reviser_response(reply, expected_artifacts=[path])
    assert artifacts == {path: "body"}
    assert len(responses) == 1
    assert responses[0]["concern_id"] == "C1"


def test_legacy_single_doc_new_spec_md():
    path = "specs/000-x/spec.md"
    reply = json.dumps(
        {
            "new_spec_md": "# revised spec\nbody\n",
            "responses": [
                {"concern_id": "C1", "response": "r", "what_changed": "w"}
            ],
        }
    )
    artifacts, responses = parse_reviser_response(reply, expected_artifacts=[path])
    assert artifacts == {path: "# revised spec\nbody\n"}
    assert responses[0]["concern_id"] == "C1"


def test_legacy_multi_doc_updated_artifacts():
    reply = json.dumps(
        {
            "updated_artifacts": {"a/plan.md": "# plan v2"},
            "responses": [],
        }
    )
    artifacts, responses = parse_reviser_response(
        reply, expected_artifacts=["a/plan.md", "a/research.md"]
    )
    assert artifacts == {"a/plan.md": "# plan v2"}
    assert responses == []


def test_legacy_parsed_but_no_doc_returns_empty_artifacts():
    """A parseable reply with no doc field returns ({}, responses) so the
    caller can raise its own 'no usable <field>' message — NOT a crash."""
    reply = json.dumps({"responses": []})
    artifacts, responses = parse_reviser_response(
        reply, expected_artifacts=["specs/000-x/spec.md"]
    )
    assert artifacts == {}
    assert responses == []


def test_total_failure_raises_runtimeerror():
    """No delimited markers AND not parseable as JSON/YAML at all → raise."""
    with pytest.raises(RuntimeError, match="===BEGIN_ARTIFACT"):
        parse_reviser_response(
            "this is not json: and: not: valid: {[}",
            expected_artifacts=["specs/000-x/spec.md"],
        )


def test_response_format_block_documents_both_parts():
    assert "===BEGIN_ARTIFACT" in RESPONSE_FORMAT_BLOCK
    assert "===END_ARTIFACT===" in RESPONSE_FORMAT_BLOCK
    assert "responses" in RESPONSE_FORMAT_BLOCK


def test_build_concern_responses_pads_missing_honestly():
    responses_raw = [
        {"concern_id": "C1", "response": "fixed", "what_changed": "did"}
    ]
    out = build_concern_responses(
        responses_raw, _concerns(), default_artifacts=["specs/000-x/spec.md"]
    )
    by_id = {r.concern_id: r for r in out}
    assert by_id["C1"].response == "fixed"
    assert by_id["C1"].artifacts_changed == ["specs/000-x/spec.md"]
    assert by_id["C2"].response == "<missing>"
    assert "no response" in by_id["C2"].what_changed.lower()
    # Observability: a partial miss names the concerns the reviser DID answer
    # so the trail distinguishes a skip from a total parse-to-zero.
    assert "C1" in by_id["C2"].what_changed


def test_build_concern_responses_all_missing_records_parse_to_zero_reason():
    """When the whole reply parses to zero per-concern responses (the
    PROJ-552 plan-009 R2 shape), every padded entry must say SO in the
    trail — not the generic skip message (notes/spec-015 observability
    follow-up)."""
    out = build_concern_responses([], _concerns())
    assert all(r.response == "<missing>" for r in out)
    for r in out:
        assert "ZERO per-concern responses" in r.what_changed


def test_delimited_path_with_crlf_line_endings():
    """Models sometimes emit CRLF. The markers must still match and the body
    is captured without the marker lines."""
    path = "specs/000-x/spec.md"
    reply = (
        "```json\r\n{\"responses\": []}\r\n```\r\n"
        f"===BEGIN_ARTIFACT {path}===\r\nbody line\r\nsecond\r\n===END_ARTIFACT===\r\n"
    )
    artifacts, _ = parse_reviser_response(reply, expected_artifacts=[path])
    assert path in artifacts
    assert "body line" in artifacts[path]
    assert "BEGIN_ARTIFACT" not in artifacts[path]


def test_run_pass_with_artifact_retry_corrects_zero_artifact_reply():
    """Spec 023 defect #13 (observed live on PROJ-552's plan panel): under
    a heavy concern load the model emits the change-log but ZERO artifact
    blocks. One corrective re-pass with the explicit re-prompt recovers."""
    from llmxive.convergence.revisers._reviser_response import (
        MISSING_ARTIFACTS_REPROMPT,
        run_pass_with_artifact_retry,
    )

    calls: list[str] = []

    def run_pass(extra: str = ""):
        calls.append(extra)
        if len(calls) == 1:
            raise RuntimeError(
                "PlanReviser: response JSON has no usable "
                "'updated_artifacts' map; got: 0 artifacts"
            )
        return {"a/plan.md": "fixed"}, []

    arts, responses = run_pass_with_artifact_retry(run_pass, reviser_name="PlanReviser")
    assert arts == {"a/plan.md": "fixed"}
    assert calls == ["", MISSING_ARTIFACTS_REPROMPT]


def test_run_pass_with_artifact_retry_propagates_other_errors():
    from llmxive.backends.base import BackendUnavailable
    from llmxive.convergence.revisers._reviser_response import (
        run_pass_with_artifact_retry,
    )

    def outage(extra: str = ""):
        raise BackendUnavailable("endpoint down")

    with pytest.raises(BackendUnavailable):
        run_pass_with_artifact_retry(outage, reviser_name="X")

    def config_error(extra: str = ""):
        raise RuntimeError("response tried to write artifacts outside the plan set")

    with pytest.raises(RuntimeError, match="outside the plan set"):
        run_pass_with_artifact_retry(config_error, reviser_name="X")
