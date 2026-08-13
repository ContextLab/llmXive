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

- [ ] T001a [P] Create project code structure: Create directories `projects/PROJ-582-socratic-transformers-dialogue-based-sel/code/src/`, `projects/PROJ-582-socratic-transformers-dialogue-based-sel/code/src/data/`, `projects/PROJ-582-socratic-transformers-dialogue-based-sel/code/src/train/`, `projects/PROJ-582-socratic-transformers-dialogue-based-sel/code/src/eval/`, `projects/PROJ-582-socratic-transformers-dialogue-based-sel/code/src/utils/`. **Verification**: Run `ls -R projects/PROJ-582-socratic-transformers-dialogue-based-sel/code/src` and assert all directories exist.
- [ ] T001b [P] Create project test structure: Create directories `projects/PROJ-582-socratic-transformers-dialogue-based-sel/code/tests/`, `projects/PROJ-582-socratic-transformers-dialogue-based-sel/code/tests/contract/`, `projects/PROJ-582-socratic-transformers-dialogue-based-sel/code/tests/integration/`. **Verification**: Run `ls -R projects/PROJ-582-socratic-transformers-dialogue-based-sel/code/tests` and assert all directories exist.
- [ ] T001c [P] Create project data structure: Create directories `data/raw/`, `data/processed/`, `data/results/` at project root. **Verification**: Run `ls -R data` and assert all directories exist.
- [ ] T002 [P] Initialize Python project with dependencies (`transformers`, `peft`, `bitsandbytes`, `datasets`, `scikit-learn`, `pandas`, `pytest`, `tokenizers`) in `projects/PROJ-582-socratic-transformers-dialogue-based-sel/code/requirements.txt`
- [ ] T003 [P] Configure linting and formatting tools: Create `pyproject.toml` and `ruff.toml` in `projects/PROJ-582-socratic-transformers-dialogue-based-sel/code/`. **Verification**: Run `ruff check .` and verify exit code 0.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [P] Setup data directory structure (`data/raw/`, `data/processed/`, `data/results/`) and `.gitkeep` files (Note: T001c creates dirs, this task adds files).
- [ ] T005 [P] Implement structured logging utility in `src/utils/logging.py` to handle degenerate dialogue events as JSON lines. **Schema**: Events must follow `{"event_type": str, "timestamp": str, "details": dict}`.
- [ ] T006 [P] Setup environment configuration management for random seeds and model paths in `src/utils/config.py`. **Requirement**: Define `CRITIC_MODEL_ID` and `BASE_MODEL_ID` here.
- [ ] T007 [P] Implement base model loader utility in `src/utils/model_loader.py` supporting 4-bit quantization via `bitsandbytes` (CPU backend). **Verification**: Run `python -c "from src.utils.model_loader import load_model; load_model()"` and assert exit code 0.
- [ ] T008 [P] Implement metric utility in `src/utils/metrics.py` for standard accuracy and loss calculations.
- [ ] T010 [P] Implement `verify_datasets.py` in `src/data/verify_datasets.py`: Record checksums for GSM8K (`openai/gsm8k`) and MATH (`hendrycks/math`) in `state/` manifest, validate raw data integrity against the manifest before processing. **Verification**: Run script and assert exit code 0 only if checksums match the recorded manifest.
- [ ] T045 [P] Implement dialogue tuple schema validation in `tests/contract/test_schemas.py`: implement `test_validate_dialogue_schema` to assert JSONL records contain `question`, `initial_answer`, `critique`, and `revised_answer` fields, matching the spec's tuple structure.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Adversarial Dialogue Data Generation (Priority: P1) 🎯 MVP

**Goal**: Generate static QA tuples and Socratic dialogue tuples (question, answer, critique, revised_answer) from source datasets using a deterministic, non-origination-compliant process.

**Independent Test**: Run the generation script on a small subset of samples and verify the output files contain static tuples, dialogue tuples with critique fields populated, and ablation tuples with neutral placeholders.

