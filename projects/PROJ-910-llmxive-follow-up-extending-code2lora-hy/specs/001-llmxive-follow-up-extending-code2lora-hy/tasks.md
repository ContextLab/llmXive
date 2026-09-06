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

- [X] T000 [P] **CRITICAL**: Resolve Plan/Spec Contradiction (F001). **NOTE: Plan.md originally stated 'Paired t-test' but Spec SC-005 mandates 'Wilcoxon signed-rank test'.** Update `plan.md` to explicitly align with Spec SC-005 (Wilcoxon) by amending the Plan text to reflect the Wilcoxon test as the primary method. Then, implement `code/evaluation/stats.py` to use **Wilcoxon signed-rank test** as the primary method. Document the Plan amendment and the implementation choice in `code/evaluation/stats.py` comments.

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
- [X] T006 [P] **SETUP ONLY**: Implement `code/utils/logging.py` to define the **exact interface** for `log_warning(message: str, filename: str, error: str) -> None`. This function must log to stderr with a specific format: `WARNING [filename]: {error}`. **This task is a stub/interface definition only; it does not implement skip logic.** The functional behavior of FR-007 (skip and continue) is implemented in T016. This task is a prerequisite for T016.
- [X] T007 Create `code/__init__.py` and empty module stubs for `code/feature_extractor/__init__.py`, `code/hypernetwork/__init__.py`, `code/evaluation/__init__.py`, `code/utils/__init__.py`.
- [X] T008 [P] Setup `data/raw/`, `data/processed/`, `data/adapters/` directories with `.gitkeep`.
- [X] T009 [P] Implement `code/main.py` CLI entry point with `argparse` for `generate`, `evaluate`, `sensitivity` commands; verify execution via `python code/main.py --help` listing all three commands.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Generate Adapter via AST Features (Priority: P1) 🎯 MVP

**Goal**: Generate a repository-specific LoRA adapter using only static AST features and a lightweight MLP, running on CPU‑only CI.

**Independent Test**: The system processes a sample repo, generates an adapter file, and verifies it loads without GPU. [UNRESOLVED-CLAIM: c_6b23ab37 — status=not_enough_info]

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation

- [X] T010 [US1] Contract test for `ast_parser.py` in `tests/unit/test_ast_parser.py`: Implement `test_parse_valid_file` (valid Python file input) and `test_parse_invalid_syntax` (malformed syntax string input). *(Removed `[P]` to avoid running before code exists)*
- [X] T011a [US1] **ATOMIZED**: Unit test for `ast_parser.py` in `tests/unit/test_ast_parser.py`: Verify parsing of a valid file returns expected metrics.
- [X] T011b [US1] **ATOMIZED**: Unit test for `adapter_generator.py` in `tests/unit/test_adapter_generator.py`: Verify MLP projection and adapter saving logic with mock data.
- [X] T011c [US1] **ATOMIZED**: Unit test for `adapter_loader.py` in `tests/unit/test_adapter_loader.py`: Verify loading of generated `.safetensors` file without GPU.

### Implementation for User Story 1

