# Tasks: llmXive Follow-up: OPD Generalization Gap in Unified Diffusion

**Input**: Design documents from `/specs/001-opd-generalization-gap/`
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

- [ ] T001 Create project structure per implementation plan (`projects/PROJ-913-llmxive-follow-up-extending-qwen-image-2/`)
- [ ] T002 Initialize Python project with `diffusers`, `transformers`, `torch`, `scikit-learn`, `pandas`, `numpy`, `requests`, `huggingface_hub`, `seaborn`, `datasets`, `pytest`, `statsmodels` dependencies in `code/requirements.txt`
- [ ] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools in `code/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

Examples of foundational tasks (adjust based on your project):

- [ ] T004 Setup data directory structure (`data/prompts/`, `data/models/`, `data/outputs/base/`, `data/outputs/rl_unified/`) and `.gitkeep` files
- [ ] T005 [P] Implement global random seed pinning utility in `code/utils/seeding.py` (A fixed random seed will be used to ensure reproducibility.)
- [ ] T006 [P] Setup configuration management for batch sizes and CPU offloading limits in `code/config.py`
- [ ] T007 Create base data models (PromptSet, ModelWeights, GeneratedImage, EvaluationScore) in `code/models/entities.py`
- [ ] T008 Configure logging infrastructure to `code/utils/logger.py` with file rotation for long-running jobs
- [ ] T009 Setup environment configuration management for HF token and cache paths in `code/config.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Prompt Curation (Priority: P1) 🎯 MVP

**Goal**: Acquire model weights and curate leakage-free prompt sets (In-Distribution vs OOD)

**Independent Test**: Verify model weights exist with correct SHA-256 checksums and OOD prompts have < 0.3 cosine similarity to ID centroids.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T010 [P] [US1] Unit test for SHA-256 checksum verification in `tests/unit/test_data_acquisition.py`
- [ ] T011 [P] [US1] Unit test for latent-space similarity check (< 0.3 threshold) in `tests/unit/test_prompt_curation.py`
- [ ] T012 [P] [US1] Integration test for full download and validation flow in `tests/integration/test_data_pipeline.py`

### Implementation for User Story 1

- [ ] T013 [P] [US1] Implement `download_models.py` to fetch `Qwen/Qwen-Image-2.0` and `Qwen/Qwen-Image-2.0-RL` from Hugging Face with retry logic (limited attempts, exponential backoff) in `code/data_acquisition.py`
- [ ] T014 [US1] Implement `verify_checksums.py` to validate downloaded weights against repository manifest in `code/data_acquisition.py`
- [ ] T015a [US1] Implement `curate_prompts.py` to generate the **Pilot** prompt sets (N=20 ID, N=20 OOD). **Must include**: (1) Dynamic scaling logic to measure runtime, (2) Abort if OOD contamination detected (integrated logic), (3) Logging for pilot stats. **Must run BEFORE T016**. Output: `data/prompts/pilot_in_distribution.csv`, `data/prompts/pilot_ood.csv` in `code/prompt_curation.py`.
- [ ] T016 [US1] Implement `validate_ood.py` to compute cosine similarity between OOD embeddings and ID centroids. **Must include**: (1) Abort with `[CRITICAL: DATA LEAKAGE DETECTED]` if > 0.3 (integrated logic), (2) Logging for validation metrics. **Must run AFTER T015a**. Output: `data/prompts/validation_report.json` in `code/prompt_curation.py`.
- [ ] T015b [US1] Implement `curate_prompts.py` (Full Run) to generate the **Target** prompt sets (N=500 or Max-Feasible). **Must run ONLY after T034_pilot_power_gate (Power Analysis) confirms feasibility**. Output: `data/prompts/in_distribution.csv`, `data/prompts/ood.csv` in `code/prompt_curation.py`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently (Pilot only until T034_pilot_power_gate clears Full Run)

---

## Phase 4: User Story 2 - CPU-Only Inference Execution (Priority: P2)

**Goal**: Generate images for both models on CPU-only environment using diffusers with float16 and offloading

**Independent Test**: Verify images are generated within time limits without OOM crashes.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T018 [P] [US2] Unit test for memory-batch calculation logic in `tests/unit/test_inference_batching.py`
- [ ] T019 [P] [US2] Integration test for single-prompt generation on CPU in `tests/integration/test_cpu_inference.py`

### Implementation for User Story 2

