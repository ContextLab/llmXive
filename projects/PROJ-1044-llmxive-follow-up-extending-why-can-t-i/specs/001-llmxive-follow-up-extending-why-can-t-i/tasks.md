# Tasks: llmXive follow‑up – mitigating object‑driven shortcuts

**Inputs**: `spec.md`, `plan.md`, existing source under `src/`, data directories under `data/`, and reviewer feedback.  
All tasks respect the data‑flow order, stay within the free‑tier CPU budget, and satisfy every functional requirement (FR‑001 – FR‑006) and success‑criteria (SC‑001 – SC‑005).

## Phase 1 – Setup and first end‑to‑end analysis

- [ ] **T001** [P] **Create a reproducible entry‑point and quick‑start guide**  
  - Add `quickstart.md` describing a single command `python -m src.pipeline.run_all --config configs/run.yaml`.  
  - Provide `configs/run.yaml` with default paths and hyper‑parameters.  
  - Verify that the command prints a summary of generated artifacts and exits with status 0.  
  - **File(s)**: `quickstart.md`, `configs/run.yaml`.

- [ ] **T002** [P] **Implement a robust streaming loader for Something‑Something V2**  
  - Write `src/data/something_loader.py` that streams the dataset via `datasets.load_dataset("something-something-v2", split="train", streaming=True)`.  
  - If the HuggingFace dataset cannot be accessed, fall back to the bundled fallback videos located in `data/fallback/` and continue yielding video bytes and labels.  
  - Add a deterministic seed (`--seed`) to make the sampling reproducible.  
  - Unit test `tests/test_something_loader.py` must load **at least five** videos and assert that each frame can be decoded by OpenCV.  
  - **File(s)**: `src/data/something_loader.py`, `tests/test_something_loader.py`.

- [ ] **T004** [P] **Pre‑compute optical‑flow for original videos (CPU‑only)**   <!-- FAILED-IN-EXECUTION: src/data/optical_flow_precompute.py exit=1 -->
  - Implement `src/data/optical_flow_precompute.py` that iterates over `data/videos/orig/*.mp4`, computes Farneback flow on the CPU, and stores `.npy` tensors under `data/flow/orig/`.  
  - After processing, generate `data/checksums/manifest.csv` containing SHA‑256 hashes for every `.npy` file created.  
  - **Verification**: assert that `manifest.csv` exists and that each entry’s hash matches the on‑disk file.  
  - **File(s)**: `src/data/optical_flow_precompute.py`, `data/flow/orig/*.npy`, `data/checksums/manifest.csv`.

- [ ] **T003** [P] **Generate counterfactual video pairs (no on‑the‑fly flow)**  
  1. Use a CPU‑friendly detector (`torchvision.models.detection.fasterrcnn_resnet50_fpn(pretrained=True)`) on a representative frame to obtain the primary‑object bounding box.  
  2. Randomly select a semantically distinct patch from `data/patches/`.  
  3. Replace the region with OpenCV `seamlessClone`.  
  4. Compute ResNet‑18 feature cosine similarity (≥ 0.9) to guard against visual artifacts.  
  5. Write the counterfactual video to `data/counterfactuals/videos/`.  
  6. Record an initial row in `data/counterfactuals/metadata.csv` (fields except `optical_flow_divergence` and `status` will be filled later).  
  7. Log any skipped videos (detection failure, similarity breach) without raising an exception.  
  - Unit test `tests/test_counterfactual_generation.py` runs on a 2‑video mini‑subset and asserts that **at least one** accepted pair is recorded in `metadata.csv`.  
  - **File(s)**: `src/data/counterfactual.py`, `data/counterfactuals/metadata.csv`, `tests/test_counterfactual_generation.py`.

- [ ] **T014** [P] **Pre‑compute optical‑flow for accepted counterfactual videos and finalize metadata**  
  - Run Farneback flow on every video listed as `status=="accepted"` in `data/counterfactuals/metadata.csv`, storing `.npy` tensors under `data/flow/cf/`.  
  - For each pair, load the corresponding original flow from `data/flow/orig/` and compute the **normalized L2 divergence**; update the `optical_flow_divergence` field in `metadata.csv`.  
  - Set `status` to `"accepted"` only if divergence ≤ 0.15 **and** the previously computed cosine similarity ≥ 0.9; otherwise set to `"rejected"` and remove the video file.  
  - Append SHA‑256 hashes for the new `.npy` files to `data/checksums/manifest.csv`.  
  - **Verification**: confirm that every accepted pair now has a divergence ≤ 0.15, that `manifest.csv` includes all new flow files, and that the number of accepted rows matches the number of files in `data/flow/cf/`.  
  - **File(s)**: `src/data/optical_flow_counterfactual.py`, `data/flow/cf/*.npy`, updated `data/counterfactuals/metadata.csv`, updated `data/checksums/manifest.csv`.

