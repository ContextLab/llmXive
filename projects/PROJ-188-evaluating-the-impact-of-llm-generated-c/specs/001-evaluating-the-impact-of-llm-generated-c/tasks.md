# Tasks: Evaluating the Impact of LLM-Generated Code Explanations on Comprehension

**Input**: Design documents from `/specs/001-evaluating-the-impact-of-llm-generated-c/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Functional Requirements Context**:
- FR-001: System must use CodeLlama-7B for explanation generation (with TinyLlama fallback).
- FR-005: Analysis must use LMM with participant-only random intercepts.
- FR-009: Report must include limitation statement about BLEU similarity.

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

---

## ⛔ Phase 0: Governance & Prerequisites (GATE)

**Purpose**: Resolve critical governance conflicts and establish prerequisites. **NO implementation tasks in Phases 1-N can proceed until this phase is marked COMPLETE.**

- [ ] T000a [GATE] [Governance] [Tag: Const-VII] [Tag: FR-001] **DECISION REQUIRED**: Formal decision to amend Constitution Principle VII (StarCoder-15B) to align with Spec FR-001 (CodeLlama-7B).
 - **Logic**: Since Spec FR-001 mandates CodeLlama-7B and Constitution Principle VII mandates StarCoder-15B, the decision is to **AMEND the Constitution** to match the Spec.
 - **Action**: Initiate the formal amendment process by opening a Pull Request to update `constitution.md`. The PR description must state the rationale: "Spec FR-001 takes precedence for implementation; Constitution updated to align."
 - **Constraint**: This task is a **PREREQUISITE GATE**. The pipeline is invalid and halts if this task is not marked COMPLETE before any other task execution.
 - **Escalation**: If the amendment process fails or is rejected, the project MUST escalate to `human_input_needed`.
 - **Output**: A Pull Request link or a record in `data/governance_amendment_decision.json` containing the decision rationale and approval signature.
- [ ] T000b [GATE] [Governance] [Tag: Const-VII] [Tag: FR-001] **EXECUTION**: Execute the formal amendment of `constitution.md` Principle VII to authorize CodeLlama-7B with TinyLlama fallback.
 - **Dependency**: **[Depends on: T000a]**
 - **Action**: Update the local `constitution.md` file with the amended text: "All LLM-generated explanations MUST be produced using CodeLlama-7B (or TinyLlama fallback) via the HuggingFace `transformers` library with a fixed token limit of 200 and pinned random seeds."
 - **Action**: Update the version line in `constitution.md` to "2.0.0".
 - **Action**: Commit the change to the repository.
 - **Output**: Updated `constitution.md` with amended Principle VII and version 2.0.0.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001a [P] [Setup] Create root directory `projects/PROJ-188-evaluating-the-impact-of-llm-generated-c/`.
- [ ] T001b [P] [Setup] Create `code/` subdirectory.
 - **Dependency**: **[Depends on: T001a]**
- [ ] T001c [P] [Setup] Create `data/` subdirectory.
 - **Dependency**: **[Depends on: T001a]**
- [ ] T001d [P] [Setup] Create `data/raw/`, `data/intermediate/`, and `data/processed/` subdirectories.
 - **Dependency**: **[Depends on: T001c]**
- [ ] T001e [P] [Setup] Create empty `__init__.py` files in `code/` and `tests/` (once created).
- [ ] T015a [P] [Data Model] Create `specs/001-evaluating-the-impact-of-llm-generated-c/data-model.md` with initial schema definitions for Snippet and Response entities.
 - **Schema**: `Snippet: {snippet_id, code, docstring, complexity_score, complexity}`, `Response: {participant_id, condition, snippet_id, answer, latency_ms, timestamp}`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T002 [P] [Setup] Initialize Python project with `code/requirements.txt` containing: `transformers==4.36.0`, `torch==2.1.0+cpu`, `scikit-learn==1.3.0`, `statsmodels==0.14.0`, `sacrebleu==2.3.0`, `datasets==2.14.0`, `pandas==2.1.0`, `numpy==1.24.0`, `pyyaml==6.0.1`. **Note**: Install torch using `--index-url https://download.pytorch.org/whl/cpu` for Linux.
