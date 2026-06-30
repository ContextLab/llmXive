# Tasks: Survey of Large Audio Language Models – Hallucination Analysis

**Input**: Design documents from `/specs/feature-001-audio-hallucination/`
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

- [ ] T001 Create project structure per implementation plan: `code/`, `data/`, `results/`, `tests/` at repository root
- [ ] T002 Initialize Python 3.11 project with `requirements.txt` (torch CPU-only, transformers, librosa, pandas, scikit-learn, datasets, pyyaml, nltk, fuzzywuzzy)
- [ ] T003 [P] Configure linting (ruff) and formatting (black) tools

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Setup data hygiene and checksum infrastructure (`code/checksum_data.py`) to verify SHA-256 hashes of downloaded datasets
- [ ] T005 [P] Implement logging infrastructure to write reproducible `pipeline.log` (FR-010)
- [ ] T006 [P] Create base configuration management for model lists, dataset paths, and sample limits (a fixed number per domain)
- [ ] T007 Create base entity models (`AudioSample`, `ModelInstance`) in `code/utils.py`
- [ ] T008 Implement CPU-only model loading utility (`code/load_audio.py`) with memory guards (no CUDA, no bitsandbytes)
- [ ] T009 Setup runtime time-limit guard (configurable threshold) and OOM handling logic

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Automated Domain‑wise Hallucination Evaluation (Priority: P1) 🎯 MVP

**Goal**: End-to-end pipeline loading LALMs, running on a representative set of audio samples per domain (Speech, Music, Env), and outputting per-domain hallucination rates with confidence intervals.

**Independent Test**: Execute the pipeline on a fresh runner; verify `hallucination_rates.csv` contains three rows with hallucination rates and confidence intervals.

### Sub-phase 3a: Contract Definition (MUST precede Implementation)

**Purpose**: Define the exact schema and interfaces before implementation begins to ensure test-consumer alignment.
**⚠️ ORDERING NOTE**: T010 and T011 MUST be completed BEFORE T012-T018. These tasks define the schema that the implementation tasks will produce. Do not mark T010/T011 as parallel with implementation.

- [ ] T010 [US1] Define and implement contract test for `hallucination_rates.csv` schema in `tests/contract/test_hallucination_schema.py`. **MUST run BEFORE T012-T018**.
- [ ] T011 [US1] Define and implement integration test scaffolding for full inference pipeline on samples in `tests/integration/test_inference_pipeline.py`. **MUST run BEFORE T012-T018**.

### Sub-phase 3b: Implementation

**Purpose**: Implement the logic required to satisfy the contracts defined in Sub-phase 3a.

- [ ] T012 [P] [US1] Implement dataset loading logic for LibriSpeech (Speech), FMA Small (Music), and ESC-50 (Env) in `code/load_audio.py`
- [ ] T013 [US1] Implement audio preprocessing: resample to a standard audio sampling rate, truncate/discard >10s samples, log discards (FR-002)
- [ ] T014 [US1] Implement model exclusion logic (FR-013) using fuzzy matching (similarity > 0.8) against keyword list (`esc-50`, `musicbench`, `audiobench`, `librispeech`) to skip models trained on test datasets
- [ ] T015 [US1] Implement caption generation using standardized prompt template in `code/run_inference.py`
- [ ] T016 [US1] Implement rule-based hallucination detector (`code/detect_hallucination.py`): Read ground truth from `data/raw/librispeech/dev-clean.json`, `data/raw/fma_small/metadata.json`, `data/raw/esc50/esc50.json`. Use fuzzy/synonym logic ONLY for entity normalization; final flagging decision must use EXACT STRING MATCH on normalized entity names (FR-004, FR-012)
- [ ] T017a [US1] Implement Wilson-score confidence interval calculation function in `code/run_inference.py`: Input is list of dicts `{domain: str, hallucinated_flag: bool}`; Output is list of dicts `{domain: str, rate: float, ci_lower: float, ci_upper: float}`
- [ ] T017b [US1] Write `results/hallucination_rates.csv` with columns `[domain, rate, ci_lower, ci_upper]` in `code/run_inference.py`. **Produces artifact required by US2 (T021/T022)**
- [ ] T018 [US1] Add error handling for OOM and model load failures (graceful abort with logging)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently. `results/hallucination_rates.csv` is generated.

