"""Unit tests for the canonical verified-fact store + correction sweep.

Closes the PROJ-552 trustworthiness gap: the claim layer resolves numeric
claims PER-INSTANCE, so the verified value (9988, from OEIS A002863) is known
for one mention of "prime knots at crossing number 13" yet a different mention
that still asserts the fabricated 27,635 survives into the converged spec.

The canonical store keys verified facts by SUBJECT (excluding the asserted /
verified numeric value, but INCLUDING qualifier numbers), and the correction
sweep forces EVERY mention of a verified subject to its verified value.

All deterministic — no model mocks.
"""

from __future__ import annotations

from llmxive.claims.canonical import (
    CanonicalFact,
    apply_canonical_corrections,
    build_canonical_facts,
    subject_key,
    subject_keywords,
)
from llmxive.claims.models import Claim, ClaimKind, ClaimStatus

# ---------------------------------------------------------------------------
# Helpers — real Claim objects, mirroring the PROJ-552 registry shape.
# ---------------------------------------------------------------------------


def _verified_knot_claim(
    raw_text: str,
    *,
    resolved_value: str = "9988",
    claim_id: str = "c_00000001",
    with_source: bool = True,
) -> Claim:
    """A VERIFIED knot-count claim with a real fetched fill source (or not)."""
    evidence = None
    if with_source:
        evidence = {
            "filled": True,
            "fill": {
                "value": resolved_value,
                "source_id": "A002863",
                "url": "https://oeis.org/A002863",
                "quote": (
                    "... 552, 2176, 9988, 46972 ... (sequence A002863 in the OEIS)."
                ),
                "channel": "oeis",
                "conflicts": [],
            },
        }
    return Claim(
        claim_id=claim_id,
        kind=ClaimKind.NUMERIC,
        raw_text=raw_text,
        canonical=raw_text,
        context="knot tabulation",
        artifact_path="projects/PROJ-552/specs/spec.md",
        source_type="external",
        status=ClaimStatus.VERIFIED,
        resolved_value=resolved_value,
        evidence=evidence,
        resolver="fill",
        attempts=1,
        updated_at="2026-06-02T00:00:00Z",
    )


# The two real PROJ-552 strings: the fabricated mention and the verified mention.
_FAB_13 = (
    "For crossing number 13, the exact count is 27,635 prime knots, as "
    "established in Hoste, J., Thistlethwaite, M. B., & Weeks, J. (1998). "
    "'A Census of Knots.' Experimental Mathematics, 7(4), 281-299."
)
_OK_13 = (
    "The number of prime knots at crossing number 13 is 9,988 "
    "(sequence A002863 in the OEIS)."
)
_OK_12 = "There are 2,176 prime knots at crossing number 12."


# ---------------------------------------------------------------------------
# subject_key — equivalence / distinction / empty
# ---------------------------------------------------------------------------


class TestSubjectKey:
    def test_asserted_value_excluded_27635_eq_9988(self) -> None:
        """'27,635 ... crossing 13' and '9,988 ... crossing 13' map to the SAME
        key: the asserted/verified value digits are stripped, the qualifier 13
        kept."""
        fab = _verified_knot_claim(_FAB_13, resolved_value="9988")
        ok = _verified_knot_claim(_OK_13, resolved_value="9988")
        k_fab = subject_key(fab)
        k_ok = subject_key(ok)
        assert k_fab != ""
        assert k_fab == k_ok

    def test_qualifier_number_distinguishes_subject(self) -> None:
        """Crossing number 12 must NOT collide with crossing number 13."""
        c13 = _verified_knot_claim(_OK_13, resolved_value="9988")
        c12 = _verified_knot_claim(_OK_12, resolved_value="2176")
        assert subject_key(c13) != subject_key(c12)

    def test_subject_key_includes_qualifier_digit(self) -> None:
        """The kept qualifier (13) appears in the key; the asserted value does not."""
        fab = _verified_knot_claim(_FAB_13, resolved_value="9988")
        key = subject_key(fab)
        assert "13" in key
        assert "9988" not in key
        assert "27635" not in key

    def test_empty_subject_returns_empty_key(self) -> None:
        """A bare number with no distinctive subject → '' (never a canonical fact)."""
        bare = Claim(
            claim_id="c_bare0001",
            kind=ClaimKind.NUMERIC,
            raw_text="27,635",
            canonical="27,635",
            context="",
            artifact_path="x.md",
            source_type="external",
            status=ClaimStatus.VERIFIED,
            resolved_value="9988",
            evidence=None,
            resolver=None,
            attempts=0,
            updated_at="2026-06-02T00:00:00Z",
        )
        assert subject_key(bare) == ""

    def test_plural_rephrasing_same_key(self) -> None:
        """The reviser toggles plurals between rounds; 'knots'/'knot' must not
        produce different subjects."""
        a = _verified_knot_claim(
            "There are 9,988 prime knots at crossing number 13.",
            resolved_value="9988",
        )
        b = _verified_knot_claim(
            "There is a prime knot count of 9,988 at crossing number 13.",
            resolved_value="9988",
        )
        assert subject_key(a) == subject_key(b)


