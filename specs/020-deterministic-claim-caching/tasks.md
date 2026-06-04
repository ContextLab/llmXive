# Tasks: Deterministic Claim Caching + Planning-Stage Reference-Only Verification

**Input**: Design documents from `specs/020-deterministic-claim-caching/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/claim-layer-contracts.md, quickstart.md

**Tests**: REQUIRED for this feature — FR-016 mandates real-call tests for externally-dependent paths
and offline tests for the deterministic logic. Test tasks precede their implementation (TDD).

**Organization**: grouped by user story (US1, US2 = P1; US3 = P2). MVP = US1 (the immediate unblocker).

## Format: `[ID] [P?] [Story] Description with file path`

- **[P]**: parallelizable (different files, no dependency on an incomplete task)
- **[Story]**: US1 / US2 / US3 (Setup/Foundational/Polish carry no story label)

## Path Conventions

Single project: source at `src/llmxive/`, tests at `tests/`. Docs/templates at repo root
(`.specify/templates/`, `.claude/skills/`, `agents/prompts/`, `projects/PROJ-552-*/.specify/templates/`).

---

## Phase 1: Setup (baseline + drift guard)

**Purpose**: capture the no-regression baseline and confirm the plan's code anchors still hold.

- [X] T001 Capture the baseline offline gate: run `python -m pytest tests/contract tests/integration tests/unit -q -p no:cacheprovider --deselect tests/unit/test_audit_pdf.py::TestPdfAuditorOnLivePdfs` plus `ruff check .` and `mypy src/llmxive`; record the passing test count and clean lint/type state in the PR/commit notes (the figure to match at T032/T034).
- [X] T002 [P] Confirm the real-call harness is usable: verify `llmxive.credentials.load_dartmouth_key()` resolves a key and that only free models are selectable (free-only guard), so the FR-016 real-call tasks can run; record availability.

---

## Phase 2: Foundational (blocking prerequisites — MUST complete before US1/US2)

**Purpose**: the single stage-class predicate used by US1's planning branch and the fill short-circuit.

- [X] T003 Write failing unit test `tests/unit/test_stage_class.py` for the C1 contract: `is_planning_stage("spec"|"clarify"|"plan"|"tasks") is True`; `is_planning_stage("paper_plan"|"paper_tasks"|None|"unknown") is False`; `PLANNING_STAGE_LABELS` is exactly `{"spec","clarify","plan","tasks"}`.
- [X] T004 Implement `src/llmxive/claims/stage.py` (`PLANNING_STAGE_LABELS: frozenset[str]`, `is_planning_stage(stage_label: str | None) -> bool`) — single SSoT for the planning/full distinction (FR-001); make T003 pass.

**Checkpoint**: stage classification exists and is tested → US1 and US2 can proceed.

---

## Phase 3: User Story 1 — Planning verifies references; low-level claims are stripped/smoothed (Priority: P1) 🎯 MVP

**Goal**: in specify/clarify/plan/tasks the claim layer verifies citations only; a detected low-level
claim is replaced by a higher-level statement (no fetch/ground/kickback); an unresolvable citation
still blocks.

**Independent test**: run a planning-stage doc with a wrong low-level number + a citation → number
generalized (no specific value remains), no `[UNRESOLVED-CLAIM:]` marker, no kickback, citation still
checked; a fabricated DOI still blocks; a second round leaves the smoothed passage unchanged.

### Tests (write first — they must fail before impl)

- [X] T005 [P] [US1] Write `tests/unit/test_strip_smooth.py` (C3): asserts `strip_and_smooth` output is claim-free (`extract_claims` finds no low-level claim with the same `subject_key`), is idempotent (no-op on already-smoothed text — FR-002b/SC-001a), preserves an embedded citation (FR-002c), and that the **deterministic fallback** path (force the LLM rewrite to still contain the claim) removes the asserting clause and yields grammatical, claim-free text.
- [X] T006 [P] [US1] Write `tests/unit/test_planning_skip.py` (C2/C8): with `stage_label` planning, a low-level NUMERIC claim triggers **no** external fetch/locator/grounding call (assert the fetch entry point is not invoked) and **no** `[UNRESOLVED-CLAIM:]` marker is emitted, and the stage produces no low-level kickback (FR-002/003).
- [X] T007 [P] [US1] Write `tests/integration/test_planning_references_only.py` (real-call, `LLMXIVE_REAL_TESTS=1`): `test_lowlevel_stripped` (a planning doc with a wrong count → generalized, no marker, no kickback, advances) and `test_fabricated_doi_blocks` (a fabricated DOI in the same doc → reference flagged unresolvable, advancement blocked, fail-closed — FR-004/SC-002).

### Implementation

- [X] T008 [US1] Implement `src/llmxive/claims/smooth.py::strip_and_smooth(passage, claim, *, backend, model)` — LLM rewrite via `backends/router.py::reasoning_chat` → re-detect guard (`claims/extract.extract_claims`) → deterministic clause-removal fallback; preserves citations/RQ/method (FR-002a/b/c). Make T005 pass.
- [X] T009 [US1] Add `stage_label: str | None` to `SlashCommandContext` and forward it in `_validate_artifact_citations` → `process_document(..., stage_label=ctx.stage_label)` in `src/llmxive/speckit/slash_command.py` (C9).
- [X] T010 [US1] Add `stage_label: str | None = None` to `src/llmxive/claims/service.py::process_document`; in the planning branch (`is_planning_stage(stage_label)`) skip resolve/fill/ground + the `[UNRESOLVED-CLAIM:]` marker for low-level kinds and route each detected low-level claim through `strip_and_smooth`, replacing its span in the document; CITATION claims keep their existing path (C2; FR-002/002a/003). Make T006 pass.
- [X] T011 [US1] Add a `stage_label` parameter to `src/llmxive/fill/channels/__init__.py::channels_for` and short-circuit the fill gate in `src/llmxive/fill/service.py` (around L307-311) so a planning-stage low-level claim returns no channels / does no fetch (C8; defense-in-depth with T010).
- [X] T012 [US1] Populate `ctx.stage_label` from each speckit command's existing stage label. **First verify the actual emitted label strings** (grep each `*_cmd.py` for `stage_label=`): the specify/clarify path emits `"spec"` (and possibly `"clarify"`), `plan_cmd.py` emits `"plan"`, `tasks_cmd.py` emits `"tasks"`. Ensure **every** planning command's emitted label is a member of `PLANNING_STAGE_LABELS` (add any missing actual label, e.g. `"specify"`, to the frozenset in `claims/stage.py` so the set matches reality), and confirm `paper_plan_cmd.py`/`paper_tasks_cmd.py` emit `paper_*` (→ full verification, not planning) (FR-001/005).
- [X] T013 [US1] Verify+wire the reference validator path so it still runs for planning artifacts and an unresolvable citation still sets `has_blocking_citations` (`agents/reference_validator.py` unchanged behavior; confirm it is invoked independently of the low-level-claim handling). Make T007's `test_fabricated_doi_blocks` pass (FR-004).

**Checkpoint**: US1 independently testable — planning skips/strips low-level claims, references still gate.

---

## Phase 4: User Story 2 — A verified claim is frozen and never waffles (Priority: P1)

**Goal**: a VERIFIED claim is immutable; reuse is by value-independent `subject_key`; the value rides
in the doc as a durable placeholder, substituted only in a rendered view.

**Independent test**: verify in round 1, rephrase in round 2 → same record reused, no re-resolution,
identical value; re-run from a clean checkout → frozen value persists; a transient failure never
re-opens a VERIFIED record; the stored doc never bakes a value into prose.

### Tests (write first)

- [X] T014 [P] [US2] Write `tests/unit/test_frozen_claim_cache.py` (C4/C5): a VERIFIED `(kind, subject_key)` record is returned by `load_verified_by_subject` and adopted with **no** call to `resolve()` for a rephrased twin (FR-009/010); a transient resolver failure on a later round does **not** downgrade/overwrite the VERIFIED record (FR-011); re-resolution happens only when `source_hash` differs. **Also assert non-collision** (spec edge case, FR-009): a claim whose `subject_key` legitimately *differs* (a genuinely distinct subject) is NOT served the frozen value — the freeze must not collapse two distinct subjects into one record.
- [X] T015 [P] [US2] Write `tests/unit/test_value_independent_cache_key.py` (C7): the fill cache key for a PENDING phrasing ("49") and a VERIFIED phrasing ("9,988") of the **same** fact (same `subject_key`, same qualifiers) is **identical**; qualifier numbers still differentiate genuinely distinct subjects (FR-012).
- [ ] T016 [P] [US2] Write `tests/unit/test_durable_placeholder.py` (C6): `render` leaves a durable `{{claim:c_…}}` for a VERIFIED claim (no literal baked into prose); `strip_claim_artifacts` **preserves** that pointer while still removing `[UNRESOLVED-CLAIM:]` markers and orphan pointers; `render_view` substitutes the frozen value; a stored doc round-trips the loop with zero baked-in values (FR-007/008/SC-007).
- [X] T017 [P] [US2] Write `tests/integration/test_paper_stage_freeze.py` (real-call): `test_exact_count_frozen` (9,988 OEIS count verifies + later lookup does not re-resolve), `test_rephrase_no_waffle` (verify→rephrase across 3 rounds → same value, 0 re-resolutions — SC-003), `test_cross_run_frozen` (clean-checkout re-run reads frozen value, 0 cold re-resolutions — SC-004), `test_constants_and_entities` (π≈3.14159, capital of France = Paris still verify — SC-005).

### Implementation

- [X] T018 [US2] Implement `src/llmxive/state/claims.py::load_verified_by_subject(project_id, repo_root) -> dict[tuple[ClaimKind, str], Claim]` over VERIFIED records with non-empty `subject_key` (C4; FR-009/013). Make the lookup half of T014 pass.
- [X] T019 [US2] In `src/llmxive/claims/service.py::resolve_registered_claims`, key reuse by `(kind, subject_key)` via `load_verified_by_subject` (replacing the `claim_id` reuse at L92) and guard the self-heal re-resolution (L94-107) so a VERIFIED record is never re-resolved/overwritten unless `source_hash` changed (C5; FR-009/010/011). Make T014 pass.
- [X] T020 [US2] Drop the asserted value from the cache key: `fill/service.py::_cache_key_parts` (remove `claim.resolved_value`), use a value-excluded fingerprint in `fill/subject_query.py` (exclude the asserted token, keep qualifier numbers), and drop the `number` component from `grounding/cache.py` verdict key (C7; FR-012). Make T015 pass.
- [ ] T021 [US2] Durable placeholder + rendered view: `claims/pointer.py::render` emits the durable `{{claim:id}}` for VERIFIED claims instead of baking the value; add `claims/pointer.py::render_view(text, registry_by_id)`; `claims/extract.py::strip_claim_artifacts` preserves durable pointers (C6; FR-007/008). Make T016 pass.
- [ ] T022 [US2] Hand the **rendered view** (`render_view` from the frozen store) to the review panel in `src/llmxive/speckit/_stage_panel.py` so reviewers judge values while the stored artifact keeps placeholders (C9/FR-008); convergence still operates on the placeholder form.

**Checkpoint**: US2 independently testable — verified claims are frozen, value-independent, placeholder-carried.

---

## Phase 5: User Story 3 — Planning docs don't assert low-level claims in the first place (Priority: P2)

**Goal**: templates/prompts instruct producers to state RQ + method + references and defer empirical
specifics. Prevention complementing US1's cure.

**Independent test**: generate a fresh spec/plan for a research project → success criteria/technical
context describe what to measure + the reference, not pre-asserted specific values.

- [X] T023 [P] [US3] Edit `.specify/templates/spec-template.md` Success Criteria examples (L112-115): replace specific-number examples with "what will be measured + against which reference; defer specific values to implementation" guidance (FR-006).
- [X] T024 [P] [US3] Edit `.specify/templates/plan-template.md` Technical Context (L26 Performance Goals, L28 Scale/Scope): replace numeric examples with reference-anchored phrasing + a "defer empirical specifics" note (FR-006).
- [X] T025 [P] [US3] Edit `.claude/skills/speckit-specify/SKILL.md` Success Criteria Guidelines (L313-330) to show method/reference examples and to instruct deferral of specific empirical values to research/implementation (FR-006).
- [X] T026 [P] [US3] Edit `.claude/skills/speckit-clarify/SKILL.md`, `speckit-plan/SKILL.md`, `speckit-tasks/SKILL.md` scope notes to add the "state RQ+method+references; defer empirical specifics" guidance (FR-006).
- [X] T027 [P] [US3] Edit `agents/prompts/panels/panel_plan_data_resources.md` to instruct the data-resources panel to evaluate that planning docs cite sources/references rather than asserting specific empirical counts (FR-006).
- [X] T028 [US3] Sync the per-project copies `projects/PROJ-552-quantifying-the-complexity-of-knot-diagr/.specify/templates/spec-template.md` and `plan-template.md` with the T023/T024 edits (FR-006 requires per-project copies updated; keep in sync until de-duplicated).
- [X] T029 [US3] Write `tests/integration/test_planning_doc_scope.py` (real-call): generate a fresh planning doc for an empirical project and assert (a) running the claim-layer low-level detector (`claims/extract.extract_claims` + `classify`) over the doc's Success Criteria / Technical Context finds **zero** non-citation (low-level) claims, and (b) those sections contain ≥1 reference/source anchor — i.e. measurable outcomes are expressed as *what to measure + source/reference*, not pre-asserted specific empirical values (US3 §1).

**Checkpoint**: producers are steered away from low-level numbers; US1 still catches any that slip in.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [X] T030 Write `tests/integration/test_proj552_planning_no_kickback.py` (SC-006): drive the PROJ-552 planning stage and assert the wrong "49 prime knots at crossing 13" is absent/generalized in the planning artifact, citations resolve, convergence advances, and the kickback trail contains no low-level-claim entry.
- [X] T031 No-regression sweep (FR-014/FR-005/SC-005): run `tests/integration/test_exact_count_no_regress.py`, `tests/integration/test_claim_subject_reuse.py`, and `tests/unit/test_claim_* tests/unit/test_fill_* tests/unit/test_grounding_*`; fix any breakage in the **code** (never the tests) until green.
- [X] T032 Full offline gate green: `python -m pytest tests/contract tests/integration tests/unit -q -p no:cacheprovider --deselect tests/unit/test_audit_pdf.py::TestPdfAuditorOnLivePdfs`, then `ruff check .` and `mypy src/llmxive` clean; if any fix touched code, re-run the entire gate (no partial re-verification). **Reuse audit (FR-015)**: confirm the change introduced no duplicate of `subject_key`, the reference validator, the `ClaimKind` taxonomy, or the per-kind fill gate — `claims/stage.py` and `claims/smooth.py` are the only new modules, and every other change extends a canonical module in place (grep for any copied helper).
- [X] T033 Real-call matrix (FR-016): run the quickstart B1-B6 + C scenarios with `LLMXIVE_REAL_TESTS=1` and free models; record outcomes.
- [X] T034 Documentation parity: confirm `state/claims/` is git-tracked and `state/grounding-cache/` stays gitignored (FR-013); update `notes/spec-015-review-status.md` and any claim-layer docstrings/READMEs touched, in the same change as the code.
- [X] T035 Update `specs/020-deterministic-claim-caching/checklists/requirements.md` Notes to record plan→tasks→analyze→implement completion + the SC→evidence mapping from quickstart.md.

---

## Dependencies & Execution Order

- **Setup (T001-T002)** → **Foundational (T003-T004)** → user stories.
- **US1 (T005-T013)** and **US2 (T014-T022)** are both P1 and **independent** of each other (US1 = stage gating + strip/smooth; US2 = freeze + placeholder). Either can be the first delivered increment; US1 is the designated MVP (immediate unblocker).
- Within US1: T008 needs T004; T010 needs T008+T009; T011 needs T004; T013 gates T007.
- Within US2: T019 needs T018; T021/T022 are the placeholder pair (T022 needs T021); T020 is independent within US2.
- **US3 (T023-T029)** depends on nothing in US1/US2 (doc edits) — can run anytime after Setup; T028 needs T023/T024.
- **Polish (T030-T035)** runs last; T031/T032 gate the commit; T033 is the real-call sign-off.
- **Same-file sequencing (not [P])**: T010↔T019 (both edit `claims/service.py`); T011↔T020 (both edit `fill/service.py`); T021 edits `claims/pointer.py`+`extract.py`. Run these serially.

## Parallel Execution Examples

- After T004: launch T005, T006, T007 together (distinct new test files), and T014, T015, T016, T017 (US2 tests) in parallel.
- US3 doc edits T023, T024, T025, T026, T027 are all `[P]` (distinct files) — do them in one batch.

## Implementation Strategy

- **MVP = US1**: deliver planning references-only + strip/smooth first; it alone removes the PROJ-552
  stall and the wasted hours. Ship/verify, then layer US2 (freeze) and US3 (prevention).
- **TDD**: each story's tests are written first and must fail before implementation.
- **No-regression is a release gate**: T031/T032 must be green and the real-call matrix (T033) must
  pass before the change lands on `main`.
