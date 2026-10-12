# Tasks: llmXive follow‑up – mitigating object‑driven shortcuts

**Inputs**: `spec.md`, `plan.md`, existing source under `src/`, data directories under `data/`, and reviewer feedback (none at this stage).

The study must (1) generate counterfactual video pairs, (2) train a linear classifier with the Counterfactual Consistency (CC) loss, (3) evaluate robustness, and (4) produce reproducible artifacts and documentation.  
The tasks below respect data‑flow dependencies, stay within the free‑tier CPU limits, and cover every functional requirement (FR‑001 – FR‑006) and success‑criteria (SC‑001 – SC‑005).

---  

- [X] **T001** [US1] **Create a reproducible entry‑point and quick‑start guide**  
  - Add `quickstart.md` in the feature root describing a single command `python -m src.pipeline.run_all --config configs/run.yaml`.  
  - Document required environment (Python 3.11, dependencies from `requirements.txt`).  
  - Verify that the command prints a summary of generated artifacts and exits with status 0.  
  - **File(s)**: `quickstart.md`, `configs/run.yaml`.

- [ ] **T002** [US1] **Implement streaming loader for Something‑Something V2**  
  - Write `src/data/something_loader.py` that uses `datasets.load_dataset("something-something-v2", split="train", streaming=True)`.  
  - Yield video file URLs (or raw bytes) together with action labels; include a deterministic random seed for reproducible sampling.  
  - Add a unit test `tests/test_something_loader.py` that loads 5 videos and asserts non‑empty frames.  
  - **File(s)**: `src/data/something_loader.py`, `tests/test_something_loader.py`.

- [X] **T004** [US1] **Load pre‑computed optical‑flow features (CPU‑only)**
  - Implement `src/data/optical_flow_loader.py` that copies or symlinks existing FlowNet‑C `.npy` feature files from the repository bundle into `data/flow_features/`.  
  - Verify that each copied file matches its stored SHA‑256 checksum (manifest generated later).  
  - No on‑the‑fly flow computation is performed, preserving the CPU budget.  
  - **File(s)**: `src/data/optical_flow_loader.py`.

- [ ] **T003** [US1] **Detect primary objects and generate counterfactual videos**   <!-- FAILED-IN-EXECUTION: src/data/counterfactual.py exit=1 --> <!-- FAILED-IN-EXECUTION: tests/test_counterfactual_generation.py exit=1; tests/test_something_loader.py exit=1 -->
  1. Use CPU‑friendly Faster‑RCNN (`torchvision.models.detection.fasterrcnn_resnet50_fpn(pretrained=True)`) on a representative frame to obtain a bounding box.  
  2. Randomly select a distinct object patch from `data/patches/`.  
  3. Replace the region via OpenCV `seamlessClone`.  
  4. Load pre‑computed optical‑flow tensors (produced by T004) and compute **normalized L2 divergence**; accept only if ≤ 0.15.  
  5. Compute cosine similarity of FlowNet‑C feature vectors; accept only if ≥ 0.9.  
  6. Write the counterfactual video to `data/counterfactuals/videos/`.  
  7. Compute a SHA‑256 checksum for each accepted video and add a `video_sha256` column to `data/counterfactuals/metadata.csv`.  
  8. Record a row in `metadata.csv` that conforms to `specs/.../counterfactual_pair.schema.yaml`.  
  9. Log skipped videos (detection failure, divergence breach, or similarity breach) without crashing.  
  - Add a focused test `tests/test_counterfactual_generation.py` that runs on a 2‑video mini‑subset and checks that at least one accepted pair has `optical_flow_divergence <= 0.15`.  
  - **File(s)**: `src/data/counterfactual.py`, `data/counterfactuals/metadata.csv`, `tests/test_counterfactual_generation.py`.

- [X] **T005** [US2] **Implement the Counterfactual Consistency loss**  
  - Add `src/model/loss.py` containing:  
    - `cross_entropy_loss` (standard `torch.nn.CrossEntropyLoss`).  
    - `counterfactual_consistency_loss(pred_orig, pred_cf)` that returns KL‑divergence (torch.nn.functional.kl_div, log‑softmax vs softmax).  
    - `total_loss = ce + lambda_ * cc`.  
  - Provide a small sanity‑check script `src/model/check_loss.py` that feeds identical logits for orig/CF and asserts `cc == 0`.  
  - **File(s)**: `src/model/loss.py`, `src/model/check_loss.py`.

