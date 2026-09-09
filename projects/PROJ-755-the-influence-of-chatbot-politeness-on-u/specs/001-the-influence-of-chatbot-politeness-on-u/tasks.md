# Tasks: The Influence of Chatbot Politeness on User-Perceived Quality

**Input**: Design documents from `/specs/001-chatbot-politeness-trust/`
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

- [ ] T001 [P] Create all project directories: `data/raw`, `data/processed`, `data/models`, `code`, `code/utils`, `tests`, `tests/contract`, `tests/unit`, `tests/integration`, `docs`, `state`.
 - *Logic*: Consolidates T001a-T001d into a single atomic step to ensure directory structure is created as one verifiable action.
- [X] T002 [P] Initialize Python project with `code/requirements.txt` (transformers, datasets, statsmodels, pandas, scikit-learn, numpy, pyyaml, tqdm, rpy2, textstat, evalue, memory_profiler).
 - *Logic*: Create `code/requirements.txt` containing ONLY Python packages. `ordinal` is an R package and must NOT be in this list; it is handled in T004b.
- [ ] T003 [P] Configure linting (ruff/flake8) and formatting (black)
- [ ] T004 [P] Setup CI workflow (GitHub Actions) to install R-base and Python dependencies
- [ ] T004b [P] Setup R environment: Install R packages `lme4` and `ordinal` via system-level commands in CI workflow.
 - *Logic*: R packages cannot be installed via pip. This task ensures `lme4` and `ordinal` are available for `rpy2` execution on the CI runner.
- [X] T006 [P] Implement `code/utils/pii_scanner.py` for PII scanning (regex for email, phone, SSN patterns)
- [X] T007 [P] Implement `code/utils/data_integrity.py` for checksumming and data integrity checks
- [X] T007b Implement `state/projects/PROJ-755-the-influence-of-chatbot-politeness-on-u.yaml` to record checksums in `artifact_hashes.raw_data` key after T007 generates them.
 - *Logic*: Dependency: T007. Must wait for T007 to complete.
 - *Note*: Removed [P] marker to enforce sequential execution.
- [ ] T008 Create `contracts/dataset.schema.yaml` defining Dialogue, Utterance, and User entities
 - *Logic*: This task MUST be completed before T011. Removed [P] to enforce sequential execution.
- [ ] T010 [P] [Setup] Create `contracts/output.schema.yaml` defining CLMM results structure
- [ ] T010b [P] [Setup] Setup environment configuration management (`.env` template for `HF_TOKEN` if needed).
 - *Logic*: Create `.env.example` with `HF_TOKEN=` placeholder. Document in `README.md` that this is for local development only and that CI secrets must be injected via GitHub Actions environment variables to ensure reproducibility on fresh runners per Constitution Principle I.

**Checkpoint**: Setup ready - Foundational phase can now begin

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure and validation that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete. These tasks verify the data exists and meets schema requirements.

- [ ] T011 [P] [Foundational] Implement `code/utils/schema_validator.py` to validate dataset schemas against `contracts/dataset.schema.yaml`
 - *Logic*: Dependency: T008 must be completed first. T011 validates the schema generated in T008.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Politeness Scoring (Priority: P1) 🎯 MVP

**Goal**: Download **Persona-Chat** and **EmpatheticDialogues** datasets. Filter for completeness, and compute mean politeness scores per conversation using `jfiedler/politeness-bert` on CPU.
**Strict Abort Logic**: The pipeline MUST proceed with any dataset that has the required `quality_rating` variable. The pipeline MUST ONLY abort if BOTH datasets fail to download OR BOTH datasets are downloaded but lack the `quality_rating` variable. If a dataset is downloaded but lacks the variable, it is excluded from the merged set, and the pipeline continues with the remaining valid datasets. If only one dataset is valid, the pipeline proceeds with that one.

**Independent Test**: Run `code/01_download_and_score.py` on a sample of dialogues; verify `data/processed/scored_dialogues.parquet` exists with `politeness_score` and `quality_rating` columns, and that excluded dialogues are logged.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T013 [P] [US1] Contract test for dataset schema validation in `tests/contract/test_dataset_schema.py`
- [X] T014 [P] [US1] Unit test for politeness scoring logic (batched inference) in `tests/unit/test_scoring.py`

