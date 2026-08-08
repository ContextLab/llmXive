# Tasks: Socratic Transformers: Dialogue-Based Selection on Belief

**Input**: Design documents from `/specs/582-socratic-transformers-dialogue-based-sel/`
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

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure per implementation plan: create directories `projects/PROJ-582-socratic-transformers-dialogue-based-sel/code/src/`, `projects/PROJ-582-socratic-transformers-dialogue-based-sel/code/src/data/`, `projects/PROJ-582-socratic-transformers-dialogue-based-sel/code/src/train/`, `projects/PROJ-582-socratic-transformers-dialogue-based-sel/code/src/eval/`, `projects/PROJ-582-socratic-transformers-dialogue-based-sel/code/src/analyze/`, `projects/PROJ-582-socratic-transformers-dialogue-based-sel/code/src/utils/`, `projects/PROJ-582-socratic-transformers-dialogue-based-sel/code/tests/`, `projects/PROJ-582-socratic-transformers-dialogue-based-sel/code/tests/contract/`, `projects/PROJ-582-socratic-transformers-dialogue-based-sel/code/tests/integration/` and files `requirements.txt`, `src/__init__.py`, `tests/__init__.py`. **Verification**: Run `find projects/PROJ-582-socratic-transformers-dialogue-based-sel/code -type d -name src` and assert all directories and files exist.
- [X] T002 Initialize Python project with dependencies (`transformers`, `peft`, `bitsandbytes`, `datasets`, `scikit-learn`, `pandas`, `pytest`) in `projects/PROJ-582-socratic-transformers-dialogue-based-sel/code/requirements.txt`
- [ ] T003 [P] Configure linting and formatting tools: Create `ruff.toml` and `pyproject.toml` (with `[tool.black]` section) in `projects/PROJ-582-socratic-transformers-dialogue-based-sel/code/`. **Verification**: Run `ruff check.` and verify exit code 0.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [P] Setup data directory structure (`data/raw/`, `data/processed/`, `data/results/`) and `.gitkeep` files
- [ ] T005 [P] Implement structured logging utility in `src/utils/logging.py` to handle degenerate dialogue events as JSON lines. **Schema**: Events must follow `{"event_type": str, "timestamp": str, "details": dict}`.
- [ ] T006 [P] Setup environment configuration management for random seeds and model paths in `src/utils/config.py`
- [ ] T007 [P] Implement base model loader utility in `src/utils/model_loader.py` supporting 4-bit quantization via `bitsandbytes` (CPU backend). **Verification**: Implement memory check using `psutil` within the loader script; assert `psutil.Process().memory_info().rss < 7 * 1024 * 1024 * 1024` bytes during load.
- [ ] T008 [P] Implement metric utility in `src/utils/metrics.py` for standard accuracy and loss calculations.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Adversarial Dialogue Data Generation (Priority: P1) 🎯 MVP

**Goal**: Generate static QA tuples and Socratic dialogue tuples (question, answer, critique, revised_answer) from source datasets using a deterministic, non-origination-compliant process.

**Independent Test**: Run the generation script on a small subset of samples and verify the output files contain both static tuples and dialogue tuples with critique fields populated.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation. T045 defines the schema contract that T014 must satisfy.

- [X] T045 [Contract Definition] Implement dialogue tuple schema validation in `tests/contract/test_schemas.py`: implement `test_validate_dialogue_schema` to assert JSONL records contain `question`, `initial_answer`, `critique`, and `revised_answer` fields, matching the spec's tuple structure.

### Implementation for User Story 1