- [ ] T003 [P] [Setup] Configure linting (ruff) and formatting (black) tools.
- [ ] T005 [P] [Config] Implement `code/utils/config.py` with seeds (a sufficient quantity to ensure statistical power), paths, and constants (max_tokens=200, timeout=300s). **Note**: Token limit applies to CodeLlama generation per amended Constitution.
- [ ] T006 [P] [Metrics] Create `code/utils/metrics.py` with BLEU calculation and latency parsing helpers.
- [ ] T007 [P] [Setup] Setup `code/__init__.py` and empty `tests/` directory.
- [ ] T008 [P] [Config] [FR-001] [US1] Configure environment variable loading for HuggingFace token and model paths. **[Depends on: T002]**
 - **Action**: Create `code/utils/env_loader.py` to load `HF_TOKEN` from environment variables.
 - **Action**: Update `code/utils/config.py` to import and use `env_loader`.
 - **Output**: `code/utils/env_loader.py` and updated `code/utils/config.py`.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Dataset Curation and Explanation Generation (Priority: P1) 🎯 MVP

**Goal**: Ingest CodeSearchNet corpus, label complexity, and generate LLM explanations (with CPU-tractable fallback)

**Independent Test**: The script produces a JSON file with ≥20 snippets, valid explanations <200 tokens, and correct complexity labels.

### Implementation for User Story 1

- [ ] T012 [P] [US1] Implement data ingestion in `code/01_data_curation.py`: Fetch Python subset from CodeSearchNet (HuggingFace `codeparrot/code-search-net`). **Constraint**: Must stream data to avoid OOM.
- [ ] T013b [US1] Implement raw complexity score calculation in `code/01_data_curation.py`: Compute the raw cyclomatic complexity score (float) for each snippet and store it in the `complexity_score` field of the Snippet entity. **[Depends on: T012]**
- [ ] T013 [US1] Implement cyclomatic complexity labeling (low/medium/high) based on raw score ranges in `code/01_data_curation.py`. **[Depends on: T013b]**
 - **Logic**: `low` if score < 5, `medium` if 5 <= score <= 10, `high` if score > 10.
- [ ] T013c [US1] Implement validation script to verify derivation logic in `code/01_data_curation.py`. **[Depends on: T013]**
 - **Action**: Assert that `complexity_label` correctly maps to `complexity_score` ranges (low: <5, medium: 5-10, high: >10) for all rows.
 - **Pass Criteria**: Script exits with code 0 only if all assertions pass.
 - **Output**: Log validation results to `data/intermediate/complexity_validation.log`.
- [ ] T014 [US1] Implement LLM explanation generation in `code/01_data_curation.py`:
 - **⚠️ GOVERNANCE CONFLICT RESOLVED**: This task implements Spec FR-001 (CodeLlama-7B) with Constitution-compliant token limit (200) after amendment T000b.
 - **Dependency**: **[Depends on: T005, T008, T012, T000b]**
 - Attempt CodeLlama-7B (4-bit quantized) with CPU device map.
 - **Fallback Logic**: If model fails to load or exceeds memory/time thresholds (catch `OutOfMemoryError`, `RuntimeError`, or if RAM > 7GB), switch to TinyLlama/TinyLlama-7B-Chat-v1.0.
 - **Validation**: Ensure fallback model and token limit do not violate Constitution Principle VII (amended).
 - **Constraint**: If fallback triggers for >20% of snippets, the task MUST fail and escalate to `human_input_needed`.
 - Enforce a token limit and a multi-retry backoff strategy.
 - **Output**: Save `data/intermediate/explanations.json` with fields: `snippet_id`, `code`, `complexity`, `complexity_score`, `explanation`, `token_count`, `model_used`, `status` (success/skipped).
- [ ] T016 [US1] Implement validation script to verify: no nulls, all labels valid, token counts <200, and N ≥ 20. **[Depends on: T014]**
- [ ] T017 [US1] Add logging for skipped snippets and fallback triggers. **[Depends on: T014]**
 - **Action**: Append to `data/intermediate/generation.log` with format: `[timestamp] [level] [model] [snippet_id] [reason]`.

### Validation for User Story 1

- [ ] T009 [US1] Unit test for complexity labeling logic in `tests/test_curation.py`: Create `test_complexity_labeling()` that asserts `complexity_label in ['low', 'medium', 'high']` and correctly maps to score ranges. **[Depends on: T013]**
- [ ] T010 [US1] Integration test for model loading fallback in `tests/test_curation.py`: Create `test_model_fallback()` that asserts `model_loaded == True` when CodeLlama fails and TinyLlama is used. **[Depends on: T014]**

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Study Survey Construction and Deployment (Priority: P2)

**Goal**: Construct survey logic (simulation) for three conditions, randomization, and data recording.

**Independent Test**: Mock survey logic correctly assigns conditions, records latency, and outputs structured CSV.

### Implementation for User Story 2

