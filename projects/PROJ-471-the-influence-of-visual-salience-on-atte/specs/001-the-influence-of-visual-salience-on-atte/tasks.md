# Tasks: The Influence of Visual Salience on Attentional Bias in Moral Judgements

**Inputs**: `specs/001-influence-of-visual-salience/spec.md`, `plan.md`, `data-model.md`, `contracts/` (dataset.schema.yaml, output.schema.yaml, salience.schema.yaml), SCR-001.

## Phase 1: Setup and first end‑to‑end analysis

- [X] T001 [P] Establish project layout, generate `requirements.txt`, and provide a runnable entry point.  
  **Implementation**: `code/bootstrap.py` creates `code/`, `data/raw/`, `data/interim/`, `data/processed/`, `data/results/`, `code/tests/`, `docs/`. It also writes a pinned `requirements.txt` (Python 3.11, torch, torchvision, datasets, scikit‑learn, statsmodels, opencv‑python, ultralytics, detectron2, pandas, numpy, pingouin, psutil) that lists exact version pins required for reproducibility. The script prints a directory tree as proof. `code/config.py` defines paths, seeds, and thresholds. `specs/.../quickstart.md` documents the command `python code/main.py --stage smoke`.  
  **Verification**: Running `bootstrap.py` exits 0 and the printed tree includes all required folders; `requirements.txt` exists and matches the pinned list.

- [ ] T002 [US1] Real‑data ingestion with fail‑loud semantics.   <!-- FAILED-IN-EXECUTION: code/ingestion/download_data.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/ingestion/download_data.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/ingestion/download_data.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/ingestion/download_data.py exit=1 -->
  **Implementation**: `code/ingestion/download_data.py` uses the OpenNeuro CLI (`openneuro download ds003123`) or `datasets.load_dataset("openneuro/ds003123", ...)` to fetch the dataset into `data/raw/`. It verifies the expected `sub‑*` structure, computes SHA‑256 checksums stored in `data/raw/checksums.json`, and raises `RuntimeError("DATA_MISSING_001: Real data fetch failed")` on any error. No synthetic fallback code is present; a dedicated test scans the module for prohibited patterns.  
  **Verification**: `pytest code/tests/test_no_synthetic_fallback.py` passes; a fresh runner without the dataset exits non‑zero with the specified error code.

- [ ] T003a [US1] DeepGaze II inference (CPU‑only).  
  **Implementation**: `code/ingestion/salience_map.py` loads DeepGaze II with `device='cpu'`, processes images in configurable batches (default 8) respecting a per‑batch timeout of 15 min. For each image it writes a `.npy` salience map to `data/interim/salience_maps/` and records metadata (height, width, generation_method) in `metadata.json`.  
  **Verification**: Smoke run on the first 5 images creates matching‑resolution `.npy` files; `metadata.json` validates against `contracts/salience.schema.yaml`.

- [ ] T003b [US1] Resource validation for salience generation.  
  **Implementation**: `code/utils/resource_validator.py` monitors RAM usage via `psutil`, enforces a peak RAM < 7 GB and a total wall‑clock time ≤ 14 400 s (4 h) as per the plan’s performance goal. It writes `data/interim/resource_usage.json` with `ram_peak_gb`, `cpu_time_seconds`, and `cumulative_job_time_seconds`. Exceeding limits raises a `RuntimeError`.  
  **Verification**: The validator is invoked after each batch; failures abort the pipeline with a clear message.

- [ ] T004a [US2] ROI segmentation (faces & weapons).  
  **Implementation**: `code/eye_tracking/segment_roi.py` first checks for pre‑segmented masks; if absent it runs YOLOv8 for faces (confidence ≥ 0.85) and Detectron2 for weapons (confidence ≥ 0.85). Masks are saved as PNGs in `data/interim/masks/` with filenames `<stimulus_id>_face.png` and `<stimulus_id>_weapon.png`. Images with empty/invalid masks are logged to `data/interim/flagged_images.csv`.  
  **Verification**: Unit tests `test_segmentation.py` confirm that both face and weapon masks are produced for a sample image and that low‑confidence detections are excluded.

