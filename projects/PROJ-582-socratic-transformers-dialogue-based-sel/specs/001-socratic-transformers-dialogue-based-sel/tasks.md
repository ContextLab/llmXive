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

- [ ] T001a [P] Create project directory structure: Create directories `projects/PROJ-582-socratic-transformers-dialogue-based-sel/code/`, `projects/PROJ-582-socratic-transformers-dialogue-based-sel/code/src/`, `projects/PROJ-582-socratic-transformers-dialogue-based-sel/code/src/data/`, `projects/PROJ-582-socratic-transformers-dialogue-based-sel/code/src/train/`, `projects/PROJ-582-socratic-transformers-dialogue-based-sel/code/src/eval/`, `projects/PROJ-582-socratic-transformers-dialogue-based-sel/code/src/analyze/`, `projects/PROJ-582-socratic-transformers-dialogue-based-sel/code/src/utils/`, `projects/PROJ-582-socratic-transformers-dialogue-based-sel/code/tests/`, `projects/PROJ-582-socratic-transformers-dialogue-based-sel/code/tests/contract/`, `projects/PROJ-582-socratic-transformers-dialogue-based-sel/code/tests/integration/`. **Verification**: Run `ls -R projects/PROJ-582-socratic-transformers-dialogue-based-sel/code` and assert all directories exist.
- [ ] T001b [P] Create project init files: Create files `projects/PROJ-582-socratic-transformers-dialogue-based-sel/code/requirements.txt`, `projects/PROJ-582-socratic-transformers-dialogue-based-sel/code/src/__init__.py`, `projects/PROJ-582-socratic-transformers-dialogue-based-sel/code/tests/__init__.py`. **Verification**: Run `ls projects/PROJ-582-socratic-transformers-dialogue-based-sel/code/requirements.txt` and assert file exists.
- [X] T002 Initialize Python project with dependencies (`transformers`, `peft`, `bitsandbytes`, `datasets`, `scikit-learn`, `pandas`, `pytest`, `tokenizers`) in `projects/PROJ-582-socratic-transformers-dialogue-based-sel/code/requirements.txt`
- [ ] T003 [P] Configure linting and formatting tools: Create `pyproject.toml` and `ruff.toml` in `projects/PROJ-582-socratic-transformers-dialogue-based-sel/code/`. **Verification**: Run `ruff check.` and verify exit code 0.
- [ ] T010 [P] Implement `verify_datasets.py` in `src/data/verify_datasets.py`: Record checksums for GSM8K (`openai/gsm8k`) and MATH (`hendrycks/math`) in `state/` manifest, validate raw data integrity against the manifest before processing. **Verification**: Run script and assert exit code 0 only if checksums match the recorded manifest.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [P] Setup data directory structure (`data/raw/`, `data/processed/`, `data/results/`) and `.gitkeep` files
- [ ] T005 [P] Implement structured logging utility in `src/utils/logging.py` to handle degenerate dialogue events as JSON lines. **Schema**: Events must follow `{"event_type": str, "timestamp": str, "details": dict}`.
- [ ] T006 [P] Setup environment configuration management for random seeds and model paths in `src/utils/config.py`
- [ ] T007 [P] Implement base model loader utility in `src/utils/model_loader.py` supporting 4-bit quantization via `bitsandbytes` (CPU backend). **Verification**: Ensure the loader successfully instantiates a low-precision model without OOM on a standard 7GB RAM instance. (Note: Full runtime memory monitoring is handled in T021).
- [ ] T008 [P] Implement metric utility in `src/utils/metrics.py` for standard accuracy and loss calculations.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Adversarial Dialogue Data Generation (Priority: P1) 🎯 MVP

**Goal**: Generate static QA tuples and Socratic dialogue tuples (question, answer, critique, revised_answer) from source datasets using a deterministic, non-origination-compliant process.

**Independent Test**: Run the generation script on a small subset of samples and verify the output files contain both static tuples and dialogue tuples with critique fields populated.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE**: Write these tests FIRST, ensure they FAIL before implementation. T045 defines the schema contract that T014a must satisfy.

