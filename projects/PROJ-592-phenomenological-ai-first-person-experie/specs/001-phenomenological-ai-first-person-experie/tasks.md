# Tasks: Phenomenological AI: First-Person Experience Modeling

**Input**: Design documents from `/specs/592-phenomenological-ai-first-person-experie/`
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

- [X] T001 [P] Write `scripts/init_project.py` script to scaffold directories: `code/`, `data/raw/`, `data/processed/`, `data/qualitative/`, `tests/unit/`, `tests/integration/`, `specs/contracts/`. **Execution**: Run `python scripts/init_project.py` to verify completion.
- [X] T002 [P] {{claim:c_6e3384cd}} **Execution**: Run `pip freeze > code/requirements.txt` after installing dependencies.
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Implement `code/config.py` with:
 1. Seeds, paths, and model IDs (Primary: `TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF ` for CI; Optional: 7B models for local only).
 2. **Phenomenological Marker Dictionaries**: Define concrete lists for 'sensory' (e.g., see, hear, feel, touch, taste, smell, light, sound), 'temporal' (e.g., now, then, before, after, moment, duration), and 'intentional' (e.g., think, believe, desire, intend, perceive, experience) keywords as per FR-008 and FR-009.
- [X] T005 [P] Setup `code/utils/logging.py` for structured logging, warning capture, and retry logic (multiple attempts per sample)
- [X] T006 [P] Implement `code/utils/io.py` for JSON/CSV schema validation and artifact archiving
- [X] T007 [P] Create base data schemas in `specs/contracts/`: `specs/contracts/generation_output.schema.yaml`, `specs/contracts/validity_scores.schema.yaml`, `specs/contracts/qualitative_ratings.schema.yaml`
- [X] T008 [P] Implement `code/generation/prompt_engineering.py` with the defined strategies (Direct, Hypothetical, Comparative, Role-play) and 20 base prompts loaded from `data/prompts/base_prompts.json`. **Execution**: {{claim:c_4d5dfa7d}}

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Automated Report Generation Pipeline (Priority: P1) 🎯 MVP

**Goal**: Generate the corpus of phenomenological reports using CPU-tractable models and four prompting strategies.

**Independent Test**: Execute `code/generation/runner.py` and verify `data/raw/` contains ≥80 samples per strategy (totaling a substantial set of samples: 80 samples × 20 prompts × 4 strategies) with valid JSON metadata (seed, prompt, strategy) and no CUDA errors.

### Implementation for User Story 1

- [X] T009 [P] [US1] Implement `code/generation/runner.py` using `llama-cpp-python` for `TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF ` (specifically `tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf`) on CPU-only environment (FR-002). **Constraint**: Do not use 7B models in this script; they are excluded from CI. Target volume: approximately 80 samples per prompt per strategy, yielding a substantial total dataset for analysis..
- [X] T010 [US1] Implement retry logic in `runner.py`: A fixed number of attempts per prompt/strategy combination, marking samples as missing after failure (FR-001).
- [X] T011 [P] [US1] Create `code/generation/control_corpus.py` to generate ≥80 control samples using `datasets.load_dataset("arxiv_nlp")` with `filter='arxiv_nlp'` and random sampling. **Verification**: Ensure these samples are processed through the same three validity metrics (Consistency, Stability, Markers) as the phenomenological reports to compute discriminant validity (FR-001).
- [X] T012 [P] [US1] Implement `code/generation/runner_local.py` for the second checkpoint (Mistral-7B or Llama-7B) using `llama-cpp-python` with 4-bit GGUF. **Note**: This script is for local execution only (users with ≥16GB RAM) and satisfies the "two checkpoints" requirement of FR-001/US-1. It is NOT used in the primary CI path.
- [X] T013 [US1] Add timeout handling and sample-size logging to ensure ≥80 successful samples per condition. **Note**: This is the CI minimum; The Plan's statistical power target is a research goal to be addressed via sensitivity analysis if CI limits are hit.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Phenomenological Metric Computation (Priority: P2)

