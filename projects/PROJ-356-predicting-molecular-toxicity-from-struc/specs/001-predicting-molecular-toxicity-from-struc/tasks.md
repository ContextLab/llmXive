# Tasks: Predicting Molecular Toxicity from Structural Alerts via Rule-Based Systems

**Input**: Design documents from `/specs/001-predicting-molecular-toxicity/`
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

**Purpose**: Project initialization and basic structure (Programmatic execution)

- [ ] T001 [P] Write `scripts/init_project.py` to programmatically create the required directory structure: `projects/PROJ-356-predicting-molecular-toxicity-from-struc/code/`, `src/`, `tests/`, `data/`, `results/`, `models/`, `config/`, `docs/`, `contracts/`, `scripts/`. (Replaces T001-T008, addresses executability/reproducibility)
- [ ] T002 [P] Execute `scripts/init_project.py` to generate the directory structure and verify creation via file system checks. (Depends on T001)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T009 [P] Create `contracts/` directory with `dataset.schema.yaml`, `model_output.schema.yaml`, and `alerts.schema.yaml`.
- [ ] T010 [P] Create `config/structural_alerts.json` with a curated set of at least 10 SMARTS patterns and weights. **Requirement**: Each pattern must include a `source` field (e.g., "ToxCast", "Brenk set") and `description` to satisfy the "curated" requirement. **Exact JSON Schema Example**:
```json
{
 "patterns": [
 {
 "pattern_id": "NITRO_AROMATIC_01",
 "smarts_string": "[*;a]([N+](=O)[O-])",
 "weight": 1.5,
 "source": "Brenk Set",
 "description": "Nitroaromatic group"
 },
 {
 "pattern_id": "EPOXIDE_01",
 "smarts_string": "[C;D3]1[O;D1][C;D3]1",
 "weight": 2.0,
 "source": "Brenk Set",
 "description": "Epoxide ring"
 },
 {
 "pattern_id": "PRIMARY_ARI_AMINE_01",
 "smarts_string": "[N;D1;H2][c]",
 "weight": 1.2,
 "source": "Brenk Set",
 "description": "Primary aromatic amine"
 },
 {
 "pattern_id": "SECONDARY_ARI_AMINE_01",
 "smarts_string": "[N;D2;H1][c]",
 "weight": 1.0,
 "source": "Brenk Set",
 "description": "Secondary aromatic amine"
 },
 {
 "pattern_id": "AZIDE_01",
 "smarts_string": "[N;D1]=[N;D1]=[N;D1]",
 "weight": 2.5,
 "source": "Brenk Set",
 "description": "Azide group"
 },
 {
 "pattern_id": "ISOCYANATE_01",
 "smarts_string": "[N;D1]=[C;D2]=[O;D1]",
 "weight": 2.0,
 "source": "Brenk Set",
 "description": "Isocyanate group"
 },
 {
 "pattern_id": "ALDEHYDE_01",
 "smarts_string": "[C;D2](=[O;D1])[H;D1]",
 "weight": 0.8,
 "source": "Brenk Set",
 "description": "Aldehyde group"
 },
 {
 "pattern_id": "HALO_ALIPHATIC_01",
 "smarts_string": "[C;D4][Cl,Br,I,F]",
 "weight": 0.5,
 "source": "Brenk Set",
 "description": "Halogenated aliphatic"
 },
 {
 "pattern_id": "AZO_01",
 "smarts_string": "[N;D1]=[N;D1]",
 "weight": 1.8,
 "source": "Brenk Set",
 "description": "Azo group"
 },
 {
 "pattern_id": "HYDRAZINE_01",
 "smarts_string": "[N;D1][N;D1]",
 "weight": 1.5,
 "source": "Brenk Set",
 "description": "Hydrazine group"
 }
 ]
}
```
 (FR-003)
- [ ] T010b [US1] Implement validation logic in `src/features/alerts.py` (or a new `src/utils/validator.py`) to load `config/structural_alerts.json` and validate it against `contracts/alerts.schema.yaml`. Log any missing fields or invalid SMARTS patterns. (Depends on T009, T010; addresses constraint preservation)
- [ ] T011 [P] Create `src/pipeline/run.py` orchestration skeleton with CLI argument parsing
- [ ] T012 Create `src/config/__init__.py` and environment variable management for paths
- [ ] T013 Implement `src/scripts/update_state.py` for artifact hashing and state file updates
- [ ] T014 Setup logging infrastructure in `src/utils/logger.py` to capture data counts, errors, and checksums

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Reproducible Baseline Comparison (Priority: P1) 🎯 MVP

