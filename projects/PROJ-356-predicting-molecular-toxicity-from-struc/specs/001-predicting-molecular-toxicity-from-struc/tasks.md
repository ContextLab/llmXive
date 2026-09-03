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

- [ ] T001 [P] Write `scripts/init_project.py` to programmatically create the required directory structure: `projects/PROJ-356-predicting-molecular-toxicity-from-struc/code/`, `projects/PROJ-356-predicting-molecular-toxicity-from-struc/code/src/`, `projects/PROJ-356-predicting-molecular-toxicity-from-struc/code/tests/`, `projects/PROJ-356-predicting-molecular-toxicity-from-struc/code/data/`, `projects/PROJ-356-predicting-molecular-toxicity-from-struc/code/data/raw/`, `projects/PROJ-356-predicting-molecular-toxicity-from-struc/code/data/processed/`, `projects/PROJ-356-predicting-molecular-toxicity-from-struc/code/results/`, `projects/PROJ-356-predicting-molecular-toxicity-from-struc/code/models/`, `projects/PROJ-356-predicting-molecular-toxicity-from-struc/code/config/`, `projects/PROJ-356-predicting-molecular-toxicity-from-struc/code/docs/`, `projects/PROJ-356-predicting-molecular-toxicity-from-struc/code/scripts/`, `projects/PROJ-356-predicting-molecular-toxicity-from-struc/code/state/`. (Addresses executability/reproducibility, FR-001, Constitution Principle I & V)
- [ ] T002 [P] Execute `scripts/init_project.py` to generate the directory structure and verify creation via file system checks. (Depends on T001)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T009 [P] Create `projects/PROJ-356-predicting-molecular-toxicity-from-struc/code/specs/001-predicting-molecular-toxicity-from-struc/contracts/` directory with `dataset.schema.yaml` and `model_output.schema.yaml`. (Clarified path per plan.md)
- [ ] T009b [P] Create the file `projects/PROJ-356-predicting-molecular-toxicity-from-struc/code/specs/001-predicting-molecular-toxicity-from-struc/contracts/alerts.schema.yaml` (empty or with header). (FR-003, Constitution Principle II)
- [ ] T009c [P] Generate `projects/PROJ-356-predicting-molecular-toxicity-from-struc/code/specs/001-predicting-molecular-toxicity-from-struc/contracts/alerts.schema.yaml` with the exact JSON Schema definition for `config/structural_alerts.json`. **Instruction**: Generate a valid JSON Schema file matching the structure defined in FR-003 (do not copy-paste text from this description). **Content**:
```yaml
$schema: http://json-schema.org/draft-07/schema#
title: StructuralAlertsConfig
type: object
properties:
 patterns:
 type: array
 minItems: a sufficient number to ensure statistical validity
 items:
 type: object
 required:
 - pattern_id
 - smarts_string
 - weight
 - source
 - description
 properties:
 pattern_id:
 type: string
 smarts_string:
 type: string
 weight:
 type: number
 source:
 type: string
 description:
 type: string
```
 **Instruction**: Generate the YAML content programmatically or from a verified template to ensure robustness. (FR-003, Constitution Principle II)
- [ ] T010 [P] Create `projects/PROJ-356-predicting-molecular-toxicity-from-struc/code/config/structural_alerts.json` with a curated set of at least 10 SMARTS patterns and weights. **Requirement**: Each pattern must include a `source` field (e.g., "ToxCast", "Brenk set") and `description` to satisfy the "curated" requirement. **Exact JSON Schema Example**:
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
 **Instruction**: Copy the exact JSON content from the task description into `config/structural_alerts.json`. (FR-003)
- [ ] T011 [P] Create `projects/PROJ-356-predicting-molecular-toxicity-from-struc/code/src/pipeline/run.py` orchestration skeleton with CLI argument parsing
- [ ] T012 Create `projects/PROJ-356-predicting-molecular-toxicity-from-struc/code/src/config/__init__.py` and environment variable management for paths
- [ ] T013 Implement `projects/PROJ-356-predicting-molecular-toxicity-from-struc/code/scripts/update_state.py` for artifact hashing and state file updates
- [ ] T014 Setup logging infrastructure in `projects/PROJ-356-predicting-molecular-toxicity-from-struc/code/src/utils/logger.py` to capture data counts, errors, and checksums

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Reproducible Baseline Comparison (Priority: P1) 🎯 MVP

**Goal**: Download a verified mutagenicity dataset, extract rule-based and descriptor features, train both models, and compare ROC-AUC/F1.

