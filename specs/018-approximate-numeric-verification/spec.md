# Feature Specification: Per-Claim Verification Modes — Approximate-Numeric, Computational & Magnitude/Relational

**Feature Branch**: `018-approximate-numeric-verification`
**Created**: 2026-05-30
**Status**: Draft
**Input**: User description: "Complete the spec-017 fast-follow (magnitude/superlative + set/relational fills); add a precision-aware verification mode for approximate/irrational numeric values (pi, e, physical constants) where multiple roundings are correct (library-backed constants table, pre-seeded); AND add a computational verification mode that EVALUATES self-contained claims (arithmetic, comparisons, unit conversions) — e.g. catch '1 plus 2 is 1' and '1 is larger than 2' as wrong by computing them, rather than only being able to block them as unsourceable."

## Context & Motivation

llmXive is an **automated** scientific-discovery pipeline whose core promise is **trustworthy** science, not "AI slop." Spec 016 ([`specs/016-claim-verification/`](../016-claim-verification/)) built the **detective** claim layer (extract → register → resolve → block unverifiable claims via the unified `[UNRESOLVED-CLAIM:]` marker). Spec 017 ([`specs/017-claim-auto-correction/`](../017-claim-auto-correction/)) added the **constructive** authoritative-fill layer (search authoritative sources, extract the correct value, verify it is literally present in a fetched source, substitute it + repair the citation; never fill from model memory). Spec 017 shipped **numeric + entity/definitional** fills in v1 and **explicitly deferred** two claim types as a fast-follow (FR-006/FR-015): **magnitude/superlative** and **set/relational**. This spec delivers that fast-follow AND closes a verification gap the spec-017 gate cannot handle.

**The approximate-numeric gap** (maintainer-flagged): spec 017's safety gate is a deterministic **literal-substring** presence check ("is this exact string in the fetched text?"). That is correct for **exact/discrete counts** (9,988 prime knots at 13 crossings — verified live in spec 017) but **wrong for approximate/continuous real-valued quantities** (irrational constants like π, e, the golden ratio; physical constants; measured quantities). For those, **multiple claimed values can all be correct** depending on stated precision: "π is about 3", "π is 3.14", "π is 3.14159" are **all** valid roundings of π; "π is 3.15" is **wrong**. The literal gate passes "3.14" by luck (substring of "3.14159"), passes "π is about 3" spuriously ("3" is everywhere), and could wrongly block a correct "3.0". Approximate numbers need **precision-aware** verification: a value is correct iff it is a valid **rounding/truncation of the true value to the claim's stated precision** (significant figures / decimal places), with hedges ("about", "approximately", "roughly", "~", "≈") relaxing the tolerance.

