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
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools: Create `pyproject.toml` with black configuration (target-version = 'py311', line-length = 88) and `.ruff.toml` with ruff configuration files to enforce project coding standards.
- [X] T004 [P] Implement `code/load_data.py` to fetch public datasets (ASSISTments/OULAD via HuggingFace `datasets.load_dataset`) and verify presence of timestamped responses, error logs, hint requests, and interaction features. **MUST perform a flexible schema check**: instead of requiring exact column names, the task MUST check for the *presence of latency features* by looking for any of a set of semantically equivalent column names (e.g., 'response_timestamp', 'answer_start_timestamp', 'time_spent', 'response_time', 'latency', 'duration_ms') OR by attempting to derive latency from timestamp pairs (e.g., `answer_end - answer_start`). This flexibility handles real-world data variations while strictly verifying the *presence* of the required semantic features (latency, errors, hints) as mandated by FR-001. If no latency feature can be found or derived, the task MUST raise a clear error: "Schema Missing: Required latency features not found (checked: response_timestamp, answer_start_timestamp, time_spent, response_time, latency, duration_ms). Cannot proceed." If the schema supports derived features like `retrieval_latency` or `error_pattern`, extract and store them; otherwise, proceed with available features only. **Depends on T001**
- [X] T007 [P] [US1] Generate Golden Set Template: Create `data/processed/golden_set_template.csv` with columns `interaction_id`, `expert_load_score` (empty), and a README file with instructions for domain experts to label at least 50 interactions. **Depends on T001**
- [X] T007d [P] [US1] Document Golden Set Creation Process: Create a detailed guide in `docs/golden_set_creation.md` explaining how to generate the `golden_set_template.csv` and the process for domain experts to label interactions, clarifying that this is a manual process not automated by code. **Depends on T007**
- [X] T007e [P] [US1] Manual Golden Set Acquisition: **Human Action Required**. This task is a manual instruction step. Domain experts must label interactions from the template and save the result as `data/processed/golden_set.csv`. **This task does NOT produce an automated 'complete' flag for the pipeline.** The pipeline will check for the existence of `data/processed/golden_set.csv` in T007c. **Depends on T007**
- [X] T007c [P] [US1] Validate and Load Golden Set: Check for `data/processed/golden_set.csv`. **If it does not exist**, raise a hard HALT error with the exact message: "WAITING_FOR_HUMAN: Golden Set file (data/processed/golden_set.csv) is missing. Please complete the manual labeling process described in `docs/golden_set_creation.md` to acquire the Golden Set. The pipeline cannot proceed without external expert labels." **NO synthetic generation is permitted.** **NO fallback to public self-reports.** **NO fallback to NASA-TLX.** **Depends on T004, T007**
- [X] T008 [P] [US1] Validate Golden Set: Check for `data/processed/golden_set.csv` (populated version). Verify it contains ≥50 rows with valid `expert_load_score` values (0-100). If missing or invalid, halt with error: "Validation Data Missing: Golden Set with ≥50 expert labels not found. Cannot proceed with model training." **Depends on T007c**
- [X] T010 [P] [US1] Implement utility functions in `code/utils.py`: VIF calculation, Flesch-Kincaid scoring, Jaccard similarity, semantic similarity (using lightweight CPU-safe embeddings or cosine similarity on TF-IDF)
- [X] T011 [P] [US1] Setup environment configuration management and logging infrastructure in `code/config.py`: Implement `get_logger()` and `load_env()` functions.

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
- [X] T015 [US1] Implement full Gradient Boosting Regressor pipeline in `code/train_load_model.py`: Train `LightGBM` (with `tree_method='hist'`, `device='cpu'`). Read `data/processed/golden_set.csv` (validated in T008) to determine the validation file path. Validate against the Golden Set with target Pearson r ≥ 0.6. **If r < 0.6**, log the achieved metric and raise a ValueError to halt the pipeline. **If r ≥ 0.6**, save the model to `data/processed/load_model.pkl` (≤ 500 MB). **Depends on T014, T008**
- [X] T016 [P] [US1] Implement collinearity diagnostic (VIF ≤ 5) in `code/utils.py` and `code/train_load_model.py`; add logic to flag predictors and frame descriptive relationships if VIF > 5. **Depends on T014**
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
- [X] T022b [US2] Generate Moderate Tier: Generate the "Moderate" (baseline) tier for each instructional unit in `data/processed/instructional_units.csv` by preserving the original text or applying minimal stylistic normalization. Save to `data/explanation_tiers/moderate_tiers.csv`. **Depends on T022**
- [X] T023 [US2] Implement "Simple" tier generation: Read from `data/processed/instructional_units.csv` and write to `data/explanation_tiers/simple_tiers.csv`. **MUST ensure** the output Flesch-Kincaid difference vs moderate is ≥ 5 points AND Jaccard similarity ≥ 0.85. **Algorithm**: Implement an iterative adjustment loop with a maximum of 5 attempts. 
    1. Attempt generation with current parameters.
    2. Measure FK diff and Jaccard similarity.
    3. If constraints are met, save and stop.
    4. If constraints are not met, apply the next aggressiveness level (e.g., Reduce max sentence length significantly., increase jargon removal threshold).
    5. Repeat up to 5 times.
    6. If all 5 attempts fail, raise a ValueError with the best attempt's metrics and the specific constraints that failed.
    **Depends on T022b**