- [ ] T020 [P] [US2] Implement `inference.py` to load Base and RL-Unified models with `torch_dtype=torch.float16` and `device_map="cpu"` (or CPU offloading) in `code/inference.py`
- [ ] T020a [US2] Implement `generate_batch.py` (Pilot) to process **Pilot** prompts (from T015a) in dynamic batches. **Must include**: Memory monitoring, garbage collection, and runtime logging. Output: `data/outputs/pilot_base/`, `data/outputs/pilot_rl_unified/` in `code/inference.py`.
- [ ] T020b [US2] Implement `generate_batch.py` (Full) to process **Target** prompts (from T015b) in dynamic batches. **Must run ONLY after T034_pilot_power_gate (Power Analysis) clears the sample size**. Output: `data/outputs/base/`, `data/outputs/rl_unified/` in `code/inference.py`.
- [ ] T022 [US2] Implement `save_images.py` to save generated images to `data/outputs/base/` and `data/outputs/rl_unified/` with naming convention `{prompt_id}_{model}_{seed}.png` in `code/inference.py`
- [ ] T023 [US2] Implement `monitor_memory.py` to trigger garbage collection and reduce batch size if RAM usage approaches a high magnitude. in `code/inference.py`
- [ ] T024 [US2] Add retry logic for generation failures (e.g., transient model loading issues) in `code/inference.py`
- [ ] T025 [US2] Add logging for batch progress, generation time, and memory stats in `code/inference.py`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently (Pilot images ready; Full images pending T034_pilot_power_gate)

---

## Phase 4.5: Power Analysis Gate (Critical Dependency for Full Run)

**Goal**: Determine if full-scale generation is statistically feasible before proceeding.

- [ ] T034_pilot_power_gate [US3] Implement `power_analysis.py` to calculate achieved statistical power and required sample size using `statsmodels` based on **Pilot** results (T020a). **CRITICAL GATE**: If required N > feasible N (prohibitively long runtime), output `STOP` and block T015b/T020b. If feasible, output `GO` and recommend N. Output: `data/results/power_analysis.json` in `code/analysis.py`. **Must run after T020a (Pilot Inference) and before T015b (Full Curation) / T020b (Full Inference)**.

---

## Phase 5: User Story 3 - Statistical Analysis of Generalization Gap (Priority: P3)

**Goal**: Compute score degradation and perform statistical tests on the Generalization Gap

**Independent Test**: Verify statistical test outputs correct p-values and gap metrics on synthetic data.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T026 [P] [US3] Unit test for score calculation (Aesthetics, Prompt Adherence, Identity) in `tests/unit/test_scoring.py`
- [ ] T027 [P] [US3] Unit test for Wilcoxon test implementation with mock data in `tests/unit/test_analysis.py`
- [ ] T028 [P] [US3] Integration test for full analysis pipeline (scoring -> degradation -> Wilcoxon) in `tests/integration/test_analysis_pipeline.py`

### Implementation for User Story 3

