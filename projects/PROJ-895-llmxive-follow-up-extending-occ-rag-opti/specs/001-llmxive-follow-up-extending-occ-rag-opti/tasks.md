# Tasks: llmXive follow-up: extending "OCC-RAG: Optimal Cognitive Core for Faithful Question Answering"

**Input**: Design documents from `/specs/001-llmxive-occrag-sparse-core/`
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

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001.1 **Project Initialization**: Create the root directory `projects/PROJ-895-llmxive-follow-up-extending-occ-rag-opti/` and the following subdirectories: `code/`, `data/`, `tests/`, `paper/`. **Explicitly create** `data/raw/` and `data/processed/` inside `data/`. **Explicitly create** `tests/contract/`, `tests/integration/`, `tests/unit/` inside `tests/`. **Explicitly create** `paper/draft.md` with a placeholder template containing sections: Introduction, Methodology, Results, Discussion.
- [ ] T001.2 **Code Directory & Requirements**: Create `code/` directory. Create `code/requirements.txt` with the exact content: `torch (cpu-only), transformers, scikit-learn, pandas, numpy, datasets`. **Explicitly exclude** `bitsandbytes` and other 8-bit/4-bit quantization libraries.
- [ ] T001.3 **Data Directory Structure**: Create `data/` directory with subdirectories `data/raw/` and `data/processed/`.
- [ ] T001.4 **Tests Directory Structure**: Create `tests/` directory with subdirectories `tests/contract/`, `tests/integration/`, `tests/unit/`.
- [ ] T001.5 **Paper Directory**: Create `paper/` directory. Create `paper/draft.md` with a placeholder template containing sections: Introduction, Methodology, Results, Discussion.
- [X] T002 [P] Initialize Python 3.11 project with `torch` (CPU-only wheel), `transformers`, `scikit-learn`, `pandas`, `numpy`, `datasets` in `code/requirements.txt`. **Explicitly exclude** `bitsandbytes` and other 8-bit/4-bit quantization libraries that depend on GPU to align with CPU-only constraints.
- [X] T003 [P] Configure linting and formatting tools. **Create** `.flake8` configuration file with `max-line-length = 88`, `ignore = E203, E501, W503`, and `exclude =.git,__pycache__,venv`. **MUST COMPLETE BEFORE T004** to ensure linting tools are available for subsequent script execution.
- [X] T003.1 [P] **Black Configuration**: Create or update `pyproject.toml` to include the exact TOML block:
  ```toml
  [tool.black]
  line-length = 88
  target-version = ['py311']
  ```
  **MUST CREATE** `pyproject.toml` if it does not exist.
- [X] T003.2 [P] **Isort Configuration**: Create or update `pyproject.toml` to include the exact TOML block:
  ```toml
  [tool.isort]
  profile = "black"
  line_length = 88
  ```
  **MUST CREATE** `pyproject.toml` if it does not exist.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Implement `code/utils/dataset_loader.py` to fetch the specific dataset `nlp4research/occ-rag-synthetic-corpus` from HuggingFace Datasets, ensuring checksum verification. **MUST FAIL LOUDLY** if the real fetch fails; do not implement synthetic fallbacks. **Requirement**: The loader MUST define `DATA_SOURCE_ID` as a string in the format `huggingface:{dataset_id}:{revision}:{split}` and assert this format before attempting fetch. If the fetch fails, raise `ValueError` with the specific error message.
 - *Note: Foundational blocker. If fetch fails, manual fetch and upload to `data/raw/` is required before proceeding.*
