# Feature Specification: Deterministic Claim Caching + Planning-Stage Reference-Only Verification

**Feature Branch**: `020-deterministic-claim-caching`
**Created**: 2026-06-04
**Status**: Draft
**Input**: User description: "Re-architect the claim-verification stack (specs 016→019) so (A) the planning stages — specify / clarify / plan / tasks — verify only REFERENCES, never low-level factual claims, and (B) any verified claim is deterministically cached behind a stable placeholder and FROZEN: once verified it never changes. Accuracy stays paramount; this strengthens paper-stage verification while removing the planning-stage thrash that loops on numbers (e.g. a knot count) that don't affect the ability to proceed."

## Context

The trustworthiness stack — spec 016 (claim detection / `[UNRESOLVED-CLAIM:]` marker), 017 (authoritative fill), 018 (per-claim verify modes), 019 (semantic substantiation) — runs uniformly on every artifact at every stage. Two maintainer-observed failures motivate this spec:

1. **Claim waffling.** Within the convergence loop a factual claim is made, flagged, corrected, then in a later round overwritten (cache miss), re-flagged, and re-corrected — without ever stabilizing. The intended behavior is the opposite: a claim, once identified and resolved in the **first** review round, is replaced by a placeholder that is read **deterministically** from a cache; once verified, it **never changes**.
2. **Low-level claims block planning.** The planning documents assert specific empirical values (e.g. "the exact count of prime knots at 13 crossings is 9,988"). These don't affect whether the project can proceed, yet they are fully fetched, grounded, and — when wrong — drive kickbacks that exhaust the convergence cap toward human escalation. Concrete case (PROJ-552): the spec asserted "49 prime knots at crossing 13" (wrong — 49 is the count at crossing 9), contradicting the plan's correct 9,988, and the panel looped on it. Planning documents should state the **research question, method, and references** and defer empirical specifics to the implementation/research phase.

This spec keeps **accuracy paramount**: references are still verified everywhere, and the paper/implementation-stage freeze is *stronger* than today. In the **planning** stages it does not merely skip low-level claims (which would leave a possibly-false value sitting unverified in the document) — it **detects and strips** them, replacing each with a higher-level statement so no unverified/false low-level value propagates, while never blocking on it. Prevention (template/prompt guidance) reduces how often low-level claims appear; the strip/smooth transform is the cure for the ones that still do.

## Clarifications

### Session 2026-06-04

- Q: Which pipeline stages count as "planning" (references-only + strip/smooth) vs. "full verification"? → A: The four speckit stages **specify, clarify, plan, tasks** are planning (references-only + strip/smooth); paper / research / implementation stages do full verification (with the Part-B freeze); the idea/flesh_out stages keep their current behavior.
- Q: How is a detected low-level claim replaced with a higher-level statement (the strip/smooth)? → A: An **LLM rewrite** to a claim-free higher-level statement, with the claim detector **re-run on the output to guarantee no low-level claim remains** (idempotent); a **deterministic fallback** (delete the asserting clause) applies if the rewrite still contains one.
- Q: Where does the frozen verified-claim store live and how does it persist across runs? → A: The already-git-tracked **`state/claims/`** registry (keyed by value-independent **subject_key**) is the single frozen source of truth; verified verdicts persist there, removing dependence on the gitignored grounding-cache for freezing.
- Q: How do reviewers/humans see values if the canonical doc carries placeholders? → A: The canonical stored doc keeps **placeholders**; a values-substituted view is **rendered deterministically from the frozen store at review time and for the final published artifact**; convergence operates on the placeholder form.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Planning stages verify references and strip/smooth low-level claims (Priority: P1)

When the pipeline runs a planning stage (specify, clarify, plan, tasks), the claim layer verifies that **references** (citations: DOI / arXiv / URL) resolve, and for any detected **low-level factual claim** (a specific count, measured quantity, or entity fact) it does **not** fetch, ground, or kick back — instead it **replaces the claim with a higher-level statement** that preserves the document's intent without asserting the specific unverified value. So an unverified or false low-level value (e.g. "exactly 49 prime knots at 13 crossings") is neither left in place, nor blocked on, nor expensively verified: it is **stripped and smoothed** into a qualitative statement (e.g. "the count of prime knots grows with crossing number, per the cited enumeration"). The project advances on correct references and a sound method, not on the correctness of empirical numbers that belong to a later stage.

**Why this priority**: This is the immediate unblocker — it stops the hours of wasted verification and the kickback loops on numbers that don't gate progress (the PROJ-552 stall), while ensuring no false low-level claim survives into the planning docs. It is independently shippable and delivers value on its own.

