# Tasks: llmXive follow-up: extending "Mellum2 Technical Report"

**Input**: Design documents from `/specs/001-llmxive-complexity-loss/`
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

- [ ] T001a Create root directory structure (`projects/PROJ-877-llmxive-follow-up-extending-mellum2-tech/`) and subdirectories (`code/`, `data/`, `tests/`, `docs/`)
- [ ] T001b Create `requirements.txt` with exact versions for datasets, transformers, tree-sitter, codeql, scikit-learn, statsmodels, pandas, numpy, matplotlib, seaborn, kenlm
- [ ] T001c Create `.gitignore` and `README.md` with project overview
- [ ] T002 Initialize Python project with `requirements.txt` (datasets, transformers, tree-sitter, codeql, scikit-learn, statsmodels, pandas, numpy, matplotlib, seaborn, kenlm)
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented. **Includes Pilot Feasibility Check.**

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Implement `code/config.py` with paths, random seeds, and hyperparameter defaults
- [ ] T005 [P] Setup `data/` directory structure (`raw/`, `processed/`, `results/`) with SHA-256 checksumming utilities in `code/data/checksum.py`
- [ ] T006 [P] Implement robust error handling and logging infrastructure in `code/utils/logging.py` (must handle parse errors, timeouts, OOMs gracefully as per Edge Cases)
- [ ] T007 Create base entity schemas (`CodeChunk`, `Threshold`, `CorrelationResult`) in `code/contracts/` with explicit field definitions
- [ ] T008 Setup environment configuration management (`.env` handling for HF token)
- [ ] T014a [P] Implement timeout enforcement and benchmarking logic in `code/utils/timeout.py` to enforce a fixed per-chunk duration constraint (FR-003); must raise `TimeoutError` on breach.
- [ ] T026 [P] [US1] Implement `code/analysis/feasibility.py` (Pilot Sample & Feasibility Check): 
    - **Input**: Fetch a small pilot sample (N=50) of code chunks from `codeparrot/github-code` (Python/Java) using `code/data/download.py` logic.
    - **Dependency**: **MUST run after T014a** (timeout logic available) and **before T012** (full download) and T013.
    - **Action**: Run static analysis and a *small-scale* LLM inference (TinyLlama-1.1B, CPU) on these 50 chunks.
    - **Output**: Calculate preliminary effect size (correlation) and variance. Compute the required sample size N to achieve [deferred] power within the total pipeline limit.
    - **Gate**: If calculated N > max feasible chunks for 6h limit, **log a WARNING** and report the limitation in `data/results/feasibility_report.json` with `final_sample_size: max_feasible`. **DO NOT raise SystemExit(1)**. Proceed with the max feasible sample size.
    - **Artifact**: `data/results/feasibility_report.json`.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Correlation Analysis of Code Complexity and Prediction Loss (Priority: P1) 🎯 MVP

**Goal**: Download code, label with static analysis, run frozen LLM inference, compute correlations, and generate scatter plots.

**Independent Test**: The system can be fully tested by executing the data pipeline on a fixed sample of repositories and verifying that a correlation coefficient (Pearson/Spearman) is computed and a scatter plot is generated, regardless of the specific value of the correlation.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T009 [P] [US1] Unit test for dataset download logic in `tests/unit/test_download.py`
- [ ] T010 [P] [US1] Unit test for static analysis parsing in `tests/unit/test_preprocess.py`
- [ ] T011 [P] [US1] Unit test for LLM loss calculation in `tests/unit/test_inference.py`

### Implementation for User Story 1

- [ ] T012 [US1] Implement `code/data/download.py` to fetch `codeparrot/github-code` subset (Python/Java) with streaming to stay within Disk storage constraints.
    - **Logic**: Fetch dataset. Split immediately into `data/processed/train_python/` and `data/processed/val_java/` based on language metadata.
    - **Constraint**: MUST fail loudly on fetch error. If fetch fails, log "ERROR: Failed to fetch dataset: <reason>" and execute `sys.exit(1)`. No synthetic fallback.
    - **Artifact**: `data/processed/train_python/`, `data/processed/val_java/`.

- [ ] T013 [US1] Implement `code/data/preprocess.py` to run CodeQL and tree-sitter.
    - **Dependency**: Must run AFTER T012 (Download/Split).
    - **Logic**: Create `queries/complexity.ql` for cyclomatic complexity, nesting depth, and repetition ratio. Process files in `data/processed/train_python/` and `data/processed/val_java/`.
    - **Edge Case**: MUST skip unparseable files and log errors (Edge Case 1).
    - **Artifact**: `data/processed/annotated_python.jsonl`, `data/processed/annotated_java.jsonl`.

