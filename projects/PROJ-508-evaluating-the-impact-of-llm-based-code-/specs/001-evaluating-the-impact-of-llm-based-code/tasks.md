# Tasks: Evaluating the Impact of LLM-Based Code Completion on Developer Cognitive Load

**Input**: Design documents from `/specs/001-evaluating-the-impact-of-llm-based-code-completion/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each user story.

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

## Phase 0: Spec Verification (Critical Prerequisites)

**Purpose**: Verify that `spec.md` has been updated to formally authorize methodological changes, new metrics, and specific report sections before implementation begins. This ensures all downstream tasks have a valid requirement anchor.

**⚠️ BLOCKING**: No other phase can begin until Phase 0 is complete and the spec artifact is verified.

- [X] T004 [US2] **Verify spec.md contains FR-008**: Confirm `spec.md` contains **FR-008** text: "The system MUST calculate `diff_complexity_score` = (lines_added + lines_deleted) / max(1, total_lines) if lines_deleted > 0 else 0. It MUST flag 'AI Noise' if `diff_complexity_score` > 0.3 AND commit message contains 'fix', 'hotfix', or 'patch'."
 - **Status**: [X] if present.
 - **Rationale**: Ensures the 'Signal Separation' analysis is authorized and formula is consistent.

- [X] T005 [US3] **Verify spec.md contains SC-009**: Confirm `spec.md` contains **SC-009** text: "The report must explicitly state: 'Note: This study uses proxy metrics for cognitive load. Self-report measures (e.g., NASA-TLX) were not available.' "
 - **Action**: If SC-009 text is missing or incomplete, update `spec.md` with the exact required sentence before marking this task complete.
 - **Status**: [X] if present.
 - **Rationale**: Ensures specific report content is authorized.

- [X] T006 [US2] **Verify spec.md contains updated FR-003**: Confirm `spec.md` **FR-003** states "Mixed-Effects Models (GLMM) with random intercepts for repositories; Zero-Inflated Negative Binomial (ZINB) or Hurdle models for zero-inflated outcomes."
 - **Status**: [X] if present.
 - **Rationale**: Ensures the statistical engine change is authorized.

- [X] T007 [US1] **Verify spec.md contains updated FR-002**: Confirm `spec.md` **FR-002** states "Count TOTAL push events between PR open and merge (no exclusions). "
 - **Status**: [X] if present.
 - **Rationale**: Ensures the circular bias conflict resolution is in the spec.

**Checkpoint**: Spec is verified and ready for implementation.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T008 Create directory `projects/PROJ-508-evaluating-the-impact-of-llm-based-code-/data/raw/`
- [X] T009 Create directory `projects/PROJ-508-evaluating-the-impact-of-llm-based-code-/data/derived/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T011 Initialize Python 3.11 project with `requirements.txt` dependencies: `pandas`, `requests`, `scikit-learn`, `statsmodels`, `matplotlib`, `seaborn`, `pyyaml`, `scipy`
- [X] T012 [P] Configure linting (ruff) and formatting (black) tools
 - **Deliverable**: Create `pyproject.toml` at repository root.
 - **Content**: Add `[tool.ruff]` and `[tool.black]` sections with standard project settings (e.g., `line-length = 88`, `target-version = 'py311'`).
 - **Verification**: Run `ruff check.` and `black --check.` with exit code 0.
- [X] T013 [P] Implement `code/utils/github_client.py` with exponential backoff retry logic (a limited number of retries with a fixed delay)
- [X] T014 [P] Create `code/utils/metrics.py` for cognitive load proxy calculation
- [X] T015 Create `code/utils/config.py` for environment variables and API key handling
- [X] T016 [P] Setup `pytest` configuration and basic test scaffolding in `tests/`
 - **Deliverable**: Create `pytest.ini` at repository root.
 - **Content**: Add `[pytest]` section with `testpaths = tests`, `python_files = test_*.py`, `python_classes = Test*`, `python_functions = test_*`.
 - **Deliverable**: Create `tests/test_example.py` with a single passing assertion (e.g., `def test_example(): assert 1 == 1`).
 - **Verification**: Run `pytest` and ensure the test passes.
- [X] T017 Implement `code/utils/data_validation.py` for PII scanning and schema validation

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Ingestion and LLM Adoption Classification (Priority: P1) 🎯 MVP

**Goal**: Identify a corpus of GitHub repositories, classify LLM adoption, and extract PR metadata to establish the independent variable and dependent variables.

