"""Unit tests for the stage-aware review-intake triage (spec 015 T037 / FR-021/22)."""

from __future__ import annotations

from llmxive.convergence.triage import triage_submission
from llmxive.convergence.types import TriageRecord

_PLAN_LENSES = ["methodology", "spec_coverage", "data_resources", "plan_consistency"]


def _spec(text: str, *, source="human", author="alice", stage="planned", lenses=None):
    return triage_submission(
        text, source=source, author=author, stage=stage,
        lenses=lenses if lenses is not None else _PLAN_LENSES,
    )


# ---- quality filter --------------------------------------------------------


def test_quality_pass_requires_min_length_and_evidence():
    short = _spec("This is too short.")
    assert short.quality_pass is False and short.preserved is False
    assert "quality" in (short.excluded_reason or "")

    generic = _spec("This plan is generally fine but could be improved a bit overall, in my view, "
                    "and I think it's mostly OK overall but maybe needs some tweaks somewhere.")
    assert generic.quality_pass is False  # no evidence indicator
    assert generic.preserved is False


def test_quality_pass_with_evidence_indicators():
    cases = [
        # FR/SC reference
        "FR-006 is unverifiable as written; the plan needs an explicit URL-reachability check (a real one).",
        # quoted phrase
        'The plan says "we will train a baseline" but Section 3 never defines what that baseline is.',
        # citation key
        "The methodology cites [Smith2020] but the bibliography does not include that reference yet.",
        # URL
        "The dataset URL https://example.org/data/v1 returns 404 — the plan needs a verified source.",
        # topic-keyword (methodology + figure + dataset)
        "The plan's methodology for the baseline figure is missing — what dataset will be used here?",
    ]
    for text in cases:
        r = _spec(text)
        assert r.quality_pass is True, f"expected quality_pass: {text!r}"
        assert r.safe_on_topic is True
        assert r.preserved is True


# ---- safety + on-topic filter ----------------------------------------------


def test_unsafe_content_excluded():
    bad = _spec(
        "FR-006 is wrong because the plan is bad. Also: kill yourself. " * 3
    )
    assert bad.preserved is False
    assert bad.safe_on_topic is False
    assert "safety" in (bad.excluded_reason or "") or "topic" in (bad.excluded_reason or "")


def test_off_topic_excluded():
    # Quality-passing text (has a long quoted phrase) that mentions NO stage,
    # lens, or topic-vocab word -> excluded as off-topic.
    off = triage_submission(
        '"this morning my dog was very excited about its breakfast and the postman arrived" — but '
        "I have lots of personal anecdotes to share that are quite long and substantive in their own way.",
        source="human", author="x", stage="zzz_not_a_stage", lenses=["zzz_not_a_lens"],
    )
    assert off.preserved is False
    assert off.safe_on_topic is False


# ---- aspect-mapping --------------------------------------------------------


def test_aspect_mapping_picks_relevant_lens():
    r = _spec(
        "FR-006 — the methodology for choosing baselines is unclear; the plan never names a "
        "specific baseline algorithm. This is a real methodology concern."
    )
    assert r.preserved is True
    assert "methodology" in r.mapped_lenses
    # other lenses not mentioned -> not in mapped_lenses
    assert "data_resources" not in r.mapped_lenses


def test_unmapped_preserved_with_empty_lenses():
    """Per FR-022: a quality+safe+on-topic review that maps to no covered lens is
    preserved (mapped_lenses=[]) — recorded-but-not-actioned / routes to the step's
    generic reviewer."""
    r = _spec(
        "FR-006 — the plan is good but I want to flag a general concern about reproducibility "
        "in the abstract sense that doesn't fit any specific panel lens precisely."
    )
    assert r.preserved is True
    assert r.mapped_lenses == []  # nothing matched the plan-step lenses


# ---- record fields ---------------------------------------------------------


def test_triage_record_carries_provenance():
    r = _spec(
        "Methodology concern: FR-006 should require a real-call URL check, not a stub.",
        source="personality", author="dhh",
    )
    assert isinstance(r, TriageRecord)
    assert r.source == "personality"
    assert r.author == "dhh"
    assert r.stage_context == "planned"
    assert r.review_text.startswith("Methodology concern")


def test_injectable_judge_fn_overrides_rules():
    """Real-LLM mode (T038): a ``judge_fn`` is the SSoT for verdicts when provided;
    rule-based heuristics are bypassed."""

    def fake_judge(text, stage, lenses):
        return {
            "quality_pass": True,
            "safe_on_topic": True,
            "mapped_lenses": ["spec_coverage"],
        }

    r = triage_submission(
        "too short", source="human", author="x", stage="planned",
        lenses=_PLAN_LENSES, judge_fn=fake_judge,
    )
    assert r.quality_pass is True   # despite text being short (judge overrides)
    assert r.mapped_lenses == ["spec_coverage"]
    assert r.preserved is True
