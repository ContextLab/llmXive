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

- [ ] T001a [P] Create root project directory structure `projects/PROJ-913-llmxive-follow-up-extending-qwen-image-2/` (create if not exists)
- [ ] T001b [P] Create code directory structure `projects/PROJ-913-llmxive-follow-up-extending-qwen-image-2/code/` with subdirs `data/`, `inference/`, `analysis/`, `utils/` (create if not exists)
- [ ] T001c [P] Create data directory structure `projects/PROJ-913-llmxive-follow-up-extending-qwen-image-2/data/` with subdirs `raw/`, `models/`, `processed/`, `outputs/` (create if not exists)
- [ ] T001d [P] Create tests directory structure `projects/PROJ-913-llmxive-follow-up-extending-qwen-image-2/tests/` with subdirs `unit/`, `integration/` (create if not exists)
- [X] T002 Initialize Python project with `diffusers`, `transformers`, `torch`, `scikit-learn`, `pandas`, `numpy`, `requests`, `huggingface_hub`, `seaborn`, `datasets`, `pytest`, `statsmodels`, `robust` dependencies in `code/requirements.txt`
- [ ] T003 [P] Configure linting (ruff/flake8) and formatting (black) tools in `code/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

Examples of foundational tasks (adjust based on your project):

- [ ] T004 Setup data directory structure (`data/prompts/`, `data/models/`, `data/outputs/base/`, `data/outputs/rl_unified/`) and `.gitkeep` files
- [X] T005 [P] Implement global random seed pinning utility in `code/utils/seeding.py` (A fixed random seed will be used to ensure reproducibility.)
- [X] T006 [P] Setup configuration management for batch sizes, CPU offloading limits, `MAX_RECURATION_ITERATIONS` (default 3), and `VARIANCE_THRESHOLD` key in `code/config.py`
- [X] T007 Create base data models (PromptSet, ModelWeights, GeneratedImage, EvaluationScore) in `code/models/entities.py`
- [X] T008 Configure logging infrastructure to `code/utils/logger.py` with file rotation for long-running jobs
- [X] T009 Setup environment configuration management for HF token and cache paths in `code/config.py`
- [~] T004b [P] [US1] Implement `scan_pii.py` using `presidio` to scan `data/raw/` and `data/processed/` directories for PII. **GATE**: This task MUST run as a pre-commit hook or CI gate. If PII is detected, the build MUST fail. **Output**: `data/logs/pii_scan_report.json` (empty if clean). in `code/utils/scan_pii.py`.
- [X] T006a [P] [US1] Implement `dependency_check.py` to perform a **dry-run inference** on the Base and RL-Unified models using CPU-only execution. **MUST abort** if the dry-run triggers CUDA kernels or fails to load the model on CPU. **Function Name**: `check_cpu_compatibility`. in `code/utils/dependency_check.py`.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Acquisition & Pilot Curation (Priority: P1) 🎯 MVP

**Goal**: Acquire model weights and curate leakage-free *Pilot* prompt sets (In-Distribution vs OOD)

**Independent Test**: Verify model weights exist with correct SHA-256 checksums and Verify model weights exist with correct SHA-256 checksums and OOD prompts have < 0.3 cosine similarity to ID centroids.

### Model Acquisition (Parallel)

- [X] T013 [P] [US1] Implement `download_models.py` to fetch `Qwen/Qwen-Image-2.0` and `Qwen/Qwen-Image-2.0-RL` from Hugging Face with retry logic (limited attempts, exponential backoff) in `code/data/download_models.py`
- [X] T014 [US1] Implement `verify_checksums.py` to **verify downloaded weights by fetching the official Qwen-Image-2.0 `manifest.json` from the HF repo at the commit hash pinned in `config.py`, computing local SHA-256 hashes, and comparing against the fetched values**. in `code/data/verify_checksums.py`
- [X] T013b [P] [US1] Implement `download_vlms.py` to fetch `Aesthetics`, `Prompt Adherence`, and `Identity` VLM reward models from Hugging Face (specific IDs defined in `config.py`) with retry logic in `code/data/download_vlms.py`
- [X] T013c [P] [US1] Implement `download_proxy.py` to fetch `HuggingFaceH4/image-reward` model from Hugging Face with retry logic in `code/data/download_proxy.py`

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T010 [P] [US1] Unit test for SHA-256 checksum verification in `tests/unit/test_data_acquisition.py`
- [X] T011 [P] [US1] Unit test for latent-space similarity check (< 0.3 threshold) in `tests/unit/test_prompt_curation.py`
- [X] T012 [P] [US1] Integration test for full download and validation flow in `tests/integration/test_data_pipeline.py`

### Implementation for User Story 1 (Pilot Only)

- [~] T015a-1 [US1] Implement `curate_id_prompts.py` to generate the **In-Distribution** prompt set (N=20) by sampling from the **Qwen-Image-Bench** dataset (specific shard defined in `config.py`). **Function Name**: `curate_id_prompts`. Output: `data/prompts/pilot_in_distribution.csv` in `code/data/curate_id_prompts.py`.
- [~] T015a [US1] Implement `curate_ood_prompts.py` to generate the **Out-of-Distribution** prompt set (N=20). **Must include**: (1) Dynamic scaling logic to measure runtime, (2) **Iterative Re-curation Loop**: Re-sample from a fresh random subset of the LAION-2B Physics/History shard (shard ID pinned in `config.py`); (3) **Exhaustion Logic**: If a valid OOD candidate is not found after a configurable number of attempts (`MAX_RECURATION_ITERATIONS` from `config.py`), **ABORT with `[CRITICAL: OOD SHARD EXHAUSTED]`** (no fallback to other datasets, no fallback to synthetic, no fallback to different shards). **Function Name**: `curate_ood_prompts`. Output: `data/prompts/pilot_ood.csv` in `code/data/curate_ood_prompts.py`.
- [~] T016 [US1] Implement `validate_ood.py` to compute cosine similarity between OOD embeddings and ID centroids using **`openai/clip-vit-large-patch14`**. **Must include**: (1) **Abort Mechanism**: If similarity > 0.3, execute `sys.exit(1)` with exit code 101 and log `[CRITICAL: DATA LEAKAGE DETECTED]`; (2) **Output Schema**: Write `validation_report.json` containing `{"status": "pass|fail", "max_similarity": float, "threshold": 0.3}`. **Must run AFTER T015a-1 and T015a**. Output: `data/prompts/validation_report.json` in `code/data/validate_ood.py`.
- [ ] T016a [US1] Implement `pipeline_gate.py` to implement the **orchestration logic** that halts the entire pipeline (exit code 1) if T016 (OOD validation) fails after `MAX_RECURATION_ITERATIONS` (from `config.py`). **MUST prevent execution of FR-003/FR-004** (T020/T020a) if the gate is not passed. **This task MUST be the absolute final task of Phase 3; T020a (Pilot) and T015b (Full) MUST explicitly depend on T016a's success. If T016a fails, the pipeline halts before Phase 4.5.** in `code/utils/pipeline_gate.py`.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently (Pilot only until T034 (Power Gate) clears Full Run)

---

## Phase 4: User Story 2 - Pilot Inference Execution (Priority: P2)

**Goal**: Generate images for both models on CPU-only environment using diffusers with float16 and offloading (Pilot Run Only)

**Independent Test**: Verify images are generated within time limits without OOM crashes.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [ ] T018 [P] [US2] Unit test for memory-batch calculation logic in `tests/unit/test_inference_batching.py`
- [ ] T019 [P] [US2] Integration test for single-prompt generation on CPU in `tests/integration/test_cpu_inference.py`

### Implementation for User Story 2 (Pilot)

- [ ] T020 [P] [US2] Implement `inference.py` to load Base and RL-Unified models with `torch_dtype=torch.float16` and `device_map="cpu"` (or CPU offloading) in `code/inference/inference.py`
- [ ] T020a [US2] Implement `generate_pilot.py` to process **Pilot** prompts (from T015a-1/T015a) in dynamic batches. **Must include**: Memory monitoring, garbage collection, and runtime logging. **Must run ONLY after T016a (Pipeline Gate) succeeds**. **Function Name**: `generate_pilot_images`. Output: `data/outputs/pilot_base/`, `data/outputs/pilot_rl_unified/` in `code/inference/generate_pilot.py`.
- [ ] T022 [US2] Implement `save_images.py` to save generated images to `data/outputs/base/` and `data/outputs/rl_unified/` with naming convention `{prompt_id}_{model}_{seed}.png` in `code/inference/save_images.py`
- [ ] T023 [US2] Implement `monitor_memory.py` to trigger garbage collection and reduce batch size if RAM usage approaches a high magnitude. in `code/inference/monitor_memory.py`
- [ ] T024 [US2] Add retry logic for generation failures (e.g., transient model loading issues) in `code/inference/inference.py`
- [ ] T025 [US2] Add logging for batch progress, generation time, and memory stats in `code/inference/inference.py`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently (Pilot images ready; Full images pending T034 (Power Gate))

---

## Phase 4.5: Power Analysis Gate (Critical Dependency for Full Run)

**Goal**: Determine if full-scale generation is statistically feasible before proceeding.

- [ ] T034 [US3] Implement `power_analysis.py` to calculate achieved statistical power, **Minimum Detectable Effect Size (MDES) at N=500 ** using **Cohen's d on the Generalization Gap and Pilot Degradation Variance** with ** (Wikipedia: Power (statistics), https://en.wikipedia.org/wiki/Power_(statistics))**, and a **"Variance Saturation Check" flag** (indicating if VLM score variance < 0.01) using `statsmodels` based on **Pilot** results (T020a). **CRITICAL GATE**: If required N > feasible N (prohibitively long runtime), output `STOP` and block T015b/T020b. If feasible, output `GO` and recommend N. **Blocking Mechanism**: Write `gate_status.json` with `{"status": "GO|STOP", "reason": "string"}`. **Output**: `data/results/power_analysis_report.json` (containing power, MDES, and Variance Saturation flag) in `code/analysis/power_analysis.py`. **Must run after T020a (Pilot Inference) and before T015b (Full Curation) / T020b (Full Inference)**.

---

## Phase 5: User Story 1 & 2 - Full Inference & User Story 3 - Statistical Analysis (Priority: P3)

**Goal**: Generate full dataset (if feasible) and perform statistical analysis on the Generalization Gap

**Independent Test**: Verify statistical test outputs correct p-values and gap metrics on synthetic data.

### Implementation for Full Inference (Post-Power Gate)

- [ ] T015b [US1] Implement `curate_full.py` to generate the **Target** prompt sets (N=500 or Max-Feasible). **Must run ONLY after T034 (Power Gate) confirms feasibility**. **Function Name**: `curate_full_prompts`. Output: `data/prompts/in_distribution.csv`, `data/prompts/ood.csv` in `code/data/curate_full.py`.
- [ ] T020b [US2] Implement `generate_full.py` to process **Target** prompts (from T015b) in dynamic batches. **Must run ONLY after T034 (Power Gate) clears the sample size**. **Must integrate T023 (`monitor_memory.py`) to enforce <7GB RAM and Runtime constraints

The research question, the method, and the references remain unchanged.**. **Function Name**: `generate_full_images`. Output: `data/outputs/base/`, `data/outputs/rl_unified/` in `code/inference/generate_full.py`.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [ ] T026 [P] [US3] Unit test for score calculation (Aesthetics, Prompt Adherence, Identity) in `tests/unit/test_scoring.py`
- [ ] T027 [P] [US3] Unit test for Paired T-Test with HC3 implementation with mock data in `tests/unit/test_analysis.py`
- [ ] T028 [P] [US3] Integration test for full analysis pipeline (scoring -> degradation -> Paired T-Test) in `tests/integration/test_analysis_pipeline.py`

### Implementation for User Story 3 (Statistical Analysis)

- [ ] T029 [P] [US3] Implement `score_images.py` to load INT8 quantized VLM reward models (Aesthetics, Prompt Adherence, Identity) and score all images (Pilot and Full) in `code/analysis/scoring.py`
- [ ] T030 [US3] Implement `compute_degradation.py` to calculate mean score degradation (Base - RL) for ID and OOD sets separately. **Input**: VLM scores from T029. **Output**: `data/results/degradation_scores.csv` in `code/analysis/compute_degradation.py`.
- [ ] T031 [US3] Implement `calculate_gap.py` to compute the "Generalization Gap" (OOD degradation - ID degradation) for each prompt. **Input**: Degradation scores (T030). **Output**: `data/results/gap_scores.csv` in `code/analysis/calculate_gap.py`.
- [ ] T032 [US3] Implement `statistical_test.py` to perform **Paired T-Test with Robust Standard Errors (HC3)** on the **paired degradation scores (Base Score - RL Score) for each prompt** to determine significance (p < 0.05 (Wikipedia: P-value, https://en.wikipedia.org/wiki/P-value)) as per **FR-006**. **Must use `statsmodels.stats.sandwich_covariance`** to calculate HC3 robust standard errors and manually compute the t-statistic; **Do NOT use `scipy.stats.ttest_rel`** for thiscalculation as it lacks HC3 support. **Output**: `data/results/paired_ttest_hc3_results.json` in `code/analysis/statistical_test.py`.
- [ ] T033 [US3] Implement `statistical_test.py` (Bootstrap) to perform **Bootstrap Resampling** on the Generalization Gap distribution to ensure stability of the estimated confidence intervals as per FR-007. **Input**: Gap scores (T031). **Output**: `data/results/bootstrap_ci_results.json` in `code/analysis/statistical_test.py`.
- [ ] T045 [US3] Implement `external_consistency.py` to load the **`HuggingFaceH4/image-reward`** model as a proxy, calculate the Generalization Gap using this proxy model, and **Calculate Pearson correlation (r)** between the VLM-derived Gap (T031) and the Proxy-derived Gap. **Must use `torch_dtype=torch.float16`**. **Output**: `data/results/proxy_correlation.json` in `code/analysis/external_consistency.py`. **Must run after T031**.
- [ ] T035 [US3] Implement `variance_flagging.py` to calculate score variance per prompt using the **Interquartile Range (IQR)** method and flag prompts exceeding a threshold defined in **`code/config.py` (key: `VARIANCE_THRESHOLD`)** for manual review. **Output**: `data/results/variance_flags.csv` (explicitly formatted for manual review workflow with columns: `prompt_id`, `score`, `variance`, `flag`) in `code/analysis/variance_flagging.py`. **Depends on T006 for VARIANCE_THRESHOLD initialization**.
- [ ] T036 [US3] Generate final report in `data/reports/generalization_gap_report.md` containing: (1) Mean degradation, (2) Paired T-Test with HC3 statistic (T032), (3) Bootstrap CI (T033), (4) Power analysis (T034), (5) **Validation**: **Pearson correlation (r)** between VLM-derived Gap and Proxy-derived Gap (T045) to assess robustness, (6) Variance flags (T035). in `code/analysis/report.py`.
- [ ] T037 [US3] Add logging for scoring progress, statistical results, and report generation in `code/analysis/report.py`.
- [ ] T038 [US3] Implement `power_limitation_report.py` to generate a specific "Power Limitation" section in the final report if T034 blocked the full run due to feasibility constraints. Output: `data/reports/power_limitation_notes.md` in `code/analysis/power_limitation_report.py`.

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T039a [P] Update `README.md` in `projects/PROJ-913-llmxive-follow-up-extending-qwen-image-2/` with installation steps and usage instructions
- [ ] T039b [P] Create `quickstart.md` in `projects/PROJ-913-llmxive-follow-up-extending-qwen-image-2/` with step-by-step pipeline execution guide
- [ ] T039c [P] Update contract schemas in `specs/001-opd-generalization-gap/contracts/` with final field definitions
- [ ] T040a [P] Profile inference loop in `inference.py` using `cProfile` to identify bottlenecks
- [ ] T040b [P] Refactor `inference.py` and `scoring.py` for memory efficiency based on profiling results
- [ ] T040c [P] Verify peak RAM usage < 7GB in `inference.py` using `tracemalloc` and log results
- [ ] T042 [P] Additional unit tests for edge cases (empty datasets, model load failures) in `tests/unit/`
- [ ] T043 [P] Additional security hardening: ensure no PII in logs or outputs (Secondary check, primary gate is T004b)
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
 - **Pilot** (T020a) requires T015a-1, T015a, and **T016a (Pipeline Gate success)**
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
- **Critical Order (US1)**: T015a-1 (ID Curate) -> T015a (OOD Curate with Loop) -> T016 (Validate) -> T016a (Pipeline Gate) -> **T020a (MUST NOT run if T016a exits non-zero)** -> T020a (Pilot Infer) -> T034 (Power Gate) -> T015b (Full Curate) -> T020b (Full Infer). **Note**: T016a explicitly enforces the abort condition preventing FR-003/FR-004.
- **Critical Order (US3)**: T029 (Score) -> T030 (Degradation) -> T031 (Gap) -> **Branch 1**: T032 (Paired T-Test on **paired degradation scores**, consumes T030 output) & T033 (Bootstrap) -> T036; **Branch 2**: T045 (Calculates Pearson r, consumes T031 output) -> T036. **Note**: T032 explicitly consumes the paired degradation array from T030 to test the mean difference. T045 explicitly calculates Pearson r. T035 depends on T006 for VARIANCE_THRESHOLD.
- **Critical Order (Human Proxy)**: T045 (Calculates Pearson r) -> T036 (Report). T045 does NOT feed T030.

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if staffed)
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
3. Complete Phase 3: User Story 1 (Pilot only: T015a-1, T015a, T016, T016a)
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
- **Critical Constraint**: All inference must run on CPU-only (no CUDA, no quantized base models). to meet free-tier constraints.
- **Critical Constraint**: OOD prompts must be validated for < 0.3 cosine similarity to ID centroids to ensure data integrity.
- **Critical Constraint**: Statistical analysis must use **Paired T-Test with HC3 Robust Errors** on **paired degradation scores** and **A sufficient number of Bootstrap iterations ** as per Spec FR-007.
- **Critical Constraint**: External consistency check (FR-008) MUST use the `HuggingFaceH4/image-reward` model (T045), not a static dataset.
- **Critical Constraint**: Power Analysis (T034) is a **GATE**. It must block Full Generation (T015b) if feasibility is not met, and must output MDES and Variance Saturation flag.
- **Critical Constraint**: T015a-1 (ID Set) and T015a (OOD Set) are distinct tasks. Do not reuse IDs.
- **Critical Constraint**: T015a includes a **Re-curation Loop** (up to `MAX_RECURATION_ITERATIONS`) before **aborting** (no fallback).
- **Critical Constraint**: T016a explicitly enforces the abort condition preventing FR-003/FR-004 if OOD validation fails.
- **Critical Constraint**: T032 explicitly consumes the **paired degradation scores** from T030 to test the mean difference.
- **Critical Constraint**: T045 explicitly calculates Pearson r.
- **Critical Constraint**: T035 depends on T006 for VARIANCE_THRESHOLD initialization.
- **Critical Constraint**: T020b MUST integrate T023 for memory monitoring.