**Goal**: Compute Internal Consistency, Semantic Stability, and Marker Presence metrics, then perform statistical analysis.

**Independent Test**: Run `code/analysis/stats.py` on a small subset of reports and verify `data/processed/validity_scores.csv` contains non-null scores for all three metrics and correct statistical test outputs.

### Implementation for User Story 2

- [X] T014 [P] [US2] Implement `code/analysis/consistency.py`: Load NLI model `cross-encoder/stsb-distilroberta-base ` (CPU-safe), compute pairwise contradiction counts, handle length limits by skipping pairs with warnings (US-2 Edge Case).
- [X] T015 [P] [US2] Implement `code/analysis/stability.py`: Compute embeddings for repeated generations, calculate cosine similarity, and store stability scores.
- [X] T016 [P] [US2] Implement `code/analysis/markers.py`: Load the keyword dictionary defined in `code/config.py` (T004) to count sensory, temporal, and intentional markers (FR-008). **Dependency**: Requires T004 (Phase 2) and T009-T013 (Phase 3) to be complete.
- [X] T017 [P] [US2] Implement `code/analysis/fdr_correction.py` and `code/analysis/tukey_hsd.py` for Benjamini-Hochberg FDR and Tukey HSD post-hoc tests (FR-005).
- [X] T018 [US2] Implement `code/analysis/stats.py` to orchestrate metric aggregation. **Logic**: Run Shapiro-Wilk and Levene tests (FR-012). If assumptions (p≥0.05) hold, run ANOVA + FDR + Tukey. If violated, skip FDR/Tukey and run Kruskal-Wallis instead.
- [X] T019 [US2] Implement `code/analysis/sensitivity_analysis.py` to test validity score weights (FR-006) and address the sample size gap (CI vs Research 1024) by analyzing robustness across sample subsets. **Justification**: Output a report justifying the fixed weights used in the Constitution based on sensitivity results.
- [X] T020 [P] [US2] Implement `code/analysis/validity_justification.py` to cite phenomenology literature or perform alternative metric sensitivity (FR-009).
- [X] T021 [P] [US3] Implement `code/validation/human_rater.py` to load generated reports, apply independent validation rubric from `code/validation/rubric.md` (FR-010), and store ratings. **Dependency**: Requires T020 to create the rubric.
- [X] T022 [US2] Implement Cohen's κ calculation and threshold sensitivity analysis in `code/analysis/sensitivity_kappa.py`: Analyze robustness of conclusions across a range of kappa thresholds as required by FR-011. **Note**: Report the threshold as the benchmark., but do not enforce it as a hard gate in the analysis logic itself.
- [X] T023 [US3] Create `code/validation/stratified_sampler.py` to select a representative set of reports per condition for human rating (SC-002).
- [X] T024 [US2] Implement `code/main.py` to orchestrate the full pipeline: Generation → Metrics → Stats (enables US1+US2 integration testing).
- [X] T034 [US2] Implement `code/analysis/experience_trace.py` (FR-009/Review-DanRockmore): Create a lightweight attention-mapping script that extracts and logs the top-k token attention heads for specific phenomenological keywords (e.g., "feel", "now") to trace internal state activation patterns. Output to `data/processed/experience_traces.json`. <!-- ATOMIZE: requested -->
- [X] T035 [US2] Implement `code/analysis/stylistic_comparison.py` (FR-009/Review-DavidKrakauer): Add a comparative analysis module that explicitly tests the "phenomenological style" hypothesis by comparing the generated reports against a baseline of "ordinary conversation" (e.g., from `datasets.load_dataset("imdb")` or `common_crawl` subset) to measure the operational difference in marker density and structural coherence.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Qualitative Validation & Reproducibility (Priority: P3)

**Goal**: Facilitate human evaluation, compute inter-rater reliability, and archive all artifacts.

