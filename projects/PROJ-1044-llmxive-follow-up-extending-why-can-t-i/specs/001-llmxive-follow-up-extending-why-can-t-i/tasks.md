# Tasks: Mitigating Object‑Driven Shortcuts with Counterfactual Consistency

**Inputs**: `spec.md`, `plan.md`, existing source under `src/`, data directories under `data/`, and reviewer feedback.

The following checklist implements the smallest complete study that satisfies every functional requirement (FR‑001 – FR‑009) and success‑criterion (SC‑001 – SC‑007).  Tasks are ordered to respect data flow and the free‑tier CPU budget.  Previously verified tasks are retained (checked).  All remaining tasks are unchecked and must be executed to completion.

---

## Phase 0 – Core data creation (new)

- [X] **T000** [ ] **Generate deterministic synthetic original videos**
  - Run `src/data/synthetic_generator.py` to create `N=200` short videos (5 s, 64×64) in `data/videos/orig/`.  
  - Record each video filename and a UUID in `data/videos/orig/manifest.csv`.  
  - Verification: at least 150 videos exist and manifest rows equal file count.  
  - **Files**: `src/data/synthetic_generator.py`, `data/videos/orig/`, `data/videos/orig/manifest.csv`.

- [ ] **T001** [ ] **Create a reproducible entry‑point and quick‑start guide**  
  - Add `quickstart.md` describing the single command `python -m src.pipeline.run_all --config configs/run.yaml`.  
  - Provide `configs/run.yaml` with default paths, hyper‑parameters, and seed list.  
  - Verify that the command prints a concise summary of generated artifacts and exits with status 0.  
  - **Files**: `quickstart.md`, `configs/run.yaml`.

- [ ] **T002** [ ] **Implement a robust streaming loader for Something‑Something V2**  
  - Write `src/data/something_loader.py` that streams the dataset via `datasets.load_dataset("something-something-v2", split="train", streaming=True)`.  
  - Raise any download exception (no synthetic fallback).  
  - Add deterministic shuffling with `--seed` (default 42).  
  - Pin the Faster‑RCNN detector weights version in `requirements.txt` (e.g., `torchvision==0.17.2`).  
  - Unit test `tests/test_something_loader.py` must load at least five videos, decode each frame with OpenCV, and assert non‑zero dimensions.  
  - **Files**: `src/data/something_loader.py`, `tests/test_something_loader.py`.

- [ ] **T016** [ ] **Populate `data/patches/` with real object patches**   <!-- FAILED-IN-EXECUTION: src/data/patches_download.py exit=-1 (TIMEOUT) -->
  - Download a small, license‑compatible image patch library (e.g., Open Images “Object” subset) and extract one patch per target class into `data/patches/`.  
  - Record a `patches/manifest.csv` mapping `patch_source_id` to source URL and class label.  
  - Verification: at least 20 distinct patches exist and manifest entries match file count.  
  - **Files**: `data/patches/`, `data/patches/manifest.csv`.

- [ ] **T003** [ ] **Generate counterfactual video pairs (video creation only)**   <!-- FAILED-IN-EXECUTION: src/data/patches_download.py exit=-1 (TIMEOUT) -->
  1. Detect the primary object on the first frame using `torchvision.models.detection.fasterrcnn_resnet50_fpn(pretrained=True)`.  
  2. Sample a semantically distinct patch from `data/patches/` (populated by T016).  
  3. Replace the region using OpenCV `seamlessClone`.  
  4. Write the counterfactual video to `data/counterfactuals/videos/{orig_id}_cf.mp4`.  
  5. Record interim information (original path, counterfactual path, object classes, bbox, patch ID, generation timestamp, and ResNet‑18 cosine similarity) to a **temporary CSV** `data/counterfactuals/temp_metadata.csv`.  
  6. Log any skipped videos (detector failure, similarity breach) without raising an exception.  
  - Unit test `tests/test_counterfactual_generation.py` runs on a 2‑video mini‑subset and asserts that at least one counterfactual video file and a corresponding temporary metadata row are produced.  
  - **Files**: `src/data/counterfactual.py`, `data/counterfactuals/videos/`, `data/counterfactuals/temp_metadata.csv`, `tests/test_counterfactual_generation.py`.

