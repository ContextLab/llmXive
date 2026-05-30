# Implementation Plan: Claim-Verification Layer (Claim Registry)

**Branch**: `016-claim-verification` | **Date**: 2026-05-30 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `specs/016-claim-verification/spec.md`

## Summary

Add a **constructive** claim-verification layer on top of spec-015's detective controls (F-18 citation guard, F-19 full-text grounding, F-14 adaptive kickback). Every check-worthy factual claim a doc-producing agent writes is **extracted → registered → substituted with a pointer → resolved** against an authoritative external source (numbers/citations via F-18/F-19; relational/causal/superlative via web-search+grounding) **or** a harness-signed internal execution receipt (our own results), then the document **renders the verified value via the pointer** so a model never retypes a fact. Unresolved/refuted/unbacked claims hard-block advancement and **auto-route** the specific claim back to the librarian (external) or implementation stage (results) for a bounded automated retry — repointing F-14's `cap→human` terminal to this automated loop. The new unified claim-marker + gate **replaces** F-18's `[UNVERIFIED]` marker (one-time migration; no back-compat).

## Technical Context

**Language/Version**: Python 3.11 (repo standard)
**Primary Dependencies**: existing `llmxive` package — `state/citations.py` (store pattern), `agents/citation_guard.py` (F-18), `librarian/verify.py` (`resolve_reference`), `grounding/` (F-19: service/entailment/full_text/cache), `convergence/engine.py` (panel gate) + `convergence/revisers/_self_consistency.py` (reviser loop), `pipeline/_kickback.py` + `pipeline/graph.py` (routing), `speckit/slash_command.py` (`_validate_artifact_citations` write chokepoint), `agents/prompts.py` (`substitute` `{{token}}`). External: `httpx` (retrieval, already used by F-19), `PyYAML` (stores), stdlib `hmac`/`hashlib`/`hmac.compare_digest` (receipt signing). Models via the free-first Dartmouth backend (`llmxive.credentials.load_dartmouth_key`).
**Storage**: YAML under `state/` — claims at `state/claims/<PROJECT-ID>.yaml` (flat list, mirrors `state/citations/<PROJECT-ID>.yaml`); result receipts at `state/results/<PROJECT-ID>/<result_id>.yaml`; resolution/grounding caches under the existing `state/librarian-cache/` TTL scheme.
**Testing**: `pytest` across `tests/{contract,integration,unit}` + `tests/real_call`; real-call tests gated by `LLMXIVE_REAL_TESTS=1` with a Dartmouth key, per constitution III & FR-018. Offline gate: `python -m pytest tests/contract tests/integration tests/unit -q -p no:cacheprovider --deselect tests/unit/test_audit_pdf.py::TestPdfAuditorOnLivePdfs`.
**Target Platform**: local pipeline runtime (darwin/linux); no network required for pure-logic paths.
**Project Type**: single project (Python library + automated pipeline).
**Performance Goals**: per-round re-extraction is cheap because verified values are cached by `claim_id` and receipts by `(code_sha, data_sha, seed, env_sha)`; resolution is hash-revalidated, not re-run.
**Constraints**: free-first models only; **no mocks** of external services/executions; fail-fast precondition checks; the receipt signing key MUST never enter any model's context.
**Scale/Scope**: per-project claim sets of ~tens–hundreds of claims; one registry + one result store per project; 7 claim types.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-checked after Phase 1 design.*

