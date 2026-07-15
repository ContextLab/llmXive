# Tasks: 001-code-generation-performance-outcomes

**Input**: Design documents from `/specs/001-code-generation-performance-outcomes/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `tests/`, `data/` at repository root
- Paths shown below assume single project - adjust based on plan.md structure

---

## Phase 0: Dataset Acquisition & Citation Verification (CRITICAL BLOCKING)

**Purpose**: Acquire verified datasets and validate all citations BEFORE any ingestion or analysis

**⚠️ CRITICAL**: Pipeline halts until this phase completes - no data or analysis tasks may run

- [X] T000 [P] Search for public developer productivity datasets (OpenDev benchmark, GitHub Copilot studies) containing required variables; verify URLs accessible; add verified dataset(s) to `# Verified datasets` block in spec.md with SHA-256 checksums (FR-001 prerequisite)
- [X] T049 [P] [US1] Implement Reference-Validator Agent citation verification at `code/validate/citations.py` (Constitution Principle II) - validates all external citations before ingestion/analysis
- [X] T050 [P] [US1] Integrate Reference-Validator into pipeline at `code/main.py` (Constitution Principle II) - blocks if citations unverified before Phase 1 starts
- [X] T051 [P] [US1] Create citation verification report at `data/output/citation_validation.json` (Constitution Principle II) - records verification status; must pass before data ingestion

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001a [P] Create `code/` directory at repository root
- [X] T001b [P] Create `data/` directory with subdirectories `data/raw/`, `data/processed/`, `data/output/`
- [X] T001c [P] Create `tests/` directory with subdirectories `tests/unit/`, `tests/integration/`, `tests/contract/`
- [X] T001d [P] Initialize git repository and create `.gitignore` for Python at repository root
- [X] T002a [P] Create `code/requirements.txt` file with pinned dependencies (pandas>=2.0.0, numpy>=1.24.0, scipy>=1.11.0, scikit-learn>=1.3.0, matplotlib>=3.7.0, pyyaml>=6.0)
- [X] T002b [P] Install dependencies using `pip install -r code/requirements.txt` in virtualenv
- [X] T003a [P] Install black formatter in development environment
- [X] T003b [P] Install flake8 linter in development environment
- [X] T003c [P] Configure black pre-commit hook in `.pre-commit-config.yaml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T043 [P] Create data-model.md at `specs/001-code-generation-performance-outcomes/data-model.md` documenting DatasetRecord, AnalysisResult, VisualizationOutput entities
- [X] T004 [P] Create dataset schema contract at `specs/001-code-generation-performance-outcomes/contracts/dataset.schema.yaml` (DatasetRecord entity with tool_usage, task_time, defect_rate, experience_years, task_complexity, project_type, team_size)
- [X] T005 [P] Create analysis schema contract at `specs/001-code-generation-performance-outcomes/contracts/analysis.schema.yaml` (AnalysisResult entity with anova_table, effect_sizes, adjusted_p_values, associational_framing, confounding_controls)
- [X] T006 [P] Create visualization schema contract at `specs/001-code-generation-performance-outcomes/contracts/visualization.schema.yaml` (VisualizationOutput entity with plot_type, stratification_variable, interaction_lines, file_path)
- [X] T007 [P] Setup artifacts.yaml at `state/projects/PROJ-462-evaluating-the-impact-of-code-generation/artifacts.yaml` for checksum tracking
- [X] T008a [P] Create experiment configuration file at `code/config/experiment.yaml` (alpha=0.05, power=0.80, effect_size=0.5, min_observations_per_stratum=30)
- [X] T008b [P] Create experience classification module at `code/analysis/experience.py` with version-controlled thresholds (novice <2 years, intermediate 2-5 years, expert >5 years)
- [X] T009 [P] [US1] Create contract test for dataset schema at `tests/contract/test_dataset_schema.py`
- [X] T020 [P] [US2] Create contract test for analysis schema at `tests/contract/test_analysis_schema.py`
- [X] T031 [P] [US3] Create contract test for visualization schema at `tests/contract/test_visualization_schema.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and Validation (Priority: P1) 🎯 MVP