- [ ] **T006** [US2] **Train linear classifier with λ‑sweep and multiple seeds**  
  - Create `src/train/trainer.py` that:  
    1. Loads frozen FlowNet‑C features (`data/flow_features/*.npy`).  
    2. Builds a single linear layer (`torch.nn.Linear(1024, num_classes)`).  
    3. Accepts command‑line arguments `--lambda`, `--seed`, `--epochs`.  
    4. For each training step, computes `L_total` using the module from T005 on paired original‑counterfactual features.  
    5. Saves checkpoints to `data/checkpoints/<model_id>_seed<seed>.pt`.  
  - Run the trainer for λ ∈ {0.1, 0.5, 1.0} and seeds ∈ {42, 43, 44, 45, 46}.  
  - Record a summary CSV `results/training_log.csv` (model_id, lambda, seed, final_val_acc).  
  - **File(s)**: `src/train/trainer.py`, `results/training_log.csv`.

- [ ] **T007** [US2] **Train baseline model (λ = 0)**  
  - Re‑use `trainer.py` with `--lambda 0` and the same seed list.  
  - Store checkpoints under `data/checkpoints/baseline_seed<seed>.pt`.  
  - Append baseline rows to `results/training_log.csv`.  
  - **File(s)**: (same as T006, additional rows in `results/training_log.csv`).

- [ ] **T008** [US3] **Evaluate models on original, swapped, and motion‑only test sets**  
  - Implement `src/eval/evaluator.py` that loads a checkpoint, computes predictions on:  
    * `data/test/original/` (original videos).  
    * `data/test/counterfactual/` (object‑swapped videos).  
    * `data/test/motion_only/` (objects blurred with Gaussian kernel).  
  - Calculate `accuracy_original`, `accuracy_counterfactual`, `delta_accuracy`, `accuracy_motion_only`.  
  - Write per‑seed rows to `results/per_seed.csv` adhering to `evaluation_results.schema.yaml`.  
  - **File(s)**: `src/eval/evaluator.py`, `results/per_seed.csv`.

- [ ] **T009** [US3] **Statistical validation (paired t‑test & bootstrap CI)**  
  - Add `src/eval/statistics.py` that:  
    1. Loads `results/per_seed.csv`.  
    2. Performs a paired t‑test (`scipy.stats.ttest_rel`) comparing `delta_accuracy` of CC‑models vs baseline across the 5 seeds.  
    3. Runs 10 000 bootstrap resamples of the seed‑level differences to compute a 95 % confidence interval.  
    4. Writes an aggregated summary row to `results/summary.csv` with `p_value`, `t_statistic`, and CI bounds.  
  - Unit test `tests/test_statistics.py` that checks the function returns a dict with the expected keys.  
  - **File(s)**: `src/eval/statistics.py`, `results/summary.csv`, `tests/test_statistics.py`.

- [ ] **T010** [US3] **Generate figures & tables for the paper hand‑off**  
  - Implement `src/report/report.py` that reads `results/per_seed.csv` and `results/summary.csv` and produces:  
    * Line plot of `ΔAcc` vs λ (saved as `figures/delta_acc_vs_lambda.png`).  
    * Histogram of bootstrap ΔAcc differences with 95 % CI overlay (`figures/bootstrap_hist.png`).  
    * Table `tables/evaluation_summary.csv` summarising all metrics.  
  - Verify that each figure file exists and is a valid PNG.  
  - **File(s)**: `src/report/report.py`, `figures/delta_acc_vs_lambda.png`, `figures/bootstrap_hist.png`, `tables/evaluation_summary.csv`.

- [ ] **T011** [US3] **Manual quality inspection of 50 counterfactual pairs**  
  - Write a script `src/analysis/manual_inspection.py` that randomly selects 50 accepted rows from `metadata.csv`, computes SSIM on background regions (using `skimage.metrics.structural_similarity`) and runs a pretrained object classifier on the swapped patch region to ensure class confidence > 0.9.  
  - Output a CSV `results/manual_inspection.csv` with columns `video_id, ssim_bg, patch_confidence, pass`.  
  - The script must abort with a non‑zero exit code if fewer than 45 rows pass both criteria (i.e., SSIM > 0.95 and confidence > 0.9).  
  - **Added checksum step**: after CSV generation, compute a SHA‑256 checksum for `results/manual_inspection.csv` and record it in the checksum manifest generated by T014.  
  - **File(s)**: `src/analysis/manual_inspection.py`, `results/manual_inspection.csv`.

- [ ] **T012** [US2] **Resource‑usage profiling to certify CPU‑only feasibility and core‑count limit**  
  - Add a wrapper `src/utils/profile.py` that executes the full training‑and‑evaluation pipeline while recording:  
    * Peak RAM (`psutil.virtual_memory().used`).  
    * Wall‑clock time (`time.perf_counter`).  
    * Number of logical CPUs used (`psutil.cpu_count(logical=True)` and runtime affinity checks).  
  - After the run, assert `peak_ram_mb <= 7000`, `wall_time_h <= 6`, **and** `cpu_count_used <= 2`.  
  - Append a JSON report `results/resource_profile.json` with `peak_ram_mb`, `wall_time_h`, `cpu_count_used`, and a pass/fail flag.  
  - **File(s)**: `src/utils/profile.py`, `results/resource_profile.json`.

