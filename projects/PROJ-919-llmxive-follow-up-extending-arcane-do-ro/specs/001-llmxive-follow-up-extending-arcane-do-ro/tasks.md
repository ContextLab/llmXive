# Tasks: llmXive follow-up: extending "ArcANE"

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

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure per implementation plan (`src/`, `tests/`, `data/`, `specs/001-gene-regulation/`)
- [X] T002 Initialize Python 3.11 project with `requirements.txt` (transformers, llama-cpp-python, datasets, scikit-learn, scipy, pandas, numpy, tiktoken, hypothesis, pytest)
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Setup data directory structure (`data/raw/`, `data/derived/`, `data/gold_standard/`, `artifacts/`)
- [X] T005 [P] Implement robust logging infrastructure in `src/lib/utils.py` (file + console handlers, JSON formatting)
- [X] T006 [P] Create base configuration management for seeds and model paths in `src/lib/config.py`
- [X] T007 Implement data validation helpers in `src/lib/validators.py` (schema checks, type clamping)
- [ ] T008 Setup experiment state tracking (logging run IDs, timestamps, and parameter hashes)
- [ ] T009a [P] [US3] Create `data/gold_standard/human_annotations.json` following `calibration.schema.yaml` (fields: character, scenario, ground_truth_score, ground_truth_phase) for Judge Calibration and Gold Standard validation (FR-006, FR-007). After creation, generate a SHA-256 checksum and record it in the project state file (Constitution Principle III)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Construct and Validate Character Arc Specifications (Priority: P1) 🎯 MVP

**Goal**: Allow researchers to define and store independent Coarse and Fine psychological axes for characters.

**Independent Test**: A researcher can input a character name and receive two distinct, non-overlapping JSON objects representing the Coarse and Fine axes, verified against semantic overlap constraints.

### Tests for User Story 1 (OPTIONAL) ⚠️

- [X] T009 [P] [US1] Unit test for axis semantic overlap constraint in `tests/unit/test_axis_validation.py`. Note: This test depends on T010 (schema) and T011 (service) being implemented first; it is written first (TDD) but will fail until T010/T011 are complete.

### Implementation for User Story 1

- [ ] T010 [P] [US1] Define JSON schemas for `CharacterAxis` (Coarse/Fine) in `specs/001-gene-regulation/contracts/axis.schema.yaml`
- [ ] T011 [US1] Implement `src/services/axis_generator.py` with manual input interface for defining axes, including serialization logic to produce `data/derived/axes.jsonl` (T013) AND implement `display_axis_output(coarse, fine)` in `src/cli/run_experiment.py` to print the two distinct JSON objects to the console (US-1) <!-- SKIPPED: YAML+regex parse failed (while parsing a block mapping
expected <block end>, but found ':'
 in "<unicode string>", line 1, column 1:
: |
 ^) -->
- [ ] T011a [US1] Implement `src/cli/axis_input.py` with independent input validation logic: requires two separate text blocks for Coarse and Fine axes, prevents copy-paste between fields, and validates that Fine axes originate from independent narrative observations (FR-001, US-1). The validation MUST compare the 'Fine' axis text against a provided 'Source Text Segment' from the narrative using a semantic similarity threshold to prove independence.
- [ ] T012 [US1] Implement semantic validation logic in `src/services/axis_generator.py` (lexical overlap > 0.4, embedding cosine distance < 0.3)
- [ ] T012a [US1] Implement logic in `src/cli/axis_input.py` to verify that input data originates from independent narrative observations as per FR-001 (e.g., separate input streams, validation against source text segments)
- [ ] T013 [US1] Create `data/derived/axes.jsonl` writer to store validated axis definitions
- [ ] T014 [US1] Add CLI entry point in `src/cli/run_experiment.py` to initialize axes for a given character

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Generate Out-of-World Probes (Priority: P2)

**Goal**: Generate at least 50 unique "Out-of-World" scenario prompts per character that are semantically distant from the source text.

**Independent Test**: The system generates a batch of probes, and a sample check confirms none contain direct quotes/plot points and average cosine similarity to source text is < 0.3.

### Tests for User Story 2 (OPTIONAL) ⚠️

- [ ] T015 [P] [US2] Unit test for probe regeneration loop and similarity threshold in `tests/unit/test_probe_generation.py`

### Implementation for User Story 2