- [X] T024 [US2] Implement "Complex" tier generation: Read from `data/processed/instructional_units.csv` and write to `data/explanation_tiers/complex_tiers.csv`. **MUST ensure** the output Flesch-Kincaid difference vs moderate is ≥ 5 points AND Jaccard similarity ≥ 0.85. **Algorithm**: Implement an iterative adjustment loop with a maximum of 5 attempts.
    1. Attempt generation with current parameters.
    2. Measure FK diff and Jaccard similarity.
    3. If constraints are met, save and stop.
    4. If constraints are not met, apply the next complexity level (e.g., increase nested clause injection, add jargon from a predefined list).
    5. Repeat up to 5 times.
    6. If all 5 attempts fail, raise a ValueError with the best attempt's metrics and the specific constraints that failed.
    **Depends on T022b**
- [X] T025 [US2] Tier Validation & Tuning: Verify Flesch-Kincaid scoring for all tiers (simple, moderate, complex) and ensure monotonic progression (simple < moderate < complex) with ≥ 5 point differences. Also verify Jaccard similarity (≥ 0.85) and semantic similarity (≥ 0.90) against source text. If constraints are not met, trigger a re-generation loop with adjusted parameters (e.g., more aggressive simplification) up to a maximum iteration limit. Save final tiers and metadata to `data/explanation_tiers/` (CSV/JSON) ONLY if all constraints pass. **Depends on T022b, T023, T024**
- [X] T026 [US2] Document the tier generation process and validation results in `docs/research.md`.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Adaptive vs Static Complexity Simulation (Priority: P3)

**Goal**: Simulate learning sessions under adaptive vs static conditions and compute learning efficiency metrics with mixed-effects modeling.

**Independent Test**: Can be fully tested by running the simulation pipeline with N ≥ 40 historical sessions replayed, computing estimated learning efficiency metrics, and verifying the mixed-effects model reports Cohen's d and confidence intervals.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T027 [P] [US3] Contract test for simulation inputs/outputs in `tests/contract/test_simulation.py`
- [X] T028 [P] [US3] Integration test for mixed-effects model fitting and statistical reporting in `tests/integration/test_stats_integration.py`

### Implementation for User Story 3

