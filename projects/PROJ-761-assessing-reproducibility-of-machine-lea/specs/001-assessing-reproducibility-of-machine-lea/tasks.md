# Tasks: Assessing Reproducibility of Machine‑Learned Reaction Yield Models

**Input**: Design documents from `/specs/PROJ-761-01-reproducibility/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- Paths shown below assume single project - adjust based on plan.md structure

<!--
 ============================================================================
 IMPORTANT: The tasks below are SAMPLE TASKS for illustration purposes only.

 The /speckit-tasks command MUST replace these with actual tasks based on:
 - User stories from spec.md (with their priorities P1, P2, P3...)
 - Feature requirements from plan.md
 - Entities from data-model.md
 - Endpoints from contracts/

 Tasks MUST be organized by user story so each story can be:
 - Implemented independently
 - Tested independently
 - Delivered as an MVP increment

 DO NOT keep these sample tasks in the generated tasks.md file.
 ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure per implementation plan by executing: `mkdir -p data/raw data/processed code tests artifacts/logs artifacts/plots artifacts/reports contracts`
- [ ] T002 Initialize Python 3.11 project with `requirements.txt` containing exact pinned versions: `torch==2.2.0+cpu`, `scikit-learn==1.5.0`, `rdkit==2024.3.1`, `statsmodels==0.14.1`, `pandas==2.2.0`, `numpy==1.26.0`, `matplotlib==3.8.0`, `pyyaml==6.0.1`, `requests==2.31.0`. **Note**: Installation requires `pip install -r requirements.txt --extra-index-url.
- [ ] T003a [P] Create `pyproject.toml` with `[tool.black]` and `[tool.ruff]` sections configuring line length 88, target-version py311, and specific linting rules (E, F, W, I).
- [ ] T003b [P] Configure linting (ruff) and formatting (black) tools by running initial checks on the empty project structure to verify configuration validity.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Create `Dockerfile` with Python 3.11, CPU-only PyTorch 2.2, scikit-learn 1.5, RDKit; enforce no GPU flags
- [ ] T005 [P] Implement `code/ingest.py` for manifest validation and data fetching (including supplementary material extraction) referencing `contracts/PaperManifest.json` for schema validation. Extraction logic must rely on defined patterns in the manifest or standard supplementary file naming conventions (e.g., `*_supp.csv`, `*_data.parquet`).
- [~] T006 [P] Setup `contracts/` directory and generate JSON Schemas for `PaperManifest`, `ReproResult`, `StatSummary`
- [X] T007 Create `code/metrics.py` with functions for MAE, R², Spearman ρ, and the Deviation Index (S) calculation (FR-009) using the exact formula: `S = 1 – (|ΔMAE|/(|MAE_ref|+ε) + |ΔR2|/(|R2_ref|+ε) + |Δρ|/(|ρ_ref|+ε))/3` where ε = 1e-6. (See spec.md Requirements FR-009)
- [X] T008 Configure environment logging in `code/main.py` to capture Python version, library versions, OS, and Docker hash (FR-012)
- [X] T009 Implement `data/manifest.yaml` loader and validator to ensure DOI, repo URL, dataset name, and reported metrics are present (FR-001)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Reproduce Reported Metrics (Priority: P1) 🎯 MVP

**Goal**: For each paper, retrieve data, re-implement the model on CPU, and compute reproduced metrics with deviations.

**Independent Test**: Run the pipeline on a single target paper with known results; verify `artifacts/reports/repro_results.json` contains MAE, R², ρ, deviations, and the calculated reproducibility score S.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation.
> **Dependency**: These tests require T007 (metrics.py) to be implemented first.

- [X] T010 [P] [US1] Unit test for Deviation Index calculation in `tests/unit/test_metrics.py` (Depends on T007)
- [X] T011 [P] [US1] Unit test for metric calculation (MAE, R², Spearman) in `tests/unit/test_metrics.py` (Depends on T007)
- [ ] T012 [P] [US1] Integration test for data ingestion and validation in `tests/integration/test_ingest.py`

### Implementation for User Story 1

- [ ] T013 [P] [US1] Implement `code/model_runner.py` to load data from `data/processed/`, apply preprocessing, train model (CPU, seed 42 or reported), and evaluate. Output JSON to `artifacts/reports/repro_results.json`. Include logic to substitute models exceeding 1M parameters with a baseline and log "Model Substitution/Unavailable" (FR-004, FR-005). **Dependency**: Requires T006 (Schema) to be complete.
- [ ] T014 [US1] Implement logic in `code/model_runner.py` to handle missing seeds (default 42) and flag in results (US-1 Scenario 2)
- [ ] T015 [US1] Implement logic in `code/ingest.py` to verify dataset variables (SMILES, yield, covariates) against the manifest schema. If missing, generate a detailed flag in the results log for the specific missing variables and record in `ReproResult` as "Data Unavailable" (FR-003, Plan Phase 0).
- [ ] T016 [US1] Implement `code/model_runner.py` to enforce the ≤1M parameter limit; log "Model Substitution/Unavailable" if exceeded (Plan Phase 2)
- [ ] T017 [US1] Implement sensitivity analysis in `code/model_runner.py` to sweep seeds `{42, 123, 999}`, compute `metric_std` for each metric, and report the **maximum standard deviation** observed. Add `metric_std` and `max_metric_std` fields to the `ReproResult` JSON object (FR-010, SC-003). **Dependency**: Requires T006 (Schema) and T007 (Metrics).
- [ ] T018 [US1] Implement `code/main.py` to aggregate individual `ReproResult` objects into `artifacts/reports/repro_results.json` containing deviations and score S (FR-005, FR-009)
- [ ] T019 [US1] Add logging in `code/main.py` to record environment details (Python, libs, OS, Docker hash) to `artifacts/logs/env.log` (FR-012)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Quantify Agreement Across Studies (Priority: P2)