- [ ] T016 [P] [US2] Define JSON schema for `Probe` in `specs/001-gene-regulation/contracts/probe.schema.yaml`
- [ ] T017 [US2] Implement `src/services/probe_generator.py` with logic to generate novel scenarios based on character axes
- [ ] T018 [US2] Implement semantic similarity check (cosine similarity < 0.3) against source text corpus in `src/services/probe_generator.py`
- [ ] T019 [US2] Implement regeneration loop (max reasonable attempts) with discard logic for invalid probes in `src/services/probe_generator.py`, including specific error handling: implement logic to log 'Generation Limit Exceeded' and proceed with available valid probes (if >= 50) or mark character as invalid if attempts > 150 (Edge Cases, FR-002)
- [ ] T020 [US2] Create `data/derived/probes.jsonl` writer to store validated out-of-world probes
- [ ] T021 [US2] Implement error handling for "Generation Limit Exceeded" (log error, proceed if >= 50 valid probes)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Execute Hybrid Prompting and Consistency Evaluation (Priority: P3)

**Goal**: Execute the target model under three conditions, calibrate a Judge model, and perform statistical analysis.

**Independent Test**: The system processes a probe through all conditions, outputs structured results with scores, and performs a Shapiro-Wilk test to select ANOVA or Friedman.

### Tests for User Story 3 (OPTIONAL) ⚠️

- [ ] T022 [P] [US3] Contract test for Judge output format and clamping in `tests/unit/test_judge_clamp.py`
- [ ] T023 [P] [US3] Integration test for full experiment flow in `tests/integration/test_experiment_flow.py`

### Implementation for User Story 3

- [ ] T024 [P] [US3] Implement model loading utilities in `src/models/loader.py` (CPU-quantized small language models, 4-bit)
- [ ] T025 [US3] Implement `src/services/judge_service.py` for LLM-based consistency scoring using a standard Likert scale, with output validation, clamping, and implementation of logic to extract and return `adherence_flag` (bool) alongside the score. The `adherence_flag` MUST be determined using VADER or BERT-based sentiment/coherence analysis of the response against the target phase, NOT by keyword presence (FR-004, US-3).
- [ ] T026 [US3] Implement rule-based scoring metric in `src/services/judge_service.py`: `calculate_rule_score(response, keywords)` returning a discrete score based on sentiment alignment and coherence (using VADER or BERT, NOT keyword presence) per FR-004 (distinct from Judge).
- [ ] T026a [US3] Implement `aggregate_consistency_scores` in `src/analysis/stats_engine.py` to combine the Judge score (T025) and rule-based score (T026) into a single 'Consistency Score' artifact and write it to `data/derived/results.jsonl` (FR-005, SC-001).
- [ ] T027 [US3] Implement Judge Calibration step in `src/services/judge_service.py` (Kappa > 0.6 against `data/gold_standard/human_annotations.json`) AND implement `validate_against_gold_standard(results, gold_data)` in `src/analysis/stats_engine.py` to compute correlation/error metrics against `data/gold_standard/human_annotations.json` and validate consistency scores against the external Gold Standard dataset (FR-006)
- [ ] T028 [US3] Implement `src/services/experiment_runner.py` to run target model under Coarse, Fine, and Hybrid conditions
- [ ] T029 [US3] Implement timeout handling and default score assignment (0) for failed generations in `src/services/experiment_runner.py`
- [ ] T029a [US3] Instrument `experiment_runner` and `stats_engine` to capture, log, and report the total wall-clock time of the full experiment run to `data/derived/timing.log` to verify against the predefined confidence interval time limit (SC-003).
- [ ] T030 [US3] Implement `src/analysis/stats_engine.py` to aggregate scores and perform Shapiro-Wilk test
- [ ] T031 [US3] Implement statistical test selection in `src/analysis/stats_engine.py` (ANOVA if normal, Friedman if not)
- [ ] T033 [US3] Implement `run_statistical_test(scores, test_type)` in `src/analysis/stats_engine.py` to execute the chosen statistical test (ANOVA or Friedman) and write the p-value and effect size to `data/derived/stats_results.json` (FR-005)
- [ ] T032 [US3] Create `data/derived/results.jsonl` writer to store raw responses and scores
- [ ] T035 [US3] Add CLI entry point in `src/cli/run_experiment.py` to trigger the full experiment pipeline

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T036 [P] Documentation updates in `specs/001-gene-regulation/quickstart.md`
- [ ] T037 Code cleanup and refactoring for error handling consistency
- [ ] T038 Performance optimization for batch processing of probes
- [ ] T039 [P] Additional unit tests for statistical engine edge cases in `tests/unit/test_stats_engine.py`
- [ ] T040 Run `quickstart.md` validation to ensure end-to-end reproducibility on CPU

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on T013 (axes.jsonl) for prompt generation context
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on T020 (probes.jsonl) and T013 (axes.jsonl) for execution

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
Task: "Unit test for axis semantic overlap constraint in tests/unit/test_axis_validation.py"

# Launch all models for User Story 1 together:
Task: "Define JSON schemas for CharacterAxis in specs/001-gene-regulation/contracts/axis.schema.yaml"
Task: "Implement logging infrastructure in src/lib/utils.py"
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