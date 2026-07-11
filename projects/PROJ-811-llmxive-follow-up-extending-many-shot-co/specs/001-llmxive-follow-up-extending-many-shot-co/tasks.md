# Tasks: llmXive Follow-up: Logical Dependency vs. Semantic Curvature in Many-Shot ICL

**Input**: Design documents from `/specs/001-logical-dependency-icl/`
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

- [X] T001 Create project structure matching directory tree in `plan.md` Section "Project Structure" (`projects/PROJ-811-llmxive-follow-up-extending-many-shot-co/`)
- [X] T002 Initialize Python 3.11 project with `requirements.txt` (networkx, llama-cpp-python, pandas, statsmodels, sentence-transformers, pyyaml, huggingface_hub)
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Setup `data/` directory structure (`raw/`, `processed/`, `results/`) and `artifacts/` for checksums
- [X] T005 [P] Implement `code/src/update_state.py` for Constitution Principle V (artifact hashing and state YAML updates)
- [X] T006 [P] Setup environment configuration management (load seeds, model paths from `.env` or YAML)
- [ ] T007 Create base data loading utilities for HuggingFace datasets (`aaabiao/DAG_sft`)
- [X] T008 Implement `code/src/parser.py` skeleton with `networkx` DAG initialization logic

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Logical Dependency Graph Construction (Priority: P1) 🎯 MVP

**Goal**: Parse raw CoT traces into Directed Acyclic Graphs (DAGs) and calculate "Logical Difficulty Scores" (max path depth), validated against a human-annotated gold standard.

**Independent Test**: The system can ingest a raw CoT trace file, output a valid DAG structure for each example, and calculate a maximum path depth score that correlates (r ≥ 0.6) with human-judged logical complexity from a labeled subset of 50 traces from the actual SFT dataset.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T009 [P] [US1] Unit test for cycle detection and invalid trace flagging in `code/tests/test_parser.py`
- [ ] T010 [P] [US1] Unit test for DAG depth calculation logic in `code/tests/test_parser.py`
- [ ] T011 [P] [US1] Integration test for gold-standard correlation validation (r ≥ 0.6) in `code/tests/test_integration.py`

### Implementation for User Story 1

- [ ] T012 [US1] Implement CoT trace parser in `code/src/parser.py` to convert text steps to `networkx` DAG nodes/edges
- [~] T013 [US1] Implement cycle detection logic (max cycle length of 5 steps, >3 incoming edges) and flagging mechanism in `code/src/parser.py` <!-- SKIPPED: YAML+regex parse failed (while scanning an alias
 in "<unicode string>", line 4, column 1:
 **Input**: Design documents from...
 ^
expected alphabetic or numeric character, but found '*'
 in "<unicode string>", line 4, column 2:
 **Input**: Design documents from...
 ^) -->
- [~] T014 [US1] Implement "Logical Difficulty Score" calculation (max path depth) in `code/src/parser.py`
- [~] T015 [US1] Load/Verify existence of `data/processed/gold_standard_annotations.json`. If missing, generate a template file with instructions for expert annotation (handling the 'deferred' assumption) rather than failing.
- [~] T016 [US1] Implement validation script to compute Pearson correlation (r) between DAG depth (from T014) and human-rated logical complexity (from T015), outputting `data/processed/validation_report.json` with r-value and pass/fail status (exit 0 only if r ≥ 0.6) (Plan Deviation: GeoQA replaced by SFT human ratings). **Depends on: T014, T015**.
- [~] T017 [US1] Implement filtering and exclusion logic to remove invalid traces (cycles) from `data/processed/dag_manifest.json` and ensure they are not included in downstream prompt generation (US-001 AC-2)
- [~] T018 [US1] Generate `data/processed/dag_manifest.json` containing dependency depths for all VALID traces only

**⚠️ GATING CHECK**: T016 must pass (r ≥ 0.6) AND T017 must complete before Phase 4 can begin.

---

## Phase 4: User Ordering Strategy Generation (Priority: P2)

