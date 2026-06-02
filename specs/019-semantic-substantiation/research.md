# Phase 0 Research: Semantic Substantiation for the Claim-Fill Layer

All "NEEDS CLARIFICATION" from Technical Context are resolved below. Each entry
records the Decision, the Rationale, and the Alternatives rejected. Findings are
grounded in the *current* code shapes (verified by direct read, May 2026).

## D1 — Where does the semantic gate hook in?

**Decision**: Add a single trust-boundary helper `_accept(candidate, source,
claim, *, backend, model, repo_root) -> bool` in `fill/extract.py` and route
BOTH gate sites in `extract_value` (offline path L129, LLM path L139) through it.
`_accept` = `present_in_source(...)` AND, when the channel is PROSE, also
`prose_substantiated(...)`.

**Rationale**: `extract_value` is already the documented single trust boundary
("the proposed value is accepted ONLY if it passes `present_in_source`"). Both
admission sites call `present_in_source` today — folding the prose requirement
into one `_accept` keeps the gate in exactly one place (Constitution I) and
guarantees no candidate can enter the candidate list without passing it.

**Alternatives rejected**:
- *Gate inside `present_in_source`* — rejected: its signature is
  `(value, source, kind)`; it has neither the `Claim` (needed for
  `subject_keywords`) nor the `backend` (needed for `assess`). Widening it would
  pollute the deterministic literal gate and break its direct unit tests.
- *Gate inside `conflict.choose`* — rejected: `choose` receives only
  `(FetchedSource, value)` tuples that already passed extraction; gating there
  would duplicate the trust boundary (violates Constitution I) and would run the
  LLM on candidates the locator may already have dropped. See D6.

## D2 — STRUCTURED vs PROSE channel classification (single source of truth)

**Decision**: In `fill/channels/__init__.py`, alongside the existing
`AUTHORITY` dict, add:
```python
STRUCTURED_CHANNELS: frozenset[str] = frozenset({"constants", "oeis", "wikidata"})
def is_structured(channel: str) -> bool: return channel in STRUCTURED_CHANNELS
def is_prose(channel: str) -> bool: return not is_structured(channel)
```
PROSE is everything else, so an unknown/unclassified channel is PROSE
(fail-closed — it gets the stricter gate). The current channels are exactly the
six `AUTHORITY` keys: `constants, oeis, wikidata` (STRUCTURED) and
`wikipedia, theorem, paper` (PROSE).

**Rationale**: One module owns the classification; callers ask `is_prose(channel)`.
Defining PROSE as the complement makes the unknown-channel case fail-closed
automatically (Constitution V / FR-001). Theorem text is full prose where a value
can coincidentally appear, so it is PROSE.

**Alternatives rejected**: a `ChannelKind` enum stored on `FetchedSource` —
rejected: `FetchedSource` is a frozen value object built by six channel modules;
threading an enum through all of them is churn with no benefit over a pure
function keyed on the existing `channel` string.

## D3 — Adapting `assess` to a fetched source

**Decision**: `assess(claim: str, doc, ...)` reads only `doc.full_text or
doc.abstract`. The prose gate builds a minimal shim — a small frozen dataclass
`_SourceDoc(full_text: str, abstract: str = "")` in `fill/relevance.py` — with
`full_text=source.text`, and calls
`assess(claim.canonical or claim.raw_text, _SourceDoc(source.text),
backend=backend, model=model, repo_root=repo_root)`. Accept iff
`verdict.status == "grounded"`; `contradicted`/`not_found`/error → reject.

**Rationale**: `assess` already returns `not_found` on backend/parse error
(verified L130-132), so consuming `status == "grounded"` is inherently
fail-closed (FR-006/FR-010). Passing the canonical text matches the resolve.py
call sites (`assess(canonical, doc, ...)`).

**Alternatives rejected**: reusing `RetrievedDoc` — rejected: it carries
librarian-specific fields the fill layer doesn't have; the two attributes `assess`
actually reads are the entire contract, so a 2-field shim is the minimal honest
adapter.

## D4 — Deterministic subject-relevance pre-filter

**Decision**: In `fill/relevance.py`, before calling `assess`, run a zero-network
co-occurrence check: locate every occurrence of the candidate `value` in
`source.text` (numeric values via `grounding_guard._number_anchor_re(value)` —
the same anchor `locate_passages` uses; entity values via normalized substring
search, reusing the `_entity_present` normalization), and require at least one of
the claim's `subject_keywords` to appear within a ±`_WINDOW` character window of
some occurrence. No keyword co-occurrence near any occurrence → reject (no LLM
call). Reuse the entailment module's `_WINDOW = 320` as the window constant
(single source of truth for "near").

**Rationale**: This rejects "about 6 generations" in an unrelated article
instantly (subject keywords like "knot"/"crossing" never appear near the `6`),
satisfying SC-007 with zero LLM cost (Constitution IV) and shrinking the load on
`assess`. Anchoring on the same regex `assess` uses keeps "where the number is"
consistent between the two layers.

