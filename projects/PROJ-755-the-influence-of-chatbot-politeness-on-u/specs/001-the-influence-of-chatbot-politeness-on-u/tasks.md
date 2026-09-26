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

- [ ] T001a [P] **Create** project directories: `data/raw`, `data/processed`, `data/models`, `code`, `code/utils`, `tests`, `tests/contract`, `tests/unit`, `tests/integration`, `docs`, `state`.
 - *Logic*: Use `os.makedirs(path, exist_ok=True)` for each directory. This task is atomic and parallelizable.
 - *Implementation Detail*: Create a Python script `code/utils/setup_dirs.py` that iterates through the list and creates directories.
- [ ] T001b [P] **Verify** directory existence: Run `ls` (Linux/Mac) or `dir` (Windows) and `stat` to confirm all directories from T001a exist. Log output to `data/.setup_verification.log`.
 - *Logic*: This task provides the evidence artifact required by Constitution Principle I (Reproducibility) to prove directories exist on a fresh runner.
 - *Compliance*: Fails if any directory is missing. **CRITICAL**: The generated `data/.setup_verification.log` MUST be committed to the repository as a required artifact for reproducibility proof.
- [ ] T002 [P] Initialize Python project with `code/requirements.txt` (transformers, datasets, statsmodels, pandas, scikit-learn, numpy, pyyaml, tqdm, rpy2, polite, ruff, black, memory_profiler, psutil, scipy).
 - *Logic*: Create `code/requirements.txt` containing ONLY Python packages. `ordinal` is an R package and must NOT be in this list; it is handled in T004b. Removed `textstat` and `evalue` as per plan.md constraints.
 - *ComplianceNote*: `textstat` and `evalue` are explicitly FORBIDDEN per plan.md "Complexity Tracking" which authorizes `polite` as the substitute for LIWC. This task ensures compliance by excluding unauthorized dependencies.
- [ ] T003 [P] Configure linting (ruff/flake8) and formatting (black)
- [ ] T004 [P] Setup CI workflow (GitHub Actions) to install R-base and Python dependencies
- [ ] T004b [P] Setup R environment: Install R packages `lme4` and `ordinal` via system-level commands in CI workflow.
 - *Logic*: R packages cannot be installed via pip. This task ensures `lme4` and `ordinal` are available for `rpy2` execution on the CI runner.
- [X] T006 [P] Implement `code/utils/pii_scanner.py` for PII scanning (regex for email, phone, SSN patterns)
- [X] T007 [P] Implement `code/utils/data_integrity.py` for checksumming and data integrity checks
 - *Logic*: Implementation of the script is parallelizable. However, T007b depends on the *runtime output* (checksums) of T007 execution, not just the script existence.
 - *Note*: T007 is marked [P] for implementation, but T007b is a sequential execution step.
- [ ] T007b [US1] Implement `state/projects/PROJ-755-the-influence-of-chatbot-politeness-on-u.yaml` update logic to record checksums in `artifact_hashes.raw_data` key.
 - *Logic*: Dependency: T007 execution output. Must wait for T007 to complete and generate checksums. T007 is [P] for parallel implementation, but T007b is a sequential step in the execution flow.
 - *Correction*: Removed [P] marker to enforce sequential execution of the update logic if it implies execution; if purely implementation, [P] is retained. Clarified as implementation of the update logic.
- [ ] T008 [P] [Setup] Create `contracts/dataset.schema.yaml` defining Dialogue, Utterance, and User entities.
 - *Logic*: This task MUST be completed before T011. Removed [P] to enforce sequential execution.
 - *Instruction*: Generate the file with the following structure, using `trust_rating` as the primary outcome variable and `quality_rating` as an alias:
   ```yaml
   Dialogue:
     type: object
     properties:
       user_id: string
       dialogue_id: string
       trust_rating: integer (1-5) # Primary outcome per spec scenarios
       quality_rating: integer (1-5) # Alias for trust_rating per spec Key Entities
       # Map quality_rating from requirements to trust_rating if needed
   Utterance:
     ...
   User:
     ...
   ```
 - *Traceability Note*: The `spec.md` Key Entities section defines `quality_rating`, while User Scenarios define `trust_rating`. This task explicitly resolves the spec inconsistency by defining `quality_rating` as a mapped alias for `trust_rating` to satisfy both the Key Entities and User Scenarios requirements.
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

