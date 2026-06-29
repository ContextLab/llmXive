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

- [ ] T001 Create project structure with specific directories/files: `code/`, `code/descriptors/`, `code/models/`, `code/config/`, `data/`, `data/raw/`, `data/derived/`, `data/samples/`, `tests/`, `tests/unit/`, `tests/contract/`, `tests/integration/`, `scripts/`, `results/`, `results/shap_plots/`, `state/`, `contracts/`, `requirements.txt`, `code/config/env.yaml`
- [ ] T002 Initialize Python 3.11 project with pinned dependencies in requirements.txt (scikit-learn, pandas, numpy, shap, pymatgen, DScribe, pyyaml, imbalanced-learn, pytest)
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools in pre-commit hooks

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [P] Implement schema contracts for alloy_composition, descriptor_vector, model_performance_record in contracts/
- [ ] T005 [P] Create `scripts/generate_synthetic_data.py` to produce CI-testable dataset (a representative set of samples, labeled glass/crystalline) with deterministic random seed
- [ ] T006 [P] Create `scripts/download_and_verify.py` with verified materials-science dataset sources: (a) ucimlrepo alloy composition datasets via Python package, (b) Materials Project API via pymatgen with phase label filtering; implement checksum validation and log data availability status; include synthetic data fallback for CI testing when real data unavailable
- [ ] T007 [P] Setup environment configuration management for random seeds and memory limits in `code/config/env.yaml`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Compute thermodynamic descriptors for alloy compositions (Priority: P1) 🎯 MVP

**Goal**: Compute atomic size mismatch, mixing enthalpy, and electronegativity variance from elemental stoichiometries

**Independent Test**: Provide a CSV of alloy compositions and verify descriptor values match known calculations for benchmark alloys (e.g., Cu-Zr systems)

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T008 [P] [US1] Contract test for descriptor output schema in tests/contract/test_descriptor_schema.py
- [ ] T009 [P] [US1] Unit test for elemental symbol validation against periodic table in tests/unit/test_validate_elements.py

### Implementation for User Story 1

- [ ] T010 [P] [US1] Implement `code/descriptors/validate_elements.py` to check symbols against pymatgen periodic table; return validated/invalid list
- [ ] T011 [US1] Implement `code/descriptors/compute.py` to calculate atomic size mismatch, mixing enthalpy, electronegativity variance; compare against DScribe benchmark alloys (±0.02 tolerance); write validation results to results/descriptor_validation.json
- [ ] T012 [US1] Implement fallback logic for missing elemental properties (nearest neighbor from periodic table) in `code/descriptors/utils.py` with warning logged
- [ ] T013 [US1] Add validation and error handling for invalid compositions in `code/descriptors/compute.py`; flag with error code format 'INVALID_SYMBOL' or 'INVALID_STOICHIOMETRY'; output flagged rows in data/derived/descriptor_vector.csv with error_code column
- [ ] T014 [US1] Add logging for descriptor computation steps and excluded samples in `code/descriptors/compute.py`; write JSON lines to logs/computation_log.jsonl with timestamp, step, and sample_id
- [ ] T035 [US1] Implement benchmark validation script `scripts/validate_descriptors.py` to compare computed descriptors against DScribe reference values for Cu-Zr benchmark alloys; report pass/fail with ±0.02 tolerance; output to results/descriptor_benchmark_report.json (SC-002 verification)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Train and evaluate glass-forming classifier on CPU (Priority: P2)

**Goal**: Train Random Forest and Gradient Boosting classifiers with 5-fold CV and report metrics

**Independent Test**: Run training pipeline on a subset of 200 samples and verify model achieves ≥0.75 ROC-AUC on held-out test split

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T015 [P] [US2] Contract test for model performance metrics schema in tests/contract/test_performance_schema.py
- [ ] T016 [P] [US2] Integration test for full training pipeline on synthetic data in tests/integration/test_training_pipeline.py

### Implementation for User Story 2

- [ ] T017 [US2] Implement `scripts/sample_dataset.py` to ensure dataset ≤7 GB RAM before processing (FR-007) using STRATIFIED sampling with random seed 42 to maintain class ratio; output sampling ratio and method to logs/sampling_log.json
- [ ] T018 [US2] Implement `scripts/filter_labels.py` to retain only experimentally validated phase labels (FR-009); if no experimental labels exist, use DFT-derived labels with WARNING logged and document as lower confidence in data/derived/label_confidence.json
- [ ] T019 [US2] Implement `code/descriptors/check_imbalance.py` to detect class imbalance ratio >3:1; log WARNING-level message to stdout and write to data/derived/imbalance_report.json with flag 'UNSUITABLE_FOR_BINARY_CLASSIFICATION' (FR-006 hard requirement)
- [ ] T020 [US2] Implement `code/models/train.py` for RF and GB classifiers with 5-fold CV (FR-003); save trained models to models/trained_models.pkl
- [ ] T021 [US2] Implement `code/models/evaluate.py` to report ROC-AUC, precision, recall on held-out test set (FR-004); compute and report standard deviation across folds; write results to results/performance_metrics.json with all Key Entity attributes (ROC-AUC, precision, recall, std_dev, training_time)
- [ ] T022 [US2] Implement class weighting or SMOTE handling in `code/models/train.py` if imbalance detected; log handling method to models/training_method.log; NOTE: FR-006 hard stop requires spec revision if mitigation is needed

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Generate feature importance and SHAP visualization (Priority: P3)

