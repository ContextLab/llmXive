# Tasks: llmXive follow-up: extending "Code2LoRA: Hypernetwork-Generated Adapters for Code Language Models under Software Evolution"

**Input**: Design documents from `/specs/001-ast-based-adapter-generation/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `code/`, `tests/` at repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- Paths shown below assume single project - adjusted based on plan.md structure

---

## Phase 0: Alignment & Fixes (Critical Pre-requisites)

**Purpose**: Resolve contradictions between Plan and Spec, and fix unimplementable tasks before Phase 1.

- [X] T000 [P] **CRITICAL**: Resolve Plan/Spec Contradiction (F001). **NOTE: Plan.md states 'Paired t-test' but Spec SC-005 mandates 'Wilcoxon signed-rank test'.** Update `code/evaluation/stats.py` (when implemented) to use **Wilcoxon signed-rank test** as the primary method per Spec SC-005, overriding the Plan's instruction. Document this override and the contradiction in `code/evaluation/stats.py` comments.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project structure per `plan.md` directory layout in `projects/PROJ-910-llmxive-follow-up-extending-code2lora-hy/` including specific files: `code/__init__.py`, `tests/__init__.py`, `data/raw/.gitkeep`, `data/processed/.gitkeep`, `data/adapters/.gitkeep`, `requirements.txt`, `pyproject.toml`, `.github/workflows/ci.yml`.
- [X] T002 Initialize Python project with `requirements.txt` pinning `transformers`, `peft`, `torch`, `scikit-learn`, `networkx`, `pytest`, `pytest-cov`.
- [X] T003 [P] Configure `ruff` for linting and `black` for formatting in `pyproject.toml`.
- [X] T004 [P] Setup CI workflow file `.github/workflows/ci.yml` targeting GitHub Actions free tier with limited computational resources.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T005 [P] Implement `code/utils/config.py` to load random seeds, base model paths (defaulting to 'TinyLlama-1.1B-Chat-hf' if not specified), and RepoPeftBench paths. **Must be completed before T015 can run.**
- [X] T006 [P] **SETUP ONLY**: Implement `code/utils/logging.py` to define the warning handler for FR-007. **Does not implement skip logic.** This task is a prerequisite for T016 but does not provide the functional behavior of FR-007 until T016 is merged.
- [X] T007 Create `code/__init__.py` and empty module stubs for `code/feature_extractor/__init__.py`, `code/hypernetwork/__init__.py`, `code/evaluation/__init__.py`, `code/utils/__init__.py`.
- [ ] T008 [P] Setup `data/raw/`, `data/processed/`, `data/adapters/` directories with `.gitkeep`.
- [ ] T009 [P] Implement `code/main.py` CLI entry point with `argparse` for `generate`, `evaluate`, `sensitivity` commands; verify execution via `python code/main.py --help` listing all three commands.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Generate Adapter via AST Features (Priority: P1) 🎯 MVP

**Goal**: Generate a repository-specific LoRA adapter using only static AST features and a lightweight MLP, running on CPU‑only CI.

**Independent Test**: The system processes a sample repo, generates an adapter file, and verifies it loads without GPU.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation

- [ ] T010 [US1] Contract test for `ast_parser.py` in `tests/unit/test_ast_parser.py`: Implement `test_parse_valid_file` (valid Python file input) and `test_parse_invalid_syntax` (malformed syntax string input). *(Removed `[P]` to avoid running before code exists)*
- [ ] T011 [US1] Integration test for end‑to‑end adapter generation on `data/raw/sample_repo` in `tests/integration/test_adapter_generation.py`: Assert `data/adapters/sample_adapter.safetensors` exists and loads successfully. *(Removed `[P]`)* <!-- ATOMIZE: requested -->

### Implementation for User Story 1

- [X] T012 [P] [US1] Implement `code/feature_extractor/ast_parser.py` to extract cyclomatic complexity, depth of inheritance, and token histograms using `ast` and `tokenize` (FR-001).
- [X] T013 [P] [US1] Implement `code/feature_extractor/graph_builder.py` to compute import graph centrality using `networkx` (FR-001).
- [X] T014 [US1] Implement `code/hypernetwork/mlp_projection.py`: Define a small MLP (ReLU) mapping AST feature vectors to the original embedding dimension. **Derive `input_dim` from `config.feature_vector_size` and `output_dim` from `config.hidden_size` (or `embedding_dim`) loaded from the base model config.** Verify model forward pass returns tensor of shape (batch, embedding_dim).
- [X] T015 [US1] Implement `code/hypernetwork/adapter_generator.py`: Load frozen base model **and preserve the original GRU‑based hypernetwork weights** (FR-003), train **ONLY** the new MLP projection layer, and output a `.safetensors` adapter (FR-003). **Depends on configuration from T005.**
- [~] T016 [US1] **FUNCTIONAL IMPLEMENTATION**: Implement the control-flow logic in `ast_parser.py` to skip malformed files, log warnings using the handler from T006, and **continue processing** (FR-007). **This task is the functional prerequisite for FR-007; T006 alone is insufficient.**
- [~] T017 [US1] Add memory check in `adapter_generator.py` to abort if RAM > **7 GB** and log specific error (FR-008).
- [~] T018 [US1] Add checkpoint validation in `adapter_generator.py` to abort on incompatible base models (FR-009).

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Evaluate Adapter Performance on Assertion Tasks (Priority: P2)

**Goal**: Evaluate the generated AST‑based adapter against the RepoPeftBench Python subset and compare with neural baseline.

**Independent Test**: The system loads an adapter, runs RepoPeftBench tasks, and outputs exact‑match scores.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T019 [P] [US2] Contract test for `runner.py` scoring logic on a mock assertion task in `tests/unit/test_evaluation_runner.py`.
- [X] T020 [P] [US2] Integration test for full evaluation pipeline on a subset of RepoPeftBench in `tests/integration/test_evaluation.py`.

### Implementation for User Story 2

- [X] T024 [P] [US2] Create `code/evaluation/baseline_loader.py` to load the original Code2LoRA neural‑encoder adapter for comparison (produces artifact required by T021). *(Retained for convenience; does not duplicate functionality of existing loaders.)*
- [~] T021 [US2] Implement `code/evaluation/runner.py` to load RepoPeftBench data, apply the **AST‑based** adapter, and compute exact‑match scores. Output scores to `data/results/ast_scores.csv`. **(Note: This task does NOT record generation latency; that is handled by T040/T049a).**
- [ ] T022 [US2] Instrument the evaluation runner to measure inference latency per task in milliseconds, saving results to `data/results/latency.csv` with columns `task_id, latency_ms`. (Addresses FR-004.)
- [~] T023 [US2] Implement failure‑mode classification (`'Syntax Error'`, `'Semantic Mismatch'`, `'Timeout'`) for complex tasks; verify logging for a mock `SyntaxError`.
- [X] T025 [US2] Implement `code/evaluation/comparison_report.py` to generate a paired comparison report (AST vs Neural) with performance delta (US‑2 Scenario 2).
- [~] T026 [US2] Implement `code/evaluation/stats.py` to **first perform a Wilcoxon signed-rank test** (per SC-005 and T000) on the two score lists; if normality fails (not applicable to Wilcoxon), fall back to t-test as secondary. Accepts two CSVs (`ast_scores.csv`, `neural_scores.csv`), outputs `data/results/stats.json` containing `p_value`, `statistic`, and `test_used`. Includes verification step asserting `p_value < 0.05` on mock significant data.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Perform Sensitivity Analysis on Feature Complexity (Priority: P3)

**Goal**: Determine the minimum AST feature set required to maintain >80 % of baseline accuracy.

**Independent Test**: The system runs evaluation with different feature subsets and produces a sensitivity curve.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T027 [P] [US3] Contract test for `sensitivity.py` feature subset logic in `tests/unit/test_sensitivity.py`.
- [~] T028 [P] [US3] Integration test for sensitivity analysis loop in `tests/integration/test_sensitivity_analysis.py`.

### Implementation for User Story 3

- [X] T029 [P] [US3] Implement `code/evaluation/sensitivity.py` to define feature subsets (e.g., token counts only, cyclomatic only, full AST) (FR‑005).
- [~] T030 [US3] **BLOCKING PREREQUISITE**: Implement the sensitivity loop in `sensitivity.py` that, for each subset, calls the adapter generator (T015) and evaluator (T021/T022) to obtain scores. **T021 and T022 are BLOCKING PREREQUISITES; Phase 5 cannot begin until Phase 4 evaluation tasks are complete.** <!-- FAILED: unspecified -->
- [ ] T031a [US3] **NEW**: Implement logic to extract the **baseline accuracy score** from the neural evaluation results (T021/T024) and save it to `data/results/baseline_score.json`. **Must be completed before T032.**
- [~] T031 [US3] Within `sensitivity.py`, calculate the drop in exact‑match score when specific features are removed (US‑3 Scenario 3).
- [~] T032 [US3] **Depends on T031a**: Identify the minimal feature set meeting a threshold **calculated dynamically as >80% of the baseline accuracy score** (derived from T031a).
- [ ] T033 [US3] Generate a **CSV summary** `data/results/sensitivity_summary.csv` with columns `feature_set, accuracy, meets_threshold`. The research question investigates the sensitivity of model accuracy to different feature sets. The method involves training models across various feature combinations and evaluating performance against a predefined accuracy threshold. References: (Author et al.,).. Verify the file exists and is non‑empty. *(No visual plot is produced, respecting the spec.)*

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Resource Enforcement & Validation (Cross‑Cutting)

**Purpose**: Ensure FR‑006 compliance (2 cores, 7 GB RAM) and SC‑001/SC‑004 measurement requirements.

**Conflict Avoidance**: Tasks in this phase target distinct files to prevent merge conflicts. Do not modify the same file across parallel tasks. T039 -> `cpu_monitor.py`, T040 -> `latency_monitor.py`, T041/T043 -> `memory_monitor.py`, T048 -> `cpu_monitor.py` (audit), T050 -> `resource_summary.csv`.

- [X] T039 [P] Implement `code/utils/cpu_monitor.py` to enforce a **2-core limit** via `taskset` (CPU affinity) and log CPU usage; verify that the process is restricted to a bounded subset of cores.
- [~] T040 [P] Implement `code/utils/latency_monitor.py` to **measure adapter generation latency** (during T015 execution) and compare against the original Code2LoRA neural-encoder generation time on the same hardware (SC‑001). Output comparison report to `data/results/generation_latency_comparison.json`.
- [~] T041 [P] Implement `code/utils/memory_monitor.py` to measure **peak RSS memory usage** via the `resource` module at each pipeline step and log to `data/results/memory_log.csv` (SC‑004).
- [~] T042 [P] Add a CI job that runs the full pipeline on sample data to verify the **timeouts** and resource limits (replaces previous T036 verification task).
- [X] T043 [P] Implement RAM‑limit enforcement in `code/utils/memory_monitor.py` to abort gracefully if memory usage exceeds **7 GB** (FR-006, FR-008).
- [~] T047 [P] Add CI step that executes the pipeline with the timeout mechanism (implemented in T036) and asserts the job finishes within the specified time limit.
- [X] T048 [P] (Optional) Add a lightweight script in `code/utils/cpu_monitor.py` to verify that the process is limited to **2 CPU cores** at runtime (e.g., using `psutil`), logging the result for audit purposes.
- [ ] T049a [US2] **NEW**: Measure baseline neural-encoder generation latency (run the baseline loader T024 and measure time) and save to `data/results/baseline_generation_latency.json`. **Must be completed before T049b.**
- [ ] T049b [US2] **NEW**: Compute the latency reduction ratio (AST generation latency from T040 / baseline generation latency from T049a) and store a comparison report in `data/results/generation_latency_comparison.json`. Ensure the reduction is ≥ 10× as required by SC‑001. **Depends on T049a.**
- [ ] T050 [P] Aggregate peak memory usage logs from `data/results/memory_log.csv`, compute total runtime per stage, and write a summary `data/results/resource_summary.csv`. Verify that peak RAM stays ≤ 7 GB and total runtime ≤ 6 h.
- [ ] T051 [P] Add unit tests for `graph_builder.py` centrality algorithms in `tests/unit/test_graph_builder.py`.
- [ ] T052 [P] Create `scripts/validate_quickstart.sh` that executes the commands in `quickstart.md` and asserts successful exit codes.
- [ ] T053 [P] Polish documentation updates in `README.md` and `specs/001-ast-based-adapter-generation/quickstart.md`.

---

## Phase 7: Data Acquisition & Reproducibility (Critical Fix)

**Purpose**: Ensure real data availability and prevent fabrication (Rule: Real data + real results only).

- [ ] T054 [P] Implement `code/data/download_repopeftbench.py` to fetch the RepoPeftBench Python subset from the official HuggingFace dataset (`datasets.load_dataset("repo-peft-bench", "python")`) or Zenodo mirror, verifying checksums before writing to `data/raw/`.
- [ ] T055 [P] Implement `code/data/download_sample_repo.py` to fetch a small, real Python repository (e.g., `requests` or `flask` subset) from GitHub via `git clone` or `requests` API for local AST parsing tests, ensuring no synthetic/fake code is used.
- [ ] T056 [P] Add a validation step in `code/main.py` that checks for the existence of `data/raw/` datasets before running `generate` or `evaluate` commands, failing fast with a clear error message if data is missing.

---

## Phase 8: Polish & Cross‑Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T034 [P] Documentation updates in `README.md` and `specs/001-ast-based-adapter-generation/quickstart.md`.
- [ ] T035 Code cleanup and refactoring of `code/` modules for readability.
- [ ] T036 [P] Implement a **timeout mechanism** in `code/main.py` that terminates the entire pipeline after a predetermined time limit, raising a controlled exception.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **Data Acquisition (Phase 7)**: Can run in parallel with Setup/Foundational but **MUST complete before** any Evaluation (US2) or Sensitivity (US3) tasks.
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable. **Requires data from Phase 7.**
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable. **Requires data from Phase 7.**

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Data Acquisition (Phase 7) tasks marked [P] can run in parallel with Setup/Foundational
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
3. Complete Phase 7: Data Acquisition (Fetch real RepoPeftBench data)
4. Complete Phase 3: User Story 1
5. **STOP and VALIDATE**: Test User Story 1 independently
6. Deploy/demo if ready

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
- **Critical**: All data tasks must use real, reachable URLs or package fetchers. No synthetic data generation.
- **Critical**: T043 uses 7 GB limit. T049a/b handles baseline latency. T031a provides baseline score for T032. T016 handles skip logic. T021 does NOT record generation latency.