**Independent Test**: Run a planning-stage document containing (a) a specific (and wrong) low-level numeric claim and (b) a citation. Confirm the numeric claim is removed/generalized into a higher-level statement (no specific value remains), no `[UNRESOLVED-CLAIM:]` marker or kickback is produced, and the citation is still checked for resolvability (a fabricated citation still blocks advancement). Re-run a second round and confirm the generalized passage is left unchanged (no re-rewrite).

**Acceptance Scenarios**:

1. **Given** a plan document asserting a specific empirical count, **When** the planning-stage claim layer runs, **Then** the count is neither fetched nor grounded, no `[UNRESOLVED-CLAIM:]` marker is injected, the stage does not kick back, and the specific value is replaced by a higher-level statement that no longer asserts it.
2. **Given** a planning document whose low-level claim has been stripped/smoothed in round 1, **When** a later round re-processes the document, **Then** the generalized passage contains no detectable low-level claim and is NOT rewritten again (the strip/smooth is stable — no new waffling).
3. **Given** a plan document citing a fabricated DOI, **When** the planning stage runs, **Then** the reference is flagged unresolvable and advancement is blocked (fail-closed on references is unchanged), independently of the low-level-claim handling.
4. **Given** a plan document with a research question, method, and resolvable references and no low-level claims, **When** the planning stage runs, **Then** no strip/smooth and no low-level-claim verification occur and the stage can converge.
5. **Given** a passage that mixes a reference and a number, **When** the planning stage runs, **Then** only the specific low-level assertion is generalized; the citation and surrounding non-claim content are preserved unchanged.

---

### User Story 2 - A verified claim is frozen and never waffles (Priority: P1)

Once a claim has been identified and resolved (in any stage that verifies it), its verified value is stored against a **stable, value-independent identity** and is **frozen**. Subsequent convergence rounds read the frozen value deterministically from the cache; a rephrasing of the same fact maps to the same record and is never re-resolved to a different value. The value is carried in the canonical document as a **durable placeholder**, not baked back into prose where it would be re-extracted as a new claim.

**Why this priority**: This eliminates the waffling at its root for every stage that legitimately verifies claims (references in planning; empirical claims in the paper/research phase). It is the structural fix the maintainer described.

**Independent Test**: Verify a claim in round 1; rephrase the surrounding prose in round 2; confirm the same record is reused (a cache hit by stable identity, no re-resolution) and the value is identical. Re-run the whole pipeline from a clean checkout and confirm the frozen value persists (no cold re-resolution).

**Acceptance Scenarios**:

1. **Given** a claim verified in round 1, **When** a later round re-processes a rephrased version of the same fact, **Then** the system reuses the frozen record by stable identity, performs no re-resolution, and the value is unchanged.
2. **Given** a verified claim, **When** the canonical document is stored between rounds, **Then** it contains a durable placeholder for that claim (not the baked-in literal value), so the value cannot be re-extracted as a new claim.
3. **Given** a verified store committed by one run, **When** a subsequent run starts from a clean checkout, **Then** the frozen value is read from the persisted store without re-resolving against external sources (unless the cited source itself changed).
4. **Given** a transient external failure during a later round, **When** resolution would otherwise re-run, **Then** an already-VERIFIED record is **not** re-opened or overwritten by the transient failure.

---

### User Story 3 - Planning documents don't assert low-level empirical claims in the first place (Priority: P2)

The specify / clarify / plan / tasks agents and templates instruct the producing agent to state the research question, the method, and the references, and to **defer specific empirical values** (counts, dataset sizes, measured quantities) to the implementation/research phase. Low-level numbers therefore rarely appear in planning documents at all — and US1 ensures that even if one slips in, it does not block progress.

**Why this priority**: Complements US1 (prevention vs. tolerance). Lower priority because US1 already removes the blocking behavior; this reduces noise and improves document quality.

**Independent Test**: Generate a fresh spec/plan for a research project and confirm the produced documents express measurable outcomes as *what will be measured and against which reference*, not as pre-asserted specific values.

**Acceptance Scenarios**:

1. **Given** the updated specify/plan guidance, **When** an agent produces a planning document for an empirical research project, **Then** success criteria and technical context describe what to measure and the source/reference, not specific unverified numbers.

---

### Edge Cases