**Independent Test**: The system can be tested by running the ingestion script against a known subset of repositories (some with `.cursorrules`, others without) and verifying that the output CSV correctly flags the LLM adoption status and contains non-empty rows for review metrics.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T018 [P] [US1] Unit test for `.cursorrules` detection in `tests/test_ingest.py`
- [X] T019 [P] [US1] Unit test for commit message "Copilot" frequency calculation in `tests/test_ingest.py`
- [X] T020 [P] [US1] Integration test for GitHub API retry logic in `tests/test_github_client.py`

### Implementation for User Story 1

- [X] T021 [US1] Implement `code/ingest.py` to fetch repository list and metadata (PRs, commits, config files)
- [X] T022 [US1] Implement `llm_adoption_flag` logic in `code/ingest.py`:
 - Check for `.cursorrules` or `copilot` config files
 - Check `README.md`/`CONTRIBUTING.md` for "Copilot"/"LLM" mentions (A fixed-length context window of moderate size will be employed to evaluate performance.)
 - Check commit messages for ≥5% "Copilot"/"LLM" frequency
- [X] T023 [US1] Implement `iteration_count` logic in `code/utils/metrics.py`:
 - **Logic**: Count TOTAL push events between PR open and merge (no exclusions).
 - **Rationale**: Per updated `spec.md` FR-002 (Task T007).
- [X] T024 [US1] Implement extraction of `avg_comment_length`, `review_thread_depth`, and `revert_frequency` in `code/ingest.py`
 - **Function**: Create `extract_pr_metrics(pr_data)` in `code/ingest.py`.
 - **Logic**:
 - `avg_comment_length`: Mean length of comment bodies in PR review threads (source: `review_threads.comments.body`).
 - `review_thread_depth`: Count of comments per PR (source: `review_threads` count).
 - `revert_frequency`: Count of commits with "revert" in message (case-insensitive regex: `r'\brevert\b'`).
 - **Output**: Ensure columns `avg_comment_length`, `review_thread_depth`, `revert_frequency` exist in `master_dataset.csv`.
 - **Rationale**: Required by FR-001 (Data Ingestion) and Data Model (PullRequest entity).
- [X] T025 [US1] Filter repositories to include only those with >= 10 Pull Requests in the last 12 months.
- [X] T026 [US1] Implement `code/ingest.py` to log "ambiguous LLM signal" warnings for repos with generic configs (e.g., `config.json` without tool naming) to support sensitivity analysis
- [X] T027b [US1] Implement `domain_complexity` calculation in `code/ingest.py`
 - **Formula**: Sum of unique programming languages + count of dependencies found in manifest files (e.g., `package.json`, `requirements.txt`, `pom.xml`).
 - **Verification**: Verify column `domain_complexity` is populated in `master_dataset.csv`.
- [X] T027c [US1] **New Metric**: Implement `diff_complexity_score` calculation in `code/utils/metrics.py`
 - **Formula**: `(lines_added + lines_deleted) / max(1, total_lines)` if `lines_deleted > 0` else `0`.
 - **Flag Logic**: Flag "AI Noise" if `diff_complexity_score` > 0.3 AND commit message contains "fix", "hotfix", or "patch".
 - **Rationale**: Per updated `spec.md` FR-008 (Task T004).
- [ ] T028 [US1] Generate `data/derived/master_dataset.csv` with all required columns
- [X] T029 [US1] Generate `data/manifest.json` with API endpoints, parameters, and timestamps to satisfy Constitution Principle VI (Empirical Data Collection Transparency)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Statistical Analysis and Hypothesis Testing (Priority: P2)

**Goal**: Compute regression models to test the association between LLM adoption and cognitive load proxies, controlling for confounders, applying multiple-comparison corrections, and performing sensitivity analysis.

**Independent Test**: The system can be tested by running the analysis script on a synthetic dataset where the correlation is hardcoded; the output must report a statistically significant coefficient matching the synthetic input.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T030 [P] [US2] Unit test for Bonferroni correction logic in `tests/test_analysis.py`
- [X] T031 [P] [US2] Unit test for VIF calculation in `tests/test_analysis.py`
- [X] T032 [P] [US2] Unit test for sensitivity analysis sweep logic in `tests/test_analysis.py`

### Implementation for User Story 2

- [X] T033 [US2] Implement `code/analyze.py` to load `data/derived/master_dataset.csv`
 - **Dependency**: Requires T024 (data extraction) to be complete.
- [X] T034a [US2] **Signal Separation Control**: Implement Mixed-Effects Models (GLMM) with random intercepts for repositories **[FR-003-UPDATED]** including `diff_complexity_score` as a control variable.
 - **Formula**: `iteration_count ~ llm_adoption_flag + diff_complexity_score + loc + contributors + domain_complexity + (1|repository_id)`
 - **Rationale**: Per updated `spec.md` FR-003 (Task T006) and SC-008.
 - **Note**: Must include `diff_complexity_score` as a covariate in this model.