**Goal**: Download public developer productivity datasets and validate that all required variables are present before analysis begins

**Independent Test**: Can be fully tested by running the ingestion script against a known dataset and verifying the variable presence report without executing any statistical analysis

### Logging Infrastructure (US1)

- [X] T015 [P] [US1] Add logging for ingestion and validation operations at `code/ingest/logging.py` - establishes logging before implementation

### Implementation for User Story 1

- [X] T017 [P] [US1] Create sample dataset for testing at `data/raw/sample_developer_productivity.csv` with all required variables (tool_usage, task_time, defect_rate, experience_years, task_complexity, project_type, team_size)
- [X] T017a [P] [US1] Validate that actual public datasets (OpenDev, GitHub Copilot studies) match spec assumptions at `code/ingest/validate.py` (FR-002, Assumptions) - verify real datasets contain required variables before ingestion
- [X] T011a [US1] Write function to download dataset from URL at `code/ingest/download.py` (FR-001) - supports URLs from verified-datasets block
- [X] T011b [US1] Write function to calculate SHA-256 checksum at `code/ingest/download.py` (FR-001) - validates file integrity
- [X] T011c [US1] Implement checksum validation integration at `code/ingest/download.py` (FR-001) - compares calculated vs recorded checksum
- [ ] T012a [US1] Write function to check for tool_usage variable at `code/ingest/validate.py` (FR-002)
- [ ] T012b [US1] Write function to check for task_time variable at `code/ingest/validate.py` (FR-002)
- [ ] T012c [US1] Write function to check for defect_rate variable at `code/ingest/validate.py` (FR-002)
- [ ] T012d [US1] Write function to check for experience_years variable at `code/ingest/validate.py` (FR-002)
- [ ] T013a [US1] Write function to identify missing experience data values at `code/ingest/validate.py` (FR-010)
- [ ] T013b [US1] Write function to calculate percentage of missing entries at `code/ingest/validate.py` (FR-010)
- [X] T013c [US1] Implement missing data filtering with percentage reporting at `code/ingest/validate.py` (FR-010) - flag if >20% entries removed
- [X] T014 [US1] Add error handling for missing required variables at `code/ingest/validate.py` - halt with clear error identifying missing variable
- [X] T016 [US1] Implement SHA-256 checksum verification in download pipeline at `code/ingest/download.py` (FR-001)

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation

- [X] T010 [P] [US1] Create integration test for data ingestion pipeline at `tests/integration/test_pipeline.py` - validates against sample dataset from T017

### Edge Case Tests for User Story 1

- [X] T046a [P] [US1] Add unit tests for missing data edge cases at `tests/unit/test_data_validation.py` - tests filtering logic and >20% flagging

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Statistical Analysis with Methodological Controls (Priority: P2)

**Goal**: Perform two-way ANCOVA/ANOVA with interaction terms, calculate effect sizes, apply multiple-comparison corrections, and frame results as associational

**Independent Test**: Can be fully tested by running the analysis script on sample data and verifying that output includes ANOVA tables, effect sizes, and appropriate associational framing language

### Logging Infrastructure (US2)

- [X] T030 [P] [US2] Add logging for analysis operations at `code/analysis/logging.py` - establishes logging before implementation

### Implementation for User Story 2

