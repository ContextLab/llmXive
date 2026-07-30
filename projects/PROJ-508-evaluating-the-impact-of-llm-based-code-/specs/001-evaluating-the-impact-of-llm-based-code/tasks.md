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

## Phase 0: Spec Verification (Critical Prerequisites)

**Purpose**: Verify that `spec.md` has been updated to formally authorize methodological changes, new metrics, and specific report sections before implementation begins. This ensures all downstream tasks have a valid requirement anchor.

**⚠️ BLOCKING**: No other phase can begin until Phase 0 is complete and the spec artifact is verified.

- [ ] T004 [US2] **Verify spec.md contains FR-008**: Confirm `spec.md` contains **FR-008** text: "The system MUST calculate `diff_complexity_score` = (lines_added + lines_deleted) / total_lines if lines_deleted > 0 else 0. It MUST flag 'AI Noise' if `diff_complexity_score` > 0.3 AND commit message contains 'fix', 'hotfix', or 'patch'."
 - **Status**: [ ] if missing, [X] if present.
 - **Rationale**: Ensures the 'Signal Separation' analysis is authorized.

- [ ] T005 [US3] **Verify spec.md contains SC-009**: Confirm `spec.md` contains **SC-009** text: "The report must explicitly state: 'Note: This study uses proxy metrics for cognitive load. Self-report measures (e.g., NASA-TLX) were not available.' "
 - **Status**: [ ] if missing, [X] if present.
 - **Rationale**: Ensures specific report content is authorized.

- [ ] T006 [US2] **Verify spec.md contains updated FR-003**: Confirm `spec.md` **FR-003** states "Mixed-Effects Models (GLMM) with random intercepts for repositories; Zero-Inflated Negative Binomial (ZINB) or Hurdle models for zero-inflated outcomes."
 - **Status**: [ ] if missing, [X] if present.
 - **Rationale**: Ensures the statistical engine change is authorized.

- [ ] T007 [US1] **Verify spec.md contains updated FR-002**: Confirm `spec.md` **FR-002** states "Count TOTAL push events between PR open and merge (no exclusions)."
 - **Status**: [ ] if missing, [X] if present.
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
- [ ] T012 [P] Configure linting (ruff) and formatting (black) tools
 - **Deliverable**: Create `pyproject.toml` with `[tool.ruff]` and `[tool.black]` sections.
 - **Verification**: Run `ruff check .` and `black --check .` with exit code 0.
- [X] T013 [P] Implement `code/utils/github_client.py` with exponential backoff retry logic (a limited number of retries with a fixed delay)
- [X] T014 [P] Create `code/utils/metrics.py` for cognitive load proxy calculation 
- [X] T015 Create `code/utils/config.py` for environment variables and API key handling
- [ ] T016 Setup `pytest` configuration and basic test scaffolding in `tests/`
 - **Deliverable**: Create `pytest.ini` with `[pytest]` configuration.
 - **Deliverable**: Create `tests/test_example.py` with a single passing assertion (e.g., `assert 1 == 1`).
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
- [ ] T024 [US1] Implement extraction of `avg_comment_length`, `review_thread_depth`, and `revert_frequency`
 - **Definition**: `revert_frequency` = count of commits with "revert" in message.
 - **Output**: Ensure columns `avg_comment_length`, `review_thread_depth`, `revert_frequency` exist in `master_dataset.csv`.
- [X] T025 [US1] Filter repositories to include only those with >= 10 Pull Requests in the last 12 months.
- [X] T026 [US1] Implement `code/ingest.py` to log "ambiguous LLM signal" warnings for repos with generic configs (e.g., `config.json` without tool naming) to support sensitivity analysis
- [ ] T027b [US1] Implement `domain_complexity` calculation in `code/ingest.py`
 - **Formula**: Sum of unique programming languages + count of dependencies found in manifest files (e.g., `package.json`, `requirements.txt`, `pom.xml`).
 - **Verification**: Verify column `domain_complexity` is populated in `master_dataset.csv`.
- [X] T027c [US1] **New Metric**: Implement `diff_complexity_score` calculation in `code/utils/metrics.py`
 - **Formula**: `(lines_added + lines_deleted) / max(1, total_lines)` if `lines_deleted > 0` else `0`.
 - **Flag Logic**: Flag "AI Noise" if `diff_complexity_score` > 0.3 AND commit message contains "fix", "hotfix", or "patch".
 - **Rationale**: Per updated `spec.md` FR-008 (Task T004).
- [X] T028 [US1] Generate `data/derived/master_dataset.csv` with all required columns
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
- [X] T034 [US2] Implement Mixed-Effects Models (GLMM) with random intercepts for repositories **[FR-003-UPDATED]**:
 - **Rationale**: Per updated `spec.md` FR-003 (Task T006).
 - **Note**: Must include `diff_complexity_score` as a control variable (from T027c) in this model.
- [X] T035 [US2] Implement Zero-Inflated Negative Binomial (ZINB) or Hurdle models for zero-inflated outcomes (reverts/iterations) **[FR-003-UPDATED]**:
 - **Rationale**: Per updated `spec.md` FR-003 (Task T006).
 - **Note**: Must include `diff_complexity_score` as a control variable (from T027c) in this model.
