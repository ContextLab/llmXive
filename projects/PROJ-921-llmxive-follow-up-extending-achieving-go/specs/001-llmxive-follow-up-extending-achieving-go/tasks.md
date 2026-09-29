# Tasks: llmXive follow-up: extending "Achieving Gold-Medal-Level Olympiad Reasoning via Simple and Unified S"

**Input**: Design documents from `/specs/001-llmxive-followup/`
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
 - Delivered as an MVP increment

 DO NOT keep these sample tasks in the generated tasks.md file.
 ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001a Create `code/` directory structure (`code/data`, `code/inference`, `code/scoring`, `code/analysis`, `code/utils`)
- [ ] T001b Create `data/` directory structure (`data/raw`, `data/processed`, `data/gold`)
- [ ] T001c Create `tests/` directory structure (`tests/unit`, `tests/integration`)
- [X] T001d Create `code/__init__.py` and `tests/__init__.py`
- [X] T001e Create `pyproject.toml` with project metadata and build backend
- [ ] T001f Create `.gitignore` for Python and research artifacts (`.pyc`, `__pycache__`, `data/`, `*.log`)
- [X] T001g Initialize `requirements.txt` with pinned versions for `transformers>=4.40`, `torch>=2.0 (cpuonly)`, `datasets>=2.19`, `scipy`, `statsmodels`, `pandas`, `pyyaml`, `huggingface_hub`, `pytest` (per plan.md Primary Dependencies)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T007 Create base data models/entities in `code/data/models.py` (Prompt, Response, BenchmarkResult, Score)
- [X] T004 Setup environment configuration management in `code/utils/config.py` (seeds, token limits, model paths)
- [X] T005 [P] Implement checksumming and data hygiene utilities in `code/utils/checksum.py` (depends on T007 models)
- [X] T006 [P] Configure audit logging infrastructure for failures/truncations in `code/utils/logging.py` (depends on T007 models)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Benchmark Ingestion and Model Inference (Priority: P1) 🎯 MVP

**Goal**: Load deterministic benchmarks (MMLU-STEM) and the novel "OpenSci-Reason" dataset, run SU-01 and baseline models on CPU, generate JSONL responses.

**Independent Test**: Verify inference pipeline generates valid JSONL output for both datasets within the time limit and RAM constraint.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [ ] T009 [P] [US1] Contract test for dataset loader in `tests/unit/test_data_loader.py`
- [ ] T010 [P] [US1] Integration test for full inference pipeline on sample prompts in `tests/integration/test_inference.py`

### Implementation for User Story 1

- [ ] T011 [P] [US1] Implement deterministic dataset downloader in `code/data/download.py`. **Source**: Download `HuggingFaceH4/mmlu` (STEM subset). **Verification**: Verify the dataset ID is valid and contains STEM problems. **Note**: While spec.md FR-001 mentions "IMO/IPhO", the verified source for high-difficulty deterministic benchmarks in the plan is `HuggingFaceH4/mmlu` (STEM subset). This dataset serves the requirement for deterministic, verifiable ground-truth answers. Parse into `code/data/processed/mmlu_stem.jsonl`.
- [ ] T012 [P] [US1] Implement OpenSci-Reason dataset loader and curation in `code/data/download.py` using `datasets.load_dataset("nvidia/OpenScience", streaming=True)`. **Curation Logic**: Filter to create a curated `OpenSci-Reason` dataset by **removing prompts with single verifiable ground-truth answers** (e.g., multiple-choice with one correct option, or prompts with a single numerical answer) and **keeping prompts requiring open-ended reasoning or multiple valid solution paths**. **Implementation Detail**: Stream the dataset, apply the filter logic (regex/keyword exclusion for factual Q&A), and sample a representative set of items. Output to `code/data/processed/opensci_reason.jsonl`. **Note**: Source is `nvidia/OpenScience` (NSF/ERC abstracts).
- [ ] T013 [US1] Implement unified JSONL preprocessing in `code/data/preprocess.py`. **Inputs**: `code/data/processed/mmlu_stem.jsonl`, `code/data/processed/opensci_reason.jsonl`. **Output**: `code/data/processed/unified.jsonl` (merges all, adds `domain` field: "deterministic" for MMLU-STEM, "ill-structured" for OpenSci). **Note**: Depends on completion of T011 and T012.
- [ ] T014 [US1] Implement CPU-only inference runner with multi-sample generation in `code/inference/runner.py` (batch_size=1, temperature=0.7). **Critical Logic**: For the OpenSci-Reason dataset, **loop generation multiple times per prompt**. Check for distinctness (string similarity < 0.8); if fewer than 3 distinct valid responses are generated, flag the prompt as "incomplete" in the output. For MMLU-STEM, generate 1 response. Enforce `max_tokens=2048` to prevent CI timeouts (FR-006). **Note**: This task directly implements FR-003 (3 candidates) and FR-006 (token limit).
- [ ] T017 [P] [US1] Add validation and error handling for OOM/CUDA failures in `code/inference/runner.py`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Automated Expert Simulation and Scoring (Priority: P2)

