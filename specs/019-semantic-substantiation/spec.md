# Feature Specification: Semantic Substantiation for the Claim-Fill Layer

**Feature Branch**: `019-semantic-substantiation`
**Created**: 2026-05-30
**Status**: Draft
**Input**: User description: "Close the literal-presence residual in the claim-fill safety gate. Complete the trustworthiness stack (016 detect → 017 fill → 018 verify-modes) by requiring a PROSE-channel fill/verification to be SEMANTICALLY substantiated — the cited source must actually assert that THIS claim's subject has THIS value — not merely contain the value's digits somewhere in unrelated text."

## Context & Motivation

This feature closes a maintainer-flagged residual in the trustworthiness stack
built by specs [016-claim-verification](../016-claim-verification/spec.md),
[017-claim-auto-correction](../017-claim-auto-correction/spec.md), and
[018-approximate-numeric-verification](../018-approximate-numeric-verification/spec.md).

Today, the fill safety gate (`grounding.service.number_substantiated` →
`grounding_guard.number_appears_in`) is a pure literal digit-boundary regex: it
accepts a candidate value if and only if the value's digits appear as a
standalone token *anywhere* in the fetched source text. This is **correct for
STRUCTURED channels** — the constants alias table, the OEIS b-file read by
index, and a Wikidata statement triple — because in those data structures the
subject↔value link is inherent (the value is returned *for* the subject). It is
**WRONG for PROSE channels** — Wikipedia article text, paper full-text, theorem
prose — where a small integer can coincidentally appear in unrelated text.