### Implementation for User Story 1

#### Download & Validate Tasks (Merged for Atomicity)
- [X] T015 [US1] **Download, Validate, and Filter All Datasets**: Implement `code/01_download_and_score.py` to fetch **Persona-Chat** and **EmpatheticDialogues**.
 - *Logic*:
 1. **Sources**: `huggingface/datasets/persona-chat`, `emotional-reality/empathetic_dialogues`. (Reference: plan.md "Dataset Constraint Resolution" for authorized sources).
 2. **Action**: Download raw data to `data/raw/{source}/raw_data.parquet`.
 3. **Validate**: Verify `quality_rating`, `user_id`, `dialogue_id` columns exist in each source.
 4. **Granular Exclusion**: If a source has the `quality_rating` column, filter out individual dialogues where `quality_rating` is missing. Log the count of excluded dialogues per source.
 5. **Source Exclusion**: If a source lacks the `quality_rating` column entirely, exclude the entire source and log "excluded" in `data/raw/validation_status.json`.
 6. **Abort**: If ALL sources are excluded, abort pipeline with "NO_VALID_DATA_SOURCE".
 7. **Store**: Save raw data with checksums.
 - *Deliverable*: `data/raw/persona_chat/filtered.parquet`, `data/raw/empathetic_dialogues/filtered.parquet`, and `data/raw/validation_status.json`.

#### Transform & Score Tasks
- [ ] T018 [US1] **Transform to Target Schema**: Transform filtered datasets to match target schema.
 - *Logic*:
 1. **Dependency**: T015.
 2. **Define Schema**: Define target schema (user_id, dialogue_id, quality_rating, age, gender, utterances, source_dataset).
 3. **Transform**: Transform each filtered dataset to match schema.
 4. **Output**: Save transformed datasets to `data/processed/transformed_{source}.parquet`.
 - *Deliverable*: `data/processed/transformed_persona_chat.parquet`, `data/processed/transformed_empathetic_dialogues.parquet`.
- [ ] T019 [US1] **Merge, Score, and Standardize**: Merge all transformed datasets, compute politeness scores, and apply global standardization.
 - *Logic*:
 1. **Dependency**: T018.
 2. **Merge**: Merge all valid transformed sources into `data/processed/filtered_dialogues.parquet`.
 3. **Score**: Load `jfiedler/politeness-bert` (Revision: `main`, Cache: `data/models`). Verify model file size ≤ 100MB. Iterate through utterances in batches. Compute politeness scores; assign NaN to failures and log counts.
 4. **Conversation Length**: Compute `conversation_length` as **word count** per dialogue.
 5. **Standardize**: Calculate global mean/std using `pandas` and apply z-scoring to create `mean_politeness_score`.
 6. **Memory Check**: If dataset size > 6GB, raise `MemoryError` with message "Dataset exceeds memory limit. Please reduce sample size or use streaming." Do NOT use Dask.
 7. **Save**: Save final merged and scored dataset to `data/processed/filtered_dialogues.parquet`.
 - *Note*: This task combines merging and scoring to ensure the final output has the standardized score.
 - *Deliverable*: `data/processed/filtered_dialogues.parquet` (contains `mean_politeness_score`).

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: Data Verification Gate (Pre-US3)

**Purpose**: Validate sample sizes for subgroup analysis before attempting US3. This task must pass for US3 to proceed.

- [ ] T012 [Gate] **Sample Size Verification** for Subgroups and Primary Analysis.
 - *Logic*:
 1. **Dependency**: T019.
 2. Load the **merged** dataset (`data/processed/filtered_dialogues.parquet`).
 3. **Check Subgroups**: Count dialogues per `age` group and `gender` group.
 4. **Gate Condition**: If ANY subgroup (e.g., Male, Female, Age 18-25) has n < 30, log that US3 will be skipped for that specific group.
 5. Generate `data/processed/validation_report.json` with schema:
 ```json
 {
 "status": "full" | "partial" | "missing_demographics",
 "demographic_completeness_pct": 0.0,
 "total_sample_size": 500,
 "primary_analysis_valid": true,
 "missing_fields": [],
 "subgroup_counts": { "male": 500, "female": 480, "age_18_25": 200,... },
 "subgroups_eligible": ["male", "female", "age_18_25"],
 "subgroups_excluded": [],
 "gate_status": "passed"
 }
 ```
 - *Deliverable*: `data/processed/validation_report.json`.
 - *Note*: This task gates US3. It must run after data is merged and scored.

