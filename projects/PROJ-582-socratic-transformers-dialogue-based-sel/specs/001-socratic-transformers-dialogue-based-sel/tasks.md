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

- [ ] T001 [P] Initialize project directory structure: Create directory `projects/PROJ-582-socratic-transformers-dialogue-based-sel/code/` and subdirectories `src/`, `data/raw/`, `data/processed/`, `data/results/`, `tests/`. Create `.gitkeep` files in data directories. **Verification**: Run `python -c "import os; assert all(os.path.isdir(p) for p in ['projects/PROJ-582-socratic-transformers-dialogue-based-sel/code/src', 'projects/PROJ-582-socratic-transformers-dialogue-based-sel/code/data/raw'])"` and assert exit code 0.
- [ ] T002 [P] Initialize Python project with dependencies in `projects/PROJ-582-socratic-transformers-dialogue-based-sel/code/requirements.txt`. **Required Lines**: `transformers==4.35.0`, `peft==0.7.0`, `bitsandbytes==0.41.0`, `datasets==2.14.0`, `scikit-learn==1.3.0`, `pandas==2.0.0`, `pytest==7.4.0`, `tokenizers==0.14.0`, `nltk==3.8.0`, `psutil==5.9.0`. **Verification**: Run `grep -q 'transformers==4.35.0' requirements.txt` and assert exit code 0.
- [ ] T003 [P] Configure linting and formatting tools: Create `pyproject.toml` and `ruff.toml` in `projects/PROJ-582-socratic-transformers-dialogue-based-sel/code/`. **Content**: `pyproject.toml` must contain `[tool.black] line-length = 88` and `ruff.toml` must contain `target-version = 'py39'`. **Verification**: Run `ruff check. --output-format=concise` and verify exit code 0.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T005 [P] Implement structured logging utility in `src/utils/logging.py` to handle degenerate dialogue events as JSON lines. **Schema**: Events must follow `{"event_type": str, "timestamp": str, "details": dict}`.
- [ ] T006 [P] Setup environment configuration management for random seeds and model paths in `src/utils/config.py`. **Requirement**: Define `GENERATOR_MODEL_ID` (e.g., "google/flan-t5-base") and `CRITIC_MODEL_ID` (e.g., "google/flan-t5-small").
- [ ] T007 [P] Implement base model loader utility in `src/utils/model_loader.py` supporting 4-bit quantization via `bitsandbytes` (CPU backend). **Verification**: Run `python -c "from src.utils.model_loader import load_model; load_model()"` and assert exit code 0.
- [ ] T008 [P] Implement metric utility in `src/utils/metrics.py`. **Deliverable**: Implement `calculate_accuracy(y_true, y_pred)` and `calculate_loss(y_true, y_pred)`. **Verification**: Run `pytest tests/unit/test_metrics.py::test_calculate_accuracy` and assert exit code 0.
- [ ] T012 [P] Implement dataset downloader in `src/data/download.py` fetching GSM8K/MATH via HuggingFace `datasets.load_dataset` (real data requirement). **Verification**: Verify checksums match spec.md verified block. **Dependency**: This task must run BEFORE T010 to provide files for validation.
- [ ] T010 [P] Implement `verify_datasets.py` in `src/data/verify_datasets.py`: Fetch checksums from the `spec.md` 'Verified Datasets' block for GSM8K (`openai/gsm8k`) and MATH (`hendrycks/math`), validate raw data integrity against these static checksums. **Requirement**: This task validates the *downloaded* files from T012 against *pre-computed* checksums defined in `spec.md`. It does NOT generate the manifest; it validates against the spec's known good values. **Dependency**: Must run AFTER T012. **Verification**: Run script and assert exit code 0 only if checksums match the recorded manifest.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Adversarial Dialogue Data Generation (Priority: P1) 🎯 MVP

**Goal**: Generate static QA tuples and Socratic dialogue tuples (question, answer, critique, revised_answer) from source datasets using a deterministic, non-origination-compliant process.

**Independent Test**: Run the generation script on a small subset of samples and verify the output files contain static tuples, dialogue tuples with critique fields populated, and ablation tuples with neutral placeholders.

### Implementation for User Story 1