- [X] T012 [P] [US1] Implement `code/feature_extractor/ast_parser.py` to extract cyclomatic complexity, depth of inheritance, and token histograms using `ast` and `tokenize` (FR-001).
- [X] T013 [P] [US1] Implement `code/feature_extractor/graph_builder.py` to compute import graph centrality using `networkx` (FR-001).
- [X] T014 [US1] Implement `code/hypernetwork/mlp_projection.py`: Define a small MLP (ReLU) mapping AST feature vectors to the original embedding dimension. **Derive `input_dim` from `config.feature_vector_size` and `output_dim` from `config.hidden_size` (or `embedding_dim`) loaded from the base model config.** Verify model forward pass returns tensor of shape (batch, embedding_dim).
- [X] T015 [US1] Implement `code/hypernetwork/adapter_generator.py`: Load frozen base model **and preserve the original GRU‑based hypernetwork weights** (FR-003), train **ONLY** the new MLP projection layer, and output a `.safetensors` adapter (FR-003). **Depends on configuration from T005.**
- [ ] T015b [US1] **MODIFICATION OF T015**: **Add latency timer logic to T015**. Wrap the adapter generation logic in `code/hypernetwork/adapter_generator.py` with a timer. Output the measured generation time (in seconds) to `data/results/ast_generation_latency.json` with keys `timestamp`, `duration_seconds`, `feature_set`. **This is the SOLE task measuring AST generation latency; T040 will consume this output.** **Depends on T015 implementation.**
- [ ] T017 [US1] **MERGED & REFINED**: Implement **pre-flight and runtime** error handling in `adapter_generator.py`. Define custom exceptions: `MemoryLimitError` (inherits Exception) and `CheckpointIncompatibilityError` (inherits Exception). Implement logic to: 1) **Pre-flight RAM Check**: Before allocation, check available RAM; if < 7 GB, raise `MemoryLimitError` (Code: **E001**) with exact log message format: `ERROR: E001: Memory Limit Exceeded (7GB) - Pre-flight`. 2) **Runtime RAM Check**: Monitor RSS during execution; if > 7 GB, raise `MemoryLimitError` (Code: **E003**) with exact log message format: `ERROR: E003: Memory Limit Exceeded (7GB) - Runtime`. 3) **Checkpoint Check**: Validate base model checkpoint compatibility; if incompatible, raise `CheckpointIncompatibilityError` (Code: **E002**) with exact log message format: `ERROR: E002: Incompatible Checkpoint: {reason}`. 4) All exceptions must be caught in `main.py` to abort gracefully. **Verification**: Unit tests must assert the exact exception type is raised and the log output matches the specified `ERROR: [CODE]: {message}` format exactly. (FR-008, FR-006, FR-009).
- [ ] T016 [US1] **FUNCTIONAL IMPLEMENTATION**: Implement the control-flow logic in `ast_parser.py` to skip malformed files, call the `log_warning` handler defined in T006 (passing filename and error), and **continue processing** (FR-007).

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Evaluate Adapter Performance on Assertion Tasks (Priority: P2)

**Goal**: Evaluate the generated AST‑based adapter against the RepoPeftBench Python subset and compare with neural baseline.

**Independent Test**: The system loads an adapter, runs RepoPeftBench tasks, and outputs exact‑match scores.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T019 [P] [US2] Contract test for `runner.py` scoring logic on a mock assertion task in `tests/unit/test_evaluation_runner.py`.
- [X] T020 [P] [US2] Integration test for full evaluation pipeline on a subset of RepoPeftBench in `tests/integration/test_evaluation.py`.

### Implementation for User Story 2

- [X] T024a [US2] **NEW**: Create `code/evaluation/baseline_loader.py` to load the original Code2LoRA neural‑encoder adapter for comparison (produces artifact required by T021).
- [X] T024b [US2] **NEW**: Create `code/evaluation/baseline_generator.py` to **generate** the baseline neural-encoder adapter using the original Code2LoRA pipeline. This script must output the baseline adapter to `data/adapters/baseline_adapter.safetensors` and log generation time to `data/results/baseline_generation_latency.json`. **Required for T049a.**
- [ ] T021 [US2] Implement `code/evaluation/runner.py` to load RepoPeftBench data, apply the **AST‑based** adapter, and compute **BOTH** exact-match scores **AND** inference latency. Output scores to `data/results/ast_scores.csv` (columns: `task_id, exact_match, latency_ms`). **This task now fully implements FR-004 by including latency measurement.** (Note: This task merges the previous T022 functionality).
- [X] T023 [US2] Implement failure‑mode classification (`'Syntax Error'`, `'Semantic Mismatch'`, `'Timeout'`) for complex tasks; verify logging for a mock `SyntaxError`.
- [X] T025 [US2] Implement `code/evaluation/comparison_report.py` to generate a paired comparison report (AST vs Neural) with performance delta (US‑2 Scenario 2).
- [X] T026 [US2] Implement `code/evaluation/stats.py` to **first perform a Wilcoxon signed-rank test** (per SC-005 and T000) on the two score lists; if normality fails (not applicable to Wilcoxon), fall back to t-test as secondary. Accepts two CSVs (`ast_scores.csv`, `neural_scores.csv`), outputs `data/results/stats.json` containing `p_value`, `statistic`, and `test_used`. Includes verification step asserting `p_value < 0.05` on mock significant data.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Perform Sensitivity Analysis on Feature Complexity (Priority: P3)