**Checkpoint**: Data verified - user story implementation can now begin in parallel

---

## Phase 5: User Story 2 - Cumulative Link Mixed-Effects Analysis (Priority: P2)

**Goal**: Fit a CLMM testing the association between politeness and quality ratings, controlling for length and user random effects, with multiple-comparison correction.

**Independent Test**: Run `code/02_fit_clmm.py` on `filtered_dialogues.parquet`; verify `data/processed/clmm_results.csv` contains coefficients, p-values, and that fallback to fixed-effects is logged if CLMM fails.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T023 [P] [US2] Unit test for VIF calculation and collinearity check in `tests/unit/test_collinearity.py`
- [X] T024 [P] [US2] Integration test for CLMM execution and result schema validation in `tests/integration/test_clmm.py`

### Implementation for User Story 2

- [X] T025 [US2] Implement `code/02_fit_clmm.py` to load `filtered_dialogues.parquet`
- [ ] T026 [US2] Implement VIF check for `politeness` and `conversation_length`; log warning and drop variable if VIF ≥ 5.
 - *Logic*: Dependency: T025.
- [ ] T027a [US2] **CLMM Fitting with Fallback**: Fit primary CLMM and record convergence status; fit fixed-effects ordinal regression if CLMM fails.
 - *Logic*:
 1. **Dependency**: T026.
 2. **Fit Primary**: Fit CLMM via `rpy2` (formula: `quality_rating ~ politeness + conversation_length + (|user_id)`) with `lme4`.
 3. **Check Convergence**: Calculate convergence status.
 4. **Fallback Logic**: If `convergence_status` is "failed", fit fixed-effects ordinal regression (remove random effects).
 5. **Record Status**: Save `data/processed/project_status.json` with fields: `convergence_status` ("success" | "failed"), `model_type` ("clmm" | "ordinal_fixed_effects"), `error_message` (if failed), `timestamp`.
 6. **SC-003 Metric**: Explicitly note that if the fallback model is used, it does **NOT** count toward the SC-003 ≥95% convergence rate metric (i.e., the convergence rate for this run is [deferred]).
 7. **Save Results**: Save results (CLMM or fallback) to `data/processed/clmm_primary_results.csv` with coefficients, SEs, p-values, and convergence metrics.
 8. **Save Model Object**: Save the fitted model object to `data/processed/clmm_model.pkl` (pickle protocol 5) for later prediction.
 - *Note*: This task handles both primary and fallback logic in one deterministic step.
 - *Deliverable*: `data/processed/clmm_primary_results.csv`, `data/processed/project_status.json`, and `data/processed/clmm_model.pkl`.
- [ ] T028 [US2] Implement Benjamini-Hochberg correction for p-values across fixed effects.
 - *Logic*:
 1. **Dependency**: T027a.
 2. **Selection Logic**: Apply **Benjamini-Hochberg** correction to all fixed-effect p-values.
 3. **Definition**: N is defined as the count of fixed-effect terms in the model (excluding the intercept).
 4. **Apply Correction**: Apply the BH method to the p-values of all fixed effects.
 5. **Save**: Update `data/processed/clmm_primary_results.csv` with corrected p-values.
 - *Deliverable*: Updated `data/processed/clmm_primary_results.csv`.
- [ ] T029 [US2] **Consolidate and Save Results**: Save final results to `data/processed/clmm_results.csv`.
 - *Logic*:
 1. **Dependency**: T028.
 2. Consolidate results from T027a into a single file.
 3. Apply corrections.
 4. Save to `data/processed/clmm_results.csv`.
 - *Note*: This task ensures the final file is written after all corrections.
 - *Deliverable*: `data/processed/clmm_results.csv`.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 6: User Story 3 - Robustness and Subgroup Analysis (Priority: P3)