**Goal**: Download a verified mutagenicity dataset, extract rule-based and descriptor features, train both models, and compare ROC-AUC/F1.

**Independent Test**: The pipeline can be fully tested by running the data acquisition, feature extraction, and model training scripts on a local CPU environment and verifying that the script outputs a JSON report containing ROC-AUC and F1 scores for both models without requiring external API calls or GPU resources.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T015 [P] [US1] Unit test for SMILES standardization and MW filtering in `tests/unit/test_preprocess.py`
- [ ] T016 [P] [US1] Unit test for SMARTS pattern loading and binary vector generation in `tests/unit/test_alerts.py`
- [ ] T017 [P] [US1] Unit test for descriptor calculation (a set of fixed descriptors) in `tests/unit/test_descriptors.py`
- [ ] T018 [P] [US1] Integration test for full data-to-model pipeline in `tests/integration/test_pipeline.py`

### Implementation for User Story 1

- [ ] T019 [P] [US1] Implement `src/data/download.py` to fetch ToxCast/PubChem data from verified URL (HuggingFace/UCI) with SHA-256 checksumming
- [ ] T020 [US1] Implement `src/data/preprocess.py` for SMILES canonicalization, MW < 1000 Da filtering, and duplicate handling (FR-002, Edge Cases). **Algorithm**: Group by canonical SMILES; if any group has >1 unique label, discard all rows in that group and log the count of discarded rows; otherwise, keep one instance. (FR-002, Edge Cases)
- [ ] T021 [US1] Implement `src/features/alerts.py` to load `config/structural_alerts.json`, validate SMARTS, and generate binary vectors (FR-003). **Depends on T010b**.
- [ ] T022 [US1] Implement `src/features/descriptors.py` to compute a comprehensive set of RDKit global descriptors (non-correlated): `MolWt`, `MolLogP`, `TPSA`, `NumHDonors`, `NumHAcceptors`, `NumRotatableBonds`, `NumAromaticRings`, `NumAliphaticRings`, `NumSaturatedRings`, `NumHeteroatoms`, `HeavyAtomCount`, `FractionCSP`, `NumBridgeheadAtoms`, `NumSpiroAtoms`, `RingCount`, `MaxDendriticBranching`, `Kappa`, `Kappa2`, `Kappa3`, `Chi0` (FR-004). **Output**: Save results as a pandas DataFrame to `data/processed/descriptors.csv` with columns `[smiles, descriptor_1,..., descriptor_20]`.
- [ ] T022b [US1] Implement `src/features/descriptors.py` (or `src/utils/validate_descriptors.py`) to compute the correlation matrix of the 20 selected descriptors on a **random sample of 1000 rows drawn strictly from the training set of the first CV split** and verify that no pair exceeds a correlation threshold (e.g., |r| > 0.9). Log the result to `results/descriptor_validation.json`. (Addresses FR-004 non-correlation requirement and leakage prevention)
- [ ] T023 [P] [US1] Implement `src/models/rule_based.py` for scoring based on alert weights (FR-005)
- [ ] T024 [P] [US1] Implement `src/models/logistic.py` for Logistic Regression with **5-fold stratified cross-validation repeated multiple times**. **Constraint**: Hardcode `n_splits=5` and `n_repeats=3` to ensure the 15-fold structure required by FR-005. (Addresses executability/ordering)
- [ ] T025 [US1] Implement `src/evaluation/metrics.py` to calculate ROC-AUC, F1, and Recall for both models on held-out test set (FR-006). **Specific Task**: Measure and report the difference in Recall (Desc - Rule) against a predefined significance threshold of a non-trivial absolute percentage point difference. (as per SC-002). **Output**: Append `recall_diff` (float) and `recall_diff_significant` (boolean, true if > 0.05) to `results/metrics_baseline.json`. (Addresses SC-002 measurability)
- [ ] T026 [US1] Implement `src/pipeline/run.py` logic to orchestrate download → preprocess → features → train → evaluate. **Critical**: Must output **intermediate OOF prediction vectors for every instance in every fold** to `results/oof_predictions_fold_{fold_id}.json` (a file for each fold). **Schema**: Each file must be a JSON list of objects: `[{ "instance_id": <int>, "prediction": <float> },...]`. **Depends on T019, T020, T021, T022, T023, T024, T025**. (FR-001, FR-010)
- [ ] T027 [US1] Generate `results/metrics_baseline.json` with ROC-AUC and F for both models

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Statistical Significance Verification (Priority: P2)

**Goal**: Perform DeLong's test on **Out-of-Fold (OOF)** predictions (one prediction per instance from the fold where it was held out) to determine if the performance difference is statistically significant.

