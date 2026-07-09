# Tasks: Investigating the Correlation Between Structural Brain Connectivity and Individual Music Preferences

**Input**: Design documents from `/specs/001-gene-regulation/`
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

- [ ] T001a [P] Create directory: `code/`
- [ ] T001b [P] Create directory: `tests/`
- [ ] T001c [P] Create directory: `data/`
- [ ] T001d [P] Create directory: `docs/`
- [ ] T002 Initialize Python 3.11 project with `requirements.txt` dependencies (pandas, numpy, scipy, statsmodels, matplotlib, seaborn, pyyaml, requests, sklearn)
- [ ] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T005 [P] Implement data hygiene utilities: `code/utils/checksum.py` (MD5/SHA256 for input validation)
- [ ] T006 [P] Setup configuration management: `code/utils/config.py` (seed pinning, path loading)
- [ ] T007 Create base data models: `contracts/study_record.schema.yaml` and `contracts/meta_analysis_result.schema.yaml`
- [ ] T008 [P] Implement tract harmonization logic: `code/analysis/tract_mapping.py` (JHU Atlas mapping, string normalization). **Specific Prioritization Logic**: Implement a scoring system where the 'auditory-reward pathway' (Heschl's gyrus to ventral striatum) is assigned a `priority_score` of 1.0, and all other tracts are assigned a baseline value. The system MUST filter and prioritize results by this score first.
- [ ] T009 Setup logging infrastructure: `code/utils/logger.py` (structured logging for convergence warnings, fallbacks)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Meta-Analysis Data Extraction and Synthesis (Priority: P1) 🎯 MVP

**Goal**: Extract effect sizes from CSV, handle missing data, perform random-effects meta-analysis, and trigger narrative fallback if N < 10.

**Independent Test**: Run extraction script on a small, synthetic CSV of 3 mock studies with known effect sizes and verify the output JSON contains the correct weighted mean and confidence intervals calculated via `statsmodels` logic.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T010 [P] [US1] Unit test for extraction logic in `tests/unit/test_extraction.py` (verify r, n parsing)
- [ ] T011 [P] [US1] Unit test for meta-analysis calculation in `tests/unit/test_meta_analysis.py` (verify weighted mean within 0.001 tolerance)
- [ ] T012 [P] [US1] Unit test for narrative fallback trigger in `tests/unit/test_narrative.py` (verify N < 10 skips aggregation)

### Implementation for User Story 1

- [ ] T013 [P] [US1] Implement `code/extraction/parser.py` to parse CSV/JSON inputs for r, n, tract AND qualitative descriptors. **Extraction Logic**: Use regex/keyword matching to extract 'neural circuitry' and 'preference' descriptors from raw text fields when quantitative data is missing. **Required Keywords**: `['neural circuitry', 'white matter integrity', 'music preference', 'auditory cortex', 'reward pathway', 'functional connectivity']`. **Required Regex**: `r'(pref|prefer|liking|enjoy).*?(music|auditory|sound)'`. Output includes a new column `qualitative_notes` populated by these matches.
- [ ] T014 [US1] Implement `code/analysis/meta_analysis.py` Random-Effects model using `statsmodels` (handle convergence failure by falling back to Fixed-Effects with warning); output `study_count` artifact.
- [ ] T015 [US1] Implement `code/analysis/narrative.py` to generate structured text summary if eligible study count < 10; consumes `qualitative_notes` from T013. **Structure Requirements**: Output MUST be a Markdown document with H2 headers: `## Study Overview`, `## Qualitative Themes`, `## Limitations`. Additionally, include a JSON metadata block at the top with keys: `study_count`, `synthesis_mode`, `timestamp`. **Depends on: T013**
- [ ] T016 [US1] Implement `code/main.py` entry point logic: load raw CSV, run extraction, check N count, branch to quantitative or narrative mode.
- [ ] T017 [US1] Add validation and error handling for missing effect sizes (exclude study with log entry if conversion fails).
- [ ] T018 [US1] Handle zero-studies edge case: ensure `narrative.py` produces a valid "No studies found" summary if input CSV is empty.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Heterogeneity and Bias Assessment (Priority: P2)

**Goal**: Calculate I² statistics and perform Egger's regression test (only if N ≥ 10).

**Independent Test**: Provide a synthetic dataset with high variance and verify I² > 50%; provide skewed data to verify Egger's test p-value < 0.05; verify skip logic for N < 10.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T019 [P] [US2] Unit test for I² calculation in `tests/unit/test_heterogeneity.py` (verify precision to **exactly two decimal places** as required by SC-002, e.g., 52.34)
- [ ] T020 [P] [US2] Unit test for Egger's regression in `tests/unit/test_bias.py` (verify p-value calculation and N < 10 skip logic; verify `egger_skipped_reason` output matches **exact string**: 'Skipped: Insufficient studies (N < 10) for Egger's regression')

