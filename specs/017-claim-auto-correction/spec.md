# Feature Specification: Authoritative-Fill / Claim Auto-Correction

**Feature Branch**: `017-claim-auto-correction`
**Created**: 2026-05-30
**Status**: Draft
**Input**: User description: "When an external factual claim can't be verified as written, the system should look up the correct value from an authoritative source and substitute it — instead of only blocking the document. The substituted value must come from a real, fetched source (never the model's memory), or the claim stays blocked."

## Context & Motivation

llmXive is an **automated** scientific-discovery pipeline; its core promise is **trustworthy** science, not "AI slop" with no factual basis. Spec 015's Part-7 end-to-end shakeout surfaced a show-stopping gap: doc-producing agents **fabricate factual claims**. Concretely (real run, 2026-05-30, recorded in [`notes/spec-015-review-status.md`](../../notes/spec-015-review-status.md), "In-situ run #1" + "F-20"): asked to fix a fabricated knot-count citation, the spec reviser invented "**27,635** prime knots at 13 crossings" (the correct count is **9,988**, OEIS A002863) attributed to a non-resolvable author-year reference.

Spec 016 ([`specs/016-claim-verification/`](../016-claim-verification/)) built the **detective** half: the claim-verification layer extracts every check-worthy claim, registers it, substitutes a pointer, resolves it, and renders the unified `[UNRESOLVED-CLAIM:]` marker + hard-block gate when a claim cannot be verified. But spec 016's **external** resolvers are **check-only**: for a numeric/relational claim they return `verified | refuted | not_enough_info` with `resolved_value = None` — they only verify the model's value against the *cited* source and never **derive** the correct value. Verified live (2026-05-30): the real document-write chokepoint extracted the "27,635" fabrication, resolved it to `not_enough_info` ("no resolvable source identifier found"), and blocked it with the unified marker — but it did **not** replace it with the correct 9,988. (By contrast, spec 016's *internal-result* resolver already positively substitutes a receipt's value; external claims do not.)

This spec adds the **constructive** complement that 016 deferred: when an external claim is unresolved or refuted, the system **searches authoritative sources, extracts the substantiated value, verifies that value is literally present in a real fetched source, substitutes the corrected value via the existing claim pointer, and records its provenance** — so a fabricated value is replaced by a sourced one (e.g., 27,635 → 9,988), or the claim stays blocked only when no authoritative value can be found. This realizes the original "fact-finder/librarian **fill** + check → cached value used 'for free' as pointers" vision from tracking **issue #256**, and builds directly on spec 016's registry, resolver, cache, and gating. It does **not** replace 016 — the detective layer remains the safety net.

## Clarifications

### Session 2026-05-30

- Q: When two authoritative sources disagree on a value, what should v1 do? → A: **Channel-priority + record** — trust a fixed channel authority order (curated reference > paper search), take the higher-authority source's value, and record the disagreement in provenance; never silently drop the conflict.
- Q: Which claim types does the fill/correct step cover in v1? → A: **Numeric/statistic + entity/definitional first** (the demonstrated path); magnitude/superlative and set/relational are a fast-follow (their candidate-set / triple extraction is harder).
- Q: Which curated reference sources does v1 wire (beyond paper search)? → A: **OEIS + Wikipedia + Wikidata**, plus **theorem search** for math/theorem claims (the TheoremSearch backend already exists — spec 006, `librarian/theoremsearch.py` — and returns resolvable paper `Candidate`s, so it is a low-effort additional channel; included where the claim is math-classified).
- Q: On a successful fill, what does the rendered document show? → A: **Value + repair citation** — substitute the corrected value AND repair the surrounding citation to the authoritative source (e.g., 9,988 cited to OEIS A002863), so the wrong number and its bogus citation are fixed together.

## User Scenarios & Testing *(mandatory)*

> "Users" here = the automated pipeline and the eventual human consumers of llmXive's published science. The value is **trustworthiness**: a wrong factual value is not merely blocked but, wherever an authoritative source exists, **corrected to the sourced truth** — and a correction is never itself a fabrication.

### User Story 1 - A fabricated value is auto-corrected from a real source (Priority: P1)

When an agent writes a factual value that cannot be verified as written (no resolvable cited source, or the cited source does not support it), the system searches authoritative sources for the claim's subject, finds the correct value, confirms that value appears in a fetched source, and substitutes the corrected value into the document with its provenance — so the document advances with the *sourced* value rather than blocking and waiting for a reviser to re-guess.

**Why this priority**: This is the MVP and the direct completion of the fabrication fix. Spec 016 stops the bad value; this turns "blocked" into "corrected," which is what makes the pipeline both trustworthy *and* able to make progress without re-guessing.