**Independent Test**: The statistical analysis module can be tested by providing it with two vectors of predicted probabilities from the models (OOF predictions, one per instance) and verifying that it outputs a p-value and confidence interval indicating whether the AUC difference is significant at the 0.05 level.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T028 [P] [US2] Unit test for DeLong's test implementation using synthetic paired data in `tests/unit/test_statistical.py`. **Specific Task**: Verify DeLong's test returns p-value < 0.05 (Wikipedia: Misuse of p-values, https://en.wikipedia.org/wiki/Misuse_of_p-values) for synthetic data and appends result to `results/metrics_baseline.json`.
- [ ] T029 [P] [US2] Integration test for OOF prediction collection and statistical comparison in `tests/integration/test_statistical.py`. **Specific Task**: Verify the OOF prediction vector is constructed correctly (one value per instance).

### Implementation for User Story 2

- [ ] T030 [US2] Implement logic in `src/pipeline/run.py` to **COLLECT** all 15 OOF prediction files generated in T026 into a single matrix (15 x N) and save to `results/oof_predictions_matrix.json`. (FR-007, US-2). **Depends on T026**.
- [ ] T030b [US2] Implement logic to **SELECT** the single OOF prediction per instance from the 15-fold matrix. **Logic**: For each instance, identify the fold where it was held out and extract the prediction from that specific fold. **Constraint**: Do NOT average the 15 predictions. Save the resulting 1D vector (N predictions) to `results/oof_predictions_final.json` as a **JSON array of floats** (e.g., `[0.12, 0.95,...]`). (Addresses constraint preservation/executability: "Do NOT average")
- [ ] T031 [US2] Implement `src/evaluation/statistical.py` with a custom, reproducible implementation of DeLong's test. **Input**: The **deduplicated single-prediction vector** from T030b. **Output**: P-value and 95% CI. (FR-007)
- [ ] T032 [US2] Execute DeLong's test on paired OOF probability vectors and append p-value and confidence interval to `results/metrics_baseline.json`. (FR-007, SC-001)
- [ ] T033 [US2] Implement logic to flag "statistically significant" if p < 0.05 and "no significant difference" otherwise. (FR-009)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Error Analysis and Alert Gap Identification (Priority: P3)

**Goal**: Identify false negatives of the rule-based model and extract Murcko scaffolds to find missing structural motifs.

**Independent Test**: The error analysis module can be tested by feeding it the test set predictions and labels, filtering for false negatives, and verifying that it outputs a list of unique chemical substructures or scaffold classes associated with these failures.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T034 [P] [US3] Unit test for Murcko scaffold extraction in `tests/unit/test_error_analysis.py`
- [ ] T035 [P] [US3] Integration test for false negative identification and scaffold frequency ranking in `tests/integration/test_error_analysis.py`

### Implementation for User Story 3

- [ ] T036 [P] [US3] Implement `src/evaluation/error_analysis.py` to filter test set for Rule-Based model False Negatives (FR-008)
- [ ] T037 [US3] Implement Murcko scaffold extraction for false negative compounds using RDKit (FR-008)
- [ ] T038 [US3] Implement frequency ranking of top unique **Murcko scaffolds** in false negatives by **counting occurrences** (US-3, SC-003). **Note**: Ranking by frequency is a standard descriptive statistic; no external citation required.
- [ ] T039 [US3] Generate a report listing the top unique **Murcko scaffolds** present in the **false negatives** of the rule-based model. **Output**: Save to `results/error_analysis_scaffolds.json` as a list of objects: `[{ "scaffold_smiles": str, "count": int, "frequency": float },...]`. (FR-008)
- [ ] T040 [US3] Append error analysis results (scaffold counts, missing motifs) to `results/metrics_baseline.json`

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Research Validation & Reviewer Concerns (Priority: P1 - Addressing Marie Curie Review)

**Goal**: Address the specific concerns raised by the "Marie Curie" review regarding sample size, assay specificity, and reproducibility standards.

**Independent Test**: Verify that the `results/metrics_baseline.json` and `research.md` explicitly state the compound count (N > 1000), the specific assay source (e.g., PubChem AID 1851), and the reproducibility standard (5-fold CV x 3 repeats).

### Implementation for Research Validation

- [ ] T041 [US1] Update `src/data/download.py` to enforce a minimum sample size check (N > 1000) and fail gracefully if the dataset is too small (Addressing Reviewer Concern: "quantity of material matters"). **Source**: Spec Assumptions. **Depends on T019**.
- [ ] T042 [US1] Update `src/data/download.py` to explicitly log the specific assay ID (e.g., a PubChem AID) and assay type (Ames/ToxCast) in the data report (Addressing Reviewer Concern: "measurement instrument for mutagenicity"). **Source**: Spec Assumptions.
- [ ] T043 [US1] Update `results/metrics_baseline.json` schema to include `dataset_metadata` field to store assay_id, assay_type, and total_compounds (FR-001, FR-002). **Schema**: `{ "assay_id": str, "assay_type": str, "total_compounds": int }`.
- [ ] T044 [US1] Update `research.md` to explicitly state the reproducibility standard: "Validation requires 5-fold stratified CV repeated 3 times on N > 1000 compounds from [Specific Assay]". **Constraint**: Replace any placeholder text with verified facts from T041/T042 or explicitly mark as "pending verification" if data is not yet available. (Addresses writing/constraint preservation)
- [ ] T045 [US1] Add a pre-flight validation script `scripts/validate_dataset.py` that checks column existence, label distribution, and SMILES validity before pipeline execution

---

## Phase 7: Statistical Constraint Enforcement (Priority: P2)

**Goal**: Ensure functional enforcement of statistical constraints (FR-009) and memory limits (SC-004/005).

- [ ] T046 [US2] Implement `src/evaluation/statistical.py` check: Add an explicit guard clause in the statistical workflow that ensures **no multiple-comparison correction** (e.g., Bonferroni, FDR) is applied to the p-value output. **Constraint**: The logic must explicitly skip any adjustment step, not just block specific library calls, to satisfy FR-009. (Enforces FR-009)
- [ ] T047 [P] [Polish] Implement `tests/integration/test_memory.py` with a specific test command to verify peak RSS < 7 GB during full pipeline execution.

---

## Phase 8: Polish & Documentation (Priority: P3)

**Goal**: Final documentation, cleanup, and performance verification.

- [ ] T048 [P] [Polish] Update `README.md` with CLI usage examples and dependency list
- [ ] T049 [Polish] Update `docs/quickstart.md` with end-to-end execution instructions
- [ ] T050 [Polish] Code cleanup and refactoring for memory efficiency: Run `pytest tests/integration/test_memory.py` and ensure PASS (< 7 GB peak RSS) (SC-004, SC-005)
- [ ] T051 [Polish] Performance optimization to ensure full pipeline < 4 hours on CPU-only runner (SC-004)
- [ ] T052 [P] Additional unit tests for edge cases (duplicate SMILES, invalid SMARTS) in `tests/unit/`
- [ ] T053 Run `quickstart.md` validation to ensure end-to-end reproducibility

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Phase 8)**: Depends on all desired user stories being complete
- **Research Validation (Phase 6)**: Can run in parallel with US1 implementation but must be completed before final report generation
- **Statistical Constraint Enforcement (Phase 7)**: Depends on Phase 2 and Phase 4 completion

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Depends on US1 completion (needs model predictions)
- **User Story 3 (P3)**: Depends on US1 completion (needs model predictions)
- **Research Validation (Phase 6)**: Depends on US1 completion (needs data metrics)

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
- Research Validation tasks (T041-T045) can run in parallel with US1 implementation

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for SMILES standardization in tests/unit/test_preprocess.py"
Task: "Unit test for SMARTS pattern loading in tests/unit/test_alerts.py"
Task: "Unit test for descriptor calculation in tests/unit/test_descriptors.py"

