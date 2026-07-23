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
- [X] T002 Initialize Python project with `diffusers`, `transformers`, `torch`, `scikit-learn`, `pandas`, `numpy`, `requests`, `huggingface_hub`, `seaborn`, `datasets`, `pytest`, `statsmodels`, `robust` dependencies in `code/requirements.txt`
- [ ] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools in `code/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

Examples of foundational tasks (adjust based on your project):

- [ ] T004 Setup data directory structure (`data/prompts/`, `data/models/`, `data/outputs/base/`, `data/outputs/rl_unified/`) and `.gitkeep` files
- [X] T005 [P] Implement global random seed pinning utility in `code/utils/seeding.py` (A fixed random seed will be used to ensure reproducibility.)
- [X] T006 [P] Setup configuration management for batch sizes, CPU offloading limits, and **VARIANCE_THRESHOLD key** in `code/config.py`
- [X] T007 Create base data models (PromptSet, ModelWeights, GeneratedImage, EvaluationScore) in `code/models/entities.py`
- [X] T008 Configure logging infrastructure to `code/utils/logger.py` with file rotation for long-running jobs
- [X] T009 Setup environment configuration management for HF token and cache paths in `code/config.py`
- [X] T006a [P] [US1] Implement `dependency_check.py` to verify `diffusers`/`transformers` compatibility with Qwen-Image-2.0 by loading the model config and checking for required ops; **MUST abort if specific unlisted ops are required** to mitigate the risk stated in the Spec's 'Assumptions' section. in `code/data/dependency_check.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition and Prompt Curation (Priority: P1) 🎯 MVP

**Goal**: Acquire model weights and curate leakage-free prompt sets (In-Distribution vs OOD)

**Independent Test**: Verify model weights exist with correct SHA-256 checksums and Verify model weights exist with correct SHA-256 checksums and OOD prompts have < 0.3 cosine similarity to ID centroids. [UNRESOLVED-CLAIM: c_1ea8e85d — status=not_enough_info]

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Unit test for SHA-256 checksum verification in `tests/unit/test_data_acquisition.py`
- [X] T011 [P] [US1] Unit test for latent-space similarity check (< 0.3 threshold) in `tests/unit/test_prompt_curation.py`
- [X] T012 [P] [US1] Integration test for full download and validation flow in `tests/integration/test_data_pipeline.py`

### Implementation for User Story 1

- [X] T013 [P] [US1] Implement `download_models.py` to fetch `Qwen/Qwen-Image-2.0` and `Qwen/Qwen-Image-2.0-RL` from Hugging Face with retry logic (limited attempts, exponential backoff) in `code/data/download_models.py`
- [X] T014 [US1] Implement `verify_checksums.py` to **verify downloaded weights by computing local SHA-256 hashes and comparing against hardcoded known values from the official Qwen-Image-2.0 release manifest**. in `code/data/verify_checksums.py`
- [X] T015a [US1] Implement `curate_pilot.py` to generate the **Pilot** prompt sets (N=20 ID, N=20 OOD). **Must include**: (1) Dynamic scaling logic to measure runtime, (2) **Iterative Re-curation Loop**: If OOD contamination is detected, re-sample from a fresh random subset of the LAION-2B Physics/History shard with a new seed; **if the shard is exhausted, fallback to LAION-4M 'Physics' category**; (3) Logging for pilot stats. **Must run BEFORE T016**. **Function Name**: `curate_pilot_prompts`. Output: `data/prompts/pilot_in_distribution.csv`, `data/prompts/pilot_ood.csv` in `code/data/curate_pilot.py`.
- [ ] T016 [US1] Implement `validate_ood.py` to compute cosine similarity between OOD embeddings and ID centroids. **Must include**: (1) Abort with `[CRITICAL: DATA LEAKAGE DETECTED]` if > 0.3 (integrated logic), (2) Logging for validation metrics. **Must run AFTER T015a**. Output: `data/prompts/validation_report.json` in `code/data/validate_ood.py`.
- [ ] T016a [US1] Implement `pipeline_gate.py` to implement the **orchestration logic** that halts the entire pipeline (exit code 1) if T016 (OOD validation) fails after 2 re-curation iterations. **MUST prevent execution of FR-003/FR-004** (T020/T020a) if the gate is not passed. in `code/utils/pipeline_gate.py`
- [ ] T015b [US1] Implement `curate_full.py` to generate the **Target** prompt sets (N=500 or Max-Feasible). **Must run ONLY after T034 (Power Analysis) confirms feasibility**. **Function Name**: `curate_full_prompts`. Output: `data/prompts/in_distribution.csv`, `data/prompts/ood.csv` in `code/data/curate_full.py`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently (Pilot only until T034 (Power Gate) clears Full Run)

---

## Phase 4: User Story 2 - CPU-Only Inference Execution (Priority: P2)

**Goal**: Generate images for both models on CPU-only environment using diffusers with float16 and offloading