**Goal**: Download **HCI_P2** and **EmpatheticDialogues** datasets (per plan substitution for Persona-Chat). Filter for completeness, and compute mean politeness scores per conversation using `jfiedler/politeness-bert` on CPU.
**Strict Abort Logic**: The pipeline MUST proceed with any dataset that has the required `trust_rating` variable. The pipeline MUST ONLY abort if BOTH datasets fail to download OR BOTH datasets are downloaded but lack the `trust_rating` variable. If a dataset is downloaded but lacks the variable, it is excluded from the merged set, and the pipeline continues with the remaining valid datasets. If only one dataset (HCI_P2) is valid, the pipeline proceeds with that one.

**Independent Test**: Run `code/01_download_and_score.py` on a sample of dialogues; verify `data/processed/scored_dialogues.parquet` exists with `politeness_score` and `trust_rating` columns, and that excluded dialogues are logged.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T013 [P] [US1] Contract test for dataset schema validation in `tests/contract/test_dataset_schema.py`
- [X] T014 [P] [US1] Unit test for politeness scoring logic (batched inference) in `tests/unit/test_scoring.py`

### Implementation for User Story 1

#### Download & Validate Tasks (Merged for Atomicity)
- [X] T015 [US1] **Download, Validate, and Filter All Datasets**: Implement `code/01_download_and_score.py` to fetch **HCI_P2**, **EmpatheticDialogues**, and **Persona-Chat**.
 - *Logic*:
 1. **Sources**: `huggingface/datasets/hci_p2`, `emotional-reality/empathetic_dialogues`, `nlp-projects/persona-chat`. (Reference: plan.md "Dataset Constraint Resolution" for authorized sources).
 2. **Action**: Download raw data to `data/raw/{source}/raw_data.parquet`.
 3. **Traceability**: **MUST attempt Persona-Chat first**. If Persona-Chat is **unverified** OR lacks the `trust_rating` (or `quality_rating`) variable, **EXCLUDE IT** and log the specific reason in `data/raw/validation_status.json` (e.g., "Persona-Chat excluded: missing trust_rating variable" or "Persona-Chat excluded: unverified source").
 4. **Validate**: Verify `trust_rating`, `user_id`, `dialogue_id` columns exist in each source.
 5. **Granular Exclusion**: If a source has the `trust_rating` column, filter out individual dialogues where `trust_rating` is missing. Log the count of excluded dialogues per source.
 6. **Source Exclusion**: If a source lacks the `trust_rating` column entirely, exclude the entire source and log "excluded" in `data/raw/validation_status.json`.
 7. **Abort**: If ALL sources are excluded, abort pipeline with "NO_VALID_DATA_SOURCE".
 8. **Mapping**: If `quality_rating` is present but `trust_rating` is missing, map `quality_rating` to `trust_rating`. If `trust_rating` is missing but `quality_rating` exists, map `quality_rating` to `trust_rating` (bidirectional alias).
 9. **Store**: Save raw data with checksums. **The script `code/01_download_and_score.py` is the single source responsible for writing `data/raw/validation_status.json` with the exact schema keys.**
 - *Deliverable*: `data/raw/hci_p2/filtered.parquet`, `data/raw/empathetic_dialogues/filtered.parquet`, `data/raw/validation_status.json` (with explicit exclusion reasons).

#### Transform & Score Tasks
- [ ] T018 [P] [US1] **Transform to Target Schema**: Transform filtered datasets to match target schema.
 - *Logic*:
 1. **Dependency**: T015.
 2. **Define Schema**: Target schema columns: `user_id` (str), `dialogue_id` (str), `trust_rating` (int), `age` (int/str), `gender` (str), `utterances` (list), `source_dataset` (str), `conversation_length` (int, word count).
 3. **Transform**: Transform each filtered dataset to match schema. **This task can run in parallel per source.**
 4. **Output**: Save transformed datasets to `data/processed/transformed_{source}.parquet`.
 - *Deliverable*: `data/processed/transformed_hci_p2.parquet`, `data/processed/transformed_empathetic_dialogues.parquet`.
