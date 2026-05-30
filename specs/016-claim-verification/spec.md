# Feature Specification: Claim-Verification Layer (Claim Registry)

**Feature Branch**: `016-claim-verification`
**Created**: 2026-05-30
**Status**: Draft
**Input**: User description: "A claim-registry layer so every factual claim a pipeline agent produces is extracted, registered, resolved against an authoritative source (external) or a harness-signed execution receipt (internal results), and rendered as a verified value via a pointer — so the model never retypes a fact and nothing unverified can advance. Human escalation must be rare (publication only)."

## Context & Motivation

llmXive is an **automated** scientific-discovery pipeline; its core promise is **trustworthy** science, not "AI slop" with no factual basis. Spec 015's Part-7 end-to-end shakeout surfaced a show-stopping gap: doc-producing agents **fabricate factual claims**. Concretely (real run, 2026-05-30, recorded in [`notes/spec-015-review-status.md`](../../notes/spec-015-review-status.md), "In-situ run #1" + "F-20"): asked to fix a fabricated knot-count citation, the spec reviser invented "**27,635** prime knots at 13 crossings" (the correct count is **9,988**, OEIS A002863) attributed to a non-resolvable author-year reference.

Spec 015 ([`specs/015-pipeline-convergence-protocol/`](../015-pipeline-convergence-protocol/)) added **detective** controls — F-18 (citation existence guard), F-19 (full-text claim grounding), F-14 (adaptive kickback) — which *catch and block* unverifiable claims. But the agent keeps inventing, so documents never converge, and F-14's cap→human-escalation terminal is unacceptable for an automated pipeline. This spec adds the **constructive** complement: claims are resolved to verified values and substituted by pointer, so fabrication cannot occur or persist. Prior-art research and the full design are in tracking **issue #256** and [`docs/superpowers/specs/2026-05-30-claim-verification-layer-design.md`](../../docs/superpowers/specs/2026-05-30-claim-verification-layer-design.md). F-18/F-19/F-14 are reused as the resolution + gating substrate.

## Clarifications

### Session 2026-05-30

- Q: How should non-numeric (relational/causal/magnitude) claims be resolved — structured knowledge base vs. web-search + grounding? → A: Web-search + grounding only (reuse the librarian / F-19): decompose to a subject–relation–object (or candidate-set) form, retrieve a citable source, verify by entailment; unsourceable → block. A structured-KB resolver may be added in a later version, but is out of scope for v1.
- Q: Where does claim extraction/resolution run — only the shared document-write chokepoint, or also inside the reviser loop each round? → A: Both — at the single shared document-write chokepoint (uniform coverage of all doc-producing agents) AND inside the reviser revision loop each round (earliest interception, before the panel re-reviews). The verified-value cache keeps the repeated per-round passes cheap.
- Q: Should the new claim layer replace F-18's `[UNVERIFIED]` marker or coexist with it? → A: Replace — a single unified claim-marker + gate supersedes F-18's `[UNVERIFIED]`; F-18/F-19 become resolvers within the layer. Backward compatibility is NOT required (early-stage, sole developer); a one-time migration pass updates existing projects' artifacts/markers. Prefer clean unified designs over compatibility shims.

## User Scenarios & Testing *(mandatory)*

> "Users" here = the automated pipeline and the eventual human consumers of llmXive's published science. The value is **trustworthiness**: no advanced document may contain a fact that isn't traceable to an authoritative source or a real execution.

### User Story 1 - No fabricated external claim can advance (Priority: P1)

Every factual claim an agent writes into a document (numbers, citations, relational/magnitude/causal facts) is extracted and verified against an authoritative external source; the verified value is what appears in the document. A claim that cannot be verified is never silently published and never requires routine human input — it blocks the document and is automatically routed back for re-resolution.

**Why this priority**: This is the MVP and the direct fix for the fabrication that is currently blocking the pipeline. Without it, all downstream output is untrustworthy.

**Independent Test**: Run the spec stage on the project that previously fabricated "27,635 prime knots"; confirm the produced spec either renders the verified value (9,988, from a resolvable source) or blocks the claim and auto-routes it for resolution — with **no** fabricated number and **no** human-input request.

**Acceptance Scenarios**:

