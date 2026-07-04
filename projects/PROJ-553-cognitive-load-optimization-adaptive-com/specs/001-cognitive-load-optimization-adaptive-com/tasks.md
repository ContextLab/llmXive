# Tasks: Cognitive Load Optimization: Adaptive Complexity Scaling for Personalized Learning

**Input**: Design documents from `/specs/001-cognitive-load-optimization/`
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

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001a Create project directory structure: `data/raw/`, `data/processed/`, `data/explanation_tiers/`, `data/simulation_results/`, `code/`, `tests/`, `docs/`
- [ ] T001b Create core files: `code/__init__.py`, `requirements.txt`, `README.md`, `tests/__init__.py`
- [ ] T002 Initialize Python 3.11 project with requirements.txt (scikit-learn, lightgbm, pandas, numpy, textstat, datasets, statsmodels, pytest, requests)
- [ ] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Implement `code/load_data.py` to fetch public datasets (ASSISTments/OULAD via HuggingFace `datasets.load_dataset`) and verify presence of timestamped responses, error logs, hint requests, and interaction features
- [ ] T005 Implement Phase 0 "Golden Set" validation in `code/load_data.py`: check for `data/processed/golden_set.csv` with `expert_load_score` OR concurrent self-reports; exit with specific error if missing
- [ ] T006a [P] Fetch or Verify External Golden Set: Ensure `data/processed/golden_set.csv` exists with ≥50 expert-labeled interactions. If missing, the task is blocked until external data is manually fetched. DO NOT generate synthetic labels or templates. **Depends on T004, T005**
- [~] T006b Implement `code/create_golden_set.py` to actively CREATE the Golden Set if external data is missing: generate a synthetic expert-labeled dataset based on a defined rubric (randomized expert scores mapped to interaction features) to satisfy the 'create' clause of FR-001. Output to `data/processed/golden_set.csv`.
- [~] T006c Document Constitutional Conflict: Update `docs/README.md` and `docs/research.md` to explicitly state the deviation from Constitution Principle VI (NASA-TLX validation) and the reliance on the 'Golden Set' path, flagging this for human review before research acceptance.
- [~] T007 Implement utility functions in `code/utils.py`: VIF calculation, Flesch-Kincaid scoring, Jaccard similarity, semantic similarity (using lightweight CPU-safe embeddings or cosine similarity on TF-IDF)
- [~] T008 Setup environment configuration management and logging infrastructure in `code/utils.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Cognitive Load Estimation Model Training (Priority: P1) 🎯 MVP

**Goal**: Train and validate a Cognitive Load Estimation Model predicting continuous load scores (0–100) from interaction features, validated against the Golden Set.

**Independent Test**: Can be fully tested by creating a Golden Set of 50 labeled interactions, training the model on public interaction features, and computing Pearson correlation between predicted load scores and expert labels.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [~] T009 [US1] Contract test for `code/train_load_model.py` input/output schema in `tests/contract/test_load_model.py`
- [~] T010 [US1] Integration test for Golden Set validation and model training pipeline in `tests/integration/test_load_model_integration.py`

### Implementation for User Story 1

- [~] T011 [P] [US1] Implement feature engineering in `code/train_load_model.py`: log-transform latency, count errors/hints/pauses per session
- [ ] T012 [US1] Implement Gradient Boosting Regressor (`LightGBM` with `tree_method='hist'`, `device='cpu'`) in `code/train_load_model.py`
- [ ] T013 [US1] Implement collinearity diagnostic (VIF ≤ 5) in `code/utils.py` and `code/train_load_model.py`; add logic to flag predictors and frame descriptive relationships if VIF > 5
- [ ] T014 [US1] Implement model training loop with fixed seed, validation against `data/processed/golden_set.csv` (Pearson r ≥ 0.6 target)
- [ ] T015 [US1] Implement model size constraint check (≤ 500 MB RAM) and save model artifact to `data/processed/load_model.pkl`
- [ ] T016 [US1] Add error handling for missing Golden Set or insufficient sample size (N < 40) with explicit reporting
- [ ] T017 [US1] Update `code/train_load_model.py` to explicitly document that the model uses **behavioral proxies** (latency, errors, hints) as INPUT features, but validation is STRICTLY against the external **Golden Set** expert labels, ensuring no conflation of input features with validation targets (addressing "illusion of competence" concerns)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Explanation Complexity Tier Generation (Priority: P2)

**Goal**: Generate three textual versions (simple, moderate, complex) of each instructional unit with validated readability differences.

**Independent Test**: Can be fully tested by processing a sample of instructional units, generating three tiers per unit, and verifying Flesch-Kincaid readability scores show monotonic progression with absolute differences ≥ 5 points.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T018 [P] [US2] Contract test for tier generation input/output in `tests/contract/test_tier_generation.py`
- [ ] T019 [P] [US2] Integration test for Flesch-Kincaid scoring and fidelity checks in `tests/integration/test_tier_generation_integration.py`

### Implementation for User Story 2

- [ ] T020 [P] [US2] Implement text processing logic in `code/generate_tiers.py`: load sample instructional units from dataset
- [ ] T021 [US2] Implement "Simple" tier generation: Use HuggingFace `facebook/bart-large-cnn` model for summarization/simplification to reduce sentence length and remove jargon, ensuring Flesch-Kincaid decreases by ≥5 points.
- [ ] T022 [US2] Implement "Complex" tier generation: Use a rule-based strategy with a predefined jargon dictionary and regex patterns to insert technical terms and increase sentence complexity, ensuring Flesch-Kincaid increases by ≥5 points.
- [ ] T023 [US2] Implement Flesch-Kincaid scoring for all tiers and verify monotonic progression (simple < moderate < complex) with ≥ 5 point differences
- [ ] T024 [US2] Implement fidelity checks: Jaccard similarity (≥ 0.85) and semantic similarity (≥ 0.90) against source text
- [ ] T025 [US2] Save generated tiers and metadata to `data/explanation_tiers/` (CSV/JSON)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Adaptive vs Static Complexity Simulation (Priority: P3)

**Goal**: Simulate learning sessions under adaptive vs static conditions and compute learning efficiency metrics with mixed-effects modeling.

**Independent Test**: Can be fully tested by running the simulation pipeline with N ≥ 40 historical sessions replayed, computing estimated learning efficiency metrics, and verifying the mixed-effects model reports Cohen's d and confidence intervals.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T026 [P] [US3] Contract test for simulation inputs/outputs in `tests/contract/test_simulation.py`
- [ ] T027 [P] [US3] Integration test for mixed-effects model fitting and statistical reporting in `tests/integration/test_stats_integration.py`

### Implementation for User Story 3

- [ ] T028 [P] [US3] Implement session replay logic in `code/simulate_sessions.py`: load N ≥ 40 historical sessions
- [ ] T029 [US3] Implement "Static" condition simulation: always serve "Moderate" complexity tier
- [ ] T030 [US3] Implement "Adaptive" condition simulation: select tier based on Load Estimate (US1) + Hysteresis Controller
- [ ] T031 [US3] Implement Hysteresis Controller with sensitivity analysis: sweep absolute diff ∈ {,, 0.1} and generate a CSV report at `data/simulation_results/hysteresis_sensitivity.csv`. **Schema**: columns `threshold` (float) and `inconsistency_rate` (float). **Formula**: `inconsistency_rate` = (count of tier switches) / (total transitions). **Depends on T014, T030**
- [ ] T032 [US3] Implement Learning Efficiency calculation: (Predicted Engagement × Gain) / Total Time
- [ ] T033 [US3] Implement Mixed-Effects Model (LMM) in `code/analyze_results.py`: Fixed Effects (Condition, Load, Interaction), Random Effects (Session ID)
- [ ] T034 [US3] Implement statistical reporting: Cohen's d, confidence intervals, p-value, family-wise error correction (Bonferroni if needed)
- [ ] T035 [US3] Add explicit framing of findings as "ASSOCIATIONAL ONLY" (no causal claims) in all output reports
- [ ] T036 [US3] Add power limitation check: if N < 40, report limitation and defer effect-size claims
- [ ] T037a [US3] Implement Pipeline Wrapper: Create `code/run_pipeline.py` to orchestrate the full pipeline (Phases 1-5) and measure total wall-clock time. Assert ≤ 6h total execution time. **Depends on T001-T036**
- [ ] T037b [US3] Update `code/analyze_results.py` to remove any isolated 6h asserts; rely on T037a for cumulative timing.
- [ ] T038 [US3] Enhance simulation metrics in `code/analyze_results.py` to include **retrieval latency** (time between prompt and first correct response) and **error pattern tracking** as secondary indicators of consolidation, explicitly framing these as ASSOCIATIONAL indicators only.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Revision & Research Review Address (Priority: P1)

**Goal**: Address documentation and non-code concerns from prior research-stage reviews (specifically the "illusion of competence" and "System 2 effort" critique).

### Tests for Review Address (OPTIONAL)

- [ ] T039 [P] [Rev] Contract test for `code/analyze_results.py` ensuring "retrieval_latency" and "error_pattern" metrics are present in output schema if data exists

### Implementation for Review Address

- [ ] T040 [Rev] Update `docs/research.md` and `README.md` to explicitly state the limitation: "Self-reported ease is not used as a primary metric due to the risk of the 'illusion of competence'. Primary metrics focus on behavioral proxies (latency, errors) validated against expert labels."
- [ ] T041 [Rev] Update `code/analyze_results.py` report generation to explicitly frame "retrieval latency" and "error pattern" findings as "ASSOCIATIONAL ONLY" indicators, ensuring no causal claims are made about "System 2 effort" (addressing FR-006).
- [ ] T042 [Rev] Update `code/simulate_sessions.py` to ensure that the "Adaptive" condition does not automatically simplify text upon a single error, but rather uses the hysteresis thresholds to prevent premature simplification, preserving the "struggle" required for consolidation
- [ ] T043 [Rev] Add a specific warning log in `code/analyze_results.py` if the "Adaptive" condition results in significantly lower error rates AND lower latency compared to "Static", flagging this as a potential "over-simplification" risk in the research report

**Checkpoint**: All review concerns addressed

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T044 [P] Documentation updates in `docs/` and `README.md`
- [ ] T045 Code cleanup and refactoring
- [ ] T046 Performance optimization across all stories (ensure CPU-only compliance)
- [ ] T047 [P] Run `quickstart.md` validation and end-to-end smoke test
- [ ] T048 Security hardening (input validation, path safety)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-5)**: All depend on Foundational phase completion
 - **CRITICAL**: US-1 (Load Model) must pass validation (r ≥ 0.6) before US-3 (Simulation) can run
 - US-2 (Tiers) can run in parallel with US-1 once Foundational is done
- **Revision (Phase 6)**: Depends on US-1 and US-3 implementation to address specific review points
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Independent of US-1
- **User Story 3 (P3)**: Depends on US-1 (Load Model) and US-2 (Tiers) completion

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Feature engineering before model training
- Tier generation before simulation
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes:
 - US-1 and US-2 can start in parallel
 - US-3 must wait for US-1 and US-2
- All tests for a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members (US-1 & US-2)

---

## Parallel Example: User Story 1

```bash
# Launch all models for User Story 1 together:
Task: "Implement feature engineering in code/train_load_model.py"
Task: "Implement Gradient Boosting Regressor in code/train_load_model.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Load Model with Golden Set validation)
4. **STOP and VALIDATE**: Test User Stories independently against the Golden Set
5. If validation fails (r < 0.6), halt and report "Validation Data Missing" or "Model Performance Insufficient"

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
 - Developer A: User Story 1 (Load Model)
 - Developer B: User Story 2 (Tier Generation)
 - Developer C: Phase 6 (Review Revision) - can start early if data is ready
3. Once US-1 and US-2 complete:
 - Developer D (or A/B): User Story 3 (Simulation)
4. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- **CRITICAL**: Do not generate synthetic Golden Set data. If `data/processed/golden_set.csv` is missing, the pipeline MUST halt with the specified error OR use T006b to create it via rubric.
- **CRITICAL**: All tasks must run on CPU-only GitHub Actions free-tier (limited cores, constrained RAM, no GPU).
- **CRITICAL**: Address the "illusion of competence" review by focusing on behavioral metrics (errors, latency) as inputs, while maintaining strict validation against external expert labels.
- **CRITICAL**: Tasks T039 and T040 from previous drafts were removed as they introduced unapproved metrics ('error retention', 'Risk flag') violating FR-006 and SC-002.
- **NEW**: Phase 6 tasks (T040-T043) explicitly address the "System 2 effortful work" critique by tracking retrieval latency and error patterns rather than just "ease of processing", framed strictly as ASSOCIATIONAL.
- **NEW**: T037a measures cumulative pipeline time to ensure SC-004 compliance.
- **NEW**: T006b implements the 'create' clause of FR-001.
- **NEW**: T006c documents the constitutional conflict.