**Goal**: Generate three distinct multi-shot prompt configurations (Original CDS, Logical Ascending, Logical Random) for each test seed.

**Independent Test**: The system can take the parsed dataset and the three strategy definitions, generating three distinct prompt files where the sequence of examples strictly adheres to the specified sorting or shuffling logic.

**⚠️ DEPENDENCY**: This phase requires output from Phase 3 (T018) AND T016 (Validation Pass). Do not start until Phase 3 is complete and validated.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [~] T019 [P] [US2] Unit test for "Logical Ascending" sort order verification in `code/tests/test_prompt_gen.py`
- [~] T020 [P] [US2] Unit test for deterministic shuffling with fixed seed in `code/tests/test_prompt_gen.py`
- [~] T021 [P] [US2] Integration test for prompt file generation across multiple seeds in `code/tests/test_integration.py`

### Implementation for User Story 2

- [~] T022 [US2] Implement "Logical Ascending" sorter in `code/src/prompt_gen.py` (sort by DAG depth from T018, non-decreasing). **Depends on: T016 (Validation Pass)**.
- [~] T023 [US2] Implement "Logical Random" shuffler in `code/src/prompt_gen.py` (fixed seed, preserve distribution)
- [~] T024a [US2] Implement "Original CDS" (Semantic Curvature) metric calculation in `code/src/prompt_gen.py`. Algorithm: Compute sentence embeddings via SBERT, calculate cosine similarity between adjacent sentences, then compute the variance of these similarities as the "Curvature Score".
- [~] T024b [US2] Implement "Original CDS" sorting logic in `code/src/prompt_gen.py` using the Curvature Score from T024a.
- [~] T025 [US2] Implement prompt template assembler to combine a set of examples into a single prompt string in `code/src/prompt_gen.py`
- [~] T026 [US2] Create batch runner to generate prompts for multiple seeds across three strategies, saving to `data/processed/prompts/`
- [ ] T027 [US2] Add validation to ensure no duplicate orderings within a strategy group across seeds
- [ ] T028 [US2] Generate `data/processed/prompt_manifest.json` mapping seed/strategy to file paths

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - CPU-Only Inference & Statistical Analysis (Priority: P3)

**Goal**: Execute inference on generated prompts using `llama.cpp` (CPU) and perform Linear Mixed-Effects Model (LMM) analysis to test for interaction effects.

**Independent Test**: The system can run inference on a sample of few-shot prompts using `llama.cpp` (CPU mode), collect accuracy metrics, aggregate them by seed, and output a statistical report confirming whether the interaction term in the LMM is significant.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T029 [P] [US3] Unit test for accuracy calculation and retry logic in `code/tests/test_inference.py`
- [ ] T030 [P] [US3] Unit test for LMM model fitting and p-value extraction in `code/tests/test_analysis.py`
- [ ] T031 [P] [US3] Integration test for full pipeline (Prompt → Inference → Stats) on a small subset in `code/tests/test_integration.py`

### Implementation for User Story 3

