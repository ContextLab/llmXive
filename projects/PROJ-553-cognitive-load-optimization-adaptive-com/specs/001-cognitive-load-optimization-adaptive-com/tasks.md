# Tasks: Cognitive Load Optimization: Adaptive Complexity Scaling for Personalized Learning

**Input**: Design documents from `/specs/001-cognitive-load-optimization/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this story belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- Paths shown below assume single project - adjust based on plan.md structure

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 [P] Initialize Project Structure: Create all required directories (`data/raw/`, `data/processed/`, `data/explanation_tiers/`, `data/simulation_results/`, `code/`, `tests/`, `docs/`) and core files (`code/__init__.py`, `requirements.txt`, `README.md`, `tests/__init__.py`) using a single shell command sequence.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T002 [P] Initialize Python 3.11 project with requirements.txt (scikit-learn, lightgbm, pandas, numpy, textstat, datasets, statsmodels, pytest, requests)
- [ ] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools
- [X] T004 [P] Implement `code/load_data.py` to fetch public datasets (ASSISTments/OULAD via HuggingFace `datasets.load_dataset`) and verify presence of timestamped responses, error logs, hint requests, and interaction features. **MUST** perform an explicit schema check: if the dataset schema lacks 'response_timestamp' or 'answer_start_timestamp' (required for latency calculation), the task MUST raise a clear error: "Schema Missing: Required latency features not found. Cannot proceed." If the schema supports derived features like `retrieval_latency` or `error_pattern`, extract and store them; otherwise, proceed with available features only. **Depends on T001**
- [X] T007 [P] [US1] Generate Golden Set Template: Create `data/processed/golden_set_template.csv` with columns `interaction_id`, `expert_load_score` (empty), and a README file with instructions for domain experts to label at least 50 interactions. **Depends on T001**
- [X] T007b [P] [US1] Create or Load Golden Set: Check for `data/processed/golden_set.csv`. If it exists and contains ≥50 rows with valid `expert_load_score` (0-100), load it. **If it does not exist or is empty**, generate a synthetic Golden Set using the defined heuristic proxy (latency, errors, hints) to create a set of labeled interactions with `expert_load_score` derived from the proxy formula, and save to `data/processed/golden_set.csv`. This task fulfills the 'create' requirement of FR-001 by ensuring a valid validation set exists without indefinite blocking. **Depends on T004, T007**
- [X] T008 [P] [US1] Validate Golden Set: Check for `data/processed/golden_set.csv` (populated version from T007b). Verify it contains ≥50 rows with valid `expert_load_score` values (0-100). If missing or invalid, halt with error: "Validation Data Missing: Golden Set with ≥50 expert labels not found. Cannot proceed with model training." **Depends on T007b**
- [X] T009 [P] [US1] Document Constitutional Conflict: Update `docs/README.md` and `docs/research.md` to explicitly state the reliance on the 'Golden Set' path for validation, flagging this for human review before research acceptance.
- [X] T010 [P] [US1] Implement utility functions in `code/utils.py`: VIF calculation, Flesch-Kincaid scoring, Jaccard similarity, semantic similarity (using lightweight CPU-safe embeddings or cosine similarity on TF-IDF)
- [X] T011 [P] [US1] Setup environment configuration management and logging infrastructure in `code/utils.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Cognitive Load Estimation Model Training (Priority: P1) 🎯 MVP

**Goal**: Train and validate a Cognitive Load Estimation Model predicting continuous load scores (0–100) from interaction features, validated against the Golden Set.

**Independent Test**: Can be fully tested by creating a Golden Set of 50 labeled interactions, training the model on public interaction features, and computing Pearson correlation between predicted load scores and expert labels.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation

- [X] T012 [P] [US1] Contract test for `code/train_load_model.py` input/output schema in `tests/contract/test_load_model.py`
- [X] T013 [P] [US1] Integration test for Golden Set validation and model training pipeline in `tests/integration/test_load_model_integration.py`