# ---------------------------------------------------------------------------
# build_canonical_facts
# ---------------------------------------------------------------------------


class TestBuildCanonicalFacts:
    def test_builds_fact_from_verified_sourced_claim(self) -> None:
        ok = _verified_knot_claim(_OK_13, resolved_value="9988")
        facts = build_canonical_facts([ok])
        assert len(facts) == 1
        key = subject_key(ok)
        assert key in facts
        fact = facts[key]
        assert isinstance(fact, CanonicalFact)
        assert fact.value == "9988"
        assert fact.source_id == "A002863"
        assert fact.url == "https://oeis.org/A002863"
        assert fact.quote

    def test_skips_pending_and_unsourced_and_empty_subject(self) -> None:
        pending = _verified_knot_claim(_OK_13, resolved_value="9988")
        pending.status = ClaimStatus.PENDING
        unsourced = _verified_knot_claim(
            _OK_13, resolved_value="9988", with_source=False
        )
        bare = Claim(
            claim_id="c_bare0002",
            kind=ClaimKind.NUMERIC,
            raw_text="9988",
            canonical="9988",
            context="",
            artifact_path="x.md",
            source_type="external",
            status=ClaimStatus.VERIFIED,
            resolved_value="9988",
            evidence={"filled": True, "fill": {"value": "9988",
                      "source_id": "A002863", "url": "https://oeis.org/A002863",
                      "quote": "q", "channel": "oeis", "conflicts": []}},
            resolver="fill",
            attempts=1,
            updated_at="2026-06-02T00:00:00Z",
        )
        facts = build_canonical_facts([pending, unsourced, bare])
        assert facts == {}

    def test_agreeing_duplicates_collapse_to_one(self) -> None:
        a = _verified_knot_claim(_FAB_13, resolved_value="9988", claim_id="c_a")
        b = _verified_knot_claim(_OK_13, resolved_value="9988", claim_id="c_b")
        facts = build_canonical_facts([a, b])
        assert len(facts) == 1
        assert next(iter(facts.values())).value == "9988"

    def test_conflict_keeps_sourced_value_never_fabricates(self) -> None:
        """Two candidates for one subject with DIFFERENT values: the sourced /
        first-verified one wins; NO fabricated/blended value appears."""
        good = _verified_knot_claim(
            _OK_13, resolved_value="9988", claim_id="c_good", with_source=True
        )
        # A second claim for the SAME subject but a WRONG verified value and no
        # real fetched source — must never overwrite the sourced fact.
        bad = _verified_knot_claim(
            "The count of prime knots at crossing number 13 is 27,635.",
            resolved_value="27635",
            claim_id="c_bad",
            with_source=False,
        )
        facts = build_canonical_facts([good, bad])
        assert len(facts) == 1
        fact = next(iter(facts.values()))
        # The sourced 9988 wins; the unsourced 27635 never becomes canonical.
        assert fact.value == "9988"
        assert fact.value != "27635"

    def test_conflict_two_sourced_disagree_first_wins_no_fabrication(self) -> None:
        """Two SOURCED candidates that disagree: keep the first, never blend."""
        first = _verified_knot_claim(
            _OK_13, resolved_value="9988", claim_id="c_first", with_source=True
        )
        second = _verified_knot_claim(
            "prime knots at crossing number 13 number 27,635.",
            resolved_value="27635",
            claim_id="c_second",
            with_source=True,
        )
        facts = build_canonical_facts([first, second])
        assert len(facts) == 1
        fact = next(iter(facts.values()))
        assert fact.value == "9988"  # first sourced wins
        assert fact.value in {"9988", "27635"}  # never a fabricated blend

    def test_skips_sequence_list_claim_no_garbage_fact(self) -> None:
        """A claim listing the WHOLE OEIS sequence is not a single subject→value
        fact — keying it would map a garbage subject to one arbitrary list member.
        build_canonical_facts must skip it (POLISH follow-up)."""
        from llmxive.claims.canonical import _is_sequence_like

        seq = _verified_knot_claim(
            "The prime-knot counts by crossing number are 1, 1, 2, 3, 7, 21, "
            "49, 165, 552, 2176, 9988.",
            resolved_value="9988",
        )
        # Sanity: this claim's subject enumerates many numbers (sequence-like).
        assert _is_sequence_like(seq)
        assert build_canonical_facts([seq]) == {}

    def test_skips_digitless_inequality_claim_with_fabricated_value(self) -> None:
        """A qualitative inequality with NO numeric value in its own text must not
        become a fact even if the fill assigned a (fabricated) resolved_value.

        Real PROJ-552 garbage: "braid index ≤ crossing number for most knots per
        known inequality" was filled to resolved_value "2" cited to an unrelated
        source (an email address). A numeric fact must assert a number itself."""
        bad = _verified_knot_claim(
            "braid index ≤ crossing number for most knots per known inequality",
            resolved_value="2",
            claim_id="c_ineq",
        )
        assert build_canonical_facts([bad]) == {}

    def test_correction_claim_still_built_value_differs_from_asserted(self) -> None:
        """The guard must NOT skip the correction case: the raw_text asserts a
        number (27,635) even though the verified value (9988) differs."""
        ok = _verified_knot_claim(_FAB_13, resolved_value="9988", claim_id="c_corr")
        facts = build_canonical_facts([ok])
        assert len(facts) == 1
        assert next(iter(facts.values())).value == "9988"

    def test_clean_single_subject_fact_survives_alongside_list(self) -> None:
        """The list claim is skipped but a properly-scoped 9988 claim still yields
        the clean fact."""
        seq = _verified_knot_claim(
            "Counts: 1, 1, 2, 3, 7, 21, 49, 165, 552, 2176, 9988.",
            resolved_value="9988",
            claim_id="c_seq",
        )
        ok = _verified_knot_claim(_OK_13, resolved_value="9988", claim_id="c_ok")
        facts = build_canonical_facts([seq, ok])
        assert len(facts) == 1
        assert next(iter(facts.values())).value == "9988"


