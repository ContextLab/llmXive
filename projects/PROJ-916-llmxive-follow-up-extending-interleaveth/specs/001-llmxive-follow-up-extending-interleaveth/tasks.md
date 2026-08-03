# Tasks: llmXive follow-up: extending "InterleaveThinker: Reinforcing Agentic Interleaved Generation"

**Input**: Design documents from `/specs/001-llmxive-interleave-structure-vs-modality/`
**Prerequisites**: plan.md (required), spec.md (required for user stories)

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this user story belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- Paths shown below assume single project - adjust based on plan.md structure

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001a [P] Create `src/` directory structure: `src/simulator`, `src/agents`, `src/pipeline`, `src/benchmarks`, `src/stats`, `src/utils`
- [ ] T001b [P] Create `tests/` directory structure: `tests/unit`, `tests/integration`, `tests/contract`
- [ ] T001c [P] Create `data/` directory structure: `data/raw`, `data/intermediate`, `data/simulator_validation`
- [ ] T001d [P] Create `docs/` directory structure
- [ ] T001e [P] Create `contracts/` directory structure: `contracts/scene`, `contracts/trajectory`, `contracts/stats`
- [X] T002 Initialize Python 3.11 project with `transformers`, `datasets`, `scikit-learn`, `torch`, `pyyaml`, `pytest`, `networkx` dependencies in `requirements.txt`
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools in `.pre-commit-config.yaml`
- [X] T004 [P] Implement data integrity infrastructure: Create `data/raw/checksums.txt` by downloading verified hashes from HuggingFace dataset manifests or hardcoding from spec's verified source; implement `src/utils/checksum.py` to verify downloaded shards against these hashes.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T005 [P] Create data models `SceneGraph` and `TrajectoryLog` in `src/data_models.py` conforming to `specs/001-llmxive-interleave-structure-vs-modality/contracts/scene.schema.yaml` and `specs/001-llmxive-interleave-structure-vs-modality/contracts/trajectory.schema.yaml`
- [ ] T006 [P] Setup logging infrastructure in `src/utils/logging.py` to track RAM usage (via `tracemalloc`) and execution time per step
- [ ] T007 Create `src/config.py` for environment configuration (random seeds, critic thresholds {0.7, 0.8, 0.9}, batch sizes)
- [X] T008 [P] Implement robust data loader in `src/data/loader.py` that streams Visual Genome, GQA, WISE, and RISE datasets using `datasets.load_dataset(..., streaming=True)`. The loader MUST raise `ValueError` if core datasets (WISE, RISE) are unavailable. If pre-computed image-based baselines are missing, the loader MUST issue a `UserWarning` and proceed with Single-Pass Text Baseline comparison only (no silent fallback for core data).

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Construct Text-Based Scene Simulator (Priority: P1) 🎯 MVP

**Goal**: Implement a deterministic text-based simulator that converts image prompts into structured JSON scene descriptions with controllable "Noisy Mode" to simulate the grounding gap.

**Independent Test**: The simulator can be invoked with a prompt string and a mode flag ("Perfect" or "Noisy"), returning a valid JSON object within 500ms containing keys for `objects`, `relationships`, and `attributes`, with no external image generation API calls made.

### Implementation for User Story 1