| Principle | Assessment |
|-|-|
| **I. Single Source of Truth** (NON-NEGOTIABLE) | PASS — reuses F-18/F-19/librarian/citation-store rather than re-implementing (FR-016); new `state/claims.py` + `state/results.py` follow the existing `state/citations.py` store pattern; the unified claim-marker **replaces** (not duplicates) F-18's `[UNVERIFIED]` with a one-time migration (FR-019). No forked logic. |
| **II. Verified Accuracy** (NON-NEGOTIABLE) | PASS — this layer *is* the enforcement of verified accuracy: every external reference is resolved against primary sources (FR-006) and every result against a signed receipt (FR-007/009); references introduced into spec/tests are WebFetch-verified before use (FR-018). |
| **III. Robustness & Real-World Testing** | PASS — FR-018 mandates real-call verification (real sources, real executions); mock-only paths prohibited; offline pure-logic tests are the secondary layer. |
| **IV. Cost Effectiveness (Free-First)** | PASS — free Dartmouth models; aggressive caching of resolutions/receipts (FR-015) avoids repeat calls. |
| **V. Fail Fast** | PASS — the gate validates claim resolution **before** a document advances (FR-012); receipt verification fails fast on missing/hash-mismatched backing (FR-009). |
| **VI. Convergent Review** (NON-NEGOTIABLE) | PASS — adds a blocking panel check that all reported claims resolve (FR-017); repoints F-14's `cap→human` terminal to an automated resolution loop (FR-014) without introducing a point system. |

**Result: PASS — no violations. Complexity Tracking section omitted (nothing to justify).**

## Project Structure

### Documentation (this feature)

```text
specs/016-claim-verification/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (module contracts)
│   └── claim-layer.md
└── tasks.md             # Phase 2 output (/speckit-tasks — not created here)
```

### Source Code (repository root)

```text
src/llmxive/
├── claims/                      # NEW package — the claim-verification layer
│   ├── __init__.py
│   ├── models.py                # Claim, ClaimStatus, ClaimKind, Verdict dataclasses
│   ├── extract.py               # LLM claim extraction (check-worthy, precision-favored)
│   ├── classify.py              # taxonomy classification (7 kinds)
│   ├── pointer.py               # {{claim:<id>}} substitution + render-from-store (pure)
│   ├── resolve.py               # per-kind resolver dispatch (external)
│   ├── triple.py                # NEW relational + superlative/candidate-set resolver
│   ├── service.py               # extract→register→substitute→resolve→render orchestrator
│   ├── gate.py                  # unified claim-marker + hard-block predicate (replaces F-18 marker)
│   └── migrate.py               # one-time migration: [UNVERIFIED] → unified marker
├── state/
│   ├── claims.py                # NEW store: load/save/upsert at state/claims/<PROJ>.yaml
│   └── results.py               # NEW receipt store: state/results/<PROJ>/<id>.yaml
├── results/                     # NEW — harness-signed execution receipts
│   ├── __init__.py
│   ├── receipt.py               # Receipt dataclass + HMAC sign/verify (key out of model ctx)
│   └── harness.py               # capture stdout/return + mint receipt (NOT an LLM)
├── agents/citation_guard.py     # MODIFY — route through unified marker (deprecate UNVERIFIED prefix)
├── grounding/                   # REUSE as a resolver (no change unless gap found)
├── librarian/verify.py          # REUSE resolve_reference; extend triple/set retrieval if needed
├── convergence/engine.py        # MODIFY — add "all claims resolved" blocking concern (FR-017)
├── convergence/revisers/_self_consistency.py  # MODIFY — run claim layer each round
├── pipeline/_kickback.py        # MODIFY — repoint cap→human terminal to automated loop
├── pipeline/graph.py            # MODIFY — route unresolved-claim kickback
└── speckit/slash_command.py     # MODIFY — claim layer at _validate_artifact_citations chokepoint

tests/
├── unit/        test_claims_*.py, test_results_receipt.py, test_claim_pointer.py, test_claim_migrate.py
├── integration/ test_claim_layer_chokepoint.py, test_claim_panel_gate.py, test_kickback_repoint.py
├── contract/    test_claims_store_contract.py, test_receipt_contract.py
└── real_call/   test_claim_resolve_real.py (9988 vs 27635), test_receipt_real.py, test_triple_real.py
```

**Structure Decision**: Single project. The layer lands as a new `src/llmxive/claims/` package plus two new state stores (`state/claims.py`, `state/results.py`) and a `src/llmxive/results/` receipt-minting package, composing the existing F-18/F-19/librarian/convergence/pipeline modules at their established extension points (the write chokepoint, the reviser loop, the panel gate, the kickback router). No new top-level project; everything follows the existing `src/llmxive/<area>/` + `tests/<tier>/test_<module>.py` conventions.