**Goal**: Validate findings with the **LIWC-2015 Politeness Dictionary** and conduct subgroup analyses by age/gender (n ≥ 30 guard).

**Independent Test**: Run `code/03_robustness_analysis.py`; verify `data/processed/robustness_results.csv` exists, correlation (r ≥ 0.80) is calculated, and subgroup exclusions are logged.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T030 [P] [US3] Unit test for lexicon-based scoring logic in `tests/unit/test_lexicon_scoring.py`
- [X] T031 [P] [US3] Integration test for subgroup filtering logic (n ≥ 30) in `tests/integration/test_subgroup.py`

### Implementation for User Story 3

- [ ] T032a [US3] **Mandatory LIWC-2015 Acquisition**: Implement `code/03_robustness_analysis.py` to attempt loading the LIWC-2015 dictionary.
 - *Logic*:
 1. **Dependency**: T019 (Completion of US1). Load `filtered_dialogues.parquet`.
 2. **Citation Requirement**: Include explicit citation to HCI literature (Nass & Moon, 2000; Bickmore & Picard, 2005) validating `quality_rating` as a proxy for 'trust' with explicit citation to HCI literature (Nass & Moon, 2000; Bickmore & Picard, 2005) validating the correlation in conversational agents.
 3. **Attempt LIWC Acquisition**: Attempt to load LIWC-2015 from `data/models/liwc_2015/liwc_2015_dictionary.txt` or via `huggingface_hub.hf_hub_download` from repo `LIWC-2015/LIWC-2015` (filename: `liwc_2015_dictionary.txt`).
 4. **Strict Requirement**: If acquisition fails, **FAIL** this task. Do NOT proceed to T033. Log "LIWC-2015 Acquisition Failed. FR-005 NOT SATISFIED."
 5. **Scoring**: If successful, apply LIWC-2015 to all utterances. Compute mean scores per dialogue.
 6. **Save Scores**: Save scores to `data/processed/robustness_scores_liwc.parquet`.
 7. **Status File**: Save `data/processed/robustness_status.json` with schema:
 ```json
 {
 "source_used": "liwc",
 "liwc_acquisition_failed": false,
 "fallback_reason": null
 }
 ```
 - *Traceability*: Explicitly addresses **FR-005** (Robustness) using the mandatory classifier.
- [ ] T033 [US3] **Re-fit CLMM**: Re-fit CLMM on lexicon scores.
 - *Dependency*: Requires T032a (must succeed).
 - *Logic*:
 1. **Check**: Use `data/processed/robustness_scores_liwc.parquet`.
 2. **Fit**: Re-fit CLMM using the LIWC-based politeness scores.
 3. **Save**: Save model object to `data/processed/robustness_model.pkl` (pickle protocol 5).
 - *Deliverable*: `data/processed/robustness_model.pkl`.
- [ ] T033b [US3] **Generate Predicted Scores & Correlate**: Calculate **Spearman** rank correlation of per-dialogue predicted quality scores.
 - *Logic*:
 1. **Dependency**: T033 and T029.
 2. Load `data/processed/clmm_model.pkl` (from T027a) for **primary** predictions.
 3. Load `data/processed/robustness_model.pkl` (from T033) for **robust** predictions.
 4. Generate `predicted_quality` scores for each dialogue using both models via the `predict()` method on the original input data.
 5. Save per-dialogue predictions to `data/processed/robustness_predictions.csv` (columns: `dialogue_id`, `primary_predicted`, `robust_predicted`).
 6. **Target Variable**: Use the available robustness model (LIWC) for the correlation.
 7. **Calculate Correlation**: Calculate **Spearman rank correlation** `correlation_r` between `primary_predicted_quality` and `robust_predicted_quality`.
 8. **Calculate P-value and N**: Compute the p-value and sample size (N) for the correlation.
 9. **Rationale**: Spearman is used for ordinal data consistency (Likert 1-5) to match SC-004 intent.
 10. **Verify**: Check if `correlation_r` >= 0.80. Log "SC-004 MET" or "SC-004 NOT MET".
 11. Save `correlation_r`, `p_value`, `n`, and `source_used` to `data/processed/robustness_summary.json`.
 - *Note*: Explicitly generate per-dialogue predicted quality scores via CLMM prediction before correlation calculation. This task ALWAYS produces the correlation metric.
 - *Dependency*: T033, T029.
 - *Deliverable*: `data/processed/robustness_summary.json`.