- [X] T004.1 [P] **Model Download**: Download the frozen OCC-RAG model weights from `nlp4research/occ-rag-1.7b-frozen` (HuggingFace). **MUST USE** `huggingface_hub.hf_hub_download` with `local_dir_use_symlinks=False` and a **layer-wise streaming download strategy** to ensure the file is written directly to disk without loading the full file into RAM, preventing memory spikes before T006's layer-wise loading logic. Ensure the artifact is ready for layer-wise loading. **If** the specific path `nlp4research/occ-rag-1.7b-frozen` fails, **log a descriptive error and halt execution**; do not fallback to synthetic or guessed paths. Manual fetch and upload to `data/raw/` is required.
- [X] T004.2 [P] **Dataset Fetch**: Fetch the raw dataset `nlp4research/occ-rag-synthetic-corpus` (or manual upload if automated fetch fails). **Sample [deferred] examples** (matching T008.4 requirement) using `CONFIG.SAMPLE_SEED` and save to `data/processed/sampled_corpus.jsonl`. Ensure the sample size is sufficient for downstream tasks like T008.4 (10k examples). Record the sampling logic and checksum in `data/checksums.json`. **Manual Fallback**: If automated fetch fails, log specific error and provide checksum-verified path for manual upload to `data/raw/`.
- [X] T004.3 [P] **Dataset Sampling Logic**: Implement sampling logic in `code/utils/dataset_loader.py` or a separate script: 'Use `datasets.load_dataset(..., split='train').shuffle(seed=CONFIG.SAMPLE_SEED).select(range(CONFIG.SAMPLE_SIZE))` to sample exactly `CONFIG.SAMPLE_SIZE` examples from the fetched dataset. Save to `data/processed/sampled_corpus.jsonl`.'
- [X] T005 [P] Implement `code/utils/faithfulness_score.py` to calculate the "Context Faithfulness Score" (weighted ConFiQA accuracy + citation precision) on CPU.
- [X] T006 [P] Implement `code/utils/masking.py` with layer-wise loading logic to ensure memory usage remains within acceptable limits for CPU-only execution.
- [X] T007 Create `data/raw/` directory structure and `data/checksums.json` for artifact tracking.
- [X] T008 [P] Setup `code/00_config.py` to define random seeds, CPU-only device constraints, and **baseline values** for empirical quantities. Define keys: `MASK_FRACTIONS = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]` (for iterative sweep), `RETENTION_PCT = 50`, `FINE_TUNE_SAMPLE_SIZE = 10000`, `SAMPLE_SEED = 42`, `MAX_RAM_THRESHOLD = 6.5`, `SAMPLE_SIZE = 10000`. **Note**: `MASK_FRACTIONS` is the definitive list for the iterative sweep; the config serves as the baseline for the initial run, but the sweep logic in T009/T010 dynamically iterates through this list, overriding any single fixed fraction assumption.
- [X] T008.4 [P] **Define and Sample Fine-Tuning Dataset**: Using `CONFIG.SAMPLE_SEED`, sample exactly `CONFIG.FINE_TUNE_SAMPLE_SIZE` (10000) examples from `data/processed/sampled_corpus.jsonl` (from T004.2) and save to `data/processed/finetune_subset.jsonl`. **Sampling Logic**: 'Use `itertools.islice` on a shuffled iterator with `CONFIG.SAMPLE_SEED` to extract exactly 10000 rows. Save to `data/processed/finetune_subset.jsonl`.' Record the checksum in `data/checksums.json`. **Note**: While [deferred] is the default for the MVP, this value is a variable parameter to be determined in the research phase; the task uses the default for executability.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Sparse Sub-network Identification via Gradient-Free Sensitivity (Priority: P1) 🎯 MVP

**Goal**: Execute gradient-free sensitivity analysis to identify critical parameters for faithfulness

**Independent Test**: Can be fully tested by running the sensitivity analysis script on a subset of the synthetic corpus and verifying that the output CSV correctly lists parameters ranked by sensitivity score, with a clear distinction between high-sensitivity and low-sensitivity parameters compared to random masking.

### Implementation for User Story 1

- [X] T009 [US1] Implement masking logic in `code/utils/masking.py` to mask **both attention heads and feed-forward neurons** per layer based on a given fraction. Ensure the logic is modular and testable independently.
- [X] T009.2 [US1] **Iterative Sensitivity Sweep**: Implement logic in `code/01_sensitivity_analysis.py` to **iterate sequentially through `CONFIG.MASK_FRACTIONS`** (10 steps). **Invoke the masking logic from T009** for each fraction to mask the specified percentage of parameters per layer. Run inference on a representative set of samples for each fraction and record the faithfulness score. **Clarification**: `CONFIG.MASK_FRACTIONS` is a **baseline for the MVP** to ensure executability; the 'iterative search' (T032) or research phase will determine the final scientific values for the '[deferred]' requirement of FR-001. This task satisfies the '10 steps' requirement with a default sweep.
- [X] T010 [US1] **Random Baseline Generation & Aggregation**: Implement logic in `code/01_sensitivity_analysis.py` to run a control baseline of multiple random masking iterations and aggregate the results. **Crucially, these iterations must correspond to the 10 fractions in `CONFIG.MASK_FRACTIONS`**, masking a random subset of parameters for each fraction. This ensures the baseline matches the specific sweep's spectrum.
  - **Step 1 (Generate Iterations)**: For each of the 10 random masking iterations, **stream the results row-by-row** to `data/processed/random_baseline_iterations.csv` to prevent RAM overflow. The CSV MUST contain columns: `iteration_id`, `mask_fraction`, `layer_id`, `param_id`, `faithfulness_score`. **Do NOT store raw per-parameter rows in memory**; write directly to disk. **Random Masking Algorithm**: 'For each layer, select `mask_fraction * total_params` indices uniformly at random using `numpy.random.choice` with `CONFIG.SAMPLE_SEED`. Mask these parameters to zero.'
  - **Step 2 (Aggregate)**: **Stream read** `data/processed/random_baseline_iterations.csv` and compute the mean and variance of `faithfulness_score` for each `param_id` across the 10 iterations. **Aggregation Logic**: 'Use `pandas.read_csv` to stream, then `groupby('param_id').agg(['mean', 'var'])` to compute aggregates.' Save the aggregated baseline (one row per `param_id` with columns: `param_id`, `mean_faithfulness`, `variance_faithfulness`) to `data/processed/random_baseline_summary.csv`. This artifact is required for T011 delta calculation.