- [ ] T019a [US1] **Merge Transformed Datasets**: Merge all valid transformed sources into a single dataset.
 - *Logic*:
 1. **Dependency**: T018 (all sources transformed). **Strictly requires T018 outputs.**
 2. **Input**: `data/processed/transformed_*.parquet`.
 3. **Merge**: Concatenate all valid transformed sources into `data/processed/merged_dialogues.parquet`.
 4. **Barrier Note**: T018 is [P] per source, but T019a acts as a **global barrier** waiting for all T018 instances. This creates a serialization bottleneck where T019a cannot start until the slowest T018 instance finishes.
 5. **Deliverable**: `data/processed/merged_dialogues.parquet`.
- [ ] T019b [US1] **Compute Politeness Scores**: Load `jfiedler/politeness-bert` and compute scores for utterances.
 - *Logic*:
 1. **Dependency**: T019a.
 2. **Score**: Load `jfiedler/politeness-bert` (Revision: `main`, Cache: `data/models`). Verify model file size ≤ 100MB. Iterate through utterances in batches. Compute politeness scores; assign NaN to failures and log counts.
 3. **Memory Check**: Use `psutil` to monitor **peak RSS** (Resident Set Size). If peak RSS > 6.0 GB, raise `MemoryError` with message "Dataset exceeds memory limit (6.0 GB peak RSS). Please reduce sample size or use streaming."
 4. **GPU Escape Hatch**: If `MemoryError` is raised or CUDA OOM occurs, **trigger a re-run command for the Kaggle GPU environment** using the specific script: `kaggle-kernels run --gpu ...` (as defined in the CI workflow). This is the authorized fallback mechanism.
 5. **Save**: Save scored dataset to `data/processed/scored_dialogues.parquet`.
 - *Note*: This task separates scoring from merging/standardization to isolate inference logic.
 - *Deliverable*: `data/processed/scored_dialogues.parquet`.
- [ ] T019c [US1] **Standardize Scores**: Calculate mean/std and apply global z-scoring.
 - *Logic*:
 1. **Dependency**: T019b. (Requires scores from T019b to compute global mean/std).
 2. **Model Constraint**: Explicitly use scores generated by `jfiedler/politeness-bert` (from T019b).
 3. **Global Standardization**: Calculate mean and standard deviation of `politeness_score` across ALL dialogues in the merged dataset. Apply z-scoring globally.
 4. **Deterministic Output**: Store the standardized value as `mean_politeness_score` (single column, global).
 5. **Save**: Save final standardized dataset to `data/processed/filtered_dialogues.parquet`.
 - *Deliverable*: `data/processed/filtered_dialogues.parquet` (contains `mean_politeness_score`).

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: Data Verification Gate (Pre-US3)

**Purpose**: Validate sample sizes for subgroup analysis before attempting US3. This task must pass for US3 to proceed.

- [ ] T012 [Gate] **Sample Size Verification** for Subgroups and Primary Analysis.
 - *Logic*:
 1. **Dependency**: T019c.
 2. Load the **merged** dataset (`data/processed/filtered_dialogues.parquet`).
 3. **Check Subgroups**: Count dialogues per `age` group and `gender` group.
 4. **Gate Condition**: If ANY subgroup (e.g., Male, Female, Age 18-25) has n < 30, log that US3 will be skipped for that specific group.
 5. **Pipeline Logic**: If primary analysis (all data) has n < 30, abort. Otherwise, proceed to US2/US3, but US3 subgroup tasks will be skipped for insufficient groups.
 6. **Conditional Gate**: This task is a **Conditional Gate**. It gates ONLY T034 (Subgroup Analysis). T032a and T033 (US3 Robustness) can proceed independently of this gate.
 7. Generate `data/processed/validation_report.json` with schema:
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
 - *Note*: This task is a **Conditional Gate**. It blocks T034 (Subgroup Analysis) but does NOT block T032a/T033 (Robustness). US3 starts before T012, but T034 waits for T012.

