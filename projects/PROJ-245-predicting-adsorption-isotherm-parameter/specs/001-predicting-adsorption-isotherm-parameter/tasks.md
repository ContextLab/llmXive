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
- [X] T002 Initialize Python 3.11 project with `requirements.txt` (rdkit, scikit-learn, pandas, numpy, shap, pyyaml, pytest)
- [X] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented. Includes the Hybrid Data Loader to handle unverified sources.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Define `contracts/dataset.schema.yaml` and `contracts/model_output.schema.yaml`
- [X] T005 [P] [US1] Create `code/data/synthetic_gen.py` to generate raw synthetic data (N=5000) with noise and random correlations
- [X] T006 [P] [US1] Create `code/data/validate_schema.py` to validate generated data against `contracts/dataset.schema.yaml`
- [X] T007 [P] [US1] Implement `code/data/download.py` to attempt NIST/MOF-1000 fetch and write `verification_log.json` on failure
- [X] T008 [US1] Create base data classes/entities in `code/models/entities.py` for Adsorbate, Adsorbent, and IsothermParameter with all required attributes (molecular weight, surface area, etc.)
- [X] T009 Configure environment variable management and logging infrastructure in `code/__init__.py`
- [X] T010 [US1] Setup pytest configuration and test directory structure: Create `pytest.ini` with seed pinning and `tests/__init__.py` to enable test execution
- [X] T011 [P] Create `code/main.py` orchestrator to support both synthetic and external data flows (US1, US2, US3)
- [X] T014a [P] [US1] Implement `code/data/descriptors.py` to calculate standard molecular descriptors: molecular weight, polar surface area, polarizability, H-bond counts, van der Waals volume using RDKit (FR-001).
- [X] T014z [P] [US1] **Define Descriptor Provenance Registry**: Create `docs/descriptor_provenance.md`. This task does NOT create a runtime configuration file. It MUST document the exact mathematical formulas and literature citations (DOI/URL) for Kinetic Diameter, Lennard-Jones epsilon, and Quadrupole Moment as implemented in RDKit (T014b/c/d). **CRITICAL**: This file is for provenance tracking only. **NO** values are to be stored here for runtime lookup. All runtime descriptor calculations MUST be performed dynamically by RDKit in `code/data/descriptors.py`. This task resolves the conflict between FR-001 (calculation) and the previous misconception of a lookup table.
- [X] T014b [P] [US1] Implement `code/data/descriptors.py` to calculate **Kinetic Diameter**. **Logic**: MUST use RDKit geometric approximation (Diameter ≈ 2 * sqrt(Area/PI)). **No fallbacks allowed**. If RDKit fails, the script MUST raise an error. The formula and citation are documented in T014z.
- [X] T014c [P] [US1] Implement `code/data/descriptors.py` to calculate **Lennard-Jones Energy Parameter (epsilon)**. **Logic**: MUST use RDKit estimation or critical temperature correlation. **No fallbacks allowed**. If calculation fails, the script MUST raise an error. The formula and citation are documented in T014z.
- [X] T014d [P] [US1] Implement `code/data/descriptors.py` to calculate **Quadrupole Moment**. **Logic**: MUST use RDKit calculation. **No fallbacks allowed**. If calculation fails, the script MUST raise an error. The formula and citation are documented in T014z.
- [X] T043a [P] [US1] Implement `code/data/loader.py` part 1: **Fetch & Validate**. Attempt to fetch real data from NIST/MOF-1000 using `code/data/download.py`. Validate schema. If fetch fails, write `verification_log.json` with status "UNVERIFIED" and rationale.
- [X] T043b [P] [US1] Implement `code/data/loader.py` part 2: **Synthetic Fallback & Logging**. If T043a fails, generate synthetic data using `code/data/synthetic_gen.py` for CI reproducibility (Plan Phase 0-2). Ensure synthetic data is marked "Provisional".
- [X] T044 [P] [US1] Implement `code/data/verified_source_enforcer.py`: A module that checks if the current dataset is from a "Verified Source" (real data). If the run is for **Scientific Validation (Phase 3)**, this module must verify that the data source is in a `verified_sources.json` whitelist. If synthetic data is detected during a Phase 3 run, it must raise a `ScientificValidityError` to prevent claiming scientific results from synthetic data. This task enforces the separation between Pipeline Validation (Synthetic) and Scientific Validation (Real).
- [X] T017 [US1] Update `code/main.py` orchestrator to run the full data curation pipeline (Download -> Synthetic Gen -> Preprocess -> Outlier Check); depends on T014a, T014b, T014c, T014d, T043a, T043b

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Curate and Prepare the Adsorption Dataset (Priority: P1) 🎯 MVP

