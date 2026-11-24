"""The lane's proposal reviser: ONE routed call per revise() (spec 025 slice 1B, Task 5).

Integration, because the call ledger is durable — these need a real git repo. The router
boundary is injected so a specific reply can be scripted; the real routing path is covered
by the Task 3 suite.

The reviser speaks the SAME wire contract as every other reviser in the package
(``RESPONSE_FORMAT_BLOCK`` → ``parse_reviser_response`` → ``build_concern_responses``);
only the DISPATCH is bespoke, because the shared ``run_with_self_consistency`` path makes up
to three LLM calls per ``revise()`` and the proposal ceiling's ``+2``-per-round term pays for
exactly two.
"""

from __future__ import annotations

import json
import subprocess

import pytest

from llmxive.convergence.types import Concern
from llmxive.self_improvement.call_ledger import LaneCallLedger
from llmxive.self_improvement.lane_log import LaneLogConfig, bootstrap_lane_log
from llmxive.self_improvement.route_context import LaneRouteContext

_BUDGET = 50.0  # ONE AttemptConfigured record binds this with the ceiling.


class _Sink:
    def __init__(self):
        self.events = []

    def record(self, event) -> None:
        self.events.append(event)

    def claim_dispatch(self, event) -> bool:
        self.events.append(event)
        return True


class _Budget:
    def reserve(self, credits, *, reservation_id, call_id) -> bool:
        return True

    def release(self, reservation_id) -> None:
        pass

    def mark_retained(self, reservation_id) -> None:
        pass


@pytest.fixture
def repo(tmp_path):
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    for k, v in (("user.email", "t@t"), ("user.name", "t")):
        subprocess.run(["git", "config", k, v], cwd=str(tmp_path), check=True)
    bootstrap_lane_log(tmp_path, config=LaneLogConfig())
    return tmp_path


def _ctx(repo, ceiling=10):
    ledger = LaneCallLedger(repo=repo, problem_id="P1", attempt_id="A1", call_ceiling=ceiling,
                            attempt_budget_credits=_BUDGET, actor="proposer",
                            clock=lambda: "2026-07-25T00:00:00+00:00", config=LaneLogConfig())
    return LaneRouteContext(
        repo=repo, problem_id="P1", attempt_id="A1", actor="proposer",
        clock=lambda: "2026-07-25T00:00:00+00:00", route_audit=_Sink(),
        reservation_authority=_Budget(), call_ledger=ledger,
    )


def _concern(cid="c1"):
    return Concern(id=cid, reviewer="worthwhile-improvement", severity="requirement",
                   artifact="proposal.md", text="Blast radius is unbounded.")


def _body(proposal="# Revised\n\nScoped to one module.", *, responses=None, cid="c1"):
    """A reply in the package's SHARED two-part contract: a small fenced ```json change-log,
    then the full artifact VERBATIM between ===BEGIN_ARTIFACT=== markers."""
    if responses is None:
        responses = [{"concern_id": cid, "response": "Scoped it.",
                      "what_changed": "Added a blast-radius section.",
                      "artifacts_changed": ["proposal.md"]}]
    return (
        "```json\n" + json.dumps({"responses": responses}) + "\n```\n\n"
        "===BEGIN_ARTIFACT proposal.md===\n" + proposal + "\n===END_ARTIFACT===\n"
    )


def _reviser(repo, monkeypatch, fake):
    monkeypatch.setattr("llmxive.convergence.lane_reviser.chat_with_model_fallback", fake)
    from llmxive.convergence.lane_reviser import LaneProposalReviser

    ctx = _ctx(repo)
    return LaneProposalReviser(backend=object(), route_context=ctx), ctx


def _replying(text):
    def _fake(backend, messages, **kw):
        class R:
            pass

        R.text = text
        return R()

    return _fake


# ---- the single-call contract ----


def test_revise_makes_exactly_one_routed_call_with_the_lane_hooks(repo, monkeypatch):
    calls = []

    def _fake(backend, messages, **kw):
        calls.append(kw)

        class R:
            text = _body()

        return R()

    rev, ctx = _reviser(repo, monkeypatch, _fake)
    updated, responses = rev.revise({"proposal.md": "# Original"}, [_concern()])

    # ONE call — NOT the 3-call self-consistency path (that would break the ceiling's +2).
    assert len(calls) == 1 and ctx.calls_used() == 1
    assert calls[0]["route_audit"] is ctx.route_audit
    assert calls[0]["reservation_authority"] is ctx.reservation_authority
    assert calls[0]["route_id"]
    assert calls[0].get("independence_against") is None  # the producer has no constraint
    # A revision turn REGENERATES the whole proposal: it needs the GENERATION budget, not
    # the reasoning one. At 32K a reasoning model's hidden CoT eats the budget before the
    # artifact block closes and the reply truncates into a malformed parse — spec-023
    # defect #20 (revisers/_self_consistency.py:154-160).
    from llmxive.backends.router import GENERATION_MAX_TOKENS, REASONING_MAX_TOKENS

    assert calls[0]["max_tokens"] == GENERATION_MAX_TOKENS != REASONING_MAX_TOKENS
    assert updated["proposal.md"].startswith("# Revised")
    assert [r.concern_id for r in responses] == ["c1"]