- A sentence mixes a reference and a number ("there are 49 prime knots at 9 crossings (Rolfsen 1976)"): in a planning stage the specific numeric assertion is stripped/generalized while the citation is preserved and still checked. The number is not verified there and must not trigger a kickback.
- The strip/smooth would otherwise produce broken or empty prose (the claim is load-bearing for a sentence): it must yield a grammatical higher-level statement, not a dangling fragment — and must still not re-introduce a specific value.
- A claim's cited source genuinely changes between runs (source hash differs): the frozen record is allowed to re-resolve (freeze is keyed to source identity, not eternal).
- A claim is rephrased such that its value-independent identity legitimately differs (a different subject): it is treated as a new claim, not a cache hit — the freeze must not collapse two distinct subjects.
- A reviewer/human reads a stored document full of placeholders: a rendered view substitutes verified values so the document is readable and reviewer-judgeable; the stored canonical form keeps placeholders.
- A planning document legitimately needs a quantity to express scope (e.g. a dataset identifier): it cites the source/reference rather than asserting a verified count.

## Requirements *(mandatory)*

### Functional Requirements — Part A: planning = references-only

- **FR-001**: The system MUST distinguish *planning* stages (specify, clarify, plan, tasks) from *paper/research/implementation* stages when running the claim layer, via an explicit signal threaded to the claim layer (not a global, stage-blind setting).
- **FR-002**: In a planning stage, the claim layer MUST NOT fetch, fill, ground, or verify low-level claim kinds (numeric, magnitude, relational, causal, entity-fact): no external fetch, no LLM locator call, no grounding call.
- **FR-002a**: In a planning stage, a detected low-level claim MUST be **replaced with a higher-level statement** that preserves the surrounding intent without asserting the specific unverified value — so no unverified/false low-level value remains in the document. The replacement is produced by an **LLM rewrite**; the claim detector MUST be **re-run on the rewritten passage to confirm it contains no low-level claim**, and if any remains a **deterministic fallback** (removing the asserting clause) MUST be applied so the result is always claim-free.
- **FR-002b**: The strip/smooth transform MUST be **idempotent/stable**: because the rewritten passage is guaranteed claim-free (FR-002a), subsequent convergence rounds detect nothing to re-process and MUST NOT rewrite it again (no new waffling). Re-running the transform on already-smoothed text MUST be a no-op.
- **FR-002c**: The strip/smooth MUST alter ONLY the specific low-level assertion; it MUST NOT remove or modify references (citations), the research question, the method, or other non-claim content.
- **FR-003**: In a planning stage, a low-level claim MUST NOT cause a convergence kickback or block advancement (it is stripped/smoothed, not flagged with an `[UNRESOLVED-CLAIM:]` marker).
- **FR-004**: References MUST continue to be verified in planning stages: a citation that does not resolve (DOI / arXiv / URL) MUST block advancement (fail-closed), using the existing reference-validation path.
- **FR-005**: The paper / research / implementation stages MUST be unchanged: they continue to verify **all** claim kinds (with the Part-B freeze applied).
- **FR-006**: The specify / clarify / plan / tasks agent prompts and templates MUST instruct the producing agent to state the research question, method, and references and to defer specific empirical values to implementation — including the shared templates and any per-project template copies.

### Functional Requirements — Part B: deterministic frozen cache

- **FR-007**: A verified claim's value MUST be carried in the canonical stored document as a **durable placeholder**, never baked into prose as a literal between rounds. The artifact-cleaning step MUST NOT delete this placeholder.
- **FR-008**: A human/reviewer-facing **rendered view** MUST substitute verified values for placeholders, rendered **deterministically from the frozen store at review time and for the final published artifact**, so documents remain readable and reviewer-judgeable; the canonical stored form retains placeholders and convergence operates on it.
- **FR-009**: A claim's cache/registry identity MUST be **value-independent** (derived from the claim's subject, excluding the asserted value), so a rephrasing or correction of the same fact maps to the same record.
- **FR-010**: A record in the VERIFIED state MUST be treated as **immutable**: lookup by the value-independent identity returns the frozen value without re-resolution unless the cited source's identity (source hash) genuinely changed.
- **FR-011**: The system MUST NOT re-resolve or overwrite an already-VERIFIED record due to a transient failure or a later-round re-extraction landing in a pending state.
- **FR-012**: The fill/verification cache key MUST NOT depend on the asserted value, so a pending phrasing and a verified phrasing of the same fact hit the same cache entry.
- **FR-013**: The frozen verified-claim store MUST be the already-git-tracked **`state/claims/`** registry, keyed by the value-independent **subject_key**, as the single source of truth. Verified verdicts MUST persist there so a re-run reads frozen values deterministically rather than re-resolving from cold; freezing MUST NOT depend on the gitignored grounding-cache (that cache may remain a within-run optimization, but is not the system of record for verified values).