- [ ] T032 [US3] Implement `llama.cpp` inference runner in `code/src/inference.py` (CPU mode, Q4_K_M quantization, retry logic)
- [ ] T033 [US3] Implement model selection logic for "Reasoning" vs "Non-Reasoning" classes in `code/src/inference.py`
- [ ] T034 [US3] Implement result aggregation script to collect accuracy per seed/strategy/model in `code/src/analysis.py`
- [ ] T035a [US3] Implement Linear Mixed-Effects Model (LMM) in `code/src/analysis.py` (Fixed: Strategy, ModelType, Interaction; Random: Seed, PromptID) to test interaction effects (Plan Deviation from Spec FR-004 ANOVA).
- [ ] T035b [US3] Implement calculation of Partial Eta-Squared (or LMM-equivalent effect size like Cohen's f²) from the LMM results to satisfy SC-005. Document the deviation from Spec FR-004 (ANOVA) to Plan LMM in `artifacts/stats_report.md` including a power analysis justification (alpha=0.05, power=0.8, effect_size=0.25) using `statsmodels.stats.power`.
- [ ] T036 [US3] Implement Bonferroni correction for multiple comparisons on post-hoc tests in `code/src/analysis.py`
- [ ] T038 [US3] Implement Levene's test for variance stability (SC-001): Calculate the variance of the MEAN accuracy across multiple seeds. for "Logical Ascending" and "Logical Random" strategies separately. Compare the two variances to verify ≥15% reduction (p < 0.10). Append results to `artifacts/stats_report.md`.
- [ ] T037 [US3] Generate final statistical report (`artifacts/stats_report.md`) with p-values, effect sizes (partial eta-squared), variance comparisons, and the deviation note from T035b
- [ ] T039 [US3] Add timeout handling and failure logging for inference runs exceeding a prolonged duration limit

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T040 [P] Documentation updates in `docs/` (Quickstart, Data Model, Contracts)
- [ ] T041 Code cleanup and refactoring of `parser.py` and `inference.py`
- [ ] T042 Performance optimization for DAG parsing: Refactor `parser.py` to achieve < 15 min runtime on 1000 raw/CoT traces; verify by running benchmark script and recording time in `artifacts/perf_log.txt`
- [ ] T043 [P] Additional unit tests (if requested) in `code/tests/unit/`
- [ ] T044 Run `quickstart.md` validation to ensure end-to-end reproducibility
- [ ] T045 Verify `data/results.csv` integrity and checksum update via `update_state.py`

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
- **User Story 2 (P2)**: **MUST START AFTER Phase 3 is complete AND T016 (Validation) passes**. Depends on T018 (DAG Manifest) for "Logical Ascending" sort and T024a/b for "Original CDS". Cannot run in parallel with Phase 3 implementation.
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2 output (Prompts) for inference

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, User Story 1 can start immediately.
- **User Story 2 and 3 cannot start until User Story 1 is complete and validated (T016/T017).**
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members ONLY if US1 is already complete.

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Unit test for cycle detection and invalid trace flagging in code/tests/test_parser.py"
Task: "Unit test for DAG depth calculation logic in code/tests/test_parser.py"
Task: "Integration test for gold-standard correlation validation (r ≥ 0.6) in code/tests/test_integration.py"

# Launch all models for User Story 1 together:
Task: "Implement CoT trace parser in code/src/parser.py"
Task: "Implement cycle detection logic in code/src/parser.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (including T016 Validation and T017 Exclusion)
4. **STOP and VALIDATE**: Test User Story 1 independently (DAG construction + correlation + exclusion). T016 must pass (r ≥ 0.6).
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently (T016 must pass) → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo (Prompt generation)
4. Add User Story 3 → Test independently → Deploy/Demo (Inference + Stats + LMM)
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Parser + Validation + Exclusion) - **Must complete first**
 - Developer B: (Wait for US1 completion before starting US2)
 - Developer C: (Wait for US2 completion before starting US3)
3. Stories complete and integrate sequentially due to data flow dependencies.

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **CRITICAL**: Ensure `llama.cpp` inference tasks (T032) strictly use CPU-only flags and Q4_K_M quantization to fit within 7GB RAM.
- **CRITICAL**: Ensure DAG parser (T012) handles edge cases (cycles, ambiguous steps) as per spec edge cases.
- **CRITICAL**: T016 (Validation) is a hard gate. If r < 0.6, the "Logical Difficulty Score" is invalid, and the project must pivot or report failure before proceeding to US2.
- **CRITICAL**: T017 (Exclusion) must remove invalid traces from the manifest to prevent data leakage.
- **CRITICAL**: Phase 4 (US2) cannot start until Phase 3 (US1) is fully complete and validated (T016 passed).
- **CRITICAL**: T024a explicitly defines the "curvature" metric (variance of adjacent cosine similarities) to satisfy Spec Assumptions.
- **CRITICAL**: T035b ensures SC-005 (effect size) is met despite the ANOVA->LMM deviation.
- **CRITICAL**: T038 explicitly calculates variance of mean accuracy across 10 seeds to satisfy SC-001.