- [X] T029 [P] [US3] Implement session replay logic in `code/simulate_sessions.py`: load N ≥ 40 historical sessions. **Depends on T004**
- [X] T030 [P] [US3] Implement "Static" condition simulation: always serve "Moderate" complexity tier. **This task does NOT depend on the Load Model (T018) or Hysteresis Controller (T032).** **Depends on T029, T025**
- [X] T032 [US3] Implement Hysteresis Controller: Define the controller logic with a **fixed baseline threshold** of 0.05 for the baseline simulation. **MUST depend on T015** to ensure the model is validated (r ≥ 0.6) before generating config. Output a config file `data/simulation_results/hysteresis_config.json` with schema: `{"baseline_threshold": 0.05, "hysteresis_band": "moderate"}`. **Note**: The sensitivity analysis sweep is handled separately in T033. **Depends on T015**
- [X] T031 [US3] Implement "Adaptive" condition simulation: select tier based on Load Estimate (US1) + Hysteresis Controller (from T032). **This task REQUIRES the Load Model (T018) and Hysteresis Controller (T032).** **Depends on T029, T025, T018, T032**
- [X] T033 [US3] Hysteresis Sensitivity Analysis: Sweep absolute diff over a range of specific threshold values and generate a CSV report at `data/simulation_results/hysteresis_sensitivity.csv`. **Schema**: columns `threshold` (float) and `inconsistency_rate` (float). **Formula**: `inconsistency_rate` = (count of tier switches) / (total transitions). If no tier switches occur, `inconsistency_rate` = 0.0. **This task requires the output of T031 (Adaptive Simulation) to calculate tier switches.** **Depends on T031, T032**
- [X] T034 [US3] Implement Learning Efficiency calculation: (Predicted Engagement × Gain) / Total Time. **Depends on T030, T031**
- [X] T035 [US3] Implement Mixed-Effects Model (LMM) in `code/analyze_results.py`: Fixed Effects (Condition, Load, Interaction), Random Effects (Session ID). **Depends on T034**
- [X] T036 [US3] Implement statistical reporting: Cohen's d, confidence intervals, p-value, family-wise error correction (Bonferroni if needed). **Depends on T035**
- [X] T037 [US3] Add explicit framing of findings as "ASSOCIATIONAL ONLY" (no causal claims) in all output reports. **Depends on T036**
- [X] T038 [US3] Add power limitation check: if N < 40, report limitation and defer effect-size claims. **Depends on T036**
- [X] T039a [US3] Implement Pipeline Wrapper: Create `code/run_pipeline.py` to orchestrate the full pipeline (Phases 1-5) and measure total wall-clock time. Assert ≤ 6h total execution time. **If execution exceeds 6h, raise a TimeoutError and log the specific stage where the timeout occurred.** **Depends on T001-T038**
- [X] T039b [US3] Update `code/analyze_results.py` to remove any isolated 6h asserts; rely on T039a for cumulative timing.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Revision & Research Review Address (Priority: P1)

**Goal**: Address documentation and non-code concerns from prior research-stage reviews (specifically the "illusion of competence" and "System 2 effort" critique).

### Tests for Review Address (OPTIONAL)

- [X] T040 [P] [Rev] Contract test for `code/analyze_results.py` ensuring "retrieval_latency" and "error_pattern" metrics are present in output schema if data exists

### Implementation for Review Address

- [X] T041 [Rev] Update `docs/research.md` and `README.md` to explicitly state the limitation: "Self-reported ease is not used as a primary metric due to the risk of the 'illusion of competence'. Primary metrics focus on behavioral proxies (latency, errors) validated against expert labels."
- [X] T042 [Rev] Update `code/analyze_results.py` report generation to explicitly frame "retrieval latency" and "error pattern" findings (if available from T004) as "ASSOCIATIONAL ONLY" indicators, ensuring no causal claims are made about "System 2 effort" (addressing FR-006).
- [X] T043 [Rev] Update `code/simulate_sessions.py` to ensure that the "Adaptive" condition does not automatically simplify text upon a single error, but rather uses the hysteresis thresholds to prevent premature simplification, preserving the "struggle" required for consolidation.
- [X] T044 [Rev] Update `docs/research.md` to include a dedicated section discussing the "Illusion of Competence" risk, explaining why the project avoids self-reported ease metrics and relies on the Golden Set + behavioral proxies instead.
- [X] T049 [Rev] Update `docs/research.md` with a "System 2 Preservation" section: Explicitly detail how the hysteresis controller and minimum struggle thresholds are designed to prevent the "illusion of competence" by ensuring students engage in effortful retrieval practice before complexity is reduced. Cite the specific logic in `code/simulate_sessions.py` (T043) and `code/analyze_results.py` (T037). **Depends on T037, T043**