- [ ] T018 [P] [US2] Implement participant randomization in `code/02_survey_logic.py`: Stratified assignment to Code Only, Code+LLM, Code+Docstring (seed=42). **[Depends on: T014]**
- [ ] T019 [US2] Implement condition rendering logic in `code/02_survey_logic.py`:
 - Condition A: Code only.
 - Condition B: Code + LLM Explanation (from `explanations.json`).
 - Condition C: Code + Official Docstring (or "No Doc" placeholder if missing).
 - **Output**: Save `data/intermediate/survey_conditions.json` with the rendered conditions.
 - **[Depends on: T014]**
- [ ] T020b [US2] Implement mock survey runner in `code/02_survey_logic.py`: Simulate N=10 participants with random latency >30s (Uniform(30000, 300000) milliseconds). Output `data/intermediate/mock_responses.csv` with columns: `participant_id`, `condition`, `snippet_id`, `answer` (bool), `latency_ms`, `timestamp`, `missing_count` (calculated in-memory only, NOT persisted). **[Depends on: T019]**
- [ ] T021a [US2] Implement script to ingest real participant data (from a deployed survey or CSV) into `data/intermediate/responses.csv`.
 - **Fallback**: If real data is missing, generate mock data using T020b logic and log the fallback.
- [ ] T021b [US2] Implement script to ingest mock survey data (from T020b) into `data/intermediate/responses.csv`. **[Depends on: T020b]**
- [ ] T022 [US2] Add filtering logic for invalid participants (<30s total time or >80% missing). **Definition**: 'missing' is defined as unanswered questions. Denominator is `total_questions` = 3 per participant. Log exclusion counts. **[Depends on: T021b]**
 - **Action**: Calculate `missing_count` in-memory for each participant. If `latency < 30000` OR `missing_count >= 0.8 * 3`, mark as invalid.
 - **Action**: Do NOT persist `missing_count` to the CSV.
 - **Output**: Save `data/intermediate/responses_clean.csv` with only valid participants.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Analysis and Robustness Reporting (Priority: P3)

**Goal**: Execute LMM analysis, Tukey post-hoc, and BLEU sensitivity sweep.

**Independent Test**: Analysis script runs on synthetic data, produces F-stat/p-values, and generates sensitivity report.

### Implementation for User Story 3

- [ ] T025 [US3] Implement data cleaning in `code/03_analysis.py`: Filter invalid participants, merge with snippet data (complexity, explanation).
 - **[Depends on: T014, T022, T021b]**
- [ ] T026 [US3] Implement Linear Mixed Model (LMM) in `code/03_analysis.py`:
 - **⚠️ DESIGN DECISION**: Explicitly implement Spec FR-005 mandate: "LMM with participant-only random intercepts".
 - **Note**: This task overrides the Plan's GLMM rationale. The Plan contains a design flaw; the Spec is the source of truth.
 - Fixed effects: `condition`, `complexity`, `condition:complexity`.
 - Random intercepts: `participant_id` (ONLY).
 - Family: Gaussian.
 - Formula: `answer ~ condition * complexity + (1|participant_id)`.
 - **[Depends on: T025]**
- [ ] T027 [US3] Implement post-hoc Tukey HSD test for pairwise condition comparisons with adjusted p-values.
 - **[Depends on: T026]**
- [ ] T028 [US3] Implement BLEU sensitivity sweep (Internal Analysis Requirement derived from FR-009):
 - Calculate BLEU scores for LLM explanations vs. official docstrings (reference).
 - Re-run analysis on subsets where BLEU scores meet varying high-quality thresholds.
 - **Output Artifact**: Save `data/processed/sensitivity_report.csv` with columns: `threshold`, `accuracy_mean`, `latency_mean`, `p_value_interaction`.
 - **Mandatory Deliverable**: The analysis script MUST generate a `limitation_note` field in the report metadata containing a statement about BLEU similarity (e.g., "BLEU similarity measures fidelity to the baseline...").
 - **[Depends on: T026]**