- [ ] T029 [P] [US3] Implement `score_images.py` to load INT8 quantized VLM reward models (Aesthetics, Prompt Adherence, Identity) and score all images (Pilot and Full) in `code/scoring.py`
- [ ] T030 [US3] Implement `compute_degradation.py` to calculate mean score degradation (Base - RL) for ID and OOD sets separately. **Input**: VLM scores from T029. **Output**: `data/results/degradation_scores.csv` in `code/analysis.py`.
- [ ] T031 [US3] Implement `calculate_gap.py` to compute the "Generalization Gap" (OOD degradation - ID degradation) for each prompt. **Input**: Degradation scores (T030) AND Human Ground Truth scores (T034_human_ground_truth) for validation. Output: `data/results/gap_scores.csv` in `code/analysis.py`.
- [ ] T032 [US3] Implement `statistical_test.py` to perform **Wilcoxon signed-rank test** with **10,000 bootstrap resampling iterations** on the paired degradation values (Base vs RL) to determine significance (p < 0.05) as per FR-007. Output: `data/results/wilcoxon_results.json` in `code/analysis.py`.
- [ ] T033 [US3] Implement `statistical_test.py` (Gap Test) to perform **Independent Samples T-Test (Welch's t-test)** on the gap distributions (ID gap vs OOD gap) to determine significance as per Plan. **Input**: Gap scores (T031) AND Human Ground Truth scores (T034_human_ground_truth) for validation. Output: `data/results/welch_results.json` in `code/analysis.py`.
- [ ] T034_human_ground_truth [US3] Implement `human_proxy.py` to fetch and load a **static, human-annotated benchmark dataset** (e.g., from a public research repository) to serve as independent ground truth. **Output**: `data/results/human_ground_truth_scores.csv`. **Must run before T031/T033**. Note: This is for validation in T031/T033, NOT an input to T030. in `code/human_proxy.py`.
- [ ] T035 [US3] Implement `variance_flagging.py` to calculate score variance per prompt (e.g., using IQR or Coefficient of Variation) and flag prompts exceeding a predefined threshold (defined in `code/config.py`) for manual review. Output: `data/results/variance_flags.csv` in `code/analysis.py`.
- [ ] T036 [US3] Generate final report in `data/reports/generalization_gap_report.md` containing: (1) Mean degradation, (2) Wilcoxon statistic (T032), (3) Welch's statistic (T033), (4) Power analysis (T034_pilot_power_gate), (5) **Validation**: Comparison of calculated gap against Human Ground Truth (T034_human_ground_truth) to rule out circular dependency, (6) Variance flags (T035). in `code/analysis.py`.
- [ ] T037 [US3] Add logging for scoring progress, statistical results, and report generation in `code/analysis.py`.
- [ ] T038 [US3] Implement `power_limitation_report.py` to generate a specific "Power Limitation" section in the final report if T034_pilot_power_gate blocked the full run due to feasibility constraints. Output: `data/reports/power_limitation_notes.md` in `code/analysis.py`.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T039 [P] Documentation updates in `docs/` (README, quickstart.md)
- [ ] T040 Code cleanup and refactoring for memory efficiency
- [ ] T041 Performance optimization: profile inference loop and optimize batch sizes
- [ ] T042 [P] Additional unit tests for edge cases (empty datasets, model load failures) in `tests/unit/`
- [ ] T043 Security hardening: ensure no PII in logs or outputs
- [ ] T044 Run `quickstart.md` validation to ensure full pipeline reproducibility

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
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Requires prompt sets from US1
  - **Pilot** (T020a) requires T015a
  - **Full** (T020b) requires T034_pilot_power_gate (Power Analysis) and T015b
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Requires generated images from US2
  - **Pilot Analysis** (T034_pilot_power_gate) requires T020a
  - **Full Analysis** (T030-T036) requires T020b

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority
- **Critical Order (US1)**: T015a (Pilot Curate) -> T016 (Validate) -> T020a (Pilot Infer) -> T034_pilot_power_gate (Power Analysis) -> [Gate Check] -> T015b (Full Curate) -> T020b (Full Infer)
- **Critical Order (US3)**: T034_human_ground_truth (Generate Ground Truth) -> T029 (Score) -> T030 (Degradation) -> T031 (Gap) -> T032 (Wilcoxon) & T033 (Welch) -> T036 (Report with Human Proxy Validation)
- **Critical Order (Human Proxy)**: T034_human_ground_truth (Generate Ground Truth) -> T031/T033 (Validate against Ground Truth). T034_human_ground_truth does NOT feed T030.

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
Task: "Unit test for SHA-256 checksum verification in tests/unit/test_data_acquisition.py"
Task: "Unit test for latent-space similarity check in tests/unit/test_prompt_curation.py"

# Launch all models for User Story 1 together:
Task: "Implement download_models.py in code/data_acquisition.py"
# Note: T015a (Pilot) MUST run BEFORE T016 (Validate). T015b (Full) MUST wait for T034_pilot_power_gate.
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Pilot only: T015a, T016)
4. **STOP and VALIDATE**: Test User Story 1 independently (Pilot)
5. Run T034_pilot_power_gate (Power Analysis) to determine feasibility of Full Run
6. If feasible, proceed to T015b/T020b. If not, document limitation (T038).

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 (Pilot) → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 (Pilot Inference) → Test independently → Deploy/Demo
4. Run Power Analysis (T034_pilot_power_gate) → Decide on Full Run
5. Add User Story 1 (Full) & User Story 2 (Full) → Test independently → Deploy/Demo
6. Add User Story 3 (Full Analysis) → Test independently → Deploy/Demo
7. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (Pilot)
   - Developer B: User Story 2 (Pilot Inference)
   - Developer C: User Story 3 (Scoring/Analysis logic)
3. Pilot completes → T034_pilot_power_gate runs → Decision made
4. Team proceeds to Full Run (T015b, T020b, T030-T036)

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **Critical Constraint**: All inference must run on CPU-only (no CUDA, no 8-bit base models) to meet free-tier constraints.
- **Critical Constraint**: OOD prompts must be validated for < 0.3 cosine similarity to ID centroids to ensure data integrity.
- **Critical Constraint**: Statistical analysis must use **BOTH** Wilcoxon signed-rank test (paired) **AND** Welch's t-test (independent) as per Spec FR-007 and Plan.
- **Critical Constraint**: Human Proxy must use **static human-annotated data**, not a VLM, to break circular dependency. It is used for validation in the Report (T031/T033/T036), not as an input to Degradation (T030).
- **Critical Constraint**: Power Analysis (T034_pilot_power_gate) is a **GATE**. It must block Full Generation (T015b) if feasibility is not met.
- **Critical Constraint**: T015a (Pilot) and T015b (Full) are distinct tasks with distinct dependencies. Do not reuse IDs.