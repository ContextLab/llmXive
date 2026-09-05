# Tasks: Predicting Molecular Surface Charge Distribution from Quantum Chemical Calculations

**Input**: Design documents from `/specs/001-predicting-molecular-surface-charge/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[S]**: Sequential (must wait for previous task in phase)
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

 Tasks MUST be organized by user story so each story can:
 - Implemented independently
 - Tested independently
 - Delivered as an MVP increment

 DO NOT keep these sample tasks in the generated tasks.md file.
 ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure per implementation plan by executing: `mkdir -p projects/PROJ-404-predicting-molecular-surface-charge-dist/{code/{data,models,utils},tests,artifacts/{reports,models,splits},data/{raw,processed}}` and creating `__init__.py` files in all `code/` subdirectories, then verifying all directories exist and contain `__init__.py`.

- [X] T002 Initialize Python 3.11 project with pinned dependencies in `code/requirements.txt`: `torch==2.1.0`, `torch-geometric==2.4.0`, `rdkit==2023.9.1`, `datasets==2.14.0`, `pandas==2.1.0`, `numpy==1.24.0`, `scikit-learn==1.3.0`.

- [X] T003 [P] Configure linting and formatting by creating `code/pyproject.toml` with `[tool.ruff]` (line-length=100) and `[tool.black]` (line-length=100) sections.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 [P] Implement seed setting and logging utility in `code/utils.py`: Define `def set_seed(seed: int) -> None` using `random`, `numpy`, and `torch` seeds; define `def get_logger(name: str) -> logging.Logger` with format `'%(asctime)s - %(name)s - %(levelname)s - %(message)s'`.

- [X] T004a [P] Define exit codes and constants in `code/utils.py`: Define `EXIT_CODE_BASELINE_LOSS = 2`, `EXIT_CODE_THRESHOLD_FAIL = 3`, and `EXIT_CODE_SUCCESS = 0` as module-level constants to be used by the evaluation and training scripts for deterministic termination.

- [X] T005 [P] Create base data model classes in `code/data/dataset.py`: Define `class MoleculeData(torch_geometric.data.Data)` with attributes `x` (atomic numbers), `pos` (coordinates), `y` (charges), and `scaffold_id` to satisfy FR-001 data model requirements.

- [X] T006 [P] Setup memory profiling and adaptive sampling logic in `code/data/loader.py`: Implement a streaming wrapper around HuggingFace dataset with `adaptive_sample_size(batch_size: int, target_gb: float) -> int` that returns `max_samples` based on measured per-molecule overhead and a predefined memory limit. This task consolidates logic from T006a and T014.

- [X] T007 [P] Implement coordinate normalization (center of mass) in `code/data/preprocess.py`: Define function to shift coordinates such that `mean(pos) == 0` for each molecule, satisfying FR-001.

- [X] T008 [S] Implement Bemis-Murcko scaffold extraction, index generation, and stream filtering in `code/data/splits.py`: Use `rdkit.Chem.Scaffolds.MurckoScaffold.GetScaffoldForMol` to generate scaffold strings, **group molecules by their scaffold ID**, and apply a fixed random seed to assign **entire groups** (all molecules sharing a scaffold) to train/val/test split indices (ensuring no scaffold appears in multiple sets). Write the indices to `artifacts/splits/splits.json` and provide a function to consume these indices to filter the `MoleculeData` stream, satisfying FR-004.

- [X] T008a [S] Wire split indices to loader in `code/data/loader.py`: Import the filtered iterator function from T008 and integrate it into the loader's `__iter__` method to ensure the streaming loader consumes the correct train/val/test splits generated by T008.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Data Pipeline Construction and Validation (Priority: P1) 🎯 MVP

**Goal**: Ingest QM9 subset with Merz-Kollman charges, validate memory constraints, and ensure data integrity.

**Independent Test**: The system can be fully tested by executing the data loading script on the free-tier runner, confirming the dataset loads into memory without OOM errors, and verifying that the extracted features match the expected schema.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [X] T010 [P] [US1] Unit test for memory profiling logic in `tests/test_loader.py`: Implement `test_adaptive_sample_size_returns_correct_limit` and assert `max_samples > 0` based on measured overhead.

- [X] T011 [P] [US1] Integration test for full data loading and schema validation in `tests/test_loader.py`: Implement `test_full_load_schema_validation` and assert `'charge' in batch.y` and schema fields match expected types. <!-- FAILED: unspecified -->

### Implementation for User Story 1

- [X] T012 [S] [US1] Implement HuggingFace dataset loader with `streaming=True` for QM (Merz-Kollman subset) in `code/data/loader.py`, consuming split indices from T008a; verify the existence of Merz-Kollman charges before proceeding.

- [X] T013 [US1] Implement "Fail Loudly" logic: raise explicit `RuntimeError` if real data fetch fails, NO synthetic fallback in `code/data/loader.py`.

- [X] T015 [US1] Implement data validation checks (non-null charges, connectivity alignment) AND specific filtering/imputation strategy for missing coordinates or undefined bonds in `code/data/loader.py`: Filter molecule if undefined bonds; for missing coordinates, implement the strategy **defined in `data-model.md`** (do not hardcode 'mean' unless specified there); assert schema validity; **explicitly check that `scaffold_id` is present and populated in the `MoleculeData` objects**; output a summary of loaded feature dimensions to the console.

- [X] T015b [S] [US1] Validate scaffold_id presence in loaded stream: After T012 loads data, explicitly check that the `scaffold_id` attribute is present and populated in the `MoleculeData` objects before proceeding to T051/T063, ensuring data integrity for scaffold checks. (Note: This logic is now integrated into T015, but T015b remains as a specific verification step in the stream pipeline).

- [X] T016 [US1] Add logging for loaded feature dimensions and memory usage in `code/data/loader.py`.

- [ ] T056a [US1] Implement full dataset checksum verification in `code/data/loader.py`: After downloading the QM9 parquet file, compute the SHA-256 hash of the **entire** file and record it in `state/projects/PROJ-404-predicting-molecular-surface-charge-dist.yaml` under `artifact_hashes`, satisfying Constitution Principle III. <!-- FAILED: unspecified -->

- [X] T081 [S] [US1] Implement explicit QM9 column name verification in `code/data/loader.py`: Add a pre-flight check that attempts to access the `partial_charges` or `charges_merkollman` key on the first streamed item; if missing, raise `ValueError` with a clear message referencing the plan's assumption about Merz-Kollman availability, ensuring the "Fail Loudly" principle is applied specifically to schema mismatches. (Moved from Phase N+1 to Phase 3 for MVP completeness).

- [X] T082 [S] [US1] Implement robust handling of "undefined bond order" in `code/data/loader.py`: Instead of filtering silently, log a warning with the specific molecule ID and the nature of the undefined bond, then apply a fallback strategy (e.g., assume single bond or skip) ONLY if the plan explicitly allows it; otherwise, raise an error to prevent data contamination. (Moved from Phase N+1 to Phase 3 for MVP completeness).

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Geometric Graph Neural Network Training (Priority: P2)

**Goal**: Implement and train a Geometric GNN (SchNet/DimeNet) on CPU, respecting time and memory limits.

**Independent Test**: The system can be tested by running the training script for a fixed number of epochs and verifying that the loss decreases, the model weights are saved, and the process completes within a reasonable wall-clock time limit.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [X] T018 [P] [US2] Unit test for SchNet/DimeNet architecture initialization in `tests/test_model.py`: Implement `test_schnet_init` and assert `model.num_parameters > 0`.

- [X] T019 [P] [US2] Integration test for training loop completion and early stopping in `tests/test_model.py`: Implement `test_training_loop_completion` and assert `final_loss < initial_loss` after 10 epochs.

### Implementation for User Story 2

- [X] T020 [P] [US2] Implement Geometric GNN (SchNet or DimeNet) architecture class in `code/models/schnet.py` inheriting from `torch.nn.Module`.

- [X] T020a [P] [US2] Configure model hyperparameters in `code/models/config.yaml`: Set `num_filters=128`, `num_gaussians=50`, `num_interaction_blocks=3`.

- [X] T021 [US2] Implement connectivity-only GNN (2D) baseline architecture in `code/models/baseline_2d.py` (ignores `pos` attribute), satisfying FR-006.

- [X] T022 [US2] Implement Atom-Type Average baseline logic in `code/models/baseline_atom.py` (returns mean charge per atomic number).

- [X] T023c [S] [US2] Construct validation data loader in `code/train.py`: Wrap the validation split from T008a into a `DataLoader` for early stopping.

- [X] T023b [S] [US2] Implement early stopping logic based on validation MAE (patience=10) in `code/train.py`.

- [X] T023 [US2] Implement training loop with Adam optimizer (lr=1e-3), a maximum number of epochs sufficient to ensure convergence in `code/train.py`: Must accept train and validation loaders, satisfying FR-003.

- [X] T024 [US2] Implement model checkpointing (save state dict < 500 MB) in `code/train.py`, satisfying FR-003.

- [X] T026 [US2] Add logging for epoch loss and validation MAE in `code/train.py`, satisfying FR-003.

- [X] T050 [US2] Implement conditional GPU check in `code/train.py`: If `torch.cuda.is_available()` is true and `KAGGLE_OFFLOAD` environment variable is NOT set, log a warning and force `device='cpu'`. If `KAGGLE_OFFLOAD` IS set, allow GPU usage, preserving the CPU-only default while enabling the valid offload path.

- [X] T053 [US2] Add training time monitoring in `code/train.py`: Implement a timer that logs the total wall-clock time after each epoch and raises a `TimeoutError` if the total time exceeds a substantial duration, allowing the process to exit gracefully before the Time-limited runner constraint

The research question remains: How does the duration of the runner constraint affect the overall search efficiency? The method involves implementing a time-bound termination condition for the runner process, as described in [Author, Year; DOI/arXiv ID]. This approach ensures that the search does not exceed a predefined temporal threshold, thereby preventing resource exhaustion while maintaining algorithmic viability. is hit.

- [ ] T058 [US2] Implement gradient norm logging in `code/train.py`: Log the L2 norm of the gradients after each backward pass to detect vanishing/exploding gradients early, writing to `artifacts/reports/gradient_norms.log`.

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Evaluation and Baseline Comparison (Priority: P3)

**Goal**: Evaluate models against test set, compare 3D GNN vs 2D GNN vs Atom-Type baseline, and validate hypothesis.

**Independent Test**: The system can be tested by loading the trained model and test set, running inference, and generating a report containing MAE, RMSE, and $R$ values.

### Tests for User Story 3 (OPTIONAL - only if tests requested) ⚠️

- [X] T040 [P] [US3] Unit test for metric calculation (MAE, RMSE, Pearson R) in `tests/test_eval.py`: Implement `test_mae_rmse_pearson_known_values` with known input/output pairs. <!-- FAILED: unspecified -->

- [X] T041 [P] [US3] Integration test for full evaluation pipeline and baseline comparison in `tests/test_eval.py`: Implement `test_full_evaluation_pipeline` and assert expected report file path and metrics.

### Implementation for User Story 3

- [X] T042 [US3] Implement evaluation script to calculate MAE, RMSE, and Pearson R in `code/eval.py`, satisfying FR-005.

- [X] T043 [US3] Implement baseline comparison logic (3D GNN vs 2D GNN vs Atom-Type) in `code/eval.py`, satisfying FR-006. <!-- FAILED: unspecified -->

- [ ] T044 [US3] Implement hypothesis validation check in `code/eval.py`: Calculate 3D GNN test MAE. **Perform two distinct checks**: 1) Absolute Threshold: Check if MAE ≤ 0.05 e. 2) Baseline Comparison: Check if 3D GNN MAE < 2D GNN MAE. **Report both outcomes separately** in the final report. **Exit with `EXIT_CODE_THRESHOLD_FAIL` (3) if Absolute Threshold fails**, and **exit with `EXIT_CODE_BASELINE_LOSS` (2) if Baseline Comparison fails**. If both pass, exit with `EXIT_CODE_SUCCESS` (0). **Explicitly write the result 'Hypothesis Validated: True/False' to `artifacts/reports/metrics.json`** to satisfy SC-008 programmatically. Satisfying FR-007 and US-3.

- [ ] T045 [US3] Calculate and report MAE deltas between test/validation and training/validation sets for generalization error detection in `code/eval.py` function `calculate_generalization_deltas`, satisfying SC-006/SC-007.

- [ ] T045a [US3] Implement explicit Generalization Gap calculation in `code/eval.py`: Calculate `generalization_gap_train_val = train_mae - val_mae` and `generalization_gap_val_test = val_mae - test_mae`. Persist these specific numeric values to `artifacts/reports/metrics.json` to satisfy SC-006 and SC-007 verification requirements.

- [ ] T047 [US3] Aggregate metrics into JSON in `code/eval.py` to `artifacts/reports/metrics.json`, satisfying FR-005.

- [ ] T048 [US3] Render final report `artifacts/reports/results.md` from aggregated data in `code/eval.py`, satisfying Constitution Principle IV.

- [ ] T069 [US3] Implement error distribution analysis in `code/eval.py`: Generate a histogram of the absolute errors (predicted - actual) and save it as `artifacts/reports/error_distribution.png` to visually inspect systematic biases.

- [ ] T051 [US3] Implement scaffold leakage verification in `code/eval.py`: Add a diagnostic step that cross-references the scaffold IDs of the test set against the training set to ensure zero overlap, raising a `ValueError` if any scaffold ID appears in both sets, to satisfy FR-004 generalization requirements.

- [ ] T054 [US3] Implement a "Hypothesis Not Validated" report generator in `code/eval.py`: If the hypothesis check (T044) fails, generate a detailed `artifacts/reports/failure_analysis.md` explaining which baseline was beaten and by how much, to aid in research iteration.

- [ ] T057 [US3] Implement a "Baseline Performance Threshold" check in `code/eval.py`: If the Atom-Type Average baseline MAE is > 0.15 e, log a warning that the baseline is too weak to be a meaningful comparison, but do not fail the run.

- [ ] T063 [US3] Implement `code/eval.py` scaffold uniqueness check: Before calculating metrics, verify that the `scaffold_id` list in the test set contains no duplicates; if duplicates are found, log a warning and filter to unique scaffolds to ensure the generalization test is statistically valid.

- [ ] T066 [US3] Implement `code/eval.py` correlation significance test: Calculate the p-value for the Pearson correlation coefficient ($R$) between predicted and actual charges using `scipy.stats.pearsonr`; if $p > 0.05$, flag the result as "Not Statistically Significant" in the final report.

- [ ] T068 [US3] Implement `code/eval.py` confidence interval calculation: Calculate 95% confidence intervals for the MAE and RMSE metrics using bootstrapping (A sufficient number of resamples) on the test set.

- [ ] T083 [S] [US3] Implement a "Generalization Gap" visualization in `code/eval.py`: Generate a bar chart comparing Train MAE, Val MAE, and Test MAE side-by-side for both the 3D GNN and the 2D baseline, saving it to `artifacts/reports/generalization_gap.png`, to visually satisfy SC-006 and SC-007.

- [ ] T087 [S] [US3] Implement a "Baseline Comparison" table in `code/eval.py`: Generate a Markdown table in `artifacts/reports/baseline_comparison.md` listing MAE, RMSE, and R for all three models (3D GNN, 2D GNN, Atom-Type) with significance stars (*) if p < 0.05, to satisfy FR-006 and FR-007 clearly.

**Checkpoint**: All user stories should now be independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T034a [P] Generate Google-style docstrings for all classes and functions in `code/` directory using `pydocstyle --count --select=D` and verify 0 errors, satisfying Constitution Principle IV.

- [ ] T035a Refactor `code/data/loader.py` to ensure streaming logic is efficient and handles chunking correctly by extracting `ChunkedIterator` class and verifying memory profile < 7GB, satisfying Constitution Principle III.

- [ ] T036a Run benchmark script `python code/data/loader.py --benchmark` and verify load time < 10 minutes, recording result in `artifacts/reports/load_time.log`, satisfying Constitution Principle VI.

- [X] T037 [P] Additional unit tests for edge cases (missing coordinates, undefined bonds) in `tests/`: Implement `test_missing_coordinates_imputation` and `test_undefined_bond_filtering` with specific assertions, satisfying Constitution Principle V.

- [X] T038 Run quickstart.md validation by executing `python code/quickstart.py --validate` and verifying exit code 0, satisfying Constitution Principle I.

- [ ] T055 [US2] Implement model size verification in `code/train.py`: Add a post-save check that verifies the saved model file size is < 500 MB; if larger, log a warning and attempt to save in a compressed format or reduce the number of saved checkpoints.

- [ ] T062 [US2] Implement `code/train.py` CPU fallback logic: If `torch.cuda.is_available()` is true but `KAGGLE_OFFLOAD` is NOT set, explicitly move the model and data to `torch.device('cpu')` and log a warning that GPU acceleration was intentionally disabled to match the free-tier constraint.

- [ ] T064 [P] [US1] Add `code/data/loader.py` batch size auto-tuning: Implement a binary search routine that finds the maximum batch size that fits in 6 GB RAM during the first molecules, then locks this batch size for the remainder of the run to maximize throughput without OOM.

- [ ] T065 [US2] Implement `code/train.py` learning rate scheduler: Add a `ReduceLROnPlateau` scheduler based on validation MAE (factor=0.5, patience=5) to improve convergence on the CPU-constrained training set.

- [ ] T067 [P] [US1] Implement `code/data/loader.py` progress bar: Add a `tqdm` progress bar to the streaming iterator that displays the number of molecules processed, estimated time remaining, and current memory usage.

- [ ] T070 [P] [US1] Implement `code/data/loader.py` checksum verification: After downloading the QM9 parquet file, verify its SHA-256 hash against the known hash stored in `state/projects/PROJ-404-predicting-molecular-surface-charge-dist.yaml` before processing.

- [ ] T071 [US2] Implement `code/train.py` checkpoint resume: Add logic to detect if a previous training run was interrupted (by checking for a `checkpoint.pt` file) and resume training from the last saved epoch with the same optimizer state.

- [ ] T072 [US3] Implement `code/eval.py` baseline sensitivity analysis: Run the Atom-Type Average baseline with different atomic number groupings (e.g., by period, by group) to determine the most effective 2D representation for comparison.

- [ ] T073 [P] [US1] Implement `code/data/loader.py` data versioning: Add a `data_version` field to the `MoleculeData` object that records the HuggingFace dataset revision hash used for the current run.

- [ ] T074 [US2] Implement `code/train.py` hyperparameter logging: Log all training hyperparameters (learning rate, batch size, number of filters, etc.) to `artifacts/reports/training_config.json` at the start of each run.

- [ ] T075 [US3] Implement `code/eval.py` model ensemble: If multiple model checkpoints are available, compute a weighted average of their predictions to see if ensemble methods improve MAE.

- [ ] T076 [P] [US1] Implement `code/data/loader.py` memory leak detection: Add a periodic check using `gc.collect()` and `psutil` to ensure memory usage does not drift upwards over long streaming sessions.

- [ ] T077 [US2] Implement `code/train.py` early stopping metric selection: Allow the user to choose between `val_mae` and `val_loss` as the metric for early stopping via a command-line argument.

- [ ] T079 [P] [US1] Implement `code/data/loader.py` parallel loading: Use `num_workers > 0` in the PyTorch DataLoader to parallelize data loading and preprocessing on the multi-core CPU runner.

- [ ] T080 [US2] Implement `code/train.py` mixed precision training: If supported, enable `torch.cuda.amp` (or CPU equivalent if available) to reduce memory usage and potentially speed up training.

---

## Phase N+1: Revision & Gap Resolution (Addressing Review Concerns)

**Purpose**: Resolve specific gaps identified in the analysis phase regarding data source verification, error handling, and reporting completeness.

- [ ] T084 [S] [US2] Implement a "Training Convergence" diagnostic in `code/train.py`: If the loss increases for 3 consecutive epochs after epoch 5, log a critical warning and suggest a learning rate reduction, writing the suggestion to `artifacts/reports/convergence_advice.md`.

- [ ] T086 [P] [US1] Implement a "Data Source Fingerprint" in `code/data/loader.py`: Record the exact HuggingFace dataset commit hash and the specific subset name used in the first line of the `artifacts/reports/data_manifest.json` to ensure full reproducibility of the input data.

- [ ] T088 [P] [US2] Implement a "Memory vs Batch Size" sweep in `code/train.py`: Before starting the main training loop, run a quick sweep (A set of molecules) to determine the maximum batch size that fits in Adequate RAM capacity., and log this as the `max_safe_batch_size` in `artifacts/reports/memory_profile.json`.

- [ ] T089 [S] [US1] Implement a "Streaming Integrity" check in `code/data/loader.py`: After the stream finishes, verify that the total number of molecules processed matches the expected count from the split indices (allowing for a small tolerance for molecules filtered due to missing data), and log a warning if the discrepancy exceeds a notable threshold.

- [ ] T090 [S] [US3] Implement a "Scaffold Distribution" report in `code/eval.py`: Count the number of unique scaffolds in the train, val, and test sets and log this distribution to `artifacts/reports/scaffold_distribution.json` to verify that the split is not trivial (e.g., all test scaffolds are singletons).