- [ ] T034 [US3] **Subgroup Analysis**: Split data by age/gender.
 - *Dependency*: Requires T012 (Sample Size Verification) to have reported `subgroups_eligible`. **Also requires T019 (US1 completion)**.
 - *Logic*:
 1. **Check Columns**: If `age` or `gender` columns are missing, log "Subgroup analysis skipped: missing demographic columns" and exit.
 2. **Filter**: Exclude groups with n < 30 (as per T012), log exclusions.
 3. **Fit**: Fit separate CLMMs for valid subgroups and test interaction terms.
 4. **Output**: Save each subgroup model to `data/processed/subgroup_clmm_{group}.csv`.
 - *Deliverable*: `data/processed/subgroup_clmm_{group}.csv` files.
- [ ] T035 [US3] Apply multiplicity correction for subgroup tests.
 - *Logic*:
 1. **Dependency**: T034.
 2. **Action**: Apply Benjamini-Hochberg correction to p-values from subgroup tests.
 3. **Output**: Save corrected results to `data/processed/subgroup_corrected_results.csv`.
 - *Deliverable*: `data/processed/subgroup_corrected_results.csv`.
- [ ] T037 [US3] Save all robustness results to `data/processed/robustness_results.csv`.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T038a [P] Update `README.md` with project overview, installation instructions, and usage examples.
- [ ] T038b [P] Update `docs/quickstart.md` with a step-by-step guide to running the full pipeline.
- [ ] T038c [P] Update `docs/data-model.md` with entity definitions and data flow diagrams.
- [ ] T039 Code cleanup and refactoring (remove debug prints, ensure type hints)
- [ ] T040 [P] Performance optimization: verify memory usage < 7GB during peak BERT inference using `memory_profiler`.
 - *Logic*:
 1. Decorate the BERT inference function in `code/01_download_and_score.py` with `@profile` from `memory_profiler`.
 2. Run the function on a full batch.
 3. Check peak memory usage from output.
 4. If > 7GB, log error "MEMORY_EXCEEDED" and suggest batch size reduction.
 - *Deliverable*: `data/processed/memory_profile.log`.
- [ ] T041 [P] Additional unit tests for edge cases (empty dialogues, NaN handling) in `tests/unit/`
- [ ] T042 [P] Configure CI workflow for full pipeline execution on GitHub Actions.
 - *Logic*: Create `.github/workflows/ci.yml` to install R, Python deps, and run the full pipeline.
- [ ] T042b [P] Execute full pipeline on GitHub Actions and capture metrics.
 - *Logic*: Run the CI workflow. Verify runtime < 6h and RAM < 7GB. Capture metrics.
 - *Dependency*: T042.
 - *Deliverable*: `data/processed/performance_metrics.json`.
- [ ] T043 [P] Generate `docs/performance_report.md` with explicit schema.
 - *Schema*: `runtime_seconds`, `peak_memory_gb`, `convergence_rate`, `status`.
 - *Logic*: Collect metrics from `data/processed/performance_metrics.json` (generated by T042b).
 - *Dependency*: T042b.
 - *Deliverable*: `docs/performance_report.md`.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - **BLOCKS** all user stories.
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Requires output from US1 (`filtered_dialogues.parquet`)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Requires output from US1 and US2 for comparison. **Explicitly depends on T012 passing (or partial status with available fields).**

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
- Different user stories can be worked on in parallel by different team members

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all user stories, includes T012 verification)
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
 - Developer C: User Story 3 (Only if T012 passes or partial status available)
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
- **Constraint**: All BERT inference must be CPU-only (no CUDA); use batch processing to stay under available RAM limits.
- **Constraint**: Dataset source MUST include Persona-Chat and EmpatheticDialogues. Abort only if ALL three fail.
- **Constraint**: Subgroup analysis (US3) is strictly gated by T012 (Sample Size Verification, n ≥ 30).
- **Constraint**: Robustness classifier (US3) MUST use LIWC-2015; if acquisition fails, the task fails (no fallback).
- **Constraint**: Convergence rate (SC-003) is measured by the primary run's convergence status; fallback models count as [deferred] convergence.
- **Constraint**: Memory limit is ~6GB; if exceeded, the pipeline MUST raise a `MemoryError` and stop (no Dask fallback).

