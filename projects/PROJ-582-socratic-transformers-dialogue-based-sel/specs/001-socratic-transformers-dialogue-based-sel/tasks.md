# Tasks: Socratic Transformers: Dialogue-Based Selection on Belief

**Input**: Design documents from `/specs/582-socratic-transformers-dialogue-based-sel/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each user story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[S]**: Sequential (must follow specific task)
- **[Story]**: Which user story this story belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- Paths shown below assume single project - adjust based on plan.md structure

## Phase 0: Setup & Verification

**Purpose**: Project initialization, data download, and basic structure

- [ ] T001 [P] Initialize project directory structure: Create directory `projects/PROJ-582-socratic-transformers-dialogue-based-sel/code/` and subdirectories `src/`, `data/raw/`, `data/processed/`, `data/results/`, `tests/`, `state/`. **Verification**: Run `cd projects/PROJ-582-socratic-transformers-dialogue-based-sel/code && python -c "import os; paths=['src', 'data/raw', 'data/processed', 'data/results', 'tests', 'state']; assert all(os.path.isdir(p) for p in paths)"` and assert exit code 0.
- [ ] T002 [P] Initialize Python project with dependencies (`transformers`, `peft`, `bitsandbytes`, `datasets`, `scikit-learn`, `pandas`, `pytest`, `tokenizers`, `nltk`, `psutil`, `resource`) in `projects/PROJ-582-socratic-transformers-dialogue-based-sel/code/requirements.txt`. **Verification**: Run `cd projects/PROJ-582-socratic-transformers-dialogue-based-sel/code && grep -q 'transformers' requirements.txt && grep -q 'peft' requirements.txt && grep -q 'bitsandbytes' requirements.txt` and assert exit code 0.
- [ ] T003 [P] Configure linting and formatting tools: Create `pyproject.toml` and `ruff.toml` in `projects/PROJ-582-socratic-transformers-dialogue-based-sel/code/`. **Verification**: Run `cd projects/PROJ-582-socratic-transformers-dialogue-based-sel/code && pip install -r requirements.txt && (if [ -d src ] || [ -d tests ]; then ruff check src/ tests/; else echo "No source files to check"; fi)` and verify exit code 0.
- [ ] T012 [P] Implement dataset downloader in `src/data/download.py` fetching GSM8K/MATH via HuggingFace `datasets.load_dataset` (real data requirement). **Logic**: Ensure `state/` directory is created if it doesn't exist before writing. **Verification**: Run `cd projects/PROJ-582-socratic-transformers-dialogue-based-sel/code && python src/data/download.py` and verify `state/artifact_hashes.yaml` exists and contains SHA-256 checksums for downloaded files. **Dependency**: None.
- [ ] T010 [FR-001] [S] Implement `verify_datasets.py` in `src/data/verify_datasets.py`: Validate checksums in `state/artifact_hashes.yaml` against raw data files in `data/raw/`. **Verification**: Run `cd projects/PROJ-582-socratic-transformers-dialogue-based-sel/code && python src/data/verify_datasets.py` and assert exit code 0 only if checksums match the recorded manifest. **Dependency**: Requires T012 (Data Download) to have downloaded data and generated the manifest first. **Note**: This task must complete after T012 (Data Download) to ensure data integrity.

---

## Phase 1: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T005 [P] Implement structured logging utility in `src/utils/logging.py` to handle degenerate dialogue events as JSON lines. **Schema**: Events must follow `{"event_type": str, "timestamp": str, "details": dict}`. **Verification**: Run `cd projects/PROJ-582-socratic-transformers-dialogue-based-sel/code && python -c "from src.utils.logging import log_event; log_event('test'); assert os.path.exists('test.log'); import json; [json.loads(line) for line in open('test.log')]"`.
- [ ] T006 [P] Setup environment configuration management for random seeds and model paths in `src/utils/config.py`. **Requirement**: Define a Python dictionary with the following keys and default values: `CRITIC_MODEL_ID` (required string, no default - must be set in environment or config file to allow experimental flexibility per FR-003), `BASE_MODEL_ID` (required string, no default), `QUESTION_BANK_PATH=None`, `ADVERSARIAL_PROMPT_TEMPLATE='Identify logical contradictions in: {answer}'`, `SELECTION_THRESHOLD=0.85`, `RANDOM_SEED=42`. **Note**: The model IDs are required configuration; the system must allow configuration to use any model that supports 4-bit quantization and fits in limited RAM per FR-003. **Verification**: Run `cd projects/PROJ-582-socratic-transformers-dialogue-based-sel/code && PYTHONPATH=src python -c "from src.utils.config import CRITIC_MODEL_ID; assert CRITIC_MODEL_ID is not None and isinstance(CRITIC_MODEL_ID, str)"` and assert exit code 0.
- [ ] T007 [P] Implement base model loader utility in `src/utils/model_loader.py` supporting 4-bit quantization via `bitsandbytes` (CPU backend). **Verification**: Run `cd projects/PROJ-582-socratic-transformers-dialogue-based-sel/code && PYTHONPATH=src python -c "from src.utils.model_loader import load_model; load_model()"` and assert exit code 0.
- [ ] T008 [P] Implement metric utility in `src/utils/metrics.py` for standard accuracy and loss calculations. **Verification**: Run `cd projects/PROJ-582-socratic-transformers-dialogue-based-sel/code && PYTHONPATH=src python -c "from src.utils.metrics import accuracy, loss; assert callable(accuracy); assert callable(loss)"`.
- [ ] T046 [FR-002] Implement Frozen Critic Model loader in `src/data/critic_loader.py`: acquire a frozen, pre‑trained small model that fits in available memory with 4-bit quantization. **Logic**: The specific model ID must be read from `src/utils/config.py` (key `CRITIC_MODEL_ID`) to allow for reproducibility and updates. This model serves as the *dynamic identification of logical contradictions* required by FR‑002, acting as the adversarial critique mechanism. The model is frozen in parameters but dynamic in output (generates different critiques for different inputs). **Verification**: Assert `model.requires_grad = False`, verify the model loads successfully from HuggingFace (cached) using the config ID, and confirm the model architecture matches the config. **Dynamic Check**: Run `cd projects/PROJ-582-socratic-transformers-dialogue-based-sel/code && PYTHONPATH=src python -c "from src.data.critic_loader import load_frozen_critic; m=load_frozen_critic(); c1=m('Contradiction A'); c2=m('Contradiction B'); assert c1 != c2"` to verify output changes with input.
- [ ] T015 [FR-007] [P] Implement ablation utility in `src/data/ablation_utils.py`:
 1. **Token Count**: Implement `calculate_token_count(text)` using the tokenizer from the base model (defined in `config.py` from T006).
 2. **Similarity**: Implement `calculate_similarity(text_a, text_b)` using `scikit-learn`'s TfidfVectorizer and cosine similarity to ensure CPU safety and compliance with FR-003 (7GB RAM limit).
 3. **Verification**: Run `cd projects/PROJ-582-socratic-transformers-dialogue-based-sel/code && PYTHONPATH=src python -c "from src.data.ablation_utils import calculate_token_count, calculate_similarity; assert calculate_token_count('test') > 0; assert 0 <= calculate_similarity('a', 'a') <= 1"` and assert exit code 0. **Dependency**: Requires `scikit-learn` (from T002).
- [ ] T050 [Utility] [P] Implement Deterministic Question Mapper in `src/data/question_mapper.py`:
 1. **Purpose**: Address **Ada Lovelace** constraints by ensuring no "spontaneous origination" of questions.
 2. **Logic**: Implement a function `map_index_to_question(dataset, index, seed)` that retrieves a question from the GSM8K/MATH dataset using a strict, deterministic integer index. This replaces any logic that might attempt to "generate" a question from scratch.
 3. **Formal Language**: Define a static set of admissible prompt templates (e.g., "Solve: {question_text}") in `config.py` that are applied to the retrieved question.
 4. **Verification**: Run `cd projects/PROJ-582-socratic-transformers-dialogue-based-sel/code && PYTHONPATH=src python -c "from src.data.question_mapper import map_index_to_question; q1 = map_index_to_question('gsm8k', 0, seed=42); q2 = map_index_to_question('gsm8k', 0, seed=42); assert q1 == q2; print('Pass')"` and assert exit code 0. **Dependency**: T012.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 2: User Story 1 - Adversarial Dialogue Data Generation (Priority: P1) 🎯 MVP

**Goal**: Generate static QA tuples and Socratic dialogue tuples (question, answer, critique, revised_answer) from source datasets using a deterministic, non‑origination‑compliant process.

**Independent Test**: Run the generation script on a small subset of samples and verify the output files contain static tuples, dialogue tuples with critique fields populated, and ablation tuples with neutral placeholders.

### Implementation for User Story 1

- [ ] T045a [Story US1] [S] Write schema validation test in `tests/contract/test_schemas.py`: implement `test_validate_dialogue_schema` to assert JSONL records contain `question`, `initial_answer`, `critique`, and `revised_answer` fields, matching the spec's tuple structure. **Schema Definition**: Records must contain exactly these keys: `question` (str), `initial_answer` (str), `critique` (str), `revised_answer` (str). **Verification**: Run `cd projects/PROJ-582-socratic-transformers-dialogue-based-sel/code && pytest tests/contract/test_schemas.py` (expected to fail initially as T014 is not implemented). **Note**: This test is written BEFORE implementation (T014) to enforce TDD. **Execution**: Code implementation is parallel-safe (can be written while T014 is written), but execution logically follows T014. **Dependency**: None.
- [ ] T013 [FR-001] [P] Implement static QA extractor in `src/data/static_extractor.py` to generate the baseline dataset (question, answer) from downloaded sources for comparative study (FR-001). **Logic**: Accept a `--seed` argument to ensure reproducibility. **Output**: `data/processed/seeds/{seed}/static_tuples.jsonl`. **Verification**: Assert output file exists and contains valid JSONL with `question` and `answer` keys.
- [ ] T014 [FR-001] [FR-002] Implement self‑critique generator in `src/data/generate_dialogue.py` that:
 1. **Prerequisites**: Depends on T012 (data), T046 (model), T006 (config), T015 (Token/Sim utility), **T050 (Question Mapper)**.
 2. **Load Model**: Loads the **frozen Critic Model** instance produced by T046 via `load_frozen_critic()`.
 3. **Select Question**: Uses **T050** to retrieve a question from GSM8K/MATH using a deterministic index. **Strictly forbids** any logic that generates a question de novo.
 4. **Generate Initial Answer**: Generates an initial answer using the Base Model (Temperature=0.7, configurable in `config.py`).
 5. **Generate Critique**: Generates a critique by prompting the frozen Critic Model to "Identify logical contradictions, unsupported assumptions, or high‑probability errors in the following answer: [ANSWER]. Output only the critique."
 6. **Generate Revised Answer (Negative Selection)**:
 - Generates K=5 candidate answers using Temperature=0.7.
 - For each candidate, computes semantic similarity (via `scikit-learn` TF-IDF cosine similarity as implemented in T015) between the **entire critique text** and the candidate answer.
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
 8. **Verification**: Run `cd projects/PROJ-582-socratic-transformers-dialogue-based-sel/code && python src/data/generate_dialogue.py --limit 5 --seed 42` and assert that the output file `data/processed/seeds/42/dialogue_tuples.jsonl` exists, contains valid JSONL, has a line count > 0, and that for generated tuples, the similarity score between the rejected candidates and the critique is > threshold, and the selected candidate's similarity is < threshold. **Core Logic Check**: Assert that for generated tuples, the similarity score between the rejected candidates and the critique is > threshold, and the selected candidate's similarity is < threshold.
 9. **Output**: `data/processed/seeds/{seed}/dialogue_tuples.jsonl`.
- [ ] T045b [Story US1] [S] Run schema validation test: Execute `cd projects/PROJ-582-socratic-transformers-dialogue-based-sel/code && pytest tests/contract/test_schemas.py` after T014 is implemented. **Verification**: Assert exit code 0. **Dependency**: T014.
- [ ] T015b [FR-007] [P] Implement ablation data generator in `src/data/ablation.py` replacing critique text with neutral placeholder text of equivalent **token length** (FR-007). **Logic**:
 - **Placeholder Generation**:
 - Load the tokenizer from the Base Model (defined in `config.py` from T006).
 - Tokenize the string `"[NEUTRAL]"` using this tokenizer.
 - Repeat the resulting token ID sequence until the total token count matches the original critique's token count (using `calculate_token_count` from T015).
 - Decode the token IDs back to text to form the placeholder string.
 - **Regeneration Loop**: If the original dialogue tuple (from T014) required critique regeneration, apply the same placeholder generation to the final accepted critique.
 - **Replacement**: Replace the semantic content of the original critique with the generated placeholder.
 - **Output**: `data/processed/seeds/{seed}/ablation_tuples.jsonl`.
 **Verification**: Assert that the token count of the generated placeholder matches the original critique's token count within ±1 token. **Dependency**: T014, T045b.

**Checkpoint**: At this point, User Story 1 is fully functional for Static, Dialogue, and Ablation tuples. **Note**: User Story 2 (Training) requires T015b (Ablation) to be complete as well. T015b is a US1 task that enables US2. Phase 2 must be fully complete before Phase 3 (US2) can begin.

---

## Phase 3: User Story 2 - CPU‑Constrained Fine‑Tuning and Evaluation (Priority: P2)

**Goal**: Fine‑tune the base model on both datasets using LoRA and evaluate performance on held‑out reasoning benchmarks within free‑tier compute limits.

**Independent Test**: Execute the training pipeline on a single random seed and verify it completes within the time budget and produces evaluation metrics.

### Implementation for User Story 2

- [ ] T020 [FR-003] [P] Implement LoRA configuration in `src/train/lora_config.py` with `batch_size ≤ 2`, `gradient_accumulation_steps = 4`, and 4‑bit quantization (FR‑003).
- [ ] T021a [FR-008] [P] Implement CPU‑safe training loop in `src/train/train_loop.py` with a configurable hard timeout using `signal.signal(signal.SIGALRM, timeout_handler)`. **Logic**: Implement memory monitoring using `psutil` to sample the training process RSS at regular intervals; log warnings if RSS > 6.5GB. **Test File**: Create `tests/unit/test_timeout.py` with function `test_timeout_handler` that mocks `signal.SIGALRM` to trigger timeout. **Dependency**: None.
- [ ] T021b [FR-008] [S] Run Timeout Test: Execute `cd projects/PROJ-582-socratic-transformers-dialogue-based-sel/code && pytest tests/unit/test_timeout.py::test_timeout_handler` to verify it exits with code 1, logs "TIMEOUT", and saves the last checkpoint. **Dependency**: T021a.
- [ ] T055 [FR-008] [P] Implement OOM Fallback Verification in `tests/unit/test_oom.py`: Create a test that simulates a real memory exhaustion condition using `resource.setrlimit` (or `ulimit` in shell) to enforce a hard memory limit that triggers the OS OOM killer or Python MemoryError, and verifies the training script exits with an out-of-memory termination code or the specific OOM error message. **Verification**: Run `cd projects/PROJ-582-socratic-transformers-dialogue-based-sel/code && pytest tests/unit/test_oom.py` and assert that the script handles the OOM condition gracefully by saving the partial checkpoint and exiting with a non-zero code.
- [ ] T047a [P] Implement Condition A (Selection) training run in `src/train/run_selection_train.py`: Fine‑tune model on `data/processed/seeds/{seed}/dialogue_tuples.jsonl`. **Logic**: Accept a `--seed` argument. **Output**: `data/results/seeds/{seed}/checkpoint_selection.pt`. **Dependency**: T014.
- [ ] T047b [P] Implement Condition B (Ablation) training run in `src/train/run_ablation_train.py`: Fine‑tune model on `data/processed/seeds/{seed}/ablation_tuples.jsonl` (from T015b). **Logic**: Accept a `--seed` argument. **Output**: `data/results/seeds/{seed}/checkpoint_ablation.pt`. **Dependency**: T015b.
- [ ] T047c [P] Implement Condition C (Static) training run in `src/train/run_static_train.py`: Fine‑tune model on `data/processed/seeds/{seed}/static_tuples.jsonl` (from T013). **Logic**: Accept a `--seed` argument. **Output**: `data/results/seeds/{seed}/checkpoint_static.pt`. **Dependency**: T013.
- [ ] T047d [FR-006] Implement Unified Evaluation in `src/eval/evaluate.py`: **Prerequisites**: T047a, T047b, T047c must be completed successfully for a specific seed. **Logic**: Load checkpoints from T047a‑c (`checkpoint_selection.pt`, `checkpoint_ablation.pt`, `checkpoint_static.pt`) for a given seed. Run evaluation on GSMK test split and MMLU STEM subset for each. **Error Handling**: If any checkpoint is missing, the script MUST exit with non-zero code. **Output**: `data/results/seeds/{seed}/metrics.json` containing **accuracy** (and loss) for all three conditions. **Verification**: Assert that `metrics.json` contains accuracy keys for all three conditions and that the GSM8K test split size matches the dataset definition.
- [ ] T048 [P] Implement Checksum Manifest Generator in `src/utils/checksum_manifest.py`: Generate SHA‑256 hashes for all checkpoint files (`checkpoint_*.pt`) and append them to `state/artifact_hashes.yaml`. **Verification**: Run script and verify `state/artifact_hashes.yaml` contains entries for all three checkpoint files with valid hashes.
- [ ] T051 [FR-002] [P] Implement **Attention Pattern Analysis** in `src/eval/attention_analysis.py`:
 1. **Purpose**: Address **Alan Turing**'s request for empirical evidence of state change.
 2. **Logic**: Load the trained model and a held-out sample. Run inference with `return_dict_in_return=True` to capture attention weights.
 3. **Comparison**: Compare attention heatmaps of the "Selection" condition vs. "Static" condition on the same questions.
 4. **Metric**: Calculate the cosine similarity between attention distributions before and after the Socratic critique step.
 5. **Output**: Append a section `attention_shift_metrics` to `data/results/seeds/{seed}/metrics.json`.
 6. **Verification**: Assert that the output file contains a `attention_shift` key with a numeric value. **Dependency**: T047d.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 4: User Story 3 - Statistical Analysis and Ablation (Priority: P3)

**Goal**: Perform statistical comparison between conditions and ablate the self‑critique component to isolate its effect.

**Independent Test**: Run the analysis script on the logged metrics from multiple seeds and verify the statistical test output.

### Implementation for User Story 3

- [ ] T060 [FR-006] [P] Implement Multi-seed Data Generation Orchestrator in `src/data/run_multi_seed_gen.py`: **Logic**: Iterate over multiple distinct random seeds.. For each seed, run the data generation pipeline (T013, T014, T015b) with the `--seed` argument to produce distinct sets of Static, Dialogue, and Ablation tuples. **Output**: `data/processed/seeds/{seed}/static_tuples.jsonl`, etc. **Verification**: Assert that 5 distinct directories exist under `data/processed/seeds/` and each contains valid JSONL files.
- [ ] T061 [FR-006] [P] Implement Multi-seed Training Orchestrator in `src/train/run_multi_seed_train.py`: **Logic**: Iterate over the 5 seeds generated by T060. For each seed, run the training pipeline (T047a, T047b, T047c) with the `--seed` argument to produce multiple distinct sets of checkpoints. **Output**: `data/results/seeds/{seed}/checkpoint_*.pt`. **Verification**: Assert that 5 distinct checkpoint sets exist.
- [ ] T062 [FR-006] [P] Implement Multi-seed Evaluation Aggregation in `src/eval/run_multi_seed_eval.py`: **Logic**: Iterate over the 5 seeds. For each seed, run evaluation (T047d) to generate `metrics.json`. Aggregate all 5 `metrics.json` files into a single `data/results/metrics_aggregated.json`. **Verification**: Assert that `metrics_aggregated.json` contains a distribution of accuracy scores for each condition.
- [ ] T033a [FR-006] [P] Create `src/utils/stats_analysis.py`: **Deliverable**: Implement `run_t_test(condition_a, condition_b)` for Independent t‑tests (Selection vs. Ablation, Selection vs. Static) with Bonferroni correction (α = 0.025).
- [ ] T033b [P] Implement MDES and Effect Size calculation in `src/utils/stats_analysis.py`. **Deliverable**: Implement `calculate_mdes()` and `calculate_effect_size()`. **Stop‑Rule**: If effect size < MDES, return "Inconclusive due to power".
- [ ] T063 [FR-006] [P] Implement Statistical Comparison Report Generator in `src/eval/generate_final_report.py`: **Logic**: Load `metrics_aggregated.json` (from T062), run t-tests (Ta), calculate effect sizes (T033b), and generate the final report. **Output**: `data/results/final_report.md`. **Verification**: Assert that `final_report.md` contains p-values, effect sizes, and a conclusion on the efficacy of negative selection.
- [ ] T059 [P] Create `quickstart.sh` in `projects/PROJ-582-socratic-transformers-dialogue-based-sel/code/`: **Logic**: Create a bash script that installs dependencies and runs the full pipeline (T012, T013, T014, T015b, T020, T047a-c, T047d, T033a-c). **Verification**: Run `cd projects/PROJ-582-socratic-transformers-dialogue-based-sel/code && bash quickstart.sh` and verify exit code 0.
- [ ] T049 [P] Run `bash projects/PROJ-582-socratic-transformers-dialogue-based-sel/code/quickstart.sh` (or equivalent command) and verify exit code 0 to confirm all quickstart steps execute without error. **Dependency**: T059. **Verification**: Run `cd projects/PROJ-582-socratic-transformers-dialogue-based-sel/code && bash quickstart.sh` and verify exit code 0.

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
- Once Foundational phase completes, all user stories can start in parallel (if staffed)
- All tests for a user story marked [P] can run in parallel (code implementation)
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

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
- [S] tasks = sequential (must follow specific task)
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
- **Token Count**: T015 now explicitly uses the tokenizer from T006.
- **Constraint Preservation**: T014 now uses stochastic temperature (0.7) and streams full datasets, ensuring compliance with the 'Variation' and 'Negative Selection' requirements.
- **Ordering**: T045a (Write) -> T014 (Impl) -> T045b (Run) -> T015b (Ablation). Validation happens before ablation generation.
- **Quality Gate**: T014 now explicitly implements the Constitution Check Principle VII (Adversarial Dialogue Quality) gate (length, BLEU, revision checks) as a mandatory part of the generation loop.
- **Model Flexibility**: T006 defines model IDs as configurable strings (no hard-coded defaults), allowing for experimental flexibility as per FR-003.
- **Execution Order**: Phase 2 execution order is strictly: T045a (Write) -> T014 (Impl) -> T045b (Run) -> T015b (Ablation).
- **Negative Selection Logic**: T014 Step 6 strictly implements "elimination of error space" (rejecting candidates similar to critique) rather than "selection of a match".
- **Scope Correction**: All unapproved scope creep tasks (T052, T053, T050-T055, T090-T095) have been **REMOVED** and **DELETED** from the task list. Phase 6 has been removed entirely.
- **Dependency Correction**: T015b moved to Phase 2 to follow T014.
- **Manifest Logic**: T012 generates the manifest; T010 validates it. Circular dependency resolved.
- **Ada Lovelace Constraint**: Data generation now occurs directly from the loaded datasets via `generate_dialogue.py` using deterministic indexing, satisfying non-origination constraints without a separate "Question Bank" task. **T050** explicitly enforces this by using a deterministic mapper.
- **Turing's Knowledge Gap**: Removed separate verification task; logic integrated into T014's Quality Gate. **T051** adds the requested attention analysis.
- **Rockmore's Productive Ignorance**: Removed separate metric; **T053** removed.
- **Kahneman's Calibration**: Removed separate metric; **T052** removed.
- **Ordering**: T014 -> T045b -> T015b -> T047b. Validation happens before ablation generation.
- **Quality Gate**: T014 now explicitly implements the Constitution Check Principle VII (Adversarial Dialogue Quality) gate (length, BLEU, revision checks) as a mandatory part of the generation loop.
- **Krakauer's Selection**: The problem statement and T014 logic now explicitly frame the process as "Negative Selection on Belief" (evolutionary pressure) rather than "Self-Teaching", aligning with the review.
- **Multi-seed**: T060, T061, T062 explicitly handle the 5-seed requirement for statistical power.
- **OOM Verification**: T055 explicitly verifies the OOM fallback mechanism with a real stress test using `resource.setrlimit`.
- **Quickstart**: T059 explicitly creates the `quickstart.sh` file.
- **Dynamic Critic**: T046 verification now checks for dynamic output changes.
- **Parallel/Sequential**: T045a is now [S] to reflect TDD execution order.
- **Path Handling**: All verification commands now explicitly `cd` to the project directory.
- **File Creation**: All tasks now explicitly describe the creation of required files/directories.
- **Scope**: Removed T052, T053. Added T063 for FR-006 compliance.
- **Tagging**: T050 is now [Utility].
- **Dependency**: T015 is now a single task merging T015a/T015c.
- **Verification**: T014 verification now checks semantic distance.
- **Verification**: T021 verification now explicitly creates the test file (T021a) and runs it (T021b).
- **Verification**: T050 verification now specifies exact command.
- **Verification**: T046 verification now checks dynamic output.
- **Verification**: T055 verification now checks real OOM handling with `resource.setrlimit`.
- **Verification**: T001-T003, T012, T010, T006, T014, T021, T050, T046, T055, T049, T059, T060, T061, T062, T063 all updated for executability.
- **Checkpoint Clarification**: Phase 2 Checkpoint explicitly states T015b is a US1 task that enables US2. Phase 4 Checkpoint explicitly states T060 must complete before T061.
- **T047d Logic**: T047d now strictly requires checkpoints to exist and exits with non-zero code if missing. T062 explicitly runs T047d 5 times.