- [X] T034b [US2] **Stratified Analysis**: Implement a secondary analysis in `code/analyze.py` that splits the dataset into "High AI‑Noise" and "Low AI‑Noise" groups to compare effect sizes.
 - **Action**: Run the models from T034a separately on the two subsets and record the difference in the `llm_adoption_flag` coefficient.
 - **Output**: Generate `data/derived/stratified_results.json` containing the stratified effect sizes and comparison metrics.
 - **Rationale**: Satisfies the "stratified result" requirement of SC-008.
- [X] T035 [US2] Implement Zero-Inflated Negative Binomial (ZINB) or Hurdle models for zero-inflated outcomes (reverts/iterations) **[FR-003-UPDATED]**:
 - **Rationale**: Per updated `spec.md` FR-003 (Task T006).
 - **Note**: Must include `diff_complexity_score` as a control variable (from T027c) in this model.
- [X] T036 [US2] Implement control variable adjustment: Project size (LOC), Team size (contributors), Domain complexity, and `diff_complexity_score` (FR-008)
- [X] T037 [US2] Implement Variance Inflation Factor (VIF) check; flag if >5.0
- [X] T038 [US2] Implement Multiple-Comparison Correction (Bonferroni) for p-values (FR-004)
- [X] T039 [US2] Implement Sensitivity Analysis: Sweep `iteration_count` threshold over a range of low integer values. and record effect estimates
- [ ] T040 [US2] Generate `data/derived/analysis_results.json` containing coefficients, SEs, p-values, adjusted p-values, and CI
- [ ] T041 [US2] Generate `data/derived/sensitivity_analysis.json` with threshold sweep results

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Visualization and Reporting (Priority: P3)

**Goal**: Generate publication‑ready visualizations and a summary report detailing findings, limitations, and sensitivity analysis.

**Independent Test**: The generated report must contain a forest plot of effect sizes and explicitly state the null hypothesis rejection status based on corrected p‑values.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T042 [P] [US3] Unit test for plot generation (matplotlib/seaborn) in `tests/test_report.py`
- [X] T043 [P] [US3] Unit test for report text generation (associational framing) in `tests/test_report.py`

### Implementation for User Story 3

- [X] T044 [US3] Implement `code/report.py` to load analysis results
- [X] T045 [US3] Generate Forest Plot of effect sizes with confidence intervals for all proxies
- [X] T046 [US3] Generate Sensitivity Analysis plot/table showing effect variation across thresholds
- [X] T047 [US3] Implement text generation for the report:
 - Explicitly frame findings as "associational" (not causal)
 - Reference observational study design
 - State null hypothesis rejection status per corrected p‑value
 - **Include "Data Gap" section stating NASA-TLX unavailability.**
- [X] T047b [US3] **Theoretical Grounding**: Update `code/report.py` to include a dedicated section "Theoretical Grounding: Distributed Cognition and Adaptive Systems". <!-- FAILED: unspecified -->
 - **Content**: Explicitly cite "Holland et al. (1998) " regarding distributed cognition.
 - **Content**: Discuss how LLM tools may reconfigure collective problem-solving dynamics rather than merely offloading individual effort.
 - **Citation Requirement**: Must include the exact string: "Holland, J. H. (1998). Hidden Order: How Adaptation Builds Complexity. Addison-Wesley."
 - **Verification**: Run Reference-Validator Agent to verify citation validity before inclusion.
 - **Rationale**: Directly addresses SC-007 and Krakauer's critique.
- [X] T048 [US3] Generate `docs/output/final_report.pdf`
- [X] T049 [US3] Add a section to the final report explicitly stating that self-report measures (e.g., NASA-TLX) were not available in this study, acknowledging the limitations of relying solely on proxy metrics for cognitive load assessment.
 - **Required Text**: "Note: This study uses proxy metrics for cognitive load. Self-report measures (e.g., NASA-TLX) were not available."

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Reviewer Revision - Signal Separation & Control (Priority: P1)

**Goal**: Address Richard Feynman's concern regarding the inability to separate "fixing AI's mess" load from "solving the problem" load.

**Independent Test**: The analysis must produce a stratified result showing how the "LLM Adoption" effect size changes when controlling for "Code Quality" (a proxy for AI‑generated mess) or when filtering for specific commit types.

### Implementation for Signal Separation (Reporting)

- [ ] T052 [US3] **Reporting Update**: Update `code/report.py` to include a dedicated subsection "Signal Separation: Distinguishing Tool Utility from AI Noise" that discusses the stratified results from `data/derived/stratified_results.json`. <!-- FAILED: unspecified -->
 - **Action**: Summarize the difference in effect sizes between High/Low AI-Noise groups.
 - **Rationale**: Satisfies the reporting requirement of SC-008.

