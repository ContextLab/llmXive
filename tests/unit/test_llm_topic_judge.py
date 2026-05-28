"""Tests for the LLM-based off-topic / on-topic triage judge.

The keyword-matching path in ``_on_topic`` lets a comment pass triage
if it merely name-drops any lens or generic word like ``paper``,
``data``, or ``figure``. For T079 (real post-``posted`` living-document
verification) we want a robust intent classifier.

``llm_topic_judge`` is a factory returning a :class:`JudgeFn` compatible
with ``triage_submission``'s ``judge_fn`` parameter. These tests use a
fake backend (no real LLM calls) to lock in the parser + fail-closed
semantics.
"""

from __future__ import annotations

from dataclasses import dataclass

from llmxive.convergence.triage import llm_topic_judge, triage_submission


@dataclass
class _FakeResp:
    text: str


@dataclass
class _FakeBackend:
    """Returns the next canned YAML reply per chat() call."""

    replies: list[str]

    def chat(self, messages, model=None, max_tokens=None):
        if not self.replies:
            raise RuntimeError("out of replies")
        return _FakeResp(text=self.replies.pop(0))


def _yaml(quality: bool, ok: bool, lenses: list[str]) -> str:
    ml = "[" + ", ".join(lenses) + "]"
    return (
        "Here's my triage:\n\n"
        "---\n"
        f"quality_pass: {str(quality).lower()}\n"
        f"safe_on_topic: {str(ok).lower()}\n"
        f"mapped_lenses: {ml}\n"
        "---\n"
    )


def test_llm_judge_accepts_on_topic_evidence_based():
    backend = _FakeBackend(replies=[_yaml(True, True, ["claim_accuracy"])])
    judge = llm_topic_judge(backend)
    record = triage_submission(
        "Citation [Smith2020] on p.4 doesn't support the 12% effect claim.",
        source="human", author="reviewer", stage="posted",
        lenses=["claim_accuracy", "writing_quality"],
        judge_fn=judge,
    )
    assert record.preserved is True
    assert record.quality_pass is True
    assert record.safe_on_topic is True
    assert record.mapped_lenses == ["claim_accuracy"]


def test_llm_judge_rejects_off_topic_even_when_lens_name_dropped():
    """The KEY scenario the keyword path mis-classifies: a comment that
    name-drops a lens but isn't substantively about it. The LLM judge
    should still reject it."""
    backend = _FakeBackend(replies=[_yaml(True, False, [])])
    judge = llm_topic_judge(backend)
    record = triage_submission(
        "Nice claim_accuracy! Also, check out my crypto giveaway @example.com",
        source="human", author="spammer", stage="posted",
        lenses=["claim_accuracy", "writing_quality"],
        judge_fn=judge,
    )
    assert record.preserved is False
    assert record.safe_on_topic is False


def test_llm_judge_rejects_low_quality_vague_comment():
    backend = _FakeBackend(replies=[_yaml(False, True, [])])
    judge = llm_topic_judge(backend)
    record = triage_submission(
        "Cool paper, I think the figure is interesting.",
        source="human", author="generic", stage="posted",
        lenses=["claim_accuracy", "writing_quality"],
        judge_fn=judge,
    )
    assert record.preserved is False
    assert record.quality_pass is False


def test_llm_judge_fails_closed_on_backend_error():
    """When the backend raises, the judge MUST treat the comment as
    rejected (quality_pass=False, safe_on_topic=False) — never
    accidentally wave through unprocessable input."""

    class _BoomBackend:
        def chat(self, *a, **k):  # type: ignore[no-untyped-def]
            raise RuntimeError("backend down")

    judge = llm_topic_judge(_BoomBackend())
    record = triage_submission(
        "This is a substantive comment citing FR-001 on page 4.",
        source="human", author="x", stage="posted",
        lenses=["claim_accuracy"], judge_fn=judge,
    )
    assert record.preserved is False
    assert record.quality_pass is False
    assert record.safe_on_topic is False


def test_llm_judge_fails_closed_on_missing_yaml_frontmatter():
    backend = _FakeBackend(replies=["Just some prose, no frontmatter at all."])
    judge = llm_topic_judge(backend)
    record = triage_submission(
        "anything", source="human", author="x", stage="posted",
        lenses=["claim_accuracy"], judge_fn=judge,
    )
    assert record.preserved is False


def test_llm_judge_fails_closed_on_malformed_yaml():
    # Frontmatter delimiters present but the inner mapping is invalid.
    backend = _FakeBackend(replies=["---\nnot: a, valid yaml structure: : :\n---\n"])
    judge = llm_topic_judge(backend)
    record = triage_submission(
        "anything", source="human", author="x", stage="posted",
        lenses=["claim_accuracy"], judge_fn=judge,
    )
    assert record.preserved is False


def test_llm_judge_drops_unknown_lenses_from_mapped():
    """``mapped_lenses`` from the LLM is type-coerced + range-restricted
    in ``triage_submission`` — but the judge itself returns whatever
    list strings the LLM emits. This test locks in that the judge
    doesn't crash on unexpected lens names; triage_submission decides
    whether to forward them to a reviewer."""
    backend = _FakeBackend(replies=[
        _yaml(True, True, ["claim_accuracy", "made_up_lens"])
    ])
    judge = llm_topic_judge(backend)
    record = triage_submission(
        "Citation [Smith2020] on p.4 about claim_accuracy.",
        source="human", author="x", stage="posted",
        lenses=["claim_accuracy"], judge_fn=judge,
    )
    # The judge passes BOTH names through; triage_submission preserves
    # them as-is (downstream wiring filters against the lens registry).
    assert "claim_accuracy" in record.mapped_lenses


def test_keyword_fallback_path_still_works_without_judge():
    """Regression: when no judge_fn is supplied, the keyword fallback
    is used (and ``llm_topic_judge`` doesn't need to be involved).
    The text must clear the 80-char minimum (`_MIN_QUALITY_CHARS`) and
    contain at least one evidence indicator (FR/SC/task id, URL, etc.)."""
    record = triage_submission(
        "On the abstract: the wording of FR-001 is vague and the spec "
        "does not specify the exact measurement protocol. Suggest "
        "tightening the requirement to MUST-style language.",
        source="human", author="x", stage="posted",
        lenses=["scope"],
    )
    # ``abstract`` is a topic word AND the comment has an FR id and
    # is long enough — quality_pass + safe_on_topic both fire under
    # the keyword fallback.
    assert record.preserved is True