**Goal**: Perform statistical meta-analysis (paired t-test, mixed-effects model, Bland-Altman) on the aggregated results.

**Independent Test**: Run the analysis module on a mock dataset of multiple papers; verify `artifacts/reports/stat_summary.json` contains t-test p-values, mixed-effects model variance components, and that Bland-Altman PNGs are saved.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T022 [P] [US2] Unit test for paired t-test implementation in `tests/unit/test_stats.py`
- [ ] T023 [P] [US2] Unit test for mixed-effects model implementation in `tests/unit/test_stats.py`
- [ ] T024 [P] [US2] Integration test for Bland-Altman plot generation in `tests/integration/test_stats.py`

### Implementation for User Story 2

- [ ] T025 [P] [US2] Implement `code/stats.py` to run paired t-tests for each metric (MAE, R², ρ) unconditionally, applying Bonferroni correction for family-wise error control. **Primary Test**: This task satisfies Spec SC-002 (paired t-test). (FR-006)
- [ ] T026 [US2] Implement `code/stats.py` with TOST (Two One-Sided Tests) for MAE, R², ρ against tolerance delta (use delta=0.1 as defined in plan.md) for supplementary equivalence analysis, including Bonferroni correction. **Supplementary**: This task satisfies Plan Phase 3 but is secondary to T025 for Spec SC-002. (FR-006, Plan Phase 3)
- [ ] T027 [US2] Implement `code/stats.py` with a Linear Mixed-Effects Model (LME) with random intercepts for paper. **Note**: Spec FR-008 mandates fixed effects for (i) preprocessing script version, (ii) library version, and (iii) random-seed choice. However, Plan Phase 3 explicitly forbids modeling these as fixed effects because the environment is constant. This task implements the Plan's methodology (random intercepts only) and flags the Spec FR-008 deviation as a known limitation requiring a spec update. Report variance components as JSON.
- [ ] T028 [US2] Implement `code/stats.py` to generate Bland-Altman plots for each metric and save as `{metric}_bland_altman.png` in `artifacts/plots/` (FR-007)
- [ ] T029 [US2] Implement `code/stats.py` to compute heterogeneity (I²) and pooled effect size from the LME results, outputting to `artifacts/reports/stat_summary.json` (Plan Phase 3)
- [ ] T030 [US2] Implement logic to compile a qualitative failure log of excluded papers (model substitution, data gaps) and ensure these are explicitly flagged in the results log as per FR-003 (Plan Phase 3)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Generate Community Guidelines (Priority: P3)

**Goal**: Synthesize a Markdown checklist of best-practice recommendations based on failure modes and statistical findings.

**Independent Test**: Run the guideline generator; verify `artifacts/reports/reproducibility_checklist.md` contains ≥5 items, each citing a guideline and referencing a specific failure mode.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T032 [P] [US3] Unit test for guideline template rendering in `tests/unit/test_guidelines.py`
- [ ] T033 [P] [US3] Integration test for checklist generation with mock failure logs in `tests/integration/test_guidelines.py`

### Implementation for User Story 3

- [ ] T034 [P] [US3] Implement `code/guidelines.py` to parse `artifacts/reports/stat_summary.json` and the qualitative failure log
- [ ] T035 [US3] Implement logic in `code/guidelines.py` to map failure modes (missing seeds, covariate gaps, version mismatches) to specific best-practice recommendations
- [ ] T036 [US3] Implement `code/guidelines.py` to generate `artifacts/reports/reproducibility_checklist.md` with ≥5 numbered items, each citing a published guideline and referencing a failure mode (FR-011)
- [ ] T037 [US3] Add logic to ensure checklist items are actionable (e.g., "Report random seed", "Version-pin libraries", "Specify reaction conditions") (US-3 Scenario 1)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T039 [P] Documentation updates in `docs/` (README, quickstart): Update README.md with installation instructions and quickstart.md with example usage
- [ ] T042 [P] Additional unit tests (if requested) in `tests/unit/`
- [ ] T043 Security hardening (dependency scanning)
- [ ] T044 Run quickstart.md validation

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Contract test for [endpoint] in tests/contract/test_[name].py"
Task: "Integration test for [user journey] in tests/integration/test_[name].py"

# Launch all models for User Story 1 together:
Task: "Create [Entity1] model in src/models/[entity1].py"
Task: "Create [Entity2] model in src/models/[entity2].py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1
 - Developer B: User Story 2
 - Developer C: User Story 3
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Removed Tasks**: T020, T021 (Experimental metadata extraction - unapproved scope), T031 (Fixed effect for missing flags - contradicts plan), T040, T041 (Vague polish tasks).
- **Spec/Plan Conflict**: Task T027 addresses the conflict between Spec FR-008 (fixed effects) and Plan Phase 3 (constant environment) by implementing the Plan's methodology and flagging the deviation.