- [ ] T014a [FR-001] [FR-002] Implement Critique Generation in `src/data/generate_dialogue.py`:
 1. **Prerequisites**: Depends on T012 (data), T006 (config), T007 (model loader).
 2. **Load Models**:
 - Load **Generator Model** (e.g., `google/flan-t5-base`) via `load_model()` from T007.
 - Load **Critic Model** (e.g., `google/flan-t5-small`) via `load_model()` with 4-bit quantization. This model is **frozen** and acts as the external mechanism for selection pressure.
 3. **Select Question**: Iterates directly over the downloaded GSM8K/MATH dataset (no external question bank).
 4. **Generate Initial Answer**: Generates an initial answer using the **Generator Model** (Temperature=0.0).
 5. **Generate Critique**: Generates a critique by prompting the **Critic Model** with the following template:
 ```
 You are an engine executing ordered operations defined by the programmer. You do not originate questions. You are processing the following input card (Question) and answer card (Answer).

 Task: Identify logical contradictions, unsupported assumptions, or high-probability errors in the following answer.
 Input Question: [QUESTION]
 Input Answer: [ANSWER]

 Output ONLY the critique text. Do not output any other text.
 ```
 6. **Quality Gate**: Applies a quality gate: Discard dialogues where critique length is 0 or lacks logical keywords. **Regex**: `r'(contradiction|error|incorrect|invalid|fallacy|unsubstantiated|contradicts)'`.
 7. **Consistency Check (T051 Integration)**: Re-prompt the **Critic Model** with the question and the generated critique: "Does the critique identify a genuine error in the answer? (Yes/No)". If the answer is "No", discard the tuple.
 8. **Output**: Writes intermediate `critiques.jsonl` containing `question`, `initial_answer`, `critique`.
 **Verification**: Run a sample batch and assert that `critique` field contains logical keywords and is non-empty.
- [ ] T014b [FR-001] Implement Revised Answer Generation in `src/data/generate_revised.py`:
 1. **Prerequisites**: Depends on T014a (critiques.jsonl).
 2. **Logic**: For each critique in `critiques.jsonl`, generate K candidates (default K=5) using the **Generator Model** (Temperature=0.0).
 3. **Rejection**: Reject any candidate that contains the specific error phrase identified in the critique.
 4. **Selection**: Select the first candidate that passes the critique check. If all fail, discard the tuple.
 5. **Output**: Appends `revised_answer` to the existing records, writing `data/processed/dialogue_tuples.jsonl`.
 **Verification**: Assert that `revised_answer` does NOT contain the specific error phrase found in `critique`.
- [ ] T014c [P] Implement Integration and Validation in `src/data/integrate_dialogue.py`:
 1. **Prerequisites**: Depends on T014b.
 2. **Logic**: Combine static, dialogue, and ablation flows. Ensure output matches schema.
 3. **Output**: Final `data/processed/dialogue_tuples.jsonl`.
 **Verification**: Run `pytest tests/contract/test_schemas.py::test_validate_dialogue_schema` and assert exit code 0.
- [ ] T015a [FR-007] Implement token counter in `src/data/ablation_utils.py`. **Deliverable**: Implement `calculate_token_count(text)` using `AutoTokenizer.from_pretrained(config.GENERATOR_MODEL_ID).encode(text)`. **Verification**: Assert that the count matches the tokenizer's `encode` length.
- [ ] T013 [FR-001] Implement static QA extractor in `src/data/static_extractor.py` to generate the baseline dataset (question, answer) from downloaded sources. **Output**: `data/processed/static_tuples.jsonl`. **Verification**: Assert output file exists and contains valid JSONL with `question` and `answer` keys.
- [ ] T015b [FR-007] Implement ablation data generator in `src/data/ablation.py` replacing critique text with neutral placeholder text of equivalent **syntactic complexity** (FR-007). **Logic**:
 - **Syntactic Mirror Algorithm**: Implement an algorithm that analyzes the original critique's sentence structure, punctuation, and token count. Generate a neutral placeholder string that mirrors this structure (e.g., if the critique has 3 sentences with specific punctuation, the placeholder should have 3 sentences with similar punctuation, filled with neutral tokens like `[NEUTRAL_SENTENCE_1]`, `[NEUTRAL_SENTENCE_2]`, etc., ensuring the total token count matches within ±1).
 - **Replacement**: Replace the semantic content of the original critique with the generated placeholder.
 - **Output**: `data/processed/ablation_tuples.jsonl`.
 **Verification**: Assert that the token count of the generated placeholder matches the original critique's token count within a tolerance of ±1 token, and that the syntactic structure (sentence count, punctuation types) is preserved.
 **Note**: This task depends on T014a and T015a completion.

