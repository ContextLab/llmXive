# Tasks: Claim-Verification Layer (Claim Registry)

**Input**: Design documents from `specs/016-claim-verification/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/claim-layer.md, quickstart.md

**Tests**: REQUIRED for this feature — the spec mandates real-call verification (FR-018) and the constitution (III) prohibits mock-only paths for core functionality. Each story gets real-call + offline pure-logic tests.

**Organization**: Tasks are grouped by user story (US1–US4 from spec.md) for independent implementation and testing.

## Path Conventions

Single project. New code under `src/llmxive/claims/`, `src/llmxive/results/`, `src/llmxive/state/`; tests under `tests/{unit,integration,contract,real_call}/`. Existing modules modified at their established extension points (per `contracts/claim-layer.md`).

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create the new packages and confirm the offline gate is green before changes.

- [X] T001 Create the claims package skeleton: `src/llmxive/claims/__init__.py` (re-exports `service.process_document`, `gate.CLAIM_MARKER_PREFIX`) and `src/llmxive/results/__init__.py` (re-exports `harness.mint_receipt`, `receipt.verify_receipt`).
- [ ] T002 Capture the baseline offline gate result: run `python -m pytest tests/contract tests/integration tests/unit -q -p no:cacheprovider --deselect tests/unit/test_audit_pdf.py::TestPdfAuditorOnLivePdfs` and record pass/fail count so regressions are detectable.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Entities, stores, marker, and pure pointer logic that EVERY user story depends on. No story can proceed until this phase is complete.

- [X] T003 [P] Write failing unit test `tests/unit/test_claims_models.py` for `claims/models.py`: `compute_claim_id` is stable+deterministic for equal `(kind, canonical, context)` and differs when any differ; `ClaimKind`/`ClaimStatus` enum membership; `Claim`/`Verdict` construction.
- [X] T004 Implement `src/llmxive/claims/models.py`: `ClaimKind`, `ClaimStatus` enums (7 kinds / 5 statuses per data-model.md), `Verdict` (frozen), `Claim` dataclass, `compute_claim_id(kind, canonical, context) -> "c_"+sha256[:8]`. Make T003 pass.
- [X] T005 [P] Write failing contract test `tests/contract/test_claims_store_contract.py`: `state/claims.py` `load`/`save`/`upsert`/`get` round-trip through `state/claims/<PROJ>.yaml`; missing file → `[]`; `upsert` replaces by `claim_id` (no dup); honors `repo_root` override.
- [X] T006 Implement `src/llmxive/state/claims.py` mirroring `state/citations.py` (use `llmxive.config.repo_root()` for default root). Make T005 pass.
- [X] T007 [P] Write failing unit test `tests/unit/test_claim_pointer.py` for `claims/pointer.py`: `to_pointer`, `substitute_pointers` (idempotent), `render` substitutes `resolved_value` for VERIFIED claims and the unified marker for non-verified; round-trip reproduces verified values; original numerals never reappear for verified claims (pure, no IO).
- [X] T008 Implement `src/llmxive/claims/pointer.py` (pure functions). NOTE: the existing `agents/prompts.py` `_TOKEN_RE` only matches `[a-z_][a-z0-9_]*` token names — it does NOT match the colon in `{{claim:<id>}}`, so `pointer.py` MUST define its OWN regex `\{\{\s*claim:(?P<id>c_[0-9a-f]{8})\s*\}\}` in the same `{{…}}` style rather than calling `substitute()`. Make T007 pass.
- [X] T009 [P] Write failing unit test `tests/unit/test_claim_gate.py` for `claims/gate.py`: `CLAIM_MARKER_PREFIX == "[UNRESOLVED-CLAIM:"`, `mark_unresolved`, `has_unresolved_claims`, `find_unresolved_claims` (API mirrors F-18 `has_unverified_markers`/`find_unverified_markers`).
- [X] T010 Implement `src/llmxive/claims/gate.py`. Make T009 pass.
- [X] T011 [P] Write failing unit test `tests/unit/test_claim_classify.py` for `claims/classify.py`: superlative wording → `MAGNITUDE`; SPO/relation → `RELATIONAL`; "X causes Y" → `CAUSAL`; produced-metric phrasing → `RESULT`; citation/number → `CITATION`/`NUMERIC`; entity definition → `ENTITY_FACT`.
- [X] T012 Implement `src/llmxive/claims/classify.py` (deterministic rule-based classifier over `raw_text`/`canonical`). Make T011 pass.

**Checkpoint**: Foundation ready — entities, registry store, marker, pure pointer/render, and classifier all green offline.

---

## Phase 3: User Story 1 — No fabricated external claim can advance (Priority: P1) 🎯 MVP

**Goal**: Extract→register→substitute→resolve→render for external claims; block + auto-route unresolved ones; the model never retypes a verified fact. Direct fix for the 27,635→9,988 fabrication.

**Independent Test**: Run the spec stage on the project that fabricated "27,635 prime knots"; confirm the produced spec renders the verified 9,988 (resolvable source) or blocks+auto-routes — no fabricated number, no human-input request.

- [X] T013 [P] [US1] Write failing unit test `tests/unit/test_claim_resolve_dispatch.py` (NO mocks/fake backends — pure logic only): a pure `claims/resolve.select_resolver(kind) -> callable` maps each `ClaimKind` to its resolver; and the deterministic `grounding.service.number_substantiated(number, doc_text)` gate returns False when the number is ABSENT from real source text and True when present — establishing that `NOT_ENOUGH_INFO`/`VERIFIED` are driven by real content, never by absence of evidence. Real end-to-end resolution (real `resolve_reference`/`ground_cited_claim` calls) is covered in T018.
- [X] T014 [US1] Implement `src/llmxive/claims/resolve.py`: a pure `select_resolver(kind)` dispatch + `resolve(claim, *, backend, model, repo_root)`; numeric/citation → `librarian.verify.resolve_reference` + `grounding.service.ground_cited_claim` (incl. `number_substantiated` deterministic gate); map outcomes to `verified|refuted|not_enough_info`; cache via `grounding/cache.py`. Make T013 pass.
- [X] T015 [P] [US1] Write failing unit test `tests/unit/test_claim_extract.py`: `claims/extract.py::extract_claims` returns `PENDING` claims with populated `kind/raw_text/canonical/context`, and does NOT return design choices / thresholds / subjective statements (SC-007) — assert on a fixed representative document (real LLM call gated behind `LLMXIVE_REAL_TESTS`; offline asserts the post-processing filter that drops non-check-worthy spans).
- [X] T016 [US1] Implement `src/llmxive/claims/extract.py`: create the LLM extraction prompt asset `prompts/claim_extraction.md` (repo-root `prompts/` convention) + `extract_claims(...)`; precision-favored check-worthy filter; load prompt via `agents/prompts.py` `load_prompt` with `config.repo_root()` fallback for static assets. Make T015 pass.
- [X] T017 [US1] Implement `src/llmxive/claims/service.py::process_document(text, *, artifact_path, project_id, backend, model, repo_root)`: extract → upsert registry → substitute pointers → resolve each pending claim → render (verified values or marker) → return `(rendered, claims, GateReport)`; idempotent across rounds via cache.
- [X] T018 [P] [US1] Write failing real-call test `tests/real_call/test_claim_resolve_real.py` (gated `LLMXIVE_REAL_TESTS`): "27,635 prime knots at 13 crossings" resolves to `refuted`/`not_enough_info` (no resolvable source supports it); true "9,988" (OEIS A002863) resolves `verified` from a resolvable reference; rendered text contains the verified value or marker, never 27,635. VERIFY the 9,988 source URL with WebFetch before asserting on it.
- [X] T019 [US1] Wire the layer into the shared write chokepoint: modify `src/llmxive/speckit/slash_command.py::_validate_artifact_citations` to run `claims.service.process_document` on each `.md`/`.tex` artifact, rewrite in place, and block on unresolved claims.
- [X] T020 [P] [US1] Write failing integration test `tests/integration/test_claim_layer_chokepoint.py`: an artifact written through the chokepoint with a fabricated number is rewritten to carry the unified marker and is blocked; a verified one renders the value.
- [X] T021 [US1] Repoint auto-routing: modify `src/llmxive/pipeline/_kickback.py` + `pipeline/graph.py::_decide_next_stage` so an unresolved-claim kickback routes the specific claim back to the librarian (external) under a bounded retry budget instead of escalating to a human (FR-013/014); `CONVERGENCE_KICKBACK_CAP` terminal repointed to the automated loop.
- [X] T022 [P] [US1] Write failing integration test `tests/integration/test_kickback_repoint.py`: exhausting the convergence kickback no longer escalates to human as routine flow; an unresolved external claim is routed to the librarian for an automated retry; human escalation only after the bounded budget is exhausted.

**Checkpoint**: US1 independently testable — fabricated external claims cannot advance; verified values render; routing is automated.

---

## Phase 4: User Story 2 — Reported results trace to real runs (Priority: P1)

**Goal**: Harness-signed execution receipts; result claims resolve only against a matching receipt; no LLM can mint/alter a receipt; results usable as first-class downstream sources.

**Independent Test**: Produce a result + backing receipt; confirm the write-up cites it by pointer and renders the receipt value; introduce a results number with no receipt → blocked.

- [x] T023 [P] [US2] Write failing unit test `tests/unit/test_results_receipt.py`: `results/receipt.py` `sign_receipt`/`verify_receipt` round-trip on real tmp files; ANY field mutation fails `verify_receipt` (uses `hmac.compare_digest`); `load_signing_key` returns bytes from a process-local secret and is never embedded in prompt text.
- [x] T024 [US2] Implement `src/llmxive/results/receipt.py`: `Receipt` dataclass (data-model.md), canonical-payload HMAC `sign_receipt`/`verify_receipt`, `load_signing_key` (env/credentials discipline like the Dartmouth key; never passed to a model). Make T023 pass.
- [x] T025 [P] [US2] Write failing contract test `tests/contract/test_receipt_contract.py`: `state/results.py` persists/loads receipts at `state/results/<PROJ>/<result_id>.yaml`; `result_backed(value, project_id)` returns a receipt only when `output_sha256` matches AND `verify_receipt` passes.
- [x] T026 [US2] Implement `src/llmxive/state/results.py` (store) and `src/llmxive/results/harness.py`: `mint_receipt(...)` (captures real stdout/return + content hash; harness-only, never an agent path) and `result_backed(value, project_id, *, repo_root)`. Make T025 pass.
- [x] T027 [US2] Extend `claims/resolve.py` so `RESULT`-kind claims resolve via `results.harness.result_backed` (matching signed receipt) and block when unbacked (FR-009); a resolved result is citable by `result:<id>` pointer (FR-010).
- [x] T028 [P] [US2] Write failing real-call test `tests/real_call/test_receipt_real.py` (gated): run a real tiny script via the harness, mint a receipt, resolve a result claim against it (verified); then a results numeral with no receipt → blocked; and an attempt to forge/alter a receipt fails verification (SC-004).
- [x] T029 [US2] Wire result-claim blocking into `claims/service.process_document` so a results-section numeral with no backing receipt is marked + blocked + routed back to the implementation stage.

**Checkpoint**: US2 independently testable — every advanced result number traces to a verified receipt; forgery is impossible.

---

## Phase 5: User Story 3 — Non-numeric claims are verified (Priority: P2)

**Goal**: Type-appropriate resolution for magnitude/superlative, relational, causal, entity claims (not text overlap, not assumed true).

**Independent Test**: Provide true+false relational and true+false superlative claims; each is classified and the false ones flagged/blocked.

- [X] T030 [P] [US3] Write failing unit test `tests/unit/test_claim_triple.py` (NO mocks/fake backends — pure logic only): the pure ordering check `claims/triple.check_ordering(candidates, claim)` flags a wrong "largest" given a real candidate list (list in → ordering verdict out, no network), and the pure `claims/triple.decompose_triple(text) -> (subject, relation, object)` parses an SPO assertion correctly. Real retrieval + entailment is exercised in T033.
- [X] T031 [US3] Implement `src/llmxive/claims/triple.py`: pure helpers `decompose_triple` + `check_ordering`, plus `resolve_relational` (decompose → retrieve citable source via librarian → entailment) and `resolve_superlative` (retrieve full candidate set → `check_ordering`). Make T030 pass.
- [X] T032 [US3] Extend `claims/resolve.py` dispatch: `MAGNITUDE`→`resolve_superlative`, `RELATIONAL`→`resolve_relational`, `CAUSAL`→grounding requiring a citable source (else `NOT_ENOUGH_INFO`, never model inference), `ENTITY_FACT`→authoritative-reference entailment.
- [X] T033 [P] [US3] Write failing real-call test `tests/real_call/test_triple_real.py` (gated): a true relational claim resolves `verified` and a false one `refuted`; a true superlative `verified` and a false one `refuted`/`not_enough_info`. WebFetch-verify any external source used in assertions first.

**Checkpoint**: US3 independently testable — each non-numeric claim type flags a known-false instance (SC-008).

---

## Phase 6: User Story 4 — Verified facts reused "for free" and never drift (Priority: P3)

**Goal**: Render from registry; reuse verified values across rounds/stages/documents with no re-resolution; invalidate cache when the underlying source/receipt hash changes.

**Independent Test**: Verify a claim once; a later document referencing it renders the identical cached value with no new resolution call and no chance for the model to change it.

- [X] T034 [P] [US4] Write failing integration test `tests/integration/test_claim_reuse.py`: a verified claim referenced in two artifacts renders an identical value from the registry; the second render performs no new resolution (assert the resolver short-circuits on the existing `VERIFIED` registry entry — e.g. the real `grounding/cache.py` verdict cache is hit, or a counter wrapping the REAL resolver stays flat; not a fake resolver); changing the underlying source/receipt hash invalidates the cached resolution and forces re-resolution (FR-015).
- [X] T035 [US4] Implement cross-document reuse + invalidation in `claims/service.py`/`claims/resolve.py`: short-circuit resolution when a `VERIFIED` registry entry exists and its source/receipt hash is unchanged; invalidate (`VERIFIED → PENDING`) on hash change. Make T034 pass.

**Checkpoint**: US4 independently testable — verified facts are consistent and reused with no drift.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Panel gate, marker migration, prompt-agent registry, and full-run verification.

- [X] T036 [P] Write failing integration test `tests/integration/test_claim_panel_gate.py`: the convergence panel emits a blocking SCIENCE-severity concern when a reviewed document has unresolved claims (`has_unresolved_claims` true), and converges only when all reported claims are resolved (FR-017).
- [X] T037 Modify `src/llmxive/convergence/engine.py` to synthesize the blocking "all claims resolved" concern (sibling to `_unverified_marker_concerns`) using `claims.gate.has_unresolved_claims`. Make T036 pass.
- [X] T038 Wire the claim layer into the reviser loop: modify `src/llmxive/convergence/revisers/_self_consistency.py::run_with_self_consistency` to run `claims.service.process_document` on revised artifacts each round (earliest interception, FR-002).
- [X] T039 [P] Write failing unit test `tests/unit/test_claim_migrate.py`: `claims/migrate.py::migrate_unverified_markers` rewrites `[UNVERIFIED: …]` → `[UNRESOLVED-CLAIM: …]`, seeds registry entries as `NOT_ENOUGH_INFO`, returns changed files; `--dry-run` changes nothing.
- [X] T040 Implement `src/llmxive/claims/migrate.py` + `python -m llmxive.claims.migrate` entrypoint (replaces F-18 marker, FR-019). Make T039 pass.
- [X] T041 Implement the agent registry (FR-001): a maintained list in `claims/__init__.py` (or `claims/agents.py`) enumerating every claim-producing stage (spec, clarify, plan, tasks, implement, paper-spec, paper-clarify, flesh-out, results/summary producers); add `tests/unit/test_claim_agent_registry.py` asserting the chokepoint covers each.
- [X] T042 Deprecate/replace the F-18 `[UNVERIFIED]` path in `src/llmxive/agents/citation_guard.py` so F-18/F-19 operate as resolvers within the layer and the unified marker is the single block signal (FR-019); update existing `tests/unit/test_citation_guard.py` expectations to the unified marker.
- [ ] T043 Run the one-time migration `python -m llmxive.claims.migrate` across the repo; commit the migrated artifacts.
- [ ] T044 Run the full offline gate (`pytest tests/contract tests/integration tests/unit -q -p no:cacheprovider --deselect tests/unit/test_audit_pdf.py::TestPdfAuditorOnLivePdfs`) and the gated real-call suite (`LLMXIVE_REAL_TESTS=1 pytest tests/real_call -q`); fix code (never tests) until green.
- [ ] T045 Update `quickstart.md` only if any public signature drifted during implementation; confirm the SC-001…SC-008 success signals each map to a passing test.

---

## Dependencies & Execution Order

- **Setup (Phase 1)** → **Foundational (Phase 2)** block everything.
- **US1 (Phase 3)** is the MVP; depends only on Foundational. Deliverable on its own.
- **US2 (Phase 4)** depends on Foundational (+ `claims/resolve.py` from US1 for T027/T029). Otherwise independent of US1's external path.
- **US3 (Phase 5)** depends on Foundational + `claims/resolve.py` (US1).
- **US4 (Phase 6)** depends on US1 (verified claims existing to reuse).
- **Polish (Phase 7)** depends on US1–US4 surfaces; T038/T037 need `claims.service`/`claims.gate`; migration (T040/T043) independent after gate exists.

## Parallel Opportunities

- Phase 2: T003, T005, T007, T009, T011 (distinct test files) run in parallel; each implementation follows its test.
- Within US1: T013/T015/T018/T020/T022 test files are `[P]`; implementations are sequential where they share `claims/resolve.py`/`service.py`.
- Across stories: once Foundational is done, US2's receipt stack (T023–T026) can proceed in parallel with US1's external path (different files).

## Implementation Strategy

**MVP = Phase 1 + Phase 2 + Phase 3 (US1).** That alone stops the fabrication blocking the pipeline (SC-001/002/005). Then layer US2 (results provenance, SC-003/004), US3 (non-numeric, SC-008), US4 (reuse, SC-006), and Polish (panel gate, migration, full-run). Tests precede implementation in every task pair; real-call tests are gated by `LLMXIVE_REAL_TESTS` per the constitution.