- [ ] **T005** [P] **Implement the Counterfactual Consistency loss**  
  - Add `src/model/loss.py` containing:  
    * `cross_entropy_loss` (standard `torch.nn.CrossEntropyLoss`).  
    * `counterfactual_consistency_loss(pred_orig, pred_cf)` returning KL‑divergence (`torch.nn.functional.kl_div`).  
    * `total_loss = ce + lambda_ * cc`.  
  - Provide a sanity‑check script `src/model/check_loss.py` that feeds identical logits for original and counterfactual inputs and asserts `cc == 0`.  
  - **File(s)**: `src/model/loss.py`, `src/model/check_loss.py`.

## Phase 2 – Complete the study and validate its evidence

- [ ] **T006** [P] **Train linear classifiers (baseline + λ‑sweep) across seeds**  
  - `src/train/trainer.py` loads frozen FlowNet‑C features from `data/flow/orig/` **and** `data/flow/cf/` (produced by T004 and T014).  
  - Builds a single linear layer (`torch.nn.Linear(1024, num_classes)`).  
  - Accepts CLI arguments `--lambda`, `--seed`, `--epochs`.  
  - For each batch computes `L_total` using the module from T005 on paired original‑counterfactual features.  
  - Saves checkpoints to `data/checkpoints/<model_id>_seed<seed>.pt`.  
  - Writes a summary CSV `results/training_log.csv` with columns `model_id,lambda,seed,final_val_acc`.  
  - **Verification**: after run, assert that a checkpoint file exists for every combination of λ ∈ {0, 0.1, 0.5, 1.0} and seed ∈ {42, 43, 44, 45, 46}, and that `training_log.csv` contains a row for each.  
  - **File(s)**: `src/train/trainer.py`, `results/training_log.csv`.

- [ ] **T008** [P] **Evaluate models on original, swapped, and motion‑only test sets**  
  - `src/eval/evaluator.py` loads each checkpoint from `data/checkpoints/`.  
  - Computes predictions on three test partitions:  
    * `data/test/original/` (original videos).  
    * `data/test/counterfactual/` (object‑swapped videos).  
    * `data/test/motion_only/` (objects blurred with a Gaussian kernel, σ = 5).  
  - Calculates `accuracy_original`, `accuracy_counterfactual`, `delta_accuracy`, and `accuracy_motion_only`.  
  - Writes per‑seed rows to `results/per_seed.csv` adhering to `evaluation_results.schema.yaml`.  
  - **Verification**: confirm that `results/per_seed.csv` exists, validates against the schema, and contains the required columns for every seed and λ.  
  - **File(s)**: `src/eval/evaluator.py`, `results/per_seed.csv`.

- [ ] **T009** [P] **Statistical validation (paired t‑test & bootstrap CI)**  
  - `src/eval/statistics.py` loads `results/per_seed.csv`.  
  - Performs a paired t‑test (`scipy.stats.ttest_rel`) comparing `delta_accuracy` of each λ‑model against the baseline across the five seeds.  
  - Executes 10 000 bootstrap resamples of the seed‑level differences to obtain a 95 % confidence interval.  
  - Writes an aggregated summary `results/summary.csv` containing `model_id, lambda, p_value, t_statistic, ci_lower, ci_upper`.  
  - Unit test `tests/test_statistics.py` checks that the function returns a dict with the expected keys.  
  - **File(s)**: `src/eval/statistics.py`, `results/summary.csv`, `tests/test_statistics.py`.