- [X] T011 [US1] Implement logic in `code/01_sensitivity_analysis.py` to calculate `delta_faithfulness` for each masked configuration relative to the **aggregated baseline** (mean/variance) in `data/processed/random_baseline_summary.csv` (FR-002). **DEPENDS ON**: T010 (Step 2).
- [X] T012 [US1] Ensure `code/01_sensitivity_analysis.py` loads the frozen OCC-RAG-1.7B model using layer-wise loading to stay within 7 GB RAM (FR-006).
- [X] T012.1 [US1] Implement memory monitoring and logging logic within `code/01_sensitivity_analysis.py`. **Measure the peak resident set size (RSS) of the Python process** during the sensitivity loop. **Measurement Method**: 'Use `psutil.Process().memory_info().rss` to measure peak RSS.' **If** peak RSS > 7 GB, the script MUST fail hard with an error message. **Do not** trigger sampling as a fallback; sampling is handled in T004.2. Log peak RSS to `data/processed/memory_log.json` to satisfy SC-003.
- [X] T013 [US1] Write output to `data/processed/sensitivity_results.csv` with columns: `layer_id`, `param_id` (formatted as `layer_id.param_type.param_index`), `sensitivity_score`, `delta_faithfulness`, `random_baseline_score` (US1-Acceptance-1).
- [X] T013.1 [US1] Run inference on the **original** (unpruned) OCC-RAG-1.7B model on the held-out test set to generate per-sample faithfulness scores, saving the result to `data/processed/original_faithfulness_scores.csv` (required for FR-005 paired t-test in T023). **Explicitly load a fresh copy of the frozen model** after the sensitivity loop to ensure no state contamination. **Inference Parameters**: 'Run inference with `batch_size=1`, `max_length=512`, `do_sample=False`.' This artifact is a shared prerequisite for T023.
- [X] T014 [US1] Implement logic to identify the "Critical Sub-network" candidate by sorting parameters by magnitude of performance drop relative to random baseline, using `CONFIG.RETENTION_PCT` (from T008) to determine the cutoff. Save the list of top parameters to `data/processed/critical_subnetwork_ids.csv`. **Clarification**: `CONFIG.RETENTION_PCT = 50` is a **baseline for the MVP** to ensure executability; the 'identify critical sub-network' step implies a dynamic determination to be refined in the research phase (T032). This task satisfies the 'top [deferred]' requirement with a default value.
- [X] T010.4 [US1] **Generate Matching Random Subset**: **Read the row count from `data/processed/critical_subnetwork_ids.csv`** (produced by T014) to determine the target size. Using `CONFIG.SAMPLE_SEED`, generate a random subset of indices (`data/processed/random_subset_indices.csv`) of the **exact same size** as the critical sub-network. This artifact is required for SC-005 collinearity check. **DEPENDS ON**: T014, T015.
- [X] T015 [US1] Add edge case handling: flag if sensitivity delta < `0.01` (hard-coded per spec). **If** the flag is raised, output an empty `critical_subnetwork_ids.csv` and set a `no_sparse_core` flag in `data/processed/edge_case_flags.json`. **Explicitly link this flag** to the failure of Critical Sub-network identification.

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Pruned Model Construction and Lightweight Re-mid-training (Priority: P2)

**Goal**: Construct a pruned model retaining only critical parameters and perform lightweight fine-tuning

