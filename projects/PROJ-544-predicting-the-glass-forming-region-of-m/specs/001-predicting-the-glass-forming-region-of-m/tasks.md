# Tasks: Predicting the Glass Forming Region of Multi-Component Alloys via Machine Learning

**Input**: Design documents from `/specs/001-predicting-the-glass-forming-region/`
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
*Note: These tasks provide required infrastructure and are not directly mapped to a specific FR/SC.*

- [X] T001a Create directory `code/` with a README describing its purpose. <!-- infrastructure task -->
- [X] T001b Create sub‑directories `code/descriptors/`, `code/models/`, `code/config/`. <!-- infrastructure task -->
- [X] T001c Create directories `data/`, `data/raw/`, `data/derived/`, `data/samples/`, `results/`, `results/shap_plots/`, `logs/`, `state/`, `contracts/`. <!-- infrastructure task -->

- [X] T002 Initialize Python 3.11 virtual environment (`python -m venv.venv`) and create `requirements.txt` pinned to scikit‑learn==1.5.*, pandas==2.2.*, numpy==1.26.*, shap==0.45.*, pymatgen==2024.*, dscribe==2.3.*, pyyaml==6.0.*, imbalanced-learn==0.12.*, pytest==8.3.*. <!-- infrastructure task -->

- [X] T003 Configure linting and formatting: create `.pre-commit-config.yaml` with ruff and black hooks, install pre‑commit, and run `pre-commit install`. <!-- infrastructure task -->

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Implement JSON‑Schema contracts for `alloy_composition`, `descriptor_vector`, and `model_performance_record` in `contracts/` (e.g., `alloy_composition.schema.json`). <!-- foundational task; schema contracts are necessary infrastructure -->
- [X] T005 Create `scripts/generate_synthetic_data.py` that deterministically generates a CSV `data/samples/synthetic_alloys.csv` with a substantial number of rows, balanced between glass and crystalline structures, using a fixed random seed for reproducibility

The research question is: Can large language models be prompted to perform few-shot learning on a novel task with minimal examples? The method will involve prompting a large language model with varying numbers of examples and evaluating its performance on a held-out test set. (Brown et al., 2020). and writes the seed in a header comment. <!-- foundational task for CI testing -->
- [X] T006 Implement `scripts/download_and_verify.py`:
 - Uses `requests` to download datasets from the ucimlrepo package and Materials Project API.
 - Verifies each file against a SHA‑ checksum listed in `data/manifest.sha256`.
 - Retries failed downloads up to 3 times with exponential back‑off.
 - Logs progress and errors to `logs/download.log`. <!-- foundational data acquisition -->
- [X] T007 Create `code/config/env.yaml` containing:
 - Fixed random seeds for numpy, sklearn, shap.
 - Memory limit flag (`max_ram_gb: sufficient for model and data`).

The research question is: Can large language models be effectively fine-tuned for specialized tasks with limited computational resources?
The method is: We will explore parameter-efficient fine-tuning (PEFT) techniques, specifically LoRA (Hu et al., 2021), on a moderately sized language model.
References: Hu et al. (2021). LoRA: Low-Rank Adaptation of Large Language Models. arXiv:2106.09685.
 - A sanity‑check script `scripts/run-ci.sh --dry-run` that attempts to execute **every** script under `code/` and `scripts/` without manual input; logs success to `logs/env_check.log`. This satisfies Constitution I’s requirement that all scripts be runnable end‑to‑end. <!-- environment configuration and verification -->

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Compute thermodynamic descriptors for alloy compositions (Priority: P1) 🎯 MVP

**Goal**: Compute atomic size mismatch, mixing enthalpy, and electronegativity variance from elemental stoichiometries

**Independent Test**: Provide a CSV of alloy compositions and verify descriptor values match known calculations for benchmark alloys (e.g., Cu‑Zr systems)

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T008 [US1] Contract test for descriptor output schema in `tests/contract/test_descriptor_schema.py` (must run before implementation).
- [X] T009 [US1] Unit test for elemental symbol validation against periodic table in `tests/unit/test_validate_elements.py` (must run before implementation).

### Implementation for User Story 1

- [X] T010 [US1] Implement `code/descriptors/validate_elements.py`:
 - Reads a composition CSV, checks each symbol against pymatgen's periodic table.
 - Outputs two files: `data/derived/valid_elements.csv` and `data/derived/invalid_elements.csv`.
 - **FR‑002** compliance: validates all elemental symbols before any descriptor computation.