- [ ] T012 [P] Implement dataset downloader in `src/data/download.py` fetching GSM8K/MATH via HuggingFace `datasets.load_dataset` (real data requirement). **Verification**: Verify checksums match `state/` manifest.
- [ ] T050 [P] Download/Load Frozen Critic Model in `src/data/critic_loader.py`: acquire a frozen, pre-trained small model (e.g., Llama-3-8B or similar). **Verification**: Assert `model.requires_grad = False` and verify model is not fine-tuned (check `model.config` for fine-tune history or use a known base checkpoint).
- [ ] T015a [P] Implement token length calculator in `src/data/ablation_utils.py`: Calculate the exact token count of a critique string using the target tokenizer.
- [ ] T015c [P] Implement syntactic complexity calculator in `src/data/ablation_utils.py`: Calculate a syntactic complexity score (e.g., based on parse tree depth or dependency count) for a critique string using `spaCy` or `nltk`. **Verification**: Assert the function returns a numeric score > 0 for valid critiques.
- [ ] T013 [P] Implement static QA extractor in `src/data/static_extractor.py` to generate the baseline dataset (question, answer) from downloaded sources for comparative study (FR-001).
- [ ] T014 Implement self-critique generator in `src/data/generate_dialogue.py` that:
 1. Loads input questions from GSM8K/MATH (T012).
 2. Uses the **frozen Critic Model** (from T050) to **apply a deterministic template** from `src/data/templates/critique_templates.py` to identify logical contradictions. **Templates**: The file `critique_templates.py` must explicitly define error types: `["calculation_error", "logic_gap", "unsupported_assumption"]` and their corresponding prompt templates.
 3. Generates a critique by filling the selected template with model-derived evidence.
 4. Outputs a structured JSON with `question`, `initial_answer`, `critique`, and `revised_answer`.
 5. Validates that the *answer/critique pair* adheres to the schema (T045).
 6. **Quality Gate**: Discard dialogues where critique length < 20 tokens, lacks logical keywords, or confidence < 0.6.
 **Note**: This task depends on T012, T050, T045, and T015a completion.
- [ ] T015b Implement ablation data generator in `src/data/ablation.py` replacing critique text with neutral placeholder text of equivalent token length AND equivalent syntactic complexity (FR-007). **Logic**:
 - **Generation Method**: Generate neutral text by repeating a fixed syntactic template (e.g., a nested clause structure like "The variable X is defined as Y, which implies Z, therefore...") until the token count matches the original critique.
 - **Verification**: Use T015a to verify token count match and T015c to verify the syntactic complexity score is within 5% of the original critique.
 **Note**: This task depends on T014, T015a, and T015c completion.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - CPU-Constrained Fine-Tuning and Evaluation (Priority: P2)

**Goal**: Fine-tune the base model on both datasets using LoRA and evaluate performance on held-out reasoning benchmarks within free-tier compute limits.

**Independent Test**: Execute the training pipeline on a single random seed and verify it completes within the time budget and produces evaluation metrics.

### Implementation for User Story 2

- [ ] T020 [P] Implement LoRA configuration in `src/train/lora_config.py` with `batch_size ≤ 2`, `gradient_accumulation_steps = 4`, and 4-bit quantization (FR-003).
- [ ] T021 Implement CPU-safe training loop in `src/train/train_loop.py` with **a hard timeout of several hours** using `signal.signal(signal.SIGALRM, timeout_handler)`. **OOM Behavior**: If OOM occurs on CPU, the script MUST exit with **code 1** to trigger the execution stage's auto-offload. The script must NOT attempt to load a fallback model locally. **Note**: This task is NOT parallel-safe with T022 as it is the trigger for the failover. **Verification**: Simulate timeout and verify exit code 1.
- [ ] T022 Implement GPU Offload Orchestrator in `src/train/gpu_offload.py`: A **CI wrapper script** that monitors the exit code of `train_loop.py` (T021). If T021 exits with code 1 (OOM), this script **automatically re-invokes** the training command on a Kaggle GPU environment with scaled-down parameters (reduced batch size, gradient accumulation compensation). **Note**: This task is NOT parallel-safe with T021; it runs sequentially only upon T021 failure. **Execution Order**: Triggered automatically by CI upon T021 failure.
- [ ] T046 Create `src/eval/evaluate.py` running GSM8K test split and MMLU STEM subset, logging accuracy to `data/results/metrics.json`. **Verification**: Assert `data/results/metrics.json` exists, is valid JSON, and contains keys `accuracy` and `loss`.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Analysis and Ablation (Priority: P3)

**Goal**: Perform statistical comparison between conditions and ablate the self-critique component to isolate its effect.

**Independent Test**: Run the analysis script on the logged metrics from multiple seeds. and verify the statistical test output.

### Implementation for User Story 3