**Checkpoint**: Data verified - US2 implementation can proceed independently; US3 is gated by T012 for subgroup tasks only.

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
 - *Logic*: Dependency: T025. Define `conversation_length` as **word count** (per spec assumption).
- [ ] T027a [US2] **CLMM Fitting (Single Run)**: Fit primary CLMM and record convergence status; fit simplified ordinal regression (remove random effects) if CLMM fails.
 - *Logic*:
 1. **Dependency**: T026.
 2. **Fit Primary**: Fit CLMM via `rpy2` (formula: `trust_rating ~ politeness + conversation_length + (1|user_id)`) with `lme4`.
 3. **Check Convergence**: Calculate convergence status.
 4. **Fallback Logic**: If `convergence_status` is "failed", fit simplified ordinal regression (remove random effects).
 5. **Record Status**: Save `data/processed/project_status.json` with fields: `convergence_status` ("success" | "failed"), `model_type` ("clmm" | "ordinal_fixed_effects"), `error_message` (if failed), `timestamp`.
 6. **SC-003 Metric**: Explicitly note that fallback models count as "failed convergence" in the SC-003 metric calculation (denominator includes all runs, numerator counts successful CLMMs).
 7. **Save Results**: Save results (CLMM or fallback) to `data/processed/clmm_primary_results.csv` with coefficients, SEs, p-values, and convergence metrics.
 8. **Save Model Object**: Save the fitted model object to `data/processed/clmm_model.rds` using `robjects.r['saveRDS'](model, 'path', version=3)` via `rpy2` for cross-platform compatibility.
 9. **Aggregation**: Append the run status (success/fail) to `data/processed/convergence_report.csv` to enable calculation of the convergence rate across multiple sensitivity analysis runs.
 - *Note*: This task handles a single run. T027b will iterate this.
 - *Deliverable*: `data/processed/clmm_primary_results.csv`, `data/processed/project_status.json`, `data/processed/clmm_model.rds`, and `data/processed/convergence_report.csv`.
- [ ] T027b [US2] **Sensitivity Analysis Loop**: Iterate T027a N times to calculate convergence rate.
 - *Logic*:
 1. **Dependency**: T027a.
 2. **Loop**: Run T027a N times (N=20 or as defined by sensitivity analysis requirements) with **specific data perturbations (e.g., bootstrapping) or parameter sweeps**. **Do NOT simply re-run on the same data**; valid sensitivity analysis requires varying inputs or parameters.
 3. **Aggregate**: Read `data/processed/convergence_report.csv` after N runs.
 4. **Calculate Rate**: Compute convergence rate = (successful CLMMs / N).
 5. **Verify**: Check if rate ≥ 0.95 (SC-003). Log "SC-003 MET" or "SC-003 NOT MET".
 6. **Save**: Save final convergence rate to `data/processed/convergence_rate.json`.
 - *Deliverable*: `data/processed/convergence_rate.json`.
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
 - *Note*: This task ensures the final file is written after all corrections. **Constraint: T029 must complete before T033b (US3 correlation) begins.**
 - *Deliverable*: `data/processed/clmm_results.csv`.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 6: User Story 3 - Robustness and Subgroup Analysis (Priority: P3)

**Goal**: Validate findings with the **LIWC-2015 Politeness Dictionary** (or fallback) and conduct subgroup analyses by age/gender (n ≥ 30 guard).

**Independent Test**: Run `code/03_robustness_analysis.py`; verify `data/processed/robustness_results.csv` exists, correlation (r ≥ 0.80) is calculated, and subgroup exclusions are logged.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T030 [P] [US3] Unit test for lexicon-based scoring logic in `tests/unit/test_lexicon_scoring.py`
- [X] T031 [P] [US3] Integration test for subgroup filtering logic (n ≥ 30) in `tests/integration/test_subgroup.py`

### Implementation for User Story 3

