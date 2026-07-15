# Tasks: Evaluating the Impact of Code Generation on Code Review Quality with LLM Assistance

**Input**: Design documents from `/specs/001-eval-llm-review-quality/`
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

- [ ] T001 Create project directories: `src/`, `data/raw/`, `data/derived/`, `data/annotations/`, `results/`, `tests/`, `specs/`
- [ ] T002 Create `requirements.txt` with pinned versions: `datasets`, `transformers`, `scikit-learn`, `scipy`, `pandas`, `pyyaml`, `pytest`, `numpy`
- [ ] T003 [P] Create virtualenv and install dependencies from `requirements.txt`
- [ ] T004 [P] Configure linting (ruff) and formatting (black) tools
- [ ] T005 Create `config/settings.py` for hyperparameters, paths, and random seeds

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T006 Define data classes in `src/extraction/schema.py` (PullRequest, BugDetection, AlignmentResult)
- [~] T007 Define data classes in `src/detection/schema.py` (LLMCodeDetectionResult)
- [~] T008 Define data classes in `src/inference/schema.py` (InferenceRequest, InferenceResponse)
- [ ] T009 Implement `src/utils/timeout_wrapper.py` to enforce global 6h runtime limit (FR-013). **Deliverable**: Must log a warning to `logs/timeout.log` and exit with code 143 if limit exceeded, gracefully skipping remaining PRs.
- [ ] T010 Setup logging infrastructure in `src/utils/logger.py` with runtime tracking
- [~] T011 Create `contracts/` YAML schemas for PR data, BugDetection, and AlignmentResult

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Automated PR Data Extraction and Preprocessing (Priority: P1) 🎯 MVP

**Goal**: Extract PR diffs, review comments, and linked issues from GitHub to create a structured dataset.

**Independent Test**: Run extraction script against `microsoft/vscode` (10 PRs) and verify output JSON contains valid diffs, comments, and issue IDs.

### Implementation for User Story 1

- [~] T012 [US1] Implement `src/extraction/fetch_prs.py` to: (a) load and validate the list of 3-5 target repos from `config/settings.py` (FR-001), (b) fetch PRs using GitHub API, (c) handle missing linked issues (empty list), (d) log unverified issues. Output raw JSON to `data/raw/`.
- [X] T013 [US1] Implement `src/extraction/preprocess.py` to truncate diffs exceeding context window and log warnings (Edge Case)
- [~] T014 [US1] Implement `src/extraction/preprocess.py` to extract raw review comments into `data/annotations/raw_comments.json` (NOT ground truth yet)
- [~] T015 [US1] Implement `src/extraction/preprocess.py` to save raw JSON to `data/raw/` with SHA-256 checksums in `data/raw/checksums.json`
- [~] T016 [US1] Add validation logic to ensure `linked_issue_ids` are explicitly labeled as "reported" but not ground truth (FR-011)
- [~] T017 [US1] Implement `src/extraction/preprocess.py` to generate "triangulated ground truth" in `data/derived/human_baseline.json` by: (a) requiring linked issue AND ≥2 independent reviewers (FR-011), (b) EXCLUDING any bug that does not meet strict criteria (NO fallback to "Closed Issue" alone), and (c) flagging excluded bugs. **Output Schema**: JSON list of objects with fields: `pr_id`, `file_path`, `line_start`, `line_end`, `severity`, `is_verified` (bool), `verification_method` (string: "strict_triangulation" or "excluded_unverified").

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - LLM-Assisted Bug Detection Simulation (Priority: P2)

**Goal**: Process extracted diffs using a CPU-tractable LLM (StarCoder2-3B) to generate bug reports with severity.

**Independent Test**: Feed `test-fixtures/bug-synth-001.json` into the pipeline and verify output JSON contains detected bug with correct location/severity.

### Implementation for User Story 2

- [ ] T018 [US2] Implement `src/detection/detect_llm_code.py` to detect LLM-generated code in diffs using heuristics (FR-016) and output `llm_code_flag` in `data/derived/llm_detections.json`
- [ ] T019 [P] [US2] Implement `src/inference/load_model.py` to load StarCoder2-3B in default precision with `device_map="auto"` and `low_cpu_mem_usage=True` to ensure memory usage ≤7GB (FR-015).
- [ ] T019b [P] [US2] Implement `src/utils/memory_watchdog.py` to monitor process memory usage during inference. If usage >7GB, trigger graceful skip and log to `logs/memory_warning.log`.
- [ ] T020 [P] [US2] Implement `src/inference/prompt_templates.py` with standardized bug detection prompt and severity labels (critical, major, minor, style)
- [ ] T021 [US2] Implement `src/analysis/split_dataset.py` to split analysis data into "Human-Written" and "LLM-Generated" subsets based on `llm_code_flag` from T018. **Dependency**: Must run after T018.
- [ ] T022 [US2] Implement `src/inference/run_inference.py` to batch process PRs with retry logic (limited number of retries, short delay) for JSON parsing errors (Edge Case). **Dependency**: Must run after T019 and T021.
- [ ] T023 [US2] Implement `src/inference/run_inference.py` to enforce max latency per PR and skip on timeout (FR-013, FR-015). **Dependency**: Part of T022 logic.
- [ ] T024 [US2] Save LLM outputs to `data/derived/llm_detections.json` with source, file_path, line_start, line_end, severity, description. **Dependency**: Part of T022 logic.
- [ ] T025 [US2] Add logic to flag "LLM error" PRs in `data/derived/llm_detections.json` with field `llm_error_flag: true` and exclude them from final metric calculation (Edge Case). **Deliverable**: Verify `llm_detections.json` contains entries with `llm_error_flag: true` for failed PRs.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently (for implementation); US3 execution depends on US1 and US2 data.