1. **Given** an agent output containing a numeric claim attributed to a real, resolvable source whose content supports it, **When** the claim layer runs, **Then** the claim is registered, resolved, and the document renders the verified value via a pointer.
2. **Given** an agent output containing a fabricated number or a claim cited to a non-resolvable source, **When** the claim layer runs, **Then** the claim is marked unresolved, the document is blocked from advancing, and the specific claim is auto-routed to the fact-finder/librarian for re-resolution (no human escalation).
3. **Given** a previously verified claim, **When** the same claim appears again in any later round or document, **Then** the cached verified value is reused without re-resolution and without the model retyping the value.

### User Story 2 - Reported results trace to real runs, never hallucinated (Priority: P1)

Every empirical result llmXive reports (in implementation summaries, results sections, the paper) must trace to an actual code execution on actual data. A reported number that has no backing execution artifact cannot appear in an advanced document.

**Why this priority**: Fabricated *results* are as corrosive to trustworthiness as fabricated citations — and a documented LLM failure mode (reporting "expected" results instead of computed ones). Equal-priority for v1 per maintainer decision.

**Independent Test**: Have the implementation/analysis stage produce a result and a backing receipt; confirm the write-up can cite that result by pointer and renders the receipt's value. Then attempt to introduce a results-section number with no backing receipt; confirm it is blocked.

**Acceptance Scenarios**:

1. **Given** an analysis step that computes a value, **When** the execution harness records it, **Then** a tamper-evident receipt is created binding the value to the code, data, parameters, and environment that produced it — created by the harness, not by any language model.
2. **Given** a write-up that references a result by pointer, **When** the document renders, **Then** the value comes from the receipt store (the model does not retype it).
3. **Given** a results-section numeral with no matching execution receipt, **When** the claim layer runs, **Then** the document is blocked and routed back to the implementation stage.

### User Story 3 - Non-numeric claims are verified, not just numbers (Priority: P2)

Claims of magnitude/direction/superlative ("largest", "more than", "earliest"), set/relational facts ("X is the capital of Y", "X wrote Y"), causal claims ("X causes Y"), and entity/definitional facts are each verified by an appropriate strategy — not assumed true and not checked only as text overlap.

**Why this priority**: These are at least as common as numeric claims; trustworthiness requires covering them, but the numeric/citation path (US1) is the acute blocker.

**Independent Test**: Provide outputs containing a true and a false relational claim and a true and a false superlative claim; confirm each is classified by type and the false ones are flagged/blocked.

**Acceptance Scenarios**:

1. **Given** a superlative/comparative claim, **When** resolved, **Then** the layer evaluates it against the full relevant candidate set (not single-statement entailment) and verifies the ordering.
2. **Given** a relational claim, **When** resolved, **Then** it is checked as a subject–relation–object assertion against an authoritative source, and an unsupported relation is flagged.

### User Story 4 - Verified facts are reused "for free" and never drift (Priority: P3)

Once a claim is verified, it is a pointer to a registry entry. Documents render from the registry, so the same fact is identical everywhere it appears, reused across rounds and documents without re-verification, and impossible for an agent to alter by retyping.

**Why this priority**: Efficiency + consistency; valuable but depends on US1/US2 existing first.

**Independent Test**: Verify a claim once; confirm a later document referencing the same claim renders the identical cached value with no new resolution call and no opportunity for the model to change it.

**Acceptance Scenarios**:

1. **Given** a verified claim referenced in two documents, **When** both render, **Then** they show the identical value sourced from the registry.

### Edge Cases

