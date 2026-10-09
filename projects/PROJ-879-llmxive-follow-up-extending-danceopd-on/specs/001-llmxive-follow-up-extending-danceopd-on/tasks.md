# Tasks: llmXive follow‑up – extending “DanceOPD: On‑Policy Generative Field Distillation”

**Input**: `spec.md`, `plan.md`, `data‑model.md`, contracts, existing code skeleton.  
**Goal**: End‑to‑end research pipeline that (1) generates teacher‑routing ground‑truth, (2) trains static decision‑tree approximations, (3) evaluates image‑fidelity degradation and statistical significance, and (4) produces reproducible artefacts for hand‑off.

---

## Phase 1 – Project scaffolding & core utilities (already completed)

- [X] T001a [P] Create project directory structure (`code/`, `data/raw/`, `data/processed/`, `data/results/`, `models/`, `tests/…`).  
- [ ] T001b [P] Add empty starter scripts (`code/main.py`, `code/00_data_fetch.py`, `code/00_data_stream.py`, `code/00_teacher_inference.py`, `code/01_train_trees.py`, `code/02_evaluate_fidelity.py`, `code/03_versioning.py`, `code/utils/timer.py`, `code/utils/stats.py`, `code/data/generate_teacher.py`, `code/models/train_tree.py`).  
- [ ] T002 Initialize `requirements.txt` (CPU‑only `torch`, `scikit‑learn`, `pandas`, `numpy`, `datasets`, `transformers`, `accelerate`, `pillow`, `scipy`, `torch‑fidelity`, `pyyaml`, `pytest`).  
- [X] T004 [P] Implement `code/utils/config.py` (seeds, paths, hyper‑parameters such as `N_TARGET=2500`, `TIMEOUT_HOURS=6`).  
- [ ] T005 [P] Stub metric functions in `code/utils/metrics.py` (`calculate_clip_score`, `calculate_fid`) raising `NotImplementedError`.  
- [ ] T005b [P] Replace stubs with real CPU‑only implementations (CLIP ViT‑B/32, `torch‑fidelity`).  
- [ ] T006 Create `code/03_versioning.py` (SHA‑256 hashing, writes `state/artifact_hashes.yaml`).   <!-- FAILED-IN-EXECUTION: code/03_versioning.py exit=1 -->
- [ ] T007 Initialise data directories (`data/raw/`, `data/processed/`, `data/results/`).  
- [ ] T008 [P] Implement `code/utils/check_weights.py` (manifest verification, abort on missing/invalid checksum).  
- [ ] T012c [P] Initialise CLIP model for embeddings in `code/utils/models.py` (device=`cpu`).  

*Checkpoint*: Core infrastructure ready; user‑story work can proceed in parallel.

---

## Phase 2 – User Story 1: Generate Teacher‑Routing Ground Truth (Priority P1)

> **FR‑001** – Produce ≥ 1 000 rows of `(prompt_embedding, noise_level, routing_label, velocity_vector)` from the pre‑trained DanceOPD teacher.

- [ ] T042 [US1] **Robust real‑data streaming fetch** – Implement `code/00_data_fetch.py` to (1) prefer pre‑downloaded Parquet files (`data/raw/imagenet_samples.parquet`, `data/raw/laion_samples.parquet`) with SHA‑256 verification; (2) if missing, stream from HuggingFace (`datasets.load_dataset(..., streaming=True)`) in chunks, compute per‑chunk SHA‑256, aggregate to a total hash stored in `state/artifact_hashes.yaml`; (3) write exactly `N_TARGET=2500` samples (or ≥ 1 000 with warning) to the Parquet files; (4) exit with code 1 on any failure (network error, < 1 000 rows, checksum mismatch).  
  - **Verification**: `data/results/data_fetch_validation.json` reports `status: verified`, `source_tier: prefetch|stream`, and the recorded hash; script returns non‑zero on error.

- [ ] T043 [US1] **Post‑fetch source verification & hashing** – Extend `code/00_data_fetch.py` (or a new helper `code/utils/hash_verify.py`) to (a) recompute SHA‑256 of the written Parquet files, (b) compare against the stream‑hash recorded in `state/artifact_hashes.yaml`; (c) on mismatch abort loudly; (d) on success write `data/results/source_hashes.json` containing both stream and file hashes.  
  - **Verification**: Unit test `tests/unit/test_hash_verify.py` asserts that a deliberately corrupted file triggers a non‑zero exit.

- [ ] T012b [US1] **Stream & embed prompts** – `code/00_data_stream.py` reads the verified raw Parquet files, streams up to `N_TARGET` rows, extracts CLIP text embeddings (using the model from T012c), records `noise_level` (taken from dataset or sampled uniformly), writes `data/processed/combined_samples.parquet` with columns `image_path`, `prompt_embedding`, `noise_level`.  

