# Tasks: Socratic Transformers: Dialogue-Based Selection on Belief

**Input**: Design documents from `/specs/582-socratic-transformers-dialogue-based-sel/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this story belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- Paths shown below assume single project - adjust based on plan.md structure

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001a [P] Create project code root: Create directory `projects/PROJ-582-socratic-transformers-dialogue-based-sel/code/`. **Verification**: Run `python -c "import os; assert os.path.isdir('projects/PROJ-582-socratic-transformers-dialogue-based-sel/code')"` and assert exit code 0.
- [ ] T001b [P] Create `src` directory: Create directory `projects/PROJ-582-socratic-transformers-dialogue-based-sel/code/src/`. **Verification**: Run `python -c "import os; assert os.path.isdir('projects/PROJ-582-socratic-transformers-dialogue-based-sel/code/src')"` and assert exit code 0.
- [ ] T001c [P] Create data directories and `.gitkeep`: Create directories `data/raw/`, `data/processed/`, `data/results/` at project root and create `.gitkeep` files in each. **Verification**: Run `python -c "import os; assert os.path.isdir('data/raw') and os.path.isfile('data/raw/.gitkeep')"` and assert exit code 0 for all directories.
- [ ] T002 [P] Initialize Python project with dependencies (`transformers`, `peft`, `bitsandbytes`, `datasets`, `scikit-learn`, `pandas`, `pytest`, `tokenizers`, `nltk`, `spaCy`) in `projects/PROJ-582-socratic-transformers-dialogue-based-sel/code/requirements.txt`
- [ ] T003 [P] Configure linting and formatting tools: Create `pyproject.toml` and `ruff.toml` in `projects/PROJ-582-socratic-transformers-dialogue-based-sel/code/`. **Verification**: Run `ruff check .` and verify exit code 0.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T005 [P] Implement structured logging utility in `src/utils/logging.py` to handle degenerate dialogue events as JSON lines. **Schema**: Events must follow `{"event_type": str, "timestamp": str, "details": dict}`.
- [ ] T006 [P] Setup environment configuration management for random seeds and model paths in `src/utils/config.py`. **Requirement**: Define `CRITIC_MODEL_ID` and `BASE_MODEL_ID` here.
- [ ] T007 [P] Implement base model loader utility in `src/utils/model_loader.py` supporting 4-bit quantization via `bitsandbytes` (CPU backend). **Verification**: Run `python -c "from src.utils.model_loader import load_model; load_model()"` and assert exit code 0.
- [ ] T008 [P] Implement metric utility in `src/utils/metrics.py` for standard accuracy and loss calculations.
- [ ] T010 [P] Implement `verify_datasets.py` in `src/data/verify_datasets.py`: Record checksums for GSM8K (`openai/gsm8k`) and MATH (`hendrycks/math`) in `state/` manifest, validate raw data integrity against the manifest before processing. **Verification**: Run script and assert exit code 0 only if checksums match the recorded manifest.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Adversarial Dialogue Data Generation (Priority: P1) 🎯 MVP

**Goal**: Generate static QA tuples and Socratic dialogue tuples (question, answer, critique, revised_answer) from source datasets using a deterministic, non-origination-compliant process.

**Independent Test**: Run the generation script on a small subset of samples and verify the output files contain static tuples, dialogue tuples with critique fields populated, and ablation tuples with neutral placeholders.

### Implementation for User Story 1

- [ ] T015a [FR-007] Implement complexity calculator in `src/data/ablation_utils.py`: Calculate the **syntactic complexity** of a critique string for natural language text. **Logic**: Implement a function `calculate_complexity(text)` that returns a dict with `token_count` and `ngram_entropy`. `token_count` is the number of tokens using the target tokenizer. `ngram_entropy` is calculated by computing the Shannon entropy of the 2-gram distribution of the text. This replaces the invalid 'AST depth' requirement with a metric valid for natural language. **Dependency**: Requires `nltk` or `spaCy` (from T002).
- [ ] T046 [P] Download/Load Frozen Critic Model in `src/data/critic_loader.py`: acquire a frozen, pre-trained small model that fits in available memory with 4-bit quantization. **Logic**: The specific model ID must be read from `src/utils/config.py` (key `CRITIC_MODEL_ID`) to allow for reproducibility and updates. **Verification**: Assert `model.requires_grad = False`, verify the model loads successfully from HuggingFace (cached) using the config ID, and confirm the model architecture matches the config.
- [ ] T012 [P] Implement dataset downloader in `src/data/download.py` fetching GSM8K/MATH via HuggingFace `datasets.load_dataset` (real data requirement). **Verification**: Verify checksums match `state/` manifest.
- [ ] T013 [P] Implement static QA extractor in `src/data/static_extractor.py` to generate the baseline dataset (question, answer) from downloaded sources for comparative study (FR-001). **Output**: `data/processed/static_tuples.jsonl`.
- [ ] T014 [P] Implement self-critique generator in `src/data/generate_dialogue.py` that:
 1. **Prerequisites**: Depends on T012 (data), T046 (model), and T015a (complexity calc).
 2. **Load Model**: Loads the **frozen Critic Model** instance produced by T046 via `load_frozen_critic()`.
 3. **Generate Critique**: Generates a critique by filling deterministic templates with model-derived evidence. **Prompt Template**: "Identify logical contradictions, unsupported assumptions, or high-probability errors in the following answer: [ANSWER]. Output only the critique."
 4. **Generate Revised Answer (Negative Selection)**: Generates a `revised_answer` by:
    - Generating N=5 candidate answers using Temperature=0.0 (deterministic) to ensure reproducibility.
    - Scoring each candidate against the generated critique using the Critic Model's likelihood (log-probability).
    - **Rejecting** any candidate that fails the critique check (i.e., if the critique identifies a specific error, the candidate must not contain that error).
    - **Selecting** the first candidate that passes the critique check.
    - If no candidate passes within N attempts, default to a safe fallback answer or mark as `null` (logged).
    - **Note**: This is a rejection-based selection process (negative selection), not a reinforcement of the initial belief.
 5. **Quality Gate**: Applies a quality gate: Discard dialogues where critique length < 20 tokens or lacks logical keywords. **Regex**: `r'(contradiction|error|incorrect|invalid|fallacy|unsubstantiated|contradicts)'`.
 6. **Integration**: Combines the core generation logic and quality gate into a single execution flow, ensuring the output matches the schema defined in T045.
 7. **Output**: `data/processed/dialogue_tuples.jsonl`.
 **Note**: This task explicitly integrates the model loading (T046) and quality gating logic into a single coherent script as defined in plan.md T014.
- [ ] T015b [FR-007] Implement ablation data generator in `src/data/ablation.py` replacing critique text with neutral placeholder text of equivalent **syntactic complexity** (token count and n-gram entropy) (FR-007). **Logic**:
 - **Placeholder Generation**: Generate a neutral, semantically void placeholder string that matches the **token count** and **n-gram entropy** of the original critique (calculated by T015a).
 - **Replacement**: Replace the semantic content of the original critique with the generated placeholder.
 - **Output**: `data/processed/ablation_tuples.jsonl`.
 **Note**: This task depends on T014 and T015a completion.
- [ ] T045 [P] Implement dialogue tuple schema validation in `tests/contract/test_schemas.py`: implement `test_validate_dialogue_schema` to assert JSONL records contain `question`, `initial_answer`, `critique`, and `revised_answer` fields, matching the spec's tuple structure. **Schema Definition**: Records must contain exactly these keys: `question` (str), `initial_answer` (str), `critique` (str), `revised_answer` (str). **Verification**: Run `pytest tests/contract/test_schemas.py` and assert exit code 0. **Dependency**: Requires T014 to have generated sample data for validation.

**Checkpoint**: At this point, User Story 1 is fully functional for Static, Dialogue, and Ablation tuples. **Note**: User Story 2 (Training) requires T015b (Ablation) to be complete as well.

---

## Phase 4: User Story 2 - CPU-Constrained Fine-Tuning and Evaluation (Priority: P2)

**Goal**: Fine-tune the base model on both datasets using LoRA and evaluate performance on held-out reasoning benchmarks within free-tier compute limits.

**Independent Test**: Execute the training pipeline on a single random seed and verify it completes within the time budget and produces evaluation metrics.

### Implementation for User Story 2

- [ ] T020 [P] Implement LoRA configuration in `src/train/lora_config.py` with `batch_size ≤ 2`, `gradient_accumulation_steps = 4`, and 4-bit quantization (FR-003).
- [ ] T021 Implement CPU-safe training loop in `src/train/train_loop.py` with a hard timeout of **5 hours** using `signal.signal(signal.SIGALRM, timeout_handler)`. **Verification**: Implement memory monitoring using `psutil` to sample the training process RSS at regular intervals; log warnings if RSS > 6.5GB. Rely on execution stage error handling if limit is exceeded. Note: Validation data loading for Early Stopping is [deferred] per plan.md, so this check applies to the training batch processing only.
- [ ] T047a [P] Implement Condition A (Selection) training run in `src/train/run_selection_train.py`: Fine-tune model on `data/processed/dialogue_tuples.jsonl`. **Output**: `data/results/checkpoint_selection.pt`.
- [ ] T047b [P] Implement Condition B (Ablation) training run in `src/train/run_ablation_train.py`: Fine-tune model on `data/processed/ablation_tuples.jsonl` (from T015b). **Output**: `data/results/checkpoint_ablation.pt`.
- [ ] T047c [P] Implement Condition C (Static) training run in `src/train/run_static_train.py`: Fine-tune model on `data/processed/static_tuples.jsonl` (from T013). **Output**: `data/results/checkpoint_static.pt`.
- [ ] T047e [P] Execute Comparative Training Runs: Orchestrate the execution of T047a, T047b, and T047c scripts sequentially to generate the required checkpoints. **Verification**: Assert that `data/results/checkpoint_selection.pt`, `data/results/checkpoint_ablation.pt`, and `data/results/checkpoint_static.pt` exist and are non-empty after execution. **Note**: This task ensures the data required for T047d is actually produced.
- [ ] T047d [FR-006] Implement Unified Evaluation in `src/eval/evaluate.py`: **Prerequisites**: T047e must be completed successfully. Load checkpoints from T047e (`checkpoint_selection.pt`, `checkpoint_ablation.pt`, `checkpoint_static.pt`). Run evaluation on GSM8K test split and MMLU STEM subset for each. **Error Handling**: If any checkpoint is missing, log error and exit with non-zero code. **Output**: `data/results/metrics.json` containing accuracy and loss for all three conditions.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Analysis and Ablation (Priority: P3)

**Goal**: Perform statistical comparison between conditions and ablate the self-critique component to isolate its effect.

**Independent Test**: Run the analysis script on the logged metrics from multiple seeds. and verify the statistical test output.

### Implementation for User Story 3

- [ ] T033 [P] Create `src/utils/stats_analysis.py`:
 - **Input**: Read from `data/results/metrics.json`.
 - **Output**: Write to `data/results/stats_report.md`.
 - Perform **Independent t-tests** (Selection vs. Ablation, Selection vs. Static) with Bonferron correction ($\alpha = 0.025$).
 - Calculate MDES and report effect sizes.
 - **Stop-Rule**: If effect size < MDES, report "Inconclusive due to power".
 - **Ablation Logic**: Implement the specific comparison logic to isolate the effect of the selection signal content vs. token count.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and address philosophical/operational clarity from reviews.

- [ ] T042 [P] Run `ruff check` and `black --check` on all `src/` and `tests/` files; fix any linting/formatting errors to achieve zero violations.
- [ ] T049 [P] Run `bash projects/PROJ-582-socratic-transformers-dialogue-based-sel/code/quickstart.sh` (or equivalent command) and verify exit code 0 to confirm all quickstart steps execute without error.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-5)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable
- **Polish (Final Phase)**: Can start after Foundational (Phase 2)

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
- **Scope Decision**: Phase 6 (Philosophical Alignment) and associated tasks (T050-T055) have been REMOVED as they constitute unapproved scope creep not defined in spec.md FR-001 through FR-008.