**Independent Test**: Run the claim layer on the project that fabricated "27,635 prime knots at 13 crossings"; confirm the rendered document shows the verified **9,988** (drawn from a resolvable source whose fetched text contains 9,988) with that source recorded as provenance — and never shows 27,635 and never requests human input.

**Acceptance Scenarios**:

1. **Given** a numeric claim whose written value is wrong/unverifiable but whose subject has an authoritative source, **When** the fill step runs, **Then** the system retrieves a resolvable source, confirms the correct value is present in the fetched text, sets the claim's resolved value to that sourced value, and the rendered document shows the corrected value with provenance.
2. **Given** a claim whose subject has **no** discoverable authoritative source after the available channels are exhausted, **When** the fill step runs, **Then** the claim stays blocked (the unified marker remains) — the system never invents a fill — and no human input is requested as routine flow.
3. **Given** a claim the model wrote **correctly** but without a resolvable citation, **When** the fill step runs, **Then** the system confirms the value against a fetched authoritative source and lets it advance (verified), rather than blocking a true statement.

### User Story 2 - A filled value is always traceable to a fetched source, never to model memory (Priority: P1)

Every corrected value is bound to a specific authoritative source and the supporting passage/value within it; the model never supplies the replacement value from its own memory or inference. If the candidate value cannot be located in fetched source text, it is not used.

**Why this priority**: The entire point is trustworthiness. A fill that fabricates is strictly worse than a block — it is a *more confident* hallucination. This safety property is co-equal with US1.

**Independent Test**: Force the search to return a source whose fetched text does **not** contain the model's proposed value; confirm the value is rejected (not filled) and the claim stays blocked. Inspect any successful fill and confirm its recorded provenance (source id/URL + the supporting quote/number) and that the value is literally present in the fetched source text.

**Acceptance Scenarios**:

1. **Given** a candidate fill value, **When** it cannot be located (by a deterministic presence check) in the fetched text of a resolvable source, **Then** it is discarded and the claim is not filled.
2. **Given** a successful fill, **When** the claim is inspected, **Then** it carries provenance: the source identifier/URL and the exact supporting passage or number, and the source is independently resolvable.

### User Story 3 - Non-numeric claims are corrected too (Priority: P2)

Magnitude/superlative ("the largest"), set/relational ("X is the capital of Y"), and entity/definitional claims are auto-corrected by the same fetch-and-verify discipline — the corrected term/answer must appear in a fetched authoritative source — not only numeric statistics.

**Why this priority**: Non-numeric claims are at least as common; trustworthiness requires covering them. But the numeric path (US1) is the acute, demonstrated blocker, so it leads.

**Independent Test**: Provide a wrong relational claim and a wrong superlative claim, each with a discoverable authoritative source; confirm each is corrected to the sourced answer with provenance, and that a wrong claim with no source stays blocked.

**Acceptance Scenarios**:

1. **Given** a wrong superlative/comparative claim with an authoritative candidate set available, **When** filled, **Then** the corrected extreme is taken from the fetched source set and substituted.
2. **Given** a wrong relational (subject–relation–object) claim, **When** filled, **Then** the corrected object is the one stated in a fetched authoritative source.

### User Story 4 - Corrected values are reused "for free" and never drift (Priority: P3)

A filled value is cached against its claim and source, reused across rounds, stages, and documents without re-searching, and invalidated when its underlying source changes — mirroring spec 016's verified-value reuse.

**Why this priority**: Efficiency + consistency; valuable but depends on US1/US2 existing first.

**Independent Test**: Fill a claim once; reference the same claim in a later document and confirm it renders the identical cached corrected value with no new search; change the underlying source and confirm the cached fill is invalidated and re-derived.

**Acceptance Scenarios**:

1. **Given** a previously filled claim referenced again, **When** the second document renders, **Then** it shows the identical corrected value from cache with no new search call.

### Edge Cases

