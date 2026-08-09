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
- [ ] T003 [P] Configure linting and formatting tools: Create `pyproject.toml` and `ruff.toml` in `projects/PROJ-582-socratic-transformers-dialogue-based-sel/code/`. **Verification**: Run `ruff check.` and verify exit code 0.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 [P] Setup data directory structure (`data/raw/`, `data/processed/`, `data/results/`) and `.gitkeep` files
- [ ] T005 [P] Implement structured logging utility in `src/utils/logging.py` to handle degenerate dialogue events as JSON lines. **Schema**: Events must follow `{"event_type": str, "timestamp": str, "details": dict}`.
- [ ] T006 [P] Setup environment configuration management for random seeds and model paths in `src/utils/config.py`
- [ ] T007 [P] Implement base model loader utility in `src/utils/model_loader.py` supporting 4-bit quantization via `bitsandbytes` (CPU backend). **Verification**: Implement memory check using `psutil` within the loader script; assert `psutil.Process().memory_info().rss < 7 * 1024 * 1024 * 1024` bytes during load (Note: This is a load-time check; full process memory must be monitored during training).
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
 2. Uses the **frozen Critic Model** (from T050) to generate critiques based on deterministic templates for critique *structure*.
 3. Generates a critique by filling the selected template with model-derived evidence.
 4. Outputs a structured JSON with `question`, `initial_answer`, `critique`, and `revised_answer`.
 5. Validates that the answer/critique pair adheres to the schema (T045).
 6. **Quality Gate**: Discard dialogues where critique length < 20 tokens or lacks logical keywords (e.g., "contradiction", "error", "incorrect").
 **Note**: This task depends on T012, T050, T045, and T015a completion. T015c is NOT required for T014; it is only required for T015b (Ablation Matching).
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
- [ ] T021 Implement CPU-safe training loop in `src/train/train_loop.py` with a hard timeout of a reasonable duration using `signal.signal(signal.SIGALRM, timeout_handler)`. Verify that the total memory usage remains within acceptable limits during training.
- [ ] T046 Create `src/eval/evaluate.py` running GSM8K test split and MMLU STEM subset, logging accuracy to `data/results/metrics.json`. **Verification**: Assert `data/results/metrics.json` exists, is valid JSON, and contains keys `accuracy` and `loss`.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Analysis and Ablation (Priority: P3)

**Goal**: Perform statistical comparison between conditions and ablate the self-critique component to isolate its effect.

**Independent Test**: Run the analysis script on the logged metrics from multiple seeds. and verify the statistical test output.

### Implementation for User Story 3

- [ ] T033 [P] Create `src/utils/stats_analysis.py`:
 - **Input**: Read from `data/results/metrics.json`.
 - **Output**: Write to `data/results/stats_report.md`.
 - Perform **Independent Samples t-tests** (Selection vs. Ablation, Selection vs. Static).
 - Apply Bonferroni correction ($\alpha = 0.025$).
 - Calculate MDES and report effect sizes.
 - **Stop-Rule**: If effect size < MDES, report "Inconclusive due to power".
 - **Ablation Logic**: Implement the specific comparison logic to isolate the effect of the selection signal content vs. token count.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Review Alignment & Philosophical Clarity (Priority: P4) 🎯 Critical Revision

**Goal**: Address specific concerns from Ada Lovelace (origination), Alan Turing (verification), Daniel Kahneman (bias), and David Krakauer (selection vs. instruction) to ensure the project's philosophical and operational rigor.

- [ ] T040 [P] Update `research.md` to align with the current spec: Replace any "self-teaching" language with "evolutionary pressure" and "negative selection on belief" by copying the exact text from the `spec.md` "Review Alignment" section into the `research.md` "Problem Statement" and "Methodology" sections. **Verification**: Diff `research.md` against `spec.md` to ensure terminology matches.

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and address philosophical/operational clarity from reviews.

- [ ] T042 [P] Run `ruff check` and `black --check` on all `src/` and `tests/` files; fix any linting/formatting errors to achieve zero violations.
- [ ] T049 [P] Run `bash projects/PROJ-582-socratic-transformers-dialogue-based-sel/code/quickstart.sh` (or equivalent command) and verify exit code 0 to confirm all quickstart steps execute without error.