- [ ] T014 [US1] Implement `code/data/inference.py` to run frozen LLM (TinyLlama) with retry logic and n-gram normalization.
    - **Dependency**: Must run AFTER T012, T013, T014a (Timeout logic), and T026 (Feasibility Report).
    - **Constraint**: MUST load model with **`device='cpu'`** and **`torch.set_num_threads(2)`** to enforce CPU-only execution (FR-003). Explicitly document deviation from spec examples (Llama-3-8B/Mistral-7B) due to CPU constraints.
    - **Retry Logic**: On `TimeoutError`, `ConnectionError`, or `OSError`, retry up to 3 times with `backoff_factor=2`. If all retries fail, skip chunk and log failure.
    - **Normalization**: Build/load kenlm n-gram model (if not already present) to normalize per-token loss by n-gram probability (FR-010).
    - **Artifact**: `data/processed/inference_results_python.jsonl`, `data/processed/inference_results_java.jsonl` (fields: `chunk_id`, `token_loss`, `entropy`, `normalized_loss`).

- [ ] T015 [US1] Implement `code/analysis/correlation.py` to compute Pearson/Spearman coefficients.
    - **Dependency**: Must run AFTER T014 (Inference).
    - **Logic**: Use normalized loss from T014. Compute correlations.
    - **Artifact**: `data/results/us1_correlation_stats.json`.

- [ ] T016 [US1] Implement `code/analysis/correlation.py` visualization.
    - **Dependency**: Must run AFTER T015.
    - **Logic**: Generate scatter plot with regression line using `seaborn.regplot`.
    - **Artifact**: Save plot to `data/results/us1_correlation_plot.png`.
    - **Edge Case**: MUST detect lack of variance in metrics; if detected, output structured JSON report with `variance_status: null` and exit code 2.
    - **Stratification**: Generate separate plots/stats for Python and Java sets.

- [ ] T018 [US1] Implement `code/main.py` pipeline orchestration.
    - **Logic**: Ensure strict order: Download (T012) -> Preprocess (T013) -> Feasibility (T026) -> Inference (T014) -> Correlation (T015) -> Visualization (T016).
    - **Dependency**: Must **explicitly wire T014a timeout logic into T014 execution flow**.

- [ ] T018b [US1] Implement `code/analysis/correlation.py` extension for cross-language validation.
    - **Logic**: Compare correlation coefficients between Python (train) and Java (val) sets.
    - **Artifact**: Append cross-language comparison stats to `data/results/us1_correlation_stats.json`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently (Correlation computed, plot generated, held-out validation complete).

---

## Phase 4: User Story 2 - Non-Linear Threshold Detection (Priority: P2)

**Goal**: Identify structural thresholds where complexity/loss relationship shifts and perform sensitivity analysis.

**Independent Test**: The system can be tested by running the change-point detection on the P1 output and verifying that either a threshold value is identified OR a linear model is preferred (AIC/BIC difference > 2), and a sensitivity analysis is performed.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T019 [P] [US2] Unit test for piecewise regression logic in `tests/unit/test_threshold.py`

### Implementation for User Story 2

- [ ] T020 [US2] Implement `code/analysis/threshold.py` to apply piecewise regression/change-point detection on US1 correlation data (FR-005).
    - **Input**: `data/results/us1_correlation_stats.json`.
    - **Artifact**: `data/results/us2_threshold_candidates.json`.

- [ ] T021 [US2] Implement logic in `code/analysis/threshold.py` to compare linear vs. non-linear models using AIC/BIC and report preference.
    - **Artifact**: Append `model_preference` to `data/results/us2_threshold_candidates.json`.

- [ ] T022 [US2] Implement `code/analysis/threshold.py` sensitivity analysis.
    - **Logic**: Sweep threshold values with explicit 0.05 unit perturbation magnitude (±0.01, ±0.05, ±0.1).
    - **Constraint**: MUST assert that the resulting shift in the identified threshold is ≤ 0.05 units (SC-002). If shift > 0.05, log failure and set `sc002_pass: false`.
    - **Artifact**: Append `sensitivity_analysis` and `sc002_pass` to `data/results/us2_threshold_candidates.json`.

- [ ] T023 [US2] Implement `code/analysis/threshold.py` to generate a report.
    - **Format**: Markdown file at `data/results/us2_threshold_report.md`.
    - **Sections**:
        1. `# Threshold Value` (Identified value)
        2. `# Sensitivity Sweep Results` (Table of shifts)
        3. `# Justification` (Data distribution or community standards)
    - **Artifact**: `data/results/us2_threshold_report.md`.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently (Thresholds identified, sensitivity report generated).

---

## Phase 5: User Story 3 - Statistical Significance and Power Validation (Priority: P3)

**Goal**: Perform permutation tests, power analysis, and multiple-comparison correction.

**Independent Test**: The system can be tested by running the permutation test (shuffling labels) and verifying that a p-value is calculated and reported, along with a statement on statistical power.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T024 [P] [US3] Unit test for permutation test logic in `tests/unit/test_stats.py`

### Implementation for User Story 3

