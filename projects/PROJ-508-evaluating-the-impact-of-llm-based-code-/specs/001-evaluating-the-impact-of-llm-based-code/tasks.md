# Tasks: Evaluating the Impact of LLM-Based Code Completion on Developer Cognitive Load

**Input**: Design documents from `/specs/001-evaluating-the-impact-of-llm-based-code-completion/`
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

## Phase 0: Spec Updates (Critical Prerequisites)

**Purpose**: Update `spec.md` to formally authorize methodological changes, new metrics, and specific report sections before implementation begins. This ensures all downstream tasks have a valid requirement anchor and resolves conflicts between the plan and the current spec text.

**⚠️ BLOCKING**: No other phase can begin until Phase 0 is complete and the spec artifact is updated.

- [ ] T004 [US2] **Spec Update**: Update `spec.md` to add **FR-008** and **SC-008**. <!-- FAILED: unspecified -->
 - **FR-008 Text**: "The system MUST calculate `diff_complexity_score` = (lines_added + lines_deleted) / total_lines if lines_deleted > 0 else 0. It MUST flag 'AI Noise' if `diff_complexity_score` > 0.3 AND commit message contains 'fix', 'hotfix', or 'patch'."
 - **SC-008 Text**: "The analysis must produce a stratified result showing how the 'LLM Adoption' effect size changes when controlling for 'AI Noise' or when filtering for specific commit types."
 - **Rationale**: Authorizes the 'Signal Separation' analysis (Phase 7) to address Feynman's concern.

- [X] T005 [US3] **Spec Update**: Update `spec.md` to add **FR-009** and **SC-009**.
 - **FR-009 Text**: "The final report MUST include a 'Theoretical Grounding' section citing Holland et al. on distributed cognition and a 'Data Gap' section explicitly stating the unavailability of self-report scales (e.g., NASA-TLX)."
 - **SC-009 Text**: "The report must explicitly state: 'Note: This study uses proxy metrics for cognitive load. Self-report measures (e.g., NASA-TLX) were not available.' "
 - **Rationale**: Authorizes specific report content (Phase 5) not previously in the spec.

- [X] T006 [US2] **Spec Update**: Update `spec.md` **FR-003** to replace "linear regression analysis" with "Mixed-Effects Models (GLMM) with random intercepts for repositories; Zero-Inflated Negative Binomial (ZINB) or Hurdle models for zero-inflated outcomes."
 - **Rationale**: Authorizes the statistical engine change from the plan to the spec, ensuring implementation aligns with updated requirements.

- [X] T007 [US1] **Spec Update**: Update `spec.md` **FR-002** to replace "EXCLUDING any push event where the commit message contains 'Copilot' OR the diff size is < 100 lines" with "Count TOTAL push events between PR open and merge (no exclusions)."
 - **Rationale**: Resolves the circular bias conflict in the original spec; authorizes the implementation logic in T023.