- [ ] T013a [US1] **Generate teacher ground truth** – `code/00_teacher_inference.py` loads `combined_samples.parquet`, runs the public DanceOPD teacher (GPU‑enabled; the runner will off‑load to a free Kaggle GPU if needed) to obtain `routing_label` and `velocity_vector`.  Invalid/undefined routing labels are logged to `data/results/undefined_routing_log.json` and excluded.  The script aborts with code 1 if fewer than 1 000 valid rows remain.  Output: `data/processed/teacher_ground_truth.parquet`.  

- [ ] T013c [US1] **Graceful fallback to pre‑computed teacher data** – If GPU inference exceeds the CPU time budget, `code/00_teacher_inference.py` checks for `PRE_COMPUTED_TEACHER_DATA_DIR`; if present, loads `teacher_ground_truth.parquet` from there, otherwise exits with error (no synthetic fallback).  

- [ ] T014 [US1] **Extract final TeacherRoutingDataset** – `code/00_data_extraction.py` selects the four required columns from `teacher_ground_truth.parquet` and streams them to `data/processed/teacher_routing_dataset.parquet` (≥ 1 000 rows).  It validates that each `routing_label` belongs to the allowed enum (`expert_text_to_image`, `expert_editing`, `expert_inpainting`, `expert_super_resolution`, `expert_fallback`).  

- [ ] T015 [US1] **Routing‑label integrity check** – Added to `code/00_data_extraction.py`; aborts if any label is outside the enum.  

- [ ] T016 [US1] **Version & checksum the final dataset** – `code/03_versioning.py` hashes `teacher_routing_dataset.parquet` and records the hash in `state/artifact_hashes.yaml`.  

*Checkpoint*: A verified `teacher_routing_dataset.parquet` (≥ 1 000 rows) exists and is versioned.

---

## Phase 3 – User Story 2: Train & evaluate static Decision Trees (Priority P2)

> **FR‑002 / FR‑003** – Train multiple trees of varying `max_depth`, compute routing‑consistency accuracy on a held‑out test split.

- [ ] T020 [US2] **Data split** – `code/01_train_trees.py` reads `teacher_routing_dataset.parquet`, performs stratified split (80 % train, 20 % test) preserving `routing_label` distribution, writes `data/processed/train_split.parquet` and `data/processed/test_split.parquet`.  

- [ ] T021a [US2] **Train a single tree** – Function `train_tree(depth, X_train, y_train)` returns a scikit‑learn `DecisionTreeClassifier`.  It also computes `train_accuracy` and `test_accuracy` (using the test split) and logs a warning to `data/results/overfitting_log.json` if the gap > 0.1.  Model saved as `models/trained_trees/tree_depth_{depth}.pkl`.  

- [ ] T021b [US2] **Depth‑sweep loop** – Calls `train_tree` for `max_depth` ∈ `range(2, 21)`.  Consolidates results into `data/results/tree_accuracy.csv` (`max_depth`, `train_accuracy`, `test_accuracy`).  

- [ ] T021c [US2] **Random‑forest sweep** – Trains `RandomForestClassifier` for `n_estimators` ∈ `{10, 50, 100, 200}` (default `max_depth=None`).  Saves models to `models/trained_forests/forest_{n}.pkl` and records accuracies in `data/results/forest_accuracy.csv`.  

- [ ] T021d [US2] **Validate model metadata & update state** – For every saved tree/forest, create a JSON metadata file (`models/metadata/{model_id}.json`) containing `model_id`, `max_depth`/`n_estimators`, `train_accuracy`, `test_accuracy`, SHA‑256 hash of the artifact.  Validate each file against the contract `specs/contracts/DecisionTreeMetadata.json` (assumed to exist).  After validation, update `state/artifact_hashes.yaml` with the new model hashes.  
  - **Verification**: Unit test `tests/unit/test_model_metadata.py` loads each metadata JSON, checks schema compliance, and asserts the recorded hash matches the actual file hash.

*Checkpoint*: All tree and forest models are trained, versioned, and their metadata validated.

---

## Phase 4 – User Story 3: Fidelity degradation & statistical significance (Priority P3)

> **FR‑004 / FR‑005 / FR‑006** – Use tree‑predicted routing to generate images, compute FID & CLIP, and run bootstrap / paired‑t tests.

### 4.1 Expert‑field loading & Euler integration (core utilities)

- [ ] T029b [US3] **Load expert field logic** – `code/models/expert_loader.py` loads the individual expert sub‑modules from the DanceOPD package and caches them for fast reuse.  

- [ ] T029c [US3] **CPU‑only Euler integrator** – `code/models/euler.py` implements `integrate(velocity_vector, noise_level, expert_type) → PIL.Image` using step size 0.1, 10 steps, and Gaussian noise (`torch.randn`).  All tensors forced to CPU.  