---

## Phase 5: User Story 3 - Comparative Statistical Analysis and Reporting (Priority: P3)

**Goal**: Align LLM and Human bugs, compute metrics, perform statistical tests, and generate the final report.

**Independent Test**: Run analysis on manually constructed PRs and verify Precision/Recall/F1 and p-values are calculated correctly.

### Implementation for User Story 3

- [ ] T026 [US3] Implement `src/analysis/align.py` to match bugs using exact file/line range + cosine similarity with configurable threshold parameter (default 0.85) (FR-003). **Dependency**: Requires T017 (Human Baseline) and T024 (LLM Outputs).
- [ ] T027 [US3] Implement `src/analysis/align.py` to calculate Jaccard index for line overlap (≥ 0.5 required) for valid matches (FR-012). **Note**: STRICT adherence to exact line sets; NO line-shift tolerance.
- [ ] T028 [US3] Implement `src/analysis/metrics.py` to compute Precision, Recall, F1 against triangulated ground truth (FR-004).
- [ ] T029 [US3] Implement `src/analysis/metrics.py` to calculate "Recall relative to the triangulated ground truth" (FR-017) by identifying "LLM-only" detections (bugs in LLM output but NOT in `human_baseline.json`). **Output**: Must include key `recall_llm_only` in the final metrics JSON.
- [ ] T030 [US3] Implement `src/analysis/metrics.py` to exclude unverified bugs (where `is_verified == false` in `human_baseline.json`) from ground truth calculation (Edge Case).
- [ ] T031 [US3] Implement `src/analysis/stats.py` to perform McNemar's test for detection rates and Chi-square for severity distributions (FR-005).
- [ ] T032 [US3] Implement `src/analysis/stats.py` to calculate and report effect sizes (Odds Ratio for McNemar's, Cramér's V for Chi-square) alongside p-values (Constitution VII). **Deliverable**: Output JSON must include `effect_size_odds_ratio` and `effect_size_cramers_v`.
- [ ] T033 [US3] Implement `src/analysis/sensitivity.py` to sweep similarity thresholds across a range of values using the configurable parameter from T026 and report F1 variance (FR-006).
- [ ] T034 [US3] Implement `src/reporting/generate_report.py` to output final report with P-values, metrics, and associational framing (FR-007, FR-014). **Deliverable**: Report must contain the exact phrase "correlate with" when discussing impact.
- [ ] T034a [US3] Ensure `results/final_report.md` explicitly states that alignment used strict Jaccard index without line-shift tolerance (Constraint Preservation).
- [ ] T035 [US3] Generate `results/final_report.md` and `results/metrics.json`. **Deliverable**: Inject content hashes of `data/derived` files used into the report footer (Constitution IV).

**Checkpoint**: All user stories should now be independently functional (for implementation); US3 execution requires data from US1 and US2.

---

## Phase 6: Testing & Validation

**Purpose**: Ensure data integrity and metric correctness

- [ ] T036 [P] [US1] Unit test `src/extraction/fetch_prs.py` with mocked GitHub API responses
- [ ] T037 [P] [US2] Unit test `src/inference/load_model.py` to verify CPU-only loading and memory constraints
- [ ] T038 [P] [US3] Unit test `src/analysis/align.py` with known Jaccard index and similarity scores
- [ ] T039 [P] [US3] Integration test `tests/integration/test_end_to_end.py` processing a set of PRs end-to-end
- [ ] T040 [P] Contract test `tests/contract/test_schema_validation.py` for all JSON outputs
- [ ] T041 [P] Verify `data/raw/checksums.json` matches raw data files

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T042 [P] Documentation updates in `quickstart.md` and `README.md`
- [ ] T043 Code cleanup and refactoring
- [ ] T044 Performance optimization for batch processing (ensure ≤6h runtime for 500 PRs)
- [ ] T045 [P] Additional unit tests in `tests/unit/`
- [ ] T046 Run `quickstart.md` validation to ensure reproducibility

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed) for implementation
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - **Execution Dependency**: Requires output from US1 (T017) for ground truth validation.
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - **Execution Dependency**: Requires output from US1 (T017) and US2 (T024) for alignment and metrics.

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel for **implementation** (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

**Note on Execution**: While US1, US2, and US3 can be implemented in parallel, the **runtime pipeline** must execute sequentially: US1 (Data) → US2 (Inference) → US3 (Analysis).

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
3. Stories complete and integrate independently (for code); execution requires data flow.

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence