# Tasks: Investigating the Impact of Network Topology on Neural Entrainment to Rhythmic Stimuli

**Input**: Design documents from `/specs/001-network-topology-entrainment/`
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

- [ ] T001b [P] Create subdirectories: `code/`, `data/`, `data/raw/`, `data/processed/`, `data/visualizations/`, `tests/`, `tests/unit/`, `tests/integration/`, `docs/`.
- [ ] T001c [P] Initialize `.gitkeep` files in all empty directories.
- [ ] T002a [P] Create `requirements.txt` pinning: `networkx==2.8.8`, `numpy==1.24.0`, `pandas==2.0.0`, `scikit-learn==1.2.0`, `scipy==1.10.0`, `matplotlib==3.7.0`, `pyyaml==6.0`, `pytest==7.3.0`.
- [ ] T002b [P] Create `code/__init__.py` and `tests/__init__.py`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004a [P] Implement `code/config.py` skeleton: Define `ATLAS_TYPES` as the immutable list `['Schaefer', 'AAL', 'Power 264']` and `RANDOM_SEED`.
- [ ] T004b [P] Extend `code/config.py`: Add `atlas_type` parameter support for alternative atlases (AAL, Power 264) and corresponding data paths.
- [ ] T005a [P] Implement `code/data_loader.py` skeleton: Define function signatures for `validate_entrainment_csv()`, `validate_topology_columns()`, `validate_rhythmic_metadata()`.
- [ ] T005b [P] Implement `code/data_loader.py`: `validate_entrainment_csv()` to check for `subject_id`, `entrainment_metric` columns and numeric types (FR-008).
- [ ] T005c [P] Implement `code/data_loader.py`: `validate_topology_columns()` to check for required topology metric columns (FR-007).
- [ ] T005d [P] Implement `code/data_loader.py`: `validate_rhythmic_metadata()` to check for 'rhythmic stimulus' metadata in external data source.
- [ ] T006 [P] Implement HCP data download logic in `code/data_loader.py`: Download `HCP_S1200_Release` from `https://db.humanconnectome.org/rest/datasets/HCP_S1200_Release` (canonical source) using `HCP_USERNAME` and `HCP_PASSWORD` environment variables; exclude subjects with missing IDs and log count; **Move the downloaded file to `data/raw/` with a checksummed filename (e.g., `hcp_data_<sha256>.zip`) BEFORE any processing**; compute SHA256 and update `state/projects/PROJ-486-investigating-the-impact-of-network-topo.yaml` immediately; ensure raw data is preserved unchanged.
- [ ] T007 [P] Implement `code/main.py` orchestration skeleton: Argument parsing, error handling wrapper, and "Data Gap" exit protocol (Plan: Data Gap Handling Protocol).
- [ ] T008 [P] Setup `data/checksums.json` structure (optional cache) but ensure primary state is in YAML.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Core Correlation Analysis (Priority: P1) 🎯 MVP

**Goal**: Compute resting-state network topology metrics from HCP fMRI data and correlate them with external entrainment strength metrics.

**Independent Test**: Can be fully tested by executing the correlation pipeline on a subset of subjects and verifying that a scatter plot and correlation coefficient (r, p-value) are generated for the primary hypothesis.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T010a [P] [US1] Create `tests/unit/test_network_metrics.py` and write a test for `calculate_clustering_coefficient()` using a synthetic small matrix.
- [ ] T010b [P] [US1] Create `tests/unit/test_network_metrics.py` and write a test for `calculate_path_length()` using a synthetic small matrix.
- [ ] T011a [P] [US1] Create `tests/unit/test_analysis.py` and write a test for Spearman correlation logic with known synthetic data.
- [ ] T011b [P] [US1] Create `tests/unit/test_analysis.py` and write a test for VIF calculation logic.

### Implementation for User Story 1

- [ ] T012 [US1] Implement `code/data_loader.py`: Ingest external entrainment metrics from CSV (Source: `data/raw/entrainment_metrics.csv`); validate columns; perform inner join on Subject ID; exclude missing subjects and log count; **Call `validate_rhythmic_metadata()` and halt with "Data Gap: Missing rhythmic stimulus metadata" if validation fails**; **Trigger "Power Warning: N < 30 (Exploratory)" if inner join results in N < 30**; compute SHA256 and update `state/projects/PROJ-486-investigating-the-impact-of-network-topo.yaml` immediately.
- [ ] T012b [US1] Implement `code/data_loader.py`: **Explicitly validate the presence and structure of the HCP fMRI connectivity matrix variables** (e.g., ensure matrix dimensions match the atlas, columns are numeric) before the correlation pipeline begins; halt with "Invalid HCP Data" if validation fails (FR-007).
- [ ] T013a [US1] Implement `code/network_metrics.py`: Function `calculate_clustering_coefficient()` for weighted correlation matrices.
- [ ] T013b [US1] Implement `code/network_metrics.py`: Function `calculate_path_length()` for weighted correlation matrices.
- [ ] T013c [US1] Implement `code/network_metrics.py`: Zero-variance detection: If a metric has zero variance (std < 1e-9), flag it as "Non-informative" and halt correlation for that specific metric (Edge Case: Zero Variance).
- [ ] T014 [US1] Implement `code/analysis.py`: Calculate **Spearman correlation** between topology metrics and entrainment strength; **Skip calculation for any metric flagged "Non-informative" by T013c**.
- [ ] T015a [US1] Implement `code/analysis.py`: Calculate **VIF** between the two topology metrics to check collinearity in the joint model; flag "Collinearity Warning: VIF > 5" if threshold exceeded (FR-004).
- [ ] T015b [US1] Implement `code/analysis.py`: Apply Bonferroni correction (`min(raw_p * 2, 1.0)`) for the two tested metrics; add `adjusted_p_value` and `is_significant` columns (FR-004).
- [ ] T015c [US1] Implement `code/analysis.py`: Generate `data/processed/correlation_results.csv` containing subject IDs, metrics, r, p, adjusted p.
- [ ] T016 [US1] Implement `code/analysis.py`: Generate scatter plot with 95% confidence intervals using `matplotlib`; save to `data/visualizations/scatter_topology_entrainment.png`.
- [ ] T017 [US1] Implement `code/main.py`: Orchestrate full US1 pipeline: Load -> Validate -> Compute Metrics -> Correlate -> Plot.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Multiple Comparisons & Power Correction (Priority: P2)

