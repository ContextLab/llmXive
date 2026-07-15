# Tasks: Evaluating the Impact of Prompt Complexity on LLM Code Generation Performance

**Input**: Design documents from `/specs/001-prompt-complexity-evaluation/`
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

## Phase 0: Pre-Implementation (Spec Amendments)

**Purpose**: Resolve critical contradictions between Spec and Plan before implementation begins.
**⚠️ CRITICAL GATE**: This phase MUST complete successfully before Phase 1 (Setup) begins. **Verification Step**: After T001, verify `spec.md` content matches `plan.md` requirements (FR-005: LMM, FR-012: prompt token count). If verification fails, halt execution.

- [ ] T001 [P] **Apply Spec Amendments**: Create and apply a unified diff patch `spec_amendments.patch` to update `spec.md` with the following changes: <!-- FAILED: unspecified --> <!-- FAILED: unspecified --> <!-- FAILED: unspecified -->
 1. Update FR-005 to mandate **Linear Mixed Models (LMM)** instead of ANOVA/Kruskal-Wallis (aligning with Plan.md).
 2. Update FR-012 to mandate **'prompt token count'** as the covariate for readability metrics instead of 'code length' (aligning with Plan.md).
 3. Update US-1 Acceptance Scenario 3 and US-3 Acceptance Scenario 4 to link structural element count failures to 'manual review' flagging.
 4. Update Assumptions to acknowledge 'State Transition Proxy' limitation.
 Execute `git apply spec_amendments.patch` to update `spec.md`. This task is executable and atomic.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T002 Create project structure per implementation plan: Create directories `code/`, `tests/`, `data/raw/`, `data/processed/`, `data/results/`, `state/` at repository root.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T003 Initialize Python 3.11 project with dependencies: `datasets`, `tiktoken`, `scikit-learn`, `statsmodels`, `pandas`, `ruff`, `requests`, `pyyaml` in `requirements.txt`
- [X] T004 [P] Configure linting and formatting tools (ruff) and pytest in `pyproject.toml`
- [X] T005 Setup data directory structure `data/raw/`, `data/processed/`, `data/results/` and implement `code/utils/hash_artifacts.py` for SHA-256 checksumming
- [X] T006 [P] Implement configuration management in `code/config.py` with fixed random seeds, paths, and API keys
- [ ] T007 [P] Setup error handling and logging infrastructure in `code/utils/logger.py`
- [X] T008 Create base data models (Pydantic) for `HumanEvalProblem`, `PromptVariant`, `GeneratedCode`, `AnalysisResult` in `code/models/data_models.py`
- [ ] T009 Implement artifact versioning utility to update `state/projects/PROJ-527-evaluating-the-impact-of-prompt-complexi.yaml` after data generation, deriving the filename from the project ID.
- [X] T010 [P] Setup CPU-tractable LLM client wrapper in `code/llm/client.py` supporting HuggingFace Inference API with fallback to local GGUF (CPU only, no CUDA). This task implements the HTTP/GGUF client interface only.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Generate and Evaluate Code from Multiple Prompt Complexity Levels (Priority: P1) 🎯 MVP

**Goal**: Generate multiple distinct prompt variants (simple, moderate, complex, very complex, degenerate) per HumanEval problem, query LLM, and capture code with metadata.

**Independent Test**: Can be fully tested by generating prompts for a single HumanEval problem, querying the LLM, and verifying that 5 distinct code samples are captured with correct metadata tags.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T011 [P] [US1] Contract test for prompt generation logic in `tests/unit/test_prompt_gen.py`: Implement `test_generates_5_variants` using a single HumanEval problem JSON as input, asserting `len(variants) == 5` and `all(label in ['simple', 'moderate', 'complex', 'very_complex', 'degenerate'] for label in labels)`.
- [X] T012 [P] [US1] Integration test for LLM query and capture in `tests/integration/test_llm_capture.py`: Implement `test_query_and_capture` using a mocked LLM response, asserting that 5 distinct code samples are captured with correct metadata tags (complexity_label, token_count, structural_element_count).

### Implementation for User Story 1

