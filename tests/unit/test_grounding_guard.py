"""Unit tests (OFFLINE — no network, no LLM) for the F-19 factual-grounding guard.

F-19 closes the gap F-18 left open: F-18 verifies that a *reference resolves*
(DOI/arXiv/URL existence) but cannot catch (a) a WRONG NUMBER attached to a
citation, or (b) a free-text author-year citation with no resolvable identifier.
The PROJ-552 fabrication cascade exploited exactly that: the reviser "resolved"
a (correct) knot count by FABRICATING a wrong number (1,296) + a free-text
citation ("Kauffman & Lambropoulou 2004"), and the panel PASSED it.

These tests exercise the PURE pieces (no I/O):

1. ``apply_grounding_verdicts`` — given parsed :class:`CitedClaim`s + per-claim
   grounding verdicts, mark exactly the UNGROUNDED ones ``[UNVERIFIED: ...]``
   (reusing the F-18 marker so the existing F-18c gates hard-block them), and
   leave grounded claims AND uncited design-numbers byte-for-byte untouched.
2. The false-positive guard: a doc full of uncited thresholds / dimensions /
   identifiers yields ZERO flags (the scope guard's whole reason to exist).
3. ``classify_source`` — a source string with a resolvable id (DOI/arXiv/URL)
   is resolvable; a free-text author-year-only string is NOT (→ ungroundable).
4. The F-18 marker is reused (so ``has_unverified_markers`` trips on F-19 flags).
"""

from __future__ import annotations

from llmxive.agents.citation_guard import (
    UNVERIFIED_MARKER_PREFIX,
    find_unverified_markers,
    has_unverified_markers,
)
from llmxive.agents.grounding_guard import (
    CitedClaim,
    GroundingVerdict,
    apply_grounding_verdicts,
    classify_source,
    number_appears_in,
)
from llmxive.types import CitationKind

# --- 1. pure rewriter: mark ungrounded claims, leave grounded untouched -----


def test_apply_marks_ungrounded_freetext_citation() -> None:
    """The trail's exact case: a fabricated number on a free-text-only citation."""
    text = (
        "There are 1,296 prime knots with 13 crossings "
        "(Kauffman & Lambropoulou 2004)."
    )
    claim = CitedClaim(
        claim_text="There are 1,296 prime knots with 13 crossings "
        "(Kauffman & Lambropoulou 2004).",
        number="1296",
        source_str="Kauffman & Lambropoulou 2004",
    )
    verdict = GroundingVerdict(
        claim=claim,
        ok=False,
        reason="free-text citation has no resolvable identifier; cannot substantiate claim",
    )
    cleaned, report = apply_grounding_verdicts(text, [verdict])

    assert UNVERIFIED_MARKER_PREFIX in cleaned
    assert has_unverified_markers(cleaned) is True
    assert report.flagged_count == 1
    bodies = find_unverified_markers(cleaned)
    assert len(bodies) == 1
    assert "1,296" in bodies[0] or "1296" in bodies[0]
    # original claim prose is preserved inside/around the marker
    assert "prime knots with 13 crossings" in cleaned


def test_apply_leaves_grounded_claim_untouched() -> None:
    text = "There are 9,988 prime knots with 13 crossings (arXiv:1706.03762)."
    claim = CitedClaim(
        claim_text=text,
        number="9988",
        source_str="arXiv:1706.03762",
        source_kind=CitationKind.ARXIV,
        source_value="1706.03762",
    )
    verdict = GroundingVerdict(claim=claim, ok=True, reason="")
    cleaned, report = apply_grounding_verdicts(text, [verdict])
    assert cleaned == text
    assert report.flagged_count == 0
    assert report.verified_count == 1
    assert has_unverified_markers(cleaned) is False


def test_apply_idempotent_on_already_marked() -> None:
    text = "There are 1,296 prime knots (Kauffman & Lambropoulou 2004)."
    claim = CitedClaim(
        claim_text=text, number="1296", source_str="Kauffman & Lambropoulou 2004"
    )
    verdict = GroundingVerdict(claim=claim, ok=False, reason="ungroundable")
    once, _ = apply_grounding_verdicts(text, [verdict])
    twice, report2 = apply_grounding_verdicts(once, [verdict])
    assert once == twice
    assert once.count(UNVERIFIED_MARKER_PREFIX) == 1
    assert report2.flagged_count == 0