- [X] T011 [US1] Implement `code/descriptors/compute.py`:
 - Calculates the three descriptors, writes `data/derived/descriptor_vector.csv`.
 - Records descriptor‑calculation parameters in `code/descriptors/provenance.yaml`.
 - Triggers a SHA‑256 checksum entry for the descriptor file in `state/artifact_hashes.yaml` whenever parameters change, satisfying **Constitution VI**.
- [ ] T012 [US1] Implement fallback logic in `code/descriptors/utils.py`:
 - For missing elemental properties, selects the nearest periodic‑table neighbor, logs a warning to `logs/fallback.log`.
- [ ] T013 [US1] Extend `code/descriptors/compute.py` to **explicitly handle error cases** for invalid compositions:
 - Adds an `error_code` column (enum: `INVALID_SYMBOL`, `INVALID_STOICHIOMETRY`) and writes flagged rows to `data/derived/descriptor_vector_errors.csv`.
 - This fulfills **FR‑001**’s requirement for robust error handling of invalid inputs.
- [X] T014 [US1] Add structured logging in `code/descriptors/compute.py`:
 - Writes JSON‑Lines to `logs/computation_log.jsonl` with fields `timestamp`, `sample_id`, `step`, `status`.
- [ ] T035 [US1] Implement `scripts/validate_descriptors.py`:
 - Compares descriptors for Cu‑Zr benchmark alloys against DScribe reference values (tolerance ±0.02) and writes a pass/fail report to `results/descriptor_benchmark_report.json`, supporting **SC‑002** verification of descriptor accuracy.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Train and evaluate glass-forming classifier on CPU (Priority: P2)

**Goal**: Train Random Forest and Gradient Boosting classifiers with 5‑fold CV and report metrics

**Independent Test**: Run training pipeline on a subset of 200 samples and verify model achieves ≥0.75 ROC‑AUC on a held‑out test split

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T015 [US2] Contract test for model performance metrics schema in `tests/contract/test_performance_schema.py`.
- [ ] T016 [US2] Integration test for full training pipeline on synthetic data in `tests/integration/test_training_pipeline.py`.

### Implementation for User Story 2

- [ ] T017 [US2] Implement `scripts/sample_dataset.py`:
 - Performs stratified sampling (`StratifiedShuffleSplit` with seed 42) to keep class ratios.
 - Ensures resulting CSV `data/samples/sample_dataset.csv` is **≤ 7 GB** to respect the RAM limit (`max_ram_gb`) per **FR‑007**.
 - Writes sampling metadata (ratio, seed) to `logs/sampling_log.json`.
- [ ] T018 [US2] Implement `scripts/filter_labels.py`:
 - Retains rows with `phase_label` from experimental sources.
 - Marks DFT‑derived rows with `confidence='low'` and logs a warning, fulfilling **FR‑009** (experimental priority, lower‑confidence DFT handling).
 - Outputs `data/derived/filtered_alloys.csv`.
- [ ] T019 [US2] Implement `code/descriptors/check_imbalance.py`:
 - Calculates glass‑to‑crystalline ratio.
 - **If ratio > 3:1, writes `data/derived/imbalance_report.json` with `flag='UNSUITABLE_FOR_BINARY_CLASSIFICATION'` and **aborts** the pipeline (hard stop).** This enforces **FR‑006** as a non‑negotiable flag.
- [ ] T020 [US2] Implement `code/models/train.py`:
 - Trains Random Forest and Gradient Boosting with cross-validation.
 - Saves models to `models/trained_models.pkl`.
 - Writes **all hyper‑parameters** to `code/models/hyperparameters.yaml` (Constitution VII compliance).
 - After training, checks if mean ROC‑AUC < 0.80; if so, logs explanation in `logs/model_accuracy_issue.log` as required by Constitution VII.
- [ ] T021 [US2] Implement `code/models/evaluate.py`:
 - Evaluates on held‑out test set, computes **ROC‑AUC**, precision, recall, and standard deviation across folds.
 - Writes `results/performance_metrics.json` containing all metrics, training time, and a `validation_limitation_note` field, satisfying **FR‑004**, **SC‑001**, and Constitution VII.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Generate feature importance and SHAP visualization (Priority: P3)

**Goal**: Provide interpretability via permutation importance, SHAP plots, and sensitivity analysis

