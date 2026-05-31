# tests/unit/test_grounding_service.py
from llmxive.grounding.entailment import Verdict
from llmxive.grounding.full_text import RetrievedDoc
from llmxive.grounding.service import decide, number_substantiated


def _doc(full=None, abstract=None, tier="s2"):
    return RetrievedDoc("doi", "10.x/y", tier, full, abstract, None, "u")


def test_decide_grounded_full_text_ok():
    ok, _reason = decide(_doc(full="body"), Verdict("grounded"))
    assert ok is True


def test_decide_contradicted_flags():
    ok, reason = decide(_doc(full="body"), Verdict("contradicted", note="says 9988"))
    assert ok is False and "contradict" in reason.lower()


def test_decide_not_found_full_text_flags():
    ok, _reason = decide(_doc(full="body"), Verdict("not_found"))
    assert ok is False


def test_decide_abstract_only_grounded_ok():
    ok, _reason = decide(_doc(abstract="abs", tier="abstract"), Verdict("grounded"))
    assert ok is True


def test_decide_abstract_only_not_found_flags():
    ok, reason = decide(_doc(abstract="abs", tier="abstract"), Verdict("not_found"))
    assert ok is False and "abstract" in reason.lower()


# --- Fix 1: deterministic number gate (design §5) ----------------------------


def test_number_substantiated_no_number_is_noop():
    # No number on the claim -> gate not applicable -> True regardless of text.
    assert number_substantiated(None, "anything") is True
    assert number_substantiated("", "anything") is True


def test_number_substantiated_present():
    assert number_substantiated("9988", "the table reports 9,988 prime knots") is True
    assert number_substantiated("28.4", "BLEU of 28.4 on En-De") is True


def test_number_substantiated_absent():
    assert number_substantiated("9988", "the paper reports 1,296 knots") is False
    # decimal must not match the digit-run form
    assert number_substantiated("28.4", "the score was 284 points") is False


def test_number_substantiated_empty_text():
    assert number_substantiated("42", "") is False
    assert number_substantiated("42", None) is False


def test_number_gate_flips_grounded_to_flagged(monkeypatch, tmp_path):
    """End-to-end (offline) proof: even when the LLM entailment returns
    ``grounded``, a NUMBER-bearing claim whose number is ABSENT from the
    retrieved source text is overridden to a FLAG by the deterministic gate.
    """
    from llmxive.agents.grounding_guard import CitedClaim
    from llmxive.grounding import service
    from llmxive.types import CitationKind

    # The fetched source text does NOT contain the fabricated number 1296.
    fake_doc = RetrievedDoc("doi", "10.x/y", "s2",
                            "The paper reports 9,988 prime knots.", None, None, "u")
    monkeypatch.setattr(service, "retrieve", lambda *a, **k: fake_doc)
    # Force the LLM verdict to a (false-positive) grounded.
    monkeypatch.setattr(service, "assess", lambda *a, **k: Verdict("grounded"))

    claim = CitedClaim(
        claim_text="There are 1,296 prime knots.",
        number="1296",
        source_str="10.x/y",
        source_kind=CitationKind.DOI,
        source_value="10.x/y",
    )
    verdict = service.ground_cited_claim(
        claim, backend=object(), model=None, repo_root=tmp_path
    )
    assert verdict.ok is False
    assert "1296" in verdict.reason


def test_number_gate_passes_when_number_present(monkeypatch, tmp_path):
    """Counterpart: a grounded verdict whose number IS present stays grounded."""
    from llmxive.agents.grounding_guard import CitedClaim
    from llmxive.grounding import service
    from llmxive.types import CitationKind

    fake_doc = RetrievedDoc("doi", "10.x/y", "s2",
                            "The paper reports 9,988 prime knots.", None, None, "u")
    monkeypatch.setattr(service, "retrieve", lambda *a, **k: fake_doc)
    monkeypatch.setattr(service, "assess", lambda *a, **k: Verdict("grounded"))

    claim = CitedClaim(
        claim_text="There are 9,988 prime knots.",
        number="9988",
        source_str="10.x/y",
        source_kind=CitationKind.DOI,
        source_value="10.x/y",
    )
    verdict = service.ground_cited_claim(
        claim, backend=object(), model=None, repo_root=tmp_path
    )
    assert verdict.ok is True


def test_unreadable_source_not_cached(monkeypatch, tmp_path):
    """Fix 3: an unreadable retrieval is not written to either cache, so it can
    self-heal next round."""
    from llmxive.agents.grounding_guard import CitedClaim
    from llmxive.grounding import cache, service
    from llmxive.types import CitationKind

    unreadable = RetrievedDoc("doi", "10.x/z", None, None, None, None, "", error="x")
    monkeypatch.setattr(service, "retrieve", lambda *a, **k: unreadable)

    claim = CitedClaim(
        claim_text="Some claim.", number=None, source_str="10.x/z",
        source_kind=CitationKind.DOI, source_value="10.x/z",
    )
    v = service.ground_cited_claim(claim, backend=object(), model=None, repo_root=tmp_path)
    assert v.ok is False
    # Neither cache was populated.
    assert cache.get_fulltext(tmp_path, "doi", "10.x/z") is None
    assert cache.get_verdict(tmp_path, source_id="doi:10.x/z",
                             claim="Some claim.", number=None) is None