- A source resolves (exists) but its content does not support the claim → claim is REFUTED/unsupported and blocked (distinct from "no evidence found").
- Evidence retrieval fails (network/source unavailable) → claim is "not enough info" (kept distinct from "refuted") and routed for retry; never silently treated as verified.
- A document mixes verifiable claims with legitimate design parameters / uncited values → only externally-attributed, check-worthy claims are extracted; design choices and thresholds are left untouched (no over-flagging).
- An agent attempts to fabricate a result receipt → impossible: receipts are created and signed only by the execution harness with a key never exposed to any model.
- A stochastic result whose value differs across runs → the recorded run's captured output is what is verified (by hash), not a fresh re-execution.
- A claim cannot be resolved after the automated retry budget is exhausted → the document remains blocked and the project waits in an automated-resolution state; human escalation occurs only in genuinely-exhausted, rare cases (and at publication sign-off), never as routine flow.
- A previously verified claim's underlying source/result changes (code or data hash changes) → the cached resolution is invalidated and must be re-resolved.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST maintain a comprehensive, maintained registry of which pipeline agents/stages produce factual claims (every document-producing agent: spec, clarify, plan, tasks, implement, and their paper-stage equivalents, plus flesh-out and any results/summary producers).
- **FR-002**: For every claim-producing agent's output, the system MUST extract **every** check-worthy, verifiable factual claim, while NOT extracting subjective statements, design choices, thresholds, or other non-claims (precision over recall is favored to avoid over-flagging). Extraction MUST run at BOTH the single shared document-write chokepoint (uniform coverage of all doc-producing agents) and inside the reviser revision loop each round (earliest interception).
- **FR-003**: The system MUST register each extracted claim in a per-project, machine-parsable claim set, with a stable identifier, the claim's type, its verbatim text, an anchoring context, its source type, status, resolved value, and the provenance of its resolution.
- **FR-004**: The system MUST classify each claim into a defined taxonomy: numeric/statistic; magnitude/direction/superlative; set/relational; causal; entity/definitional; citation/existence; internal empirical result.
- **FR-005**: The system MUST replace each in-text claim with a pointer to its registry entry, and MUST render documents by substituting verified values for pointers, such that a language model never retypes a verified fact.
- **FR-006**: The system MUST resolve external claims against authoritative sources using per-type strategies: numeric/citation via existence + content verification (reusing F-18/F-19); superlative/comparative via retrieval of the full candidate set and ordering check; relational via subject–relation–object lookup; causal via a citable supporting source (never model inference); entity/definitional via authoritative reference.
- **FR-007**: For internal empirical results, the system MUST require a tamper-evident execution receipt that binds the reported value to the code, input data, parameters, random seed, and environment that produced it, with the captured real output.
- **FR-008**: Execution receipts MUST be created and signed by the execution harness only; no language model may create, sign, or alter a receipt, and the signing key MUST never be exposed to any model.
- **FR-009**: A reported result value MUST resolve only if a backing receipt exists whose recorded output matches (by hash) a cached or re-verified execution; results with no backing receipt MUST be blocked.
- **FR-010**: Internal results MUST be usable as first-class sources for downstream claims (a later claim may cite a result by pointer exactly as it would cite an external reference).
- **FR-011**: A claim resolution MUST yield one of: verified, refuted, or not-enough-info — and the system MUST keep "not-enough-info" (retrieval failure) distinct from "refuted" (source contradicts), and MUST never treat absence of evidence as verification.
- **FR-012**: Any document containing an unresolved (refuted / not-enough-info / unbacked) claim MUST be blocked from advancing (reusing the spec-015 hard-block gate).
- **FR-013**: On a blocked document, the system MUST automatically route the specific unresolved claims back to the appropriate resolver (librarian/fact-finder for external; implementation stage for results) for another automated resolution attempt, governed by a bounded retry budget.
- **FR-014**: The system MUST NOT escalate to a human as part of routine operation; human input is reserved for publication sign-off and genuinely-unresolvable cases after the automated retry budget is exhausted. The spec-015 F-14 kickback cap's human-escalation terminal MUST be repointed to this automated-resolution loop.
- **FR-015**: Verified claims MUST be cached and reused across rounds, stages, and documents without re-resolution, and a cached resolution MUST be invalidated when its underlying source or execution artifact changes.
- **FR-016**: The system MUST reuse existing infrastructure where applicable: the citation store, the librarian (search + verification + full-text retrieval), the F-18 reference resolver, the F-19 grounding service, and the existing document templating/substitution mechanism.
- **FR-017**: The convergence review panel MUST include a blocking check that every reported claim in a reviewed document is resolved (verified or receipt-backed).
- **FR-018**: All verification MUST be performed against real sources and real executions (no mocked or fabricated verification); correctness MUST be demonstrated with real-call tests.
- **FR-019**: The layer MUST use a single unified claim-marker + hard-block gate that REPLACES the F-18 `[UNVERIFIED]` marker (F-18/F-19 become resolvers within the layer). Backward compatibility with the prior marker is NOT required; the system MUST provide a one-time migration that updates existing projects' artifacts and registries to the unified scheme.