- [X] T021a [US2] Write function to perform two-way ANOVA at `code/analysis/anova.py` (FR-003, FR-011) - tool usage × experience level
- [X] T021b [US2] Write function to calculate interaction term at `code/analysis/anova.py` (FR-003) - tool usage × experience level interaction
- [X] T021c [US2] Write function to extract p-values and F-statistics at `code/analysis/anova.py` (FR-003)
- [X] T022 [US2] Implement ANCOVA fallback when covariates available at `code/analysis/anova.py` (FR-011) - task_complexity, project_type, team_size as covariates
- [ ] T022a [US2] Write function to test for normality/homogeneity assumption violations at `code/analysis/anova.py` (SC-002) - Shapiro-Wilk, Levene's test before deciding on Welch's ANOVA
- [ ] T023 [US2] Implement Welch's ANOVA fallback for unequal variances at `code/analysis/anova.py` - apply when assumption violations detected in T022a
- [ ] T024 [US2] Implement Cohen's d effect size calculation at `code/analysis/effect_sizes.py` (FR-004, SC-004) - pairwise comparisons within experience strata
- [ ] T024b [US2] Implement paired output verification at `code/analysis/effect_sizes.py` (Constitution Principle VI) - ensure effect sizes reported alongside p-values in same result block
- [ ] T025 [US2] Implement Bonferroni/Holm-Bonferroni correction at `code/analysis/effect_sizes.py` (FR-005, SC-003) - family-wise error rate ≤0.05
- [ ] T026 [US2] Implement VIF diagnostics for collinearity at `code/analysis/anova.py` - flag if VIF > 5 (edge case handling)
- [ ] T027 [US2] Implement power analysis flagging at `code/analysis/anova.py` - flag if <30 observations per stratum (SC-006)
- [ ] T028 [US2] Implement associational framing enforcement at `code/analysis/anova.py` (FR-006) - no causal language permitted in output headers/summaries
- [ ] T029 [US2] Implement confounding control reporting at `code/analysis/anova.py` (FR-011, SC-008) - report adjusted effect estimates
- [ ] T034 [US2] Implement sensitivity analysis for experience thresholds at `code/analysis/sensitivity.py` (FR-009, SC-005) - sweep thresholds ∈ {1, 2, 3 years}
- [ ] T038 [US2] Add sensitivity analysis report generation at `code/analysis/sensitivity.py` (FR-009) - report variation in task completion time, defect rates, effect sizes

### Edge Case Tests for User Story 2

- [ ] T046b [P] [US2] Add unit tests for skewed distributions at `tests/unit/test_data_validation.py` - tests Welch's ANOVA fallback logic
- [ ] T046c [P] [US2] Add unit tests for collinearity handling at `tests/unit/test_data_validation.py` - tests VIF diagnostics and warning

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T018 [P] [US2] Create unit test for ANOVA calculation at `tests/unit/test_anova.py`
- [ ] T019 [P] [US2] Create unit test for effect size calculation at `tests/unit/test_effect_sizes.py`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Results Visualization and Export (Priority: P3)

**Goal**: Generate publication-ready visualizations and export results in CSV and JSON formats for reproducibility

**Independent Test**: Can be fully tested by running the visualization module on pre-computed analysis results and verifying output files are generated with correct formatting

### Logging Infrastructure (US3)

- [ ] T039 [P] [US3] Add logging for visualization and export operations at `code/viz/logging.py` - establishes logging before implementation

### Implementation for User Story 3

- [ ] T033a [US3] Write function to prepare boxplot data at `code/viz/plots.py` (FR-007, SC-005) - stratified by experience level
- [ ] T033b [US3] Write function to calculate interaction lines at `code/viz/plots.py` (FR-007) - connect group means across experience levels
- [ ] T033c [US3] Write function to render publication-ready boxplot at `code/viz/plots.py` (FR-007)
- [ ] T035 [US3] Implement CSV export of statistical outputs at `code/export/results.py` (FR-008)
- [ ] T036 [US3] Implement JSON export with metadata at `code/export/results.py` (FR-008)
- [ ] T036a [US3] Validate export file size stays within 14 GB disk limit at `code/export/results.py` (SC-007) - check file size before export completion; fail if exceeds limit
- [ ] T037 [US3] Implement visualization export at `code/viz/plots.py` (FR-007) - publication-ready formatting

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T032 [P] [US3] Create integration test for export pipeline at `tests/integration/test_export_pipeline.py`

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Constitution Compliance & Pipeline Orchestration

