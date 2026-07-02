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

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create directory `projects/PROJ-508-evaluating-the-impact-of-llm-based-code-/data/raw/`
- [ ] T002 Create directory `projects/PROJ-508-evaluating-the-impact-of-llm-based-code-/data/derived/`
- [ ] T003 Create directory `projects/PROJ-508-evaluating-the-impact-of-llm-based-code-/docs/output/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Initialize Python 3.11 project with `requirements.txt` dependencies: `pandas`, `requests`, `scikit-learn`, `statsmodels`, `matplotlib`, `seaborn`, `pyyaml`, `scipy`
- [ ] T005 [P] Configure linting (ruff) and formatting (black) tools
- [ ] T006 [P] Implement `code/utils/github_client.py` with exponential backoff retry logic (a limited number of retries with a fixed delay)
- [ ] T007 [P] Create `code/utils/metrics.py` for cognitive load proxy calculation (NO Copilot exclusion logic)
- [ ] T008 Create `code/utils/config.py` for environment variables and API key handling
- [ ] T009 Setup `pytest` configuration and basic test scaffolding in `tests/`
- [ ] T010 Implement `code/utils/data_validation.py` for PII scanning and schema validation
- [ ] T000 **Spec Override Documentation**: Create/update `docs/methodological_notes.md` to formally document the override of FR-002 (iteration_count exclusion) and the authorization of GLMM/ZINB models (FR-003 update). This task ensures the Spec's contradictions are explicitly acknowledged and traced. **MUST be completed before T016, T030, T031.**

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and LLM Adoption Classification (Priority: P1) 🎯 MVP

**Goal**: Identify a corpus of GitHub repositories, classify LLM adoption, and extract PR metadata to establish the independent variable and dependent variables.

**Independent Test**: The system can be tested by running the ingestion script against a known subset of repositories (some with `.cursorrules`, others without) and verifying that the output CSV correctly flags the LLM adoption status and contains non-empty rows for review metrics.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T011 [P] [US1] Unit test for `.cursorrules` detection in `tests/test_ingest.py`
- [ ] T012 [P] [US1] Unit test for commit message "Copilot" frequency calculation in `tests/test_ingest.py`
- [ ] T013 [P] [US1] Integration test for GitHub API retry logic in `tests/test_github_client.py`

### Implementation for User Story 1

- [ ] T014 [US1] Implement `code/ingest.py` to fetch repository list and metadata (PRs, commits, config files)
- [ ] T015 [US1] Implement `llm_adoption_flag` logic in `code/ingest.py`:
  - Check for `.cursorrules` or `copilot` config files
  - Check `README.md`/`CONTRIBUTING.md` for "Copilot"/"LLM" mentions (500 char window)
  - Check commit messages for ≥5% "Copilot"/"LLM" frequency
- [ ] T016 [US1] Implement `iteration_count` logic in `code/utils/metrics.py` **[FR-002-OVERRIDE]**:
  - **CRITICAL**: Count TOTAL push events between PR open and merge (NO exclusions for "Copilot" or small diffs).
  - **Rationale**: Per Plan.md "Spec Conflict Resolution" and documented in T000, FR-002's exclusion rule is overridden to prevent circular bias.
- [ ] T017 [US1] Implement extraction of `avg_comment_length`, `review_thread_depth`, and `revert_frequency`
- [ ] T018 [US1] Implement logic to exclude repositories with <10 PRs in last 12 months (SC-001)
- [ ] T019 [US1] Implement `code/ingest.py` to log "ambiguous LLM signal" warnings for repos with generic configs (e.g., `config.json` without tool naming) to support sensitivity analysis (Moved from Phase 6)
- [ ] T020 [US1] Implement domain complexity calculation (unique languages + dependency count from manifests)
- [ ] T021 [US1] Generate `data/derived/master_dataset.csv` with all required columns
- [ ] T022 [US1] Generate `data/manifest.json` with API endpoints, parameters, and timestamps

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Statistical Analysis and Hypothesis Testing (Priority: P2)

**Goal**: Compute regression models to test the association between LLM adoption and cognitive load proxies, controlling for confounders, applying multiple-comparison corrections, and performing sensitivity analysis.

**Independent Test**: The system can be tested by running the analysis script on a synthetic dataset where the correlation is hardcoded; the output must report a statistically significant coefficient matching the synthetic input.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T023 [P] [US2] Unit test for Bonferroni correction logic in `tests/test_analysis.py`
- [ ] T024 [P] [US2] Unit test for VIF calculation in `tests/test_analysis.py`
- [ ] T025 [P] [US2] Unit test for sensitivity analysis sweep logic in `tests/test_analysis.py`

### Implementation for User Story 2

- [ ] T026 [US2] Implement `code/analyze.py` to load `data/derived/master_dataset.csv`
- [ ] T027 [US2] Implement Linear Regression models for each cognitive load proxy (comment length, iteration count, thread depth, revert frequency)
- [ ] T028 [US2] Implement control variable adjustment: Project size (LOC), Team size (contributors), Domain complexity
- [ ] T029 [US2] **Spec Update**: Update `spec.md` (FR-003) to explicitly authorize Mixed-Effects Models (GLMM) and Zero-Inflated Negative Binomial (ZINB) models as per Plan.md "Critical Methodological Update". **MUST be completed before T030/T031.**
- [ ] T030 [US2] Implement Variance Inflation Factor (VIF) check; flag if >5.0
- [ ] T031 [US2] Implement Multiple-Comparison Correction (Bonferroni) for p-values (FR-004)
- [ ] T032 [US2] Implement Sensitivity Analysis: Sweep `iteration_count` threshold over {1, 2, 3} and record effect estimates
- [ ] T033 [US2] Implement Mixed-Effects Model (GLMM) with random intercepts for repositories **[Plan.md Update]**:
  - **Rationale**: Per Plan.md and T029, GLMM is adopted to account for hierarchical data structure.
- [ ] T034 [US2] Implement Zero-Inflated Negative Binomial (ZINB) or Hurdle models for zero-inflated outcomes (reverts/iterations) **[Plan.md Update]**:
  - **Rationale**: Per Plan.md and T029, ZINB is adopted for zero-inflated outcomes.
- [ ] T035 [US2] Generate `data/derived/analysis_results.json` containing coefficients, SEs, p-values, adjusted p-values, and CI
- [ ] T036 [US2] Generate `data/derived/sensitivity_analysis.json` with threshold sweep results

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Visualization and Reporting (Priority: P3)

**Goal**: Generate publication-ready visualizations and a summary report detailing findings, limitations, and sensitivity analysis.

**Independent Test**: The generated report must contain a forest plot of effect sizes and explicitly state the null hypothesis rejection status based on corrected p-values.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T037 [P] [US3] Unit test for plot generation (matplotlib/seaborn) in `tests/test_report.py`
- [ ] T038 [P] [US3] Unit test for report text generation (associational framing) in `tests/test_report.py`

### Implementation for User Story 3

- [ ] T039 [US3] Implement `code/report.py` to load analysis results
- [ ] T040 [US3] Generate Forest Plot of effect sizes with confidence intervals for all proxies
- [ ] T041 [US3] Generate Sensitivity Analysis plot/table showing effect variation across thresholds
- [ ] T042 [US3] Implement text generation for the report:
  - Explicitly frame findings as "associational" (not causal)
  - Reference observational study design
  - State null hypothesis rejection status per corrected p-value
- [ ] T043 [US3] **Spec Update**: Update `spec.md` (User Story 3 / SC-005) to explicitly mandate the inclusion of "Theoretical Grounding" (Holland's work) and "Data Gap" (NASA-TLX) sections in the final report. **MUST be completed before T044-T046.**

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Reviewer Revision - Operationalization & Context (Priority: P1)

**Goal**: Address reviewer concerns regarding the under-specified operationalization of "cognitive load" and the need for historical/theoretical grounding.

**Independent Test**: The report must include a section on distributed cognition and explicitly acknowledge the limitations of proxy-only metrics vs. self-report/physiological measures.

### Implementation for Reviewer Revision

- [ ] T044 [US3] **Data Gap**: Add a task to `code/report.py` to include a warning in `docs/output/final_report.pdf` that NASA-TLX/physiological data was not available (Per Plan.md "Reviewer Revision" section and T043).
- [ ] T045 [US3] **Theoretical Grounding**: Add a "Theoretical Context" section to `code/report.py` that:
  - Cites Holland's work on adaptive systems and distributed cognition (Per Plan.md "Reviewer Revision" section and T043).
  - Discusses the phenomenon vs. method distinction.
  - Frames the study as capturing "emergent interaction patterns" rather than just individual offloading.
- [ ] T046 [US3] **Limitations Section**: Enhance `docs/output/final_report.pdf` to explicitly discuss the "under-specified operationalization" of cognitive load AND the study's "underpowered" nature for small effects (Per Plan.md "Summary" and "Reviewer Revision" sections and T043).
- [ ] T047 [US2] **Sensitivity Check**: Implement the sensitivity analysis logic in `code/analyze.py` to test robustness when excluding repositories with ambiguous LLM signals (Depends on T019 logging).

**Checkpoint**: Reviewer concerns regarding operationalization and theoretical context are addressed.

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T048 [P] Documentation updates in `docs/` (README, usage instructions)
- [ ] T049 Code cleanup and refactoring
- [ ] T050 Performance optimization (ensure runtime < 6h on 2 CPU cores)
- [ ] T051 [P] Run `pytest` suite and ensure [deferred] pass rate
- [ ] T052 [P] Run quickstart.md validation
- [ ] T053 [P] Verify `state/projects/PROJ-508-evaluating-the-impact-of-llm-based-code-.yaml` artifact hashes are updated

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Review Revision (Phase 6)**: Depends on US1 (Data) and US3 (Report) completion
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
Task: "Unit test for .cursorrules detection in tests/test_ingest.py"
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

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (verify data ingestion and flagging)
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Add Phase 6 (Revision) → Address reviewer concerns
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (Data Ingestion)
   - Developer B: User Story 2 (Analysis) - *Must wait for US1 data*
   - Developer C: User Story 3 (Reporting) - *Must wait for US2 results*
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- **CRITICAL**: Do NOT exclude "Copilot" commits from `iteration_count` (Per Plan.md "Spec Conflict Resolution" - FR-002 Override, documented in T000)
- **CRITICAL**: Ensure all tasks run on CPU-only CI (no GPU, no 8-bit/4-bit models)
- **CRITICAL**: Ensure real data is used; no fabrication of metrics or datasets
- **CRITICAL**: Address reviewer concerns about cognitive load operationalization in Phase 6 (T044-T046)
- **CRITICAL**: GLMM and ZINB models are authorized by Plan.md "Critical Methodological Update" and T029 (Spec Update), overriding Spec FR-003.
- **CRITICAL**: Theoretical Grounding and Data Gap sections are authorized by T043 (Spec Update).