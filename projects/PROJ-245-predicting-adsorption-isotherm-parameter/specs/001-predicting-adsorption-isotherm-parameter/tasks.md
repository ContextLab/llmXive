# Tasks: Predicting Adsorption Isotherm Parameters from Molecular Features

**Input**: Design documents from `/specs/001-predicting-adsorption-isotherm-params/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `data/`, `tests/` at repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- Paths shown below assume single project structure per `plan.md`

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project structure per `plan.md` (code/, data/, tests/, contracts/)
- [X] T002 Initialize Python 3.11 project with `requirements.txt` (rdkit, scikit-learn, pandas, numpy, shap, pyyaml, pytest, datasets, huggingface_hub, psi4)
- [X] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete. All data processing must use real experimental data. Synthetic data is strictly prohibited.

- [X] T004 Define `contracts/dataset.schema.yaml` and `contracts/model_output.schema.yaml`
- [X] T008 [US1] Create base data classes/entities in `code/models/entities.py` for Adsorbate, Adsorbent, and IsothermParameter with all required attributes (molecular weight, surface area, etc.)
- [X] T009 Configure environment variable management and logging infrastructure in `code/__init__.py`
- [X] T010 [US1] Setup pytest configuration and test directory structure: Create `pytest.ini` with seed pinning and `tests/__init__.py` to enable test execution
- [X] T014a [P] [US1] Implement `code/data/descriptors.py` to calculate standard molecular descriptors: molecular weight, polar surface area, polarizability, H-bond counts, van der Waals volume using RDKit (FR-001).
- [X] T014ba [P] [US1] Implement `code/data/descriptors.py` to calculate **Kinetic Diameter** (Optional for Consensus Comparison). **Logic**: Use RDKit geometric approximation (`rdMolDescriptors.CalcTPSA` for 2D area proxy or 3D convex hull if 3D coordinates available). **Requirement**: If the specific method is unavailable, the script MUST raise a clear `DescriptorCalculationError`. This is NOT a mandatory model feature, but calculated for consensus comparison.
- [X] T014bb [P] [US1] Implement `code/data/descriptors.py` to calculate **Lennard-Jones Energy Parameter (epsilon)** (Optional for Consensus Comparison). **Logic**: Use critical temperature correlation formula (e.g., `epsilon = k * Tc`). **Requirement**: If atomic parameters for the correlation are missing, the script MUST raise a clear `DescriptorCalculationError`. This is NOT a mandatory model feature.
- [X] T014bc [P] [US1] Implement `code/data/descriptors.py` to calculate **Quadrupole Moment** (Optional for Consensus Comparison). **Logic**: Requires external library `psi4` or `openff` for quantum calculation. **Requirement**: If the library is not installed, the script MUST raise a clear `DependencyMissingError`. This is NOT a mandatory model feature.
- [X] T014z [P] [US1] **Define Descriptor Provenance Registry**: Create `docs/descriptor_provenance.md`. This task does NOT create a runtime configuration file. It MUST document the exact mathematical formulas and literature citations (DOI/URL) for Kinetic Diameter, Lennard-Jones epsilon, and Quadrupole Moment as implemented in `code/data/descriptors.py`. **CRITICAL**: This file is for provenance tracking only. **NO** values are to be stored here for runtime lookup. All runtime descriptor calculations MUST be performed dynamically by RDKit/external libs in `code/data/descriptors.py`.
- [X] T043a [P] [US1] Implement `code/data/loader.py`: **Fetch & Validate**. Attempt to fetch real data from NIST/MOF-1000 using `code/data/download.py`. Validate schema. **CRITICAL**: If fetch fails, the script MUST raise a `DataFetchError` and terminate. **NO** synthetic fallback is permitted. Write `verification_log.json` with status "REAL_DATA_FETCH_FAILED" and rationale.
- [X] T045 [US2] Implement `code/models/audit.py` to perform a **Data Leakage Audit**: Before training, this script must verify that the material-level split (T020) is correct by checking the intersection of `adsorbent_structure_id` between train and test sets. If any overlap is found, it must abort training and log the specific leaking IDs to `data/audit/leakage_report.json`.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Curate and Prepare the Adsorption Dataset (Priority: P1) 🎯 MVP

**Goal**: Generate a clean, normalized CSV linking molecular descriptors to isotherm parameters using real experimental data only.

**Independent Test**: Run `code/data/preprocess.py` on the real dataset and verify the output CSV contains exactly `polarizability`, `langmuir_capacity`, `henry_constant`, `surface_area` (m²/g) with no missing values.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [X] T012 [P] [US1] Contract test for schema compliance in `tests/contract/test_dataset_schema.py`
- [X] T013 [P] [US1] Unit test for RDKit descriptor calculation in `tests/unit/test_descriptors.py`

### Implementation for User Story 1

- [X] T015 [US1] Implement `code/data/preprocess.py` to filter Type I isotherms, remove entries with missing targets, normalize units (m²/g), and handle missing pore volume (impute/exclude with logging) (FR-002); depends on T014a, T014ba, T014bb, T014bc, T043a
- [ ] T016 [US1] Implement outlier detection in `code/data/preprocess.py` to flag adsorbates with identical descriptors but conflicting targets: Group by descriptor_hash, calculate variance of target, flag if variance > threshold; output must be `data/processed/outliers.csv` with columns [material_id, descriptor_hash, target_variance] (Edge Cases); depends on T014a, T014ba, T014bb, T014bc, T015
- [ ] T017 [US1] Update `code/main.py` orchestrator to run the full data curation pipeline (Download -> Preprocess -> Outlier Check); depends on T014a, T014ba, T014bb, T014bc, T043a, T015, T016

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Train and Evaluate Predictive Models (Priority: P2)

**Goal**: Train baseline models (Linear, RF, GB) with strict material-level splitting and evaluate performance on real data.

**Independent Test**: Run training on real data; verify that the test set contains no materials present in the training set and that metrics (R², RMSE) are logged.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [P] [US2] Contract test for model output schema in `tests/contract/test_model_output.py`
- [X] T019 [P] [US2] Integration test for material-level data splitting in `tests/integration/test_data_split.py`

### Implementation for User Story 2

- [X] T020 [P] [US2] Implement `code/models/train.py` to perform **Material-Level Split**: Group rows by `adsorbent_structure_id` (the unique crystallographic identifier or MOF-177 entry ID), then split groups, ensuring no `adsorbent_structure_id` exists in both train and test sets (FR-003). This task focuses ONLY on the splitting logic.
- [X] T021 [P] [US2] Implement `code/models/train.py` to **Train Models**: Train Linear Regression, Random Forest, and Gradient Boosting models (FR-004). This task focuses ONLY on the training loop.
- [X] T022 [P] [US2] Implement **5-fold Cross-Validation and Hyperparameter Tuning** in `code/models/train.py`. This task focuses ONLY on tuning logic.
- [X] T051 [P] [US2] **Implement Cluster-Aware Permutation Engine**: Create `code/analysis/cluster_permutation.py`. This module must implement the algorithm described in FR-007: for each feature, shuffle values *only* among rows sharing the same `adsorbent_structure_id` (cluster). It must calculate the resulting drop in model performance to generate a null distribution for that feature's importance.
- [ ] T052 [P] [US2] **Integrate Cluster Permutation into Evaluation & Reporting**: Update `code/models/evaluate.py` to call `cluster_permutation.py` after model training. **Output**: Generate and persist `data/results/permutation_pvalues.json` containing adjusted p-values (SC-005). This task includes both the integration and the reporting step.
- [ ] T026 [P] [US2] Implement Benjamini-Hochberg FDR correction for p-values in `code/models/evaluate.py` (FR-006).
- [ ] T023 [P] [US2] Implement `code/models/evaluate.py` to calculate R², RMSE, MAE on the independent test set (SC-001); depends on T022
- [X] T024 [P] [US2] Implement null model comparison (predicting mean) and verify a significant RMSE improvement (>20% reduction); output `data/validation/null_model_comparison.json`; depends on T023
- [X] T033 [US3] **Retrain on Top 3 Features**: Extract the Top 3 features identified in T030. Retrain the best-performing model architecture using ONLY these 3 features.
- [X] T034 [US3] Implement diagnostic report generation for cases where R² < 0.5 (suggesting non-linear effects); output `data/validation/diagnostic_report.json`.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Interpret Model Drivers via SHAP Analysis (Priority: P3)

**Goal**: Generate SHAP plots and validate feature importance against physicochemical consensus using internal data only.

**Independent Test**: Run SHAP analysis on the best model; verify the top 3 features include at least 2 from the consensus list.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T028 [P] [US3] Contract test for SHAP output format in `tests/contract/test_shap_output.py`
- [X] T029 [P] [US3] Integration test for feature ranking validation in `tests/integration/test_feature_ranking.py`

### Implementation for User Story 3

- [X] T030 [P] [US3] Implement `code/interpret/shap_analysis.py` to generate SHAP summary plots for top-ranked features (FR-005)
- [X] T031 [US3] Implement `code/interpret/shap_analysis.py` to generate partial dependence plots (PDP) for top descriptors
- [X] T032 [US3] **Unified Consensus Validation**: Implement validation logic in `code/interpret/shap_analysis.py` to compare top-ranked features against the `LiteratureConsensusList` defined in the spec. **Requirement**: This logic applies to ALL data sources (internal NIST/MOF-1000). Generate a structured report discussing alignment/divergence (FR-008). **NO** external dataset fetching is permitted.
- [X] T056 [P] [US3] **Implement Consensus Comparator**: Create `code/analysis/consensus_report.py` to generate a structured report comparing identified descriptors with the consensus list.
- [X] T057 [P] [US3] **Integrate Consensus Report into Final Output**: Update `code/analysis/report_gen.py` to include the output of `consensus_report.py`.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T037 [P] Documentation updates in `README.md` and `docs/`
- [ ] T038 Code cleanup and refactoring of `code/main.py` orchestrator
- [ ] T054 [US2] [P] **Implement Runtime Logger**: Create `code/utils/runtime_logger.py` to instrument the `code/main.py` orchestrator.
- [ ] T055 [P] **Persist Runtime Log**: Ensure the logger writes the final JSON artifact to `data/benchmarks/runtime_log.json`.
- [ ] T039c [US2] [P] **Implement Benchmark Mode**: Update `code/main.py` to support a new CLI flag `--mode benchmark`.
- [X] T039a [US2] [P] Verify runtime metrics with benchmark run on real data.
- [X] T039b [US2] [P] Performance optimization: Optimize code to ensure pipeline runtime < 6h based on T039a results.
- [X] T040a [US1] [P] Unit test for empty dataset edge case in `tests/unit/test_preprocess_empty.py::test_empty_dataset`
- [X] T040b [US1] [P] Unit test for single material edge case in `tests/unit/test_preprocess_single.py`
- [ ] T041 Security hardening: Sanitize inputs in `code/data/download.py`
- [X] T042 Run `quickstart.md` validation if available

---

## Dependencies & Execution Order

1. Phase 1: Setup
2. Phase 2: Foundational
3. Phase 3: User Story 1 - Curate and Prepare the Adsorption Dataset
4. Phase 4: User Story 2 - Train and Evaluate Predictive Models
5. Phase 5: User Story 3 - Interpret Model Drivers via SHAP Analysis
6. Phase 6: Polish & Cross-Cutting Concerns
