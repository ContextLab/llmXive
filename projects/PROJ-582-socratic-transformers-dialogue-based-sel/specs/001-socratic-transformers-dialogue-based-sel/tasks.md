# Tasks: Socratic Transformers: Dialogue-Based Selection on Belief

**Input**: Design documents from `/specs/582-socratic-transformers-dialogue-based-sel/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each user story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this story belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- Paths shown below assume single project - adjust based on plan.md structure

## Phase 0: Setup & Verification

**Purpose**: Project initialization, data download, and basic structure

- [ ] T001 [P] Initialize project directory structure: Create directory `projects/PROJ-582-socratic-transformers-dialogue-based-sel/code/` and subdirectories `src/`, `data/raw/`, `data/processed/`, `data/results/`, `tests/`. **Verification**: Run `python -c "import os; paths=['projects/PROJ-582-socratic-transformers-dialogue-based-sel/code/src', 'projects/PROJ-582-socratic-transformers-dialogue-based-sel/code/data/raw']; assert all(os.path.isdir(p) for p in paths)"` and assert exit code 0.
- [ ] T002 [P] Initialize Python project with dependencies (`transformers`, `peft`, `bitsandbytes`, `datasets`, `scikit-learn`, `pandas`, `pytest`, `tokenizers`, `nltk`, `psutil`) in `projects/PROJ-582-socratic-transformers-dialogue-based-sel/code/requirements.txt`. **Verification**: Run `grep -q 'transformers' requirements.txt && grep -q 'peft' requirements.txt && grep -q 'bitsandbytes' requirements.txt` and assert exit code 0.
- [ ] T003 [P] Configure linting and formatting tools: Create `pyproject.toml` and `ruff.toml` in `projects/PROJ-582-socratic-transformers-dialogue-based-sel/code/`. **Verification**: Run `cd projects/PROJ-582-socratic-transformers-dialogue-based-sel/code && pip install -r requirements.txt && (if [ -d src ] || [ -d tests ]; then ruff check src/ tests/; else echo "No source files to check"; fi)` and verify exit code 0.
- [ ] T012 [P] Implement dataset downloader in `src/data/download.py` fetching GSM8K/MATH via HuggingFace `datasets.load_dataset` (real data requirement). **Verification**: Generate SHA-256 checksums for downloaded files and write them to `state/artifact_hashes.yaml`. **Dependency**: None.
- [ ] T010 [FR-001] Implement `verify_datasets.py` in `src/data/verify_datasets.py`: Validate checksums in `state/artifact_hashes.yaml` against raw data files in `data/raw/`. **Verification**: Run script and assert exit code 0 only if checksums match the recorded manifest. **Dependency**: Requires T012 (Data Download) to have downloaded data and generated the manifest first. **Note**: This task must complete after T012 (Data Download) to ensure data integrity.

---

## Phase 1: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T005 [P] Implement structured logging utility in `src/utils/logging.py` to handle degenerate dialogue events as JSON lines. **Schema**: Events must follow `{"event_type": str, "timestamp": str, "details": dict}`. **Verification**: Run `python -c "from src.utils.logging import log_event; log_event('test'); assert os.path.exists('test.log'); import json; [json.loads(line) for line in open('test.log')]"`.
- [ ] T006 [P] Setup environment configuration management for random seeds and model paths in `src/utils/config.py`. **Requirement**: Define a Python dictionary with the following keys and default values: `CRITIC_MODEL_ID` (required string, no default - must be set in environment or config file to allow experimental flexibility per FR-003), `BASE_MODEL_ID` (required string, no default), `QUESTION_BANK_PATH=None`, `ADVERSARIAL_PROMPT_TEMPLATE='Identify logical contradictions in: {answer}'`, `SELECTION_THRESHOLD=0.85`, `RANDOM_SEED=42`. **Note**: The model IDs are required configuration; the system must allow configuration to use any model that supports 4-bit quantization and fits in 7GB RAM per FR-003. **Verification**: Run `python -c "from src.utils.config import CRITIC_MODEL_ID; assert CRITIC_MODEL_ID is not None and isinstance(CRITIC_MODEL_ID, str)"` and assert exit code 0.
- [ ] T007 [P] Implement base model loader utility in `src/utils/model_loader.py` supporting 4-bit quantization via `bitsandbytes` (CPU backend). **Verification**: Run `python -c "from src.utils.model_loader import load_model; load_model()"` and assert exit code 0.
- [ ] T008 [P] Implement metric utility in `src/utils/metrics.py` for standard accuracy and loss calculations. **Verification**: Run `python -c "from src.utils.metrics import accuracy, loss; assert callable(accuracy); assert callable(loss)"`.
- [ ] T046 [FR-002] Implement Frozen Critic Model loader in `src/data/critic_loader.py`: acquire a frozen, pre‑trained small model that fits in available memory with ‑bit quantization. **Logic**: The specific model ID must be read from `src/utils/config.py` (key `CRITIC_MODEL_ID`) to allow for reproducibility and updates. This model serves as the *dynamic identification of logical contradictions* required by FR‑002, acting as the adversarial critique mechanism. **Verification**: Assert `model.requires_grad = False`, verify the model loads successfully from HuggingFace (cached) using the config ID, and confirm the model architecture matches the config.
- [ ] T015a [FR-007] [P] Implement token counter utility in `src/data/ablation_utils.py`:
 1. **Token Count**: Implement `calculate_token_count(text)` using the tokenizer from the base model (defined in `config.py` from T006).
 2. **Verification**: Run `python -c "from src.data.ablation_utils import calculate_token_count; assert calculate_token_count('test') > 0"` and assert exit code 0. **Dependency**: Requires `scikit-learn` (from T002).
- [ ] T015c [FR-007] [P] Implement similarity utility in `src/data/ablation_utils.py`:
 1. **Similarity**: Implement `calculate_similarity(text_a, text_b)` using `scikit-learn`'s TfidfVectorizer and cosine similarity to ensure CPU safety and compliance with FR-003 (7GB RAM limit).
 2. **Verification**: Run `python -c "from src.data.ablation_utils import calculate_similarity; assert 0 <= calculate_similarity('a', 'a') <= 1"` and assert exit code 0. **Dependency**: Requires `scikit-learn` (from T002).

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 2: User Story 1 - Adversarial Dialogue Data Generation (Priority: P1) 🎯 MVP

**Goal**: Generate static QA tuples and Socratic dialogue tuples (question, answer, critique, revised_answer) from source datasets using a deterministic, non‑origination‑compliant process.

**Independent Test**: Run the generation script on a small subset of samples and verify the output files contain static tuples, dialogue tuples with critique fields populated, and ablation tuples with neutral placeholders.

### Implementation for User Story 1

- [ ] T045a [Story US1] [P] Write schema validation test in `tests/contract/test_schemas.py`: implement `test_validate_dialogue_schema` to assert JSONL records contain `question`, `initial_answer`, `critique`, and `revised_answer` fields, matching the spec's tuple structure. **Schema Definition**: Records must contain exactly these keys: `question` (str), `initial_answer` (str), `critique` (str), `revised_answer` (str). **Verification**: Run `pytest tests/contract/test_schemas.py` (expected to fail initially as T014 is not implemented). **Note**: This test is written BEFORE implementation (T014) to enforce TDD. **Execution**: Code implementation is parallel-safe (can be written while T014 is written), but execution logically follows T014. **Dependency**: None.
- [ ] T013 [FR-001] [P] Implement static QA extractor in `src/data/static_extractor.py` to generate the baseline dataset (question, answer) from downloaded sources for comparative study (FR-001). **Output**: `data/processed/static_tuples.jsonl`. **Verification**: Assert output file exists and contains valid JSONL with `question` and `answer` keys.
- [ ] T014 [FR-001] [FR-002] Implement self‑critique generator in `src/data/generate_dialogue.py` that:
 1. **Prerequisites**: Depends on T012 (data), T046 (model), T006 (config), T015a (Token utility), T015c (Similarity utility).
 2. **Load Model**: Loads the **frozen Critic Model** instance produced by T046 via `load_frozen_critic()`.
 3. **Select Question**: Loads questions directly from the GSM8K/MATH datasets (via T012) using a deterministic index mapping (e.g., `dataset[i]`) to satisfy Ada Lovelace constraints (no spontaneous origination).
 4. **Generate Initial Answer**: Generates an initial answer using the Base Model (Temperature=0.7, configurable in `config.py`).
 5. **Generate Critique**: Generates a critique by prompting the frozen Critic Model to "Identify logical contradictions, unsupported assumptions, or high‑probability errors in the following answer: [ANSWER]. Output only the critique."
 6. **Generate Revised Answer (Negative Selection)**:
 - Generates K=5 candidate answers using Temperature=0.7.
 - For each candidate, computes semantic similarity (via `scikit-learn` TF-IDF cosine similarity as implemented in T015c) between the **entire critique text** and the candidate answer.
 - **Negative Selection Logic**:
   - If similarity > threshold (defined in `config.py`), the candidate is **REJECTED** (it shares the error belief identified in the critique).
   - If **all** K candidates are rejected, the tuple is **DISCARDED** and the next question is processed.
   - If at least one candidate is NOT rejected, select the candidate with the **LOWEST** similarity to the critique (furthest from the error belief).
 - **Fallback Rule**: If **no** candidate passes after N=5 regeneration attempts for the critique itself, **discard the tuple** and proceed to the next question. Do NOT write failed tuples to the output file.
 7. **Quality Gate & Regeneration Loop (Constitution Check Principle VII)**:
 - **Gate Logic**: Discards critiques that are empty, lack logical keywords, or have mean log‑probability < 0.6 (confidence check).
 - **Triviality Check**: Discards critiques that allow the model to solve the problem without negative selection (i.e., if the critique contains the answer).
 - **Regeneration**: If the critique fails, re‑prompts the Critic Model up to N=5 times for the same question.
 - After N attempts, if a satisfactory critique is still not produced, logs the question as `SKIPPED` and proceeds to the next question **without writing invalid data**.
 - **Verification**: Assert that the generated tuples satisfy the quality gate (length > 20 tokens, BLEU < 0.8, revised != initial).
 8. **Integration**: Produces output conforming to the schema validated by T045a/T045b.
 9. **Output**: `data/processed/dialogue_tuples.jsonl`.
 **Verification**: Run a sample batch and assert that the output file exists, contains valid JSONL, and has a line count > 0. Run T045b to validate schema.
- [ ] T045b [Story US1] [P] Run schema validation test: Execute `pytest tests/contract/test_schemas.py` after T014 is implemented. **Verification**: Assert exit code 0. **Dependency**: T014.
- [ ] T015b [FR-007] [P] Implement ablation data generator in `src/data/ablation.py` replacing critique text with neutral placeholder text of equivalent **token length** (FR-007). **Logic**:
 - **Placeholder Generation**:
   - Load the tokenizer from the Base Model (defined in `config.py` from T006).
   - Tokenize the string `"[NEUTRAL]"` using this tokenizer.
   - Repeat the resulting token ID sequence until the total token count matches the original critique's token count (using `calculate_token_count` from T015a).
   - Decode the token IDs back to text to form the placeholder string.
 - **Regeneration Loop**: If the original dialogue tuple (from T014) required critique regeneration, apply the same placeholder generation to the final accepted critique.
 - **Replacement**: Replace the semantic content of the original critique with the generated placeholder.
 - **Output**: `data/processed/ablation_tuples.jsonl`.
 **Verification**: Assert that the token count of the generated placeholder matches the original critique's token count within ±1 token. **Dependency**: T014, T045b.

**Checkpoint**: At this point, User Story 1 is fully functional for Static, Dialogue, and Ablation tuples. **Note**: User Story 2 (Training) requires T015b (Ablation) to be complete as well.

---

## Phase 3: User Story 2 - CPU‑Constrained Fine‑Tuning and Evaluation (Priority: P2)

**Goal**: Fine‑tune the base model on both datasets using LoRA and evaluate performance on held‑out reasoning benchmarks within free‑tier compute limits.

**Independent Test**: Execute the training pipeline on a single random seed and verify it completes within the time budget and produces evaluation metrics.

### Implementation for User Story 2

- [ ] T020 [FR-003] [P] Implement LoRA configuration in `src/train/lora_config.py` with `batch_size ≤ 2`, `gradient_accumulation_steps = 4`, and 4‑bit quantization (FR‑003).
- [ ] T021 [FR-008] Implement CPU‑safe training loop in `src/train/train_loop.py` with a configurable hard timeout using `signal.signal(signal.SIGALRM, timeout_handler)`. **Verification**: Implement memory monitoring using `psutil` to sample the training process RSS at regular intervals; log warnings if RSS > 6.5GB. **Timeout Verification**: Run script with `pytest-mock` to patch `signal.SIGALRM` and simulate timeout (avoiding real‑time sleep flakiness). Verify it exits with code 1, logs "TIMEOUT", and saves the last checkpoint. **Failure Handling**: On timeout or OOM, save the last valid checkpoint to `data/results/checkpoint_partial.pt`, log the error, and exit with code 1. Do not auto‑retry. Rely on the execution stage's error handling (which detects the non‑zero exit and re‑runs on GPU). Note: Validation data loading for Early Stopping is [deferred] per plan.md, so this check applies to the training batch processing only.
- [ ] T047a [P] Implement Condition A (Selection) training run in `src/train/run_selection_train.py`: Fine‑tune model on `data/processed/dialogue_tuples.jsonl`. **Output**: `data/results/checkpoint_selection.pt`. **Dependency**: T014.
- [ ] T047b [P] Implement Condition B (Ablation) training run in `src/train/run_ablation_train.py`: Fine‑tune model on `data/processed/ablation_tuples.jsonl` (from T015b). **Output**: `data/results/checkpoint_ablation.pt`. **Dependency**: T015b.
- [ ] T047c [P] Implement Condition C (Static) training run in `src/train/run_static_train.py`: Fine‑tune model on `data/processed/static_tuples.jsonl` (from T013). **Output**: `data/results/checkpoint_static.pt`. **Dependency**: T013.
- [ ] T047d [FR-006] Implement Unified Evaluation in `src/eval/evaluate.py`: **Prerequisites**: T047a, T047b, T047c must be completed successfully. Load checkpoints from T047a‑c (`checkpoint_selection.pt`, `checkpoint_ablation.pt`, `checkpoint_static.pt`). Run evaluation on GSMK test split and MMLU STEM subset for each. **Error Handling**: If any checkpoint is missing, the script should attempt to run the corresponding training script (T047a‑c) if not already run, or exit with non‑zero code if manual intervention is required. **Output**: `data/results/metrics.json` containing **accuracy** (and loss) for all three conditions. **Verification**: Assert that `metrics.json` contains accuracy keys for all three conditions and that the GSM8K test split size matches the dataset definition.
- [ ] T048 [P] Implement Checksum Manifest Generator in `src/utils/checksum_manifest.py`: Generate SHA‑256 hashes for all checkpoint files (`checkpoint_*.pt`) and append them to `state/artifact_hashes.yaml`. **Verification**: Run script and verify `state/artifact_hashes.yaml` contains entries for all three checkpoint files with valid hashes.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 4: User Story 3 - Statistical Analysis and Ablation (Priority: P3)

**Goal**: Perform statistical comparison between conditions and ablate the self‑critique component to isolate its effect.

**Independent Test**: Run the analysis script on the logged metrics from multiple seeds and verify the statistical test output.

### Implementation for User Story 3

- [ ] T033a [FR-006] [P] Create `src/utils/stats_analysis.py`: **Deliverable**: Implement `run_t_test(condition_a, condition_b)` for Independent t‑tests (Selection vs. Ablation, Selection vs. Static) with Bonferroni correction (α = 0.025).
- [ ] T033b [P] Implement MDES and Effect Size calculation in `src/utils/stats_analysis.py`. **Deliverable**: Implement `calculate_mdes()` and `calculate_effect_size()`. **Stop‑Rule**: If effect size < MDES, return "Inconclusive due to power".
- [ ] T033c [P] Create `src/utils/report_generator.py`. **Deliverable**: Implement `generate_stats_report(metrics_json, t_test_results, mdes_results)` to write to `data/results/stats_report.md`.
- [ ] T049 [P] Run `bash projects/PROJ-582-socratic-transformers-dialogue-based-sel/code/quickstart.sh` (or equivalent command) and verify exit code 0 to confirm all quickstart steps execute without error.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 5: Polish & Cross‑Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T042 [P] Run `ruff check` and `black --check` on all `src/` and `tests/` files; fix any linting/formatting errors to achieve zero violations.
- [ ] T075 [P] Final Review of `tasks.md`: Ensure all tasks are logically sequenced and dependencies are correct.

**Note**: All tasks now align with the spec's Core Objectives and Methodology. The "Adversarial Dialogue Quality" gate (Principle VII) is implemented within T014. No unapproved scope creep tasks remain.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 0)**: No dependencies - can start immediately (except T010 which depends on T012)
- **Foundational (Phase 1)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 2‑4)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 1) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 1) - May integrate with US1 but should be independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 1) - May integrate with US1/US2 but should be independently testable

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 1)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel (code implementation)
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 0: Setup
2. Complete Phase 1: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 2: User Story 1
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
- Avoid: vague tasks, same file conflicts, cross‑story dependencies that break independence
- **Data Integrity**: T010 (Data Verification) must complete after T012 (Data Download) to ensure checksums are validated against downloaded data.
- **TDD Principle**: T045a (Schema Validation Test) is written before T014 (Implementation) to enforce test‑first development.
- **Negative Selection**: T014 now implements rejection‑based selection (discard if error present), not best‑of‑N selection. Failed tuples are discarded, not retained.
- **Variation**: T014 now uses Temperature=0.7 (configurable) for initial answer and revised answer candidates to ensure multiple reasoning paths.
- **Fallback**: T014 now includes a clear fallback: if regeneration fails after N attempts, log the question as SKIPPED and proceed. **No invalid data is written**.
- **Algorithm**: T014 now uses `scikit-learn` TF-IDF for semantic similarity checks to ensure CPU safety and compliance with FR-003 (7GB RAM limit).
- **Token Count**: T015a and T015c now explicitly use the tokenizer from T006.
- **Constraint Preservation**: T014 now uses stochastic temperature (0.7) and streams full datasets, ensuring compliance with the 'Variation' and 'Negative Selection' requirements.
- **Ordering**: T045a (Write) -> T014 (Impl) -> T045b (Run) -> T015b (Ablation). Validation happens before ablation generation.
- **Quality Gate**: T014 now explicitly implements the Constitution Check Principle VII (Adversarial Dialogue Quality) gate (length, BLEU, revision checks) as a mandatory part of the generation loop.
- **Model Flexibility**: T006 defines model IDs as configurable strings (no hard-coded defaults), allowing for experimental flexibility as per FR-003.
- **Execution Order**: Phase 2 execution order is strictly: T045a (Write) -> T014 (Impl) -> T045b (Run) -> T015b (Ablation).
- **Negative Selection Logic**: T014 Step 6 strictly implements "elimination of error space" (rejecting candidates similar to critique) rather than "selection of a match".
- **Scope Correction**: All unapproved scope creep tasks (T050-T055, T090-T095) have been **REMOVED** and **DELETED** from the task list. Phase 6 has been removed entirely.
- **Dependency Correction**: T015b moved to Phase 2 to follow T014.
- **Manifest Logic**: T012 generates the manifest; T010 validates it. Circular dependency resolved.
- **Ada Lovelace Constraint**: Data generation now occurs directly from the loaded datasets via `generate_dialogue.py` using deterministic indexing, satisfying non-origination constraints without a separate "Question Bank" task.
- **Turing's Knowledge Gap**: Removed separate verification task; logic integrated into T014's Quality Gate.
- **Rockmore's Productive Ignorance**: Removed separate metric; not in spec.
- **Kahneman's Calibration**: Removed separate metric; not in spec.
- **Ordering**: T014 -> T045b -> T015b -> T047b. Validation happens before ablation generation.
- **Quality Gate**: T014 now explicitly implements the Constitution Check Principle VII (Adversarial Dialogue Quality) gate (length, BLEU, revision checks) as a mandatory part of the generation loop.