**Independent Test**: Verify `data/qualitative/` contains anonymized rating sheets, `code/validation/human_rater.py` calculates Cohen's κ correctly, and the archive script commits all artifacts.

### Implementation for User Story 3

- [X] T020 [P] [US3] **Create** `code/validation/rubric.md`: Author the independent validation rubric document required by FR-010, defining clear criteria for human raters separate from automated metrics. <!-- FAILED: unspecified -->
- [X] T023 [US3] Create `code/validation/stratified_sampler.py` to select a representative set of reports per condition for human rating (SC-002).
- [X] T025 [US3] Implement `code/utils/archiver.py` to package prompts, seeds, scripts, and anonymized ratings for public reproducibility (FR-007).
- [X] T036 [US3] Implement `code/validation/turing_simulation.py` (Review-AlanTuring): Create a script to generate "conversation logs" where the model attempts to sustain a first-person dialogue without contradiction. Implement a "distinction metric" that measures the rate of detected contradictions or breaks in persona over a long horizon (e.g., an extended sequence of turns), addressing the operational test for indistinguishability.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T012 [P] [Optional] Implement `code/generation/runner_local.py` for local 7B model execution (Mistral-7B/Llama-7B) with explicit hardware warnings. **Note**: This is NOT required for primary research validity or CI execution (Plan.md). 7B models are excluded from the primary CI path due to RAM constraints.
- [ ] T030a [P] Add CLI usage examples and environment setup instructions to `quickstart.md`. **Examples**: Document `python main.py --mode generation`, `python main.py --mode analysis`, `python main.py --mode validate`. <!-- FAILED: unspecified -->
- [X] T030b [P] Add schema descriptions and data flow diagrams to `data-model.md`
- [X] T031a [P] Refactor `code/analysis/stats.py` to add type hints and remove duplicate imports.
- [X] T031b [P] Refactor `code/utils/logging.py` to standardize log levels and output formats.
- [X] T032 [P] Add unit tests in `tests/unit/`: specifically `tests/unit/test_markers.py::test_count_sensory_keywords`, `tests/unit/test_consistency.py::test_pairwise_contradiction`.
- [X] T033 [P] Run `quickstart.md` validation to ensure full pipeline execution ≤6 hours on free-tier <!-- FAILED: unspecified -->
- [X] T037 [US2/US3] Update `research.md` and `data-model.md` to document the implementation details of "Experience Trace" (T034) and "Stylistic Comparison" (T035) as secondary outputs for validity, addressing Review-DanRockmore and Review-DavidKrakauer concerns. **Note**: Do not modify `spec.md` or `plan.md` requirements; document implementation in research docs. **Dependency**: Must run after T034, T035, T036.
- [X] T038 [P] Add a "Phenomenological Incoherence" test case to `tests/unit/test_metrics.py` (Review-FreemanDyson): Verify that the system does not penalize inherently incoherent but phenomenologically accurate reports (e.g., stream-of-consciousness) if they maintain internal marker consistency.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Phase N)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 data generation
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US1 data and US2 metrics
- **Polish (Phase N)**: Depends on US1, US2, US3 logic to be in place for optional enhancements

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
 - Developer A: User Story 1 (Generation)
 - Developer B: User Story 2 (Analysis)
 - Developer C: User Story 3 (Validation)
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
- **CPU Constraint**: All tasks must be executable on a minimal CPU configuration. No CUDA, no 8-bit/4-bit quantization requiring GPU drivers. Use `llama-cpp-python` with GGUF for TinyLlama.
- **Model Constraint**: TinyLlama-1.1B is the **only** model for the primary CI pipeline. 7B models are optional/local-only and excluded from the primary research validity path.
- **Review Integration**: Tasks T034, T035, T036, T037, and T038 specifically address the philosophical and methodological concerns raised by Alan Turing, Dan Rockmore, David Krakauer, and Freeman Dyson regarding operational tests, internal state tracing, stylistic distinction, and incoherence metrics.