**Goal**: Determine the minimum AST feature set required to maintain >80 % of baseline accuracy.

**Independent Test**: The system runs evaluation with different feature subsets and produces a sensitivity curve.

**⚠️ CRITICAL DEPENDENCY**: Phase 5 tasks **MUST** wait for Phase 4 (T021) to complete. Do not start T030 until T021 is done.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T027 [P] [US3] Contract test for `sensitivity.py` feature subset logic in `tests/unit/test_sensitivity.py`.
- [X] T028 [P] [US3] Integration test for sensitivity analysis loop in `tests/integration/test_sensitivity_analysis.py`. **[WAITING ON T021]**

### Implementation for User Story 3

- [X] T029 [P] [US3] Implement `code/evaluation/sensitivity.py` to define feature subsets (e.g., token counts only, cyclomatic only, full AST) (FR‑005).
- [ ] T030 [US3] **BLOCKING PREREQUISITE**: Implement the sensitivity loop in `sensitivity.py` that, for each subset, **sequentially calls** the adapter generator (T015) and evaluator (T021) to obtain scores. **T021 is a BLOCKING PREREQUISITE; Phase 5 cannot begin until T021 is verified complete.** The loop must ensure T015 completes successfully before invoking T021 for the same subset. **[WAITING ON T021]**
- [X] T031a [US3] **NEW**: Implement logic to extract the **baseline accuracy score** from the neural evaluation results (T021/T024) and save it to `data/results/baseline_score.json`. **Must be completed before T032.**
- [ ] T031b [US3] **NEW**: Ensure `baseline_score.json` is written by T031a with a single key `score` (float).
- [ ] T032 [US3] **Depends on T031a**: Implement logic to parse `data/results/sensitivity_summary.csv` (from T033) and `data/results/baseline_score.json` (from T031a). Calculate the threshold (% of baseline). Identify the minimal feature set meeting the threshold. **Output the result to `data/results/minimal_feature_set.txt` containing the feature set name.** (US‑3 Scenario 3). **[WAITING ON T031a]**
- [X] T033 [US3] Generate a **CSV summary** `data/results/sensitivity_summary.csv` with columns `feature_set, accuracy, meets_threshold`. The research question investigates the sensitivity of model accuracy to different feature sets. [UNRESOLVED-CLAIM: c_53c8e1e2 — status=not_enough_info] The method involves training models across various feature combinations and evaluating performance against a predefined accuracy threshold. References: (Author et al.,).. Verify the file exists and is non‑empty. *(No visual plot is produced, respecting the spec.)*

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Resource Enforcement & Validation (Cross‑Cutting Concerns)

**Purpose**: Ensure FR‑006 compliance (2 cores, 7 GB RAM) and SC‑001/SC‑004 measurement requirements.

**Conflict Avoidance**: Tasks in this phase target distinct files to prevent merge conflicts. Do not modify the same file across parallel tasks. T039 -> `cpu_monitor.py`, T040 -> `latency_monitor.py`, T041/T043 -> `memory_monitor.py`, T048 -> `cpu_monitor.py` (audit), T050 -> `resource_summary.csv`.