### Cross-cutting requirements

- **FR-014**: Accuracy MUST remain paramount: no proven-good verification path is weakened. The paper-stage exact-count path, constants, and entity facts MUST still verify in the stages where they belong.
- **FR-015**: The redesign MUST REUSE existing machinery — the citation/reference resolver and reference validator, the claim-kind taxonomy, the value-independent subject identity, and the existing per-kind fill gate — and MUST NOT duplicate them.
- **FR-016**: All behavior MUST be verified with real calls (no mocks) for the externally-dependent paths, per the project testing policy, while the deterministic-caching logic is pinned with offline tests.

### Key Entities

- **Claim**: a detected assertion with a kind (reference vs. low-level), a value-independent subject identity, a status (pending / verified / unresolved), a verified value, and the source identity (hash) it was verified against.
- **Claim kind**: the taxonomy separating **reference/citation** claims (resolvability-checked) from **low-level** claims (numeric, magnitude, relational, causal, entity-fact).
- **Verified store**: the persisted, frozen mapping from value-independent identity → verified value + evidence + source hash; immutable once verified; survives across runs.
- **Placeholder**: the durable token standing in for a verified claim in the canonical document; resolved to a value only in the rendered view.
- **Stage class**: planning (specify/clarify/tasks/plan) vs. paper/research/implementation — selects references-only-plus-strip/smooth vs. full verification.
- **Strip/smooth transform**: the planning-stage operation that replaces a detected low-level claim with a higher-level statement (removing the specific unverified value), preserving references and surrounding content, and idempotent on already-smoothed text.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In a planning stage, a low-level factual claim is verified/grounded **zero** times and triggers **zero** kickbacks; the specific unverified value is removed (replaced by a higher-level statement), so **zero** unverified/false low-level values remain in the planning document; planning wall-clock spent on low-level-claim verification drops to zero.
- **SC-001a**: The strip/smooth transform is **stable**: running it a second time on an already-smoothed planning document changes nothing (a no-op), and the smoothed passage is re-detected as containing **zero** low-level claims.
- **SC-002**: In a planning stage, an unresolvable reference still blocks advancement 100% of the time (no regression in reference fail-closed behavior).
- **SC-003**: A claim verified once and then rephrased across convergence rounds yields the **same** value with **zero** re-resolutions of that fact (a deterministic cache hit), across at least three rounds.
- **SC-004**: Re-running the pipeline from a clean checkout reads the frozen value from the persisted store with **zero** cold re-resolutions of already-verified facts.
- **SC-005**: In a paper/implementation stage, the proven-good claims (the exact knot count, a constant, an entity fact) still verify correctly — no regression versus specs 016–019.
- **SC-006**: The PROJ-552 "49 vs 9,988" planning kickback loop no longer occurs: the wrong "49 prime knots at crossing 13" is stripped/generalized out of the planning documents (not left, not blocked on), references verify, and the stage advances without exhausting the kickback cap on that class of issue.
- **SC-007**: A stored canonical document round-trips through the convergence loop without any verified value being baked into prose (it is always a placeholder), so no verified claim is ever re-extracted as a new claim.

## Assumptions

- "Planning" stages are specify, clarify, plan, and tasks; "paper/research/implementation" stages verify all claim kinds. (The clarify/specify/plan/tasks set is the planning class.)
- The existing reference validator (citation resolvability → the citations store, gating advancement) is the correct and sufficient "references-only" verification for planning stages; the expensive fill/grounding path is not needed there.
- The value-independent subject identity already used for claim reuse is a sufficient stable key; genuinely distinct subjects do not collide under it.
- "Frozen unless the source changed" uses the source hash already persisted by the claim layer (spec 016 FR-015) as the invalidation signal.
- Reviewers and humans consume a rendered view (values substituted); machine/convergence processing operates on the canonical placeholder form.
- The strip/smooth transform is an **LLM rewrite with a re-detect guard and a deterministic fallback** (clarified 2026-06-04): the rewrite produces a grammatical higher-level statement, detection is re-run to confirm it is claim-free, and a deterministic clause-removal is applied if not — so idempotency holds because the stored result always contains no detectable low-level claim.
- Accuracy is paramount: this spec narrows *where* low-level claims are verified (not in planning) and makes verified claims deterministic/immutable; it does not relax verification in the stages that produce research results.
