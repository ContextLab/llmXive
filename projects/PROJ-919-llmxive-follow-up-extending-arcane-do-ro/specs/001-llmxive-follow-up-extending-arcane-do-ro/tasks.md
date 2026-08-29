# Tasks: llmXive follow-up: extending "ArcANE"

**Input**: Design documents from `/specs/001-gene-regulation/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this belongs to (e.g., US1, US2, US3)
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
- [X] T002 Initialize Python project with `requirements.txt` (transformers, llama-cpp-python, datasets, scikit-learn, scipy, pandas, numpy, tiktoken, hypothesis, pytest)
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure and Data Contracts that MUST be complete before ANY user story can be implemented.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete. This phase includes the definition of all JSON schemas required for data integrity.

- [ ] T004 Setup data directory structure (`data/raw/`, `data/derived/`, `data/gold_standard/`, `artifacts/`)
- [X] T005 [P] Implement robust logging infrastructure in `src/lib/utils.py` (file + console handlers, JSON formatting)
- [X] T006 [P] Create base configuration management for seeds and model paths in `src/lib/config.py`
- [X] T007 Implement data validation helpers in `src/lib/validators.py` (schema checks, type clamping)
- [X] T008 [P] [US3] Setup experiment state tracking (logging run IDs, timestamps, parameter hashes, AND content hashes for state/parameters) in `src/lib/state.py` to satisfy Constitution Principle V.
- [ ] T009b [P] **Create File**: `specs/001-gene-regulation/contracts/calibration.schema.yaml`. **Content**: Define YAML schema with required fields: `character` (string), `scenario` (string), `ground_truth_score` (int 1-5), `ground_truth_phase` (string). This task must produce the actual YAML file.
- [ ] T010a [P] **Create File**: `specs/001-gene-regulation/contracts/axis.schema.yaml`. **Content**: Define YAML schema for `CharacterAxis.Coarse` with required fields: `character` (string), `axis_name` (string), `description` (string).
- [ ] T010b [P] **Create File**: `specs/001-gene-regulation/contracts/axis.schema.yaml`. **Content**: Define YAML schema for `CharacterAxis.Fine` with required fields: `character` (string), `axis_name` (string), `description` (string), `source_observation` (string).
- [ ] T016a [P] **Create File**: `specs/001-gene-regulation/contracts/probe.schema.yaml`. **Content**: Define YAML schema for `Probe` with required fields: `character` (string), `scenario_text` (string), `target_phase` (string), `similarity_score` (float).
- [ ] T009d [US3] **Download Real Gold Standard**: Implement script to download a verified real "Gold Standard" dataset using `datasets.load_dataset`. **Primary Source**: `lmsys/lmsys-chatbot-arena` (filter for single-turn human preference pairs). **Logic**: If unavailable, raise `FileNotFoundError`. Do NOT generate synthetic data. Save raw download to `data/raw/gold_standard_raw.jsonl`. Use fixed seed for reproducibility. <!-- FAILED: unspecified -->
- [ ] T009c [US3] **Process Gold Standard**: Filter `data/raw/gold_standard_raw.jsonl` to exactly n=20 samples for `data/gold_standard/human_annotations.json`. **Logic**: 1) Filter for samples with >200 tokens in the 'prompt' field. [UNRESOLVED-CLAIM: c_4b7a0f68 — status=not_enough_info] 2) Select a subset of samples using `random.seed(42)`. 3) Map the 'chosen' response to a 'character' field using a deterministic hash of the sample ID against `data/gold_standard/character_map.json` (which maps generic personas to specific ArcANE characters like Harry Potter, Elizabeth Bennet). 4) Map 'chosen'/'rejected' to 'ground_truth_score' (for chosen, 1 for rejected, interpolated if needed). 5) Map 'prompt' to 'scenario'. This ensures the Gold Standard is REAL, external, and reproducible.
- [ ] T009a [P] [US3] **Generate Checksum**: Generate SHA-256 checksum for `data/gold_standard/human_annotations.json`. **Output**: Write checksum to `artifacts/checksums.json` and update the manifest. Depends on T009c.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Construct and Validate Character Arc Specifications (Priority: P1) 🎯 MVP

**Goal**: Allow researchers to define and store independent Coarse and Fine psychological axes for characters.

**Independent Test**: A researcher can input a character name and receive two distinct, non-overlapping JSON objects representing the Coarse and Fine axes, verified against semantic overlap constraints.

### Tests for User Story 1 (OPTIONAL) ⚠️

- [X] T009 [P] [US1] Unit test for axis semantic overlap constraint in `tests/unit/test_axis_validation.py`. Note: This test depends on T010a/T010b (schema) and T011 (service) being implemented first; it is written first (TDD) but will fail until T010/T011 are complete.

### Implementation for User Story 1

- [ ] T011 [US1] Implement `src/services/axis_generator.py` with manual input interface for defining axes, including serialization logic to produce `data/derived/axes.jsonl` (T013). The 'manual input interface' must support TWO modes: 1) Interactive CLI prompt for local dev, and 2) Non-interactive config file loading for CI/CD. Implement `display_axis_output(coarse, fine)` in `src/cli/run_experiment.py` to print the two distinct JSON objects to the console (US-1).
- [ ] T011a [US1] Implement `src/cli/axis_input.py` with independent input validation logic: requires two separate text blocks for Coarse and Fine axes, prevents copy-paste between fields. **Depends on**: T010a, T010b, T012. **Logic**: Call T012's automated check before accepting input. If validation fails, reject input and log error.
- [ ] T012 [US1] Implement semantic validation logic in `src/services/axis_generator.py` (lexical overlap > 0.4, embedding cosine distance < 0.3) using `sentence-transformers/all-MiniLM-L6-v2`. This logic MUST be called by T011a to block invalid input.
- [ ] T012a [US1] Update `src/cli/axis_input.py` to rely on T012's automated validation result. **Remove** 'manual confirmation only' logic; the system must enforce the independence requirement programmatically. Log successful validation.
- [ ] T013 [US1] Create `data/derived/axes.jsonl` writer to store validated axis definitions.
- [ ] T014 [US1] Add CLI entry point in `src/cli/run_experiment.py` to initialize axes for a given character.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Generate Out-of-World Probes (Priority: P2)

**Goal**: Generate at least 50 unique "Out-of-World" scenario prompts per character that are semantically distant from the source text.

**Independent Test**: The system generates a batch of probes, and a sample check confirms none contain direct quotes/plot points and average cosine similarity to source text is < 0.3.

### Tests for User Story 2 (OPTIONAL) ⚠️

- [X] T015 [P] [US2] Unit test for probe regeneration loop and similarity threshold in `tests/unit/test_probe_generation.py`

### Implementation for User Story 2

- [ ] T017 [US2] Implement `src/services/probe_generator.py` with logic to generate novel scenarios based on character axes.
- [ ] T018 [US2] Implement semantic similarity check (cosine similarity < 0.3) against source text corpus in `src/services/probe_generator.py` using `sentence-transformers/all-MiniLM-L6-v2`.
- [ ] T019 [US2] Implement regeneration loop in `src/services/probe_generator.py` with explicit discard logic: **Step 1**: Generate candidate (T017). **Step 2**: Run T018 check. **Step 3**: {{claim:c_883154c1}} **Step 4**: If retry count > 150, log "Generation Limit Exceeded" and proceed with available valid probes (if >= 50) or mark character as invalid. **Depends on**: T017, T018.
- [ ] T020 [US2] Create `data/derived/probes.jsonl` writer to store validated out-of-world probes. **Depends on**: T019 (producer must finish before consumer).
- [ ] T021 [US2] Implement error handling for "Generation Limit Exceeded" in `src/services/probe_generator.py`. If valid_probes < 50 after 150 attempts, set `character_status` to 'invalid' in `data/derived/probes.jsonl` (Edge Cases, FR-002).

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Execute Hybrid Prompting and Consistency Evaluation (Priority: P3)

**Goal**: Execute the target model under three conditions, calibrate a Judge model, and perform statistical analysis.

**Independent Test**: The system processes a probe through all conditions, outputs structured results with scores, and performs a Shapiro-Wilk test to select ANOVA or Friedman.

### Tests for User Story 3 (OPTIONAL) ⚠️

- [X] T022 [P] [US3] Contract test for Judge output format and clamping in `tests/unit/test_judge_clamp.py`
- [X] T023 [P] [US3] Integration test for full experiment flow in `tests/integration/test_experiment_flow.py`

### Implementation for User Story 3

- [X] T024 [P] [US3] Implement model loading utilities in `src/models/loader.py` (CPU-quantized small language models, low-bit quantization, specifically Phi-3-mini or TinyLlama-1.1B via `llama.cpp` or low-bit `transformers` per Constitution Principle VI).
- [X] T025 [US3] Implement `src/services/judge_service.py` for LLM-based consistency scoring using a standard Likert scale, with output validation, clamping, and implementation of logic to extract and return `adherence_flag` (bool) based on LLM reasoning. The `adherence_flag` MUST be determined by the LLM's conceptual evaluation of the response against the prompt's defined phase criteria (which may include keywords), distinct from the rule-based keyword counting mechanism.
- [ ] T026 [US3] Implement `src/services/rule_based_metric.py` to calculate a composite rule-based score (1-5). **Formula**: `score = (* sentiment_score + 0.4 * coherence_score)`. **Sentiment Score**: Use **VADER** (mandatory) to calculate polarity. **Coherence Score**: Calculate entropy/perplexity check. **Note**: Keyword presence is NOT part of this formula; it is only used for the LLM Judge's adherence flag. This satisfies Spec FR-004 (keyword presence for Judge) and Plan (coherence/sentiment for rule-based).
- [ ] T032 [US3] Create `data/derived/results_raw.jsonl` writer to store raw responses and scores.
- [ ] T027 [US3] Implement Judge Calibration step in `src/services/judge_service.py` (Kappa > 0.6 against `data/gold_standard/human_annotations.json` using `sklearn.metrics.cohen_kappa_score` with quadratic weights). If Kappa <= 0.6, raise a RuntimeError and halt execution (FR-007, US-3). If the gold standard file is missing or malformed, raise a clear error. **Depends on**: T009a.
- [ ] T027b [US3] Implement `validate_against_gold_standard(results, gold_data)` in `src/analysis/stats_engine.py` to compute correlation/error metrics against `data/gold_standard/human_annotations.json` (REAL human-annotated data) and validate consistency scores against the external Gold Standard dataset to ensure the evaluation is not circular (FR-006).
- [ ] T027c [US3] Implement logic to aggregate Judge model output validation failures (scores outside a standard range), calculate the failure rate, and record it as a metric in `data/derived/judge_metrics.json` (SC-005).
- [ ] T028 [US3] Implement `src/services/experiment_runner.py` to run target model under Coarse, Fine, and Hybrid conditions. Explicitly construct "Coarse Context", "Fine Context", and "Hybrid Context" strings as per Spec definitions.
- [ ] T029 [US3] Implement timeout handling and default score assignment (0) for failed generations in `src/services/experiment_runner.py`. **Logic**: If a *single probe* times out, log the failure, assign score 0, and proceed to the *next probe*. This ensures the experiment completes within CI time limit despite individual failures.
- [ ] T029a [US3] Instrument `experiment_runner` and `stats_engine` to capture, log, and report the total wall-clock time of the full experiment run to `data/derived/timing.log`. Define a `CI_TIME_LIMIT` constant in `config.py` (default several hours). **Implementation Requirement**: If *cumulative* elapsed time > `CI_TIME_LIMIT`, the script MUST raise `SystemExit(1)` to fail the CI job immediately. This enforces the success criterion as a gate.
- [ ] T026a [US3] Implement `aggregate_consistency_scores` in `src/analysis/stats_engine.py` to combine the Judge score (T025) and rule-based score (T026) into a single 'Consistency Score' artifact. **Logic**: Read raw responses from `data/derived/results_raw.jsonl` (produced by T032). Use the scoring logic implemented in T025 and T026 to aggregate the scores. Write the final aggregated scores to `data/derived/results_final.jsonl`. **Depends on**: T032, T025, T026, T028.
- [ ] T030 [US3] Implement `check_normality(scores)` in `src/analysis/stats_engine.py` to perform Shapiro-Wilk test on the residuals of the `judge_score` field from `data/derived/results.jsonl` (ensuring raw scores are preserved) and return `is_normal` (bool). Depends on T032, T026a.
- [ ] T031 [US3] Implement `select_statistical_test(is_normal)` in `src/analysis/stats_engine.py` to return the test type ('anova' or 'friedman') based on `is_normal` from T030.
- [ ] T033 [US3] Implement `run_statistical_test(scores, test_type)` in `src/analysis/stats_engine.py` to execute the chosen statistical test (ANOVA or Friedman) and write the p-value, effect size, mean scores, and variance to `data/derived/stats_results.json` (FR-005, SC-004). Reads `test_type` from T031.
- [ ] T033b [US3] Implement logic to calculate the variance of consistency scores across the three conditions and write it to `data/derived/stats_results.json` (SC-004).
- [ ] T035 [US3] Add CLI entry point in `src/cli/run_experiment.py` to trigger the full experiment pipeline.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T036a [P] Update `specs/001-gene-regulation/quickstart.md` with new CLI flags and data format changes.
- [ ] T036b [P] Update `README.md` with new data formats and execution instructions.
- [ ] T037a Code cleanup: Refactor error handling to be consistent across all services.
- [ ] T037b Code cleanup: Refactor logging calls to use standardized format.
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