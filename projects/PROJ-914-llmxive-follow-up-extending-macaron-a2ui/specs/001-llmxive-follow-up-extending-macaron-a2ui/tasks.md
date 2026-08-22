# Tasks: llmXive follow-up: extending "Macaron-A2UI: A Model for Generative UI in Personal Agents"

**Input**: Design documents from `/specs/001-llmxive-a2ui-latency-study/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each user story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `tests/` at repository root
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

- [X] T001 Create project structure per `plan.md` (`code/`, `tests/`, `data/`, `specs/`)
- [X] T002 Initialize Python 3.11 project with `requirements.txt` (transformers[cpu-only], scikit-learn, pandas, numpy, matplotlib, seaborn, pyyaml, pytest, statsmodels)
- [X] T003 [P] Create `.ruff.toml` with rules E, W, F and max-line-length 88 (verification: `ruff check code/` passes; content must include [E, W, F] rules and max-line-length 88)
- [X] T004 [P] Create `.gitignore` excluding `data/`, `__pycache__/`, `*.pyc`, `*.log` (verification: `git status` shows no ignored files; content must be minimal and valid)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T005 Implement `code/config.py` for seeds, paths, and constants (including `RANDOM_SEED=42`)
- [X] T006 [P] Implement `code/utils/versioning.py` to compute SHA-256 hashes of `data/` and `code/` and update `state/` YAML (Constitution Principle V)
- [X] T007 [P] Implement `code/utils/logging.py` for structured JSON logging of experiment runs
- [X] T008 Create base data models/entities (`InteractionTurn`, `RoutingDecision`, `SimulationRun`) in `code/data/models.py`
- [X] T009 [P] [US1] Generate contract schemas in `specs/001-llmxive-a2ui-latency-study/contracts/` (`simulation_input.schema.yaml`, `simulation_output.schema.yaml`) using a script or `jsonschema` library; verify with T010 (no manual setup)
- [X] T023 [P] [US2] Implement `code/simulation/rubric.py` to derive and implement the "Human-Agent Alignment" scoring function: `score = 0.4 * intent_match + 0.3 * (1 - latency_penalty) + 0.3 * ui_completeness` (FR-005, SC-002); **must include latency_penalty**; **Moved to Phase 2 to ensure availability for T037 in Phase 5**
- [X] T023b [P] [US2] Implement `code/simulation/rubric.py` to explicitly calculate `latency_penalty` as `1 - min(1, latency / 2.0)` (SC-002); **explicitly implement the latency term to align with SC-002**; **Depends on: T023**

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Intent Annotation (Priority: P1) 🎯 MVP

**Goal**: Ingest the Macaron-A2UI dataset and provide an interface to label N=500 interaction turns as "High-Confidence" or "Ambiguous" to create ground truth. Additionally, create a separate N=50 human-annotated hold-out set for rubric validation.

**Independent Test**: A CSV file exists containing N=500 rows with columns `query`, `ground_truth_intent`, `complexity_score`, validated by a script checking ≥95% coverage and no missing labels. A separate N=50 hold-out set exists for rubric validation.

### Implementation for User Story 1

- [X] T012 [US1] Implement `code/data/ingest.py` with `load_dataset` (Hugging Face) to fetch raw A2UI-Bench data; **no training logic included**; outputs raw CSV
- [X] T012b-CLI [US1] Implement `code/data/annotate_cli.py` as a **CLI tool with --input and --output flags** to provide the manual annotation interface for researchers to label N=500 turns (FR-001); **uses a text-based interactive loop**; **outputs labeled CSV**
- [X] T013 [US1] Implement validation script `code/data/validate_annotation.py` to check ≥95% coverage and no missing labels in the N=500 dataset (US-1 Independent Test)
- [X] T014 [US1] Add error handling to `code/data/ingest.py` to ensure real data fetch fails loudly (no synthetic fallback) per Data Hygiene rules
- [X] T015 [US1] Implement `code/data/annotate_holdout.py` to create the **N=50 human-annotated hold-out set** for rubric validation (FR-008); **script to format raw data for manual review**; **data creation only, no validation logic**
- [X] T015b [US1] Verify N=50 hold-out set format and completeness (requires manual annotation step to be performed externally or simulated with placeholder data for testing; validates format of file assuming it exists)
- [X] T015d [US1] **Human Annotation Step**: Execute manual annotation of N=50 hold-out set using `code/data/annotate_cli.py` to produce `data/human_scores.json`; **MUST be performed by a human researcher**; **Output: `data/human_scores.json`**
- [X] T015d-Gen [US1] **CI Placeholder Generation**: Implement `code/data/generate_placeholder_scores.py` to generate a deterministic `data/human_scores.json` for CI testing only; **Explicitly marked as CI-only, not for FR-008 validation**; **Output schema: list of objects with keys 'query', 'score', 'label'**
- [X] T015d-Load [US1] **Load Committed Annotations**: Implement `code/data/load_human_scores.py` to load `data/human_scores.json` if committed; **fails loudly if file missing and CI placeholder not generated**; **Depends on: T015d (Human) OR T015d-Gen (CI Placeholder)**
- [X] T015e [US1] **CI Placeholder Generation**: Implement `code/data/generate_placeholder_scores.py` to generate a dummy `data/human_scores.json` for CI testing only; **Explicitly marked as CI-only, not for FR-008 validation**; **Output schema: list of objects with keys 'query', 'score', 'label'**

### Tests for User Story 1

- [X] T010 [P] [US1] Contract test for data schema validation in `tests/contract/test_data_schemas.py`
- [X] T011 [P] [US1] Unit test for annotation script logic in `tests/unit/test_data_ingest.py`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently.

---

## Pre-Phase 4: Manual Gate (Blocking Prerequisite for US2)

**Purpose**: Tasks that require external human input or manual verification before Phase 4 can proceed.

- [X] T015c [US1] Verify existence and validity of N=50 hold-out set before simulation (blocking prerequisite for US2). **MUST be completed by human or CI placeholder before Phase 4 starts.** **Depends on: T015d (Human) OR T015d-Gen (CI Placeholder)**; **Verification Script: `code/data/validate_holdout.py`**; **Target File: `data/human_scores.json`**

---

## Phase 4: User Story 2 - Hybrid Routing and Latency Simulation (Priority: P2)

**Goal**: Implement a routing pipeline (DistilBERT CPU classifier) and simulation engine with latency injection, user patience modeling, and fallback generation.

**Independent Test**: A simulation run processes a batch, logs routing decisions, generation time, injected latency, and abandonment events, producing a log where `total_time = gen_time + latency` (or `abandonment_time`).

### Implementation for User Story 2

- [X] T020 [US2] Implement `code/models/router.py` with DistilBERT (quantized) for intent classification (High-Confidence vs. Ambiguous)
- [X] T020b [US2] **Verify CPU-Optimization**: Implement and run a script to verify the router model is 8-bit quantized and CPU-optimized (FR-002); **Explicit verification of quantization state**
- [X] T021 [US2] Implement `code/models/fallback.py` for the deterministic rule-based generator with ontology matching
- [X] T021b [US2] **Implement Quantized Generative Model**: Implement loading and inference logic for quantized DistilGPT2 model for the generative path (Plan Constraint); **Explicit implementation step for quantized model**
- [X] T022 [US2] Implement `code/simulation/patience.py` with `sample_patience()` function modeling exponential decay (mean=2s) for user abandonment (FR-003); **explicitly define rate parameter lambda = 1/mean and apply random seed**
- [X] T024a [US2] Implement simulation runner `code/simulation/runner.py` with latency injection (sleep/delay) and dependency on **T022** for patience modeling
- [X] T024b [US2] Implement density iteration logic in `code/simulation/runner.py` to iterate through explicit density levels **{1, 3, 5, 10}** for deterministic fallback (FR-004, Constitution Principle VII); **Explicitly handle borderline confidence scores (if score == threshold, route to Ambiguous)**
- [X] T024c [US2] Implement logging of `ui_element_count` and validation/assertion for density levels in `code/simulation/runner.py`
- [X] T026 [US2] Implement logic in `code/simulation/runner.py` to handle "Ambiguous" queries: invoke fallback, log "no-match" if no ontology entry, return minimal UI (element)
- [X] T020 [US2] Implement `code/models/router.py` with DistilBERT (quantized) for intent classification (High-Confidence vs. Ambiguous)
- [X] T019 [US2] Implement training script `code/models/train_router.py` to train DistilBERT on labeled CSV from T013; **Depends on: T013, T020**; **Must save model to `code/models/router_model/`** (Removed "no model file generated yet")
- [X] T019b-Run [US2] Execute training script from T019 on labeled CSV; save model to `code/models/router_model/`; **Depends on: T015c**
- [X] T019b-Verify [US2] Verify model file exists with SHA-256 hash; **Depends on: T019b-Run**
- [X] T027 [US2] Implement `code/simulation/metrics.py` to calculate alignment scores using the rubric from **T023**; output must include `ui_element_count`; **includes validation to ensure ui_element_count is logged**
- [X] T027b [US2] Implement validation in `code/simulation/metrics.py` to explicitly verify the calculation of `ui_completeness` derived from `ui_element_count` in the rubric scoring logic
- [X] T033 [US2] Implement sensitivity analysis in `code/analysis/sensitivity.py` to sweep router confidence cutoffs across a **concrete set {0.6, 0.7, 0.8}** and report inconsistency rates. (FR-007, SC-005)
- [X] T033b [US2] **Measure Robustness**: Implement logic to measure and report the variance in inconsistency rates across swept thresholds as the router robustness metric (SC-005)
- [X] T033a [US2] Run sensitivity analysis from T033 on the trained model from T019b-Verify; generate inconsistency rate report

### Tests for User Story 2

- [X] T016 [P] [US2] Unit test for router confidence scoring in `tests/unit/test_router.py`
- [X] T017 [P] [US2] Unit test for patience model (exponential decay) in `tests/unit/test_patience_model.py`
- [X] T018 [P] [US2] Integration test for simulation runner in `tests/integration/test_simulation.py`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Alignment Scoring and Pareto Analysis (Priority: P3)

**Goal**: Calculate metrics, perform statistical tests (FDR/Bonferroni), and generate Pareto frontier plots to identify the latency threshold for fidelity degradation. The alignment score calculation includes `intent_match`, `latency_penalty`, and `ui_completeness`.

**Independent Test**: A report is generated with a Pareto plot and a table of alignment scores per density/latency, identifying the threshold via non-overlapping 95% CIs (p < 0.05).

### Implementation for User Story 3

- [X] T032 [US3] Implement `code/analysis/stats.py` for **Benjamini-Hochberg FDR** multiple-comparison correction on alignment scores (FR-006, SC-004)
- [X] T032a [US3] Implement configurable correction method in `code/analysis/stats.py` to support both FDR and Bonferroni (satisfying spec flexibility)
- [X] T034a [US3] Generate generative baseline data for latency steps including zero and non-zero intervals; **Depends on: T024**
- [X] T037a [US3] **Validate Baseline**: Validate generative baseline output quality against human-annotated gold standard (N=50) at **Negligible latency** (FR-008); **Explicit 0ms constraint**
- [X] T034b [US3] **Implement Threshold Finder**: Implement `code/analysis/threshold_finder.py` that consumes T034a baseline data and T032/T032a FDR results to **output a JSON file containing the identified latency threshold and p-value**; **explicitly implement statistical test logic for non-overlapping confidence intervals**
- [X] T034c [US3] **Verify Threshold Output**: Implement verification script for the JSON output of T034b; **Verify JSON file exists and contains expected keys**
- [X] T034d [US3] Generate statistical report table showing p-values and confidence intervals for all configurations (US-3 Independent Test)
- [X] T035 [US3] Implement `code/analysis/viz.py` to generate the Pareto frontier plot (Alignment vs. Latency)
- [X] T036 [US3] Implement `code/analysis/viz.py` to plot alignment scores across information density levels (low, medium, high)
- [X] T037 [US3] Implement `code/analysis/rubric_validation.py` to validate the rubric correlation (r ≥ 0.7) against the N=50 hold-out set from **T015d-Load** (human scores) and baseline validation results from **T037a**; **consumes rubric logic from T023 and metrics from T027; explicitly calculate correlation between rubric scores and human scores**; **Output: `data/rubric_validation_report.json`**
- [X] T038 [US3] Implement `code/main.py` entry point to orchestrate the full pipeline: Ingest -> Route -> Simulate -> Analyze -> Report
- [X] T039 [US3] Generate final report (output/report.md) containing:) Pareto frontier plot,) Table of alignment scores per density/latency, 3) Threshold identification table with 95% CIs (US-3 Independent Test)

### Tests for User Story 3

- [X] T029 [P] [US3] Unit test for statistical correction (FDR/Bonferroni) in `tests/unit/test_stats.py`
- [X] T030 [P] [US3] Unit test for Pareto frontier calculation in `tests/unit/test_metrics.py`
- [X] T031 [P] [US3] Unit test for rubric validation against N=50 hold-out set in `tests/unit/test_rubric_validation.py`

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T040 [P] Documentation updates in `specs/001-llmxive-a2ui-latency-study/quickstart.md`
- [X] T041 Code cleanup and refactoring in `code/`
- [X] T042 Performance optimization: ensure CPU inference < 500ms per query (8-bit quantization check)
- [X] T043 [P] Additional unit tests for edge cases (e.g., router confidence near boundary) in `tests/unit/`
- [X] T044 Run `quickstart.md` validation to ensure full reproducibility

---

## Phase N+1: Revision & Edge Case Hardening (Priority: P3)

**Goal**: Address specific edge cases and data integrity concerns identified during plan review to ensure robust execution.

### Implementation for Revision & Hardening

- [X] T045a [US2] Implement `code/models/router.py` load check: attempt to load the B parameter model; if it fails, **attempt to load a smaller distilled model** (Addressing Edge Case: Model Load Failure - Fallback Path).
- [X] T045b [US2] Implement `code/models/router.py` abort logic: if both the B parameter model and the smaller distilled model fail to load, **abort with a clear `RuntimeError`** specifying the memory constraint (Addressing Edge Case: Model Load Failure - Abort Path).
- [X] T046 [US2] Enhance `code/simulation/runner.py` to explicitly log `router_confidence_score` for every query, specifically for cases where the score is within ±0.05 of the decision boundary, to support post-hoc sensitivity analysis (Addressing Edge Case: Borderline Confidence).
- [X] T047 [US2] Update `code/models/fallback.py` to ensure that when no ontology match is found for an "Ambiguous" query, the system returns a specific "no-match" flag in the `RoutingDecision` object and logs the event with `event_type="no_match"` for safety analysis (Addressing Edge Case: Ontology Mismatch).
- [X] T048 [US3] **Statistical Power & Control**: Implement `calculate_power(n, effect_size)` function in `code/analysis/stats.py` and integrate into `code/analysis/rubric_validation.py` to abort if sample size is insufficient (Addressing Assumption: Rubric Validation Power); **Merged T048a and T048b**
- [X] T049 [US1] Update `code/data/ingest.py` to include a specific `streaming=True` check or chunked download strategy if the Macaron-AUI dataset exceeds the available RAM limit, ensuring the task fails loudly if the real source is unreachable rather than attempting a synthetic fallback (Addressing Data Hygiene: Large Dataset Streaming; authorized by Data Hygiene principle).
- [X] T050 [US2] Implement a "dry-run" mode in `code/simulation/runner.py` that executes a single trial with all logging enabled but no actual model inference, to verify the latency injection and patience modeling logic before committing to full simulation runs (Addressing Execution: Latency Injection Verification).

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **Pre-Phase 4 (Manual Gate)**: Depends on Phase 3 completion (specifically T015d-Load/T015d-Gen) - BLOCKS Phase 4
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data (labeled CSV) for training the router (T019 -> T019b-Run -> T019b-Verify -> T020) and **Pre-Phase 4 (T015c)** for hold-out validation
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 simulation logs for analysis (T027 -> T032 -> T034)

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
Task: "Contract test for data schema validation in tests/contract/test_data_schemas.py"
Task: "Unit test for annotation script logic in tests/unit/test_data_ingest.py"

# Launch all models for User Story 1 together:
Task: "Implement code/data/ingest.py with load_dataset and CLI --annotate flag"
Task: "Create annotation interface script code/data/annotate.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (ensure N=500 labeled data exists)
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo (Simulate routing)
4. Add User Story 3 → Test independently → Deploy/Demo (Analyze results)
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Data Ingestion)
 - Developer B: User Story 2 (Routing & Simulation)
 - Developer C: User Story 3 (Analysis & Viz)
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- **CRITICAL**: Do NOT use synthetic data fallbacks. If real data fetch fails, the task must fail loudly.
- **CRITICAL**: Ensure the router is CPU-optimized (quantized DistilBERT) and the generative model is quantized (quantized DistilGPT) to fit within GitHub Actions constraints.
- **CRITICAL**: Latency injection must be explicit and logged; user patience must be modeled as exponential decay.
- **CRITICAL**: Implement density iteration for {1, 3, 5, 10} to support the minimum viable density study (integrated into T024a/b/c).
- **CRITICAL**: Create N=50 human-annotated hold-out set for rubric validation (T015d-Load); T015d-Gen is CI-only.
- **CRITICAL**: Ensure sensitivity analysis is performed in the Analysis phase (Phase 5), not the Simulation phase.
- **CRITICAL**: Rubric validation (T037) must explicitly calculate the correlation coefficient (r) against the hold-out set (T015d-Load).
- **CRITICAL**: Statistical correction (T032) must use FDR (Benjamini-Hochberg) or Bonferroni (T032a).
- **CRITICAL**: Alignment scoring (T023) must include `latency_penalty` component.
- **CRITICAL**: T019 (Implement training script) and T019b-Run/T019b-Verify (Execute/Verify training) are distinct tasks to ensure reproducibility; T019 now generates the model file.
- **CRITICAL**: T024a/b/c logs `ui_element_count`; T027/T027b validates it.
- **CRITICAL**: T034a generates baseline data; T034b consumes it and T032/T032a to identify the threshold.
- **CRITICAL**: T039 generates the final report with specific deliverables (Pareto, table, threshold).
- **CRITICAL**: T015 formats data for manual review; T015d-Gen generates placeholder for CI; T015d-Load loads committed data.
- **CRITICAL**: T015c ensures the hold-out set is valid before simulation (Manual Gate).
- **CRITICAL**: T033a runs the sensitivity analysis on the trained model.
- **CRITICAL**: T003 and T004 have specific content rules and verification methods.
- **CRITICAL**: T009 produces specific YAML schemas using jsonschema syntax (programmatic).
- **CRITICAL**: T013 validates the N=500 dataset coverage.
- **CRITICAL**: T019b-Verify verifies the model file exists with SHA-256 hash.
- **CRITICAL**: T015b verifies the N=50 hold-out set format and completeness.
- **CRITICAL**: T037 consumes T015d-Load, T023, and T037a.
- **CRITICAL**: T034a consumes T024; T034b consumes T034a and T032/T032a.
- **CRITICAL**: T024a/b/c includes logging of `ui_element_count`.
- **CRITICAL**: T027/T027b includes validation of `ui_element_count` and `ui_completeness`.
- **CRITICAL**: T033 is in Phase 4 (US2) and T033a is in Phase 4 (US2).
- **CRITICAL**: T039 generates the final report with specific deliverables (Pareto, table, threshold).
- **CRITICAL**: T045a/T045b implements the fallback then abort logic.
- **CRITICAL**: T048 implements power calculation and abort logic.
- **CRITICAL**: T049 implements streaming for large datasets.
- **CRITICAL**: T050 implements dry-run mode.
- **CRITICAL**: T020b explicitly verifies CPU-optimization (quantization).
- **CRITICAL**: T021b explicitly implements quantized DistilGPT2 loading.
- **CRITICAL**: T033b explicitly measures robustness (variance in inconsistency rates).
- **CRITICAL**: T037a explicitly validates baseline at 0ms latency.
- **CRITICAL**: T015d-Gen is the mandatory CI placeholder generation; T015d-Load is the load step.
- **CRITICAL**: T015c gates T015d-Load (human) specifically.
- **CRITICAL**: T024b handles borderline confidence scores.
- **CRITICAL**: T048 performs the power calculation to justify N=50.
- **CRITICAL**: T020 (Router Implementation) MUST precede T019 (Training Script) because the training script needs the router class.
- **CRITICAL**: T024b iterates over {1, 3, 5, 10}.
- **CRITICAL**: T033 uses the corrected set {0.6, 0.7, 0.8}.
- **CRITICAL**: T023b implements the `latency_penalty` component.
- **CRITICAL**: T012b-CLI implements a concrete CLI annotation tool.
- **CRITICAL**: T015d-Gen and T015d-Load replace the manual T015d task to ensure reproducibility.
- **CRITICAL**: T019b is split into T019b-Run and T019b-Verify.
- **CRITICAL**: T037 outputs `data/rubric_validation_report.json`.
- **CRITICAL**: T034b is the Threshold Finder; T034c verifies it; T034d generates the table.
- **CRITICAL**: T045a/T045b, T046, T047, T048, T049, T050 are in Phase N+1.
- **CRITICAL**: Duplicate tasks T051, T052, T054, T055, T056, T057 have been removed.
- **CRITICAL**: Plan Summary N=200 vs Spec N=500 is a plan-root cause issue; tasks enforce N=500.
- **CRITICAL**: Plan Summary omits `latency_penalty`; tasks include it (T023b).
- **CRITICAL**: Spec FR-007 typo '{, 0.7, 0.8}' is a spec-root cause issue; tasks use {0.6, 0.7, 0.8}.
- **CRITICAL**: T034b ID collision resolved by renaming second T034b to T034c.