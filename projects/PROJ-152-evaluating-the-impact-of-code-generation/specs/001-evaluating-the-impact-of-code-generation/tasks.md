# Tasks: Evaluating the Impact of Code Generation Models on Code Security

**Input**: Design documents from `/specs/001-code-security-evaluation/`
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

## Phase 0: Spec & Plan Alignment (CRITICAL GATE)

**Purpose**: Resolve requirement conflicts and formally amend scope before implementation begins.

- [X] T000a [P] **AMEND SPEC**: Update `spec.md` (FR-002, SC-005) to explicitly reflect the amended scope of N=30 prompts (10 CodeXGLUE + 20 handcrafted) and N=90 snippets. Document the resource constraints (GitHub Actions GB RAM, time limit) as the justification for this amendment.
- [X] T000b [P] **ALIGN PLAN**: Update `plan.md` (Summary) to reflect the N=30 scope and ensure consistency with the amended `spec.md`.
- [X] T000c [P] **UPDATE COVERAGE MAP**: Update `plan.md` (FR/SC Coverage Map) to reflect the amended FR-002 (N=30 prompts) and SC-005 (6h limit), resolving the contradiction with the original "Generate 250 prompts" entry.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001a [P] Create `projects/PROJ-152-evaluating-the-impact-of-code-generation/` directory structure (`code/`, `data/`, `tests/`, `docs/`)
- [X] T001b [P] Create `projects/PROJ-152-evaluating-the-impact-of-code-generation/requirements.txt` with pinned versions (transformers, torch-cpu, bitsandbytes-cpu, scikit-learn, scipy, statsmodels, pandas, matplotlib, seaborn, bandit, semgrep, codeql)
- [X] T001c [P] Initialize Python 3.11 virtual environment using `python -m venv venv` and ensure `requirements.txt` is installed in the new environment.
- [X] T002 [P] Configure linting (ruff/flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T003 [P] Create `code/config.py` with pinned random seeds, path constants, and model hyperparameters (max_tokens=256, batch_size=1)
- [X] T004 [P] Create `code/update_state.py` to manage `state.yaml` and artifact hashing per Constitution Principle V
- [X] T005 [P] Implement `code/download.py` to fetch CodeXGLUE prompts from HuggingFace datasets, filter for security keywords (SQL, XSS, auth, injection, sanitize, password, token) using **keyword matching**, **select a subset of the most relevant candidates manually**, and **explicitly generate and checksum `data/prompts/filtered_codexglue.json`** as a distinct intermediate artifact. **Note**: This artifact must be saved before T010 combines it with handcrafted prompts. Justification: Resource constraints (N=30 total) require this reduction from the original FR-002 scope, and Constitution Principle III (Data Hygiene) requires the filtered subset to be a documented, checksummed derivation.
- [X] T006 [P] Create `data/prompts/handcrafted.json` with web-security prompts: **Multiple prompts each for database access, HTML rendering, authentication, and injection**
- [X] T007 [P] Create `data/mappings/nist_severity_map.yaml` with explicit NIST-based mapping rules (e.g., "High" -> 4, "Medium" -> 3) for severity conversion
- [X] T008a [P] Implement `code/generate.py` with **A timeout mechanism with a moderate duration is established.** handling using `signal.alarm` for generation and CPU-only -bit quantization loading for StarCoder-Base, CodeGen, GPT-NeoX (model loader logic). On timeout, log to `data/failures.log` and skip.
- [X] T008b [P] Implement `code/orchestrator.py` to track cumulative runtime across all generation and analysis tasks. **Logic**: Check elapsed time before each snippet generation. If `elapsed_time + estimated_time > 6 hours`, halt generation and log a "Time Budget Exceeded" warning to `data/failures.log`. **Output**: Update `data/runtime_log.json` with start/end times and status.
- [X] T009 [P] Implement `code/analyze.py` to orchestrate Bandit, Semgrep, and CodeQL with **A timeout mechanism with a configurable duration is implemented.** per scan using `subprocess` timeout.
- [X] T010 [P] Implement `code/prompts.py` to combine `data/prompts/filtered_codexglue.json` (T005) and `data/prompts/handcrafted.json` (T006) into a final `data/prompts/manifest.json` with source attribution and checksums. **Requires T005 and T006 completion**. **Note**: T010 is NOT parallel-safe; it must wait for T005 and T006.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Generate and analyze code snippets (Priority: P1) 🎯 MVP

**Goal**: Download three models, generate code from 30 standardized prompts, and run static analysis to collect vulnerability findings.

**Independent Test**: Run the generation and analysis pipeline on a subset of 5 prompts and verify the output CSV contains model, prompt, code, and vulnerability findings for each combination.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T011 [P] [US1] Integration test for generation pipeline with timeout handling in `tests/integration/test_generate.py`
- [X] T012 [P] [US1] Contract test for scanner output format in `tests/contract/test_scanner_output.py`

### Implementation for User Story 1

- [X] T013 [P] [US1] Implement model loader in `code/generate.py` to load multiple models (StarCoder-Base large-scale, CodeGen B, GPT-NeoX B) with -bit quantization (bitsandbytes CPU-compatible)
- [ ] T014 [US1] Implement generation loop in `code/generate.py` to process 30 prompts (N=90 snippets total) using `data/prompts/manifest.json` as input. **Output**: `data/generated/snippets.csv` with columns: `snippet_id, model, prompt_id, code, line_count, timestamp`. **Checksum**: Generate `data/generated/snippets.csv.sha256` using `sha256sum` and log the hash. Log failures to `data/failures.log`.
- [X] T015 [US1] Implement scanner runner in `code/analyze.py` to pipe snippets through Bandit (Python), Semgrep (security rules), CodeQL (Java/JS)
- [X] T016a [US1] Implement severity mapping in `code/metrics.py` to convert raw scanner labels to NIST-based ordinal rank using `data/mappings/nist_severity_map.yaml`. **Logic**: Map Bandit 'HIGH'->4, 'MEDIUM'->3, 'LOW'->2; Semgrep 'ERROR'->5, 'WARNING'->3, 'INFO'->1; CodeQL 'High'->4, 'Medium'->3, 'Low'->2.
- [ ] T016b [US1] Implement CWE extraction in `code/metrics.py` to parse CWE IDs from scanner output (Bandit, Semgrep, CodeQL) and map them to the findings CSV. **Output**: Update `data/findings/raw_findings.csv` with `cwe_id` column. <!-- FAILED: unspecified -->
- [X] T017 [US1] Implement failure logging in `code/analyze.py` for empty snippets, unsupported languages, and scanner errors per Edge Cases
- [ ] T018 [US1] **REMOVED**: Merged into T014. <!-- FAILED: unspecified -->
- [ ] T019 [US1] **REMOVED**: Merged into T016a/T016b.

**Checkpoint**: User Story 1 is ready for execution (T014 and T016a/b pending implementation).

---

## Phase 4: User Story 2 - Compute metrics and statistical comparison (Priority: P2)

**Goal**: Compute V/100LOC and mean severity, apply Kruskal-Wallis/Dunn tests, perform ZINB robustness check (conditional), and run sensitivity analysis.

**Independent Test**: Feed a synthetic dataset with known differences and verify Kruskal-Wallis detects significance (p < 0.05) and ZINB converges on zero-inflated data.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T020 [P] [US2] Unit test for V/100LOC calculation in `tests/unit/test_metrics.py`
- [X] T021 [P] [US2] Unit test for Bonferroni correction in `tests/unit/test_stats.py`

### Implementation for User Story 2

- [ ] T022a [US2] **Automated**: Implement `code/calibration.py` to generate `data/calibration/calibration_template.csv` (a CSV template with `snippet_id, model, prompt_id` and a `human_label` column) and `data/calibration/calibration_instructions.md` (guidelines for human experts). **Do not perform labeling**.
- [ ] T022b [US2] **MANUAL EXECUTION**: Human experts must label the snippets per model using the template from T022a. **Output**: `data/calibration/human_labels.csv`. **This task is a placeholder for human action and must be completed before T022d**. <!-- ATOMIZE: requested -->
- [ ] T022c [US2] **Automated**: Implement `code/calibration.py` to compute **Descriptive Stats**: Read `raw_findings.csv` and `human_labels.csv`. Calculate Inter-Rater Reliability (Kappa) and **False Positive Rate (FPR) per scanner/model**. **Output**: `data/calibration/fpr_stats.csv`.
- [ ] T022d [US2] **Automated**: Implement `code/calibration.py` to **Validate** `data/calibration/human_labels.csv`. **Logic**: Check file existence, schema validity (required columns), and non-empty row count. **Fail** the pipeline if validation fails. **Output**: `data/calibration/validation_report.json`. **Depends on T022b**.
- [~] T023 [US2] Implement `code/metrics.py` to compute **Raw Metrics**: Read `raw_findings.csv` and `data/generated/snippets.csv`. Calculate V/100LOC and mean severity **WITHOUT FPR correction**. **Output**: `data/results/raw_metrics.csv`. **Note**: Statistical tests (T024/T025) MUST consume `raw_metrics.csv` per Spec Limitations (manual step is for reporting only).
- [~] T023b [US2] Implement `code/metrics.py` to compute **FPR-Corrected Metrics**: Read `raw_findings.csv` and `fpr_stats.csv` (from T022c). Apply FPR correction to vulnerability counts. **Output**: `data/results/corrected_metrics.csv`. **Usage**: This file is for **sensitivity analysis and reporting only**, NOT for primary statistical tests (T024/T025).
- [X] T024 [US2] Implement `code/stats.py` to run Kruskal-Wallis test on **raw** V/100LOC (from T023 output) across models
- [X] T025 [US2] Implement `code/stats.py` to run Dunn's post-hoc with Bonferroni correction (α = 0.0167) if KW p < 0.05
- [ ] T026 [US2] Implement `code/stats.py` to run Zero-Inflated Negative Binomial (ZINB) regression **CONDITIONALLY**. **Logic**: If zero-inflation > 50% (calculated in T023), run ZINB; else skip. **Library**: `statsmodels.discrete.discrete_model.ZeroInflatedNegativeBinomialP`. **Formula**: `vuln_count ~ model + offset(log(LOC))` for count, `zero_inflated ~ model` for zero-inflation. **Output**: `data/results/zinb_results.csv` (if run).
- [ ] T027 [US2] Implement `code/sensitivity.py` to sweep high-severity cutoffs across a range of thresholds and report proportion of "high risk" snippets per FR-009. **Input**: Use `corrected_metrics.csv` (T023b) for this analysis.
- [ ] T028 [US2] Generate `data/results/statistical_summary.csv` with test name, statistic, p-value, adjusted p-value, conclusion. **Input**: Read `raw_metrics.csv` (T023), `kw_results.csv` (T024), `dunn_results.csv` (T025), and `zinb_results.csv` (T026).
- [ ] T029 [US2] Generate `data/results/sensitivity_analysis.csv` with cutoff threshold, high-risk proportion per model

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Generate visualizations and summary reports (Priority: P3)

**Goal**: Produce box-plots of vulnerability density, heat-maps of CWE distribution, and a summary table of statistical results.

**Independent Test**: Run the visualization module on summary statistics and verify three output files: box-plot PNG, heat-map PNG, summary CSV.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T030 [P] [US3] Integration test for visualization generation in `tests/integration/test_viz.py`

### Implementation for User Story 3

- [ ] T031 [US3] Implement `code/viz.py` to generate box-plot PNG of V/100LOC per model with median, quartiles, outliers
- [ ] T032 [US3] Implement `code/viz.py` to generate heat-map PNG of CWE frequency per prompt category
- [ ] T033 [US3] **REMOVED**: Merged into T028.
- [ ] T034 [US3] Generate `data/results/run_summary.csv` with completion rate, total snippets (N=90), failure counts per SC-005 (amended scope)
- [ ] T035 [US3] Update `state.yaml` with artifact hashes and `updated_at` timestamp per Constitution Principle V

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T036a [P] Update `README.md` with project overview, setup instructions, and scope (N=30 prompts)
- [ ] T036b [P] Update `docs/quickstart.md` with detailed execution guide
- [ ] T036c [P] Update `docs/research.md` with methodology, limitations, and FPR correction justification
- [ ] T037a [P] Code cleanup: Remove unused imports in `code/` modules
- [ ] T037b [P] Code cleanup: Enforce black formatting across `code/`
- [ ] T037c [P] Code cleanup: Add docstrings to all public functions in `code/`
- [ ] T038 [P] Performance optimization for model loading/unloading sequence
- [ ] T039 [P] Additional unit tests in `tests/unit/` for edge cases
- [ ] T040 Security hardening of generated code handling (ensure no execution)
- [ ] T041 Run `quickstart.md` validation

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 0 (T000a, T000b, T000c)**: No dependencies - MUST be completed first to resolve spec conflicts and amend scope.
- **Setup (Phase 1)**: No dependencies - can start after Phase 0.
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories.
 - T005, T006, T007 must complete before T010.
 - T013 must complete before T014.
 - T008a, T008b, T009 must complete before T015.
- **User Stories (Phase 3+)**: All depend on Foundational phase completion.
 - US1 (Phase 3) depends on Foundational.
 - US2 (Phase 4) depends on US1 output (findings) and T022b (Manual Calibration).
 - US3 (Phase 5) depends on US2 output (statistics).
- **Polish (Final Phase)**: Depends on all desired user stories being complete.

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories.
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 output (findings) and T022b (calibration).
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 output (statistics).

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation.
- Models before services.
- Services before endpoints.
- Core implementation before integration.
- Story complete before moving to next priority.

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel.
- All Foundational tasks marked [P] can run in parallel (within Phase 2), noting T010 requires T005/T006 and is NOT parallel-safe.
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows).
- All tests for a user story marked [P] can run in parallel.
- Models within a story marked [P] can run in parallel.
- Different user stories can be worked on in parallel by different team members.