- [ ] T032a [US3] **Mandatory LIWC-2015 Acquisition (with Fallback)**: Implement `code/03_robustness_analysis.py` to attempt loading the LIWC-2015 dictionary.
 - *Logic*:
 1. **Dependency**: T019c (Completion of US1). Load `filtered_dialogues.parquet`.
 2. **Citation Requirement**: Include explicit citations to HCI literature (Nass & Moon; Bickmore & Picard) validating `trust_rating` as a proxy for 'trust'. Store citations in `data/processed/citations.json` and in the script docstring.
 3. **Attempt LIWC Acquisition**: Attempt to load LIWC-2015 from `data/models/liwc_2015/liwc_2015_dictionary.txt` or via `huggingface_hub.hf_hub_download` from repo `LIWC-2015/LIWC-2015` (filename: `liwc_2015_dictionary.txt`).
 4. **Waiver Logic**: If acquisition fails, **DO NOT FAIL**. Log "FORMAL WAIVER: FR-005 LIWC-2015 unavailable" to `data/processed/robustness_status.json`. Immediately execute fallback: Use `polite` library as the approved substitute (per plan.md). Log "FR-005 Partially Met (Fallback)". **This log entry serves as the formal waiver record.**
 5. **Scoring**: If successful, apply LIWC-2015. If fallback, apply `polite`. Compute mean scores per dialogue.
 6. **Save Scores**: Save scores to `data/processed/robustness_scores_lexicon.parquet`.
 7. **Status File**: Save `data/processed/robustness_status.json` with schema:
 ```json
 {
 "source_used": "liwc" | "polite",
 "liwc_acquisition_failed": true/false,
 "fallback_reason": null | "licensing" | "missing_file",
 "waiver_logged": true,
 "fulfillment_status": "full" | "partial"
 }
 ```
 - *Traceability*: Explicitly addresses **FR-005** (Robustness) using the mandatory classifier or fallback with a formal waiver log.
 - *Note*: This task does NOT block the pipeline; if LIWC fails, `polite` is used immediately. The pipeline continues to T033.
- [ ] T033 [US3] **Re-fit CLMM**: Re-fit CLMM on lexicon scores.
 - *Dependency*: Requires T032a (must succeed in scoring). **Constraint: T033 does NOT depend on T029.**
 - *Logic*:
 1. **Check**: Use `data/processed/robustness_scores_lexicon.parquet`.
 2. **Fit**: Re-fit CLMM using the lexicon-based politeness scores.
 3. **Save**: Save model object to `data/processed/robustness_model.rds` (RDS format, version=3).
 - *Deliverable*: `data/processed/robustness_model.rds`.
- [ ] T033b [US3] **Generate Predicted Scores & Correlate**: Calculate **Spearman** rank correlation of per-dialogue predicted quality scores.
 - *Logic*:
 1. **Dependency**: T033, T027a (for primary model object), T029 (for results consistency). **Sequential Dependency: T027a -> T033 -> T033b.**
 2. Load `data/processed/clmm_model.rds` (from T027a) for **primary** predictions.
 3. Load `data/processed/robustness_model.rds` (from T033) for **robust** predictions.
 4. Generate `predicted_quality` scores for each dialogue using both models via the `predict()` method on the original input data.
 5. Save per-dialogue predictions to `data/processed/robustness_predictions.csv` (columns: `dialogue_id`, `primary_predicted`, `robust_predicted`).
 6. **Target Variable**: Use the available robustness model (LIWC or polite) for the correlation.
 7. **Calculate Correlation**: Calculate **Spearman rank correlation** using `scipy.stats.spearmanr(x, y, nan_policy='omit')` between `primary_predicted_quality` and `robust_predicted_quality`.
 8. **Calculate P-value and N**: Compute the p-value and sample size (N) for the correlation.
 9. **Rationale**: Spearman is used for ordinal data consistency (Likert 1-5) to match SC-004 intent.
 10. **Verify**: Check if `correlation_r` >= 0.80. Log "SC-004 MET" or "SC-004 NOT MET".
 11. Save `correlation_r`, `p_value`, `n`, and `source_used` to `data/processed/robustness_summary.json`.
 - *Note*: Explicitly generate per-dialogue predicted quality scores via CLMM prediction before correlation calculation. This task ALWAYS produces the correlation metric.
 - *Dependency*: T033, T027a, T029.
 - *Deliverable*: `data/processed/robustness_summary.json`.