- [ ] T029a [US3] **Generate velocity vectors from tree routing** – `code/models/expert_reinference.py` receives a sample (`prompt_embedding`, `noise_level`, `predicted_routing`), loads the corresponding expert via `expert_loader`, invokes it to obtain a new `velocity_vector`.  Saves per‑sample vectors to `data/processed/tree_predicted_vectors.parquet`.  

### 4.2 Pilot‑scale image generation (first executable end‑to‑end)

- [ ] T028a [US3] **Pilot image generation** – `code/02_evaluate_fidelity.py` runs the Euler integrator for (i) teacher baseline (using teacher‑provided `velocity_vector`) and (ii) tree‑predicted routing (using vectors from T029a) on the first **N=50** test samples.  Images saved under `data/results/teacher_baseline_images_pilot/` and `data/results/tree_images_pilot/` with matching filenames (`sample_{id}.png`).  

- [ ] T030a [US3] **Compute pilot FID & CLIP scores** – Using the metric functions from T005b, compute (a) dataset‑level FID between the two pilot image sets, (b) per‑sample CLIP scores (teacher vs. tree) and store the list.  Results written to `data/results/fidelity_metrics_pilot.csv` (`sample_id`, `fid_score`, `clip_score`).  

- [ ] T030b [US3] **Estimate pilot variance** – From `fidelity_metrics_pilot.csv`, calculate the variance of the per‑sample CLIP‑score differences and store in `data/results/pilot_variance.json` (`clip_diff_variance`).  

- [ ] T030c [US3] **Power analysis & sample‑size configuration** – Load `pilot_variance.json`, run a power calculation with `statsmodels.stats.power.TTestIndPower` targeting `power=0.8`, `effect_size=0.5`.  If the resulting `N_required` exceeds the remaining test‑set size or would breach the 6‑hour timeout, linearly down‑scale to the maximum feasible `N_feasible` (using the timer from T033a).  Write the final configuration to `data/results/sample_size_config.json` (`N`, `status`: `full|reduced|underpowered`).  

### 4.3 Full‑scale evaluation (scaled to the power‑determined N)

- [ ] T028b [US3] **Full‑scale image generation** – Extends the pilot loop to the `N` samples defined in `sample_size_config.json`.  Generates teacher and tree images into `data/results/teacher_baseline_images_full/` and `data/results/tree_images_full/`.  The loop checks `timer.check_timeout()` (T033a) each iteration; on timeout it saves partial results and records `status: partial` in `sample_size_config.json`.  

- [ ] T030d [US3] **Compute full FID & CLIP scores** – Same metric pipeline as T030a but on the full image sets; output `data/results/fidelity_metrics_full.csv`.  

- [ ] T030e [US3] **Statistical significance testing** – (a) Bootstrap 1 000 resamples of the FID distribution to obtain a 95 % confidence interval; (b) Paired‑sample t‑test on per‑sample CLIP scores (teacher vs. tree).  Store results in `data/results/statistical_tests.json` with keys `p_value_fid`, `p_value_clip`, `conclusion`, `n_samples`, `status`.  

### 4.4 Cross‑cutting support

- [ ] T033a [US3] **Early‑stop timer** – `code/utils/timer.py` provides `start_timer(hours)` and `check_timeout()`; on timeout it writes a JSON flag `status: partial` to the supplied results directory.  

- [ ] T033b [US3] **Timer enforcement in evaluation** – `code/02_evaluate_fidelity.py` wraps both pilot and full loops with the timer, breaking gracefully when time expires.  

*Checkpoint*: After T030e the pipeline yields (i) a fully versioned `teacher_routing_dataset.parquet`, (ii) tree/forest models with validated metadata, (iii) image‑generation artefacts for pilot and full runs, (iv) quantitative fidelity metrics, and (v) statistically sound conclusions.

---

## Phase 5 – Reproducibility & hand‑off

- [ ] T037 Documentation – Update `docs/quickstart.md` to describe the streaming fetch, checksum verification, and the “fail loud” policy.  
- [ ] T038 Code cleanup – Run `ruff` & `black`; ensure no lint errors.  
- [ ] T039 Euler integrator optimisation – Vectorise the step loop where possible (still CPU‑only).  
- [ ] T040 [P] Unit tests for streaming logic (`tests/unit/test_streaming.py`).  
- [ ] T041 Run end‑to‑end validation (`quickstart.md` steps) in a fresh runner; write report to `data/results/e2e_validation.json`.  

---

## Phase 6 – Review‑resolution (addressing analysis findings)

All previously flagged tasks have been reopened, clarified, and re‑ordered to guarantee deterministic artefacts.  The checklist above now satisfies the specification, the data contracts, and the “no‑fabrication” principle.  

--- 

*End of `tasks.md`.*