- [ ] T025 [US3] Implement `code/analysis/stats.py` for cluster-robust permutation test (block permutation at repo level) to compute p-values (FR-007).
    - **Artifact**: `data/results/us3_permutation_pvalue.json`.

- [ ] T027 [US3] Implement `code/analysis/stats.py` for multiple-comparison correction (Bonferroni/FDR) on hypothesis tests (FR-008).
    - **Artifact**: `data/results/us3_corrected_pvalues.json`.

- [ ] T028 [US3] Implement `code/analysis/stats.py` to validate against CodeXGLUE benchmark.
    - **Source**: `codeparrot/codeXGLUE` (split: `test`).
    - **Logic**: Compute Pearson r between proxy metrics and CodeXGLUE labels.
    - **Fallback**: If benchmark dataset is missing, log "WARNING: CodeXGLUE benchmark unavailable", set `validation_status: unavailable` in `data/results/us3_validation.json`, and exit with code 0 (do NOT fail).
    - **Artifact**: `data/results/us3_validation.json`.

**Checkpoint**: All user stories should now be independently functional (Significance, Power, and Cross-language validation complete).

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T030 [P] Documentation updates in `README.md` and `docs/`
- [ ] T031a [P] Refactor `code/analysis/correlation.py`: Extract complex correlation logic into a dedicated `compute_correlation_matrix` function to reduce cyclomatic complexity to < 10.
- [ ] T031b [P] Refactor `code/analysis/threshold.py`: Simplify threshold detection logic by extracting the AIC/BIC comparison into a separate `compare_models` function.
- [ ] T032 Performance optimization (ensure the specified latency limit is met with streaming/chunking)
- [ ] T033 [P] Additional unit tests for edge cases in `tests/unit/`
- [ ] T034 Run `quickstart.md` validation
- [ ] T035 Update `state/projects/PROJ-877-llmxive-follow-up-extending-mellum2-tech.yaml` with data checksums

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
  - **T026 (Feasibility)**: Depends on T014a (timeout logic). Must run BEFORE T012 (Download), T013 (Preprocess), and T014 (Full Inference).
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - **T012**: No dependencies (within Phase 3)
  - **T013**: Depends on T012
  - **T014**: Depends on T012, T013, T014a, T026
  - **T015**: Depends on T014
  - **T016**: Depends on T015
  - **T018**: Orchestrates all above
  - **T020, T021, T022, T023**: Depends on T015 (US1 output)
  - **T025, T027, T028**: Depends on T015 (US1 output)

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data output (T015)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US1 data output (T015)

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models/Contracts before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] (T004-T008, T014a, T026) can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for dataset download logic in tests/unit/test_download.py"
Task: "Unit test for static analysis parsing in tests/unit/test_preprocess.py"

# Launch all models for User Story 1 together:
Task: "Create base entity schemas in code/contracts/"
Task: "Setup logging infrastructure in code/utils/logging.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories, includes Feasibility Check T026)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (Correlation & Plot)
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo (Thresholds)
4. Add User Story 3 → Test independently → Deploy/Demo (Significance)
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (Core Pipeline)
   - Developer B: User Story 2 (Thresholds)
   - Developer C: User Story 3 (Stats)
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
- **Data Integrity**: All data loading tasks MUST fail loudly on real fetch errors; no synthetic fallbacks allowed.
- **Compute Constraints**: All inference tasks must be optimized for CPU-only execution within h/14GB limits; streaming is mandatory for large datasets.
- **Feasibility**: T026 ensures the sample size is feasible before full inference runs.

## Constitution Check (Revised for SC-002 Compliance)

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Compliance Strategy |
|-----------|--------|---------------------|
| **I. Reproducibility** | PASS | `random.seed()` pinned in all scripts; `requirements.txt` with exact versions; dataset fetched from canonical HF source; CI runs on fresh runner. |
| **II. Verified Accuracy** | PASS | All citations in `research.md` will be validated by the **Reference-Validator Agent** against the `# Verified datasets` block before proceeding to implementation. |
| **III. Data Hygiene** | PASS | `data/` files checksummed; raw data immutable; derived data in new files; PII scan in CI. |
| **IV. Single Source of Truth** | PASS | All figures/stats in paper trace to `data/` rows via script output logs. |
| **V. Versioning Discipline** | PASS | A CI job computes **SHA-256** hashes of all files in `data/` and updates `state/projects/PROJ-877-llmxive-follow-up-extending-mellum2-tech.yaml` with these hashes. |
| **VI. Static Analysis Inference Independence** | PASS | Pipeline stages strictly ordered: 1. Download, 2. Static Analysis (CodeQL/tree-sitter), 3. LLM Inference (frozen). No feedback loop. |
| **VII. Non-Linear Threshold Detection Rigor** | PASS | Plan includes piecewise regression/change-point detection (not just linear) and sensitivity analysis with explicit **0.05 unit perturbation magnitude** and **assertion** as required by SC-002. |