**Checkpoint**: At this point, User Story 1 is fully functional for Static, Dialogue, and Ablation tuples. **Note**: User Story 2 (Training) requires T015b (Ablation) to be complete as well.

---

## Phase 4: User Story 2 - CPU-Constrained Fine-Tuning and Evaluation (Priority: P2)

**Goal**: Fine-tune the base model on both datasets using LoRA and evaluate performance on held-out reasoning benchmarks within free-tier compute limits.

**Independent Test**: Execute the training pipeline on a single random seed and verify it completes within the time budget and produces evaluation metrics.

### Implementation for User Story 2

- [ ] T020 [FR-003] [P] Implement LoRA configuration in `src/train/lora_config.py` with `batch_size ≤ 2`, `gradient_accumulation_steps = 4`, and 4-bit quantization (FR-003).
- [ ] T021 [FR-008] Implement CPU-safe training loop in `src/train/train_loop.py` with a hard timeout of **5 hours** using `signal.signal(signal.SIGALRM, timeout_handler)`. **Implementation**:
 - **Timeout Handler**: Implement `timeout_handler` using `signal.signal(signal.SIGALRM, handler)`.
 - **Memory Monitoring**: Implement a loop in `train_loop.py` that samples `psutil.Process().memory_info().rss` every 60s, logging a warning if > 6.5GB.
 - **Verification**: Run script with a `timeout 2s` trigger (simulated) and assert exit code 1, logs "TIMEOUT", and saves the last checkpoint.
 **Note**: Validation data loading for Early Stopping is [deferred] per plan.md, so this check applies to the training batch processing only.
- [ ] T047a [P] Implement Condition A (Selection) training run in `src/train/run_selection_train.py`: Fine-tune model on `data/processed/dialogue_tuples.jsonl`. **Output**: `data/results/checkpoint_selection.pt`.
- [ ] T047b [P] Implement Condition B (Ablation) training run in `src/train/run_ablation_train.py`: Fine-tune model on `data/processed/ablation_tuples.jsonl` (from T015b). **Output**: `data/results/checkpoint_ablation.pt`.
- [ ] T047c [P] Implement Condition C (Static) training run in `src/train/run_static_train.py`: Fine-tune model on `data/processed/static_tuples.jsonl` (from T013). **Output**: `data/results/checkpoint_static.pt`.
- [ ] T047d [FR-006] Implement Evaluation Runner in `src/eval/evaluate.py`: **Prerequisites**: T047a, T047b, T047c. Load checkpoints. Run evaluation on GSM8K test split and MMLU STEM subset for each. **Output**: Intermediate `data/results/metrics_raw.json` containing accuracy and loss for all three conditions. **Verification**: Assert that metrics_raw.json contains accuracy keys for all three conditions.
- [ ] T047e [P] Implement Metrics Aggregation in `src/eval/aggregate_metrics.py`: Combine `metrics_raw.json` into final `data/results/metrics.json`. **Verification**: Assert `metrics.json` exists and is valid JSON.
- [ ] T048 [P] Implement Checksum Manifest Generator in `src/utils/checksum_manifest.py`: Generate SHA-256 hashes for all checkpoint files (`checkpoint_*.pt`) and append them to `state/artifact_hashes.yaml` atomically. **Verification**: Run script and verify `state/artifact_hashes.yaml` contains entries for all three checkpoint files with valid hashes.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Analysis and Ablation (Priority: P3)

**Goal**: Perform statistical comparison between conditions and ablate the self-critique component to isolate its effect.

**Independent Test**: Run the analysis script on the logged metrics from multiple seeds. and verify the statistical test output.

### Implementation for User Story 3