### Implementation for User Story 1

- [ ] T046 [P] Download/Load Frozen Critic Model in `src/data/critic_loader.py`: acquire a frozen, pre-trained small model that fits in 7GB RAM with 4-bit quantization. **Logic**: The specific model ID must be read from `src/utils/config.py` (key `CRITIC_MODEL_ID`) to allow for reproducibility and updates. **Verification**: Assert `model.requires_grad = False`, verify the model loads successfully from HuggingFace (cached) using the config ID, and confirm the model architecture matches the config.
- [ ] T012 [P] Implement dataset downloader in `src/data/download.py` fetching GSM8K/MATH via HuggingFace `datasets.load_dataset` (real data requirement). **Verification**: Verify checksums match `state/` manifest.
- [ ] T015a Implement token length calculator in `src/data/ablation_utils.py`: Calculate the exact token count of a critique string using the target tokenizer from T046. **Dependency**: Requires tokenizer from T046.
- [ ] T013 [P] Implement static QA extractor in `src/data/static_extractor.py` to generate the baseline dataset (question, answer) from downloaded sources for comparative study (FR-001). **Output**: `data/processed/static_tuples.jsonl`.
- [ ] T014 [P] Implement self-critique generator in `src/data/generate_dialogue.py` that:
 1. **Prerequisites**: Depends on T012 (data), T046 (model), T045 (schema), and T015a (token calc).
 2. **Load Model**: Loads the **frozen Critic Model** instance produced by T046 via `load_frozen_critic()`.
 3. **Generate Critique**: Generates a critique by filling deterministic templates with model-derived evidence.
 4. **Generate Revised Answer**: Generates a `revised_answer` by prompting the model with the template: "Critique: {critique}. Revised Answer:" with Temperature=0.7 and Max Retries=3.
 5. **Quality Gate**: Applies a quality gate: Discard dialogues where critique length < 20 tokens or lacks logical keywords. **Regex**: `r'(contradiction|error|incorrect|invalid|fallacy|unsubstantiated|contradicts)'`.
 6. **Integration**: Combines the core generation logic and quality gate into a single execution flow, ensuring the output matches the schema defined in T045.
 7. **Output**: `data/processed/dialogue_tuples.jsonl`.
 **Note**: This task explicitly integrates the model loading (T046) and quality gating logic into a single coherent script as defined in plan.md T014.
- [ ] T015b [FR-007] Implement ablation data generator in `src/data/ablation.py` replacing critique text with neutral placeholder text of equivalent token length (FR-007). **Logic**:
 - **Placeholder Generation**: Generate a neutral, semantically void placeholder string of exactly N tokens using the tokenizer's pad token or a fixed syntactic pattern repeated to match N tokens.
 - **Replacement**: Replace the semantic content of the original critique with the generated placeholder.
 - **Output**: `data/processed/ablation_tuples.jsonl`.
 **Note**: This task depends on T014 and T015a completion.

**Checkpoint**: At this point, User Story 1 is fully functional for Static, Dialogue, and Ablation tuples. **Note**: User Story 2 (Training) requires T015b (Ablation) to be complete as well.

---

## Phase 4: User Story 2 - CPU-Constrained Fine-Tuning and Evaluation (Priority: P2)

**Goal**: Fine-tune the base model on both datasets using LoRA and evaluate performance on held-out reasoning benchmarks within free-tier compute limits.

**Independent Test**: Execute the training pipeline on a single random seed and verify it completes within the time budget and produces evaluation metrics.

### Implementation for User Story 2