- [X] T039 [P] Implement `code/utils/cpu_monitor.py` to enforce a **core limit** via `taskset` (CPU affinity) and log CPU usage; verify that the process is restricted to a bounded subset of cores.
- [ ] T040 [US2] **DEPENDENCY**: Implement `code/utils/latency_monitor.py` to **measure adapter generation latency** (AST) by reading `data/results/ast_generation_latency.json` (from T015b) and comparing it against the baseline generation latency (from T049a). Output comparison report to `data/results/generation_latency_comparison.json`. **Does NOT re-measure; consumes T015b output.** **[NOTE: Not parallel-safe due to dependency on T015b]**. **Dependency: Must run after T015b.**
- [X] T041 [P] Implement `code/utils/memory_monitor.py` to measure **peak RSS memory usage** via the `resource` module at each pipeline step and log to `data/results/memory_log.csv` (SC‑004).
- [X] T036 [P] **MOVED FROM PHASE 8**: Implement a **timeout mechanism** in `code/main.py` that terminates the entire pipeline after a predetermined time limit, raising a controlled exception. **Required for T047.**
- [ ] T042 [P] Add a CI job that runs the full pipeline on sample data to verify the **timeouts** and resource limits (replaces previous T036 verification task).
- [X] T048 [P] (Optional) Add a lightweight script in `code/utils/cpu_monitor.py` to verify that the process is limited to a constrained number of CPU cores at runtime (e.g., using `psutil`), logging the result for audit purposes.
- [X] T049a [US2] **NEW**: Measure baseline neural-encoder generation latency by executing `code/evaluation/baseline_generator.py` (T024b) and reading the output from `data/results/baseline_generation_latency.json`. **Depends on T024b.**
- [ ] T049b [US2] **DEPENDENCY**: Compute the latency reduction ratio (AST generation latency from T015b / baseline generation latency from T049a) and store a comparison report in `data/results/generation_latency_comparison.json`. Ensure the reduction is ≥ 10× as required by SC‑001. **Depends on T015b and T049a.** **[NOTE: Not parallel-safe due to dependency on T049a]**. **Dependency: Must run after T049a.**
- [ ] T050 [P] Aggregate peak memory usage logs from `data/results/memory_log.csv`, compute total runtime per stage, and write a summary `data/results/resource_summary.csv`. Verify that peak RAM stays ≤ 7 GB and total runtime ≤ 6 h.
- [X] T051 [P] Add unit tests for `graph_builder.py` centrality algorithms in `tests/unit/test_graph_builder.py`.
- [ ] T052 [P] Create `scripts/validate_quickstart.sh` that executes the commands in `quickstart.md` and asserts successful exit codes.
- [ ] T053 [P] Polish documentation updates in `README.md` and `specs/001-ast-based-adapter-generation/quickstart.md`.

---

## Phase 7: Data Acquisition & Reproducibility (Critical Fix)

**Purpose**: Ensure real data availability and prevent fabrication (Rule: Real data + real results only).

- [X] T054 [P] Implement `code/data/download_repopeftbench.py` to fetch the RepoPeftBench Python subset from the official HuggingFace dataset (`datasets.load_dataset("repo-peft-bench", "python")`) or Zenodo mirror, verifying checksums before writing to `data/raw/`.
- [ ] T055 [P] **REPLACED**: Download a **verified, deterministic subset** of the RepoPeftBench dataset to `data/raw/sample_repo`. Use `code/data/download_repopeftbench.py` to fetch the first **N** repositories (e.g., N=10, seed=42) from the official dataset using **streaming** to avoid memory overflow. **Do NOT generate synthetic data.** This ensures the sample is a canonical subset, satisfying Data Hygiene and Reproducibility principles. Verify checksums. **Must be completed before T021.**
- [ ] T056 [P] Add a validation step in `code/main.py` that checks for the existence of `data/raw/` datasets before running `generate` or `evaluate` commands, failing fast with a clear error message if data is missing.

---

## Phase 8: Polish & Cross‑Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T034 [P] Documentation updates in `README.md` and `specs/001-ast-based-adapter-generation/quickstart.md`.
- [ ] T035 Code cleanup and refactoring of `code/` modules for readability.

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
 - **CRITICAL**: Phase 5 tasks (T030+) MUST wait for Phase 4 (T021) to complete.

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
3. Complete Phase 7: Data Acquisition (Fetch real RepoPeftBench data; Generate local sample)
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
- **Critical**: T017 implements the complete memory handling strategy (pre-flight E001, runtime E003). T043 has been merged into T017 and removed.
- **Critical**: T015b is the SOLE measurement task for AST generation latency. T040 consumes T015b output.
- **Critical**: T024b generates the baseline adapter; T024a loads it.
- **Critical**: T031a provides baseline score for T032.
- **Critical**: T016 handles skip logic. T021 now includes latency measurement (merged T022).
- **Critical**: T040 and T049b are NOT parallel-safe due to dependencies on T015b and T049a respectively.
- **Critical**: T030, T028, T032 have explicit waiting markers.
- **Critical**: T000 resolves Plan/Spec contradiction by amending Plan.
- **Critical**: T055 downloads a real subset of RepoPeftBench via streaming; no synthetic generation.