- **Multiple authoritative sources disagree** on the value → see FR-008 (conflict handling); the system must not silently pick one and present it as settled.
- **A source resolves but its fetched text does not contain the candidate value** → the candidate is rejected; never fill from a source that doesn't state the value.
- **The correct value is found but is itself a range or approximate** ("about 10,000") → fill the sourced expression faithfully; do not fabricate false precision.
- **Search returns only the same non-resolvable/free-text source the agent already cited** → no fill; stays blocked (distinct from "filled").
- **The claim's subject is genuinely novel/unknowable** (a result that does not yet exist, an open question) → no authoritative source → stays blocked; this is correct, not a failure.
- **A filled value would contradict a backing internal result receipt** (spec 016) → the receipt wins; an external fill never overrides a harness-signed internal result.
- **Channel/retry budget exhausted** → block (not human-escalate), consistent with spec 016 FR-014 (human input is rare, publication-only).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: When an external claim resolves to `not_enough_info` or `refuted` under the spec-016 resolvers, the system MUST attempt an **authoritative fill** before leaving the claim blocked.
- **FR-002**: The fill MUST follow the loop: derive a subject query (the claim minus its asserted value) → search authoritative sources → select the best candidate source(s) → fetch source text → extract the candidate value → **verify the candidate value is literally present in the fetched source text** → set the claim's resolved value + provenance → render the corrected value. If any step yields nothing usable, the claim stays blocked.
- **FR-003**: A filled value MUST be extracted from, and present in, a **resolvable** authoritative source's fetched text. The system MUST NOT use a value supplied from a model's memory or inference, and MUST NOT use a value that cannot be located in fetched source text (reuse spec 016's deterministic presence gate for numbers; an equivalent located-in-source check for non-numeric values).
- **FR-004**: Every fill MUST record provenance: the source identifier/URL and the exact supporting passage or number that substantiates the value. Provenance MUST be inspectable and the source independently resolvable.
- **FR-005**: The system MUST search across these source channels: (a) academic paper search (reusing the librarian's paper search), and (b) curated reference sources — **OEIS** (integer-sequence/combinatorial counts, e.g. the prime-knot count), **Wikipedia**, and **Wikidata** (general reference + relational facts). It MUST additionally use **theorem search** as a channel for math-classified claims (reusing the existing TheoremSearch backend, which returns resolvable paper candidates). Every channel MUST yield a resolvable source whose fetched text contains the value.
- **FR-006**: The fill MUST support, in v1, **numeric/statistic** and **entity/definitional** claim types. **Magnitude/direction/superlative** and **set/relational** fills are a fast-follow (deferred past v1; their candidate-set / subject–relation–object extraction is harder) — until then, such claims remain blocked by spec 016 rather than filled. (Citation/existence is already handled by spec 016's F-18; internal empirical results already fill from harness-signed receipts and are out of scope here.)
- **FR-007**: On a successful fill, the system MUST render the corrected value via spec 016's existing claim pointer (the model never retypes it) AND repair the surrounding citation to the authoritative fill source (the document shows the corrected value cited to the source the value was drawn from — e.g., 9,988 cited to OEIS A002863). The corrected, sourced value is what advances past the gate.
- **FR-008**: When more than one authoritative source is found and they **disagree** on the value, the system MUST take the value from the **higher-authority channel** by a fixed channel order (**curated reference > paper search**; within curated reference, the more authoritative/specific source for the fact class — e.g. OEIS for a sequence count) and MUST record the disagreement (the competing value(s) + their sources) in the fill provenance. The system MUST NOT silently drop the conflict or present a contested value as if it were uncontested.
- **FR-009**: Filled values MUST be cached against the claim and source, reused across rounds/stages/documents without re-searching, and invalidated when the underlying source changes (reuse the spec-016 cache + invalidation model).
- **FR-010**: An external fill MUST NOT override a value backed by a spec-016 internal-result receipt; receipt-backed results take precedence.
- **FR-011**: Automated fill attempts MUST be governed by a bounded channel/retry budget; on exhaustion the claim stays blocked (the spec-016 unified marker remains). Human escalation is reserved for publication sign-off or genuinely-exhausted cases — never routine flow.
- **FR-012**: The fill layer MUST reuse spec-016 / librarian / grounding infrastructure rather than re-implementing search, retrieval, presence-checking, rendering, caching, or gating.
- **FR-013**: All correctness MUST be demonstrated with real-call tests against real sources and real searches (no mocked search, retrieval, or extraction). Any external reference (curated-API URLs, etc.) introduced into the spec or code MUST be independently verified before use.
- **FR-014**: The headline behavior MUST be demonstrated end-to-end: the "27,635 prime knots at 13 crossings" fabrication is auto-corrected to a sourced **9,988** (with provenance), the rendered document shows 9,988 and never 27,635, and no human input is requested.
- **FR-015**: v1 ships **numeric/statistic + entity/definitional** fills (see FR-006); magnitude/superlative and set/relational are an explicit fast-follow and MUST NOT silently appear "covered" while deferred (a deferred type stays blocked by spec 016, never falsely filled). The headline numeric scenario (FR-014) is in v1 scope.

### Key Entities *(include if feature involves data)*

- **Fill Attempt**: one automated effort to correct a single unresolved claim; has the claim it targets, the channels tried, the candidate sources fetched, the extracted candidate value(s), the presence-check outcome, and a terminal result (filled | blocked).
- **Authoritative Source (fetched)**: a resolvable source whose text was actually retrieved; carries its identifier/URL, the fetched text (or the located passage), and the value located within it.
- **Fill Provenance**: the binding recorded on a corrected claim — source identifier/URL + the exact supporting passage/number — that makes the corrected value traceable and re-checkable.
- **Source Channel**: a strategy for finding authoritative sources for a claim's subject (paper search; curated reference; optional theorem search), each producing resolvable candidate sources.
- **(Reused) Claim / Claim Registry / Claim Pointer / Resolver** from spec 016 — the fill sets a claim's resolved value + provenance and lets the existing pointer render it.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: On the project that fabricated "27,635 prime knots," the document advances showing the verified **9,988** sourced from a resolvable reference (provenance recorded), with no 27,635 anywhere and no human-input request.
- **SC-002**: **Zero** fills are sourced from model memory: 100% of filled values are located in the fetched text of a resolvable source, with provenance recorded (verified by inspecting every fill in the test set and by the forced-absent-value test rejecting the fill).
- **SC-003**: A claim with no discoverable authoritative source is correctly left blocked (never fabricated a fill) — demonstrated by a known-unknowable claim staying blocked.
- **SC-004**: Each v1-supported claim type (numeric, entity/definitional) is corrected from a real source for a known-wrong instance, with provenance; a deferred type (superlative, relational) is confirmed to remain blocked (not falsely filled).
- **SC-008**: A successful fill repairs the citation: the rendered document cites the corrected value to the authoritative fill source (the source the value was located in), not the original bogus reference.
- **SC-005**: A corrected value referenced in a second document renders identically from cache with no new search call; changing the underlying source invalidates and re-derives it.
- **SC-006**: Routine operation requires zero human interventions for fills across an end-to-end run; blocking (not escalation) is the outcome when no source is found.
- **SC-007**: When authoritative sources disagree, the system's recorded outcome matches the chosen conflict policy (FR-008) — it never silently presents a contested value as settled.

## Assumptions

- This builds on, and reuses, spec 016 (the claim registry, resolvers, deterministic presence gate, pointer/render, cache + invalidation, and convergence/kickback gating) and the librarian (query extraction, paper search, relevance judging) and grounding (full-text retrieval, number-substantiation) modules. It is the constructive complement to 016's detective controls, not a replacement.
- **Source channels in v1** (clarified): paper search (librarian) + curated reference sources **OEIS** (integer-sequence/combinatorial counts), **Wikipedia**, **Wikidata** (general + relational reference facts), + **theorem search** for math-classified claims. Channel authority order for conflicts is **curated reference > paper search** (FR-008). Every channel must yield a *resolvable* source whose fetched text contains the value. Any specific endpoint/URL (OEIS/Wikipedia/Wikidata APIs) is WebFetch-verified before use. OEIS + Wikipedia + Wikidata require new lightweight search/fetch integrations; theorem search is already built (below).
- **Theorem search readiness** (assessed 2026-05-30): the TheoremSearch backend already exists and is low-effort to reuse — `librarian/theoremsearch.py::TheoremSearchClient.search(term)` returns resolvable librarian `Candidate`s (arXiv-sourced theorem hits), is wired into the librarian with failure-fallthrough, rate-limited, and tested (spec 006); `librarian/math_classifier.py` already detects math claims. It is therefore included as a v1 channel for math-classified claims (it resolves to *papers*, so it complements OEIS for reference counts rather than replacing it). The theorem-statement *agent* layer (issue #114) remains deferred and is **not** a dependency.
- "Authoritative" = reachable by the librarian/curated channels and independently resolvable; a free-text or non-resolvable reference is never an acceptable fill source.
- Real-call testing (no mocked search/retrieval/extraction) is required, consistent with the repository's testing methodology and constitution.
- Human input remains rare (publication sign-off or genuinely-exhausted cases), consistent with spec 016 FR-014.

## Dependencies

- **Spec 016** (`specs/016-claim-verification/`) and its claim registry, external resolvers, deterministic presence gate, pointer/render, cache, and gating (PR series on `015-pipeline-convergence-protocol`).
- The **librarian** (`query_extractor`, `search`, `relevance_judge`) and **grounding** (`full_text`, `service.number_substantiated`, `cache`) modules.
- **Spec 006** `theoremsearch-backend` + `librarian/theoremsearch.py` (optional theorem channel); **issues #113/#114** (theorem search backend / deferred agent) for context only.
- Planning/motivation context: tracking **issue #256** (the pivot + 3-agent prior-art synthesis), [`notes/spec-015-review-status.md`](../../notes/spec-015-review-status.md), and the spec-016 design doc.