- [X] T016 [US1] **Fetch HumanEval Dataset**: Implement `code/data/fetcher.py` to download HumanEval dataset from `https://huggingface.co/datasets/openai/human-eval` with checksum verification. **(MUST PRECEDE T013-T015)**
- [X] T013 [P] [US1] Implement `code/prompts/generator.py` to create multiple complexity variants based on structural composition (problem only, +1 example, +constraints, +multi-step, +redundant)
- [X] T014 [P] [US1] Implement `code/prompts/parser.py` to dynamically count structural elements (examples, constraints, instructions) and calculate structural complexity scores
- [X] T015 [US1] Implement `code/prompts/tokenizer.py` using `tiktoken cl100k_base` to count prompt tokens and validate thresholds (simple ≤50, moderate 51-150, etc.)
- [X] T017 [US1] Implement `code/llm/orchestrator.py` to query LLM with multiple variants per problem, utilizing the T010 wrapper in `code/llm/client.py`, capturing code, token counts, and structural metadata.
- [~] T018 [US1] Implement `code/data/storage.py` to write generated code and metadata to `data/processed/prompt_variants.parquet`
- [ ] T019 [US1] Add logic to flag samples where 'degenerate' prompt token delta < 100 tokens vs 'very complex' for manual review (non-fatal), appending flagged sample IDs to `data/results/manual_review_queue.csv`. **(Note: This CSV is an internal flagging artifact; the spec requires flagging, not a full workflow).**
- [ ] T020 [US1] Implement correlation check between token count and structural element count to diagnose collinearity (FR-013) and **write the correlation coefficient to `data/results/analysis_summary.csv`**.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Execute Unit Tests and Collect Pass/Fail Rates (Priority: P2)

**Goal**: Execute generated code against HumanEval unit tests, record outcomes, and aggregate pass rates by complexity level.

**Independent Test**: Can be fully tested by running 5 generated code samples against HumanEval unit tests and verifying pass/fail counts are recorded per complexity level.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T021 [P] [US2] Contract test for test runner timeout handling in `tests/unit/test_execution_runner.py`
- [X] T022 [P] [US2] Integration test for full execution pipeline in `tests/integration/test_execution_pipeline.py`

### Implementation for User Story 2

- [X] T023 [P] [US2] Implement `code/execution/runner.py` to execute generated code with a configurable timeout per test case using `subprocess` or `pytest` isolation.
- [~] T024 [US2] Implement exception handling in `runner.py` to mark samples as failed on syntax errors or runtime exceptions, logging error types.
- [~] T025 [US2] Implement timeout handling in `runner.py` to mark problems as failed if execution exceeds a predefined time threshold.
- [X] T026 [US2] Implement `code/execution/static_analysis.py` to run `ruff` on generated code and extract cyclomatic complexity, lines of code, and indentation consistency.
- [~] T027 [P] [US2] **Document Validation Sources**: Implement documentation of validation sources (McCabe, standard literature) for the readability metrics extracted in T026, satisfying FR-008's requirement for citable validation. Add comments in `static_analysis.py` and entries in `research.md`.
- [ ] T028 [US2] Implement aggregation logic in `code/analysis/aggregator.py` to calculate pass rates per complexity level (pass count / total count).
- [ ] T029 [US2] Implement security vulnerability flagging in `static_analysis.py` (e.g., hardcoded credentials, eval usage) to mark samples for manual review without failing the test.
- [ ] T030 [US2] Write execution results to `data/results/execution_outcomes.csv` with pass/fail counts, exception types, and static analysis scores.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Perform Statistical Analysis and Visualize Complexity-Performance Curves (Priority: P3)

**Goal**: Perform LMM/ANOVA analysis, apply corrections, generate plots, and validate robustness.

**Independent Test**: Can be fully tested by running statistical analysis on aggregated pass rates and readability scores, verifying that effect sizes and p-values are computed with family-wise error correction applied.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T031 [P] [US3] Contract test for LMM model fitting in `tests/unit/test_stats_models.py`
- [ ] T032 [P] [US3] Integration test for sensitivity analysis in `tests/integration/test_sensitivity_analysis.py`

### Implementation for User Story 3