**Independent Test**: Verify images are generated within time limits without OOM crashes.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T018 [P] [US2] Unit test for memory-batch calculation logic in `tests/unit/test_inference_batching.py`
- [ ] T019 [P] [US2] Integration test for single-prompt generation on CPU in `tests/integration/test_cpu_inference.py`

### Implementation for User Story 2

- [ ] T020 [P] [US2] Implement `inference.py` to load Base and RL-Unified models with `torch_dtype=torch.float16` and `device_map="cpu"` (or CPU offloading) in `code/inference/inference.py`
- [ ] T020a [US2] Implement `generate_pilot.py` to process **Pilot** prompts (from T015a) in dynamic batches. **Must include**: Memory monitoring, garbage collection, and runtime logging. **Function Name**: `generate_pilot_images`. Output: `data/outputs/pilot_base/`, `data/outputs/pilot_rl_unified/` in `code/inference/generate_pilot.py`.
- [ ] T020b [US2] Implement `generate_full.py` to process **Target** prompts (from T015b) in dynamic batches. **Must run ONLY after T034 (Power Gate) clears the sample size**. **Function Name**: `generate_full_images`. Output: `data/outputs/base/`, `data/outputs/rl_unified/` in `code/inference/generate_full.py`.
- [ ] T022 [US2] Implement `save_images.py` to save generated images to `data/outputs/base/` and `data/outputs/rl_unified/` with naming convention `{prompt_id}_{model}_{seed}.png` in `code/inference/save_images.py`
- [ ] T023 [US2] Implement `monitor_memory.py` to trigger garbage collection and reduce batch size if RAM usage approaches a high magnitude. in `code/inference/monitor_memory.py`
- [ ] T024 [US2] Add retry logic for generation failures (e.g., transient model loading issues) in `code/inference/inference.py`
- [ ] T025 [US2] Add logging for batch progress, generation time, and memory stats in `code/inference/inference.py`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently (Pilot images ready; Full images pending T034 (Power Gate))

---

## Phase 4.5: Power Analysis Gate (Critical Dependency for Full Run)

**Goal**: Determine if full-scale generation is statistically feasible before proceeding.

- [ ] T034 [US3] Implement `power_analysis.py` to calculate achieved statistical power, **Minimum Detectable Effect Size (MDES) at N=500 ** using **Cohen's d on the Generalization Gap and Pilot Degradation Variance** with **{{claim:c_7a269408}} (Wikipedia: Power (statistics), https://en.wikipedia.org/wiki/Power_(statistics))**, and a **"Variance Saturation Check" flag** (indicating if VLM score variance < 0.01) using `statsmodels` based on **Pilot** results (T020a). **CRITICAL GATE**: If required N > feasible N (prohibitively long runtime), output `STOP` and block T015b/T020b. If feasible, output `GO` and recommend N. **Output**: `data/results/power_analysis_report.json` (containing power, MDES, and Variance Saturation flag) in `code/analysis/power_analysis.py`. **Must run after T020a (Pilot Inference) and before T015b (Full Curation) / T020b (Full Inference)**.

---

## Phase 5: User Story 3 - Statistical Analysis of Generalization Gap (Priority: P3)

**Goal**: Compute score degradation and perform statistical tests on the Generalization Gap

**Independent Test**: Verify statistical test outputs correct p-values and gap metrics on synthetic data.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T026 [P] [US3] Unit test for score calculation (Aesthetics, Prompt Adherence, Identity) in `tests/unit/test_scoring.py`
- [ ] T027 [P] [US3] Unit test for Paired T-Test with HC3 implementation with mock data in `tests/unit/test_analysis.py`
- [ ] T028 [P] [US3] Integration test for full analysis pipeline (scoring -> degradation -> Paired T-Test) in `tests/integration/test_analysis_pipeline.py`

### Implementation for User Story 3