**Alternatives rejected**: skipping straight to `assess` for all PROSE — rejected:
wastes an LLM call on obvious coincidental matches and removes the cheap
deterministic backstop (the spec mandates the pre-filter, FR-005).

## D5 — Claim-kind pre-guard (bound / digit-less), before any fetch

**Decision**: In `fill/service.py::fill_claim`, immediately after the existing
kind guard and before the cache lookup / `subject_query` / channel fetch, refuse
to numeric-fill when, for a NUMERIC claim, the asserted value is a bound/percent
(`claims/canonical._asserted_is_bound_or_percent` over the claim's asserted
token, `_BOUND_PREFIX = "≤≥<>~≈"`) OR the claim asserts no numeric token at all
(`_asserted_value(claim.raw_text or claim.canonical) is None`). Return a `blocked`
`FillResult` with a reason; the claim stays unresolved (the unified marker is
applied by the caller as today).

**Rationale**: Bound/inequality claims ("braid index ≤ crossing number", "≤6")
are not point-valued facts; filling them with a single number is category-wrong.
Catching them before any fetch is the Fail-Fast (Constitution V) and cheapest
defense (FR-002/FR-003/SC-006). The guards already exist in `canonical.py` —
reuse, don't reinvent (Constitution I).

**Alternatives rejected**: relying on the semantic gate alone to catch bounds —
rejected: it would fetch + spend an LLM call to reject something decidable from
the claim text alone, and bound-claims have no single value to ground.

## D6 — FR-008 reconciliation (`conflict.choose` unchanged)

**Decision**: `fill/conflict.choose` is NOT modified. Because `_accept` gates at
extraction, a PROSE candidate that fails relevance/entailment returns `None` from
`extract_value` and never becomes a `(source, value)` candidate. Therefore
`choose` only ever ranks survivors; if no STRUCTURED candidate exists and every
PROSE candidate failed, the candidate list is empty and `fill_claim` blocks via
the existing `[UNRESOLVED-CLAIM:]` marker path.

**Rationale**: FR-008's *intent* — "a relevance-failing PROSE candidate never
wins; all-fail ⇒ blocked" — is satisfied by construction at the single chokepoint.
Adding a second gate inside `choose` would duplicate the trust boundary
(violates Constitution I, NON-NEGOTIABLE) and could only ever reject candidates
already filtered upstream. This is documented in `conflict.py` and called out in
tasks so `/speckit-analyze` sees the deliberate reconciliation, not a coverage gap.

**Alternatives rejected**: a defensive re-check in `choose` — rejected as dead,
duplicative code; the chokepoint invariant makes it unreachable.

## D7 — `subject_keywords` visibility

**Decision**: Promote `claims/canonical._subject_keywords(claim) -> list[str]` to
a public `subject_keywords` (rename + update the internal callers; keep one
implementation). The prose pre-filter imports the public name.

**Rationale**: The spec's reuse contract names `canonical.subject_keywords`. One
public implementation reused everywhere satisfies Constitution I; importing a
private `_`-prefixed helper across packages is a smell the rename removes.

**Alternatives rejected**: duplicating the keyword logic in `relevance.py` —
rejected outright (Constitution I).

## D8 — Offline path behavior (no backend)

**Decision**: On the offline `extract_value` path (`backend is None`, test-only),
`_accept` still runs `present_in_source`; for PROSE channels it additionally runs
the deterministic pre-filter but, lacking a backend, `prose_substantiated`
returns `False` at the `assess` step → PROSE numeric candidates are rejected
offline (fail-closed). STRUCTURED channels are unaffected (no prose gate).

**Rationale**: Production `fill_claim` always supplies a backend, so real PROSE
fills reach `assess`. Keeping the offline path fail-closed prevents a coincidental
offline match from being a loophole (FR-010). The deterministic-layer unit tests
exercise the pre-filter without a backend.

**Risk + mitigation**: existing offline tests in `test_fill_extract_gate.py` may
assume a PROSE numeric candidate is accepted offline. Verified scope: those tests
target `present_in_source` directly and STRUCTURED/entity cases; the implement
step MUST run the full suite and, if any offline PROSE-accept assumption exists,
reclassify that fixture's channel or supply a backend — never weaken the gate.

## Resolved unknowns

| Unknown | Resolution |
|-|-|
| Gate placement | `_accept` in `extract.py`, both `extract_value` sites (D1) |
| Channel kind source of truth | `fill/channels.is_structured/is_prose`, unknown→PROSE (D2) |
| `assess` input adapter | 2-field `_SourceDoc` shim; accept iff `grounded` (D3) |
| Pre-filter "near" window | reuse entailment `_WINDOW=320` (D4) |
| Value-location method | numeric `_number_anchor_re`; entity normalized substring (D4) |
| Pre-guard reuse | `canonical._asserted_is_bound_or_percent`, `_asserted_value` (D5) |
| `conflict.choose` change | none; intent met at chokepoint (D6) |
| keyword helper visibility | promote to public `subject_keywords` (D7) |
| offline/no-backend PROSE | fail-closed reject (D8) |