**Where the true value comes from**: for well-known constants the authoritative true value is **built into standard libraries** (mathematical constants via the language's math library at double precision; physical constants via a CODATA-backed constants table). A library constant is a **deterministic, reproducible, citable authority** (IEEE-754 / NIST CODATA) — **not** model memory — so it is a legitimate (indeed higher) authoritative source than web prose, and it can be **pre-seeded** into the resolution cache. Quantities not in the curated table fall back to spec-017 source retrieval (Wikipedia/Wikidata/papers).

**The computational gap** (maintainer-flagged): all verification in specs 016/017 is **source-based** — it confirms a claim by *finding it in an authoritative source*, never by *computing* it. So a **self-contained, evaluable** claim — arithmetic ("1 plus 2 is 1"), a comparison ("1 is larger than 2"), a unit conversion ("5 km is 5,200 m"), a percentage ("30% of 200 is 80") — cannot be sourced, so today it merely **blocks as unverifiable**: the system cannot distinguish the *true* "1 plus 1 is 2" from the *false* "1 plus 2 is 1" (it blocks both), and it cannot actively flag "1 is larger than 2" as **wrong** — only as un-sourceable. The right tool is to **evaluate the claim directly** with a safe deterministic evaluator and compare to the asserted result. Evaluation is *more* trustworthy than source lookup or LLM entailment here, because it is deterministic and reproducible — the **computation itself is the authority** (the same trust basis as a library constant), provided the evaluation is performed by code (never by the LLM asserting a result). This is a distinct verification **mode** from both literal-presence (exact counts) and precision-aware comparison (approximate constants).

**The unifying idea**: the verifier **selects a mode per claim** — *exact-count* (literal presence, spec-017, unchanged), *approximate-constant* (precision-aware rounding, US1/US2), *computational* (evaluate, US5), or *source-fact* (search + ground, specs 016/017) — plus the magnitude/relational fills (US3/US4). Picking the wrong mode is the core risk this spec addresses.

This spec **extends** specs 016/017 (it reuses their registry, resolvers, triple logic, fill service, channels, conflict/citation-repair, and present-in-source gate); it does not replace them. Tracking context: **issue #256**, [`notes/spec-015-review-status.md`](../../notes/spec-015-review-status.md).

## Clarifications

### Session 2026-05-30

- Q: How should the verifier classify a claim into a mode (exact-count / approximate-constant / computational / source-fact)? → A: **Hybrid** — deterministic heuristics first (hedge words, decimal/scientific notation, recognized-constant lookup, a self-contained-expression detector), falling to an LLM classifier ONLY when the heuristics are ambiguous.
- Q: How is an approximate value judged correct against the true value? → A: **Round-to-stated-precision match** — round the true value to the claim's stated precision (sig figs / decimals); VERIFIED iff it equals the asserted value; a hedge ("about/~") widens tolerance by one extra place.
- Q: What does the curated constants table cover in v1? → A: **Math + physical (CODATA), double precision** — mathematical constants (π, e, τ, golden ratio) from the std math library + physical constants (c, h, G, …) from `scipy.constants`; ~15–16 sig figs; claims beyond that fall back to source retrieval.
- Q: What computational forms does the safe evaluator handle in v1? → A: **Broadest** — arithmetic + comparisons + percentages + basic unit conversions + simple **symbolic/algebraic identities and set/logic relations**. This adds a `sympy` dependency (free/open-source) which unifies safe symbolic parsing, identity checking, units (`sympy.physics.units`), and logic/sets; numeric forms still use a safe AST/`sympy` path (never `eval`/`exec`).

## User Scenarios & Testing *(mandatory)*

> "Users" = the automated pipeline and the eventual human consumers of llmXive's published science. The value is **trustworthiness**: harder claim types (superlatives, relations, approximate constants) are verified and corrected to the sourced truth, and a correct approximation is never falsely "corrected."

### User Story 1 - Approximate/irrational numeric values are verified by precision, not by substring (Priority: P1)

A claim asserting an approximate/real-valued quantity is judged correct iff its value is a valid rounding/truncation of the true value to the claim's stated precision (hedges widen the tolerance); a value outside that tolerance is refuted and corrected to a properly-rounded sourced value. Exact discrete counts continue to use exact matching unchanged.

**Why this priority**: This is the maintainer-flagged correctness gap and the riskiest to get wrong (a fragile gate either falsely passes wrong values or falsely blocks correct ones). It must not regress the exact-count path (the 9,988 scenario).

**Independent Test**: "π is 3.14", "π is about 3", "π is 3.14159" all verify; "π is 3.15" and "e is 2.5" are refuted and corrected to sourced values (3.14159… / 2.71828…); "9,988 prime knots at 13 crossings" still verifies by exact match (no regression).

**Acceptance Scenarios**:

1. **Given** an approximate-numeric claim whose value is a valid rounding of the true value to its stated precision, **When** verified, **Then** it is VERIFIED (no false correction), with the true source recorded as provenance.
2. **Given** an approximate-numeric claim whose value is NOT a valid rounding (outside tolerance), **When** verified, **Then** it is refuted and corrected to a properly-rounded value drawn from the authoritative source, with provenance.
3. **Given** an exact discrete-count claim, **When** verified, **Then** the existing exact-match gate is used unchanged (no regression).
4. **Given** a hedged claim ("about 3"), **When** verified, **Then** the rounding tolerance is relaxed accordingly so a coarser-but-valid rounding passes.

### User Story 2 - Well-known constants resolve from a library-backed curated source (Priority: P1)

For recognized mathematical/physical constants, the true value is taken from a curated, library-backed constants table (pre-seeded), so verification is deterministic and offline-fast, without scraping — while remaining a citable authority.

**Why this priority**: It makes US1 reliable and deterministic for the most common approximate values (π, e, c, …) and avoids brittle web retrieval for facts the standard library already encodes authoritatively.

**Independent Test**: π and e claims resolve against the curated constants table with no network call; the recorded provenance names the authority (e.g. the math-library constant / CODATA), and the true value matches the library value.

**Acceptance Scenarios**:

1. **Given** a claim about a recognized constant, **When** verified, **Then** the true value is read from the curated constants table (no web fetch) and provenance names that authority.
2. **Given** an approximate quantity NOT in the curated table, **When** verified, **Then** the system falls back to spec-017 source retrieval (and blocks if none is found).

### User Story 3 - Magnitude/superlative claims are verified and corrected (Priority: P2)

A magnitude/comparative/superlative claim ("the largest/most/earliest/greatest X is Y") is verified by retrieving the relevant candidate set from an authoritative source, computing the ordering, and confirming the asserted extremum — and corrected to the sourced correct extremum when wrong (or blocked when no authoritative candidate set is found).

**Why this priority**: One of the two explicitly-deferred spec-017 claim types; common and not verifiable by single-statement entailment.

**Independent Test**: "the largest planet is Saturn" → corrected to "Jupiter" with provenance; a superlative with no retrievable candidate set stays blocked (not falsely filled).

**Acceptance Scenarios**:

1. **Given** a wrong superlative with a retrievable candidate set, **When** verified, **Then** the correct extremum from the fetched set replaces the asserted one, with provenance.
2. **Given** a superlative whose candidate set cannot be retrieved, **When** verified, **Then** the claim stays blocked.

### User Story 4 - Set/relational claims are verified and corrected (Priority: P2)

A relational claim ("X is the capital of Y", "X wrote Y", "X is a subclass of Y") is decomposed to a subject–relation–object triple, the correct object is looked up in an authoritative source (structured statements primarily), verified present in the fetched source, and corrected when wrong (or blocked when unsourceable).

**Why this priority**: The second explicitly-deferred spec-017 claim type; entity fills already proved the channel path in 017, this extends it to the triple form.

**Independent Test**: "the capital of Australia is Sydney" → corrected to "Canberra" (relational triple form) with provenance; an unsourceable relation stays blocked.

**Acceptance Scenarios**:

1. **Given** a wrong relational claim with a discoverable object, **When** verified, **Then** the correct object from the fetched authoritative source replaces the asserted one, with provenance.
2. **Given** a relational claim that cannot be sourced, **When** verified, **Then** it stays blocked.

### User Story 5 - Self-contained computational claims are verified by evaluation, not source lookup (Priority: P1)

A claim that can be evaluated from its own content — arithmetic, a numeric comparison, a unit conversion, a percentage, a simple set/logic relation — is verified by **computing** it with a safe deterministic evaluator and comparing to the asserted result; a wrong result is refuted and corrected to the computed value. This catches errors that are unsourceable and therefore invisible to source-based verification.

**Why this priority**: It closes a correctness hole the maintainer demonstrated ("1 plus 2 is 1" and "1 is larger than 2" must be caught as *wrong*, not merely blocked); evaluation is deterministic and is the only mode that can distinguish a true self-contained computation from a false one.

**Independent Test**: "1 plus 1 is 2" → VERIFIED; "1 plus 2 is 1" → REFUTED and corrected to 3; "1 is larger than 2" → REFUTED; "30% of 200 is 60" → VERIFIED; "5 km is 5,200 m" → REFUTED and corrected to 5,000 m — all by deterministic computation, with NO source lookup and NO model-asserted result.

**Acceptance Scenarios**:

1. **Given** a self-contained computational claim whose asserted result equals the safely-computed result, **When** verified, **Then** it is VERIFIED, with the evaluated expression recorded as provenance (deterministic, reproducible).
2. **Given** a self-contained computational claim whose asserted result differs from the computed result, **When** verified, **Then** it is REFUTED and corrected to the computed value (rendered via the pointer), with the computation recorded as provenance.
3. **Given** a computational claim that is real-valued, **When** verified, **Then** the comparison reuses the precision-aware (US1) tolerance so a correctly-rounded result still verifies.
4. **Given** a claim the safe evaluator cannot parse or evaluate (not actually self-contained, or unsupported form), **When** verified, **Then** it falls back to source-based verification (specs 016/017) or blocks — it is NEVER guessed or evaluated by the LLM.

### Edge Cases

- A claim states more precision than the curated/source true value provides (e.g. π to 40 digits when only ~15 are available) → verify to the available precision; if the claim's extra digits cannot be confirmed from a source, do not assert beyond what is sourced (block the unconfirmable portion rather than guess).
- An exact-vs-approximate misclassification risk → the classifier must default safely: when uncertain, prefer the EXACT gate for integer-valued discrete claims (never loosen a count) and the APPROXIMATE gate only when the quantity is clearly real-valued/continuous or a recognized constant.
- A hedged claim with an absurd value ("π is about 5") → still refuted; hedges relax tolerance modestly, not unboundedly.
- A superlative whose ordering depends on an unstated criterion ("largest" by area vs population) → resolve against the criterion the claim implies; if ambiguous and unsourceable for the implied criterion, block.
- A relational claim with multiple valid objects (a country with multiple official languages) → a claimed object that is one of the sourced valid objects is VERIFIED, not "corrected" to a single canonical one.
- The exact-count path (spec 017's 9,988) MUST NOT regress — exact discrete claims keep exact matching.
- A filled/verified approximate value must still trace to a real source (library constant or fetched source) — never model memory.
- A computational claim that is only *partly* self-contained (mixes an arithmetic relation with an external fact) → evaluate the computable part and source-verify the factual part; if either fails, block.
- A degenerate/unsafe computation (division by zero, overflow, an unparseable or unsupported expression) → do NOT evaluate; fall back to source-based verification or block. The evaluator MUST be a safe parser (no `eval`/`exec`; the LLM never supplies the computed result).
- A "computational" string that is actually a definition/identity from a source ("Euler's identity is e^{iπ}+1=0") → treat as the claim states; a checkable numeric identity may be evaluated, otherwise source-verify.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST select a **verification mode** per claim from: **exact-count** (literal presence), **approximate-constant** (precision-aware rounding), **computational** (safe evaluation, FR-014), or **source-fact** (search + ground, specs 016/017). Numeric claims are first triaged as exact vs approximate vs computational; self-contained evaluable claims route to the computational mode. Mode selection MUST be **hybrid**: deterministic heuristics first (hedge words, decimal/scientific notation, recognized-constant lookup, a self-contained-expression detector), falling to an LLM classifier ONLY when the heuristics are ambiguous.
- **FR-002**: For an **approximate** claim, the system MUST verify the asserted value against the true value using a **precision-aware** comparison: the value is correct iff it equals the true value rounded/truncated to the claim's stated precision (significant figures / decimal places), within a tolerance that hedge words widen. The tolerance model is **round-to-stated-precision match**: round the true value to the claim's stated precision (significant figures / decimal places); VERIFIED iff it equals the asserted value. A hedge ("about", "approximately", "~", "≈", "roughly", "around") widens the tolerance by **one extra place** (i.e. a coarser-but-valid rounding also passes).
- **FR-003**: For an **exact** claim, the system MUST continue to use the spec-017 exact/literal presence gate UNCHANGED — the 9,988-prime-knots scenario MUST NOT regress.
- **FR-004**: The true value for an approximate claim MUST come from an authoritative source — a **curated, library-backed constants table** for recognized mathematical/physical constants (deterministic, citable as IEEE-754 / CODATA / equivalent), or, for quantities not in the table, spec-017 source retrieval (Wikipedia/Wikidata/papers). The true value MUST NEVER come from model memory/inference.
- **FR-005**: The curated constants table MUST be **pre-seeded** (available without a network call) and MUST record, per constant, its high-precision value and a citable authority; it MUST be the highest-authority source for the constants it covers. v1 coverage is **mathematical constants** (π, e, τ, golden ratio) from the standard math library AND **physical constants** (c, h, G, …) from a CODATA-backed table (`scipy.constants`), at **double precision** (~15–16 significant figures). Claims stating more precision than the table provides fall back to source retrieval (no arbitrary-precision dependency in v1).
- **FR-006**: On a refuted approximate claim, the system MUST correct it to a value drawn from the authoritative true value, **rounded to the claim's stated precision** (so the correction reads naturally — "3.15" → "3.14", not the full 15-digit expansion), and render it via the spec-017 pointer + repair the citation to the authority.
- **FR-007**: A correct approximation MUST NOT be "corrected": if the asserted value is already a valid rounding within tolerance, it is left as written (verified), not replaced.
- **FR-008**: The system MUST enable **magnitude/superlative** claim fills: retrieve the relevant candidate set from an authoritative source, compute the ordering, verify the asserted extremum, and correct to the sourced extremum when wrong; block when no candidate set is retrievable.
- **FR-009**: The system MUST enable **set/relational** claim fills: decompose to a subject–relation–object triple, look up the correct object in an authoritative source (structured statements primarily, prose secondarily), verify it present in the fetched source, and correct the object when wrong; block when unsourceable. A claimed object that is one of several sourced-valid objects is VERIFIED (not over-corrected).
- **FR-010**: After this spec, the fill layer MUST treat magnitude/superlative and set/relational as fillable claim kinds (removing the spec-017 v1 deferral); any claim kind whose authoritative source cannot be found still BLOCKS (never falsely filled).
- **FR-011**: The safety property MUST hold for every mode: a verified/filled value (exact, approximate, superlative, or relational) MUST trace to a real authoritative source (library constant or fetched source) recorded as provenance; nothing is verified or filled from model memory.
- **FR-012**: The system MUST reuse, not duplicate: spec-016 (claims registry, resolvers, `triple` superlative/relational logic, pointer/render, gate) and spec-017 (fill service, channels OEIS/Wikipedia/Wikidata/papers/theorem, conflict, citation-repair, present-in-source gate). The approximate vs exact selection plugs into the existing gate so the right check runs per claim.
- **FR-013**: All correctness MUST be demonstrated with real-call tests (no mocked sources/retrieval/classification); any external reference/value introduced into spec or code MUST be independently verified before use.
- **FR-014**: The system MUST provide a **computational verification mode**: for a self-contained, evaluable claim it MUST evaluate the claim with a **safe deterministic evaluator**. The v1 computational scope is the **broadest**: arithmetic (+ − × ÷ **), numeric comparisons/inequalities, percentages, basic **unit conversions** (length/mass/time/SI prefixes), and simple **symbolic/algebraic identities** and **set/logic relations** — implemented with `sympy` (free/open-source: safe symbolic parsing, `simplify` identity checks, `sympy.physics.units` conversions, `sympy.logic`/`sympy.sets`), with a safe AST/`sympy` path for pure-numeric forms. It and VERIFY iff the asserted result equals the computed result (reusing the approximate-mode tolerance when the result is real-valued); otherwise REFUTE and correct to the computed value.
- **FR-015**: The computational evaluator MUST be a safe, sandboxed parser/evaluator — it MUST NOT use `eval`/`exec` or any unrestricted execution, and the computed result MUST be produced by code, NEVER asserted by a language model. A claim the evaluator cannot safely parse/evaluate MUST fall back to source-based verification or block — never be guessed.
- **FR-016**: A computed value's provenance MUST be the **evaluated expression + its result** (deterministic, reproducible). This satisfies the safety property (FR-011): the computation is the authority, not model memory. Corrections render the computed value via the spec-017 pointer; citation repair attaches the computation as the provenance.
- **FR-017**: The computational mode MUST be selected ONLY for genuinely self-contained claims; a claim that depends on an external fact (even if it also contains arithmetic) MUST source-verify the factual part and MUST NOT be declared verified on the computation alone.

### Key Entities *(include if feature involves data)*

- **Verification Mode**: per-claim selection of `exact-count` (literal/count matching) vs `approximate-constant` (precision-aware rounding) vs `computational` (safe evaluation) vs `source-fact` (search + ground).
- **Computational Claim**: a self-contained, evaluable assertion (arithmetic / comparison / unit conversion / percentage) whose truth is determined by computing it, not by sourcing it; its provenance is the evaluated expression + result.
- **Curated Constant**: a recognized mathematical/physical constant with a high-precision true value and a citable authority (library/CODATA); pre-seeded; the highest-authority source for that constant.
- **Precision Spec**: the stated precision of an approximate claim (significant figures / decimal places) + any hedge, derived from the claim text, governing the rounding tolerance.
- **(Reused) Claim / Claim Registry / Resolver / FillResult / FetchedSource / FillProvenance** from specs 016/017 — extended with the verification mode + constants source; corrections render via the existing pointer + citation-repair.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: "π is 3.14", "π is about 3", and "π is 3.14159" are all VERIFIED (no false correction); "π is 3.15" and "e is 2.5" are refuted and corrected to sourced values, with provenance.
- **SC-002**: The exact-count path does not regress: "9,988 prime knots at 13 crossings" still verifies by exact match (the spec-017 e2e stays green).
- **SC-003**: Recognized constants (π, e, …) resolve from the curated library-backed table with **zero network calls**, and provenance names the authority.
- **SC-004**: A wrong superlative ("largest planet is Saturn") is corrected to the sourced extremum ("Jupiter"); a superlative with no retrievable candidate set stays blocked.
- **SC-005**: A wrong relational claim ("capital of Australia is Sydney") is corrected to the sourced object ("Canberra") in triple form; an unsourceable relation stays blocked.
- **SC-006**: Zero verified/filled values originate from model memory across the test set — every one traces to a library constant or a fetched source with recorded provenance.
- **SC-007**: A claimed value that is one of several sourced-valid objects/roundings is VERIFIED, not over-corrected (no false positives on already-correct approximations or multi-valued relations).
- **SC-008**: Each deferred-then-enabled claim kind (magnitude, relational) is corrected from a real source for a known-wrong instance and blocked for an unsourceable instance.
- **SC-009**: Self-contained computational claims are decided by evaluation: "1 plus 1 is 2" / "30% of 200 is 60" VERIFIED; "1 plus 2 is 1" REFUTED and corrected to 3; "1 is larger than 2" REFUTED; "5 km is 5,200 m" REFUTED and corrected to 5,000 m — all with NO source lookup and NO model-asserted result, and the evaluated expression recorded as provenance.
- **SC-010**: The computed result is never produced by a language model: verified by confirming the evaluator path performs the computation in code, and that an unparseable computational claim falls back/blocks rather than being guessed.

## Assumptions

- Builds on and reuses specs 016 + 017 (registry, resolvers, `triple` logic, fill service, channels, conflict, citation-repair, present-in-source gate). The approximate-numeric mode is a new check that the gate selects per claim; the exact path is untouched.
- The curated constants table is library-backed: mathematical constants from the language's standard math library (double precision, ~15–16 significant figures) and, if in v1 scope, physical constants from a CODATA-backed table (`scipy.constants` is available in the environment). Double precision is assumed sufficient for the sentence-level claims the pipeline produces; claims stating more precision than the table provides fall back to source retrieval (and block the unconfirmable portion). Arbitrary-precision (e.g. an `mpmath` dependency) is a later option, not v1.
- "Hedge" words/symbols ("about", "approximately", "roughly", "~", "≈", "around") widen the rounding tolerance modestly; they do not make an absurd value pass.
- Real-call testing (no mocks) is required, consistent with the repository's testing methodology and constitution; any constant value or external reference entering the code/spec is independently verified first.
- Magnitude/superlative and relational verification reuse the spec-016 `claims/triple.py` resolvers (currently check-only) extended with the spec-017 fill (search → fetch → present-in-source → correct).
- The **computational evaluator** uses `sympy` (a free/open-source dependency added by this spec — Constitution IV compliant) for the broad v1 scope: safe symbolic parsing (never `eval`/`exec`; use restricted parsing, not raw `sympify` on untrusted input), algebraic-identity checks via `simplify`, unit conversions via `sympy.physics.units`, and `sympy.logic`/`sympy.sets` for set/logic relations; pure-numeric arithmetic/comparisons/percentages use a safe `ast`/`sympy` path. A computational result is a deterministic, reproducible authority (like a library constant), so it satisfies the "never from model memory" property — provided the evaluator, not the LLM, produces the result. The new `sympy` dependency MUST be added to the project requirements.

## Dependencies

- **Spec 016** (`specs/016-claim-verification/`) — claims registry, resolvers, `triple` superlative/relational logic, pointer/render, gate.
- **Spec 017** (`specs/017-claim-auto-correction/`) — fill service, channels (OEIS/Wikipedia/Wikidata/papers/theorem), conflict, citation-repair, the present-in-source gate this spec selects a mode for.
- The environment's standard math library and `scipy.constants` (CODATA) for the curated constants table.
- **`sympy`** (free/open-source) — NEW dependency added by this spec for the computational evaluator (symbolic parsing, identity checks, units, logic/sets); must be added to the project requirements.
- Planning/motivation context: tracking **issue #256**, [`notes/spec-015-review-status.md`](../../notes/spec-015-review-status.md).