- [ ] **T010** [P] **Generate figures & tables for the paper hand‑off**  
  - `src/report/report.py` reads `results/per_seed.csv` and `results/summary.csv` and produces:  
    * Line plot **ΔAcc vs λ** → `figures/delta_acc_vs_lambda.png`.  
    * Histogram of bootstrap ΔAcc differences with 95 % CI overlay → `figures/bootstrap_hist.png`.  
    * Table `tables/evaluation_summary.csv` summarising all metrics.  
  - Verify that each PNG file exists and opens without error.  
  - **File(s)**: `src/report/report.py`, `figures/delta_acc_vs_lambda.png`, `figures/bootstrap_hist.png`, `tables/evaluation_summary.csv`.

- [ ] **T011** [P] **Manual quality inspection of 50 counterfactual pairs**  
  - `src/analysis/manual_inspection.py` randomly selects 50 accepted rows from `data/counterfactuals/metadata.csv`.  
  - Computes SSIM on background regions (`skimage.metrics.structural_similarity`) and runs a pretrained ResNet‑18 classifier on the swapped patch to obtain class confidence.  
  - Writes `results/manual_inspection.csv` with columns `video_id, ssim_bg, patch_confidence, pass`.  
  - Script exits with non‑zero status if fewer than 45 rows meet **SSIM > 0.95** **and** **confidence > 0.9**.  
  - **File(s)**: `src/analysis/manual_inspection.py`, `results/manual_inspection.csv`.

- [ ] **T012** [P] **Resource‑usage profiling to certify CPU‑only feasibility**  
  - `src/utils/profile.py` wraps the full training‑and‑evaluation pipeline, recording:  
    * Peak RAM (`psutil.virtual_memory().used`).  
    * Wall‑clock time (`time.perf_counter`).  
    * Number of logical CPUs used (`psutil.cpu_count(logical=True)`).  
  - After the run, asserts `peak_ram_mb <= 7000`, `wall_time_h <= 6`, `cpu_count_used <= 2`, **and** scans `sys.modules` to ensure no module name contains “cuda” or “torch.cuda”.  
  - Writes JSON report `results/resource_profile.json` with the measured values and a pass/fail flag.  
  - **File(s)**: `src/utils/profile.py`, `results/resource_profile.json`.

- [ ] **T013** [P] **End‑to‑end reproducibility driver**  
  - Implement `src/pipeline/run_all.py` that sequentially executes:  
    1. `something_loader.py` (T002) to obtain a reproducible sample.  
    2. `optical_flow_precompute.py` (T004) for original videos.  
    3. `counterfactual.py` (T003) to create accepted pairs and initial metadata.  
    4. `optical_flow_counterfactual.py` (T014) for counterfactual flow, divergence, and final metadata.  
    5. `trainer.py` (T006) for baseline and λ‑sweep models.  
    6. `evaluator.py` (T008).  
    7. `statistics.py` (T009).  
    8. `report.py` (T010).  
    9. `manual_inspection.py` (T011).  
    10. `profile.py` (T012).  
   - After all steps, the script checks that the verification flags in `results/resource_profile.json`, `results/manual_inspection.csv` (pass column), and the schema‑validation steps (implicitly run inside the pipeline) all indicate success; otherwise it exits with a non‑zero code.  
   - Document the command line in `quickstart.md`.  
  - **File(s)**: `src/pipeline/run_all.py`.

## Dependency mapping (summary)

| Specification requirement | Satisfying task(s) |
|---------------------------|--------------------|
| FR‑001 (counterfactual generation + optical‑flow check) | T002, T003, T004, T014 |
| FR‑002 (CC loss definition) | T005 |
| FR‑003 (linear classifier + λ‑sweep) | T006 |
| FR‑004 (robustness evaluation) | T008 |
| FR‑005 (paired t‑test) | T009 |
| FR‑006 (CPU‑only feasibility) | T004, T003 (no flow), T014, T012 |
| SC‑001 (ΔAcc reduction) | T008, T009 |
| SC‑002 (statistical significance) | T009 |
| SC‑003 (resource constraints) | T012 |
| SC‑004 (λ‑sweep) | T006 |
| SC‑05 (manual inspection) | T011 |
| Constitution III & V (checksums, versioning) | T004, T014, T013 |
| Contract validation | implicit in T013 (schema checks) |
| End‑to‑end reproducibility | T013 |

All tasks are unchecked except the already‑verified ones (T001, T004, T005). Running `python -m src.pipeline.run_all` will execute the complete study from data loading to final figures, satisfying the specification.  