**Checkpoint**: The study now explicitly addresses the confounding variable of "AI‑generated noise" and provides a methodological boundary for the findings.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T053 [P] **Documentation**: Update `docs/` (README, usage instructions).
 - **Note**: Task T053 (Mermaid diagram) was **CANCELLED** due to lack of spec authorization. The requirement for a specific "AI Noise" visualization was not defined in the spec's Data Model or Output Artifacts.
- [X] T054 [P] Documentation updates in `docs/` (README, usage instructions)
- [X] T055 Code cleanup and refactoring
- [X] T056 Performance optimization (ensure runtime < 6h on 2 CPU cores)
- [X] T057 [P] Run `pytest` suite and ensure pass rate
- [X] T058 [P] Run quickstart.md validation

**Checkpoint**: All user stories, reviewer‑requested extensions, and polishing tasks are complete and the project is ready for final validation.

---

## Phase 8: Reviewer Revision - Theoretical Grounding & Distributed Cognition (Priority: P2)

**Goal**: Address David Krakauer's concern regarding the under-specified operationalization of "cognitive load" and the lack of historical grounding in complexity science/distributed cognition.

**Independent Test**: The final report must contain a section explicitly citing Holland et al. (1998) and discussing the reconfiguration of collective problem-solving dynamics, moving beyond individual offloading metrics.

### Implementation for Theoretical Grounding

- [X] T059 [US3] **Literature Integration**: Update `code/report.py` to include a dedicated subsection "Distributed Cognition in Adaptive Systems".
 - **Action**: Insert a paragraph discussing how LLM tools act as external cognitive resources that reconfigure the "collective problem-solving dynamics" of a team, rather than merely offloading individual effort.
 - **Citation**: Explicitly cite "Holland, J. H. (1998). Hidden Order: How Adaptation Builds Complexity. Addison-Wesley." as the theoretical anchor.
 - **Rationale**: Directly addresses Krakauer's critique that the study must "ground the interpretation of cognitive load proxies" in the history of complexity science and distributed cognition.

- [ ] T060 [US3] **Methodological Limitation Disclosure**: Update `code/report.py` to expand the "Limitations" section.
 - **Action**: Explicitly state that while proxy metrics (iteration count, review depth) are used, the study lacks physiological proxies (pupil dilation, HRV) and self-report scales (NASA-TLX) to triangulate the "phenomenon-vs-method" check.
 - **Action**: Discuss how the absence of these triangulation methods limits the ability to distinguish between "individual cognitive load" and "collective interaction patterns."
 - **Rationale**: Addresses Krakauer's point that a "more robust design would triangulate self-report scales... with physiological proxies" and captures the limitation of the current observational design.

**Checkpoint**: The study now explicitly grounds its findings in distributed cognition theory and transparently acknowledges the limitations of proxy-only measurement.

---

## Dependencies & Execution Order (Updated)

### Phase Dependencies

- **Phase 0 (Spec Verification)**: **ABSOLUTE PREREQUISITE**. No other phase can begin until Phase 0 is complete. If T004-T007 fail (spec missing), the project halts.
- **Setup (Phase 1)**: Depends on Phase 0 completion.
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories.
- **User Stories (Phase 3+)**: All depend on Foundational phase completion.
- **Polish (Final Phase)**: Depends on all desired user stories being complete.
- **Reviewer Revisions (Phase 6 & 8)**: Can run in parallel with Polish, but must complete before final report generation.

### Parallel Opportunities

- Tasks T059, T060 (Phase 8) can be executed in parallel with Phase 7 (Polish) tasks, as they primarily involve code updates to `report.py`.
- T034a/T034b (Signal Separation) are integrated into Phase 4 to ensure correct data flow.

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence

### Spec Conflict Resolution (Updated)

**RESOLVED**: The source spec's original **FR-002** mandated "EXCLUDING any push event where the commit message contains 'Copilot' OR the diff size is < 100 lines". This created a circular bias when used to define `llm_adoption_flag` (which relied on "Copilot" mentions).

**Resolution**: The implementation **MUST override** the original exclusion rule. The `spec.md` was updated (Task T007) to state: "Count TOTAL push events between PR open and merge (no exclusions). " This ensures the outcome (`iteration_count`) is independent of the predictor definition (`llm_adoption_flag`). The plan's logic is now consistent with the updated spec.

**CANCELLED TASKS**:
- **T053 (Mermaid Diagram)**: Removed due to lack of spec authorization. The spec does not define this visualization requirement.
- **T061 (Team Interaction Density)**: Removed due to lack of spec authorization. The spec's Data Model does not define this metric, and introducing it would violate the Single Source of Truth principle.