**Independent Test**: Can be fully tested by loading the pruned model architecture, running inference on the held-out test set, and confirming that the model structure matches the pruning mask (zeroed weights) and that the fine-tuning process completes without CUDA dependency.

### Implementation for User Story 2

- [X] T016 [US2] Implement `code/02_prune_model.py` to construct `OCC-RAG-Pruned-{retention_pct}B` by retaining only the top `CONFIG.RETENTION_PCT` of parameters from `data/processed/critical_subnetwork_ids.csv` (generated by T014) and setting others to zero (FR-003).
- [X] T016.1 [US2] Log the selected `CONFIG.RETENTION_PCT` and the resulting number of retained parameters to `data/processed/pruning_config.log` for auditability.
- [X] T017 [US2] Ensure `code/02_prune_model.py` preserves the original architecture topology even with zeroed weights to maintain inference compatibility (Edge Case 2). **Validation Checks**: 'Verify all weight tensors are non-None' and 'check tensor shapes match original' before saving.
- [X] T018 [US2] Save pruned weights to `data/processed/pruned_model_weights.pt`
- [X] T019 [US2] Implement `code/03_finetune_pruned.py` to perform lightweight fine-tuning on the `data/processed/finetune_subset.jsonl` (artifact from T008.4) using `CONFIG.SAMPLE_SEED` for deterministic sampling and a low learning rate (FR-004).
- [X] T019.1 [US2] Generate a checksum of the `data/processed/finetune_subset.jsonl` file and record it in `data/checksums.json` to satisfy Constitution Principle III (Data Hygiene).
- [X] T019.2 [US2] **Log Step-Level Gradients**: Implement logic in `code/03_finetune_pruned.py` to **measure and log the gradient magnitude per step** (averaged over steps) to `data/processed/gradient_log.csv`. **Gradient Extraction Logic**: 'Access gradients via `model.parameters()`, compute L2 norm per parameter, average across all parameters to get `avg_gradient_magnitude` per step.' The log must contain columns `epoch_id`, `step_id`, `avg_gradient_magnitude`.
- [X] T019.3 [US2] **Compute Epoch-Level Gradient Averages**: Implement logic in `code/03_finetune_pruned.py` to **aggregate step-level gradients** from `data/processed/gradient_log.csv` into epoch-level metrics (mean of `avg_gradient_magnitude` per epoch). Save the epoch-level averages to `data/processed/epoch_gradient_averages.csv`. This data is required for T020's early stopping check.
- [X] T020 [US2] Implement early stopping in `code/03_finetune_pruned.py` based on **epoch-level gradient magnitude < 1e-4 for 3 consecutive epochs** (FR-004, US2-Acceptance-2). **Read the epoch-level averages from T019.3** to perform this check.
- [X] T021 [US2] Ensure `code/03_finetune_pruned.py` runs entirely on CPU within 4 hours and uses standard CPU optimizers (AdamW) (FR-006, US2-Acceptance-2).
- [X] T022 [US2] Add logging to `code/03_finetune_pruned.py` to report final faithfulness score and handle collapse scenarios without falsely claiming recovery (Edge Case 3).
- [X] T022.1 [US2] Run inference on the **fine-tuned pruned model** on the held-out test set to generate per-sample faithfulness scores, saving the result to `data/processed/pruned_faithfulness_scores.csv` (required for FR-005 paired t-test).

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Statistical Validation of Pruning Impact (Priority: P3)

**Goal**: Compare performance of pruned vs. original model using paired t-test

**Independent Test**: Can be fully tested by running the statistical validation script on the results of the original and pruned models and verifying that the p-value is calculated correctly and the conclusion (significant or not) is reported.

### Implementation for User Story 3