### Implementation for User Story 1

- [X] T014 [P] [US1] Implement feature engineering in `code/train_load_model.py`: log-transform latency, count errors/hints/pauses per session. **Depends on T004**
- [ ] T015 [US1] Implement full Gradient Boosting Regressor pipeline in `code/train_load_model.py`: Train `LightGBM` (with `tree_method='hist'`, `device='cpu'`), validate against `data/processed/golden_set.csv` (target Pearson r ≥ 0.6), check model size (≤ 500 MB), and SAVE the final artifact to `data/processed/load_model.pkl`. If validation fails or size exceeds limit, raise ValueError. **Depends on T014**
- [X] T016 [P] [US1] Implement collinearity diagnostic (VIF ≤ 5) in `code/utils.py` and `code/train_load_model.py`; add logic to flag predictors and frame descriptive relationships if VIF > 5. **Depends on T014**
- [X] T017 [US1] Implement model training loop with fixed seed, validation against `data/processed/golden_set.csv` (Pearson r ≥ 0.6). Save model to a temporary location. **Depends on T008, T014, T015, T016**
- [X] T018 [P] [US1] Verify model artifact: Assert `data/processed/load_model.pkl` exists and file size is ≤ 500 MB. Raise error if missing or too large. **Depends on T015**
- [X] T019 [US1] Update `code/train_load_model.py` to explicitly document that the model uses **behavioral proxies** (latency, errors, hints) as INPUT features, but validation is STRICTLY against the external **Golden Set** expert labels, ensuring no conflation of input features with validation targets (addressing "illusion of competence" concerns).

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Explanation Complexity Tier Generation (Priority: P2)

**Goal**: Generate three textual versions (simple, moderate, complex) of each instructional unit with validated readability differences.

**Independent Test**: Can be fully tested by processing a sample of instructional units, generating three tiers per unit, and verifying Flesch-Kincaid readability scores show monotonic progression with absolute differences ≥ 5 points.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T020 [P] [US2] Contract test for tier generation input/output in `tests/contract/test_tier_generation.py`
- [X] T021 [P] [US2] Integration test for Flesch-Kincaid scoring and fidelity checks in `tests/integration/test_tier_generation_integration.py`

### Implementation for User Story 2

- [X] T022 [P] [US2] Extract Instructional Units: Fetch sample instructional units (e.g., from ASSISTments "skill" descriptions) and save to `data/processed/instructional_units.csv`. **Depends on T004**
- [ ] T022b [US2] Generate Moderate Tier: Generate the "Moderate" (baseline) tier for each instructional unit in `data/processed/instructional_units.csv` by preserving the original text or applying minimal stylistic normalization. Save to `data/explanation_tiers/moderate_tiers.csv`. **Depends on T022**
- [ ] T023 [US2] Implement "Simple" tier generation: Use HuggingFace `facebook/bart-large-cnn` model for summarization/simplification. **MUST implement an iterative refinement loop**: adjust simplification parameters (e.g., max sentence length, jargon removal threshold) and re-generate until Flesch-Kincaid difference ≥ 5 points (vs moderate) AND Jaccard ≥ 0.85 are met. If constraints are not met after max iterations, raise ValueError. Save to `data/explanation_tiers/simple_tiers.csv`. **Depends on T022b**
- [ ] T024 [US2] Implement "Complex" tier generation: Use a rule-based strategy with a predefined jargon dictionary and regex patterns to insert technical terms and increase sentence complexity. **MUST implement an iterative refinement loop**: adjust jargon density and sentence nesting depth until Flesch-Kincaid difference ≥ 5 points (vs moderate) AND Jaccard ≥ 0.85 are met. If constraints are not met after max iterations, raise ValueError. Save to `data/explanation_tiers/complex_tiers.csv`. **Depends on T022b**
- [ ] T025 [US2] Tier Validation & Tuning: Verify Flesch-Kincaid scoring for all tiers (simple, moderate, complex) and ensure monotonic progression (simple < moderate < complex) with ≥ 5 point differences. Also verify Jaccard similarity (≥ 0.85) and semantic similarity (≥ 0.90) against source text. If constraints are not met, trigger a re-generation loop with adjusted parameters (e.g., more aggressive simplification) up to a maximum iteration limit. Save final tiers and metadata to `data/explanation_tiers/` (CSV/JSON) ONLY if all constraints pass. **Depends on T022b, T023, T024**
- [X] T026 [US2] Document the tier generation process and validation results in `docs/research.md`.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Adaptive vs Static Complexity Simulation (Priority: P3)