### Implementation for User Story 2

- [ ] T021 [US2] Implement `code/analysis/bias.py` Egger's linear regression test. **Skip Logic**: Explicitly SKIP if `study_count` (from T014) < 10. **Output Requirement**: The code MUST output the exact string `egger_skipped_reason: "Skipped: Insufficient studies (N < 10) for Egger's regression"` as a runtime value in the result JSON if skipped. **Depends on: T014**
- [ ] T021b [US2] Implement `code/analysis/heterogeneity.py` I² calculation. **Precision Requirement**: The output MUST report the I² statistic with **exactly two decimal places** (e.g., 52.34). **Depends on: T014**
- [ ] T022 [US2] Implement `code/analysis/correction.py` for multiple comparison correction. **Decision Logic**: 
  1. If tracts are from **different studies** (independent), apply **Bonferroni correction**.
  2. If tracts are from the **same study** (non-independent), apply **Robust Variance Estimation (RVE)**.
  3. Apply Bonferroni correction ONLY if N ≥ 10 AND k ≥ 2 tracts (for the independent subset). If N < 10, skip and trigger narrative mode. **Depends on: T014, T008**
- [ ] T023 [US2] Integrate bias assessment into `code/main.py` (run after meta-analysis, update `MetaAnalysisResult` JSON).
- [ ] T024 [US2] Add power analysis logic in `code/analysis/correction.py` (warn if N < 20 and expected r < 0.3).

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Visualization and Reporting (Priority: P3)

**Goal**: Generate forest plots, funnel plots, and summary correlation plots using `matplotlib` and `seaborn`.

**Independent Test**: Run plotting module on a static dataset and verify PNG files exist, are under a reasonable file size limit, and contain correct axis labels/data points.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T025 [P] [US3] Integration test for plot generation in `tests/integration/test_plots.py` (verify file existence, size < 5MB, peak memory < 6GB using tracemalloc, and correct axis labels).

### Implementation for User Story 3

- [ ] T027 [P] [US3] Implement `code/visualization/plots.py` to generate all required plots: Forest plot (summary diamond aligns with `weighted_mean_r`), Funnel plot (standard error vs effect size, symmetry line at pooled effect), and Correlation summary plot. **Optimization**: Implement PNG compression settings (optimize=True, dpi=150) to ensure file size < 5MB.
- [ ] T028 [US3] Integrate visualization into `code/main.py` (save PNGs to `data/derived/` after analysis).
- [ ] T031 [US3] Implement file size validation logic in `code/utils/validator.py`: Add a function to verify generated PNGs are < 5MB. Integrate this check into the `main.py` pipeline post-generation. **Depends on: T027**

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T032 [P] Generate `docs/paper_draft.md` from `MetaAnalysisResult` JSON using Jinja2 template (automated report generation).
- [ ] T033 [P] Run linting (ruff) and fix any violations; refactoring triggered by test failures.
- [ ] T034 [P] Profile total runtime and ensure < 15 mins on CI; optimize bottlenecks if exceeded.
- [ ] T035 [P] Additional unit tests in `tests/unit/` (coverage for p-value conversion edge cases).
- [ ] T036 Run `quickstart.md` validation to ensure end-to-end pipeline execution.
- [ ] T037 Verify `tasks.md` execution order matches data flow (extraction -> analysis -> visualization).

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on data extraction from US1 (T014 output)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on results from US1 and US2

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Explicit Task Dependencies

- **T022 (Bonferroni/RVE)**: Explicitly depends on **T008 (tract_mapping)** for harmonized tract names AND **T014** for study_count.
- **T021 (Egger's)**: Explicitly depends on **T014** for study_count.
- **T021b (I²)**: Explicitly depends on **T014** for study_count.
- **T015 (Narrative)**: Explicitly depends on **T013** for qualitative_notes.
- **T031 (File Size)**: Explicitly depends on **T027** for plot generation.

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