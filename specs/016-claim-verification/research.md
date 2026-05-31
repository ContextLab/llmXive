# Phase 0 Research: Claim-Verification Layer

All NEEDS CLARIFICATION items were resolved during `/speckit-clarify` (Session 2026-05-30) and the design doc ([`docs/superpowers/specs/2026-05-30-claim-verification-layer-design.md`](../../docs/superpowers/specs/2026-05-30-claim-verification-layer-design.md)) + prior-art synthesis in **issue #256**. This file records the decisions that shape the build.

## D1 — Claim extraction strategy (recall vs. precision)

- **Decision**: LLM-based extraction of *check-worthy, verifiable, externally-attributable* claims only; favor **precision over recall**. Filter out subjective statements, design choices, thresholds, and uncited parameters.
- **Rationale**: Over-decomposition (flagging design choices as claims) is the field's #1 failure mode (VeriScore/SAFE/FActScore). False positives erode trust and stall convergence (SC-007). The acute blocker (US1) is fabricated numbers/citations, which are high-precision to detect.
- **Alternatives rejected**: Exhaustive atomic-fact decomposition (RARR/FActScore style) — too many false positives on spec/plan docs full of legitimate design parameters.

## D2 — Non-numeric (relational/causal/superlative) resolution backend

- **Decision**: Web-search + grounding only (reuse librarian + F-19). Decompose to a subject–relation–object triple (relational) or a candidate-set + ordering check (superlative/comparative); retrieve a citable source; verify by entailment. Unsourceable → block. No structured KB in v1.
- **Rationale**: Clarify Q1. A KB (Wikidata) adds a dependency + coverage gaps; the librarian/F-19 substrate already retrieves + grounds. Superlatives genuinely need the *full candidate set* (plain single-statement entailment can't verify "largest").
- **Alternatives rejected**: Wikidata/structured-KB resolver (deferred to a later version); pure single-statement NLI for superlatives (cannot establish ordering).

## D3 — Extraction placement

- **Decision**: BOTH the shared document-write chokepoint (`speckit/slash_command.py::_validate_artifact_citations`, uniform coverage of all doc-producing agents) AND inside the reviser loop each round (`convergence/revisers/_self_consistency.py`, earliest interception before the panel re-reviews).
- **Rationale**: Clarify Q2. Chokepoint guarantees no agent is missed; reviser-loop interception stops fabrication from reaching the panel. The verified-value cache (FR-015) keeps repeated per-round passes cheap.

## D4 — Marker unification (replace vs. coexist)

- **Decision**: A single unified claim-marker + hard-block gate REPLACES F-18's `[UNVERIFIED:` prefix; F-18/F-19 become resolvers within the layer. One-time migration of existing projects' artifacts/registries. No back-compat shim.
- **Rationale**: Clarify Q3 + memory `clean-over-backcompat` — early-stage, sole developer; clean unified designs beat compatibility debt. Two markers + two gates would violate Constitution I (SSoT).
- **Migration**: `claims/migrate.py` rewrites any residual `[UNVERIFIED: …]` markers in tracked artifacts to the unified marker and seeds registry entries as `status: not-enough-info` for re-resolution.

## D5 — Internal-result provenance (anti-hallucination of our own results)

- **Decision**: Harness-signed execution receipts. The execution harness (implementation/analysis stage) captures real stdout/return values and writes an HMAC-signed receipt binding the value to `(script, code_sha, entrypoint, seed, dataset_id, data_sha256, params, env_sha, output_sha256)`. A result claim resolves only if a backing receipt's `output_sha256` matches a cached/re-verified run. The LLM **never** mints/signs/alters a receipt; the signing key is loaded outside any model context.
- **Rationale**: FR-007/008/009; design §4/§9. Fabricated results are as corrosive as fabricated citations and are a documented LLM failure (reporting "expected" numbers). HMAC over a non-model key makes forgery impossible (SC-004).
- **Key handling**: signing key resolved via a process-local secret (env/credentials file, same discipline as the Dartmouth key) and passed only to `results/harness.py`; never interpolated into any prompt or agent context. Verification uses `hmac.compare_digest`.
- **Stochastic results**: verify the *recorded* run's `output_sha256` (FR/edge case), never blind re-execution.

## D6 — Verdict vocabulary

- **Decision**: `verified | refuted | not-enough-info` (NEI). NEI (retrieval failed / no evidence) is kept **distinct** from refuted (source contradicts). Absence of evidence is never verification.
- **Rationale**: FR-011; design §6. Collapsing NEI into "verified" would let unreachable sources pass; collapsing into "refuted" would over-block transient network failures (those should retry).

## D7 — Blocking & automated routing (repoint F-14)

- **Decision**: Unresolved/refuted/unbacked claim → hard-block (reuse the spec-015 gate via the unified marker) + auto-route the specific claim back to the librarian (external) or implementation stage (results), governed by a bounded retry budget. F-14's `CONVERGENCE_KICKBACK_CAP` human terminal is repointed to this automated loop; human input only at publication sign-off or genuinely-exhausted resolution.
- **Rationale**: FR-013/014; the design's core correction to F-14. An automated pipeline cannot require routine human input.

## D8 — Reuse map (from the Explore pass; exact symbols)

| Need | Reuse | Symbol(s) |
|-|-|-|
| claim store | `state/citations.py` pattern | `load(project_id,*,repo_root)`, `save(...)` → `state/claims/<PROJ>.yaml` |
| citation existence | `librarian/verify.py` | `resolve_reference(kind,value,*,timeout)->ResolutionOutcome{resolved\|present_ambiguous\|unreachable}` |
| full-text grounding | `grounding/service.py` | `ground_cited_claim(...)`, `decide(...)`, `number_substantiated(number,doc_text)` |
| entailment | `grounding/entailment.py` | `Verdict{grounded\|contradicted\|not_found}`, `locate_passages(...)`, `assess(...)` |
| retrieval cascade | `grounding/full_text.py` | `retrieve(kind,value,*,timeout)->RetrievedDoc` |
| resolution cache | `grounding/cache.py` | `get/put_fulltext`, `get/put_verdict` (TTLed) |
| marker + pure rewrite | `agents/citation_guard.py` | `UNVERIFIED_MARKER_PREFIX`, `apply_citation_verdicts`, `find_unverified_markers` (clone → claim pointer) |
| write chokepoint | `speckit/slash_command.py` | `_validate_artifact_citations(ctx, outputs)` (line 207) |
| reviser loop | `convergence/revisers/_self_consistency.py` | `run_with_self_consistency(...)` (line 256) |
| panel gate | `convergence/engine.py` | `converged = not open_concerns` (261); `_unverified_marker_concerns()` (67) → add claims check |
| kickback routing | `pipeline/_kickback.py` + `graph.py` | `consume_convergence_kickback`, `CONVERGENCE_KICKBACK_CAP`; `_decide_next_stage` (524/567) |
| templating | `agents/prompts.py` | `substitute(text, values)` `{{token}}` |

## D9 — Testing approach (constitution III, FR-018)

- **Real-call** (`LLMXIVE_REAL_TESTS=1` + Dartmouth key): extract claims from a real spec; resolve the knot-count claim (9,988 verified vs 27,635 refuted/NEI) against a resolvable source; a true + false relational claim; a true + false superlative; a result claim with vs. without a valid receipt; end-to-end on PROJ-552's spec.
- **Offline pure-logic**: registry CRUD, pointer substitute/render round-trip, taxonomy classification given fixed inputs, receipt schema + HMAC sign/verify on real tmp files, superlative ordering given a candidate set, migration rewrite.
- **No mocks** of external services or executions (constitution III). Any external reference entering spec/code is WebFetch-verified first.

**Output**: all decisions resolved; no NEEDS CLARIFICATION remain. Proceed to Phase 1.