**Concrete observed failure (PROJ-552 plan stage):** a crossing-number bound
"≤6" was "verified" against the Wikipedia article on the *Almoravid dynasty*
because the digit `6` appears there in the phrase "about 6 generations" — a
completely unrelated article. The fill gate accepted `6` as substantiated; the
literal regex matched, but nothing in the source asserted that any knot's
crossing number is 6. This residual is recorded in
[notes/spec-015-review-status.md](../../notes/spec-015-review-status.md)
(session 4: "the underlying fill substantiation gate still uses
literal-presence… a body claim could still match a coincidental source… must be
real-call-tested, NOT bolted onto the authoritative layer under time pressure")
and noted as deferred in specs 017 and 018.

The principle this feature enforces: **literal-presence ≠ substantiation for
prose sources.** A PROSE source substantiates a numeric/entity claim only when
it semantically asserts the subject↔value relation.

**Key reuse (do NOT re-implement):**
`grounding/entailment.py::assess(claim, doc, *, backend, model, repo_root)`
already performs semantic entailment via a reasoning LLM and returns
`Verdict.status ∈ {grounded, contradicted, not_found}` (it locates passages via
number-anchor + Jaccard, then asks the model whether the source supports the
claim). It is wired into the 016 resolver
(`claims/resolve.py::resolve_numeric_or_citation`) but NOT into the 017/018 FILL
safety gate (`fill/extract.present_in_source`). This feature's core is to route
PROSE-channel fills through `assess`. It must **EXTEND, not duplicate**.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Coincidental prose number never substantiates a fill (Priority: P1)

The pipeline is resolving an unresolved numeric claim whose only candidate
source is PROSE (a Wikipedia article or paper). The located value's digits
appear in the source, but the surrounding text is about an unrelated subject.
The system must refuse the fill rather than write a wrong value.

**Why this priority**: This is the exact maintainer-flagged bug (the
"≤6 / Almoravid dynasty" failure). It is the reason the feature exists and the
single highest-value behavior. Without it, the trustworthiness stack can still
emit a confidently-wrong "verified" number.

**Independent Test**: Against a live backend, run the fill path on a claim whose
value coincidentally appears in an unrelated PROSE source; assert the fill is
BLOCKED (the unified `[UNRESOLVED-CLAIM:]` marker) and the wrong value is never
returned. Delivers the core safety guarantee on its own.

**Acceptance Scenarios**:

1. **Given** a claim asserting a knot crossing-number bound and a PROSE
   candidate whose only match is "about 6 generations" in an unrelated article,
   **When** the fill gate evaluates the PROSE candidate, **Then** the candidate
   is rejected and the claim remains unresolved (never filled with `6`).
2. **Given** a PROSE candidate where the subject keywords do NOT co-occur near
   the located value, **When** the deterministic relevance pre-filter runs,
   **Then** the candidate is rejected with zero network/LLM calls.
3. **Given** a PROSE candidate that passes the keyword pre-filter but whose
   source does not semantically assert the subject↔value relation, **When**
   `assess` is consulted, **Then** a `not_found`/`contradicted`/error verdict
   REJECTS the candidate (fail-closed).

---

### User Story 2 - Proven-good paths keep working with zero regression (Priority: P1)

The exact-count, constant, and entity-fact paths that specs 016–018 already
prove correct must continue to pass unchanged. STRUCTURED channels carry an
inherent subject↔value link and must be exempt from the new prose gate.

**Why this priority**: A safety tightening that breaks the working
authoritative paths is a net loss. Zero regression on the proven paths is a hard
release gate, co-equal with Story 1.

**Independent Test**: Re-run the existing must-not-regress suites
(`test_exact_count_no_regress.py`, constants/`pi`, entity facts) and confirm all
remain green with the new gate active.

**Acceptance Scenarios**:

1. **Given** the "9,988 prime knots at 13 crossings" claim resolved via the OEIS
   b-file (STRUCTURED), **When** the fill gate runs, **Then** the prose gate is
   SKIPPED and `9988` still fills (spec 018 SC-002 stays green).
2. **Given** `π ≈ 3.14159` from the constants alias table (STRUCTURED), **When**
   the fill gate runs, **Then** the prose gate is SKIPPED and the value fills.
3. **Given** "the capital of France is Paris" with a PROSE source that
   semantically asserts it, **When** `assess` runs, **Then** the verdict is
   `grounded` and `Paris` is kept.

---

### User Story 3 - Bound/inequality and digit-less claims are blocked before any fetch (Priority: P2)

An inequality-bound claim (value preceded by ≤ ≥ < >) or a percentage (value
followed by %) or a digit-less claim is not a fillable point-valued numeric fact.
The fill entry point must refuse to numeric-fill it cheaply and deterministically,
before any network fetch. (Approximation markers ~ ≈ are NOT blocked — an
approximate value is a fillable point value handled by the spec-018 path.)

**Why this priority**: This is a cheap, deterministic pre-guard that eliminates
an entire class of mis-fills (including the "≤6" class and "braid index ≤
crossing number") at near-zero cost, and reduces load on the semantic gate. It
is P2 only because Story 1's semantic gate would also catch many of these — but
catching them earlier is strictly better.

**Independent Test**: Feed a bound claim and a digit-less claim to the fill
entry point; assert each is refused for numeric fill before any fetch occurs.

**Acceptance Scenarios**:

1. **Given** the claim "the braid index is ≤ the crossing number for most
   knots", **When** the fill entry point evaluates it, **Then** numeric fill is
   refused before any source is fetched.
2. **Given** a claim whose `raw_text` asserts no numeric token, **When** the
   fill entry point evaluates it, **Then** numeric fill is refused (no fetch).

---

### User Story 4 - Contradicted prose is corrected, never grounded (Priority: P3)

When a PROSE source semantically contradicts the asserted value, the fill must
not keep the wrong value; if a correct value is available, the existing
correction path supplies it, otherwise the claim stays unresolved.

**Why this priority**: Builds on Story 1's fail-closed gate to handle the
"source says something different" case, exercising the `contradicted` verdict.
Lower priority because the dominant observed failure is coincidental match
(`not_found`-like), not active contradiction.

**Independent Test**: Run a claim asserting a known-wrong value against a PROSE
source that asserts the correct one; confirm the wrong value is never grounded.

**Acceptance Scenarios**:

1. **Given** the claim "the capital of Australia is Sydney" and a PROSE source
   asserting Canberra, **When** `assess` runs, **Then** the verdict is
   `contradicted`, `Sydney` is never grounded, and the resolution yields
   Canberra (or stays unresolved), never Sydney.

---

### Edge Cases

- **Backend error / timeout during `assess`**: treated as REJECT (fail-closed).
  Absence of evidence MUST NOT fill.
- **PROSE source where the value appears but subject keywords are absent
  entirely**: rejected by the deterministic pre-filter without an LLM call.
- **Mixed candidates (one STRUCTURED, one failing PROSE)**: the STRUCTURED
  candidate is selected; the failing PROSE candidate is excluded from conflict
  resolution.
- **All candidates PROSE and all fail relevance/entailment**: fill is BLOCKED
  (unified `[UNRESOLVED-CLAIM:]` marker), never a wrong value.
- **Subject keywords legitimately co-occur but the source still does not assert
  the relation** (keyword pre-filter passes, semantics fail): `assess` REJECTS.
- **A value that is both a coincidental prose match AND a correct structured
  match**: STRUCTURED path wins; prose gate is irrelevant to the structured
  candidate.
- **Channel mis-classification risk**: a single source-of-truth classifier must
  decide STRUCTURED vs PROSE; an unknown/unclassified channel MUST default to
  PROSE (fail-closed — it gets the stricter gate).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST classify every fill channel as exactly one of
  STRUCTURED or PROSE via a single source-of-truth classifier exported from the
  fill-channels module. STRUCTURED = {constants alias table, OEIS b-file by
  index, Wikidata statement triple}; PROSE = {Wikipedia article text, paper
  full-text, theorem prose}. An unknown/unclassified channel MUST be treated as
  PROSE (fail-closed).
- **FR-002**: The fill entry point MUST refuse to numeric-fill an
  inequality-bound or percentage claim — a value preceded (ignoring sign and
  whitespace) by one of `≤ ≥ < >`, or immediately followed by `%` — before any
  source fetch. Approximation markers (`~ ≈`) are EXCLUDED from this block: an
  approximate value such as `π ≈ 3.14159` is a fillable point value resolved via
  the spec-018 approximate path, so it MUST still fill (SC-003). The block reuses
  the `claims/canonical` value/number primitives via a focused
  `_asserted_is_inequality_or_percent` predicate (`_INEQUALITY_PREFIX = "≤≥<>"`),
  leaving the broader correction-time `_asserted_is_bound_or_percent` unchanged.
- **FR-003**: The fill entry point MUST refuse to numeric-fill a digit-less
  claim (whose `raw_text` asserts no numeric token) before any source fetch.
- **FR-004**: For STRUCTURED-channel candidates, the system MUST preserve the
  existing literal-presence behavior unchanged — the subject↔value link is
  inherent — and MUST NOT apply the prose relevance/entailment gate.
- **FR-005**: For PROSE-channel numeric candidates, the system MUST apply a
  deterministic, zero-network subject-relevance pre-filter: the candidate is
  rejected unless the claim's subject keywords (reuse
  `claims/canonical.subject_keywords`) co-occur within a bounded window around
  the located value in the source text.
- **FR-006**: For PROSE-channel candidates that survive literal presence and the
  keyword pre-filter, the system MUST consult
  `grounding/entailment.py::assess` and accept the candidate ONLY when the
  verdict is `grounded`. A `contradicted`, `not_found`, or backend-error result
  MUST reject the candidate (fail-closed).
- **FR-007**: `grounding/entailment.py::assess` MUST be reused unchanged (no edit
  to its entailment logic or `Verdict`). The `claims/canonical.py` bound/value
  guards MUST be reused unchanged; the existing subject-keyword helper MUST remain
  a single implementation, promoted from private `_subject_keywords` to a public
  `subject_keywords` (a visibility rename only, no logic change). New runtime
  behavior is confined to the fill package: it extends `fill/extract.py`,
  `fill/service.py`, the `fill/channels` module, MAY add one focused new module
  `fill/relevance.py` for the prose gate, and leaves `fill/conflict.py`
  functionally unchanged (documented invariant only). No other package's logic is
  modified.
- **FR-008**: Conflict resolution (`fill/conflict.choose`) MUST exclude any
  PROSE candidate that fails the relevance/entailment gate. If no STRUCTURED
  candidate exists and all PROSE candidates fail, the fill MUST be BLOCKED via
  the unified `[UNRESOLVED-CLAIM:]` marker — never a wrong value.
- **FR-009**: The exact-count literal gate (`number_substantiated`) MUST NOT be
  modified or weakened; it is only AUGMENTED for PROSE channels by the layers
  above. The STRUCTURED exact-count path MUST remain byte-for-byte behavior-
  equivalent.
- **FR-010**: Every rejection/blocking path (claim-kind pre-guard, keyword
  pre-filter, semantic gate, conflict exclusion) MUST be fail-closed: on any
  ambiguity, failure, or error the system leaves the claim unresolved rather
  than emitting or keeping a value.

### Key Entities

- **Fill candidate**: a proposed value for an unresolved claim, carrying its
  source channel, the fetched source text (for PROSE), and the located position
  of the value within that text.
- **Channel classification**: the STRUCTURED-vs-PROSE label for a candidate's
  source channel; the single arbiter of whether the prose gate applies.
- **Relevance decision**: the deterministic pass/reject outcome of the
  subject-keyword co-occurrence pre-filter for a PROSE candidate.
- **Entailment verdict**: the `grounded` / `contradicted` / `not_found` result
  from `assess` (plus an error state), governing acceptance of a PROSE survivor.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The "≤6 / Almoravid dynasty" Wikipedia case results in a BLOCKED
  fill (claim stays unresolved); the value `6` is never returned. Verified with
  a real-call negative test.
- **SC-002**: The "9,988 prime knots at 13 crossings" OEIS b-file path still
  fills `9988` (STRUCTURED, gate skipped) — `test_exact_count_no_regress.py`
  stays green (spec 018 SC-002 preserved).
- **SC-003**: `π ≈ 3.14159` (constants, STRUCTURED) still fills.
- **SC-004**: "capital of France is Paris" with a supporting PROSE source yields
  `assess = grounded` and keeps `Paris`.
- **SC-005**: "capital of Australia is Sydney" against a Canberra-asserting PROSE
  source yields `assess = contradicted`; `Sydney` is never grounded.
- **SC-006**: "braid index ≤ crossing number for most knots" is BLOCKED before
  any source fetch (claim-kind pre-guard).
- **SC-007**: 100% of PROSE-channel candidates that pass only on literal digit
  presence (subject keywords absent near the value) are rejected with zero LLM
  calls by the deterministic pre-filter.
- **SC-008**: Zero regressions across the existing must-not-regress suites:
  `tests/unit/test_grounding_service.py`, `tests/unit/test_fill_extract_gate.py`,
  `tests/unit/test_claim_resolve_dispatch.py`,
  `tests/integration/test_exact_count_no_regress.py`,
  `tests/real_call/test_grounding_entailment.py`, plus the full offline gate.

## Assumptions

- The STRUCTURED-vs-PROSE classification is stable and known for every channel
  the fill layer currently uses; a new/unknown channel defaults to PROSE
  (fail-closed) until explicitly classified.
- `grounding/entailment.py::assess` continues to return the documented
  `{grounded, contradicted, not_found}` verdict surface and to locate passages
  via number-anchor + Jaccard; this feature consumes it as-is.
- Real-call verification runs against the live Dartmouth backend
  (`LLMXIVE_REAL_TESTS=1` + key, per repo convention; the backend is free for
  the models used). NO mocks substitute for the semantic gate's real behavior.
- The unified `[UNRESOLVED-CLAIM:]` marker from the 016/017 layer is the single
  blocked-fill outcome; this feature does not introduce a new marker.
- Subject keywords from `claims/canonical.subject_keywords` are sufficient to
  express subject relevance for the co-occurrence pre-filter; the window size is
  a tunable detail to be fixed in planning, not a scope question.