- [ ] T033 Create `src/utils/stats_analysis.py`:
 - **Input**: Read from `data/results/metrics.json`.
 - **Output**: Write to `data/results/stats_report.md`.
 - Perform **Independent Samples t-tests** (Selection vs. Ablation, Selection vs. Static) per Plan's Complexity Tracking.
 - Apply Bonferroni correction ($\alpha = 0.025$).
 - Calculate MDES and report effect sizes.
 - **Stop-Rule**: If effect size < MDES, report "Inconclusive due to power".
- [ ] T031 Implement ablation comparison logic in `src/analyze/stats.py` contrasting Dialogue vs. Ablation vs. Static conditions to isolate the critique signal. **Note**: This task depends on T013 (Static), T014 (Dialogue), T015b (Ablation), T046 (Evaluation), and T021 (Training) completion. **Verification**: Assert that the script correctly identifies the condition labels and performs the t-test.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and address philosophical/operational clarity from reviews.

- [ ] T034 [Review] Update `research.md` and `docs/philosophy.md` to explicitly distinguish between (a) engine executing a pre-ordained self-improvement procedure and (b) genuine origination. **Content**: Add **Section 3.1: Operational Distinction** detailing the "punch-card" mechanism and deterministic mapping, and document the operational distinction between "generative capability" and "deterministic operation" (Ada Lovelace's constraint).
- [ ] T040 [Review] Reframe `spec.md` and `research.md` problem statement to replace "self-teaching" with "evolutionary pressure" and "negative selection on belief" to align with David Krakauer's distinction between instruction and selection. **Content**: Update **Problem Statement** and **Methodology** sections explicitly.
- [ ] T042 Run `ruff check` and `black --check` on all `src/` and `tests/` files; fix any linting/formatting errors to achieve zero violations.
- [ ] T049 [P] Run `bash projects/PROJ-582-socratic-transformers-dialogue-based-sel/code/quickstart.sh` (or equivalent command) and verify exit code 0 to confirm all quickstart steps execute without error.

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
 - **Internal Dependency**: T013 depends on T012 completion.
 - **Internal Dependency**: T014 depends on T012, T050, T045, and T015a completion.
 - **Internal Dependency**: T015b depends on T014, T015a, and T015c completion.
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
 - **Internal Dependency**: T020 depends on T007 completion.
 - **Internal Dependency**: T021 depends on T020 completion.
 - **Internal Dependency**: T022 depends on T021 completion (automated failover on OOM).
 - **Internal Dependency**: T046 depends on T021 completion.
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable
 - **Internal Dependency**: T031 depends on T013, T014, T015b, T046, and T021 completion.

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
Task: "Contract test for dialogue tuple schema in tests/contract/test_schemas.py" (T045)

# Launch independent models for User Story 1 together:
Task: "Implement dataset downloader in src/data/download.py" (T012)
Task: "Download/Load Frozen Critic Model in src/data/critic_loader.py" (T050)
Task: "Implement token length calculator in src/data/ablation_utils.py" (T015a)
Task: "Implement syntactic complexity calculator in src/data/ablation_utils.py" (T015c)

# Note: T014 (critique generator) MUST run AFTER T012, T050, T045, and T015a completion.
# Note: T015b (ablation) MUST run AFTER T015a and T015c.
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (T012 -> T013 -> T050 -> T015a -> T015c -> T014 -> T015b)
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
 - Developer A: User Story 1 (Data Generation: T012, T013, T050, T015a, T015c, T014, T015b)
 - Developer B: User Story 2 (Training & Evaluation: T020, T021, T022, T046)
 - Developer C: User Story 3 (Stats & Ablation: T033, T031)
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- **Critical Review Alignment**:
 - **Alan Turing**: Tasks T021 (Hard Timeouts), T033 (Statistical Rigor) address the need for operational definitions and bounded execution.
 - **Ada Lovelace**: Tasks T034, T040 address the philosophical constraint that the engine cannot originate, only execute ordered operations via pre-defined logical templates and deterministic verification.
 - **David Krakauer**: Tasks T034, T040 address the distinction between instruction and evolutionary pressure/negative selection.
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Compute Constraint**: All training tasks (T021) must strictly adhere to 4-bit quantization and exit on OOM (code 1) for auto-offload to ensure execution on 7GB RAM free-tier runners.
- **Execution Order Note**: T022 (GPU Offload) is an automated CI script triggered ONLY if T021 fails with OOM. It is not parallel to T021.