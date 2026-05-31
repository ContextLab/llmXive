# Claim-Verification Layer (Claim Registry) — Design

_Date: 2026-05-30 · Tracking issue: **#256** · Proposed as **spec 016** · Builds on spec 015 (PR #250: F-18 citation guard, F-19 full-text grounding, F-14 adaptive kickback)._

## 1. Problem

llmXive's Part-7 shakeout proved a **show-stopping trustworthiness gap**: doc-producing agents (specifier, reviser, …) **fabricate factual claims** — inventing numbers and citing non-resolvable sources. Concretely (real run 2026-05-30): asked to fix a fabricated knot-count citation, the spec reviser produced "**27,635** prime knots (Hoste, Thistlethwaite & Weeks 1998)" — a *new* wrong number (correct 13-crossing count is 9,988, OEIS A002863) on an author-year citation with no resolvable DOI/URL.

F-18 (citation existence) and F-19 (full-text claim grounding) are **detective** controls — they *catch* and block unverifiable claims, but the agent keeps inventing, so the doc never converges. F-14's cap→**human** escalation is the wrong terminal for an *automated* discovery pipeline (human input must be rare — publication only).

This layer is the **constructive** complement: every factual claim is extracted, registered, resolved against an authoritative source (external) or a real execution artifact (internal results), and the document renders the **verified value via a pointer** — so the model never retypes a fact, and nothing unverified can advance. The goal is trustworthy science, not AI slop.

## 2. Goals / non-goals

**Goals:** (G1) extract *every* check-worthy factual claim from each doc-producing agent's output; (G2) register claims in a parsable per-project set; (G3) substitute each in-text claim with a pointer; (G4) resolve+verify each claim against an authoritative source OR a signed execution receipt; (G5) render docs from the verified/cached values; (G6) block advancement on unresolved/refuted claims with **automated** re-resolution routing (no routine human escalation); (G7) cover non-numeric claims (magnitude/direction/relational/causal/entity); (G8) guarantee reported *results* trace to real code/data runs, never hallucinated.