# --- 2. the FALSE-POSITIVE GUARD (the scope guard's reason to exist) ---------


def test_uncited_design_numbers_yield_zero_flags() -> None:
    """A spec full of uncited thresholds / dimensions / ids must pass UNTOUCHED.

    The grounding guard only ever acts on extracted CitedClaims; a doc with no
    source-attributed claims produces an empty claim list → zero verdicts → the
    rewriter is a no-op. This pins the contract that design numbers are NEVER
    touched (precision over recall).
    """
    text = (
        "# Spec\n\n"
        "FR-027: panels run at most 3 rounds with p < 0.05 and R² >= 0.05.\n"
        "Figures are 1200x900 pixels. Timeout is 60s; max_tokens = 131072.\n"
        "See issue #239 and task T123 (US2). Alpha = 0.8, threshold 0.7.\n"
    )
    # No CitedClaims extracted from a design-number-only doc → empty verdicts.
    cleaned, report = apply_grounding_verdicts(text, [])
    assert cleaned == text
    assert report.flagged_count == 0
    assert has_unverified_markers(cleaned) is False


def test_grounded_and_ungrounded_mixed() -> None:
    text = (
        "There are 9,988 prime knots with 13 crossings (arXiv:1706.03762). "
        "There are 1,296 of some other thing (Kauffman & Lambropoulou 2004). "
        "The success threshold is R² >= 0.05 (a design choice, uncited)."
    )
    grounded = GroundingVerdict(
        claim=CitedClaim(
            claim_text="There are 9,988 prime knots with 13 crossings (arXiv:1706.03762).",
            number="9988", source_str="arXiv:1706.03762",
            source_kind=CitationKind.ARXIV, source_value="1706.03762",
        ),
        ok=True, reason="",
    )
    ungrounded = GroundingVerdict(
        claim=CitedClaim(
            claim_text="There are 1,296 of some other thing (Kauffman & Lambropoulou 2004).",
            number="1296", source_str="Kauffman & Lambropoulou 2004",
        ),
        ok=False, reason="free-text citation; cannot substantiate",
    )
    cleaned, report = apply_grounding_verdicts(text, [grounded, ungrounded])
    assert report.flagged_count == 1
    assert report.verified_count == 1
    # the design threshold is never touched (it was never a CitedClaim)
    assert "R² >= 0.05" in cleaned
    # the grounded claim's source survives
    assert "arXiv:1706.03762" in cleaned
    # the ungrounded one is flagged
    assert has_unverified_markers(cleaned) is True
    bodies = find_unverified_markers(cleaned)
    assert any("1,296" in b or "1296" in b for b in bodies)


# --- 3. source classification (resolvable id vs free-text-only) -------------


def test_classify_source_freetext_is_unresolvable() -> None:
    kind, value = classify_source("Kauffman & Lambropoulou 2004")
    assert kind is None
    assert value is None


def test_classify_source_arxiv() -> None:
    kind, value = classify_source("Lee et al. 2024, arXiv:1706.03762")
    assert kind == CitationKind.ARXIV
    assert value == "1706.03762"


def test_classify_source_doi() -> None:
    kind, value = classify_source("Smith 2020, doi:10.1234/foo.5678")
    assert kind == CitationKind.DOI
    assert value == "10.1234/foo.5678"


def test_classify_source_url() -> None:
    kind, value = classify_source("[Knot Atlas](https://katlas.org/wiki/13_crossings)")
    assert kind == CitationKind.URL
    assert value == "https://katlas.org/wiki/13_crossings"


def test_classify_source_malformed_arxiv_is_resolvable_kind() -> None:
    """A malformed arXiv id is still ARXIV-kind (the resolver will 404 → flag)."""
    kind, value = classify_source("Lee et al. 2024, arXiv:2402.13")
    assert kind == CitationKind.ARXIV
    assert value == "2402.13"