### Key Entities *(include if feature involves data)*

- **Claim**: a single check-worthy factual assertion extracted from an agent's output; has a stable id, a type (taxonomy), verbatim text, a canonical/normalized form (a subject–relation–object triple for relational claims), an anchoring context, a source type (external | result | pending), a status (pending | verified | refuted | not-enough-info | unresolvable), a resolved value, and resolution provenance (which source/receipt, evidence/quote, score).
- **Claim Registry**: the per-project, machine-parsable set of all Claims for a project; the single source of truth from which documents render.
- **Claim Pointer**: the in-document reference that stands in for a claim and renders to its verified value.
- **Execution Receipt**: a tamper-evident record, created by the execution harness, binding a reported result value to its producing code, data, parameters, seed, environment, and captured output; signed with a key not exposed to any model.
- **Result Store**: the per-project set of Execution Receipts; results referenced by downstream claims as first-class sources.
- **Resolver**: a per-claim-type strategy that turns a Claim into a verified/refuted/not-enough-info verdict against an authoritative external source or a result receipt.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Zero fabricated or unverifiable factual claims appear in any document that advances past its producing stage (every advanced claim is verified against a source or receipt).
- **SC-002**: On the project that previously fabricated "27,635 prime knots," the spec stage produces only the verified count (9,988) sourced from a resolvable reference, or blocks the claim — with no human-input request in either case.
- **SC-003**: 100% of empirical-result numbers in advanced implementation/results/paper documents trace to a backing execution receipt whose captured output matches the reported value.
- **SC-004**: No language model can introduce or alter a result value that lacks a harness-created receipt (verified by attempting it in tests and confirming it is blocked).
- **SC-005**: Routine pipeline operation requires zero human interventions for claim resolution across an end-to-end project run (human input occurs only at publication sign-off or genuinely-exhausted resolution).
- **SC-006**: A verified claim referenced in multiple documents renders an identical value in every location, with no re-resolution call after the first.
- **SC-007**: The claim extractor does not flag legitimate design parameters, thresholds, or uncited values (measured false-positive rate at or near zero on a representative document set).
- **SC-008**: Each non-numeric claim type (magnitude/relational/causal/entity) is verified by its type-appropriate strategy, demonstrated by correctly flagging a known-false instance of each.

## Assumptions

- This layer builds on, and reuses, the spec-015 detective controls (F-18 citation guard, F-19 full-text grounding, F-14 kickback) rather than replacing them; F-14's human-escalation terminal is repointed to the automated-resolution loop.
- "Authoritative source" for external claims means literature/web sources reachable by the existing librarian/fact-finder; relational/causal/magnitude claims are resolved via web-search + grounding (decompose → retrieve a citable source → entailment), not a structured knowledge base in v1 (a KB resolver may be added later). Unsourceable claims block.
- Both source classes (external claim verification and internal-results provenance) are in scope for v1 (maintainer decision).
- The execution harness can capture real stdout/return values and compute content hashes for produced artifacts; reproducibility relies on pinned seeds and environment for deterministic results, and on recording the actual run's output for stochastic results.
- Real-call testing (no mocks of external services or executions) is required, consistent with the repository's testing methodology; any external reference introduced into the spec/code must be independently verified before use.
- The unified claim-marker + gate supersedes (replaces) the F-18 `[UNVERIFIED]` marker; backward compatibility is not a requirement (early-stage, sole developer). Existing projects are updated by a one-time migration pass. Clean unified designs are preferred over compatibility shims.

## Dependencies

- Spec 015 (`specs/015-pipeline-convergence-protocol/`) and its F-18/F-19/F-14 implementations (PR #250).
- The librarian/fact-finder, citation store, and document-production chokepoint shared by all doc-producing agents.
- Planning/motivation context: [`notes/spec-015-review-status.md`](../../notes/spec-015-review-status.md), the design doc [`docs/superpowers/specs/2026-05-30-claim-verification-layer-design.md`](../../docs/superpowers/specs/2026-05-30-claim-verification-layer-design.md), and tracking **issue #256**.