**Goal**: Apply Bonferroni correction to p-values and report power limitations.

**Independent Test**: Can be fully tested by providing a synthetic dataset with known raw p-values, running the correction module, and verifying that the output p-values are scaled by the number of tests (N=2) and the significance threshold is correctly updated.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T019 [P] [US2] Unit test for Bonferroni correction logic in `tests/unit/test_analysis.py` with known inputs.

### Implementation for User Story 2

- [ ] T020 [US2] Verify output CSV matches acceptance scenario: **`raw_p`, `adjusted_p_value`, `is_significant`, `vif_value`, `vif_warning` columns present**; ensure `vif_warning` is 'True' if `vif_value > 5`.
- [ ] T021 [US2] Implement `code/analysis.py`: Inject "Power Warning: N < 30 (Exploratory)" string into the summary report if N < 30 (FR-002).
- [ ] T021a [US2] Implement `code/analysis.py`: **Explicitly output the calculated VIF value**: Add a column `vif_value` to `data/processed/correlation_results.csv` containing the VIF for the two topology metrics; append a line `VIF: {value} (Warning: >5)` to the summary report if VIF > 5 (FR-004, SC-003).
- [ ] T022 [US2] Update `code/main.py` to ensure the final report generation includes the corrected p-values and power warning logic.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Robustness Sensitivity Analysis (Priority: P3)

**Goal**: Re-run core correlation using alternative parcellation schemes (AAL, Power 264) to verify robustness.

**Independent Test**: Can be fully tested by swapping the input atlas config to "AAL" and verifying that the pipeline completes without error and produces a comparative result table.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T024 [P] [US3] Integration test swapping atlas config in `tests/integration/test_sensitivity.py`.

### Implementation for User Story 3

- [ ] T025 [US3] Implement `code/network_metrics.py`: Ensure metric calculation is atlas-agnostic (works with any correlation matrix input).
- [ ] T026 [US3] Implement `code/analysis.py`: Re-run correlation pipeline for alternative atlases (AAL, Power 264); generate comparative result table.
- [ ] T027 [US3] Implement `code/analysis.py`: Generate comparative **bar chart** showing **absolute difference in effect sizes (r)** between the primary Schaefer results and **BOTH** alternative schemes (AAL and Power 264). The chart MUST contain **distinct bars** for the absolute difference of AAL vs Schaefer and Power 264 vs Schaefer. Save to `data/visualizations/sensitivity_comparison.png` (FR-006, SC-002).
- [ ] T028 [US3] Implement `code/main.py`: Add loop or flag to execute sensitivity analysis if `--sensitivity` is passed.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T029 [P] Update `docs/quickstart.md` with execution instructions and data requirements.
- [ ] T030 [P] Run full integration test on a small subset of HCP data to verify runtime constraint within a practical timeframe. (SC-004). **If the constraint is violated, the task must fail the build and trigger an optimization review; do not proceed if runtime > 6h.**
- [ ] T031 [P] Verify "Data Gap" protocol: If entrainment data is missing, ensure pipeline halts with "Invalid Entrainment Data" or "Data Gap" error (specifically "Data Gap: Missing rhythmic stimulus metadata") and no scientific results are generated; ensure `data_gap_report.json` is created (Plan: Data Gap Handling).

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 results for correction
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US1 logic for re-execution

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Data loading/validation before metric calculation
- Metric calculation before correlation
- Correlation before visualization
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
Task: "Unit test for network_metrics.py using synthetic small matrix in tests/unit/test_network_metrics.py"
Task: "Unit test for analysis.py correlation logic with known synthetic data in tests/unit/test_analysis.py"

# Launch implementation for User Story 1 (sequential dependencies):
Task: "Implement data_loader.py: Download sample HCP data..."
Task: "Implement network_metrics.py: Calculate Clustering Coefficient..."
Task: "Implement analysis.py: Calculate Spearman correlation..."
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
- **Constraint**: All tasks MUST run on CPU-only CI (cores, GB RAM). No GPU, no 8-bit models, no large LLMs.
- **Data**: Use real HCP data or verified subsets. Do not fabricate scientific results.
- **Data Hygiene**: Checksums are recorded immediately in `state/projects/PROJ-486-investigating-the-impact-of-network-topo.yaml` upon download/ingest.