# --- 4. number-equivalence (PURE) -------------------------------------------


def test_number_appears_in_grouped_and_bare() -> None:
    assert number_appears_in("9988", "the count is 9,988 knots")  # grouped form
    assert number_appears_in("9988", "the count is 9988 knots")  # bare form
    assert number_appears_in("9,988", "exactly 9988 of them")  # input separated
    assert not number_appears_in("9988", "the count is 1,296 knots")
    # a digit-run that merely CONTAINS the digits must not match as a substring
    assert not number_appears_in("988", "the value 19884 appears")


# --- 5. extraction parsing (PURE; no backend) -------------------------------


def test_parse_extraction_reply_scope_guard_empty() -> None:
    """A spec full of uncited numbers yields an empty claims list."""
    from llmxive.agents.grounding_guard import _parse_extraction_reply

    reply = "```yaml\nclaims: []\n```"
    assert _parse_extraction_reply(reply) == []


def test_parse_extraction_reply_extracts_cited_claim() -> None:
    from llmxive.agents.grounding_guard import _parse_extraction_reply

    reply = (
        "claims:\n"
        "  - claim_text: 'There are 1,296 prime knots (Kauffman & Lambropoulou 2004).'\n"
        "    number: '1296'\n"
        "    source: 'Kauffman & Lambropoulou 2004'\n"
    )
    claims = _parse_extraction_reply(reply)
    assert len(claims) == 1
    assert claims[0].number == "1296"
    assert claims[0].source_kind is None  # free-text only → ungroundable
    assert claims[0].source_value is None


def test_parse_extraction_reply_recovers_embedded_quote() -> None:
    """Fix E — a reply whose claim_text carries an embedded double-quoted title
    (``"A Census of Knots."``) breaks YAML's quoted-scalar grammar. The shared
    tolerant recovery must recover the cited claim instead of dropping every
    claim (the twin-parser fragility that recurred in PROJ-552)."""
    from llmxive.agents.grounding_guard import _parse_extraction_reply
    from llmxive.types import CitationKind

    reply = (
        "claims:\n"
        '  - claim_text: "The 1998 census, see "A Census of Knots.", lists '
        '9988 prime knots (doi:10.1090/S0273-0979-1998-00763-9)."\n'
        "    number: '9988'\n"
        "    source: 'doi:10.1090/S0273-0979-1998-00763-9'\n"
    )
    claims = _parse_extraction_reply(reply)
    assert len(claims) == 1
    assert claims[0].number == "9988"
    assert "A Census of Knots." in claims[0].claim_text
    assert claims[0].source_kind == CitationKind.DOI
    assert claims[0].source_value == "10.1090/S0273-0979-1998-00763-9"


# --- ground_claim delegates to the full-text grounding service --------------


def test_ground_claim_delegates_to_service(monkeypatch):
    import llmxive.agents.grounding_guard as gg
    from llmxive.agents.grounding_guard import CitedClaim, GroundingVerdict
    from llmxive.types import CitationKind

    captured = {}

    def fake_service(claim, *, backend, model, repo_root):
        captured["called"] = True
        return GroundingVerdict(claim=claim, ok=False, reason="from-service")

    monkeypatch.setattr(gg, "_service_ground", fake_service)
    c = CitedClaim(claim_text="x", number="1", source_str="arXiv:1706.03762",
                   source_kind=CitationKind.ARXIV, source_value="1706.03762")
    v = gg.ground_claim(c, backend=object(), model=None, repo_root=__import__("pathlib").Path("."))
    assert captured.get("called") and v.reason == "from-service"


def test_ground_claim_free_text_still_flags_without_service():
    from llmxive.agents.grounding_guard import CitedClaim, ground_claim
    c = CitedClaim(claim_text="x", number="1", source_str="Kauffman 2004",
                   source_kind=None, source_value=None)
    v = ground_claim(c, backend=object(), model=None, repo_root=__import__("pathlib").Path("."))
    assert v.ok is False and "free-text" in v.reason