- [ ] T033 [US3] Implement `code/analysis/stats.py` with **Linear Mixed Model (LMM)** using `statsmodels` to handle nested structure (5 variants per problem) with random intercepts for problem difficulty, as updated in spec.md FR-005 via Task T001 and Plan.md. **(Depends on Phase 3 data; NOT [P])**
- [ ] T034 [US3] Implement multiple-comparison correction in `stats.py` using Bonferroni or Holm-Bonferroni with adjusted significance threshold (α ≤ 0.05 / number of tests).
- [ ] T035 [US3] Implement covariate adjustment in LMM to control for **prompt token count** (as updated in spec.md FR-012 via Task T001 and Plan.md) when evaluating readability metrics, replacing the original 'code length' requirement. **(Depends on Phase 3 data)**
- [ ] T036 [US3] Implement sensitivity analysis in `stats.py` to re-bin data using shifted thresholds (±10 tokens) and report variance in pass rates (FR-010).
- [ ] T037 [US3] Implement `code/analysis/viz.py` to generate complexity vs. performance curves with inflection points identified (peak performance and diminishing returns).
- [ ] T038 [US3] Implement effect size calculation (Cohen's d, eta-squared) with standard interpretation thresholds for small, medium, and large effects.
- [ ] T039 [US3] Implement structural redundancy verification in `stats.py` to confirm 'degenerate' prompts have higher structural element counts than 'very complex' prompts, and explicitly flag failures for manual review per updated spec.md US-1/US-3 criteria.
- [ ] T040 [US3] Write final statistical results to `data/results/analysis_summary.csv` including test statistics, p-values, effect sizes, corrected thresholds, AND the correlation coefficient from FR-013 (T020).
- [ ] T041 [US3] **Report Power Limitations**: Implement reporting of sample-size limitations and power analysis caveats in `data/results/analysis_summary.csv` and `research.md` as required by Spec Assumptions.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and address specific reviewer concerns.

- [ ] T042 [P] [Research Review] Implement 'State Transition Proxy' metrics in `code/prompts/generator.py` as a *diagnostic* metric (not primary requirement) to measure dependency chain depth per alan-turing-simulated review. **(Diagnostic only, no FR/SC requirement)**
- [ ] T043 [P] Documentation updates in `docs/research.md` explicitly framing findings as associational and noting the "state transition" limitation.
- [ ] T044 Code cleanup and refactoring to ensure modularity: Reduce cyclomatic complexity of `runner.py` to < 10 and refactor `code/execution/runner.py` and `code/analysis/stats.py` to separate concerns.
- [ ] T045 Performance optimization to ensure full pipeline runs within **≤6 hours** on CPU (subset if necessary): Profile `main.py` and implement caching for LLM queries in `code/llm/client.py` to reduce runtime to **≤6 hours**.
- [ ] T046 [P] Additional unit tests for edge cases (syntax errors, timeouts, empty prompts) in `tests/unit/`.
- [ ] T047 Run `quickstart.md` validation and verify checksums in `state/projects/...yaml`, generating `validation_report.md` with pass/fail status for each checksum.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Pre-Implementation (Phase 0)**: No dependencies - MUST complete first.
- **Setup (Phase 1)**: Depends on Pre-Completion of Phase 0.
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories.
 - **CRITICAL**: Tasks T001 (Spec Amendments) MUST complete before Phase 5 tasks T033-T041 to resolve spec conflicts.
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Depends on T017/T018 (Code generation and storage) - Cannot run tests without generated code
- **User Story 3 (P3)**: Depends on T030 (Execution results) - Cannot analyze without pass/fail rates

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
Task: "Contract test for prompt generation logic in tests/unit/test_prompt_gen.py"
Task: "Integration test for LLM query and capture in tests/integration/test_llm_capture.py"

# Launch all models for User Story 1 together:
Task: "Create base data models in code/models/data_models.py"
Task: "Implement configuration management in code/config.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 0: Pre-Implementation (Spec Amendments)
2. Complete Phase 1: Setup
3. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
4. Complete Phase 3: User Story 1
5. **STOP and VALIDATE**: Test User Story 1 independently (generate prompts, query LLM, verify metadata)
6. Deploy/demo if ready

### Incremental Delivery

1. Complete Phase 0 + Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Phase 0 (Spec Amendments) together
2. Team completes Setup + Foundational together
3. Once Foundational is done:
 - Developer A: User Story 1 (Prompt Gen & LLM)
 - Developer B: User Story 2 (Execution & Testing)
 - Developer C: User Story 3 (Analysis & Viz)
4. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Reviewer Note**: Tasks T042 and T043 specifically address the "state transition" and "dependency depth" concerns raised by alan-turing-simulated regarding token length vs. internal state representation.
- **Spec Amendment Note**: Task T001 is a critical pre-requisite that amends the spec to align with the plan's methodological improvements (LMM and token covariate) before implementation begins.
- **Dependency Note**: T016 (Fetch HumanEval) MUST precede T013-T015 (Prompt Generation) to provide input data.
- **Constraint Note**: T045 targets ≤6 hours runtime to match spec/plan constraints.