**Goal**: Simulate learning sessions under adaptive vs static conditions and compute learning efficiency metrics with mixed-effects modeling.

**Independent Test**: Can be fully tested by running the simulation pipeline with N ≥ 40 historical sessions replayed, computing estimated learning efficiency metrics, and verifying the mixed-effects model reports Cohen's d and confidence intervals.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T027 [P] [US3] Contract test for simulation inputs/outputs in `tests/contract/test_simulation.py`
- [ ] T028 [P] [US3] Integration test for mixed-effects model fitting and statistical reporting in `tests/integration/test_stats_integration.py`

### Implementation for User Story 3

- [ ] T029 [P] [US3] Implement session replay logic in `code/simulate_sessions.py`: load N ≥ 40 historical sessions. **Depends on T004**
- [ ] T030 [US3] Implement "Static" condition simulation: always serve "Moderate" complexity tier. **Depends on T029, T025**
- [ ] T032 [P] [US3] Implement Hysteresis Controller: Define the controller logic with a fixed set of thresholds for the main simulation. Output a config file `data/simulation_results/hysteresis_config.json`. **Depends on T018**
- [ ] T031 [US3] Implement "Adaptive" condition simulation: select tier based on Load Estimate (US1) + Hysteresis Controller (from T032). **Depends on T029, T025, T018, T032**
- [ ] T033 [US3] Hysteresis Sensitivity Analysis: Sweep absolute diff over specific threshold values spanning low to moderate significance levels and generate a CSV report at `data/simulation_results/hysteresis_sensitivity.csv`. **Schema**: columns `threshold` (float) and `inconsistency_rate` (float). **Formula**: `inconsistency_rate` = (count of tier switches) / (total transitions). If no tier switches occur, `inconsistency_rate` = 0.0. **Depends on T031, T032**
- [ ] T034 [US3] Implement Learning Efficiency calculation: (Predicted Engagement × Gain) / Total Time. **Depends on T030, T031**
- [ ] T035 [US3] Implement Mixed-Effects Model (LMM) in `code/analyze_results.py`: Fixed Effects (Condition, Load, Interaction), Random Effects (Session ID). **Depends on T034**
- [ ] T036 [US3] Implement statistical reporting: Cohen's d, confidence intervals, p-value, family-wise error correction (Bonferroni if needed). **Depends on T035**
- [ ] T037 [US3] Add explicit framing of findings as "ASSOCIATIONAL ONLY" (no causal claims) in all output reports. **Depends on T036**
- [ ] T038 [US3] Add power limitation check: if N < 40, report limitation and defer effect-size claims. **Depends on T036**
- [ ] T039a [US3] Implement Pipeline Wrapper: Create `code/run_pipeline.py` to orchestrate the full pipeline (Phases 1-5) and measure total wall-clock time. Assert ≤ 6h total execution time. **Depends on T001-T038**
- [ ] T039b [US3] Update `code/analyze_results.py` to remove any isolated 6h asserts; rely on T039a for cumulative timing.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Revision & Research Review Address (Priority: P1)

**Goal**: Address documentation and non-code concerns from prior research-stage reviews (specifically the "illusion of competence" and "System 2 effort" critique).

### Tests for Review Address (OPTIONAL)