**Purpose**: Validate all outputs against schemas, implement constitution requirements, and orchestrate the complete pipeline

- [ ] T040a [P] Write function to orchestrate data ingestion at `code/main.py` - calls download and validate modules
- [ ] T040b [P] Write function to orchestrate statistical analysis at `code/main.py` - calls ANOVA and effect size modules
- [ ] T040c [P] Write function to orchestrate visualization and export at `code/main.py` - calls viz and export modules
- [ ] T041 [P] Implement final contract validation at `code/main.py` - validates `data/output/analysis.json` against `analysis.schema.yaml`
- [ ] T052 [P] [US3] Implement Single Source of Truth traceability verification at `code/validate/traceability.py` (Constitution Principle IV) - verifies figures/statistics trace to one data row + one code block
- [ ] T053 [P] [US1] Implement Repository-Hygiene Agent PII scan at `code/validate/pii_scan.py` (Constitution Principle III) - scans data files before commits
- [ ] T042 [P] Create quickstart.md at `specs/001-code-generation-performance-outcomes/quickstart.md` with execution instructions

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T044 [P] Update research.md at `specs/001-code-generation-performance-outcomes/research.md` to document ANCOVA methodology (FR-003 revision), dataset assumptions verification process, and FR-003/plan.md methodological resolution
- [ ] T045 [P] Run black formatter and flake8 linter on all `code/` modules; verify [deferred] pass rate with no errors or warnings (Constitution Principle I)
- [ ] T048 Run quickstart.md validation to verify pipeline completeness

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 0 (Dataset Acquisition)**: No dependencies - MUST complete first; blocks all other phases
- **Phase 1 (Setup)**: No dependencies - can start immediately (parallel with Phase 0)
- **Phase 2 (Foundational)**: Depends on Phase 1 completion - BLOCKS all user stories
- **User Stories (Phase 3-5)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Phase 6 (Constitution Compliance)**: Depends on all user stories being complete
- **Phase 7 (Polish)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on validated data from US1 for full testing
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on completed analysis from US2 for visualization

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models/contracts before services/analysis
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- All export and visualization tasks marked [P] can run in parallel

---

## Parallel Example: User Story 2

```bash
# Launch all ANOVA-related tasks together:
Task: "Write function to perform two-way ANOVA in code/analysis/anova.py"
Task: "Write function to calculate interaction term in code/analysis/anova.py"
Task: "Write function to extract p-values in code/analysis/anova.py"

# Launch all unit tests for US2 together:
Task: "Unit test for ANOVA calculation in tests/unit/test_anova.py"
Task: "Unit test for effect size calculation in tests/unit/test_effect_sizes.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 0: Dataset Acquisition & Citation Verification (CRITICAL - blocks all)
2. Complete Phase 1: Setup
3. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
4. Complete Phase 3: User Story 1 (Data Ingestion & Validation)
5. **STOP and VALIDATE**: Test data ingestion against verified dataset
6. Deploy/demo if ready

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
 - Developer A: User Story 1 (Data Ingestion)
 - Developer B: User Story 2 (Statistical Analysis)
 - Developer C: User Story 3 (Visualization & Export)
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
- **Dataset Requirement**: Pipeline halts until T000 completes - verified datasets must be added to `# Verified datasets` block (see plan.md)
- **Compute Constraint**: All methods MUST be CPU-only (no GPU/CUDA) to run on GitHub Actions free-tier
- **Associational Framing**: All findings MUST be explicitly labeled as "associational" not "causal" (FR-006)
- **Constitution Compliance**: Reference-Validator (Principle II), PII Scan (Principle III), SSoT Traceability (Principle IV) MUST be implemented in Phase 0 (citations) and Phase 6 (other validations)
- **Methodology Resolution**: T044 documents ANCOVA vs ANOVA distinction to resolve FR-003/plan.md methodological ambiguity