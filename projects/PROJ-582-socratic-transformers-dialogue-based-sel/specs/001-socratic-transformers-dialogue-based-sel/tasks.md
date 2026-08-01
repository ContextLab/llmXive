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

- [ ] T001 Create project structure per implementation plan: create directories `projects/PROJ-582-socratic-transformers-dialogue-based-sel/code/src/`, `projects/PROJ-582-socratic-transformers-dialogue-based-sel/code/src/data/`, `projects/PROJ-582-socratic-transformers-dialogue-based-sel/code/src/train/`, `projects/PROJ-582-socratic-transformers-dialogue-based-sel/code/src/eval/`, `projects/PROJ-582-socratic-transformers-dialogue-based-sel/code/src/analyze/`, `projects/PROJ-582-socratic-transformers-dialogue-based-sel/code/src/utils/`, `projects/PROJ-582-socratic-transformers-dialogue-based-sel/code/tests/`, `projects/PROJ-582-socratic-transformers-dialogue-based-sel/code/tests/contract/`, `projects/PROJ-582-socratic-transformers-dialogue-based-sel/code/tests/integration/` and files `requirements.txt`, `src/__init__.py`, `tests/__init__.py`.
- [X] T002 Initialize Python project with dependencies (`transformers`, `peft`, `bitsandbytes`, `datasets`, `scikit-learn`, `pandas`, `pytest`) in `projects/PROJ-582-socratic-transformers-dialogue-based-sel/code/requirements.txt`
- [ ] T003 [P] Configure linting and formatting tools (ruff/black) in `projects/PROJ-582-socratic-transformers-dialogue-based-sel/code/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Setup data directory structure (`data/raw/`, `data/processed/`, `data/results/`) and `.gitkeep` files
- [ ] T005 Implement structured logging utility in `src/utils/logging.py` to handle degenerate dialogue events as JSON lines (Edge Case requirement)
- [ ] T006 Setup environment configuration management for random seeds and model paths in `src/utils/config.py`
- [ ] T007 Implement base model loader utility in `src/utils/model_loader.py` supporting Low-bit quantization (GGUF or `bitsandbytes` CPU backend) to fit Limited RAM constraint.
- [ ] T008 Implement metric utility in `src/utils/metrics.py` for standard accuracy and loss calculations.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Adversarial Dialogue Data Generation (Priority: P1) 🎯 MVP

**Goal**: Generate static QA tuples and Socratic dialogue tuples (question, answer, critique, revised_answer) from source datasets using a deterministic, non-origination-compliant process.

**Independent Test**: Run the generation script on a small subset of samples and verify the output files contain both static tuples and dialogue tuples with critique fields populated.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation. T045 defines the schema contract that T014 must satisfy.

- [X] T045 [Contract Definition] Implement dialogue tuple schema validation in `tests/contract/test_schemas.py`: implement `test_validate_dialogue_schema` to assert JSONL records contain `question`, `initial_answer`, `critique`, and `revised_answer` fields, matching the spec's tuple structure.

### Implementation for User Story 1

- [ ] T012 [P] Implement dataset downloader in `src/data/download.py` fetching GSM8K/MATH via HuggingFace `datasets.load_dataset` (real data requirement)
- [ ] T013 Implement static QA extractor in `src/data/static_extractor.py` to generate the baseline dataset (question, answer) from downloaded sources for comparative study (FR-001).
- [ ] T050 [P] Download/Load Frozen Critic Model in `src/data/critic_loader.py`: acquire a frozen, pre-trained small model (e.g., Llama-3-8B or similar) to be used as the external critic for generating critiques, ensuring separation from the trainable base model.
- [ ] T014 Implement self-critique generator in `src/data/generate_dialogue.py` that:
 1. Uses the base model to generate an initial answer.
 2. Uses the **frozen Critic Model** (from T050) to generate a critique prompt dynamically to identify logical contradictions or unsupported assumptions (per FR-002).
 3. **Prompt Strategy**: The prompt must explicitly instruct the model to identify specific error types (e.g., "calculation error", "logic gap", "unsupported assumption") using pre-defined logical templates to satisfy the Ada Lovelace constraint (no spontaneous origination).
 4. Outputs a structured JSON with `question`, `initial_answer`, `critique`, and `revised_answer`.
 5. Validates that generated questions adhere to simple regex patterns for arithmetic/algebraic structure.
 **Note**: This task depends on T012, T050, and T045 completion.
- [ ] T015 Implement ablation data generator in `src/data/ablation.py` replacing critique text with neutral placeholder text of equivalent token length (FR-007). **Note**: This task depends on T014 output.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - CPU-Constrained Fine-Tuning and Evaluation (Priority: P2)

**Goal**: Fine-tune the base model on both datasets using LoRA and evaluate performance on held-out reasoning benchmarks within free-tier compute limits.

**Independent Test**: Execute the training pipeline on a single random seed and verify it completes within the time budget and produces evaluation metrics.

### Implementation for User Story 2

- [ ] T020 Implement LoRA configuration in `src/train/lora_config.py` with `batch_size ≤ 2`, `gradient_accumulation_steps = 4`, and 4-bit quantization (FR-003).
- [ ] T021 Implement CPU-safe training loop in `src/train/train_loop.py` with hard timeout (FR-008). **OOM Behavior**: If OOM occurs on CPU, the script exits with a non-zero code to trigger the execution stage's auto-offload to Kaggle GPU. The script must NOT attempt to load a fallback model locally.
- [ ] T022 [P] Implement GPU Offload Orchestrator in `src/train/offload_orchestrator.py`: implement logic to detect the non-zero exit code from T021, parse the error log for OOM, and trigger a re-run of the training script on a Kaggle GPU environment with scaled-down parameters (fewer epochs, smaller batch size).
- [ ] T046 Create `src/eval/evaluate.py` running GSM8K test split and MMLU STEM subset, logging accuracy.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Analysis and Ablation (Priority: P3)

**Goal**: Perform statistical comparison between conditions and ablate the self-critique component to isolate its effect.

**Independent Test**: Run the analysis script on the logged metrics from multiple seeds. and verify the statistical test output.

> **Scope Note**: The reviewer-derived metrics "System 2 Checkpoint" (T062), "Attention Weight Analysis" (T063), and "Productive Ignorance" (T064) were excluded from this specification as they are not listed as Functional Requirements (FR-*) or Success Criteria (SC-*) in `spec.md`. Their exclusion prevents scope creep and ensures focus on the mandated "negative selection on belief" mechanism.

### Implementation for User Story 3

- [ ] T047 Create `src/utils/stats_analysis.py`:
 - Perform **Independent Samples t-tests** (Selection vs. Ablation, Selection vs. Static) per Plan's Complexity Tracking.
 - Apply Bonferroni correction ($\alpha = 0.025$).
 - Calculate MDES and report effect sizes.
 - **Stop-Rule**: If effect size < MDES, report "Inconclusive due to power".
- [ ] T027 Implement statistical analysis script in `src/analyze/stats.py` running **Independent Samples t-tests** on multiple seeds per condition.
- [ ] T028 Implement Bonferroni/FDR correction in `src/analyze/stats.py` for multiple benchmarks (FR-006).
- [ ] T029 Implement sensitivity analysis sweep over prediction error threshold values (log-prob per token range) to validate robustness (FR-006).
- [ ] T031 Implement ablation comparison logic in `src/analyze/stats.py` contrasting Dialogue vs. Ablation vs. Static conditions to isolate the critique signal. **Note**: This task depends on T014, T015, T046 (Evaluation), and T021 (Training) completion.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and address philosophical/operational clarity from reviews.

- [ ] T034 Update `research.md` to explicitly distinguish between (a) engine executing a pre-ordained self-improvement procedure and (b) genuine origination, addressing **Ada Lovelace's** repeated concerns about "origination" vs. "operations".
- [ ] T039 [P] [Review] Document the operational distinction between "generative capability" (required by FR-001) and "deterministic operation" (Ada Lovelace's constraint) in `docs/philosophy.md`, clarifying that the system generates via ordered operations on internal states rather than spontaneous origination.
- [ ] T040 [Review] Reframe `spec.md` and `research.md` problem statement to replace "self-teaching" with "evolutionary pressure" and "negative selection on belief" to align with David Krakauer's distinction between instruction and selection.
- [ ] T042 Run `ruff check` and `black --check` on all `src/` and `tests/` files; fix any linting/formatting errors to achieve zero violations.
- [X] T043 [P] [Review] Document the operational distinction between "generative capability" (required by FR-001) and "deterministic operation" (Ada Lovelace's constraint) in `docs/philosophy.md`, clarifying that the system generates via ordered operations on internal states rather than spontaneous origination.
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
 - **Internal Dependency**: T014 depends on T012, T050, and T045 completion.
 - **Internal Dependency**: T015 depends on T014 completion.
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
 - **Internal Dependency**: T020 depends on T007 completion.
 - **Internal Dependency**: T021 depends on T020 completion.
 - **Internal Dependency**: T022 depends on T021 completion (detects its exit code).
 - **Internal Dependency**: T046 depends on T021 completion.
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable
 - **Internal Dependency**: T031 depends on T014, T015, T046, and T021 completion.

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

# Note: T014 (critique generator) MUST run AFTER T012, T050, and T045 complete.
# Note: T015 (ablation) MUST run AFTER T014 completes.
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (T012 -> T013 -> T050 -> T014 -> T015)
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
 - Developer A: User Story 1 (Data Generation: T012, T013, T050, T014, T015)
 - Developer B: User Story 2 (Training & Evaluation: T020, T021, T022, T046)
 - Developer C: User Story 3 (Stats & Ablation: T047, T027, T028, T029, T031)
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
 - **Alan Turing**: Tasks T021 (Hard Timeouts) address the need for operational definitions and bounded execution.
 - **Ada Lovelace**: Tasks T034, T039, T043 address the philosophical constraint that the engine cannot originate, only execute ordered operations via pre-defined logical templates in T014.
 - **David Krakauer**: Tasks T034, T040 address the distinction between instruction and evolutionary pressure/negative selection.
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Compute Constraint**: All training tasks (T021) must strictly adhere to 4-bit quantization and exit on OOM for auto-offload to ensure execution on 7GB RAM free-tier runners. The offload mechanism is implemented in T022.