**Goal**: Generate a clean, normalized CSV linking molecular descriptors to isotherm parameters, handling both synthetic and real data sources.

**Independent Test**: Run `code/data/preprocess.py` on the synthetic dataset and verify the output CSV contains exactly `polarizability`, `langmuir_capacity`, `henry_constant`, `surface_area` (m²/g) with no missing values.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T012 [P] [US1] Contract test for schema compliance in `tests/contract/test_dataset_schema.py`
- [X] T013 [P] [US1] Unit test for RDKit descriptor calculation in `tests/unit/test_descriptors.py`

### Implementation for User Story 1

- [X] T015 [US1] Implement `code/data/preprocess.py` to filter Type I isotherms, remove entries with missing targets, normalize units (m²/g), and handle missing pore volume (impute/exclude with logging) (FR-002); depends on T014a, T014b, T014c, T014d
- [X] T016 [US1] Implement outlier detection in `code/data/preprocess.py` to flag adsorbates with identical descriptors but conflicting targets: Group by descriptor_hash, calculate variance of target, flag if variance > threshold; output must be `data/processed/outliers.csv` with columns [material_id, descriptor_hash, target_variance] (Edge Cases); depends on T014a, T014b, T014c, T014d, T015
- [X] T017 [US1] Update `code/main.py` orchestrator to run the full data curation pipeline (Download -> Synthetic Gen -> Preprocess -> Outlier Check); depends on T014a, T014b, T014c, T014d, T043a, T043b, T015, T016

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Train and Evaluate Predictive Models (Priority: P2)

**Goal**: Train baseline models (Linear, RF, GB) with strict material-level splitting and evaluate performance.

**Independent Test**: Run training on synthetic data; verify that the test set contains no materials present in the training set and that metrics (R², RMSE) are logged.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [P] [US2] Contract test for model output schema in `tests/contract/test_model_output.py`
- [X] T019 [P] [US2] Integration test for material-level data splitting in `tests/integration/test_data_split.py`

### Implementation for User Story 2

- [X] T020 [P] [US2] Implement `code/models/train.py` to perform **Material-Level Split**: Group rows by `adsorbent_structure_id` (the unique crystallographic identifier or MOF-177 entry ID), then split groups, ensuring no `adsorbent_structure_id` exists in both train and test sets (FR-003). This task focuses ONLY on the splitting logic.
- [X] T045 [P] [US2] Implement `code/models/audit.py` to perform a **Data Leakage Audit**: Before training, this script must verify that the material-level split (T020) is correct by checking the intersection of `adsorbent_structure_id` between train and test sets. If any overlap is found, it must abort training and log the specific leaking IDs to `data/audit/leakage_report.json`. The orchestrator (T020) MUST call this script after the split is created. Depends on T020.
- [X] T021 [P] [US2] Implement `code/models/train.py` to **Train Models**: Train Linear Regression, Random Forest, and Gradient Boosting models (FR-004). This task focuses ONLY on the training loop. Depends on T020, T045.
- [X] T022 [P] [US2] Implement **5-fold Cross-Validation and Hyperparameter Tuning** in `code/models/train.py`. This task focuses ONLY on tuning logic. Depends on T021.
- [X] T051 [P] [US2] **Implement Cluster-Aware Permutation Engine**: Create `code/analysis/cluster_permutation.py`. This module must implement the algorithm described in FR-007: for each feature, shuffle values *only* among rows sharing the same `adsorbent_structure_id` (cluster). It must calculate the resulting drop in model performance (R² or RMSE) to generate a null distribution for that feature's importance. **Output**: `data/validation/cluster_adjusted_pvalues.json`. This replaces or augments the standard permutation logic in T025.
- [X] T052 [P] [US2] **Integrate Cluster Permutation into Evaluation**: Update `code/models/evaluate.py` to call `cluster_permutation.py` after model training. The output must be a new artifact `data/validation/cluster_adjusted_pvalues.json` containing the adjusted p-values derived from the cluster-aware null distribution. Depends on T051.
- [X] T026 [P] [US2] Implement Benjamini-Hochberg FDR correction for p-values in `code/models/evaluate.py` (FR-006, SC-005). **Input**: Accept `data/validation/cluster_adjusted_pvalues.json` from T052. **Output**: `data/validation/fdr_corrected_pvalues.json`. Depends on T052.
- [X] T023 [P] [US2] Implement `code/models/evaluate.py` to calculate R², RMSE, MAE on the independent test set (SC-001); depends on T022
- [X] T024 [P] [US2] Implement null model comparison (predicting mean) and verify a significant RMSE improvement (>20% reduction); output `data/validation/null_model_comparison.json`; depends on T023
- [X] T027 [P] [US2] Update `code/main.py` orchestrator to support running the pipeline on the external literature dataset (Phase 3); depends on T020, T021, T022, T051, T052, T026

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Interpret Model Drivers via SHAP Analysis (Priority: P3)

