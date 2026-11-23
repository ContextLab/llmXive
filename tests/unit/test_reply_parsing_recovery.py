"""Two reply shapes a live run lost, and what the platform now does with them.

Both come from one acceptance run of a fresh project at the specification
stage (2026-10-11):

* A reviser's self-audit answered with the fenced YAML it was asked for and
  then kept talking ("Audit notes supporting the verdict: ..."). The parser
  only removed a fence that ended on the LAST line, so the whole reply went to
  the YAML scanner, failed on the backtick, and the audit was discarded as
  "OK". That reply said ``ok: true``; one that said ``ok: false`` would have
  lost its problem list the same way.
* The clarifier wrote ``"snippet": \\"...\\"`` -- escaped quotes used as the
  string's delimiters. Neither JSON nor YAML accepts that, the reply was
  coerced to "no patches", and the stage failed and was retried from scratch.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

import llmxive.backends.router as router
from llmxive.agents.grounding_guard import _parse_extraction_reply as parse_cited_claims
from llmxive.backends.base import ChatResponse
from llmxive.claims.extract import _parse_extraction_reply as parse_claims
from llmxive.convergence.revisers._self_consistency import _parse_self_consistency_reply
from llmxive.grounding.entailment import _parse_verdict
from llmxive.speckit.clarify_cmd import ClarifierAgent, _parse_clarifier_response
from llmxive.speckit.slash_command import SlashCommandContext
from llmxive.speckit.yaml_extract import outer_fenced_body
from llmxive.types import BackendName

_REPO_ROOT = Path(__file__).resolve().parents[2]

_PROSE_AFTER = (
    "\n\nAudit notes supporting the verdict:\n\n"
    "- **(a) Resolution**: All seven concerns are genuinely resolved in the "
    'artifact body, not just claimed. FR-012 now states "within 5 minutes".\n'
)


@pytest.mark.parametrize("prefix", ["", "Here is the audit.\n\n"])
def test_audit_followed_by_prose_keeps_its_verdict(prefix: str) -> None:
    result = _parse_self_consistency_reply(prefix + "```yaml\nok: true\nproblems: []\n```" + _PROSE_AFTER)
    assert result.ok is True
    assert result.problems == []


def test_audit_followed_by_prose_keeps_its_problems() -> None:
    reply = (
        "```yaml\nok: false\nproblems:\n"
        '  - "FR-007 still says [deferred] while User Story 2 names 1 %."\n'
        "```" + _PROSE_AFTER
    )
    result = _parse_self_consistency_reply(reply)
    assert result.ok is False
    assert result.problems == ["FR-007 still says [deferred] while User Story 2 names 1 %."]


def test_a_reply_that_is_not_an_audit_is_still_refused() -> None:
    with pytest.raises(ValueError):
        _parse_self_consistency_reply("```yaml\nnew_spec_md: text\n```" + _PROSE_AFTER)


# --- the same fence handling existed in three more reply parsers ------------


def test_entailment_verdict_followed_by_prose_is_not_lost() -> None:
    reply = '```yaml\nstatus: grounded\nevidence: "phi(n) is even for n > 2"\nnote: stated directly\n```'
    plain = _parse_verdict(reply)
    assert plain.status == "grounded"
    # Before: "not_found / unparseable verdict", so a supported claim was flagged.
    assert _parse_verdict(reply + _PROSE_AFTER) == plain


_CLAIMS = (
    "```yaml\nclaims:\n"
    '  - claim_text: "Euler\'s totient is multiplicative"\n'
    '    source: "arXiv:1706.03762"\n'
    '    canonical: "phi is multiplicative"\n'
    '    context: "number theory"\n'
    "```"
)


def test_cited_claims_followed_by_prose_are_the_same_claims() -> None:
    plain = parse_cited_claims(_CLAIMS)
    assert len(plain) == 1
    assert parse_cited_claims(_CLAIMS + _PROSE_AFTER) == plain


def test_extracted_claims_followed_by_prose_are_the_same_claims() -> None:
    plain = parse_claims(_CLAIMS, "specs/001-x/spec.md")
    assert [c.raw_text for c in plain] == ["Euler's totient is multiplicative"]
    after = parse_claims(_CLAIMS + _PROSE_AFTER, "specs/001-x/spec.md")
    assert [(c.claim_id, c.raw_text, c.canonical, c.context) for c in after] == [
        (c.claim_id, c.raw_text, c.canonical, c.context) for c in plain
    ]


def test_a_fence_quoted_inside_the_document_stays_in_it() -> None:
    reply = "```yaml\nnote: |\n  run it as\n  ```\n  python x.py\n  ```\nok: true\n```\nThat is all."
    assert outer_fenced_body(reply) == "note: |\n  run it as\n  ```\n  python x.py\n  ```\nok: true"
    assert outer_fenced_body("ok: true\nproblems: []") == "ok: true\nproblems: []"


# The clarifier reply, trimmed to two patches but otherwise as the model wrote
# it: ordinary strings beside values delimited by backslash-quote.
_ESCAPED_DELIMITERS = r'''{
  "verdict": "resolved",
  "patches": [
    {
      "marker_index": 0,
      "replacement": "- **FR-017**: The `checksum` column is the SHA-256 of the \"other\" fields.\n",
      "evidence": [
        {
          "source": "https://json-schema.org/understanding-json-schema/reference/generic.html",
          "title": "JSON Schema - Generic Keywords",
          "snippet": \"The `required` keyword lists property names; fields such as `checksum` are common.\"
        }
      ]
    },
    {
      "marker_index": 3,
      "replacement": "- **FR-018**: Write `analytic_density_{N}_{p}.json` per scale.\n",
      "evidence": [
        {
          "source": "data-model.md",
          "title": "Data Model Specification",
          "snippet": \"Files named `analytic_density_{N}_{p}.json` with the fields `N`, `p`, `delta`.\"
        }
      ]
    }
  ],
  "remaining_questions": []
}'''


def test_values_delimited_by_escaped_quotes_are_read() -> None:
    report = _parse_clarifier_response(_ESCAPED_DELIMITERS)
    assert report is not None
    assert report["verdict"] == "resolved"
    first, second = report["patches"]
    assert first["marker_index"] == 0
    # An escaped quote INSIDE an ordinary string is still part of the text.
    assert first["replacement"].endswith('SHA-256 of the "other" fields.\n')
    assert first["evidence"][0]["snippet"] == (
        "The `required` keyword lists property names; fields such as `checksum` are common."
    )
    assert second["evidence"][0]["snippet"] == (
        "Files named `analytic_density_{N}_{p}.json` with the fields `N`, `p`, `delta`."
    )


def test_well_formed_reply_with_escaped_quotes_is_unchanged() -> None:
    report = _parse_clarifier_response('{"verdict": "resolved", "notes": "say \\"hi\\", then stop"}')
    assert report == {"verdict": "resolved", "notes": 'say "hi", then stop'}


def test_unreadable_reply_is_not_invented() -> None:
    assert _parse_clarifier_response('{"verdict": "resolved", "patches": [') is None


# --- one re-ask when the reply cannot be read at all -----------------------

_SPEC = """# Feature Specification: A/B test validity