**Non-goals:** replacing F-18/F-19 (reused as resolvers); a general-purpose KB; verifying subjective/design statements (filter them out — over-decomposition is the field's #1 failure).

## 3. Architecture — extract → register → substitute → resolve → render

```
agent.write_artifacts(doc)
  └─ shared chokepoint (slash_command._validate_artifact_citations) + reviser loop (_self_consistency):
     1. EXTRACT   claim_extractor(doc)  → list[Claim]   (LLM; only verifiable+check-worthy)
     2. REGISTER  claim_registry.upsert(claim)          → state/claims/<PROJ>.yaml
     3. SUBSTITUTE doc' = replace each claim span with  {{claim:<id>}}   (reuse prompts.py {{token}})
     4. RESOLVE   resolver.resolve(claim)               → verified value | refuted | unresolvable
                    external → librarian / F-19 grounding / web / triple+set retrieval
                    internal-result → result-receipt store (harness-signed)
     5. RENDER    doc'' = substitute {{claim:id}} → resolved_value   (model NEVER retypes the fact)
  └─ GATE: any unresolved/refuted claim → block (reuse F-18c marker/gate) + auto-route the
            specific claim(s) to the librarian (external) or implementer (results). No human.
```

The pointer indirection is the crux (matches the field's RARR / cite-by-pointer pattern): once resolved, the value lives in the registry; the rendered doc references it. Re-runs reuse cached resolutions "for free"; the agent cannot re-fabricate a value it never types.

## 4. Data model

**Claim** (`state/claims/<PROJ-ID>.yaml`, a list):
```yaml
- claim_id: c_<sha8>           # stable hash of normalized (kind, canonical_text, context)
  kind: numeric | magnitude | relational | causal | entity_fact | citation | result
  raw_text: "27,635 prime knots with crossing number 13"
  canonical: "count(prime_knots, crossing_number=13)"   # normalized assertion (for relational: SPO triple)
  context: "SC-001 validation benchmark"                 # surrounding anchor for re-location
  artifact_path: projects/PROJ-552/specs/001-*/spec.md
  source_type: external | result | pending
  status: pending | verified | refuted | unresolvable
  resolved_value: "9988"                                  # the value rendered into the doc
  evidence: { source_id, url_or_receipt, quote, score }  # provenance of the resolution
  resolver: librarian | grounding | web_triple | result_receipt
  updated_at: <iso>
```

**Result receipt** (`state/results/<PROJ-ID>/<result_id>.yaml`) — minted by the **execution harness, NOT the LLM**:
```yaml
result_id: r_<sha8>
value: 0.42                      # or table/figure pointer
kind: scalar | table | figure
producer: { script_path, code_sha, entrypoint, seed }
inputs:   { dataset_id, data_sha256, params }
env_sha:  <lockfile hash>
captured: { stdout_path, return_repr }
output_sha256: <hash of the produced value/artifact>
created_at: <iso>
hmac: <signature over the above, run-key never in LLM context>
```
A result claim resolves only if a receipt exists whose `output_sha256` matches a cached/re-verified run. Results are **first-class sources**: downstream claims may cite `result:<id>` exactly like a DOI.

## 5. Claim taxonomy + per-kind resolution

| kind | example | resolver strategy |
|-|-|-|
| numeric/statistic | "9,988 prime knots at 13 crossings" | librarian/web → fetch source → require the value present (F-19 number gate) |
| magnitude/direction/superlative | "the largest class", "earliest", "more than" | retrieve the **full candidate set**, compute the ordering, verify (plain entailment can't) |
| set/relational | "X is the capital of Y", "X wrote Y" | decompose to (subject, relation, object) triple → KB/web lookup → match |
| causal | "X causes Y", "X says Y" | require a citable study/source asserting it; never infer; flag if only model-asserted |
| entity/definitional fact | "a braid index is …" | authoritative reference (textbook/encyclopedia/cited source) |
| citation/existence | "(arXiv:…)", "Smith 2020" | F-18 resolve_reference (already built) |
| internal result | "accuracy was 0.42" | **result receipt** (harness-signed); unbacked → hard block |

## 6. Resolvers

- **External — reuse + extend:** F-18 `resolve_reference` (existence), F-19 `grounding` service (full-text entailment + number gate), librarian search/verify. NEW: a **triple/set resolver** for relational + magnitude/superlative claims (web/KB search → candidate set → ordering/relation check). Verdict vocabulary: `verified | refuted | not_enough_info` (keep NEI distinct from refuted; never let "no evidence" become "supported").
- **Internal — result receipts:** the execution harness (implementer/analysis stage) captures real stdout/return values and writes signed receipts. The write-up stage cites results by pointer and may NOT emit a results-section numeral without a backing receipt.

## 7. Blocking & automated routing (revises F-14)

Unresolved/refuted/unbacked claims → block advancement (reuse the F-18c hard-block gate; a claim marker subsumes `[UNVERIFIED]`). Instead of F-14's cap→human, the gate **auto-routes the specific unresolved claims** back to the librarian (external) or implementer (results) for another resolution pass. A bounded retry budget governs *automated* re-resolution; human escalation only at publication sign-off (FR-054) or genuinely-unresolvable-after-exhaustive-automated-search (rare). **F-14's `CONVERGENCE_KICKBACK_CAP` → human terminal must be repointed to this automated loop.**

## 8. Reuse of existing infrastructure

`agents/citation_guard.py` (marker + idempotent pure rewriter — clone for claim pointers); `grounding/` (F-19 extract/ground/entailment/cache); `librarian/{search,verify,pdf_sample}`; `state/citations.py` (store pattern → `state/claims.py`); `agents/prompts.py` `{{token}}` substitution (claim pointers); shared write chokepoint `slash_command._validate_artifact_citations`; reviser `_self_consistency` loop. The convergence panel gains a unanimous-blocking check "all reported claims are resolved/receipt-backed."

## 9. Risks & mitigations (from prior-art research, issue #256)

- **Decomposition recall** (hardest): filter to *verifiable + check-worthy*; track coverage as a metric; a "completeness critic" pass for missed claims.
- **NLI/entailment over-confidence on false claims:** use scores+calibrated thresholds, not hard labels; prefer the deterministic checks (number-present, citation-resolves) where possible.
- **Receipt forgeability:** the LLM must NEVER mint/sign receipts — only the run harness, with a key out of model context.
- **Non-determinism:** pin seeds + lockfile; for stochastic results verify the *recorded* run's hash, don't blindly re-execute.
- **Round-trip drift:** render numbers from the store; never let the model retype a pointer's value.
- **Cost:** cache resolutions by claim_id and receipts by (code_sha,data_sha,seed,env_sha); re-verify hashes rather than re-running.
- **Unverified prior-art citations:** the research surfaced some arXiv IDs (`2603.*`) with future-style identifiers — illustrative only; any reference entering code/spec MUST be WebFetch-verified first (repo rule).

## 10. Testing (real calls, no mocks)

- Offline pure-logic: claim registry CRUD, pointer substitution/render round-trip, taxonomy classification, receipt schema/HMAC verification (real tmp files), the ordering check for superlatives given a candidate set.
- Real-call (`LLMXIVE_REAL_TESTS`): extract claims from a real spec; resolve a real numeric claim (9,988 vs the fabricated 27,635 → refuted/unresolvable); a relational claim (e.g. a capital-of); a result claim with vs without a valid receipt; end-to-end on PROJ-552's spec → the fabricated knot count is replaced by the verified value or blocked.
- Regression: offline gate stays green; env-gate the layer where it needs a backend.

## 11. v1 build order (user: both source classes in v1)

1. Claim registry store + schema (`state/claims.py`) + result-receipt store + HMAC.
2. Claim extractor (LLM; verifiable-only) + pointer substitution (reuse `{{token}}`) + render.
3. External resolver: wire F-18/F-19 + the new triple/set resolver for relational/magnitude.
4. Internal resolver: harness-signed result receipts + cite-by-pointer + block-unbacked; repoint the implementer/analysis stage to emit receipts.
5. Gate + automated routing (repoint F-14's cap terminal); convergence-panel "all claims resolved" check.
6. Integration at the shared write chokepoint + reviser loop; real-call e2e on PROJ-552.

## 12. Open questions (resolve during plan/build)

- Extractor granularity + the exact check-worthy filter (precision/recall tuning on real specs).
- Triple/set resolver backend for relational claims (Wikidata/KB vs web+LLM) — verify-before-adopt.
- Whether the claim marker fully *replaces* F-18 `[UNVERIFIED]` or coexists.
- Migration of the F-14 cap terminal (automated loop vs a higher cap before any human touch).
- How `result:<id>` pointers render in LaTeX (paper stage) vs markdown (spec/plan).

## 13. Status

Design only — no code. After user review this becomes **speckit spec 016** (or a writing-plans implementation plan). Spec 015 (pipeline mechanics) is paused per the scope decision; its F-18/F-19/F-14 work is the foundation this builds on. Tracking: issue **#256**.