### Explicit Execution Chain (Phase 4)

- **T022a** (Generate Interface) -> **T022b** (Manual Human Labeling) -> **T022d** (Validate Labels) -> **T022c** (Compute FPR) -> **T023** (Compute Raw Metrics) -> **T023b** (Compute Corrected Metrics) -> **T024/T025/T026** (Statistical Tests) -> **T028** (Summary Generation).
- **T026** must run conditionally based on zero-inflation check.
- **T028** must read `zinb_results.csv` (if present) and `raw_metrics.csv` to produce the final summary.

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Integration test for generation pipeline with timeout handling in tests/integration/test_generate.py"
Task: "Contract test for scanner output format in tests/contract/test_scanner_output.py"

# Launch all models for User Story 1 together:
Task: "Implement model loader in code/generate.py to load 3 models..."
Task: "Implement generation loop in code/generate.py to process 30 prompts..."
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 0: Spec Alignment (T000a, T000b, T000c)
2. Complete Phase 1: Setup
3. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
4. Complete Phase 3: User Story 1
5. **STOP and VALIDATE**: Test User Story 1 independently
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
- **CRITICAL**: All model loading MUST use 4-bit quantization on CPU only (no CUDA/bitsandbytes GPU requirements).
- **CRITICAL**: Dataset N=30 prompts (10 CodeXGLUE + 20 handcrafted) to fit 6h/7GB budget; A large number of prompts is infeasible. (amended in T000a).
- **CRITICAL**: FPR data MUST be used for sensitivity analysis ONLY. Primary statistical analysis MUST use RAW metrics (T023) per Spec Limitations (T023b).
- **CRITICAL**: ZINB regression (T026) is CONDITIONAL on zero-inflation > 50% (calculated in T023), aligning with Plan.md.
- **CRITICAL**: T022d (Validate Human Labels) is a mandatory checkpoint before T022c proceeds.
- **CRITICAL**: T005 must explicitly generate `data/prompts/filtered_codexglue.json` as a checksummed artifact to satisfy Constitution Principle III (Data Hygiene).
- **CRITICAL**: T008b (Global Time Budget Orchestrator) is required to enforce the 6-hour limit.
- **CRITICAL**: T014 and T016a/b must generate checksums (`sha256sum`) for their output files.