- [ ] **T014** **Generate checksums and version‑hash manifest for all pipeline artifacts**  
  - Scan the entire `data/`, `results/`, `figures/`, `tables/`, and `src/` directories after the pipeline finishes.  
  - Compute SHA‑256 hashes for every file and write them to `data/checksums/manifest.csv` (columns: `relative_path, sha256`).  
  - This manifest satisfies Constitution III (Data Hygiene) and V (Versioning Discipline).  
  - **File(s)**: `data/checksums/manifest.csv`.

- [ ] **T015** **Verify checksums against the manifest**  
  - Implement `src/utils/verify_checksums.py` that reads `data/checksums/manifest.csv` and recomputes hashes for each listed file, failing if any mismatch is found.  
  - Produce a pass/fail flag written to `results/checksum_verification.json`.  
  - **File(s)**: `src/utils/verify_checksums.py`, `results/checksum_verification.json`.

- [ ] **T016** **Validate counterfactual metadata against its JSON‑Schema**  
  - Add `src/utils/validate_counterfactual_schema.py` that loads `data/counterfactuals/metadata.csv` and validates each row against `specs/.../counterfactual_pair.schema.yaml` using `jsonschema`.  
  - Write a verification flag to `results/counterfactual_schema_validation.json`.  
  - **File(s)**: `src/utils/validate_counterfactual_schema.py`, `results/counterfactual_schema_validation.json`.

- [ ] **T017** **Validate evaluation result CSVs against their JSON‑Schema**  
  - Add `src/utils/validate_evaluation_schema.py` that validates `results/per_seed.csv` and `results/summary.csv` against `specs/.../evaluation_results.schema.yaml`.  
  - Also checks that any figure (`figures/*.png`) and table (`tables/*.csv`) were generated by `src/report/report.py` and have timestamps newer than the evaluation CSVs.  
  - Write a verification flag to `results/evaluation_schema_validation.json`.  
  - **File(s)**: `src/utils/validate_evaluation_schema.py`, `results/evaluation_schema_validation.json`.

- [ ] **T013** [US3] **End‑to‑end reproducibility run (full pipeline)**  
  - Using the scripts from T002‑T012 and the new verification tasks (T014‑T017), create a master driver `src/pipeline/run_all.py` that sequentially:  
    1. Streams and samples the dataset.  
    2. Loads pre‑computed optical‑flow features (T004).  
    3. Generates counterfactual pairs (T003).  
    4. Extracts any remaining needed features.  
    5. Trains all models (T006‑T007).  
    6. Evaluates (T008).  
    7. Performs statistics (T009).  
    8. Produces figures/tables (T010).  
    9. Runs manual inspection (T011).  
    10. Profiles resources (T012).  
    11. Generates checksum manifest (T014) and verifies it (T015).  
    12. Validates contracts (T016, T017).  
    **Added final aggregation step**: before exiting with status 0, the script checks that all verification flags (`results/resource_profile.json`, `results/checksum_verification.json`, `results/counterfactual_schema_validation.json`, `results/evaluation_schema_validation.json`) indicate success; if any flag reports failure, the script exits with a non‑zero code.  
  - Document the command line in `quickstart.md` (already created in T001).  
  - **File(s)**: `src/pipeline/run_all.py`.

---  

### Dependency Mapping (summary)

| Requirement | Satisfying Task(s) |
|-------------|-------------------|
| FR‑001 (counterfactual generation + optical‑flow check) | T003, T004 |
| FR‑002 (CC loss definition) | T005 |
| FR‑003 (linear classifier + λ‑sweep) | T006, T007 |
| FR‑04 (robustness evaluation) | T008 |
| FR‑05 (paired t‑test) | T009 |
| FR‑06 (CPU‑only feasibility) | T012 |
| SC‑001 (ΔAcc reduction) | T008, T009 |
| SC‑002 (statistical significance) | T009 |
| SC‑003 (resource constraints + 2‑CPU limit) | T012 |
| SC‑004 (λ‑sweep) | T006 |
| SC‑005 (manual inspection) | T011 |
| Constitution III & V (checksums & hashes) | T014, T015 |
| Contract validation | T016, T017 |
| End‑to‑end verification | T013 |

All tasks are unchecked (pending) and ordered to respect data flow. Running `python -m src.pipeline.run_all` will execute the complete study from raw data to final figures, satisfying the specification.  