- [X] T036 [US2] Implement control variable adjustment: Project size (LOC), Team size (contributors), Domain complexity, and `diff_complexity_score` (FR-008)
- [X] T037 [US2] Implement Variance Inflation Factor (VIF) check; flag if >5.0
- [X] T038 [US2] Implement Multiple-Comparison Correction (Bonferroni) for p-values (FR-004)
- [X] T039 [US2] Implement Sensitivity Analysis: Sweep `iteration_count` threshold over a range of low integer values. and record effect estimates
- [X] T040 [US2] Generate `data/derived/analysis_results.json` containing coefficients, SEs, p-values, adjusted p-values, and CI
- [X] T041 [US2] Generate `data/derived/sensitivity_analysis.json` with threshold sweep results

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
- [X] T047b [US3] **Theoretical Grounding**: Update `code/report.py` to include a dedicated section "Theoretical Grounding: Distributed Cognition and Adaptive Systems".
 - **Content**: Explicitly cite "Holland et al. (1998)" regarding distributed cognition.
 - **Content**: Discuss how LLM tools may reconfigure collective problem-solving dynamics rather than merely offloading individual effort.
 - **Rationale**: Directly addresses SC-007 and Krakauer's critique.
- [X] T048 [US3] Generate `docs/output/final_report.pdf`
- [X] T049 [US3] Add a section to the final report explicitly stating that self-report measures (e.g., NASA-TLX) were not available in this study, acknowledging the limitations of relying solely on proxy metrics for cognitive load assessment.
 - **Required Text**: "Note: This study uses proxy metrics for cognitive load. Self-report measures (e.g., NASA-TLX) were not available."

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Reviewer Revision - Signal Separation & Control (Priority: P1)

**Goal**: Address Richard Feynman's concern regarding the inability to separate "fixing AI's mess" load from "solving the problem" load.

**Independent Test**: The analysis must produce a stratified result showing how the "LLM Adoption" effect size changes when controlling for "Code Quality" (a proxy for AI‑generated mess) or when filtering for specific commit types.

### Implementation for Signal Separation

- [X] T050 [US2] **Control Variable**: Add `diff_complexity_score` (AI Noise flag) as a control variable (covariate) in the GLMM/ZINB models (T034/T035) to isolate the pure "LLM Adoption" effect.
 - **Action**: Update `code/analyze.py` to include `diff_complexity_score` as a covariate in the models defined in T034/T035.
 - **Rationale**: Satisfies the "controlling for" requirement of SC-008.
- [X] T051 [US2] **Stratified Analysis**: Implement a secondary analysis in `code/analyze.py` that splits the dataset into "High AI‑Noise" and "Low AI‑Noise" groups to compare effect sizes.
 - **Action**: Run the models from T050 separately on the two subsets and record the difference in the `llm_adoption_flag` coefficient.
 - **Rationale**: Satisfies the "stratified result" requirement of SC-008.
- [X] T052 [US3] **Reporting Update**: Update `code/report.py` to include a dedicated subsection "Signal Separation: Distinguishing Tool Utility from AI Noise" that discusses the stratified results.

**Checkpoint**: The study now explicitly addresses the confounding variable of "AI‑generated noise" and provides a methodological boundary for the findings.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T053 [P] **Documentation**: Update `docs/` (README, usage instructions) and generate a **Mermaid data-flow diagram** in `docs/` that **visually distinguishes** AI-generated code introduction points (e.g., using specific node shapes or colors for "AI Noise" commits) to satisfy the finalized visualization requirement.
- [X] T054 [P] Documentation updates in `docs/` (README, usage instructions)
- [X] T055 Code cleanup and refactoring
- [X] T056 Performance optimization (ensure runtime < 6h on 2 CPU cores)
- [X] T057 [P] Run `pytest` suite and ensure pass rate
- [X] T058 [P] Run quickstart.md validation

**Checkpoint**: All user stories, reviewer‑requested extensions, and polishing tasks are complete and the project is ready for final validation.

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable

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
Task: "Contract test for [endpoint] in tests/contract/test_[name].py"
Task: "Integration test for [user journey] in tests/integration/test_[name].py"

# Launch all models for User Story 1 together:
Task: "Create [Entity1] model in src/models/[entity1].py"
Task: "Create [Entity2] model in src/models/[entity2].py"
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

---

## Spec Conflict Resolution (Resolved)

**RESOLVED**: The source spec's original **FR-002** mandated "EXCLUDING any push event where the commit message contains 'Copilot' OR the diff size is < 100 lines". This created a circular bias when used to define `llm_adoption_flag` (which relied on "Copilot" mentions).

**Resolution**: The implementation **MUST override** the original exclusion rule. The `spec.md` was updated (Task T007) to state: "Count TOTAL push events between PR open and merge (no exclusions)." This ensures the outcome (`iteration_count`) is independent of the predictor definition (`llm_adoption_flag`). The plan's logic is now consistent with the updated spec.