## User Scenarios & Testing

- **US-1** (P1): A reviewer submits a list of A/B-test summary URLs and receives
  a per-summary consistency verdict with the reconstructed p-value.

## Requirements
- **FR-001**: System MUST accept a list of URLs pointing to A/B-test summaries.
- **FR-002**: System MUST reconstruct the expected p-value via a two-proportion
  Z-test for binary conversion metrics.
- **FR-003**: [NEEDS CLARIFICATION: which threshold marks a summary inconsistent?]

### Success Criteria
- **SC-001**: Reconstruction matches a hand-computed reference on 10 worked
  examples to within 1e-6.

## Assumptions
- Summaries report sample size and conversion counts per variant.
"""

_FR003 = (
    "- **FR-003**: System MUST flag a summary inconsistent when the reported and "
    "reconstructed p-values differ by more than 0.05."
)


class _QueueBackend:
    """Serves queued replies in order and records what it was asked."""

    def __init__(self, replies: list[str]) -> None:
        self.replies = list(replies)
        self.calls: list[list] = []

    def chat(self, messages, model=None, **_kwargs):  # type: ignore[no-untyped-def]
        self.calls.append(list(messages))
        if not self.replies:
            raise RuntimeError("_QueueBackend: ran out of replies")
        return ChatResponse(text=self.replies.pop(0), model="m", backend="local")


def _run(tmp_path: Path, monkeypatch, backend: _QueueBackend | None, first_reply: str):
    project = tmp_path / "projects" / "PROJ-701-clarify-reask"
    feature = project / "specs" / "001-x"
    memory = project / ".specify" / "memory"
    feature.mkdir(parents=True)
    memory.mkdir(parents=True)
    spec = feature / "spec.md"
    spec.write_text(_SPEC, encoding="utf-8")
    # The agent reads its prompt from the repository the project lives in.
    prompts = tmp_path / "agents" / "prompts"
    prompts.mkdir(parents=True)
    shutil.copy(_REPO_ROOT / "agents" / "prompts" / "clarifier.md", prompts / "clarifier.md")
    monkeypatch.setattr(ClarifierAgent, "_run_spec_panel", lambda *a, **k: None)
    monkeypatch.setattr(router, "make_backend", lambda *_a, **_k: backend)
    ctx = SlashCommandContext(
        project_id="PROJ-701-clarify-reask", project_dir=project, run_id="r", task_id="t",
        inputs=[], expected_outputs=[],
        prompt_template_path=Path("agents/prompts/clarifier.md"),
        default_backend=BackendName.LOCAL, fallback_backends=[], default_model="m",
        prompt_version="1.0.0", agent_name="clarifier",
    )
    mechanical = {
        "spec_path": str(spec), "spec_text": _SPEC, "memory_dir": str(memory),
        "markers": [{"question": "which threshold marks a summary inconsistent?"}],
        "attempts_so_far": 0,
    }
    reply = ChatResponse(text=first_reply, model="m", backend="local")
    return spec, lambda: ClarifierAgent().write_artifacts(ctx, mechanical, reply)


_TRUNCATED = '{"verdict": "resolved", "patches": [{"marker_index": 0, "replacement": "- **FR-003**: Sys'


def test_unreadable_reply_is_asked_for_again_once(tmp_path, monkeypatch) -> None:
    good = json.dumps({"verdict": "resolved", "patches": [{"marker_index": 0, "replacement": _FR003}]})
    backend = _QueueBackend([good])
    spec, run = _run(tmp_path, monkeypatch, backend, _TRUNCATED)
    assert run()
    assert _FR003 in spec.read_text(encoding="utf-8")
    assert "NEEDS CLARIFICATION" not in spec.read_text(encoding="utf-8")
    assert len(backend.calls) == 1
    *_, sent, correction = backend.calls[0]
    assert "could not be parsed" in correction.content
    # The model is shown what it sent, so it can repair rather than start over.
    assert (sent.role, sent.content) == ("assistant", _TRUNCATED)


def test_second_unreadable_reply_fails_the_attempt(tmp_path, monkeypatch) -> None:
    backend = _QueueBackend([_TRUNCATED])
    spec, run = _run(tmp_path, monkeypatch, backend, _TRUNCATED)
    with pytest.raises(RuntimeError):
        run()
    assert len(backend.calls) == 1, "one re-ask, not a loop"
    assert spec.read_text(encoding="utf-8") == _SPEC


def test_readable_reply_is_never_asked_for_again(tmp_path, monkeypatch) -> None:
    backend = _QueueBackend([])
    good = json.dumps({"verdict": "resolved", "patches": [{"marker_index": 0, "replacement": _FR003}]})
    _spec, run = _run(tmp_path, monkeypatch, backend, good)
    assert run()
    assert backend.calls == []