- [ ] T015 [P] [US1] Implement `src/benchmarks/loader.py` to fetch Human-Annotated Scene Graphs from WISE and RISE (streaming). The loader MUST strictly fail (raise `FileNotFoundError`) if WISE/RISE are unavailable; no fallback to VG/GQA for the primary experimental run. Ensure output conforms to the `SceneGraph` model defined in T005.
- [ ] T012 [P] [US1] Implement `src/simulator/parser.py` to convert text captions into `SceneDescription` JSON objects (Perfect Mode)
- [ ] T013 [P] [US1] Implement `src/simulator/noise_injector.py` to randomly swap relationships or remove objects to simulate semantic uncertainty (Noisy Mode)
- [ ] T014 [US1] Implement `src/simulator/simulator.py` orchestration logic to switch between Perfect/Noisy modes based on config
- [ ] T016a [P] [US1] Implement `src/stats/simulator_metrics.py` to calculate `simulator_error_rate` (Graph Edit Distance) against Human-Annotated Scene Graphs
- [ ] T016b [P] [US1] Implement verification logic in `src/stats/simulator_metrics.py` to assert that the injected noise in Noisy Mode falls within the 5-15% target range (SC-006), raising `AssertionError` if out of bounds.
- [ ] T017 [P] [US1] Implement `src/simulator/validator.py` to detect ambiguous spatial relationships and flag samples for exclusion
- [ ] T018a [US1] Implement `src/stats/generator_metrics.py` to explicitly calculate and report the "Generator Error Rate" (deviation between generated JSON and intended prompt) as a separate variable, distinct from `simulator_error_rate` (FR-010)
- [ ] T018b [P] [US1] Implement deterministic seeding in `src/simulator/noise_injector.py` to guarantee reproducibility of the "grounding gap" simulation across runs (T042).

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T009 [P] [US1] Unit test for `src/simulator/parser.py` verifying deterministic JSON output from known prompts in `tests/unit/test_simulator_parser.py`
- [ ] T010 [P] [US1] Unit test for `src/simulator/noise_injector.py` verifying target error rate (5-15%) is achieved in `tests/unit/test_simulator_noise.py`
- [ ] T011 [US1] Integration test for `src/simulator/simulator.py` validating `simulator_error_rate` against ground truth in `data/simulator_validation/` in `tests/integration/test_simulator_validation.py`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Execute CPU-Tractable Agentic Loop (Priority: P2)

**Goal**: Execute the full agentic pipeline (Planner → Generator → Critic → Planner) using a lightweight LLM on CPU, evaluating JSON scene descriptions.

**Independent Test**: The pipeline processes benchmark samples from WISE/RISE, completes the full planning-generating-critic loop for each, and outputs a JSON log of reasoning scores (F1-score) within the 6-hour CI time limit on a CPU-only runner, with RAM usage ≤ 7GB.

### Implementation for User Story 2

- [ ] T022 [P] [US2] Implement `src/agents/critic.py` and define the interface contract for Planner/Generator inputs/outputs in `src/agents/interfaces.py`. The Critic MUST evaluate generated JSON against the prompt and ground truth, returning a critique and revised intent.
- [ ] T023 [US2] Implement `src/agents/planner.py` to generate intent and next steps based on Critic feedback (depends on T022 interface)
- [ ] T024 [US2] Implement `src/agents/generator.py` to reconstruct `SceneDescription` JSON from prompt using a lightweight LLM (Llama-3-8B/Mistral-7B default precision) (depends on T022 interface)
- [ ] T029 [P] [US2] Implement "warm-up" logic in `src/pipeline/orchestrator.py` to load the LLM model once into memory before the benchmark loop starts, preventing repeated load times from skewing the 6-hour runtime budget (T043).
- [ ] T030 [P] [US2] Implement "timeout" mechanism in `src/agents/generator.py` to abort generation if a single sample exceeds a configurable time limit (e.g., 30s), preventing a single outlier from stalling the entire 6-hour CI job (T045).
- [ ] T025 [US2] Implement `src/pipeline/orchestrator.py` to manage the Planner → Generator → Critic → Planner loop with configurable Critic threshold sensitivity {0.7, 0.8, 0.9}
- [ ] T026 [US2] Implement memory management in `src/pipeline/orchestrator.py` using `tracemalloc` to monitor RAM. Enforce a hard limit of ~7GB (aligned with CI runner) to prevent OOM errors, while logging the peak usage to measure against the 16GB spec success criterion (SC-005).
- [ ] T027 [US2] Implement `src/metrics/reasoning_score.py` to calculate F1-score (or Graph Edit Distance) between Generator output and Human-Annotated Scene Graphs (depends on T015 output schema)
- [ ] T028 [US2] Add logging for `TrajectoryLog` in `src/pipeline/logger.py` to record intermediate states and critiques

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T019 [P] [US2] Unit test for `src/agents/generator.py` verifying JSON output format in `tests/unit/test_agent_generator.py`
- [ ] T020 [P] [US2] Unit test for `src/agents/critic.py` verifying critique generation and threshold logic in `tests/unit/test_agent_critic.py`
- [ ] T021 [US2] Integration test for the full agentic loop in `tests/integration/test_agentic_loop.py`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Perform Statistical Comparison and Ablation (Priority: P3)