**Goal**: Generate SHAP plots and validate feature importance against physicochemical consensus.

**Independent Test**: Run SHAP analysis on the best model; verify the top 3 features include at least 2 from the consensus list (polarizability, kinetic diameter, etc.) if using the external validation dataset.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T028 [P] [US3] Contract test for SHAP output format in `tests/contract/test_shap_output.py`
- [X] T029 [P] [US3] Integration test for feature ranking validation in `tests/integration/test_feature_ranking.py`

### Implementation for User Story 3

- [X] T035a [US3] **Fetch External Data**: Fetch the **MOF-177 Benchmark** dataset from HuggingFace (`ethanolivertroy/mof-177-benchmark`). **CRITICAL**: This is the ONLY allowed source for external validation. **DEPRECATED**: The previous requirement for manual curation of `kr_cnt.csv` is removed as it violated Constitution Principle I (Reproducibility) and Principle III (Data Hygiene). If the MOF-177 Benchmark is unavailable, the pipeline MUST HALT immediately with a "Data Unavailable: Scientific Validation Blocked" error. **DO NOT** manually curate, generate synthetic, or fallback to placeholder data for scientific claims. Save to `data/external/verified_dataset.csv`.
- [X] T035 [US3] Implement `code/data/load_external.py` to load the fetched `data/external/verified_dataset.csv` and validate it against `contracts/dataset.schema.yaml` (Phase 3 External Data); depends on T035a
- [X] T030 [P] [US3] Implement `code/interpret/shap_analysis.py` to generate SHAP summary plots for top-ranked features (FR-005)
- [X] T031 [US3] Implement `code/interpret/shap_analysis.py` to generate partial dependence plots (PDP) for top descriptors
- [X] T032 [US3] Implement validation logic in `code/interpret/shap_analysis.py` to compare top-ranked features against the literature consensus list (polarizability, kinetic diameter, Lennard-Jones energy parameter, quadrupole moment, molecular volume). This logic MUST be implemented to generate `data/validation/sc002_match_report.json` when the external dataset is loaded. The orchestrator (T036) will determine when to execute this check, but the code path and artifact generation are mandatory for the external phase. (SC-002)
- [X] T033 [US3] **Retrain on Top 3 Features**: Extract the Top 3 features identified in T030. **Retraining**: Retrain the **best-performing model architecture** (from T022) using **ONLY** these 3 features. **Tuning**: Perform a **new, independent hyperparameter grid search** specifically for this 3-feature subset. **Evaluation**: Evaluate this reduced model on the held-out test set. **Success Criterion**: Calculate the Null Model R² (predicting mean per `adsorbent_structure_id` in the test set). The reduced model's R² must be **>= (Null Model R² + 0.2)**. Calculate and report the confidence interval via bootstrapping. Output `data/validation/sc003_r2_report.json`. Depends on T030, T022.
- [X] T034 [US3] Implement diagnostic report generation for cases where R² < 0.5 (suggesting non-linear effects); output `data/validation/diagnostic_report.json` with fields: [r2_score, top_features, suggested_causes]; depends on T033
- [X] T056 [P] [US3] **Implement Consensus Comparator**: Create `code/analysis/consensus_report.py`. This module must load the `LiteratureConsensusList` (from config or a YAML file) and the top-ranked features from SHAP analysis. It must generate a structured report (`data/reports/consensus_analysis.md`) that explicitly lists:
    1.  **Convergence**: Descriptors found by the model that are on the consensus list.
    2.  **Divergence**: Descriptors on the consensus list that the model did *not* select as significant.
    3.  **Novelty**: Descriptors selected by the model that are *not* on the consensus list, with a placeholder for the implementer to add a physicochemical hypothesis for their significance.
