# Tasks: Survey of Large Audio Language Models – Hallucination Analysis

**Input**: Design documents from `/specs/feature-001-audio-hallucination/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- Paths shown below assume single project - adjust based on plan.md structure

<!--
 ============================================================================
 IMPORTANT: The tasks below are SAMPLE TASKS for illustration purposes only.

 The /speckit-tasks command MUST replace these with actual tasks based on:
 - User stories from spec.md (with their priorities P1, P2, P3...)
 - Feature requirements from plan.md
 - Entities from data-model.md
 - Endpoints from contracts/

 Tasks MUST be organized by user story so each story can be:
 - Implemented independently
 - Tested independently
 - Delivered as a MVP increment

 DO NOT keep these sample tasks in the generated tasks.md file.
 ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project structure per implementation plan: `code/`, `data/`, `results/`, `tests/` at repository root
- [X] T002 Initialize Python 3.11 project with `requirements.txt` (torch CPU-only, transformers, librosa, pandas, scikit-learn, datasets, pyyaml, nltk, fuzzywuzzy, **pdfplumber**, **PyPDF2**)
- [X] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Setup data hygiene and checksum infrastructure (`code/checksum_data.py`) to verify SHA-256 hashes of downloaded datasets
- [X] T005 [P] Implement logging infrastructure to write reproducible `pipeline.log` (FR-010)
- [X] T006 [P] Create base configuration management for model lists, dataset paths, and sample limits (a fixed number per domain)
- [X] T007 Create base entity models (`AudioSample`, `ModelInstance`) in `code/utils.py`
- [X] T008 Implement CPU-only model loading utility (`code/load_audio.py`) with memory guards (no CUDA, no bitsandbytes)
- [X] T009 Setup runtime time-limit guard (configurable threshold) and OOM handling logic

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Automated Domain‑wise Hallucination Evaluation (Priority: P1) 🎯 MVP

**Goal**: End-to-end pipeline loading LALMs, running on a representative set of audio samples per domain (Speech, Music, Env), and outputting per-domain hallucination rates with confidence intervals.

**Independent Test**: Execute the pipeline on a fresh runner; verify `hallucination_rates.csv` contains three rows with hallucination rates and confidence intervals.

### Sub-phase 3a: Contract Definition (MUST precede Implementation)

**Purpose**: Define the exact schema and interfaces before implementation begins to ensure test-consumer alignment.
**⚠️ ORDERING NOTE**: T010 and T011 MUST be completed BEFORE T012-T018. These tasks define the schema that the implementation tasks will produce. Do not mark T010/T011 as parallel with implementation.

- [X] T010 [US1] Define and implement contract test for `hallucination_rates.csv` schema in `tests/contract/test_hallucination_schema.py`. **MUST run BEFORE T012-T018**.
- [X] T011 [US1] Define and implement integration test scaffolding for full inference pipeline on samples in `tests/integration/test_inference_pipeline.py`. **MUST run BEFORE T012-T018**.

### Sub-phase 3b: Data Preparation (MUST precede Implementation)

**Purpose**: Convert raw HuggingFace datasets into the specific JSON artifacts required by the detection logic.

- [X] T011b [US1] Implement dataset conversion logic: Load datasets via HF Datasets (Protocol 1) and export to `data/raw/librispeech/dev-clean.json`, `data/raw/fma_small/metadata.json`, `data/raw/esc50/esc50.json`. **Depends on: T004, T012**. **Produces artifact required by T016**.

### Sub-phase 3c: Implementation

**Purpose**: Implement the logic required to satisfy the contracts defined in Sub-phase 3a.

- [X] T012 [P] [US1] Implement dataset loading logic for LibriSpeech (Speech), FMA Small (Music), and ESC (Env) in `code/load_audio.py`. **Depends on: T011b, T010, T011**.
- [X] T013 [US1] Implement audio preprocessing: resample to a standard audio sampling rate, truncate/discard >10s samples, log discards (FR-002)
- [X] T014 [US1] Implement model exclusion logic (FR-013) using fuzzy matching (similarity > 0.8) against keyword list (`esc-50`, `musicbench`, `audiobench`, `librispeech`) to skip models trained on test datasets
- [X] T015 [US1] Implement caption generation using standardized prompt template in `code/run_inference.py`
- [X] T015b [US1] Implement caption storage: Write all generated captions to `results/captions.json` (JSONL format) for downstream consumption. **Produces artifact required by T027**.
- [X] T016 [US1] Implement rule-based hallucination detector (`code/detect_hallucination.py`):
 1. Read ground truth from `data/raw/librispeech/dev-clean.json`, `data/raw/fma_small/metadata.json`, `data/raw/esc50/esc50.json` (produced by T011b).
 2. **Normalization**: Convert ground-truth and caption entities to lowercase, strip whitespace.
 3. **Expansion**: For each ground-truth entity, expand the set of valid matches using WordNet synonyms and fuzzy matching (Levenshtein distance < 2 or similarity > 0.8).
 4. **Flagging**: Flag a sample as hallucinated IF AND ONLY IF a normalized entity in the caption is NOT found in the **expanded** ground-truth set. (FR-004, FR-012).
- [X] T017a [US1] Implement Wilson-score confidence interval calculation function in `code/run_inference.py`: Input is list of dicts `{domain: str, hallucinated_flag: bool}`; Output is list of dicts `{domain: str, rate: float, ci_lower: float, ci_upper: float}`. **Intermediate artifact: `results/ci_calculation.json`**.
- [X] T017b [US1] Write `results/hallucination_rates.csv` with columns `[domain, rate, ci_lower, ci_upper]` in `code/run_inference.py`. **Produces artifact required by US2 (T021/T022)**
- [X] T018 [US1] Add error handling for OOM and model load failures (graceful abort with logging)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently. `results/hallucination_rates.csv` is generated.

---

## Phase 4: User Story 2 - Correlation of Training‑Data Volume with Hallucination (Priority: P2)

**Goal**: Estimate domain-specific pre-training data volumes and compute Spearman's rank correlation with hallucination rates.

**Independent Test**: Run analysis on `hallucination_rates.csv`; verify report contains data volumes, Spearman coefficient, and descriptive statement.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T019 [P] [US2] Contract test for `correlation_report.json` schema in `tests/contract/test_correlation_output_schema.py`
- [X] T020 [P] [US2] Unit test for proxy derivation logic when exact counts are missing

### Implementation for User Story 2

- [X] T021 [P] [US2] Implement training data estimation logic: Parse `data/model_cards/*.md` and `data/model_cards/*.pdf` (using `pdfplumber`/`PyPDF2`) to extract speech/music/env hours. If missing, derive proxy (hours/tokens) with documented uncertainty bounds. Write output to `data/training_data_estimates.yaml` with keys: `model_name`, `speech_hours`, `music_hours`, `env_hours`, `uncertainty_notes`. **Produces artifact required by T022** (FR-006, Constitution VII)
- [X] T022a [US2] Compute Spearman rank correlation between training data volume and hallucination rates.
 - **Input**: Read `data/training_data_estimates.yaml` and `results/hallucination_rates.csv`.
 - **Constraint**: Since N=3 (three domains), **DO NOT calculate or report Confidence Intervals**. Report only the coefficient and a descriptive statement (e.g., "Higher data volume associated with lower hallucination rate").
 - **Output**: `results/correlation_report.json` containing coefficient and descriptive statement. (FR-007, Protocol 4).
- [X] T022b [US2] Generate sensitivity report (multiple permutations) to `results/correlation_sensitivity.json`
- [X] T023 [US2] Generate descriptive report framing results as exploratory and associative (FR-011)
- [X] T024 [US2] Handle missing data: flag as 'unknown' and proceed without halting (FR-006)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Human Validation of Hallucination Labels (Priority: P3)

**Goal**: Select a representative sample size, submit to crowdsourcing, retrieve judgments, and compute Cohen's κ.

**Independent Test**: Submit a representative number of samples; verify system retrieves judgments and calculates κ with flag if < 0.6.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T025 [P] [US3] Contract test for `human_judgments.csv` schema in `tests/contract/test_human_judgments_schema.py`
- [X] T026 [P] [US3] Unit test for Cohen’s κ calculation and threshold flagging

### Implementation for User Story 3

- [X] T027 [P] [US3] Implement stratified sampling logic to select a representative sample size from `results/captions.json` (produced by T015b) and `results/hallucination_rates.csv`. **Depends on: T015b, T017b**.
- [X] T028a [US3] Generate CSV template `human_judgments_template.csv` and script `submit_crowd_job.py` to format 150 samples into the required JSON payload for MTurk/Prolific
- [X] T028b [US3] Implement crowdsourcing job submission interface (`code/submit_crowd_job.py`):
 - Target Prolific API.
 - Read API keys from environment variables (`PROLIFIC_API_KEY`).
 - **Logic**: If `PROLIFIC_API_KEY` is missing, generate a mock API response for testing; otherwise, call the real API.
 - Include logic for endpoint definitions and rate-limiting.
 - Return `job_ids`.
- [X] T029 [US3] Implement judgment retrieval (`code/retrieve_crowd_judgments.py`): Use `job_ids` from T028b to fetch binary hallucination judgments and format as `human_judgments.csv`
- [X] T030 [US3] Implement Cohen’s κ calculation and low-agreement flagging in `code/analyze_correlation.py` (FR-009)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T031 [P] Documentation updates in `docs/` and `quickstart.md`
- [X] T032 Code cleanup and refactoring
- [X] T033a [P] Benchmark: Run pipeline on a representative set of samples per domain and record duration. Log to `results/benchmark_duration.json`.
- [X] T033b [P] Optimization: Implement batch size reduction and memory-efficient loading if T033a duration > 4.5 hours. Verify duration < 5 hours.
- [X] T034 [P] Additional unit tests in `tests/unit/`
- [ ] T035 Run `quickstart.md` validation and verify `pipeline.log` completeness

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
- **User Story 2 (P2)**: Depends on US1 completion (needs `hallucination_rates.csv` from T017b)
- **User Story 3 (P3)**: Depends on US1 completion (needs `results/captions.json` from T015b)

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority
- **CRITICAL**: Contract Definition (T010, T011) MUST be completed before Implementation (T012-T018).
- **CRITICAL**: Data Conversion (T011b) MUST be completed before Dataset Loading (T012) and Hallucination Detection (T016).

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
Task: "Contract test for hallucination_rates.csv schema in tests/contract/test_hallucination_schema.py"
Task: "Integration test for full inference pipeline on 3 samples in tests/integration/test_inference_pipeline.py"

# Launch all models for User Story 1 together:
Task: "Implement dataset loading logic for LibriSpeech, FMA Small, and ESC-50 in code/load_audio.py"
Task: "Implement audio preprocessing (resample, truncate) in code/load_audio.py"

# NOTE: T010 and T011 MUST complete BEFORE T012-T018 start. T011b MUST complete BEFORE T012 starts.
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
 - Complete Sub-phase 3a: Contract Definition (T010, T011) - **Strictly before implementation**
 - Complete Sub-phase 3b: Data Preparation (T011b)
 - Complete Sub-phase 3c: Implementation (T012-T018)
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
 - Developer A: User Story 1 (Contracts then Implementation)
 - Developer B: User Story 2 (after US1 data available)
 - Developer C: User Story 3 (after US1 data available)
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
- **Constraint**: All tasks must run on CPU-only CI (limited core count, 7GB RAM); no GPU libraries allowed.
- **Ordering Note**: T010 and T011 (Contract Definition) MUST be completed before T012-T018 (Implementation) to ensure schema definitions drive the implementation. T011b (Data Conversion) MUST be completed before T012 (Dataset Loading) and T016 (Detection).