# Launch all models for User Story 1 together:
Task: "Implement src/features/alerts.py"
Task: "Implement src/features/descriptors.py"
Task: "Implement src/models/rule_based.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently and verify Reviewer Concerns (T041-T045) are addressed
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
 - Developer A: User Story 1 (Data & Models)
 - Developer B: Research Validation (T041-T045)
 - Developer C: User Story 2 (Statistical) & User Story 3 (Error Analysis)
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
- **CRITICAL**: All tasks must run on CPU-only CI with a limited core count and memory capacity.. No GPU, no 8-bit/4-bit quantization, no large LLMs.
- **CRITICAL**: All data must be real and from verified sources. No synthetic data fabrication.
- **CRITICAL**: Statistical methodology in Phase 4 MUST use **Out-of-Fold (OOF)** predictions (one per instance) as mandated by Plan Phase 4 and Constitution Principle VI. The previous Spec instruction to use "averaged" predictions was incorrect and has been overridden. Tasks T030/T030b explicitly enforce this.
- **CRITICAL**: Descriptor selection in T022/T022b uses a specific, hardcoded list of 20 descriptors and includes a verification step to ensure non-correlation.
- **CRITICAL**: Research Validation tasks (T041-T045) specifically address the "Marie Curie" review regarding sample size (N > 1000), assay specificity (AID 1851), and reproducibility standards.