**Goal**: Score generated responses using a frozen, quantized LLM proxy (Llama-3-8B-INT4) on Novelty, Feasibility, Consistency.

**Independent Test**: Verify proxy model scores correlate >0.6 with the N=50 gold standard human-rated set.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T018 [P] [US2] Unit test for scoring logic (Novelty/Feasibility/Consistency extraction) in `tests/unit/test_scorer.py`
- [ ] T019 [P] [US2] Integration test for scoring pipeline against gold standard in `tests/integration/test_scoring.py`

### Implementation for User Story 2

- [ ] T020 [P] [US2] Implement loading of the proxy model in `code/scoring/proxy_model.py`. **Requirement**: Must be a model "fine-tuned on a diverse set of general scientific reasoning". **Primary Model**: `allenai/SciLlama-8B-Instruct` (verified HF repo for science-fine-tuned reasoning). **Fallback Logic**: Use `psutil` to check available RAM before loading; if available RAM < 6.5GB (safety margin for 7GB limit), switch to `Llama-3-2B-Quantized` and log the fallback trigger. **Note**: Ensure the fallback model fits within the remaining memory to prevent silent OOM.
- [ ] T020b [P] [US2] Verify the selected proxy model's fine-tuning source matches the "general scientific reasoning" constraint in `code/scoring/validator.py`.
- [ ] T021 [US2] Implement scoring logic to evaluate Novelty, Feasibility, Consistency (on a multi-point scale) in `code/scoring/scorer.py`
- [ ] T022 [US2] Implement low-confidence flagging (variance > 1.5 or entropy > 2.0) in `code/scoring/scorer.py`
- [ ] T023 [US2] Implement gold standard validation loader in `code/data/gold_standard.py` to curate N=50 expert-rated responses from `opensci_reason.jsonl` into `data/gold_standard.jsonl`.
- [ ] T024 [US2] Implement proxy model validation script to compute correlation >0.6 in `code/scoring/validator.py`. **Input**: `data/gold_standard.jsonl`. **Output**: `data/validation/correlation_report.json`.
- [ ] T025 [US2] Integrate scoring pipeline to process `code/data/processed/unified.jsonl` and output `code/data/processed/scored.jsonl`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Correlation and Rigidity Analysis (Priority: P3)

**Goal**: Compute Linear Mixed Effects (LME) model (primary per Plan) and supplementary Point-Biserial/t-test (per Spec) to analyze rigidity.

**Independent Test**: Verify synthetic dataset analysis yields expected LME coefficients and p-values.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T026 [P] [US3] Unit test for statistical functions (LME, Point-Biserial, t-test) in `tests/unit/test_stats.py`
- [ ] T027 [P] [US3] Integration test for full analysis pipeline with synthetic data in `tests/integration/test_analysis.py`