- [X] T045 [Contract Definition] Implement dialogue tuple schema validation in `tests/contract/test_schemas.py`: implement `test_validate_dialogue_schema` to assert JSONL records contain `question`, `initial_answer`, `critique`, and `revised_answer` fields, matching the spec's tuple structure.

### Implementation for User Story 1

- [ ] T046 [P] Download/Load Frozen Critic Model in `src/data/critic_loader.py`: acquire a frozen, pre-trained small model `TinyLlama-1.1B-Instruct-v0.2` (verified to fit in 7GB RAM with 4-bit quantization). **Verification**: Assert `model.requires_grad = False`, verify the model loads successfully from HuggingFace, and confirm the model architecture matches the specified version.
- [ ] T012 [P] Implement dataset downloader in `src/data/download.py` fetching GSM8K/MATH via HuggingFace `datasets.load_dataset` (real data requirement). **Verification**: Verify checksums match `state/` manifest.
- [ ] T015a [P] Implement token length calculator in `src/data/ablation_utils.py`: Calculate the exact token count of a critique string using the target tokenizer.
- [ ] T013 [P] Implement static QA extractor in `src/data/static_extractor.py` to generate the baseline dataset (question, answer) from downloaded sources for comparative study (FR-001).
- [ ] T014a Implement self-critique generator core in `src/data/generate_dialogue_core.py` that:
 1. Loads input questions from GSM8K/MATH (T012).
 2. Uses the **frozen Critic Model** (from T046) to generate critiques based on deterministic templates for critique *structure*.
 3. Generates a critique by filling the selected template with model-derived evidence.
 4. Outputs a structured JSON with `question`, `initial_answer`, `critique`, and `revised_answer`.
 5. **Note**: This task depends on T012, T046, T045, and T015a completion.
- [ ] T014b Implement self-critique quality gate in `src/data/generate_dialogue_quality.py` that:
 1. Validates that the answer/critique pair adheres to the schema (T045).
 2. **Quality Gate**: Discard dialogues where critique length < 20 tokens or lacks logical keywords (e.g., "contradiction", "error", "incorrect").
 3. Integrates with T014a to filter outputs.
 **Note**: This task depends on T014a and T045 completion.
- [ ] T015b [FR-007] Implement ablation data generator in `src/data/ablation.py` replacing critique text with neutral placeholder text of equivalent token length (FR-007). **Logic**:
 - **Generation Method**: Replace the semantic content of the original critique with a neutral, semantically void placeholder (e.g., "The variable X is defined as Y, which implies Z, therefore...") while preserving the original token count.
 - **Verification**: Use T015a to verify token count match.
 **Note**: This task depends on T014 and T015a completion.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - CPU-Constrained Fine-Tuning and Evaluation (Priority: P2)

**Goal**: Fine-tune the base model on both datasets using LoRA and evaluate performance on held-out reasoning benchmarks within free-tier compute limits.

**Independent Test**: Execute the training pipeline on a single random seed and verify it completes within the time budget and produces evaluation metrics.

### Implementation for User Story 2

- [ ] T020 [P] Implement LoRA configuration in `src/train/lora_config.py` with `batch_size ≤ 2`, `gradient_accumulation_steps = 4`, and 4-bit quantization (FR-003).
- [ ] T021 Implement CPU-safe training loop in `src/train/train_loop.py` with a hard timeout of **5 hours** using `signal.signal(signal.SIGALRM, timeout_handler)`. **Verification**: Implement memory monitoring using `psutil` to sample the training process RSS every 1 second; assert that the maximum RSS remains < **7GB** during execution. Note: Validation data loading is deferred per plan.md, so this check applies to the training batch processing only.
- [ ] T022 [P] Implement GPU Escape Hatch in `src/train/gpu_offload.py`: Detect OOM errors on CPU, set `CUDA_VISIBLE_DEVICES=0`, Reduce batch size to a minimal value., and re-run training on Kaggle GPU. **Verification**: Simulate OOM and verify script redirects to GPU path with reduced batch size.
- [ ] T047 [FR-006] Create `src/eval/evaluate.py` running GSM8K test split and MMLU STEM subset, logging accuracy to `data/results/metrics.json`. **Verification**: Assert `data/results/metrics.json` exists, is valid JSON, and contains keys `accuracy` and `loss`.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Analysis and Ablation (Priority: P3)