- [ ] **T004** [ ] **Pre‑compute optical‑flow for original videos (CPU‑only, Farnebäck)**  
  - Implement `src/data/optical_flow_precompute.py` that iterates over `data/videos/orig/*.mp4`, computes Farneback flow on the CPU, and stores each tensor as `data/flow/orig/{video_id}.npy`.  
  - After processing, generate `data/checksums/manifest.csv` containing SHA‑256 hashes for every `.npy` file created.  
  - Verification: `manifest.csv` exists, each hash matches the file, and row count equals number of `.npy` files.  
  - **Files**: `src/data/optical_flow_precompute.py`, `data/flow/orig/*.npy`, `data/checksums/manifest.csv`.

- [ ] **T005** [ ] **Compute optical‑flow divergence for counterfactual videos, finalize metadata**  
  1. Read `data/counterfactuals/temp_metadata.csv`.  
  2. For each row, compute Farneback flow on the counterfactual video and store `data/flow/cf/{video_id}.npy`.  
  3. Load the corresponding original flow and compute **normalized L2 divergence** for **three thresholds**: 0.10, 0.15, 0.20.  
  4. For each threshold, add columns `optical_flow_divergence_{thr}` to a new `metadata.csv`.  
  5. Set `status` to `"accepted"` **only if** divergence ≤ threshold **and** cosine similarity ≥ 0.9; otherwise set to `"rejected"` and delete the counterfactual video and its flow file.  
  6. Append SHA‑256 hashes for newly created `.npy` files to `data/checksums/manifest.csv`.  
  7. Produce a CSV `results/threshold_retention.csv` reporting the retention rate for each threshold.  
  - Verification: every `"accepted"` row has a corresponding `.npy` file, divergence values respect the thresholds, and retention CSV is present.  
  - **Files**: `src/data/optical_flow_counterfactual.py`, `data/flow/cf/*.npy`, `data/counterfactuals/metadata.csv`, `data/checksums/manifest.csv`, `results/threshold_retention.csv`.

- [ ] **T006** [ ] **Implement the Counterfactual Consistency loss**  
  - Add `src/model/loss.py` containing:  
    * `cross_entropy_loss` (standard `torch.nn.CrossEntropyLoss`).  
    * `counterfactual_consistency_loss(pred_orig, pred_cf)` returning KL‑divergence via `torch.nn.functional.kl_div`.  
    * `total_loss = ce + lambda_ * cc`.  
  - Provide a sanity‑check script `src/model/check_loss.py` that feeds identical logits for original and counterfactual inputs and asserts `cc == 0`.  
  - **Files**: `src/model/loss.py`, `src/model/check_loss.py`.

## Phase 1 – Setup and first end‑to‑end analysis (updated)

- [ ] **T007** [ ] **Train linear classifiers (baseline + λ‑sweep) across 15 seeds**  
  - `src/train/trainer.py` loads frozen FlowNet‑C features from `data/flow/orig/` **and** `data/flow/cf/` (only rows with `status=="accepted"`).  
  - Build a single linear layer (`torch.nn.Linear(1024, num_classes)`).  
  - Accept CLI arguments `--lambda`, `--seed`, `--epochs`.  
  - For each batch compute `L_total` using `src/model/loss.py`.  
  - Save checkpoints to `data/checkpoints/{model_id}_seed{seed}.pt`.  
  - Write a summary CSV `results/training_log.csv` with columns `model_id,lambda,seed,final_val_acc`.  
  - Verification: a checkpoint exists for every combination of `lambda ∈ {0, 0.1, 0.5, 1.0}` and `seed ∈ {0,…,14}`; `training_log.csv` contains a matching row for each.  
  - **Files**: `src/train/trainer.py`, `data/checkpoints/`, `results/training_log.csv`.

- [ ] **T008** [ ] **Evaluate models on original, swapped, and motion‑only test sets**  
  - `src/eval/evaluator.py` loads each checkpoint from `data/checkpoints/`.  
  - Compute predictions on three partitions:  
    * `data/test/original/` (original videos).  
    * `data/test/counterfactual/` (object‑swapped videos).  
    * `data/test/motion_only/` (objects blurred with Gaussian σ = 5).  
  - Calculate `accuracy_original`, `accuracy_counterfactual`, `delta_accuracy`, and `accuracy_motion_only`.  
  - Write per‑seed rows to `results/per_seed.csv` adhering to `evaluation_results.schema.yaml`.  
  - Verification: `results/per_seed.csv` exists, validates against the schema, and contains entries for every seed‑λ pair.  
  - **Files**: `src/eval/evaluator.py`, `results/per_seed.csv`.