- [ ] T004b [US2] Fixation‑metric extraction (including latency).  
  **Implementation**: `code/eye_tracking/parse_fixations.py` parses raw eye‑tracking files, computes first‑fixation probability, dwell time (ms), and **fixation latency (ms)** per ROI, and writes `data/interim/fixations.csv`. Missing fixation data trigger a logged warning and trial exclusion.  
  **Verification**: Processing a single participant yields a CSV row with columns `trial_id, participant_id, stimulus_id, roi_type, dwell_time_ms, first_fixation_prob, fixation_latency_ms`. Tests in `test_eye_tracking.py` assert correct ranges and presence of latency.

- [ ] T005a [US2] Alignment of salience, fixation metrics, and low‑level features.  
  **Implementation**: `code/analysis/align_data.py` merges mean salience scores (from T003a) with fixation metrics (from T004b) on `trial_id`/`stimulus_id`. It also computes diagnostic low‑level visual features (luminance, contrast) via `code/analysis/feature_gen.py` and adds them as columns. Crucially, it now **preserves `fixation_latency_ms`** from the fixation extraction step, writing it into the final CSV `data/processed/aligned_data.csv`. The CSV conforms to `contracts/dataset.schema.yaml` (which will be amended by T005b to include the latency field).  
  **Verification**: `test_alignment.py` checks for zero mismatched IDs, schema compliance (including latency), and that `alignment_stats.json` reports the proportion of successfully aligned trials.

- [ ] T005b [US2] Amend aligned dataset schema to include fixation latency.  
  **Implementation**: `code/analysis/update_schema.py` programmatically adds a new property `fixation_latency_ms` (type `number`, description `Fixation latency in milliseconds`) to `specs/001-the-influence-of-visual-salience-on-atte/contracts/dataset.schema.yaml`. The script validates the updated schema against a minimal example and commits the change.  
  **Verification**: A test `test_schema_update.py` confirms that the schema now requires `fixation_latency_ms` and that a sample aligned CSV validates against it.

- [ ] T006a [US3] Power analysis (non‑halting).  
  **Implementation**: `code/analysis/lmm_power.py` runs a simulation‑based power analysis for the planned mixed‑effects model (medium effect d = 0.5). It writes `data/interim/power_analysis_report.json` with estimated power and a `power_status` field (`valid`/`invalid`). The pipeline **continues** regardless of the status; downstream tasks read the flag to populate the final results.  
  **Verification**: The report includes a sensitivity sweep; a test confirms that `power_status` is set correctly.

- [ ] T006b [US3] VIF diagnostic (informational).  
  **Implementation**: `code/analysis/vif_calc.py` computes variance‑inflation factors for salience against low‑level features. Results are saved to `data/interim/vif_report.json`. No halt occurs even if VIF > 5, satisfying SCR‑001’s rationale.  
  **Verification**: The JSON contains per‑predictor VIF values; a test ensures the file is written.

- [ ] T006c [US3] Fit Model A (random intercepts).  
  **Implementation**: `code/analysis/model_fit.py` fits a Linear Mixed‑Effects Model with random intercepts for participants and items using `statsmodels.MixedLM`. Convergence warnings are captured in `data/interim/lmm_convergence_warnings.log`. Results (fixed‑effect estimate, p‑value, 95 % CI) are written to `data/interim/model_a_results.csv`.  
  **Verification**: The CSV contains the required columns; a test checks that the model converged.

- [ ] T006d [US3] Fit Model B (random intercepts + slopes) and sensitivity analysis.  
  **Implementation**: Extends `model_fit.py` to fit Model B (adds random slopes for salience). It writes `data/interim/model_b_results.csv` and computes the stability metric (absolute difference in salience estimates). A plot `data/processed/sensitivity_plot.png` visualises the comparison.  
  **Verification**: Presence of both result CSVs and the PNG; a test validates the stability metric calculation.

- [ ] T007a [US3] FDR correction and disclaimer injection for all result artifacts.  
  **Implementation**: `code/analysis/robustness.py` applies Benjamini‑Hochberg correction to all p‑values in `model_a_results.csv` and `model_b_results.csv`, producing `model_a_results_fdr.csv` and `model_b_results_fdr.csv`. It scans each CSV (both raw and FDR‑corrected versions) for rows where the (raw or corrected) p‑value < 0.05 and appends a `disclaimer` column with the exact phrase **“correlational only”**. This satisfies FR‑007 for every machine‑readable CSV artifact.  
  **Verification**: The corrected CSVs contain the new column only where appropriate; a unit test confirms the conditional insertion.