- [ ] T034 [US3] **Subgroup Analysis**: Split data by age/gender.
 - *Dependency*: Requires T012 (Sample Size Verification) to have reported `subgroups_eligible`. **Also requires T019c (US1 completion)**. **Dependency: T012 (Gate Pass)**.
 - *Logic*:
 1. **Runtime Check**: Verify `data/processed/validation_report.json` exists and `gate_status` != "failed". If not, skip T034 and log exclusion.
 2. **Check Columns**: If `age` or `gender` columns are missing, log "Subgroup analysis skipped: missing demographic columns" and exit.
 3. **Filter**: Exclude groups with n < 30 (as per T012), log exclusions.
 4. **Fit**: Fit separate CLMMs for valid subgroups and test interaction terms.
 5. **Output**: Save each subgroup model to `data/processed/subgroup_clmm_{group}.csv`.
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
- [ ] T042 [P] Configure CI workflow for full pipeline execution on GitHub Actions.
 - *Logic*: Create `.github/workflows/ci.yml` to install R, Python deps, and run the full pipeline.
- [ ] T042b [P] Execute full pipeline on GitHub Actions and capture metrics.
 - *Logic*: Run the CI workflow. Verify runtime < 6h and RAM < 6.0 GB. Capture metrics.
 - *Dependency*: T042.
 - *Deliverable*: `data/processed/performance_metrics.json`.
 - *Schema Definition*: The deliverable `data/processed/performance_metrics.json` MUST include:
   - `runtime_seconds`: integer
   - `peak_memory_gb`: float
   - `verdict`: "PASS" | "FAIL"
   - `reason`: string (e.g., "RAM exceeded 6.0 GB" or "Runtime within limits")
   - *Evaluation Logic*: If `peak_memory_gb` > 6.0, `verdict` is "FAIL" and `reason` is "RAM exceeded 6.0 GB". Otherwise, `verdict` is "PASS".
- [ ] T043 [P] Generate `docs/performance_report.md` and `docs/performance_verdict.md` with explicit schema.
 - *Schema*: `runtime_seconds`, `peak_memory_gb`, `convergence_rate`, `status`.
 - *Logic*: Collect metrics from `data/processed/performance_metrics.json` (generated by T042b).
 - **Verdict Logic**: Compare `runtime_seconds` against a predefined time threshold and `peak_memory_gb` against 6.0 GB. Generate `docs/performance_verdict.md` with a clear "PASS" or "FAIL" status and reasons.
 - *Dependency*: T042b.
 - *Deliverable*: `docs/performance_report.md`, `docs/performance_verdict.md`.

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
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Requires output from US1 and US2 for comparison. **Explicitly depends on T012 passing (or partial status with available fields) for T034.** **Constraint: T029 (US2 finalization) must complete before T033b (US3 correlation) begins.**

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
- **Constraint**: All BERT inference must be CPU-only (no CUDA) unless GPU Escape Hatch is triggered; use batch processing to stay under available RAM limits.
- **Constraint**: Dataset source MUST include HCI_P2 and EmpatheticDialogues (per plan substitution). Abort only if ALL fail.
- **Constraint**: Subgroup analysis (US3) is strictly gated by T012 (Sample Size Verification, n ≥ 30).
- **Constraint**: Robustness classifier (US3) MUST use LIWC-2015; if unavailable, fallback to `polite` library and log "Partial Fulfillment" with a formal waiver.
- **Constraint**: Convergence rate (SC-003) is measured by the primary run's convergence status; fallback models count as "failed convergence" in the metric calculation.
- **Constraint**: Memory limit is ~6GB; if exceeded, the pipeline MUST raise a `MemoryError` and stop (no Dask fallback), triggering GPU Escape Hatch.
- **Constraint**: T029 (US2 finalization) must complete before T033b (US3 correlation) begins to ensure data consistency.
- **Constraint**: T018 (Transform) is marked [P] for parallel execution per source, but T019a strictly requires all T018 outputs before merging.