- [X] T023 [US3] Implement `code/04_statistical_validation.py` to collect per-sample faithfulness scores from `data/processed/original_faithfulness_scores.csv` (generated by T013.1) and `data/processed/pruned_faithfulness_scores.csv` (generated by T022.1) (FR-005).
- [X] T023.0 [US3] **Validate Sample ID Alignment**: Verify that `sample_id` columns in `original_faithfulness_scores.csv` and `pruned_faithfulness_scores.csv` match exactly (same set, same count). **Validation Logic**: 'Compare `set(original_df['sample_id'])` and `set(pruned_df['sample_id'])`. If not equal, raise `ValueError`.' Log the count and any mismatches to `data/processed/pairing_validation.log`. **Fail** if mismatches are found.
- [X] T023.1 [US3] **Align and Pair Per-Sample Scores**: Implement logic to merge `original_faithfulness_scores.csv` and `pruned_faithfulness_scores.csv` by `sample_id`. Sort both datasets by `sample_id` to ensure exact 1:1 mapping and identical order. Save the paired dataset to `data/processed/paired_scores.csv`.
- [X] T024 [US3] Implement paired t-test logic in `code/04_statistical_validation.py` on the **paired** dataset from T023.1 to calculate p-value and confidence interval (FR-005, US3-Acceptance-1).
- [X] T025 [US3] Implement logic to flag performance drop as statistically significant if p < 0.05, or not significant if p ≥ 0.05 (US3-Acceptance-2 & 3).
- [X] T026 [US3] **Collinearity Check**: **Join** `data/processed/critical_subnetwork_ids.csv` and `data/processed/random_subset_indices.csv` with `data/processed/sensitivity_results.csv` (from T013) to extract the corresponding **numerical sensitivity score vectors** for the selected sub-network and the random subset. Compute the **Pearson correlation** between these two score vectors. **Correlation Method**: 'Use `scipy.stats.pearsonr` to compute correlation. Handle NaNs by filtering them out before correlation.' Flag if correlation > 0.2 (SC-005).
- [X] T027 [US3] Write final validation report to `data/processed/statistical_validation_report.json`

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T028.1 [P] Update `paper/draft.md` Section 3.1 with sensitivity results from `sensitivity_results.csv`.
- [X] T028.2 [P] Update `paper/draft.md` Section 4.2 with t-test results from `statistical_validation_report.json`.
- [X] T029 Code cleanup and refactoring of `code/utils/` modules
- [X] T030 [P] Add unit tests for `masking.py` and `faithfulness_score.py` in `tests/unit/`
- [X] T031 [P] Run `quickstart.md` validation to ensure end-to-end reproducibility on free-tier runner. **Dependency**: This task MUST be executed only after the completion of all User Stories (Phase 3, 4, 5) and any Review Resolution tasks (if applicable).
- [X] T032 [P] **Optional Research Search**: If initial results (T014) suggest the fixed `RETENTION_PCT` ([deferred]) is suboptimal, implement an iterative search protocol to optimize `MASK_FRACTIONS` and `RETENTION_PCT` against the delta metric. Document findings in `research.md`. This task is **optional** and does not block the MVP.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
 - User stories can then proceed in parallel (if staffed)
 - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Phase N)**: Depends on all desired user stories being complete. **T031 (Final Validation) MUST be completed after all User Stories and any Review Resolution tasks.**
- **Review Resolution**: Tasks T033-T036 were removed due to scope creep (not authorized by spec). No tasks remain in this phase.

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Depends on T014 (Sensitivity Results) to identify parameters to prune
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on T022.1 (Fine-tuned model inference) and T013.1 (Original model inference)

### Within Each User Story

- Models/Utils before services
- Services before endpoints/scripts
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] (T004, T004.1, T004.2, T004.3, T005, T006, T008, T008.4) can run in parallel
- Once Foundational phase completes, T009-T015 (US1) can start
- T016-T022.1 (US2) depends on US1 output but can start as soon as US1 CSV is generated
- T023-T027 (US3) depends on outputs from US1 and US2
- T032 (Optional Search) can run in parallel with T028-T030 (Polish)

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently (verify CSV output and sensitivity ranking)
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Add Phase N (Polish) → Final documentation and cleanup
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
 - Developer A: User Story 1 (Sensitivity Analysis)
 - Developer B: User Story 2 (Pruning & Fine-tuning) - *Note: Must wait for T014 output*
 - Developer C: User Story 3 (Statistical Validation) - *Note: Must wait for T022.1 output*
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
- **Constraint Reminder**: All tasks MUST run on CPU-only free-tier CI (CPU, limited RAM, time-limited). No GPU, no 8-bit/4-bit quantization.
- **Data Integrity**: All datasets must be fetched from real sources (GitHub/Zenodo/HF); no synthetic/fake data generation tasks. **Strictly no synthetic fallbacks** in `dataset_loader.py`.
- **Fixed Values**: Empirical quantities (MASK_FRACTIONS, RETENTION_PCT, SAMPLE_SIZE) are set to fixed baseline values in T008 to ensure pipeline executability. Optional search logic is in T032.
- **Review Resolution**: Tasks T033-T036 (Data Source, Architecture Validation, Power Analysis, Normalization) were removed as they constituted scope creep not authorized by the spec. The spec's requirements are fully met by the remaining tasks.