- [X] T057 [P] [US3] **Integrate Consensus Report into Final Output**: Update `code/analysis/report_gen.py` to include the output of `consensus_report.py` as a mandatory section in the final `data/reports/final_report.md`.
- [X] T036 [US3] Update `code/main.py` orchestrator to integrate the external dataset loading and validation flow (Phase 3); depends on T035, T032, T033, T056, T057; must trigger T032, T033, T056, T057 only when external data is present.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T037 [P] Documentation updates in `README.md` and `docs/`
- [X] T038 Code cleanup and refactoring of `code/main.py` orchestrator
- [X] T054 [US2] [P] **Implement Runtime Logger**: Create `code/utils/runtime_logger.py` to instrument the `code/main.py` orchestrator. It must record `start_time`, `end_time`, and `duration` for the full pipeline, as well as `phase_breakdown` for Data Curation, Model Training, and Interpretation.
- [X] T055 [US2] [P] **Persist Runtime Log**: Ensure the logger writes the final JSON artifact to `data/benchmarks/runtime_log.json` with the schema defined in T039c. This task ensures FR-009 is met and provides the data for SC-004 verification.
- [X] T039c [US2] [P] **Implement Benchmark Mode**: Update `code/main.py` to support a new CLI flag `--mode benchmark`. When invoked, the orchestrator must time each major phase (Data Curation, Model Training, Interpretation) and output a JSON file `data/benchmarks/runtime_log.json` with the schema: `{ "total_runtime_seconds": <float>, "phase_breakdown": { "data_curation": <float>, "model_training": <float>, "interpretation": <float> } }`. This task implements the *producer* of the benchmark data. Depends on T054, T055.
- [X] T039a [US2] [P] **Execute Benchmark**: Execute `python code/main.py --mode benchmark --output data/benchmarks/runtime_log.json`. This task verifies SC-004. Depends on T039c.
- [X] T039b [US2] [P] Performance optimization: Optimize code to ensure pipeline runtime < 6h based on T039a results; depends on T039a
- [X] T040a [US1] [P] Unit test for empty dataset edge case in `tests/unit/test_preprocess_empty.py::test_empty_dataset`
- [X] T040b [US1] [P] Unit test for single material edge case in `tests/unit/test_preprocess_single.py::test_single_material`
- [X] T041 Security hardening: Sanitize inputs in `code/data/download.py`
- [X] T042 Run `quickstart.md` validation if available

---

## Phase 7: External Data Verification & Pipeline Hardening (Revision)

**Goal**: Ensure the pipeline strictly adheres to "Real Data Only" principles for Scientific Validation (Phase 3) and handles the absence of verified large-scale datasets correctly without fabricating data.

### Implementation for Revision

- [X] T043 [US1] (Moved to Phase 2) Implements the Hybrid Loader logic.
- [X] T044 [US1] (Moved to Phase 2) Implements the Verified Source Enforcer.
- [X] T045 [US2] (Moved to Phase 4) Implements the Data Leakage Audit.
- [X] T046 [US3] Implement a "Scientific Validity Gate" in `code/main.py`: This gate must check if the current run is using the external dataset (Phase 3). If so, it must verify that `data/external/verified_dataset.csv` exists and matches the schema. If the file is missing or invalid, the pipeline must abort with a specific error message indicating that the external validation dataset is required for scientific claims, preventing a run on synthetic data from claiming scientific validity.

**Note**: Tasks T047 and T048 (previously listed) have been removed as their functionality is fully covered by T043, T044, and T046.

---

## Phase 8: Cluster-Aware Statistical Validation (Revision)

**Goal**: Implement FR-007 (Cluster-Aware Permutation Testing) to handle multicollinearity within material clusters, as standard permutation testing is insufficient for this hierarchical data structure.