- [ ] **T009** [ ] **Statistical validation (paired t‑test & bootstrap CI)**  
  - `src/eval/statistics.py` loads `results/per_seed.csv`.  
  - Perform a paired t‑test (`scipy.stats.ttest_rel`) comparing `delta_accuracy` of each λ‑model against the baseline (λ = 0) across the 15 seeds.  
  - Run 10 000 bootstrap resamples of the seed‑level differences to obtain a 95 % confidence interval.  
  - Write an aggregated summary `results/summary.csv` with columns `model_id,lambda,p_value,t_statistic,ci_lower,ci_upper`.  
  - Unit test `tests/test_statistics.py` checks that the function returns a dict containing all expected keys.  
  - **Files**: `src/eval/statistics.py`, `results/summary.csv`, `tests/test_statistics.py`.

- [ ] **T010** [ ] **Generate figures & tables for the paper hand‑off**  
  - `src/report/report.py` reads `results/per_seed.csv` and `results/summary.csv` and produces:  
    * Line plot **ΔAcc vs λ** → `figures/delta_acc_vs_lambda.png`.  
    * Histogram of bootstrap ΔAcc differences with 95 % CI overlay → `figures/bootstrap_hist.png`.  
    * Table `tables/evaluation_summary.csv` summarising all metrics (accuracy, ΔAcc, motion‑only accuracy, p‑values, effect sizes).  
  - Verification: each PNG file opens without error (e.g., via Pillow) and the CSV file contains the expected columns.  
  - **Files**: `src/report/report.py`, `figures/delta_acc_vs_lambda.png`, `figures/bootstrap_hist.png`, `tables/evaluation_summary.csv`.

- [ ] **T011** [ ] **Manual quality inspection of 50 accepted counterfactual pairs**  
  - `src/analysis/manual_inspection.py` randomly selects 50 rows with `status=="accepted"` from `metadata.csv`.  
  - For each pair compute SSIM on background regions (`skimage.metrics.structural_similarity`) and obtain ResNet‑18 class confidence for the swapped patch.  
  - Write `results/manual_inspection.csv` with columns `video_id,ssim_bg,patch_confidence,pass`.  
  - The script exits with a non‑zero status if fewer than 45 rows satisfy **SSIM > 0.95** **and** **patch_confidence > 0.9**.  
  - Verification: the CSV exists and the `pass` column is `True` for at least 45 rows.  
  - **Files**: `src/analysis/manual_inspection.py`, `results/manual_inspection.csv`.

- [ ] **T012** [ ] **Resource‑usage profiling to certify CPU‑only feasibility**  
  - `src/utils/profile.py` wraps the full training‑and‑evaluation pipeline, recording:  
    * Peak RAM (`psutil.virtual_memory().used`).  
    * Wall‑clock time (`time.perf_counter`).  
    * Number of logical CPUs used (`psutil.cpu_count(logical=True)`).  
    * Ensure no CUDA modules are imported (`"cuda"` not in any loaded module name).  
  - After execution, assert `peak_ram_mb <= 7000`, `wall_time_h <= 6`, `cpu_count_used <= 2`.  
  - Write JSON report `results/resource_profile.json` with measured values and a `pass` flag.  
  - Verification: the JSON file exists and `pass == true`.  
  - **Files**: `src/utils/profile.py`, `results/resource_profile.json`.

- [ ] **T013** [ ] **End‑to‑end reproducibility driver**  
  - Implement `src/pipeline/run_all.py` that sequentially executes:  
    1. `something_loader.py` (T002) to obtain a reproducible sample.  
    2. `optical_flow_precompute.py` (T004) for original videos.  
    3. `counterfactual.py` (T003) to create counterfactual videos and temporary metadata.  
    4. `optical_flow_counterfactual.py` (T005) for counterfactual flow, divergence sweep, and final metadata.  
    5. `trainer.py` (T007) for baseline and λ‑sweep models.  
    6. `evaluator.py` (T008).  
    7. `statistics.py` (T009).  
    8. `report.py` (T010).  
    9. `manual_inspection.py` (T011).  
    10. `profile.py` (T012).  
  - After all steps, the script checks that verification flags in `results/resource_profile.json`, `results/manual_inspection.csv` (`pass` column), and schema validation of `results/per_seed.csv` / `results/summary.csv` are all successful; otherwise it exits with a non‑zero code.  
  - Document the command line in `quickstart.md` (already present).  
  - **Files**: `src/pipeline/run_all.py`.

## Phase 2 – Additional validation and reporting