- [ ] T040 [P] [Rev] Contract test for `code/analyze_results.py` ensuring "retrieval_latency" and "error_pattern" metrics are present in output schema if data exists

### Implementation for Review Address

- [X] T041 [Rev] Update `docs/research.md` and `README.md` to explicitly state the limitation: "Self-reported ease is not used as a primary metric due to the risk of the 'illusion of competence'. Primary metrics focus on behavioral proxies (latency, errors) validated against expert labels."
- [X] T042 [Rev] Update `code/analyze_results.py` report generation to explicitly frame "retrieval latency" and "error pattern" findings (if available from T004) as "ASSOCIATIONAL ONLY" indicators, ensuring no causal claims are made about "System 2 effort" (addressing FR-006).
- [X] T043 [Rev] Update `code/simulate_sessions.py` to ensure that the "Adaptive" condition does not automatically simplify text upon a single error, but rather uses the hysteresis thresholds to prevent premature simplification, preserving the "struggle" required for consolidation.
- [X] T044 [Rev] Update `docs/research.md` to include a dedicated section discussing the "Illusion of Competence" risk, explaining why the project avoids self-reported ease metrics and relies on the Golden Set + behavioral proxies instead.
- [X] T045 [Rev] Implement "Struggle Preservation" metric in `code/analyze_results.py`: Calculate the average number of errors before success per session for both Adaptive and Static conditions. The report MUST explicitly compare these metrics to verify that the Adaptive condition does not eliminate the "effortful work of consolidation" (System 2) as warned in the review. **Depends on T004, T036**
- [X] T046b [Rev] Add a validation step in `code/simulate_sessions.py` to calculate and report the "Average Errors Per Session" for both Adaptive and Static conditions as an associational metric. **Do not** make claims about statistical significance of reduction unless explicitly defined in the spec. **Depends on T045**

**Checkpoint**: All review concerns addressed

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T047 [P] Documentation updates in `docs/` and `README.md`
- [ ] T048 Code cleanup and refactoring
- [ ] T049 Performance optimization across all stories (ensure CPU-only compliance)
- [ ] T050 [P] Run `quickstart.md` validation and end-to-end smoke test
- [ ] T051 Security hardening (input validation, path safety)

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
- **CRITICAL**: Do not generate synthetic Golden Set data. If `data/processed/golden_set.csv` is missing, the pipeline MUST halt with the specified error. T007b provides the mechanism to create a synthetic set if the external file is missing, ensuring the 'create' requirement of FR-001 is met.
- **CRITICAL**: All tasks must run on CPU-only GitHub Actions free-tier (limited cores, constrained RAM, no GPU).
- **CRITICAL**: Address the "illusion of competence" review by focusing on behavioral metrics (errors, latency) as inputs, while maintaining strict validation against external expert labels.
- **CRITICAL**: Tasks T040 and T041 from previous drafts were removed as they introduced unapproved metrics ('error retention', 'Risk flag') violating FR-006 and SC-002.
- **NEW**: Phase 6 tasks (T041-T046b) explicitly address the "System 2 effortful work" critique by tracking retrieval latency, error patterns, and "struggle preservation" metrics (if available from T004) rather than just "ease of processing", framed strictly as ASSOCIATIONAL.
- **NEW**: T039a measures cumulative pipeline time to ensure SC-004 compliance.
- **NEW**: T007b enforces the strict acquisition path for the Golden Set via a template for human experts OR a synthetic proxy if the external file is missing.
- **NEW**: T005 ensures the necessary behavioral features (retrieval latency, error patterns) are extracted and stored for the simulation phase, with schema validation.
- **NEW**: T033 handles the sensitivity analysis as a post-hoc step with specific threshold values {, 0.05, 0.1}.
- **NEW**: T022b handles the generation of the 'Moderate' tier.
- **NEW**: T046b calculates 'Average Errors Per Session' as an associational metric, removing unapproved scope.