**Note**: Tasks T045 and T046b were removed as they introduced metrics not defined in the Spec (FR-001 to FR-007) and constituted scope creep. The "System 2" critique is addressed by T043 (hysteresis logic) and T049 (documentation).

**Checkpoint**: All review concerns addressed

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T050 [P] Documentation updates in `docs/` and `README.md`
- [X] T051 Code cleanup and refactoring
- [X] T052 Performance optimization across all stories (ensure CPU-only compliance)
- [X] T053 [P] Run `quickstart.md` validation and end-to-end smoke test
- [X] T054 Security hardening (input validation, path safety)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-5)**: All depend on Foundational phase completion
 - **CRITICAL**: US-1 (Load Model) must pass validation (r ≥ 0.6) before US-3 (Simulation) can run. If validation fails, the pipeline halts.
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
- **CRITICAL**: Do not generate synthetic Golden Set data. If `data/processed/golden_set.csv` is missing, the pipeline MUST halt with the specified error. T007c now enforces this strict halt condition (WAITING_FOR_HUMAN if T007e is not complete).
- **CRITICAL**: All tasks must run on CPU-only GitHub Actions free-tier (limited cores, constrained RAM, no GPU).
- **CRITICAL**: Address the "illusion of competence" review by focusing on behavioral metrics (errors, latency) as inputs, while maintaining strict validation against external expert labels.
- **CRITICAL**: Tasks T040 and T041 from previous drafts were removed as they introduced unapproved metrics ('error retention', 'Risk flag') violating FR-006 and SC-002.
- **NEW**: Phase 6 tasks (T041-T049) explicitly address the "System 2 effortful work" critique by tracking retrieval latency, error patterns, and "struggle preservation" metrics (if available from T004) rather than just "ease of processing", framed strictly as ASSOCIATIONAL.
- **NEW**: T039a measures cumulative pipeline time to ensure SC-004 compliance and defines explicit timeout behavior.
- **NEW**: T033 handles the sensitivity analysis as a post-hoc step with specific threshold values {0.01, 0.05, 0.1}.
- **NEW**: T022b handles the generation of the 'Moderate' tier.
- **NEW**: T046b calculated 'Average Errors Per Session' as an associational metric, removed to prevent scope creep.
- **NEW**: T045 and T049 implement specific logic to prevent "over-simplification" and analyze "retrieval latency distributions" to ensure the system does not bypass the effortful work of consolidation, directly addressing the Kahneman review. T055 and T056 were removed to prevent scope creep.
- **FIX**: T032 now depends on T015 to ensure the model is validated before config generation.
- **FIX**: T015 now validates against the Golden Set only and halts if r < 0.6.
- **FIX**: T023/T024 removed prescriptive algorithmic constraints (iterative loop, max iterations) and replaced with a deterministic 3-attempt algorithm.
- **FIX**: T004 updated to support flexible column name matching for latency features.
- **FIX**: T009 removed as it documented a conflict rather than resolving it.
- **FIX**: T023a and T024a added to explicitly implement the iterative adjustment loops required for tier generation constraints.
- **FIX**: T007e removed as a hard dependency; T007c now handles the missing file state via runtime error.
- **FIX**: T023 and T024 marked complete and merged with T023a/T024a logic.
- **FIX**: T032 marked complete with explicit threshold values.
- **FIX**: T045/T046b updated to emphasize 'ASSOCIATIONAL ONLY' framing.
- **FIX**: T045 and T046b removed to prevent scope creep; System 2 concerns addressed by T043 and T049.
- **FIX**: T023a and T024a removed; logic merged into T023 and T024.
- **FIX**: T007e marked as manual instruction, not a blocking dependency.