- [ ] T029 [P] [US3] Implement `score_images.py` to load INT8 quantized VLM reward models (Aesthetics, Prompt Adherence, Identity) and score all images (Pilot and Full) in `code/analysis/scoring.py`
- [ ] T030 [US3] Implement `compute_degradation.py` to calculate mean score degradation (Base - RL) for ID and OOD sets separately. **Input**: VLM scores from T029. **Output**: `data/results/degradation_scores.csv` in `code/analysis/compute_degradation.py`.
- [ ] T031 [US3] Implement `calculate_gap.py` to compute the "Generalization Gap" (OOD degradation - ID degradation) for each prompt. **Input**: Degradation scores (T030). **Output**: `data/results/gap_scores.csv` in `code/analysis/calculate_gap.py`.
- [ ] T032 [US3] Implement `statistical_test.py` to perform **Paired T-Test with Robust Standard Errors (HC3)** on the **Generalization Gap values (output of T031)** to determine significance (p < 0.05) as per FR-007. **Output**: `data/results/paired_ttest_hc3_results.json` in `code/analysis/statistical_test.py`.
- [ ] T033 [US3] Implement `statistical_test.py` (Bootstrap) to perform **Bootstrap Resampling** on the Generalization Gap distribution to ensure stability of the estimated confidence intervals as per FR-007. **Input**: Gap scores (T031). **Output**: `data/results/bootstrap_ci_results.json` in `code/analysis/statistical_test.py`.
- [ ] T045 [US3] Implement `external_consistency.py` to load the **HuggingFaceH4/image-reward** model as a proxy, calculate the Generalization Gap using this proxy model, and **Calculate Pearson correlation (r)** between the VLM-derived Gap (T031) and the Proxy-derived Gap. **Output**: `data/results/proxy_correlation.json` in `code/analysis/external_consistency.py`. **Must run after T031**.
- [ ] T035 [US3] Implement `variance_flagging.py` to calculate score variance per prompt (e.g., using IQR or Coefficient of Variation) and flag prompts exceeding a threshold defined in **`code/config.py` (key: `VARIANCE_THRESHOLD`)** for manual review. **Output**: `data/results/variance_flags.csv` (explicitly formatted for manual review workflow) in `code/analysis/variance_flagging.py`. **Depends on T006 for VARIANCE_THRESHOLD initialization**.
- [ ] T036 [US3] Generate final report in `data/reports/generalization_gap_report.md` containing: (1) Mean degradation, (2) Paired T-Test with HC3 statistic (T032), (3) Bootstrap CI (T033), (4) Power analysis (T034), (5) **Validation**: **Pearson correlation (r)** between VLM-derived Gap and Proxy-derived Gap (T045) to assess robustness, (6) Variance flags (T035). in `code/analysis/report.py`.
- [ ] T037 [US3] Add logging for scoring progress, statistical results, and report generation in `code/analysis/report.py`.
- [ ] T038 [US3] Implement `power_limitation_report.py` to generate a specific "Power Limitation" section in the final report if T034 blocked the full run due to feasibility constraints. Output: `data/reports/power_limitation_notes.md` in `code/analysis/power_limitation_report.py`.

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
 - **Full** (T020b) requires T034 (Power Gate) and T015b
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Requires generated images from US2
 - **Pilot Analysis** (T034) requires T020a
 - **Full Analysis** (T030-T036, T045) requires T020b

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority
- **Critical Order (US1)**: T015a (Pilot Curate with Loop) -> T016 (Validate) -> T016a (Pipeline Gate) -> **T020a (MUST NOT run if T016a exits non-zero)** -> T020a (Pilot Infer) -> T034 (Power Gate) -> T015b (Full Curate) -> T020b (Full Infer). **Note**: T016a explicitly enforces the abort condition preventing FR-003/FR-004.
- **Critical Order (US3)**: T029 (Score) -> T030 (Degradation) -> T031 (Gap) -> **Branch 1**: T032 (Paired T-Test on Gap, consumes T031 output) & T033 (Bootstrap) -> T036; **Branch 2**: T045 (Calculates Pearson r, consumes T031 output) -> T036. **Note**: T032 explicitly consumes the Generalization Gap from T031. T045 explicitly calculates Pearson r. T035 depends on T006 for VARIANCE_THRESHOLD.
- **Critical Order (Human Proxy)**: T045 (Calculates Pearson r) -> T036 (Report). T045 does NOT feed T030.

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
Task: "Implement download_models.py in code/data/download_models.py"
# Note: T015a (Pilot) MUST run BEFORE T016 (Validate). T015b (Full) MUST wait for T034 (Power Gate).
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Pilot only: T015a, T016, T016a)
4. **STOP and VALIDATE**: Test User Story 1 independently (Pilot)
5. Run T020a (Pilot Inference) -> T034 (Power Gate) to determine feasibility of Full Run
6. If feasible, proceed to T015b/T020b. If not, document limitation (T038).

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 (Pilot) → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 (Pilot Inference) → Test independently → Deploy/Demo
4. Run Power Analysis (T034) → Decide on Full Run
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
3. Pilot completes → T034 (Power Gate) runs → Decision made
4. Team proceeds to Full Run (T015b, T020b, T030-T036, T045)

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
- **Critical Constraint**: Statistical analysis must use **Paired T-Test with HC3 Robust Errors** and **10,000 Bootstrap iterations ** as per Spec FR-007.
- **Critical Constraint**: External consistency check (FR-008) MUST use the `HuggingFaceH4/image-reward` model (T045), not a static dataset.
- **Critical Constraint**: Power Analysis (T034) is a **GATE**. It must block Full Generation (T015b) if feasibility is not met, and must output MDES and Variance Saturation flag.
- **Critical Constraint**: T015a (Pilot) and T015b (Full) are distinct tasks with distinct dependencies. Do not reuse IDs.
- **Critical Constraint**: T015a includes a **Re-curation Loop** (up to 2 iterations) before aborting.
- **Critical Constraint**: T016a explicitly enforces the abort condition preventing FR-003/FR-004 if OOD validation fails.
- **Critical Constraint**: T032 explicitly consumes the Generalization Gap from T031.
- **Critical Constraint**: T045 explicitly calculates Pearson r.
- **Critical Constraint**: T035 depends on T006 for VARIANCE_THRESHOLD initialization.