*Note: This phase functionality has been moved to Phase 4 (T051-T053) to ensure primary execution.*

---

## Phase 9: Runtime Logging & Benchmarking (Revision)

**Goal**: Ensure FR-009 is fully implemented and SC-004 is verifiable with a complete runtime log.

*Note: This phase functionality has been moved to Phase 6 (T054-T055) to ensure primary execution.*

---

## Phase 10: Literature Consensus & Novelty Reporting (Revision)

**Goal**: Ensure FR-008 is fully implemented with a robust comparison against the `LiteratureConsensusList`.

*Note: This phase functionality has been moved to Phase 5 (T056-T057) to ensure primary execution.*

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete
- **Revision (Phase 7-10)**: Must be completed before any final validation run to ensure data integrity and statistical validity.

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data output
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 model output

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
Task: "Contract test for schema compliance in tests/contract/test_dataset_schema.py"
Task: "Unit test for RDKit descriptor calculation in tests/unit/test_descriptors.py"

# Launch all models for User Story 1 together:
Task: "Implement code/data/descriptors.py to calculate molecular descriptors"
Task: "Implement code/data/preprocess.py to filter Type I isotherms"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (Synthetic Data)
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
 - Developer A: User Story 1 (Data Curation)
 - Developer B: User Story 2 (Model Training)
 - Developer C: User Story 3 (Interpretation)
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Critical**: All data processing must run on CPU-only runners; no GPU/CUDA dependencies.
- **Critical**: Synthetic data is for pipeline validation only; Phase 3 (External Validation) is required for scientific claims.
- **Critical**: T014a and T014b/c/d cover all descriptors required by SC-002. T014z provides the provenance for hardcoded values.
- **Critical**: T014b/c/d prioritize RDKit calculation; T014z is a documentation artifact only.
- **Critical**: T035a is a **fetch** task, not manual curation. The previous `kr_cnt.csv` manual entry requirement is deprecated.
- **Critical**: T039c implements the benchmark mode; T039a executes it.
- **Critical**: T043 (now in Phase 2) ensures the pipeline fails loudly on missing real data but falls back to synthetic for CI reproducibility.
- **Critical**: T044 ensures scientific claims are only made on verified real data.
- **Critical**: T045 adds an extra layer of protection against data leakage.
- **Critical**: T046 ensures scientific validity checks are only performed on real data.
- **Critical**: T051-T053 (Cluster Permutation) are now in Phase 4 to satisfy FR-007.
- **Critical**: T054-T055 (Runtime Logger) are now in Phase 6 to satisfy FR-009.
- **Critical**: T056-T057 (Consensus Report) are now in Phase 5 to satisfy FR-008.
- **Critical**: T033 uses the spec-defined threshold (Null + 0.2) with 95% CI.
- [X] T049 [US2] [P] Add a "Data Leakage" unit test in `tests/unit/test_leakage.py` that intentionally creates a dataset with overlapping material IDs between train/test splits and verifies that `code/models/audit.py` (T045) correctly detects and aborts the process. This ensures the leakage prevention logic is robust.
- [X] T050 [US1] [P] Add a "Missing Real Data" unit test in `tests/unit/test_loader.py` that mocks the NIST/MOF-1000 fetch to fail and verifies that the `Hybrid Data Loader` (T043) correctly falls back to synthetic data for CI runs (Phase 0-2) while logging the failure in `verification_log.json`. This ensures the CI fallback mechanism works as designed without fabricating data for scientific claims.
- [X] T058 [US2] [P] **Cluster-Aware Permutation Test**: Execute `code/analysis/cluster_permutation.py` on the trained model to generate the null distribution for feature importance, ensuring the test respects the material ID clustering. This task is required to validate FR-007 and SC-005.
- [X] T059 [US3] [P] **Consensus Report Generation**: Execute `code/analysis/consensus_report.py` to generate the `data/reports/consensus_analysis.md` artifact, fulfilling the requirements of FR-008.
- [X] T060 [US2] [P] **Final Benchmark Execution**: Run the full pipeline with `--mode benchmark` on the synthetic dataset to generate `data/benchmarks/runtime_log.json` and verify the pipeline completes within the 4-hour limit (SC-004).