- [ ] T020 [P] Implement LoRA configuration in `src/train/lora_config.py` with `batch_size ≤ 2`, `gradient_accumulation_steps = 4`, and 4-bit quantization (FR-003).
- [ ] T021 Implement CPU-safe training loop in `src/train/train_loop.py` with a hard timeout of **5 hours** using `signal.signal(signal.SIGALRM, timeout_handler)`. **Verification**: Implement memory monitoring using `psutil` to sample the training process RSS every 5 seconds; log warnings if RSS > 6.5GB. Rely on T022 (OOM fallback) if limit is exceeded. Note: Validation data loading for Early Stopping is [deferred] per plan.md, so this check applies to the training batch processing only.
- [ ] T022 [P] Implement GPU Escape Hatch in `src/train/gpu_offload.py`: Detect OOM errors on CPU, set `CUDA_VISIBLE_DEVICES=0`, Reduce batch size to a minimal value., and re-run training on Kaggle GPU. **Verification**: Simulate OOM and verify script redirects to GPU path with reduced batch size.
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

## Phase 6: Philosophical Alignment & Operational Clarity (Priority: P2 - Review Resolution)

**Goal**: Address Ada Lovelace and Alan Turing concerns regarding "origination" and "learning signals" by explicitly defining the engine as an executor of ordered operations, not an originator of inquiry.

**Independent Test**: Verify that the `research.md` and code comments explicitly distinguish between "engine executing ordered operations" and "origination", and that the critique generation is framed as a deterministic selection pressure rather than spontaneous questioning.

### Implementation for Phase 6

- [ ] T050 [FR-001/Review] Update `src/data/generate_dialogue.py` and `research.md` to explicitly frame the "Socratic" process as **negative selection on belief** (thymic analogy) rather than "self-teaching". **Logic**: Replace all instances of "self-teaching" or "self-generated inquiry" with "ordered execution of adversarial critique templates" and "selection pressure". Add a module-level docstring comment at the top of `src/data/generate_dialogue.py` stating the selectionist philosophy. **Verification**: Check that the docstring exists and uses the correct terminology.

**Checkpoint**: Philosophical alignment achieved; engine clearly defined as executing ordered operations, not originating inquiry.

---

## Phase 8: Revision Resolutions - Addressing Prior Research Reviews (Priority: P1)

**Goal**: Address specific concerns raised by Ada Lovelace, Alan Turing, Dan Rockmore, Daniel Kahneman, and David Krakauer regarding origination, knowledge gaps, and operational definitions.

### Implementation for Revision Resolutions