- [ ] T033a [FR-006] [P] Create `src/utils/stats_analysis.py`: **Deliverable**: Implement `run_t_test(condition_a, condition_b)` for Independent t-tests (Selection vs. Ablation, Selection vs. Static) with Bonferroni correction ($\alpha = 0.025$).
- [ ] T033b [P] Implement MDES and Effect Size calculation in `src/utils/stats_analysis.py`. **Deliverable**: Implement `calculate_mdes()` and `calculate_effect_size()`. **Stop-Rule**: If effect size < MDES, return "Inconclusive due to power".
- [ ] T033c [P] Create `src/utils/report_generator.py`. **Deliverable**: Implement `generate_stats_report(metrics_json, t_test_results, mdes_results)` to write to `data/results/stats_report.md`.
- [ ] T049 [P] Run `bash projects/PROJ-582-socratic-transformers-dialogue-based-sel/code/quickstart.sh` (or equivalent command) and verify exit code 0 to confirm all quickstart steps execute without error.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Philosophical Alignment & Reviewer Concerns (Priority: P1) 🛡️

**Goal**: Address specific concerns from Ada Lovelace, Alan Turing, Dan Kahneman, and David Krakauer regarding origination, verification, and bias.

**Note**: The logic for T050 (Ordered Operations), T051 (Knowledge Gap), and T052 (System 2) has been integrated directly into T014a (Phase 3) to ensure correct execution order and data flow. T054 (Attention Shift) has been removed as scope creep. T053 (Terminology) is enforced via code review and variable naming conventions in T014a.

### Implementation for Phase 6 (Integrated)

- [ ] T053 [David-Krakauer] Refine Terminology in `src/data/generate_dialogue.py` and `src/eval/evaluate.py`.
 - **Requirement**: Replace "Self-Teaching" terminology with "Negative Selection on Belief" and "Evolutionary Pressure" as per Krakauer's review.
 - **Logic**: Update all docstrings, log messages, and variable names (e.g., `self_teaching_loop` -> `selection_pressure_loop`, `teaching_signal` -> `selection_signal`).
 - **Output**: No functional change, but strict adherence to the revised problem statement.
 - **Clarification**: This task ensures code hygiene and variable names align with the reframed problem statement, rather than implementing a new requirement. The terminology is already defined in the spec; this task enforces it in the codebase.
 **Verification**: Run `grep -r "self-teach" src/` and assert exit code 1 (no matches).

**Checkpoint**: Philosophical and operational concerns from research-stage reviews are addressed.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-5)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Philosophical Alignment (Phase 6)**: Logic integrated into T014a. T053 runs in parallel with US1.
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
- **Scope Decision**: Phase 6 (Philosophical Alignment) tasks T050, T051, T052, T054 have been integrated into T014a or removed. T054 was removed as scope creep. T050, T051, T052 logic is now part of T014a.
- **Data Integrity**: T010 (Data Verification) must run AFTER T012 (Data Download) to validate downloaded files against spec-defined checksums.
- **TDD Principle**: T045 (Schema Validation) is written before T014 (Implementation) to enforce test-first development.
- **Negative Selection**: T014b strictly implements rejection-based selection (discard if error present), not best-of-N selection.
- **Ada Lovelace Constraint**: T014a iterates directly over the dataset (GSM8K/MATH) without an external "Punch-Card" bank, adhering to the spec's data generation methodology. **T014a** reinforces this by logging the "Human-Ordered Operation" in the prompt.
- **Krakauer Reframing**: Terminology in spec.md already aligns with "evolutionary pressure" and "negative selection"; **T053** enforces this in code.
- **Critic Model Clarification**: The critique mechanism uses a **separate, frozen Critic Model** (e.g., `google/flan-t5-small`) as the critic, ensuring independence from the Generator Model. This satisfies the 'Frozen Critic' constraint and avoids circular validation.
- **Knowledge Gap**: **T014a** includes the consistency check requested by Turing to ensure the critique is non-trivial.
- **Syntactic Complexity**: **T015b** uses the 'Syntactic Mirror Algorithm' to match syntactic complexity, not just token count.
- **Attention Shift**: **T054** was removed as scope creep; the Spec only mandates accuracy comparison.
- **Confidence Score**: **T052** was removed; the Spec does not define a schema for confidence scores.
- **Checksum Manifest**: **T048** updates the manifest atomically to prevent race conditions.
- **Critic Model Feasibility**: The Critic Model is a smaller model (e.g., `google/flan-t5-small`) loaded with 4-bit quantization to ensure it fits within the 7GB RAM limit alongside the Generator Model.