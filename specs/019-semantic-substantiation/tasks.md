# Tasks: Semantic Substantiation for the Claim-Fill Layer

**Input**: Design documents from `/specs/019-semantic-substantiation/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/prose-gate.md, quickstart.md

**Tests**: INCLUDED — the spec mandates a real-call acceptance matrix
(Constitution III). Deterministic layers get offline unit tests; the semantic
gate is proven by real Dartmouth calls. Mock/recording backends appear ONLY as a
secondary fast-feedback layer using the same call syntax, never as the primary
proof of the `assess` path.

**Organization**: by user story (US1–US4) so each is independently testable.

## Format: `[ID] [P?] [Story?] Description with file path`

- **[P]**: parallelizable (different files, no incomplete-task dependency)
- **[US#]**: the user story a phase task serves

## Path Conventions

Single Python project: `src/llmxive/`, `tests/` at repo root.

---

## Phase 1: Setup

- [ ] T001 Capture the offline-gate baseline on branch `019-semantic-substantiation`: run `python -m pytest tests/contract tests/integration tests/unit -q -p no:cacheprovider --deselect tests/unit/test_audit_pdf.py::TestPdfAuditorOnLivePdfs` and record the passed/failed counts in `notes/spec-015-review-status.md` (the number every later phase must not regress).

---

## Phase 2: Foundational (BLOCKING — required before US1)

- [ ] T002 [P] Write failing test `tests/unit/test_fill_channels_kind.py` asserting the C1 contract: `is_structured(c)` True for `constants/oeis/wikidata`; `is_prose(c)` True for `wikipedia/theorem/paper`; `is_prose("unknown-xyz")` True (fail-closed); `is_structured(c) != is_prose(c)` for a sample set.
- [ ] T003 Implement the classifier in `src/llmxive/fill/channels/__init__.py`: add `STRUCTURED_CHANNELS = frozenset({"constants","oeis","wikidata"})`, `is_structured(channel)`, `is_prose(channel) = not is_structured(channel)`. Run T002 → green.
- [ ] T004 [P] Write/extend a test in `tests/unit/test_claim_canonical.py` asserting a public `claims.canonical.subject_keywords(claim)` returns the same tokens the former `_subject_keywords` produced (lowercase, deduped, singularized, digit-free).
- [ ] T005 Promote `claims/canonical._subject_keywords` → public `subject_keywords` (single implementation); update every internal caller of `_subject_keywords` in the repo to the public name. Run T004 + full canonical tests → green.

**Checkpoint**: classifier + public `subject_keywords` exist and are tested; US1 can proceed.

---

## Phase 3: User Story 1 — Coincidental prose number never substantiates a fill (Priority: P1) 🎯 MVP

**Goal**: a PROSE candidate is admitted only when subject keywords co-occur near
the value AND `assess` returns `grounded`; coincidental matches are blocked.

**Independent test**: the Almoravid "≤6" real-call case returns BLOCKED, never `6`.

- [ ] T006 [P] [US1] Create `src/llmxive/fill/relevance.py` with the `_SourceDoc(full_text, abstract="")` frozen dataclass and a deterministic value-locator: numeric values located via `agents.grounding_guard._number_anchor_re(value)`; entity values via the normalized substring search reused from `fill/extract._entity_present` normalization. Export a `_subject_cooccurs(value, source_text, claim) -> bool` using `claims.canonical.subject_keywords` and the entailment `_WINDOW` (±320 chars) as the co-occurrence window.
- [ ] T007 [US1] Add `prose_substantiated(value, source, claim, *, backend, model, repo_root) -> bool` to `src/llmxive/fill/relevance.py`: return False if `_subject_cooccurs` fails (no LLM call); return False if `backend is None`; else call `grounding.entailment.assess(claim.canonical or claim.raw_text, _SourceDoc(source.text), backend=backend, model=model, repo_root=repo_root)` and return `verdict.status == "grounded"` (fail-closed on any other status/exception).
- [ ] T008 [P] [US1] Write `tests/unit/test_fill_relevance.py`: (a) coincidental case — `_subject_cooccurs` False when no subject keyword is within the window of the value, AND a recording backend proves `assess` is NOT called; (b) `backend is None` → `prose_substantiated` False; (c) co-occurrence true + recording backend returning a `grounded` Verdict (same `assess` syntax) → True; (d) `contradicted`/`not_found`/raising backend → False.
- [ ] T009 [US1] Add `_accept(candidate, source, claim, *, backend, model, repo_root) -> bool` to `src/llmxive/fill/extract.py` (= `present_in_source(candidate, source, claim.kind)` AND, for `is_prose(source.channel)`, also `prose_substantiated(...)`; STRUCTURED → present_in_source only). Route BOTH `extract_value` admission sites (offline `backend is None` path and LLM path) through `_accept`. Import `is_prose` from `fill.channels` and `prose_substantiated` from `fill.relevance`.
- [ ] T010 [US1] Extend `tests/unit/test_fill_extract_gate.py`: `_accept` on a STRUCTURED (`constants`/`oeis`) candidate equals today's `present_in_source` (no LLM call); `_accept` on a PROSE candidate with `backend=None` → False (fail-closed); `_accept` on a PROSE coincidental candidate → False. Confirm the existing `present_in_source`/extract-gate tests still pass unchanged.
- [ ] T011 [US1] Add `tests/real_call/test_semantic_substantiation.py` with the NEGATIVE case (SC-001): a knot crossing-number claim whose value `6` appears only as "about 6 generations" in a Wikipedia "Almoravid dynasty" body → `extract_value`/fill returns no value (BLOCKED); assert `6` is never returned. Real Dartmouth backend (`LLMXIVE_REAL_TESTS=1`, key via `credentials.load_dartmouth_key`).

**Checkpoint**: the headline bug is fixed and proven by a real call.

---

## Phase 4: User Story 2 — Proven-good paths, zero regression (Priority: P1)

**Goal**: STRUCTURED channels exempt; the 9988/π/Paris paths still pass.

**Independent test**: the no-regress suites stay green with the gate active.

- [ ] T012 [US2] Add to `tests/real_call/test_semantic_substantiation.py` the POSITIVE STRUCTURED cases: "9,988 prime knots at 13 crossings" via OEIS b-file still fills `9988` (SC-002, gate skipped); `π ≈ 3.14159` via constants still fills (SC-003). Assert the prose gate is NOT consulted for these (recording/spy on `prose_substantiated` shows zero calls for STRUCTURED).
- [ ] T013 [US2] Add the POSITIVE PROSE case (SC-004): "the capital of France is Paris" with a supporting Wikipedia body → `assess = grounded` → `Paris` kept.
- [ ] T014 [US2] Run and confirm GREEN (fix code, never the tests, on any failure): `tests/integration/test_exact_count_no_regress.py`, `tests/unit/test_grounding_service.py`, `tests/unit/test_fill_extract_gate.py`, `tests/unit/test_claim_resolve_dispatch.py`.

**Checkpoint**: no regression on any proven-good path.

---

## Phase 5: User Story 3 — Bound/digit-less claims blocked before any fetch (Priority: P2)

**Goal**: refuse to numeric-fill bound/inequality and digit-less claims pre-fetch.

**Independent test**: a bound claim and a digit-less claim are blocked with no fetch.

- [ ] T015 [US3] Add the claim-kind pre-guard to `src/llmxive/fill/service.py::fill_claim`, immediately after the existing kind guard and before cache lookup/`subject_query`/fetch: for a NUMERIC claim, if `claims.canonical._asserted_is_bound_or_percent(claim.raw_text, _asserted_value(...))` (bound/percent) OR `_asserted_value(claim.raw_text or claim.canonical) is None` (digit-less), return a `blocked` `FillResult` with a clear reason. Reuse the canonical guards; do not reimplement.
- [ ] T016 [P] [US3] Write `tests/unit/test_fill_claimkind_preguard.py`: a bound claim ("braid index ≤ crossing number …") → `fill_claim` returns `status="blocked"` and a recording backend / fetch counter proves NO channel fetch or `subject_query` ran (SC-006); a digit-less NUMERIC claim → blocked, no fetch; a normal digit-bearing NUMERIC claim is NOT short-circuited by the pre-guard.
- [ ] T017 [US3] Add the real-call BOUND pre-guard case (SC-006) to `tests/real_call/test_semantic_substantiation.py`: "braid index ≤ crossing number for most knots" → BLOCKED before any fetch.

**Checkpoint**: the bound/digit-less class is eliminated at the cheapest point.

---

## Phase 6: User Story 4 — Contradicted prose corrected, never grounded (Priority: P3)

**Goal**: a PROSE source that contradicts the value never grounds the wrong value.

**Independent test**: Sydney/Canberra case never grounds Sydney.

- [ ] T018 [US4] Add the CONTRADICTED real-call case (SC-005) to `tests/real_call/test_semantic_substantiation.py`: "the capital of Australia is Sydney" against a Canberra-asserting body → `assess = contradicted` → `Sydney` never grounded (resolution yields Canberra or stays unresolved, never Sydney).
- [ ] T019 [US4] Document the FR-008 invariant in `src/llmxive/fill/conflict.py` (a module/`choose` docstring note): `choose` only ever receives `_accept`-passed candidates, so a relevance-failing PROSE candidate is never ranked and an empty list blocks upstream — no gate is duplicated here (Constitution I). No functional change.

**Checkpoint**: contradiction handled; the chokepoint invariant is documented.

---

## Phase 7: Polish & Cross-Cutting

- [ ] T020 [P] `ruff check .` and `mypy src/llmxive` clean (fix any new findings in the touched files).
- [ ] T021 Run the FULL offline gate (T001 command) and confirm the passed count is ≥ the T001 baseline + the new tests, with zero failures (fix code, not tests).
- [ ] T022 [P] Confirm `tests/unit/test_llm_call_centralization.py` still passes (relevance.py reaches the backend only via `assess`→`reasoning_chat`; it must contain no direct `backend.chat(`).
- [ ] T023 Run the real-call acceptance matrix end-to-end per `quickstart.md` (all six rows) and record the results + the resolved residual in `notes/spec-015-review-status.md`.

---

## Dependencies & Execution Order

- **Phase 1 (Setup)** → **Phase 2 (Foundational)** are prerequisites for everything.
- **Phase 2** (classifier + `subject_keywords`) BLOCKS US1 (T006/T007/T009 import them).
- **US1 (Phase 3)** is the MVP and must complete before US2's regression sign-off
  is meaningful. US2 (Phase 4) verifies US1 didn't regress the proven paths.
- **US3 (Phase 5)** is independent of US1's gate (it is a pre-fetch guard) and may
  proceed in parallel with US1 once Phase 2 is done.
- **US4 (Phase 6)** depends on US1's `prose_substantiated`/`assess` wiring.
- **Phase 7** runs last.

## Parallel Opportunities

- T002 and T004 (different test files) are `[P]`.
- After Phase 2: T006 (`relevance.py`) and T015/T016 (US3 pre-guard, `service.py`)
  touch different files and can proceed in parallel.
- T008, T016 (`[P]`) are independent test files.
- T020, T022 (`[P]`) are independent checks.

## Implementation Strategy

**MVP = User Story 1** (Phases 1–3): the coincidental-prose block, proven by the
Almoravid real-call negative. Ship/verify that first; US2 then proves zero
regression, US3 adds the cheap pre-guard, US4 covers contradiction. Every gate is
fail-closed; no test is ever weakened to pass.
