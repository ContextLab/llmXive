---
description: "Task list for feature implementation"
---

# Tasks: Investigating the Predictive Power of Machine Learning for Identifying Novel Phase-Change Materials

**Input**: Design documents from `/specs/001-investigating-the-predictive-power-of-ma/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only if explicitly requested in the feature specification.

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

- [X] T001a [P] Create data directories: `data/raw`, `data/processed`, `data/results`, `data/external`. **Deliverable**: directories exist; verified by `tests/unit/test_directories.py`.
- [X] T001b [P] Create code directories: `code/data`, `code/models`, `code/utils`, `code/validate`. **Deliverable**: directories exist; verified by `tests/unit/test_directories.py`.
- [X] T001c [P] Create test directories: `tests/unit`, `tests/integration`, `tests/contract`. **Deliverable**: directories exist; verified by `tests/unit/test_directories.py`.
- [X] T001d [P] Verify project directory structure via pytest (`tests/unit/test_directories.py` checks all `data/`, `code/`, and `tests/` subfolders). **Deliverable**: `tests/unit/test_directories.py`.
- [X] T002 Initialize Python project with `pymatgen`, `scikit-learn`, `pysr`, `shap`, `pandas`, `numpy`, `matplotlib`, `requests`, `pyyaml`, `mp-api`, `datasets` dependencies. **Deliverable**: `requirements.txt` pinning all versions.
- [X] T003a [P] Configure linting in `pyproject.toml`: Add `[tool.black]` and `[tool.isort]` sections with standard project settings. **Deliverable**: `pyproject.toml`.
- [X] T003b [P] Configure formatting in `.flake8`: Create file with `max-line-length = 88` and appropriate ignore settings. **Deliverable**: `.flake8`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented. Includes Data Hygiene, Fallback Logic, and Streaming.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Setup `config.yaml` for API keys, random seeds, time/memory constraints, and `top_n` (default: 10, note: "Research Decision Required"). **Deliverable**: `config.yaml`.
- [X] T005 [P] Implement basic logging infrastructure (`code/utils/logger.py`) and error handling in `code/utils/`. **Deliverable**: `code/utils/logger.py`.
- [X] T005d [P] Add unit test for logger (`tests/unit/test_logger.py`) that writes and reads a log entry. **Deliverable**: `tests/unit/test_logger.py`.
- [X] T008 Implement `code/utils/stability_checks.py` for NaN/Inf validation and memory monitoring. **Constraint**: Dedicated to numerical stability only; no sensitivity analysis logic. **Deliverable**: `code/utils/stability_checks.py`.
- [X] T033 [P] [US1] **Revision**: Implement `code/data/fetch_materials.py` with robust fallback to verified `matbench` dataset on API failure/rate-limit. **Constraint**: MUST NOT raise error on fetch failure; MUST log fallback and proceed. **Deliverable**: `code/data/fetch_materials.py`.
- [X] T034 [P] [US1] **Revision**: Implement `code/data/fetch_nist_data.py` with fallback to `melting_point` target if NIST overlap < 500. **Constraint**: MUST NOT raise `DataInsufficientError`; MUST flag fallback in `target_decision.json`. **Deliverable**: `code/data/fetch_nist_data.py`.
- [X] T035 [P] [US1] **Revision**: Implement Streaming Data Loader in `code/data/compute_descriptors.py` using `datasets.load_dataset(..., streaming=True)` and chunked processing. **Constraint**: MUST handle >7 GB datasets without loading full data into RAM. **Deliverable**: `code/data/compute_descriptors.py`.
- [X] T036 [P] [US1] Add Unit Test for Streaming Logic (`tests/unit/test_streaming_descriptors.py`) to verify chunked processing and memory constraints. **Deliverable**: `tests/unit/test_streaming_descriptors.py`.
- [X] T037 [P] [US1] Add Contract Test for Real Data Validation (`tests/contract/test_real_data_integrity.py`) to assert no synthetic placeholders. **Deliverable**: `tests/contract/test_real_data_integrity.py`.
- [ ] T006b [P] **Pending Implementation (Artifact missing)**: Define JSON schema for `target_decision.json` (`contracts/target_decision.schema.yaml`). **Deliverable**: `contracts/target_decision.schema.yaml`.
- [ ] T007 [P] **Pending Implementation (Artifact missing)**: Create dataset schema (`contracts/dataset.schema.yaml`) covering both `latent_heat` and `melting_point`. **Deliverable**: `contracts/dataset.schema.yaml`.
- [ ] T006c [P] **Pending Implementation (Artifact missing)**: Define JSON schema for `fallback_decision.json` (`contracts/fallback_decision.schema.yaml`). **Dependency**: Runs after T006b. **Deliverable**: `contracts/fallback_decision.schema.yaml`.
- [ ] T005a [P] [US1] **Pending Implementation (Artifact missing)**: Execute `code/data/fetch_materials.py` (T033) to fetch data. **Dependency**: T033, T004. **Deliverable**: `data/raw/materials_project_data.json`.
- [ ] T005b [P] [US1] **Pending Implementation (Artifact missing)**: Execute `code/data/fetch_nist_data.py` (T034) to fetch NIST data. **Dependency**: T034, T004. **Deliverable**: `data/raw/nist_data.json`.
- [ ] T005c [P] [US1] **Pending Implementation (Artifact missing)**: Implement `code/data/target_consistency_check.py` to compute correlation, decide target, write `data/results/target_decision.json`. **Dependency**: T005a, T005b. **Deliverable**: `code/data/target_consistency_check.py`, `data/results/target_decision.json`.
- [ ] T006d [P] [US1] **Pending Implementation (Artifact missing)**: Generate `data/results/data_manifest.json` from raw datasets. **Dependency**: T005a, T005b, T005c. **Deliverable**: `data/results/data_manifest.json`.
- [ ] T006a [P] [US1] **Pending Implementation (Artifact missing)**: Execute `code/data/target_consistency_check.py` to produce `data/results/target_decision.json`. **Dependency**: T005c, T006b, T006c. **Deliverable**: `data/results/target_decision.json`.
- [ ] T006a_verify [P] [US1] Verify that `data/results/target_decision.json` exists and conforms to its schema. **Deliverable**: `tests/contract/test_target_decision_schema.py`.
- [ ] T008a [P] **Pending Implementation (Artifact missing)**: Generate SHA256 checksums for all raw data files after fetch and record them in `data/checksums.txt`. **Dependency**: T005a, T005b. **Deliverable**: `data/checksums.txt` (raw entries), `code/utils/checksum.py`.
- [ ] T008b [P] **Pending Implementation (Artifact missing)**: Generate SHA256 checksums for all processed data files after feature engineering and record them in `data/checksums.txt`. **Dependency**: T012. **Deliverable**: `data/checksums.txt` (processed entries).
- [X] T030a [P] Record checksum generation as part of pipeline (invoke after T005c and T012). **Deliverable**: updates to `code/main.py`.
- [ ] T013 [P] [US1] **Pending Implementation (Artifact missing)**: Implement `code/data/fetch_literature_pcm.py`: Fetch known PCMs from `matbench/literature_pcm_validation_set`. **Deliverable**: `code/data/fetch_literature_pcm.py`, `data/external/literature_pcms_raw.csv`.
- [~] T013a [P] [US1] **Pending Implementation (Artifact missing)**: Implement `code/data/map_literature_pcm.py`: Map literature PCMs to MP IDs. **Deliverable**: `code/data/map_literature_pcm.py`, `data/external/literature_pcms_mapped.csv`.
- [~] T012 [P] [US1] **Pending Implementation (Artifact missing)**: Implement `code/data/compute_descriptors.py` (T035) to generate elemental/graph features with streaming. **Dependency**: T005a, T035. **Deliverable**: `code/data/compute_descriptors.py`, `data/processed/graph_features.npy`.
- [X] T014 [P] [US1] **Pending Implementation (Artifact missing)**: Implement VIF analysis in `code/utils/collinearity_utils.py`. **Deliverable**: `code/utils/collinearity_utils.py`.
- [X] T015 [P] [US1] **Pending Implementation (Artifact missing)**: Create `code/main.py` orchestrating fetch → descriptors → VIF → save processed CSV. **Dependency**: T012, T014. **Deliverable**: `code/main.py`.

---

## Phase 3: User Story 1 - Retrieve and Preprocess Materials Data (Priority: P1) 🎯 MVP

**Goal**: Retrieve curated Materials Project subset, compute descriptors, prepare dataset within 7 GB RAM.

- [X] T010 [P] [US1] Integration test for data pipeline (`tests/integration/test_pipeline.py`). **Depends on** T015.
- [X] T009 [P] [US1] Contract test for dataset schema (`tests/contract/test_dataset_schema.py`). **Depends on** T007.
- [~] T030c [P] [US1] **Revision**: Implement Pearson correlation analysis in `code/evaluate.py`; output `data/results/correlation_report.json` with key `pearson_r`. **Constraint**: Do NOT enforce a hard pass condition (e.g., `>= 0.2`). Log value for research analysis only. **Depends on** T012. **Deliverable**: `code/evaluate.py`, `data/results/correlation_report.json`.
- [X] T030d [P] [US1] Add unit test `tests/unit/test_correlation_analysis.py` to assert report exists and structure is correct (no threshold check). **Depends on** T030c.

---

## Phase 4: User Story 2 - Train Baseline and Interpretable Models (Priority: P2)

**Goal**: Train RF, GB, SHAP, and PySR models on CPU within time limits; achieve R² > 0.0.

- [~] T017a [P] [US2] `code/models/train_random_forest.py` → `data/models/rf_model.pkl`; logs R² and execution time; fails if >2 h or R² ≤ 0.0.
- [~] T017b [P] [US2] `code/models/train_gradient_boosting.py` → `data/models/gb_model.pkl`; same constraints.
- [~] T017c [P] [US2] `code/models/verify_baseline_metrics.py` → `data/results/baseline_verification.json`.
- [~] T017d [P] [US2] `code/models/train_shap_analysis.py` → `data/models/shap_summary.json`.
- [~] T019 [P] [US2] `code/models/train_symbolic.py` using PySR; output `data/models/symbolic_formulas.txt`; flags limitation if R² ≤ 0.0.
- [X] T020a [P] [US2] **Revision Required**: `code/models/evaluate.py` → compute R², perform initial evaluation (may use wrong test). **Deliverable**: `code/models/evaluate.py` (initial version).
- [X] T032b [P] [US2] **Revision**: Update `code/models/evaluate.py` to replace any Diebold‑Mariano test with a paired t‑test, ensuring alignment with SC‑002. **Dependency**: T020a. **Deliverable**: `code/models/evaluate.py` (corrected version).
- [~] T020b [P] [US2] **Corrected Evaluation**: Re-run `code/models/evaluate.py` (corrected version) to produce `data/results/model_comparison.json`. **Dependency**: T032b. **Deliverable**: `data/results/model_comparison.json`.
- [X] T016 [P] [US2] Contract test for model output schema (`tests/contract/test_model_output_schema.py`). **Depends on** T020b. **Note**: Ensure T020b uses paired t-test.

---

## Phase 5: User Story 3 - Validate Governing Factors and Sensitivity (Priority: P3)

**Goal**: Validate rules against external PCMs, perform sensitivity analysis, finalize associational framing.

- [ ] T023a [P] [US3] Generate validation config (`data/results/validation_config.json`) with `top_n` (default 10). **Depends on** T013a.
- [ ] T023 [P] [US3] External validation (`code/validate/validate_external.py`) → updates `research.md` with ranking accuracy. **Depends on** T005c, T007, T019, T020b, T013a, T023a.
- [ ] T024 [P] [US3] Sensitivity analysis (`code/validate/sensitivity_analysis.py`) → `data/results/sensitivity_report.json`. **Depends on** T023.
- [ ] T040 [P] [US3] **Revision**: Extend `code/utils/collinearity_utils.py` to output a detailed `data/results/collinearity_diagnostic.json` listing all flagged variable pairs and VIF scores. **Dependency**: T014. **Deliverable**: `code/utils/collinearity_utils.py`, `data/results/collinearity_diagnostic.json`.
- [ ] T026a [P] [US3] Generate correlation analysis report section in `research.md` (uses T030c output). **Depends on** T005c.
- [ ] T026b [P] [US3] Generate model comparison report section in `research.md` (uses T020b). **Depends on** T020b.
- [ ] T026c [P] [US3] Generate final report in `research.md` and `paper/` drafts, including assumptions. **Depends on** T026a, T026b.
- [ ] T027 [P] [US3] Run reproducibility check: generate `data/results/reproducibility_report.json` confirming all artifacts have checksums and are traceable. **Depends on** T008a, T008b, T030a, T012, T017a, T017b, T019, T023, T024.
- [ ] T022 [P] [US3] Integration test for validation pipeline (`tests/integration/test_validation.py`). **Depends on** T023 and T024.

---

## Phase 6: Polish & Cross‑Cutting Concerns

**Purpose**: Improvements affecting multiple user stories.

- [ ] T028 [P] Update documentation:
 - `docs/architecture.md` with pipeline diagram.
 - `quickstart.md` with step-by-step commands and expected outputs.
 - Add `tests/integration/test_docs_updated.py` to verify sections exist. **Depends on** T026c.
- [ ] T029 [P] Code cleanup and refactoring:
 - Run `ruff` and `isort` across `code/`.
 - Produce lint report `data/reports/lint_report.txt`.
 - CI must pass linting. **Depends on** T028.
- [ ] T030 [P] Additional unit tests for descriptor computation and stability checks:
 - `tests/unit/test_compute_descriptors.py`
 - `tests/unit/test_stability_checks.py`
 - Require ≥ 80 % coverage. **Depends on** T012.
- [ ] T031 [P] Run `quickstart.md` validation:
 - Execute `python -m code.main --config config.yaml`.
 - Verify creation of `data/results/pipeline_success.json`.
 - Include `tests/integration/test_quickstart.py`. **Depends on** T028.
- [ ] T032 [P] Feasibility monitor:
 - Log total runtime and peak memory usage; assert ≤ limits in `config.yaml`.
 - Output `data/results/feasibility_report.json`. **Depends on** T031.

### New Cross‑Cutting Tasks

- [ ] T031a [P] Implement config loader (`code/utils/config.py`) to read `config.yaml` and expose `max_time_seconds` and `max_memory_gb`. **Depends on** Phase 1.
- [ ] T032a [P] Add unit test `tests/unit/test_config_loader.py` ensuring correct parsing of limits. **Depends on** T031a.

---

## Phase 7: Validation & Final Polish

**Purpose**: Final validation and readiness for research review. No revision tasks here; all revisions moved to earlier phases.

- [ ] T038 [P] [US2] **Revision**: Update PySR Execution Config in `code/models/train_symbolic.py` to explicitly set `time_limit` and `niterations` (CPU-tractable, < 4h) and log budget. **Dependency**: T019.
- [ ] T039 [P] [US3] **Revision**: Refine Sensitivity Analysis Sweep in `code/validate/sensitivity_analysis.py` to perform fine-grained sweep over threshold range and output exact values in `sensitivity_report.json`. **Dependency**: T024.