**Independent Test**: Generate SHAP plots for a trained model and verify feature importance rankings are reproducible across runs

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T023 [US3] Contract test for SHAP output format in `tests/contract/test_shap_schema.py`.
- [ ] T024 [US3] Unit test for reproducibility check (3 runs, same seed) in `tests/unit/test_reproducibility.py`.

### Implementation for User Story 3

- [ ] T030 [US3] Implement `code/descriptors/vif_report.py`:
 - Computes VIF for each descriptor and writes `data/derived/vif_report.json`.
 - Must run **before** any VIF‑based filtering.
- [ ] T025 [US3] Implement `code/descriptors/vif_filter.py`:
 - Reads VIF scores from `data/derived/vif_report.json`.
 - Removes any descriptor with VIF > 33.
 - If **all** descriptors exceed 5.0, performs PCA on the three descriptors, retains the first two components (>90 % variance), and writes `data/derived/pca_components.csv`.
 - Outputs filtered feature file `data/derived/descriptor_vector_vif_filtered.csv`.
- [ ] T026 [US3] Implement `code/models/importance.py`:
 - Computes permutation importance, writes `results/permutation_importance.csv`.
 - Generates SHAP summary plots saved as PNG at high resolution. in `results/shap_plots/` with naming `shap_summary_<model>.png`.
- [ ] T027 [US3] Implement `scripts/sensitivity_analysis.py`:
 - Evaluates model performance across **atomic size mismatch δ values {0.01, 0.05, 0.1}** as required by **FR‑005**.
 - Writes `results/sensitivity_report.json` containing ROC‑AUC, precision, recall for each δ and includes a comment linking the δ list to `DELTA_VALUES` for traceability.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross‑Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and address reviewer constraints

- [ ] T031 [P] Implement `scripts/reproducibility_check.py`:
 - Runs the full pipeline three times.
 - Computes SHA‑256 hashes for **all** generated artifacts and updates `state/projects/PROJ-544-predicting-the-glass-forming-region-of-m/artifact_hashes.yaml` with new `updated_at` timestamps, satisfying **Constitution V**.
 - Verifies that metric variance across runs is within acceptable bounds (e.g., ROC‑AUC std < 0.02).
- [ ] T032a Create `docs/limitations.md` documenting missing cooling‑rate and XRD data, citing reviewer concerns.
- [ ] T032b Create `docs/experimental_validation_requirements.md` with a checklist of required experimental confirmations.
- [ ] T033 Refactor duplicate fallback logic:
 - Grep `utils.py` for duplicated code blocks, produce `logs/refactoring_report.json`.
 - Consolidate fallback into a single function `get_fallback_property()` within `code/descriptors/utils.py`.
- [ ] T034 Validate quickstart:
 - Run `scripts/run-ci.sh` end‑to‑end and ensure exit code 0.
 - Log result to `logs/quickstart_validation.log`.
- [ ] T036a Draft `docs/experimental_validation_requirements.md` (see T032b) – content includes need for XRD‑confirmed glass samples.
- [ ] T036b Draft `docs/causal_vs_associational_claims.md` explaining the correlational nature of the ML model and citing the rosalind‑franklin‑simulated review.
- [ ] T037 Add metadata field `experimental_validation_status` (enum: `yes`, `no`, `unknown`) to `contracts/descriptor_vector.schema.json` and ensure it is populated in `data/derived/descriptor_vector.csv`.
- [ ] T038 Update `scripts/filter_labels.py` to set `experimental_validation_status` based on XRD flag; default to `unknown` when XRD data missing.
- [ ] T039 Update `contracts/model_performance_record.schema.json`:
 - Add `data_row_id` (string UUID) and `code_block_id` (string) fields.
 - Enforce that each performance record includes a `data_row_id` linking to exactly one row in the source data file **and** a `code_block_id` referencing the generating script block, thereby meeting **Constitution IV** traceability.
- [ ] T040a Create `docs/causal_vs_associational_claims.md` with a cross‑reference table linking each figure in the manuscript to its `data_row_id`.
- [ ] T040b Add the cross‑reference table to the manuscript (outside of code base – noted for authors).
- [ ] T041 Implement `scripts/validate_xrd_availability.py`:
 - Queries source databases for XRD patterns.
 - Writes `data/derived/xrd_availability_report.json` with count, list of IDs, and flag `insufficient` if < 10 samples.
- [ ] T042 Placeholder for future verified alloy dataset acquisition:
 - Document the need to locate ≥ 1000 experimentally labeled glass‑forming compositions from a verified source.
 - Create a GitHub issue template `issues/verified_dataset_acquisition.md` to track progress.