- [ ] T029c [US3] Generate statistical results JSON in `data/processed/stats_results.json`: F-stat, p-values, Tukey results. **[Depends on: T026, T027]**
- [ ] T029d [US3] Generate sensitivity report CSV in `data/processed/sensitivity_report.csv`. **[Depends on: T028]**
- [ ] T029e [US3] Generate final report in `data/processed/final_report.md`:
 - **Gate**: Verify T027, T028, T029c, and T029d outputs exist. If missing, fail the task.
 - Include F-stat/p-value for interaction, Tukey results, sensitivity chart/table.
 - **Mandatory**: Explicitly INSERT the limitation statement about BLEU similarity (derived from T028's `limitation_note`) as per FR-009.
 - **Chart Format**: Markdown table format, generated via matplotlib.
 - **[Depends on: T029c, T029d, T027, T028]**
- [ ] T030 [US3] Calculate and verify participant pass rate in `code/03_analysis.py`:
 - Compute percentage of recruited participants passing quality filters (>30s time, <80% missing).
 - **Logic**: Count participants where `latency > 30000` AND `missing_count < 0.8 * total_questions` (where `total_questions` = 3 per participant).
 - **Validation**: Report the pass rate in the final report. Do NOT halt the pipeline based on this rate.
 - Save results to `data/processed/analysis_results.json` and append to `data/processed/final_report.md`.
 - **[Depends on: T022, T021b, T025]**

### Validation for User Story 3

- [ ] T023 [US3] Unit test for LMM model fitting (statsmodels MixedLM) with synthetic data in `tests/test_analysis.py` **[Depends on: T026]**
- [ ] T024a [US3] Unit test for BLEU calculation in `tests/test_analysis.py`: Test the BLEU function from `code/utils/metrics.py` with synthetic data. **[Depends on: T006]**
- [ ] T024b [US3] Unit test for BLEU sensitivity sweep logic in `tests/test_analysis.py`: Test the sweep logic using mock data. **[Depends on: T028]**

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T031 [P] [Polish] Documentation updates in `README.md` and `docs/`
- [ ] T032 [Polish] Code cleanup and refactoring
- [ ] T033 [Polish] Performance optimization (ensure CPU inference completes within 6h)
- [ ] T034 [P] [Polish] Run `pytest` on all test suites
- [ ] T035 [Polish] Run `quickstart.md` validation

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 0 (Governance)**: **BLOCKING GATE**. Must be complete before Phase 1.
- **Setup (Phase 1)**: Depends on Phase 0 completion.
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories.
- **User Stories (Phase 3+)**: All depend on Foundational phase completion.
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - **Depends on T014** (explanations.json) for T019/T020b
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - **Depends on T014** (explanations.json) and **T022** (responses.csv) for full analysis.

### Within Each User Story

- Tests (if included) MUST be written and FAIL after the implementation logic is defined (Producer before Consumer)
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel (except T001b/T001c which depend on T001a)
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if staffed)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch models for User Story 1 together:
Task: "Implement data ingestion in code/01_data_curation.py"
Task: "Implement complexity labeling in code/01_data_curation.py"
Task: "Implement raw complexity score calculation in code/01_data_curation.py"

# Launch tests for User Story 1 after implementation:
Task: "Unit test for complexity labeling logic in tests/test_curation.py"
Task: "Integration test for model loading fallback in tests/test_curation.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 0: Governance (GATE)
2. Complete Phase 1: Setup
3. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
4. Complete Phase 3: User Story 1
5. **STOP and VALIDATE**: Test User Story 1 independently (verify N≥20, valid explanations).
6. Deploy/demo if ready.

### Incremental Delivery

1. Complete Phase 0 + Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Phase 0 + Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Data & Inference)
 - Developer B: User Story 2 (Survey Logic)
 - Developer C: User Story 3 (Analysis - can mock data initially)
3. Stories complete and integrate independently.

---

## Notes

- [P] tasks = different files, no dependencies (except where explicitly noted)
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail after implementation logic is defined
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- **CRITICAL**: Do not use `load_in_8bit` or CUDA-specific device maps. Use `load_in_4bit` with CPU device map or fallback to TinyLlama to ensure execution on GitHub Actions `ubuntu-latest` (multi-core CPU, sufficient RAM).
- **Data Integrity**: All analysis must use real data from `explanations.json` and `responses.csv`. Do not fabricate synthetic input data for the final run.
- **Task Ordering**: T014 (Generation) must complete before T019/T020b (Survey Logic) can use the explanations. T022/T021b (Responses/Missing Count) must complete before T025/T026 (Analysis) can run the full pipeline.
- **Constitutional Warnings**: Task T000a flags the conflict and mandates a blocking amendment. Task T000b performs the amendment. Task T014 implements the Spec requirement with Constitution-compliant token limit (200) after amendment. Task T026 explicitly rejects the Plan's GLMM rationale in favor of the Spec's LMM mandate.
- **Plan Alignment**: The `plan.md` 'Complexity Tracking' section contains a design flaw (GLMM vs LMM). The tasks follow the Spec (FR-005) and override the Plan.