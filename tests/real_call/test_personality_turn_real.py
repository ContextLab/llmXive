"""One bounded REAL turn against a live free model, on a disposable fixture.

The 2026-10-09 audit's pilot made 18 real calls to establish whether persona
framing adds anything; this is not that. It is the much smaller question the
redesign has to answer before the lane is re-enabled: does a real free model,
given ONE artifact it can actually read, return a parseable comment-or-abstain
grounded in that artifact — or does it do what the old lane did and critique
something that is not there?

Disposable: the fixture repo is a tmp_path, nothing is committed, and the
project is the shared CTCF fixture. Gated by LLMXIVE_REAL_TESTS=1.
"""

from __future__ import annotations

import time

import pytest

from llmxive.agents import personality as p
from llmxive.agents import personality_turn as pt
from tests.personality_fixture import make_repo


@pytest.fixture(scope="module")
def credential() -> str:
    from llmxive.credentials import load_dartmouth_key

    key = load_dartmouth_key()
    if not key:
        pytest.skip("no Dartmouth credential available")
    return key


def test_a_real_turn_is_grounded_in_the_artifact_it_was_given(tmp_path, credential):
    repo = make_repo(tmp_path, with_reviews=True)
    target = pt.select_target(repo)
    assert target is not None
    assert "FR-001" in target.artifact_text

    pool = p.load_pool(repo / p.POOL_PATH)
    persona = pool.personalities[0]

    started = time.monotonic()
    raw, model = p._grounded_call(
        target, persona, repo, persona_framing=persona.prompt_body,
    )
    elapsed = time.monotonic() - started

    # Provenance must be what answered, not the module constant.
    assert model, "no model recorded"
    assert elapsed < 360, f"a single turn took {elapsed:.0f}s"

    turn = pt.parse_turn(raw, target, model=model)
    assert turn.action in (pt.ACTION_COMMENT, pt.ACTION_ABSTAIN)
    if turn.action == pt.ACTION_ABSTAIN:
        # A real abstention is a good outcome, not a failure — but it must say
        # why, so a run of them is diagnosable rather than silent.
        assert turn.reason, "an abstention must carry a reason"
        return
    assert turn.comment, "a comment action with no comment"
    # Grounding is the whole point: a quote must be locatable in the artifact
    # it was shown. Anchoring is evidence, never a factual verdict.
    assert turn.quotes, "a grounded comment should cite the artifact"
    assert len(turn.unanchored) < len(turn.quotes), (
        f"every quote was unlocatable in the artifact: {turn.unanchored}"
    )
    assert turn.provenance["context_digest"] == pt.context_digest(target)


def test_a_real_turn_on_a_stub_costs_no_call(tmp_path, credential):
    """The guard that the audit's finding most directly implies."""
    repo = make_repo(tmp_path, spec_body="# Spec\n\nTODO.\n")

    def _forbidden(*_a, **_k):
        raise AssertionError("a stub must not reach a model")

    original = p._grounded_call
    p._grounded_call = _forbidden
    try:
        entry = p.tick(repo)
    finally:
        p._grounded_call = original
    assert entry["outcome"] == p.OUTCOME_ABSTAINED
    assert "substantive" in entry["note"]