**Goal**: Perform statistical analysis (paired t-test/Wilcoxon) and ablation study (Full Loop vs. No-Critic) to quantify the value of structural decomposition.

**Independent Test**: The analysis script outputs a report containing p-values and effect sizes (Cohen's d) for the difference between text-only and baseline scores, and a delta metric comparing "Full Loop" vs. "No-Critic Loop" performance, all computed on CPU.

### Implementation for User Story 3

- [ ] T031 [P] [US3] Implement `src/stats/analyzer.py` to perform paired t-tests and Wilcoxon signed-rank tests on reasoning scores. Dependencies: T016 (simulator metrics) AND T027 (ReasoningScore).
- [ ] T032 [P] [US3] Implement `src/stats/analyzer.py` to calculate effect sizes (Cohen's d) and confidence intervals
- [ ] T033 [US3] Implement `src/pipeline/ablation_runner.py` to execute the "No-Critic" (Single-Pass) baseline run
- [ ] T034 [US3] Implement `src/stats/report_generator.py` to generate `statistical_significance_report.md` with p-values, effect sizes, and ablation delta metrics. The report MUST handle the case where pre-computed image-based results are unavailable by strictly falling back to Single-Pass Text Baseline comparison as defined in the Plan.
- [ ] T036 [US3] Add logic to `src/stats/report_generator.py` to calculate and log the statistical power (sample size N) alongside p-values to validate the "exploratory" vs "definitive" nature of the findings as per Assumption 4 (T044).

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T029 [P] [US3] Unit test for `src/stats/analyzer.py` verifying statistical test calculations in `tests/unit/test_stats_analyzer.py`
- [ ] T030 [US3] Integration test for the full statistical reporting pipeline in `tests/integration/test_statistical_report.py` (requires T016 output data)

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T036 [P] Update `README.md` and `docs/quickstart.md` with exact setup instructions and execution examples
- [ ] T037a [P] Refactor code: Extract common parsing logic into `src/utils/parser.py`
- [ ] T037b [P] Refactor code: Consolidate logging calls into `src/utils/logging.py`
- [ ] T038 Optimize pipeline performance to ensure total runtime < 6 hours and RAM usage < 16GB on CI; measure and document optimization gains
- [ ] T039 [P] Add additional unit tests in `tests/unit/` for edge cases identified during integration
- [ ] T040 Run `quickstart.md` validation to ensure reproducibility
- [ ] T041 Verify `run_experiment.py` entry point works end-to-end on CI

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1's simulator output and data loader
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US2's pipeline output

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
# Launch all models for User Story 1 together:
Task: "Create [Entity1] model in src/models/[entity1].py"
Task: "Create [Entity2] model in src/models/[entity2].py"

# Launch all tests for User Story 1 together (after implementation):
Task: "Contract test for [endpoint] in tests/contract/test_[name].py"
Task: "Integration test for [user journey] in tests/integration/test_[name].py"
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
- **Data Integrity**: All data loaders MUST fail loudly on missing core real data (WISE, RISE); graceful fallback to text baseline is allowed only when pre-computed image-based results are unavailable.
- **Compute Constraints**: Ensure all LLM inference tasks are configured for CPU-only execution with memory limits enforced (a bounded allocation for CI).
- **Revision Concerns**: All revision concerns (T042-T046) have been integrated into their respective phases as T018b, T029, T030, T036, and T004b.