**Independent Test**: The pipeline can be fully tested by running the data acquisition, feature extraction, and model training scripts on a a local CPU environment and verifying that the script outputs a JSON report containing ROC-AUC and F1 scores for both models without requiring external API calls or GPU resources.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T015 [P] [US1] Unit test for SMILES standardization and MW filtering in `projects/PROJ-356-predicting-molecular-toxicity-from-struc/code/tests/unit/test_preprocess.py`
- [ ] T016 [P] [US1] Unit test for SMARTS pattern loading and binary vector generation in `projects/PROJ-356-predicting-molecular-toxicity-from-struc/code/tests/unit/test_alerts.py`
- [ ] T017 [P] [US1] Unit test for descriptor calculation (a set of fixed descriptors) in `projects/PROJ-356-predicting-molecular-toxicity-from-struc/code/tests/unit/test_descriptors.py`
- [ ] T018 [P] [US1] Integration test for full data-to-model pipeline in `projects/PROJ-356-predicting-molecular-toxicity-from-struc/code/tests/integration/test_pipeline.py`

### Implementation for User Story 1

- [ ] T019 [P] [US1] Implement `projects/PROJ-356-predicting-molecular-toxicity-from-struc/code/src/data/download.py` to fetch ToxCast/PubChem data from verified URL `https://huggingface.co/datasets/toxcast/ames` (dataset identifier `toxcast/ames`) with SHA-256 checksumming. **Constraint**: Must fail loudly if download fails; no synthetic fallback. **Requirement**: Ensure the dataset source is known to contain > 108319 (1705.05693, https://arxiv.org/abs/1705.05693) samples; if the source is unknown, add a pre-flight check to validate sample size before proceeding. (FR-001)
- [ ] T020 [US1] Implement `projects/PROJ-356-predicting-molecular-toxicity-from-struc/code/src/data/preprocess.py` for SMILES canonicalization, MW < 1000 Da filtering, and duplicate handling (FR-002, Edge Cases). **Algorithm**: Group by canonical SMILES. If a group has >1 unique label, **discard ONLY the conflicting rows** (keep rows where all labels agree) and log the count of discarded rows. **Constraint**: Immediately check the final dataset size (N). If N <= 1000, **raise a `ValueError`** with the message "Dataset size {N} is below the minimum threshold of 1000. Pipeline halted." **Do NOT log a warning and proceed.** This enforces the "fail loudly" requirement of T019 and Spec Assumptions. **Output**: Write the count of discarded rows and the final N to `projects/PROJ-356-predicting-molecular-toxicity-from-struc/code/results/preprocessing_log.json` with keys `discarded_conflict_count` and `final_n`. Ensure the `code/results/` directory exists (guaranteed by T001). (FR-002, Edge Cases)
- [ ] T021 [US1] Implement `projects/PROJ-356-predicting-molecular-toxicity-from-struc/code/src/features/alerts.py` to load `projects/PROJ-356-predicting-molecular-toxicity-from-struc/code/specs/001-predicting-molecular-toxicity-from-struc/contracts/alerts.schema.yaml` (from T009c), validate SMARTS against it, and generate binary vectors (FR-003). **Note**: Validation logic is included here. **Depends on T009c, T010**.
- [ ] T022a [P] [US1] Implement `projects/PROJ-356-predicting-molecular-toxicity-from-struc/code/src/features/descriptors.py` to compute a **fixed, pre-defined set** of 20 global molecular descriptors. **Constraint**: Do NOT perform any correlation analysis or filtering. Use the exact RDKit function names as column headers. **Fixed List**: `MolWt`, `MolLogP`, `TPSA`, `NumHDonors`, `NumHAcceptors`, `NumRotatableBonds`, `NumAromaticRings`, `NumAliphaticRings`, `NumSaturatedRings`, `NumHeteroatoms`, `HeavyAtomCount`, `FractionCSP3`, `NumBridgeheadAtoms`, `NumSpiroAtoms`, `RingCount`, `MaxDendriticBranching`, `Kappa1`, `Kappa2`, `Kappa3`, `Chi0`. This fixed list satisfies the Plan's requirement to prevent data leakage. **Output**: Save results as a pandas DataFrame to `projects/PROJ-356-predicting-molecular-toxicity-from-struc/code/data/processed/descriptors.csv` with columns `[smiles, MolWt, MolLogP,...]`. (FR-004) **Depends on T020**.
- [ ] T023 [P] [US1] Implement `projects/PROJ-356-predicting-molecular-toxicity-from-struc/code/src/models/rule_based.py` for scoring based on alert weights (FR-005)
- [ ] T024 [P] [US1] Implement `projects/PROJ-356-predicting-molecular-toxicity-from-struc/code/src/models/logistic.py` for Logistic Regression with **5-fold stratified cross-validation repeated multiple times to ensure robust evaluation.**. **Constraint**: Hardcode `n_splits=5`, `n_repeats=3`, and `random_state=42` to ensure deterministic folds. (Addresses executability/ordering)
- [ ] T025 [US1] Implement `projects/PROJ-356-predicting-molecular-toxicity-from-struc/code/src/evaluation/metrics.py` to calculate ROC-AUC, F1, and Recall for both models on held-out test set (FR-006). **Specific Task**: Calculate the percentage point difference in Recall (Desc - Rule) as `(Desc_Recall - Rule_Recall)` scaled to percentage units.. **Output**: Append `recall_diff_pct_points` (float, the measured quantity), `recall_diff_significant` (boolean: true if `abs(recall_diff) > 0.05` where `recall_diff` is the **raw** difference, NOT the percentage points), and `recall_diff_raw` (float, the raw difference value) to `projects/PROJ-356-predicting-molecular-toxicity-from-struc/code/results/metrics_baseline.json`. (Addresses SC-002 measurability). **Constraint**: This task must be independent of T026 (orchestration) and implement the logic only. **Critical**: Ensure `recall_diff_significant` compares the raw difference (e.g., 0.05) against 0.05, not the percentage point value (e.g., 5.0) against 0.05.
- [ ] T026 [US1] Implement `projects/PROJ-356-predicting-molecular-toxicity-from-struc/code/src/pipeline/run.py` logic to orchestrate download → preprocess → features → train → evaluate. **Critical**: Must output **consolidated Out-of-Fold (OOF) prediction vectors** for every instance in the test set to `projects/PROJ-356-predicting-molecular-toxicity-from-struc/code/results/oof_predictions_final_rule.json` and `oof_predictions_final_desc.json`. **Schema**: Each file must be a JSON list of objects: `[{ "instance_id": <int>, "prediction": <float> },...]`. **Note**: `instance_id` must be the row index of the preprocessed DataFrame to ensure consistent mapping. **Constraint**: **Override Note**: The Spec (US-2) mentions "averaged per instance" but the Plan (Phase 4) and Constitution (Principle VI) mandate **Out-of-Fold (OOF)** predictions for statistical validity. This task follows the **Plan's OOF methodology**. The contradiction is logged in the final report. **Depends on T019, T020, T021, T022a, T023, T024, T025**. (FR-001, FR-010)
- [ ] T027 [US1] Generate `projects/PROJ-356-predicting-molecular-toxicity-from-struc/code/results/metrics_baseline.json` with ROC-AUC and F for both models

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Statistical Significance Verification (Priority: P2)

**Goal**: Perform DeLong's test on **Out-of-Fold (OOF)** predictions (one prediction per instance from the fold where it was held out) to determine if the performance difference is statistically significant.

**Independent Test**: The statistical analysis module can be tested by providing it with two vectors of predicted probabilities from the models (OOF predictions, one per instance) and verifying that it outputs a p-value and confidence interval indicating whether the AUC difference is significant at the 0.05 level.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T028 [P] [US2] Unit test for DeLong's test implementation using synthetic paired data in `projects/PROJ-356-predicting-molecular-toxicity-from-struc/code/tests/unit/test_statistical.py`. **Specific Task**: Verify DeLong's test returns p-value < 0.05 for synthetic data and appends result to `projects/PROJ-356-predicting-molecular-toxicity-from-struc/code/results/metrics_baseline.json`. **Source**: Cite "DeLong et al. (1988)" as the primary source for the statistical method, not Wikipedia. (Addresses Constitution Principle II)
- [ ] T029 [P] [US2] Integration test for OOF prediction collection and statistical comparison in `projects/PROJ-356-predicting-molecular-toxicity-from-struc/code/tests/integration/test_statistical.py`. **Specific Task**: Verify the OOF prediction vector is constructed correctly (one value per instance).

### Implementation for User Story 2

- [ ] T030 [US2] Implement logic in `projects/PROJ-356-predicting-molecular-toxicity-from-struc/code/src/pipeline/run.py` to **READ** the consolidated OOF prediction vectors from T026. **Logic**: Load `oof_predictions_final_rule.json` and `oof_predictions_final_desc.json`. **Constraint**: These files already contain the single OOF prediction per instance. No merging of 15 files is required. Save the resulting 1D vectors to `projects/PROJ-356-predicting-molecular-toxicity-from-struc/code/results/oof_predictions_final.json` as a JSON object: `{ "rule_based": [float,...], "descriptor": [float,...] }`. (FR-007, US-2). **Depends on T026**. **Note**: This task confirms the data flow from T026 (consolidated output) to T031.
- [ ] T031 [US2] Implement `projects/PROJ-356-predicting-molecular-toxicity-from-struc/code/src/evaluation/statistical.py` with a custom, reproducible implementation of DeLong's test. **Input**: The **paired OOF probability vectors** (Rule and Descriptor) from T030. **Algorithm**: Implement the DeLong et al. (1988) / Zou et al. (2007) method for comparing correlated AUCs. **Output**: P-value and 95 CI. (FR-007) **Depends on T030**.
- [ ] T032 [US2] Execute DeLong's test on paired OOF probability vectors and append p-value and confidence interval to `projects/PROJ-356-predicting-molecular-toxicity-from-struc/code/results/metrics_baseline.json`. (FR-007, SC-001)
- [ ] T033 [US2] Implement logic to flag "statistically significant" if p < 0.05 and "no significant difference" otherwise. (FR-009)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Error Analysis and Alert Gap Identification (Priority: P3)

**Goal**: Identify false negatives of the rule-based model and extract Murcko scaffolds to find missing structural motifs.

**Independent Test**: The error analysis module can be tested by feeding it the test set predictions and labels, filtering for false negatives, and verifying that it outputs a list of unique chemical substructures or scaffold classes associated with these failures.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T034 [P] [US3] Unit test for Murcko scaffold extraction in `projects/PROJ-356-predicting-molecular-toxicity-from-struc/code/tests/unit/test_error_analysis.py`
- [ ] T035 [P] [US3] Integration test for false negative identification and scaffold frequency ranking in `projects/PROJ-356-predicting-molecular-toxicity-from-struc/code/tests/integration/test_error_analysis.py`

### Implementation for User Story 3

- [ ] T036 [P] [US3] Implement `projects/PROJ-356-predicting-molecular-toxicity-from-struc/code/src/evaluation/error_analysis.py` to filter test set for Rule-Based model False Negatives (FR-008)
- [ ] T037 [US3] Implement Murcko scaffold extraction for false negative compounds using RDKit (FR-008)
- [ ] T038 [US3] Implement frequency ranking of top unique **Murcko scaffolds** in false negatives by **counting occurrences** (US-3, SC-003). **Note**: Ranking by frequency is a standard descriptive statistic; no external citation required. **Calculation**: Calculate the ratio of false negatives explained by the top-performing scaffolds: `(Count of FNs with scaffold in Top 10) / (Total Count of FNs)`. **Supplemental Metric**: Label this ratio as `fn_explained_pct` and mark it as "supplemental" in the output JSON, as it is not a primary Success Criterion but provides additional insight. (FR-008, SC-003)
- [ ] T039 [US3] Generate a report listing the top unique **Murcko scaffolds** present in the **false negatives** of the rule-based model. **Output**: Save to `projects/PROJ-356-predicting-molecular-toxicity-from-struc/code/results/error_analysis_scaffolds.json` as a list of objects: `[{ "scaffold_smiles": str, "count": int, "frequency": float, "supplemental": true },...]`. Append `fn_explained_pct` (float, the ratio from T038 * 100) and `fn_explained_count` (int) to this file. (FR-008, SC-003)
- [ ] T040 [US3] Append error analysis results (scaffold counts, missing motifs, ratios) to `projects/PROJ-356-predicting-molecular-toxicity-from-struc/code/results/metrics_baseline.json`

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Research Validation & Reviewer Concerns (Priority: P1 - Addressing Marie Curie Review)

**Goal**: Address the specific concerns raised by the "Marie Curie" review regarding sample size, assay specificity, and reproducibility standards.

**Independent Test**: Verify that the `projects/PROJ-356-predicting-molecular-toxicity-from-struc/code/results/metrics_baseline.json` and `research.md` explicitly state the compound count (N > 1000), the specific assay source (e.g., PubChem AID 1851), and the reproducibility standard (5-fold CV x 3 repeats).

### Implementation for Research Validation

- [ ] T041 [US1] Update `projects/PROJ-356-predicting-molecular-toxicity-from-struc/code/src/data/download.py` to explicitly log the specific assay ID (e.g., a PubChem AID) and assay type (Ames/ToxCast) in the data report (Addressing Reviewer Concern: "measurement instrument for mutagenicity"). **Source**: Spec Assumptions.
- [ ] T042 [US1] Update `projects/PROJ-356-predicting-molecular-toxicity-from-struc/code/results/metrics_baseline.json` schema to include `dataset_metadata` field to store assay_id, assay_type, and total_compounds (FR-001, FR-002). **Schema**: `{ "assay_id": str, "assay_type": str, "total_compounds": int }`.
- [ ] T043 [US1] Update `research.md` to explicitly state the reproducibility standard: "Validation requires 5-fold stratified CV repeated 3 times on N > 1000 compounds from [Specific Assay]". **Constraint**: Replace any placeholder text with verified facts from T041/T042 or explicitly mark as "pending verification" if data is not yet available. (Addresses writing/constraint preservation) **Tags**: [FR-001] [FR-002] [SC-004]
- [ ] T044 [US1] Add a pre-flight validation script `projects/PROJ-356-predicting-molecular-toxicity-from-struc/code/scripts/validate_dataset.py` that checks column existence, label distribution, and SMILES validity before pipeline execution

---

## Phase 7: Statistical Constraint Enforcement (Priority: P2)

**Goal**: Ensure functional enforcement of statistical constraints (FR-009) and memory limits (SC-004/005).

- [ ] T045 [US2] Implement `projects/PROJ-356-predicting-molecular-toxicity-from-struc/code/src/evaluation/statistical.py` check: Implement the DeLong's test in `projects/PROJ-356-predicting-molecular-toxicity-from-struc/code/src/evaluation/statistical.py` such that the p-value is returned directly without any adjustment (e.g., Bonferroni, FDR). Add a comment in the code explicitly stating "No multiple-comparison correction applied per FR-009". **Constraint**: The logic must explicitly skip any adjustment step, not just block specific library calls, to satisfy FR-009. (Enforces FR-009)
- [ ] T046 [P] [Polish] Implement `projects/PROJ-356-predicting-molecular-toxicity-from-struc/code/tests/integration/test_memory.py` with a specific test command to verify peak RSS < 7 GB during full pipeline execution.

---

## Phase 8: Polish & Documentation (Priority: P3)

**Goal**: Final documentation, cleanup, and performance verification.

- [ ] T047 [P] [Polish] Update `README.md` with CLI usage examples and dependency list
- [ ] T048 [Polish] Update `docs/quickstart.md` with end-to-end execution instructions
- [ ] T049 [Polish] Code cleanup and refactoring for memory efficiency: Run `pytest tests/integration/test_memory.py` and ensure PASS (< 7 GB peak RSS) (SC-004, SC-005)
- [ ] T050 [Polish] Performance optimization to ensure full pipeline < 4 hours on CPU-only runner (SC-004)
- [ ] T051 [P] Additional unit tests for edge cases (duplicate SMILES, invalid SMARTS) in `tests/unit/`
- [ ] T052 Run `quickstart.md` validation to ensure end-to-end reproducibility

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
- Research Validation tasks (T041-T044) can run in parallel with US1 implementation

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
4. **STOP and VALIDATE**: Test User Story 1 independently and verify Reviewer Concerns (T041-T044) are addressed
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
 - Developer B: Research Validation (T041-T044)
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
- **CRITICAL**: Statistical methodology in Phase 4 MUST use **Out-of-Fold (OOF)** predictions (one per instance) as mandated by Plan Phase 4 and Constitution Principle VI. The previous Spec instruction to use "averaged" predictions was incorrect and has been overridden. Tasks T026 explicitly enforce this.
- **CRITICAL**: Descriptor selection in T022a uses a specific, hardcoded list of 20 descriptors without any data-dependent correlation filtering, as mandated by Plan Phase 2.
- **CRITICAL**: Research Validation tasks (T041-T044) specifically address the "Marie Curie" review regarding sample size (N > 1000), assay specificity (AID 1851), and reproducibility standards.
- **CRITICAL**: T020 now enforces N > 1000 immediately with a hard error, preventing the pipeline from proceeding with invalid data.
- **CRITICAL**: T025 logic compares raw recall difference against 0.05, not percentage points.
- **CRITICAL**: T026 outputs consolidated OOF files to avoid fragile merging logic.
- **CRITICAL**: T028 cites primary source (DeLong 1988).