**Goal**: Provide interpretability via permutation importance, SHAP plots, and sensitivity analysis

**Independent Test**: Generate SHAP plots for a trained model and verify feature importance rankings are reproducible across runs

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T023 [P] [US3] Contract test for SHAP output format in tests/contract/test_shap_schema.py
- [ ] T024 [P] [US3] Unit test for reproducibility check (3 runs, same seed) in tests/unit/test_reproducibility.py

### Implementation for User Story 3

- [ ] T025 [US3] Implement `code/descriptors/vif_filter.py` to remove features with VIF > 5.0 (FR-008); if all VIF > 5.0, apply PCA fallback retaining first 2 components explaining >90% variance; output filtered features to data/derived/descriptor_vector_vif_filtered.csv or data/derived/pca_components.csv
- [ ] T026 [US3] Implement `code/models/importance.py` for permutation importance and SHAP summary plots (FR-005)
- [ ] T027 [US3] Implement `scripts/sensitivity_analysis.py` to evaluate prediction metrics across a range of δ threshold variations (FR-005); write results to results/sensitivity_report.json
- [ ] T029 [US3] Generate SHAP plots saved as PNG in `results/shap_plots/` with descriptor values on x-axis and prediction impact on y-axis (US3 AC2)
- [ ] T030 [US3] Compute and report Variance Inflation Factor (VIF) for each descriptor in `data/derived/vif_report.json` (must precede T025 filtering)

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and address reviewer constraints

- [ ] T031 [P] Implement `scripts/reproducibility_check.py` to run full pipeline multiple times and verify metric stability (SC-003); include profiling to measure runtime per phase
- [ ] T032 [P] Documentation updates in `docs/limitations.md` addressing missing cooling rate/XRD data per rosalind-franklin-simulated review
- [ ] T033 [P] Refactor `code/descriptors/utils.py` to consolidate fallback logic: (1) grep for duplicate fallback implementations in T012 and T018, (2) extract shared logic into single function, (3) verify no code duplication remains; output cleanup report to logs/refactoring_report.json
- [ ] T034 [P] Run quickstart.md validation to ensure all tasks are executable end-to-end

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Depends on US1 (descriptors must be computed before training)
- **User Story 3 (P3)**: Depends on US2 (model must be trained before SHAP/Importance)

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
Task: "Contract test for descriptor output schema in tests/contract/test_descriptor_schema.py"
Task: "Unit test for elemental symbol validation against periodic table in tests/unit/test_validate_elements.py"

# Launch all models for User Story 1 together:
Task: "Implement validate_elements.py in code/descriptors/validate_elements.py"
Task: "Implement compute.py in code/descriptors/compute.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
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
   - Developer C: User Story 3
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
- **Critical**: Task T032 explicitly addresses the rosalind-franklin-simulated review regarding missing cooling rate/XRD data by documenting limitations rather than claiming causal determination.
- **Critical**: Task T027 (Sensitivity Analysis) mitigates the lack of thermal history data by testing robustness across δ threshold variations.
- **Critical**: Task T019 implements FR-006 hard requirement (flag as UNSUITABLE) - plan note about soft flag is a plan-root cause requiring kickback.
- **Critical**: Task T018 documents DFT-derived labels as lower confidence per FR-009, acknowledging potential availability issues.
- **Critical**: Task ordering corrected: T030 (VIF computation) precedes T025 (VIF filtering) to respect producer-consumer dependency.
- **Critical**: Tasks T022, T033, T034, T035 removed or replaced with concrete deliverables to ensure executability.
- **Critical**: T006 updated with verified materials-science dataset sources (ucimlrepo, Materials Project API) - not placeholder URLs.
- **Critical**: T017 specifies STRATIFIED sampling method with random seed 42 for reproducible sampling per FR-007.
- **Critical**: Task T035 added to explicitly verify SC-002 benchmark validation against DScribe reference values.
- **Critical**: Task T033 rewritten with executable criteria: specific file, specific duplication check (grep), and verification step.
- **Critical**: Task T028 (stratification analysis) removed as scope creep - not in any user story or functional requirement.