# Constitution (FR-030)

# The Influence of Chatbot Politeness on User Trust — Research Project Constitution

## Core Principles

### I. Reproducibility (NON-NEGOTIABLE)

Every result reported in this project MUST be reproducible by re-running the
project's `code/` against the project's `data/` on a fresh GitHub Actions
runner. Random seeds MUST be pinned in `code/`. External datasets MUST be
fetched from the same canonical source on every run.

### II. Verified Accuracy (inherits parent Principle II)

Every external citation in `idea/`, `technical-design/`,
`implementation-plan/`, or `paper/` MUST be verified by the
Reference-Validator Agent against the primary source before contributing
review points. Title-token-overlap with the cited source MUST be ≥
`CITATION_TITLE_OVERLAP_THRESHOLD` (default 0.7).

### III. Data Hygiene

Datasets MUST be checksummed and the checksum recorded under `data/`. No
data may be modified in place; every transformation MUST produce a new file
with a documented derivation. Personally identifying information MUST NOT
appear in committed data.

### IV. Single Source of Truth (inherits parent Principle I)

Every figure, statistic, or interpretation in the paper MUST trace back to
exactly one row in this project's `data/` and one block in this project's
`code/`. Derived numbers MUST NOT be hand-typed into the paper.

### V. Versioning Discipline

Every artifact under this project carries a content hash. The
Advancement-Evaluator Agent invalidates stale review records when the
hashed artifact changes. Every research-stage artifact change updates this
project's `state/projects/PROJ-755-the-influence-of-chatbot-politeness-on-u.yaml` `updated_at` timestamp.

### VI. Psychometric Measurement Validity

Self-reported trust ratings MUST be collected using established psychometric
scales with documented reliability coefficients. The trust measurement instrument
must be explicitly named in `technical-design/` and its validation properties
must be cited.

### VII. Linguistic Feature Extraction Consistency

Politeness scores computed from chatbot utterances MUST use a documented NLP
method or library with version-pinned dependencies. The same extraction method
MUST be applied to all utterances in the dataset without manual cherry-picking.

## Reproducibility Requirements

- A `requirements.txt` (or `pyproject.toml`) at `projects/PROJ-755-the-influence-of-chatbot-politeness-on-u/code/`
  pins every Python dependency.
- The Code-Execution Agent runs each task in an isolated virtualenv built
  from this requirements file; no global packages are assumed.
- Every notebook or script under `code/` is runnable end-to-end without
  manual intervention.

## Data Hygiene

- Every file under `data/` is checksummed in the project's
  `state/projects/PROJ-755-the-influence-of-chatbot-politeness-on-u.yaml` `artifact_hashes` map.
- Raw data is preserved unchanged; every transformation MUST produce a new file
  with a documented derivation.
- Personally identifying information MUST NOT appear in committed data.

## Verified Accuracy Gate

The Reference-Validator Agent runs at three points:

1. On every artifact write that introduces or modifies citations.
2. Inside the Advancement-Evaluator before awarding any review point.
3. As a blocking gate on the `research_review` → `research_accepted`
   transition.

A reviewer's score MUST be set to 0.0 if the reviewed artifact has any
citation in `unreachable` or `mismatch` status.

## Versioning

This constitution carries its own semver. Initial version:
**1.0.0** — ratified 2026-06-26.

Amendments follow the parent llmXive constitution's amendment procedure
(open a PR; update the version line; record a Sync Impact Report).

## Governance

The Advancement-Evaluator Agent is the sole writer of this project's
`current_stage`. The principal agent for this project is
**flesh_out**.

Review-point thresholds for this project follow `web/about.html`. The
parser at `src/llmxive/config.py` is the single source these numbers
flow from.

**Project ID**: PROJ-755-the-influence-of-chatbot-politeness-on-u | **Field**: psychology | **Ratified**: 2026-06-26