**Checkpoint**: Spec is updated and ready for implementation.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T008 Create directory `projects/PROJ-508-evaluating-the-impact-of-llm-based-code-/data/raw/`
- [X] T009 Create directory `projects/PROJ-508-evaluating-the-impact-of-llm-based-code-/data/derived/`
- [ ] T010 Create directory `projects/PROJ-508-evaluating-the-impact-of-llm-based-code-/docs/output/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T011 Initialize Python 3.11 project with `requirements.txt` dependencies: `pandas`, `requests`, `scikit-learn`, `statsmodels`, `matplotlib`, `seaborn`, `pyyaml`, `scipy`
- [ ] T012 [P] Configure linting (ruff) and formatting (black) tools
- [X] T013 [P] Implement `code/utils/github_client.py` with exponential backoff retry logic (a limited number of retries with a fixed delay)
- [ ] T014 [P] Create `code/utils/metrics.py` for cognitive load proxy calculation (NO Copilot exclusion logic)
- [~] T015 Create `code/utils/config.py` for environment variables and API key handling
- [~] T016 Setup `pytest` configuration and basic test scaffolding in `tests/`
- [~] T017 Implement `code/utils/data_validation.py` for PII scanning and schema validation

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and LLM Adoption Classification (Priority: P1) 🎯 MVP

**Goal**: Identify a corpus of GitHub repositories, classify LLM adoption, and extract PR metadata to establish the independent variable and dependent variables.

**Independent Test**: The system can be tested by running the ingestion script against a known subset of repositories (some with `.cursorrules`, others without) and verifying that the output CSV correctly flags the LLM adoption status and contains non-empty rows for review metrics.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [~] T018 [P] [US1] Unit test for `.cursorrules` detection in `tests/test_ingest.py`
- [~] T019 [P] [US1] Unit test for commit message "Copilot" frequency calculation in `tests/test_ingest.py`
- [~] T020 [P] [US1] Integration test for GitHub API retry logic in `tests/test_github_client.py`

### Implementation for User Story 1

- [~] T021 [US1] Implement `code/ingest.py` to fetch repository list and metadata (PRs, commits, config files)
- [~] T022 [US1] Implement `llm_adoption_flag` logic in `code/ingest.py`:
 - Check for `.cursorrules` or `copilot` config files
 - Check `README.md`/`CONTRIBUTING.md` for "Copilot"/"LLM" mentions (A fixed-length context window of moderate size will be employed to evaluate performance.)
 - Check commit messages for ≥5% "Copilot"/"LLM" frequency
- [~] T023 [US1] Implement `iteration_count` logic in `code/utils/metrics.py` **[FR-002-UPDATED]**:
 - **Logic**: Count TOTAL push events between PR open and merge (NO exclusions).
 - **Rationale**: Per updated `spec.md` FR-002 (Task T007).
- [~] T024 [US1] Implement extraction of `avg_comment_length`, `review_thread_depth`, and `revert_frequency`
- [~] T025 [US1] Implement logic to exclude repositories with <10 PRs in last 12 months (SC-001)
- [~] T026 [US1] Implement `code/ingest.py` to log "ambiguous LLM signal" warnings for repos with generic configs (e.g., `config.json` without tool naming) to support sensitivity analysis
- [~] T027 [US1] Implement domain complexity calculation (unique languages + dependency count from manifests)
- [~] T028 [US1] Generate `data/derived/master_dataset.csv` with all required columns
- [~] T029 [US1] Generate `data/manifest.json` with API endpoints, parameters, and timestamps

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Statistical Analysis and Hypothesis Testing (Priority: P2)

**Goal**: Compute regression models to test the association between LLM adoption and cognitive load proxies, controlling for confounders, applying multiple-comparison corrections, and performing sensitivity analysis.

**Independent Test**: The system can be tested by running the analysis script on a synthetic dataset where the correlation is hardcoded; the output must report a statistically significant coefficient matching the synthetic input.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [~] T030 [P] [US2] Unit test for Bonferroni correction logic in `tests/test_analysis.py`
- [~] T031 [P] [US2] Unit test for VIF calculation in `tests/test_analysis.py`
- [~] T032 [P] [US2] Unit test for sensitivity analysis sweep logic in `tests/test_analysis.py`

### Implementation for User Story 2

- [~] T033 [US2] Implement `code/analyze.py` to load `data/derived/master_dataset.csv`
- [~] T034 [US2] Implement Mixed-Effects Models (GLMM) with random intercepts for repositories **[FR-003-UPDATED]**:
 - **Rationale**: Per updated `spec.md` FR-003 (Task T006) and plan.md "Critical Methodological Update".
- [~] T035 [US2] Implement Zero-Inflated Negative Binomial (ZINB) or Hurdle models for zero-inflated outcomes (reverts/iterations) **[FR-003-UPDATED]**:
 - **Rationale**: Per updated `spec.md` FR-003 (Task T006) and plan.md "Critical Methodological Update".
- [~] T036 [US2] Implement control variable adjustment: Project size (LOC), Team size (contributors), Domain complexity, and `diff_complexity_score` (FR-008)
- [~] T037 [US2] Implement Variance Inflation Factor (VIF) check; flag if >5.0
- [~] T038 [US2] Implement Multiple-Comparison Correction (Bonferroni) for p-values (FR-004)
- [~] T039 [US2] Implement Sensitivity Analysis: Sweep `iteration_count` threshold over a range of low integer values. and record effect estimates
- [~] T040 [US2] Generate `data/derived/analysis_results.json` containing coefficients, SEs, p-values, adjusted p-values, and CI
- [~] T041 [US2] Generate `data/derived/sensitivity_analysis.json` with threshold sweep results

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Visualization and Reporting (Priority: P3)

**Goal**: Generate publication-ready visualizations and a summary report detailing findings, limitations, and sensitivity analysis.

**Independent Test**: The generated report must contain a forest plot of effect sizes and explicitly state the null hypothesis rejection status based on corrected p-values.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [~] T042 [P] [US3] Unit test for plot generation (matplotlib/seaborn) in `tests/test_report.py`
- [~] T043 [P] [US3] Unit test for report text generation (associational framing) in `tests/test_report.py`

### Implementation for User Story 3

- [~] T044 [US3] Implement `code/report.py` to load analysis results
- [~] T045 [US3] Generate Forest Plot of effect sizes with confidence intervals for all proxies
- [~] T046 [US3] Generate Sensitivity Analysis plot/table showing effect variation across thresholds
- [~] T047 [US3] Implement text generation for the report:
 - Explicitly frame findings as "associational" (not causal)
 - Reference observational study design
 - State null hypothesis rejection status per corrected p-value
 - **Include "Theoretical Grounding" section citing Holland (Per T005/FR-009)**
 - **Include "Data Gap" section stating NASA-TLX unavailability (Per T005/FR-009)**
 - **Include exact warning string: "Note: This study uses proxy metrics for cognitive load. Self-report measures (e.g., NASA-TLX) were not available."**
- [ ] T048 [US3] Generate `docs/output/final_report.pdf`

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Reviewer Revision - Signal Separation & Control (Priority: P1)

**Goal**: Address Richard Feynman's concern regarding the inability to separate "fixing AI's mess" load from "solving the problem" load.

**Independent Test**: The analysis must produce a stratified result showing how the "LLM Adoption" effect size changes when controlling for "Code Quality" (a proxy for AI-generated mess) or when filtering for specific commit types.

### Implementation for Signal Separation

- [ ] T049 [US2] **New Metric**: Implement `code/utils/metrics.py` function to calculate `diff_complexity_score`:
 - **Formula**: `(lines_added + lines_deleted) / total_lines` if `lines_deleted > 0` else `0`.
 - **Flag Logic**: Flag "AI Noise" if `diff_complexity_score` > 0.3 AND commit message contains "fix", "hotfix", or "patch".
 - **Rationale**: Per updated `spec.md` FR-008 (Task T004).
- [ ] T050 [US2] **Control Variable**: Add `diff_complexity_score` as a control variable in the GLMM/ZINB models (T034/T035) to isolate the pure "LLM Adoption" effect.
- [ ] T051 [US2] **Stratified Analysis**: Implement a secondary analysis in `code/analyze.py` that splits the dataset into "High AI-Noise" (high diff complexity) and "Low AI-Noise" groups to compare effect sizes.
- [ ] T052 [US3] **Reporting Update**: Update `code/report.py` to include a dedicated subsection "Signal Separation: Distinguishing Tool Utility from AI Noise" that discusses the stratified results.
- [ ] T053 [US3] **Data Flow Diagram**: Generate a diagram in `docs/output/` using Mermaid syntax illustrating the data flow and where "load" is inferred, explicitly marking the point where AI-generated code is conflated with human problem-solving.
 - **Nodes**: Repository, PR, Commit, Metric Calculation, GLMM, Report.
 - **Edges**: Data flow arrows, highlighting the `diff_complexity_score` calculation point.

**Checkpoint**: The study now explicitly addresses the confounding variable of "AI-generated noise" and provides a methodological boundary for the findings.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T054 [P] Documentation updates in `docs/` (README, usage instructions)
- [ ] T055 Code cleanup and refactoring
- [ ] T056 Performance optimization (ensure runtime < 6h on 2 CPU cores)
- [ ] T057 [P] Run `pytest` suite and ensure [deferred] pass rate
- [ ] T058 [P] Run quickstart.md validation
- [ ] T059 [P] Verify `state/projects/PROJ-508-evaluating-the-impact-of-llm-based-code-.yaml` artifact hashes are updated

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Review Revision (Phase 6)**: Depends on US1 (Data), US2 (Analysis), and US3 (Report) completion
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Depends on US1 completion (requires `master_dataset.csv`)
- **User Story 3 (P3)**: Depends on US2 completion (requires `analysis_results.json`)
- **Phase 6 (Revision)**: Depends on US1, US2, and US3 completion (requires final data and draft report)

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models/Utilities before services
- Services before endpoints/reporting
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, US1, US2, and US3 can start in parallel if data flow is managed (US1 must finish before US2/3 can run)
- All tests for a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members (once dependencies are met)

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for.cursorrules detection in tests/test_ingest.py"
Task: "Unit test for commit message Copilot frequency calculation in tests/test_ingest.py"
Task: "Integration test for GitHub API retry logic in tests/test_github_client.py"

# Launch all models for User Story 1 together:
Task: "Implement code/ingest.py to fetch repository list and metadata"
Task: "Implement llm_adoption_flag logic in code/ingest.py"
Task: "Implement iteration_count logic in code/utils/metrics.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 0: Spec Updates
2. Complete Phase 1: Setup
3. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
4. Complete Phase 3: User Story 1
5. **STOP and VALIDATE**: Test User Story 1 independently (verify data ingestion and flagging)
6. Deploy/demo if ready

### Incremental Delivery

1. Complete Spec Updates + Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Add Phase 6 (Signal Separation) → Address Feynman's signal separation concern
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Data Ingestion)
 - Developer B: User Story 2 (Analysis) - *Must wait for US1 data*
 - Developer C: User Story 3 (Reporting) - *Must wait for US2 results*
 - Developer D: Phase 6 (Signal Separation) - *Can work on new metric logic in parallel*
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- **CRITICAL**: Do NOT exclude "Copilot" commits from `iteration_count` (Per updated `spec.md` FR-002 - Task T007)
- **CRITICAL**: Ensure all tasks run on CPU-only CI (no GPU, no 8-bit/4-bit models)
- **CRITICAL**: Ensure real data is used; no fabrication of metrics or datasets
- **CRITICAL**: Address Feynman's concern about "AI noise" vs "brain load" in Phase 6 (T049-T053)
- **CRITICAL**: GLMM and ZINB models are authorized by updated `spec.md` FR-003 (Task T006).
- **CRITICAL**: Theoretical Grounding and Data Gap sections are mandated by updated `spec.md` FR-009 (Task T005).
- **CRITICAL**: `diff_complexity_score` and 'Signal Separation' are authorized by updated `spec.md` FR-008 (Task T004).