# ---------------------------------------------------------------------------
# apply_canonical_corrections — the PROJ-552 sweep
# ---------------------------------------------------------------------------


class TestApplyCanonicalCorrections:
    def test_27635_swept_to_9988_both_mentions(self) -> None:
        """EVERY '27,635 ... crossing 13' becomes 9988; the correct 9,988 stays;
        prose preserved."""
        ok = _verified_knot_claim(_OK_13, resolved_value="9988")
        facts = build_canonical_facts([ok])
        text = (
            "## Background\n\n"
            + _FAB_13
            + "\n\nLater we note: "
            + _OK_13
            + "\n\nAnd again, "
            + _FAB_13
            + "\n"
        )
        corrected, corrections = apply_canonical_corrections(text, facts)
        # The fabrication is gone everywhere…
        assert "27,635" not in corrected
        assert "27635" not in corrected
        # …replaced by the verified value…
        assert corrected.count("9988") + corrected.count("9,988") >= 3
        # …and the surrounding prose is preserved.
        assert "A Census of Knots" in corrected
        assert "as established in Hoste" in corrected
        assert len(corrections) >= 1
        # No lost-separator artifact: an inserted citation never butts a word
        # ("…url)prime") — the value stays separated from following prose.
        import re as _re
        assert not _re.search(r"https?://\S+\)[A-Za-z0-9]", corrected)
        assert "prime knots" in corrected  # subject noun phrase intact

    def test_subject_isolation_12_crossing_untouched(self) -> None:
        """A canonical fact ONLY for the 13-crossing subject must not touch the
        12-crossing number."""
        ok13 = _verified_knot_claim(_OK_13, resolved_value="9988")
        facts = build_canonical_facts([ok13])
        text = _OK_12 + "\n" + _FAB_13
        corrected, _ = apply_canonical_corrections(text, facts)
        assert "2,176" in corrected  # the 12-crossing count is preserved
        assert "27,635" not in corrected  # the 13-crossing fabrication is fixed

    def test_no_false_positive_unknown_subject_unchanged(self) -> None:
        """A number whose subject has no canonical fact is never touched."""
        ok13 = _verified_knot_claim(_OK_13, resolved_value="9988")
        facts = build_canonical_facts([ok13])
        text = "The dataset contains 5,000 samples collected over 7 years."
        corrected, corrections = apply_canonical_corrections(text, facts)
        assert corrected == text
        assert corrections == []

    def test_bare_number_no_subject_unchanged(self) -> None:
        ok13 = _verified_knot_claim(_OK_13, resolved_value="9988")
        facts = build_canonical_facts([ok13])
        text = "27,635"
        corrected, corrections = apply_canonical_corrections(text, facts)
        assert corrected == "27,635"
        assert corrections == []

    def test_empty_facts_is_noop(self) -> None:
        text = _FAB_13 + "\n" + _OK_13
        corrected, corrections = apply_canonical_corrections(text, {})
        assert corrected == text
        assert corrections == []

    def test_already_correct_mention_unchanged(self) -> None:
        """A mention that already asserts the verified value is left byte-identical."""
        ok = _verified_knot_claim(_OK_13, resolved_value="9988")
        facts = build_canonical_facts([ok])
        text = _OK_13
        corrected, _corrections = apply_canonical_corrections(text, facts)
        assert "9,988" in corrected
        assert "27,635" not in corrected

    def test_qualifier_mismatch_does_not_overcorrect(self) -> None:
        """A fact for crossing 13 must NOT correct a differently-qualified mention
        (crossing 12) even though they share every subject keyword — the
        qualifier number must agree EXACTLY."""
        ok13 = _verified_knot_claim(_OK_13, resolved_value="9988")
        facts = build_canonical_facts([ok13])
        # Same keywords {prime, knot, crossing} but qualifier 12 ≠ 13.
        text = "There are 1,234 prime knots at crossing number 12."
        corrected, corrections = apply_canonical_corrections(text, facts)
        assert corrected == text  # untouched — different subject
        assert corrections == []

    def test_local_window_corrects_embedded_value_in_dense_sentence(self) -> None:
        """A fabricated value EMBEDDED in a number-dense sentence is corrected via
        the LOCAL window around the number — while every other number in the SAME
        sentence (whose local window matches no fact) is preserved EXACTLY.

        This reproduces the real PROJ-552 SC-001 bullet: a long sentence whose
        whole-chunk qualifier set is {11, 13, 1} (so the conservative equal-match
        skips it), but where the noun phrase immediately quantified by 27,635 is
        'prime knots at crossing number 13' → qualifier {13} → matches the
        canonical fact {13|crossing knot prime → 9988}.
        """
        ok13 = _verified_knot_claim(_OK_13, resolved_value="9988")
        ok12 = _verified_knot_claim(_OK_12, resolved_value="2176", claim_id="c_12")
        facts = build_canonical_facts([ok13, ok12])
        text = (
            "- **SC-001**: Dataset contains all prime knots with crossing number "
            "≤13, with validation benchmarking for dataset completeness "
            "focused on crossing numbers ≤10 (≥95% completeness on "
            "required invariant fields). Crossing numbers 11-13 data is "
            "downloaded but not validated in Phase 1; this is documented in "
            "`docs/validation_scope.md` noting the practical constraint (27,635 "
            "prime knots at crossing number 13) and justification for Phase 1 "
            "scope limitation. A separate tally lists 1,234 prime knots at "
            "crossing number 12 for comparison."
        )
        corrected, corrections = apply_canonical_corrections(text, facts)

        # The embedded fabrication is corrected to the verified value …
        assert "27,635" not in corrected
        assert "27635" not in corrected
        assert "9988" in corrected or "9,988" in corrected
        # … and the crossing-12 tally is corrected to ITS verified value (2,176),
        # NOT to the 13-crossing fact — qualifier {12} matches only the 12-fact.
        assert "1,234" not in corrected
        assert "2176" in corrected or "2,176" in corrected
        # Every OTHER number in this dense sentence is preserved EXACTLY: the
        # ≤13 / ≤10 / ≥95% scope qualifiers must be byte-for-byte untouched
        # (their local windows do not match the prime-knot-count fact).
        assert "≤13" in corrected  # ≤13 (crossing number ≤13)
        assert "≤10" in corrected  # ≤10 (crossing numbers ≤10)
        assert "≥95%" in corrected  # ≥95% completeness
        assert "11-13 data is downloaded" in corrected
        assert "Phase 1" in corrected
        # The corrected sentence still reads as one bullet (prose preserved).
        assert "**SC-001**" in corrected
        assert "prime knots at crossing number 13)" in corrected
        # The 13→9988 correction (and the 12→2176 one) was recorded.
        assert any(c["to"] == "9988" and c["from"] == "27,635" for c in corrections)

    def test_local_window_does_not_overcorrect_crossing_12_to_13_fact(self) -> None:
        """A 'crossing number 12' count embedded in a dense sentence must NOT be
        corrected to a 13-crossing fact — the local window's qualifier {12} ≠ {13}.
        With ONLY a 13-fact present, the 12-count is left byte-identical."""
        ok13 = _verified_knot_claim(_OK_13, resolved_value="9988")
        facts = build_canonical_facts([ok13])  # ONLY the 13-crossing fact
        text = (
            "Per the scope note (≤13 downloaded), a tally records 1,234 prime "
            "knots at crossing number 12 alongside the 27,635 prime knots at "
            "crossing number 13 figure."
        )
        corrected, corrections = apply_canonical_corrections(text, facts)
        # The 13-crossing embedded fabrication IS corrected …
        assert "27,635" not in corrected
        assert "9988" in corrected or "9,988" in corrected
        # … but the crossing-12 count is NOT touched (no 12-fact, qualifier ≠ 13).
        assert "1,234" in corrected
        assert all(c["from"] != "1,234" for c in corrections)

    def test_local_window_no_matching_fact_unchanged(self) -> None:
        """A number whose LOCAL window matches no canonical fact is unchanged even
        when it sits in a sentence that also contains a correctable number."""
        ok13 = _verified_knot_claim(_OK_13, resolved_value="9988")
        facts = build_canonical_facts([ok13])
        text = (
            "The pipeline processed 8,500 diagrams while noting the constraint "
            "(27,635 prime knots at crossing number 13) for context."
        )
        corrected, _ = apply_canonical_corrections(text, facts)
        assert "8,500 diagrams" in corrected  # unrelated number preserved
        assert "27,635" not in corrected  # the embedded count is corrected

    def test_qualifierless_fact_does_not_overwrite_qualified_mention(self) -> None:
        """A bare 'prime knots → 49' fact (no qualifier) must NOT overwrite a
        mention that IS qualified (crossing number 13) — qualifier-less facts only
        match qualifier-less mentions, preventing a silent wrong-instance swap."""
        bare_fact = Claim(
            claim_id="c_qless001",
            kind=ClaimKind.NUMERIC,
            raw_text="There are 49 prime knots.",
            canonical="There are 49 prime knots.",
            context="",
            artifact_path="x.md",
            source_type="external",
            status=ClaimStatus.VERIFIED,
            resolved_value="49",
            evidence={"filled": True, "fill": {"value": "49",
                      "source_id": "49 (number)", "url": "https://en.wikipedia.org/wiki/49",
                      "quote": "q", "channel": "wikipedia", "conflicts": []}},
            resolver="fill",
            attempts=1,
            updated_at="2026-06-02T00:00:00Z",
        )
        facts = build_canonical_facts([bare_fact])
        assert facts  # the bare fact is built (it has a 'prime knot' subject)
        # A 13-crossing mention shares {prime, knot} but adds the qualifier 13 →
        # the qualifier-less fact must not match it.
        text = "The census lists 27,635 prime knots at crossing number 13."
        corrected, corrections = apply_canonical_corrections(text, facts)
        assert corrected == text
        assert corrections == []


# ---------------------------------------------------------------------------
# subject_keywords — public API (spec 019, C2: promoted from _subject_keywords)
# ---------------------------------------------------------------------------


class TestSubjectKeywordsPublic:
    def test_public_keywords_are_digit_free_and_singular(self) -> None:
        """The promoted public ``subject_keywords`` returns lowercase, digit-free,
        singularized subject tokens (used by the spec-019 prose relevance gate)."""
        claim = _verified_knot_claim(_OK_13, resolved_value="9988")
        kws = subject_keywords(claim)
        assert "knot" in kws          # plural 'knots' singularized
        assert "crossing" in kws
        assert all(not k.isdigit() for k in kws)  # no bare numbers
        assert "9988" not in kws and "13" not in kws
        assert kws == sorted(kws)     # sorted, stable

    def test_keywords_back_subject_key(self) -> None:
        """subject_key consumes the same keyword set, so a claim with real subject
        content yields non-empty keywords and a non-empty key."""
        claim = _verified_knot_claim(_OK_13, resolved_value="9988")
        assert subject_keywords(claim)          # non-empty
        assert subject_key(claim) != ""