def test_the_engines_second_attempt_is_a_new_logical_call(repo, monkeypatch):
    # engine.py:519-533 re-invokes revise() with BYTE-IDENTICAL arguments after a malformed
    # reply. That is a new logical call (the first already dispatched), so it must get its own
    # route_id and its own ceiling charge — which is exactly what the ceiling's +2 pays for.
    # Without next_operation_id it would replay the first claim and be refused at the gate.
    calls = []

    def _fake(backend, messages, **kw):
        calls.append(kw)

        class R:
            text = _body()

        return R()

    rev, ctx = _reviser(repo, monkeypatch, _fake)
    args = ({"proposal.md": "# Original"}, [_concern()])
    rev.revise(*args)
    rev.revise(*args)

    assert calls[0]["route_id"] != calls[1]["route_id"]
    assert ctx.calls_used() == 2


# ---- the malformed-reply contract the ENGINE recognizes ----


@pytest.mark.parametrize("text, marker", [
    ("no json block and no artifact markers here", "parseable"),   # nothing to parse
    ('```json\n{"responses": []}\n```', "no usable"),              # parsed, but no artifact
])
def test_malformed_replies_raise_the_ENGINE_RECOGNIZED_error(repo, monkeypatch, text, marker):
    # F3: the engine catches RuntimeError (engine.py:527) and then classifies with
    # is_malformed_reply_error, which keys on "parseable" / "no usable". A ValueError —
    # or a RuntimeError with any other message — skips the retry and/or files a spurious
    # engine-failure issue.
    from llmxive.convergence.revisers._reviser_response import is_malformed_reply_error

    rev, _ = _reviser(repo, monkeypatch, _replying(text))
    with pytest.raises(RuntimeError) as excinfo:
        rev.revise({"proposal.md": "# Original"}, [_concern()])
    assert marker in str(excinfo.value)
    assert is_malformed_reply_error(excinfo.value)   # the SSoT classifier accepts it


def test_an_unanswered_concern_pads_missing_and_keeps_the_revision(repo, monkeypatch):
    # MAINTAINER-DECIDED 2026-07-28: the SSoT governs. Discarding a revision because ONE
    # concern of many went unanswered would throw away every fix it DID make. Instead
    # build_concern_responses pads "<missing>", and engine.py:627 then forces that concern
    # open at R3 deterministically — no re-reviewer leniency can mark it resolved, so the
    # honesty guarantee is identical while the useful work survives.
    rev, _ = _reviser(repo, monkeypatch, _replying(_body(cid="WRONG-ID")))
    updated, responses = rev.revise(
        {"proposal.md": "# Original"}, [_concern("c1"), _concern("c2")]
    )

    assert updated["proposal.md"].startswith("# Revised"), "the revision must be KEPT"
    by_id = {r.concern_id: r for r in responses}
    assert set(by_id) == {"c1", "c2"}, "exactly one response per raised concern"
    # "<missing>" is not decoration: engine.py:627-628 keys on this exact string.
    assert by_id["c1"].response == "<missing>"
    assert by_id["c2"].response == "<missing>"


def test_empty_response_fields_become_the_shared_placeholder(repo, monkeypatch):
    # ConcernResponse.response/what_changed are min_length=1 (types.py:184-185), so passing
    # the model's omitted field through as "" raises a pydantic ValidationError — which is
    # NOT a RuntimeError, so it would skip the engine's retry AND escape the run with no
    # provenance. build_concern_responses substitutes "<empty>", the same as every other
    # reviser.
    reply = _body(responses=[{"concern_id": "c1", "response": "", "what_changed": "   "}])
    rev, _ = _reviser(repo, monkeypatch, _replying(reply))
    _, responses = rev.revise({"proposal.md": "# Original"}, [_concern()])

    assert [r.response for r in responses] == ["<empty>"]
    assert [r.what_changed for r in responses] == ["<empty>"]


def test_a_verbatim_markdown_proposal_survives_the_round_trip(repo, monkeypatch):
    # WHY the delimited contract rather than {"proposal": "<markdown>"}: a proposal is a
    # document containing quotes, backslashes, $ and fenced code. Embedding it in a JSON
    # string re-introduces the escaping failures the ===BEGIN_ARTIFACT=== markers exist to
    # eliminate (_reviser_response.py:85-86 — the body is taken literally).
    tricky = (
        "# Revised\n\n"
        'He said "no \\ escape" and $PATH stayed intact.\n\n'
        "```python\n"
        'print({"nested": "json-ish", "backslash": "\\\\"})\n'
        "```\n\n"
        "Trailing prose."
    )
    rev, _ = _reviser(repo, monkeypatch, _replying(_body(tricky)))
    updated, _ = rev.revise({"proposal.md": "# Original"}, [_concern()])

    assert updated["proposal.md"] == tricky


def test_other_artifacts_are_carried_through_untouched(repo, monkeypatch):
    rev, _ = _reviser(repo, monkeypatch, _replying(_body()))
    updated, _ = rev.revise(
        {"proposal.md": "# Original", "notes.md": "keep me"}, [_concern()]
    )
    assert updated["notes.md"] == "keep me"


def test_conforms_to_the_reviser_protocol(repo):
    from llmxive.convergence.lane_reviser import LaneProposalReviser
    from llmxive.convergence.types import Reviser

    assert isinstance(LaneProposalReviser(backend=object(), route_context=_ctx(repo)), Reviser)