- [ ] **T017** [ ] **Validate `counterfactual_pair.schema.yaml` against `metadata.csv`**  
  - Use `jsonschema` to validate each row of `data/counterfactuals/metadata.csv` against `specs/001-llmxive-counterfactual-consistency/contracts/counterfactual_pair.schema.yaml`.  
  - Write any validation errors to `results/metadata_schema_errors.log`.  
  - Verification: the log is empty (no errors).  
  - **Files**: `src/validation/validate_counterfactual_schema.py`, `results/metadata_schema_errors.log`.

- [ ] **T018** [ ] **Validate `evaluation_results.schema.yaml` against result CSVs**  
  - Validate `results/per_seed.csv` and `results/summary.csv` against `specs/001-llmxive-counterfactual-consistency/contracts/evaluation_results.schema.yaml`.  
  - Write errors to `results/evaluation_schema_errors.log`.  
  - Verification: the log is empty.  
  - **Files**: `src/validation/validate_evaluation_schema.py`, `results/evaluation_schema_errors.log`.

- [ ] **T019** [ ] **Divergence‑threshold sweep analysis & reporting** (see Phase 0 T005 for core computation)  
  - Aggregate `results/threshold_retention.csv` to produce a summary figure `figures/threshold_retention.png` showing retention rate vs. threshold and the corresponding ΔAcc curves for each λ.  
  - Update `tables/evaluation_summary.csv` with a new section reporting how ΔAcc varies across thresholds.  
  - **Files**: `src/report/threshold_report.py`, `figures/threshold_retention.png`, updated `tables/evaluation_summary.csv`.

- [ ] **T020** [ ] **Linear probe on motion‑only representations**  
  - Extract frozen FlowNet‑C features for the motion‑only test set.  
  - Train a linear classifier (no λ) to predict action labels from these features.  
  - Record probe accuracy in `results/linear_probe.csv` and compare against baseline probe accuracy.  
  - **Files**: `src/eval/linear_probe.py`, `results/linear_probe.csv`.

- [ ] **T021** [ ] **Motion‑feature ablation study**  
  - Zero‑out FlowNet‑C motion features (or randomly shuffle them) for the original test set, evaluate the best λ‑model, and compute the resulting accuracy drop.  
  - Perform a paired t‑test versus the unablated model across the 15 seeds; store p‑value and effect size in `results/ablation_stats.csv`.  
  - **Files**: `src/eval/motion_ablation.py`, `results/ablation_stats.csv`.

- [ ] **T022** [ ] **Power‑analysis computation and documentation**  
  - Use `statsmodels.stats.power.TTestPower` to compute required seed count for the observed effect size; store the calculation and achieved power in `results/power_analysis.txt`.  
  - Reference this file in `paper/methods_results.md`.  
  - **Files**: `src/utils/power_analysis.py`, `results/power_analysis.txt`.

- [ ] **T014** [ ] **Write a concise methods & results summary linked to generated artifacts**  
  - Produce `paper/methods_results.md` that:  
    * Describes the data‑generation pipeline, loss formulation, training regime, and evaluation protocol.  
    * References the exact artifact paths for each table/figure (e.g., `figures/delta_acc_vs_lambda.png`, `tables/evaluation_summary.csv`).  
    * Reports any limitations discovered during manual inspection or resource profiling.  
  - Verify that every referenced file exists in the repository.  
  - **Files**: `paper/methods_results.md`.

- [ ] **T015** [ ] **Re‑run the documented workflow from scratch to confirm full reproducibility**  
  - Delete all generated directories under `data/`, `results/`, `figures/`, `tables/`, and `data/checkpoints/`.  
  - Execute the command from `quickstart.md` (`python -m src.pipeline.run_all --config configs/run.yaml`).  
  - Confirm that the run completes without errors, all verification flags are true, and the final artifacts match those recorded in `paper/methods_results.md`.  
  - **Files**: (no new files; this task is a verification step).

---

### Dependency & Parallel‑Safety Notes

- All `[P]` tags have been removed because several tasks write to shared files (`manifest.csv`, `metadata.csv`, `results/*.csv`). Tasks are intended to run sequentially via `run_all.py`.
- The pipeline respects the free‑tier CPU limits (2 cores, ≤ 7 GB RAM, ≤ 6 h wall‑clock) as verified by T012.
- All external models (Faster‑RCNN, ResNet‑18, FlowNet‑C) are downloaded once and version‑pinned in `requirements.txt` to guarantee reproducibility (Constitution I).