---

## Phase 4: User Story 2 - Correlation of Training‑Data Volume with Hallucination (Priority: P2)

**Goal**: Estimate domain-specific pre-training data volumes and compute Spearman's rank correlation with hallucination rates.

**Independent Test**: Run analysis on `hallucination_rates.csv`; verify report contains data volumes, Spearman coefficient, and descriptive statement with 95% CI (via bootstrapping).

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T019 [P] [US2] Contract test for `correlation_report.json` schema in `tests/contract/test_correlation_output_schema.py`
- [ ] T020 [P] [US2] Unit test for proxy derivation logic when exact counts are missing

### Implementation for User Story 2

- [ ] T021 [P] [US2] Implement training data estimation logic: Parse `data/model_cards/*.md` and `data/model_cards/*.pdf` to extract speech/music/env hours. If missing, derive proxy (hours/tokens) with documented uncertainty bounds. Write output to `data/training_data_estimates.yaml` with keys: `model_name`, `speech_hours`, `music_hours`, `env_hours`, `uncertainty_notes`. **Produces artifact required by T022** (FR-006, Constitution VII)
- [ ] T022a [US2] Compute Spearman rank correlation between training data volume and hallucination rates. **MUST calculate confidence intervals using bootstrapping** (overriding Plan Protocol 4) to satisfy Spec FR-007. Output coefficient and CI.
- [ ] T022b [US2] Generate sensitivity report (multiple permutations) to `results/correlation_sensitivity.json`
- [ ] T023 [US2] Generate descriptive report framing results as exploratory and associative (FR-011)
- [ ] T024 [US2] Handle missing data: flag as 'unknown' and proceed without halting (FR-006)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Human Validation of Hallucination Labels (Priority: P3)

**Goal**: Select 150 samples, submit to crowdsourcing, retrieve judgments, and compute Cohen’s κ.

**Independent Test**: Submit 150 samples; verify system retrieves judgments and calculates κ with flag if < 0.6.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T025 [P] [US3] Contract test for `human_judgments.csv` schema in `tests/contract/test_human_judgments_schema.py`
- [ ] T026 [P] [US3] Unit test for Cohen’s κ calculation and threshold flagging

### Implementation for User Story 3

- [ ] T027 [P] [US3] Implement stratified sampling logic to select exactly 150 samples from `results/captions.json` (US1 output) and `results/hallucination_rates.csv` (FR-008)
- [ ] T028a [US3] Generate CSV template `human_judgments_template.csv` and script `submit_crowd_job.py` to format 150 samples into the required JSON payload for MTurk/Prolific
- [ ] T028b [US3] Implement crowdsourcing job submission interface (`code/submit_crowd_job.py`): Call platform API to submit the 150 samples and return the `job_ids`
- [ ] T029 [US3] Implement judgment retrieval (`code/retrieve_crowd_judgments.py`): Use `job_ids` from T028b to fetch binary hallucination judgments and format as `human_judgments.csv`
- [ ] T030 [US3] Implement Cohen’s κ calculation and low-agreement flagging in `code/analyze_correlation.py` (FR-009)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T031 [P] Documentation updates in `docs/` and `quickstart.md`
- [ ] T032 Code cleanup and refactoring
- [ ] T033 Performance optimization: ensure pipeline completes in ≤5 hours on 2 CPU/7GB RAM
- [ ] T034 [P] Additional unit tests in `tests/unit/`
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
- **User Story 3 (P3)**: Depends on US1 completion (needs `results/captions.json` from T015/T017b)

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority
- **CRITICAL**: Contract Definition (T010, T011) MUST be completed before Implementation (T012-T018).

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
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
   - Complete Sub-phase 3a: Contract Definition (T010, T011) - **Strictly before implementation**
   - Complete Sub-phase 3b: Implementation (T012-T018)
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
- **Constraint**: All tasks must run on CPU-only CI (2 cores, 7GB RAM); no GPU libraries allowed.
- **Ordering Note**: T010 and T011 (Contract Definition) MUST be completed before T012-T018 (Implementation) to ensure schema definitions drive the implementation.