**Goal**: Perform statistical comparison between conditions and ablate the self-critique component to isolate its effect.

**Independent Test**: Run the analysis script on the logged metrics from multiple seeds. and verify the statistical test output.

### Implementation for User Story 3

- [ ] T033 [P] Create `src/utils/stats_analysis.py`:
 - **Input**: Read from `data/results/metrics.json`.
 - **Output**: Write to `data/results/stats_report.md`.
 - Perform **Paired t-tests** (Selection vs. Ablation, Selection vs. Static) with Bonferroni correction ($\alpha = 0.025$).
 - Calculate MDES and report effect sizes.
 - **Stop-Rule**: If effect size < MDES, report "Inconclusive due to power".
 - **Ablation Logic**: Implement the specific comparison logic to isolate the effect of the selection signal content vs. token count.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Philosophical Alignment & Operational Rigor (Priority: P1) [DEPRECATED]

**Goal**: [DEPRECATED] The 'Philosophical Alignment' and 'Calibration' pipeline (AQL, Gap Validator, Attention Shift, Productive Ignorance) is out of scope for the current MVP (FR-001 to FR-008). These features are deferred to a future research phase.

### Implementation for Philosophical Alignment

- [ ] T050 [P] [DEPRECATED] Admissible Question Language (AQL) - Deferred.
- [ ] T051 [P] [DEPRECATED] Knowledge Gap Verification - Deferred.
- [ ] T052 [P] [DEPRECATED] Attention Shift Analysis - Deferred.
- [ ] T053 [P] [DEPRECATED] Productive Ignorance Metric - Deferred.

**Checkpoint**: Phase 6 is deprecated; no implementation required for MVP.

---

## Phase 7: Calibration & Bias Mitigation (Priority: P2) [DEPRECATED]

**Goal**: [DEPRECATED] The 'Calibration' and 'Heuristic Randomization' pipeline is out of scope for the current MVP (FR-001 to FR-008). These features are deferred to a future research phase.

### Implementation for Calibration

- [ ] T054 [P] [DEPRECATED] System 2 Calibration Checkpoint - Deferred.
- [ ] T055 [P] [DEPRECATED] Heuristic Randomization - Deferred.

**Checkpoint**: Phase 7 is deprecated; no implementation required for MVP.

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and address philosophical/operational clarity from reviews.

- [ ] T042 [P] Run `ruff check` and `black --check` on all `src/` and `tests/` files; fix any linting/formatting errors to achieve zero violations.
- [ ] T049 [P] Run `bash projects/PROJ-582-socratic-transformers-dialogue-based-sel/code/quickstart.sh` (or equivalent command) and verify exit code 0 to confirm all quickstart steps execute without error.
- [ ] T056 [P] Update `research.md` to explicitly distinguish between "engine executing ordered operations" and "origination", noting that AQL and Gap Validation are deferred features.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-5)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Philosophical Alignment (Phase 6)**: [DEPRECATED] - No dependencies.
- **Calibration (Phase 7)**: [DEPRECATED] - No dependencies.
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable
- **Philosophical Alignment (Phase 6)**: [DEPRECATED]
- **Calibration (Phase 7)**: [DEPRECATED]

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
- **Phase 6 and 7** are deprecated and do not run in parallel.

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
- **Scope Decision**: Phase 6 (Philosophical Alignment) and Phase 7 (Calibration) are DEPRECATED for the current MVP. The features (AQL, Gap Validator, Attention Shift, Productive Ignorance, Calibration) are not required by FR-001 to FR-008 and are deferred to a future research phase.