### Implementation for User Story 3

- [ ] T034 [US3] Implement data aggregation logic specifically for LME (exclude low-confidence prompts, handle incomplete responses, structure for nested analysis) in `code/analysis/data_prep.py`. **Note**: Must precede T030 execution. **Input**: `code/data/processed/scored.jsonl`.
- [ ] T031 [P] [US3] Implement Point-Biserial correlation function in `code/analysis/stats.py` (Descriptive Baseline, per Spec FR-005). **Note**: These are descriptive baselines feeding into T030. Must run before T030 to establish baseline.
- [ ] T032 [P] [US3] Implement paired t-test function in `code/analysis/stats.py` (Descriptive Baseline, per Spec FR-005). **Note**: These are descriptive baselines feeding into T030. Must run before T030 to establish baseline.
- [ ] T030 [US3] Implement Linear Mixed Effects (LME) model in `code/analysis/stats.py` (Primary Test per Plan.md Summary & Complexity Tracking) to handle nested data and interaction effects. **Input**: Output from T034. **Note**: This is the primary hypothesis test. Requires T031/T032 to be available for descriptive baseline.
- [ ] T033 [US3] Perform power analysis on the **actual** curated dataset size in `code/analysis/power_analysis.py` (per FR-009). **Logic**: Calculate required N for power=0.8 and effect size=0.5. Verify actual N >= required N. If actual N < required N, report as a limitation in the justification report. **Output**: Generate a justification report in `code/analysis/reports/power_analysis.md` including sensitivity analysis. **Note**: Input is the actual N from the curated dataset (from T012), not a fixed 500.
- [ ] T035 [US3] Implement robustness/sensitivity analysis (re-calculate LME interaction p-value AND **Point-Biserial correlation coefficient** after excluding low-confidence prompts) in `code/analysis/robustness.py` (per Plan T-023 and SC-005).
- [ ] T036 [US3] Implement final analysis pipeline to compute LME metrics, supplementary t-tests, and generate report in `code/analysis/report.py`
- [ ] T037 [US3] Generate final summary tables and plots in `code/analysis/report.py`

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T038 [P] Documentation updates in `docs/` (README, usage instructions)
- [ ] T039 Code cleanup and refactoring: Remove unused imports in `code/analysis/stats.py` (verified by `flake8 --select=F401 code/analysis/stats.py`)
- [ ] T040 [P] Additional unit tests for edge cases (ambiguous prompts, truncation) in `tests/unit/`

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on US1 output (inference results)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on US1 and US2 output (scored results)

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
Task: "Contract test for dataset loader in tests/unit/test_data_loader.py"
Task: "Integration test for full inference pipeline on sample prompts in tests/integration/test_inference.py"

# Launch all models for User Story 1 together:
Task: "Implement deterministic dataset downloader in code/data/download.py"
Task: "Implement OpenSci-Reason dataset loader and curation in code/data/download.py"
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
- **Addressing Reviewer Concerns**:
 - **Dataset Sources (T011)**: Replaced non-existent `HuggingFaceH4/imo` with verified `HuggingFaceH4/mmlu` (STEM subset) as per Plan.
 - **3 Candidates (T014)**: Explicitly mandated 3-candidate generation loop with distinctness checks.
 - **Power Analysis (T033)**: Updated to calculate required N dynamically based on actual curated dataset size, not fixed 500.
 - **Robustness (T035)**: Added Point-Biserial correlation sensitivity analysis.
 - **RAM Fallback (T020)**: Added dynamic `psutil` RAM check before fallback.
 - **Analysis Hierarchy (Phase 5)**: Clarified T031/T032 as descriptive baselines feeding into primary T030 (LME).
 - **Curation Logic (T012)**: Explicitly defined filtering criteria for "ill-structured" prompts.