- [ ] T008a [US3] Final results generation (ordered power verification) with disclaimer.  
  **Implementation**: `code/main.py` now invokes `power_verify.py` **before** assembling `results.json`. The script reads `power_status` from the power analysis report and includes it in the JSON. It also ensures the `disclaimer` field (constant “correlational only”) is present **only if** any p‑value in the final model output is < 0.05, matching FR‑007’s conditional requirement. The JSON is then validated against `contracts/output.schema.yaml` via `final_validator.py`.  
  **Verification**: A fresh run produces a schema‑valid `results.json` with accurate `power_status` and, when applicable, the disclaimer; the validator reports no errors.

## Phase 2: Complete the study and validate its evidence

- [ ] T009 Write methods/results account in `research.md` linking all numeric values to concrete artifact files (results.json, sensitivity_plot.png, alignment_stats.json, salience_stats.json, power_analysis_report.json).  
  **Verification**: Manual audit confirms every reported number has a traceable source.

- [ ] T010 Document full pipeline handoff.  
  **Implementation**: `README.md` (repo root) now lists installation steps, the pinned `requirements.txt`, data‑acquisition protocol, and the quick‑start command. `docs/pipeline.md` details each stage, the dataset recipe, and resource limits. A fresh environment run (`quickstart.md` command) completes with exit code 0, all tests pass, and final artifacts are validated.  
  **Verification**: CI runs the quick‑start on a clean runner; success is recorded.

## Phase 3: Reproducible results and paper handoff

- [ ] T011 Write methods/results account in `research.md` linking all numeric values to concrete artifact files (results.json, sensitivity_plot.png, alignment_stats.json, salience_stats.json, power_analysis_report.json).  
  **Verification**: Manual audit confirms every reported number has a traceable source.

- [ ] T012 Document full pipeline handoff.  
  **Implementation**: `README.md` (repo root) now lists installation steps, the pinned `requirements.txt`, data‑acquisition protocol, and the quick‑start command. `docs/pipeline.md` details each stage, the dataset recipe, and resource limits. A fresh environment run (`quickstart.md` command) completes with exit code 0, all tests pass, and final artifacts are validated.  
  **Verification**: CI runs the quick‑start on a clean runner; success is recorded.

## Task Traceability Mapping (Plan → Tasks)

| Plan Task ID | Consolidated Task(s) |
|--------------|----------------------|
| T013a (GBVS fallback) | T003a (fallback logic) |
| T020e (Mask Validation) | T004a (mask confidence check) |
| T029c (Power Analysis Gate) | T006a (non‑halting power analysis) |
| T030b (Low‑Level Feature Generation) | T005a (diagnostic feature columns) |
| T031 (Distributional Check) | T006d (GLMM fallback inside model_fit) |
| T032 (LMM Fit) | T006c & T006d |
| T037 (Code Documentation) | T001 (bootstrap documentation) |
| T038 (Code Cleanup) | Implicit in task revisions |
| T039 (Batched Salience Generation) | T003a (batch inference) |
| T041 (Quickstart Validation) | T010 (pipeline handoff) |
| T042 (Resource Validator) | T003b |
| T044 (Removed GPU Offload) | N/A (already omitted) |
| T049 (Final Validator) | T008a (final_validator step) |

## Dependencies

| Dependency | Provided By |
|------------|--------------|
| `requirements.txt` | T001 |
| `code/bootstrap.py` | T001 |
| `code/ingestion/download_data.py` | T002 |
| `code/ingestion/salience_map.py` | T003a |
| `code/utils/resource_validator.py` | T003b |
| `code/eye_tracking/segment_roi.py` | T004a |
| `code/eye_tracking/parse_fixations.py` | T004b |
| `code/analysis/align_data.py` | T005a |
| `code/analysis/update_schema.py` | T005b |
| `code/analysis/lmm_power.py` | T006a |
| `code/analysis/vif_calc.py` | T006b |
| `code/analysis/model_fit.py` | T006c / T006d |
| `code/analysis/robustness.py` | T007a |
| `code/main.py` | T008a |
| `code/utils/final_validator.py` | T008a |
| `docs/pipeline.md` | T010 |
| `README.md` | T010 |