- [ ] T056 [FR-001] Implement **Admissible Question Language (AQL) Engine** in `src/data/aql_engine.py`: Define a formal, deterministic grammar for question generation that prevents the model from "originating" questions. The engine must map internal states to pre-ordained question templates (punch-cards) rather than allowing free-form generation. **Verification**: Assert that all generated questions in the dialogue tuples match a regex pattern derived from the AQL grammar, ensuring no "spontaneous" inquiry occurs. (Addresses Ada Lovelace Reviews: 2026-05-17, 2026-05-18, 2026-05-19, 2026-05-30, 2026-05-31).
- [ ] T057 [FR-002] Implement **Knowledge Gap Verification** in `src/data/gap_validator.py`: Introduce a consistency check that validates a generated question exposes a genuine uncertainty or logical contradiction before it is accepted into the dialogue tuple. **Verification**: Implement a "truth-against-known" check where the model's answer to a generated question is compared against a ground-truth oracle; if the model answers correctly without hesitation, the question is discarded as trivial. (Addresses Alan Turing Review: 2026-05-17).
- [ ] T058 [FR-002] Implement **Instruction vs. Memorization Filter** in `src/data/memorization_filter.py`: Add a mechanism to distinguish between learning a principle and merely retrieving a pattern. **Verification**: Implement a threshold-based check on prediction error; the instruction table (model weights) is only updated (via LoRA) if the error exceeds a specific threshold, ensuring the machine is "learning" rather than "recalling". (Addresses Alan Turing Review: 2026-05-19).
- [ ] T059 [FR-002] Implement **Worked Dialogue Example Generator** in `src/eval/example_generator.py`: Create a script that outputs a detailed, step-by-step trace of a single Socratic dialogue, including the model's internal state changes and attention weights before and after the critique. **Verification**: Generate a markdown report `data/results/worked_example_trace.md` showing the evolution of attention patterns across the dialogue rounds. (Addresses Alan Turing Review: 2026-05-30).
- [ ] T060 [FR-003] Implement **Productive Ignorance Metric** in `src/utils/ignorance_metrics.py`: Define and calculate a metric for "productive ignorance" where the model explicitly flags the limits of its own context or confidence. **Verification**: The metric must output a score based on the frequency and quality of "I don't know" or uncertainty flags generated by the model during the dialogue, preventing confident errors. (Addresses Dan Rockmore Review: 2026-05-31).
- [ ] T061 [FR-003] Implement **System 2 Calibration Checkpoint** in `src/data/calibration_checkpoint.py`: Insert a step where the model must produce a confidence rating and compare it to an objective baseline (e.g., Monte-Carlo estimate) before finalizing an answer. **Verification**: Log the discrepancy between the model's confidence and the objective baseline to `data/results/calibration_log.json`. (Addresses Daniel Kahneman Review: 2026-05-17, 2026-05-19).
- [ ] T062 [FR-003] Implement **Heuristic Randomization** in `src/data/heuristic_randomizer.py`: Randomize the framing of questions or insert "System 2 checkpoints" to mitigate availability heuristics and bias in self-generated questions. **Verification**: Verify that the generated question set exhibits statistical variance in framing that prevents the model from over-emphasizing recent or specific patterns. (Addresses Daniel Kahneman Review: 2026-05-19).
- [ ] T063 [FR-006] Refactor **Problem Statement & Terminology** in `src/utils/docs/update_spec.py`: Update the documentation to explicitly frame the process as "evolutionary pressure" and "negative selection on belief" rather than "self-teaching" or "instruction". **Verification**: Generate a diff report showing the replacement of "teaching" terminology with "selection" terminology in `spec.md` and `research.md`. (Addresses David Krakauer Review: 2026-06-29).

**Checkpoint**: All reviewer concerns regarding origination, operational definitions, and bias mitigation are now addressed.

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and address philosophical/operational clarity from reviews.

- [ ] T042 [P] Run `ruff check` and `black --check` on all `src/` and `tests/` files; fix any linting/formatting errors to achieve zero violations.
- [ ] T049 [P] Run `bash projects/PROJ-582-socratic-transformers-dialogue-based-sel/code/quickstart.sh` (or equivalent command) and verify exit code 0 to confirm all quickstart steps execute without error.
- [ ] T064 [P] Update `research.md` to explicitly distinguish between "engine executing ordered operations" and "origination", noting that AQL and Gap Validation are now implemented features (revising previous deprecation).

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-5)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Revision Resolutions (Phase 8)**: Depends on Foundational phase completion; implements specific reviewer feedback.
- **Philosophical Alignment (Phase 6)**: [DEPRECATED] - No dependencies.
- **Calibration (Phase 7)**: [DEPRECATED] - No dependencies.
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable
- **Revision Resolutions (Phase 8)**: Can start after Foundational (Phase 2); tasks may depend on US1 components (e.g., T056 depends on T012/T046).
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
- **Phase 8 (Revision Resolutions)** tasks can run in parallel with User Stories 2 and 3, provided Foundational tasks are complete.
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
5. Add Revision Resolutions (Phase 8) → Test independently → Deploy/Demo
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1
 - Developer B: User Story 2
 - Developer C: User Story 3
 - Developer D: Revision Resolutions (Phase 8)
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
- **Scope Decision**: Phase 6 (Philosophical Alignment) and Phase 7 (Calibration) are DEPRECATED for the current MVP. The features (AQL, Gap Validator, Attention Shift, Productive Ignorance, Calibration) are now implemented in **Phase 8** to address specific reviewer concerns regarding operational definitions and bias mitigation.
