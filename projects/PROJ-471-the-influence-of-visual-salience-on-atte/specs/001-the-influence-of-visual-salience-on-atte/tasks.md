# Tasks: The Influence of Visual Salience on Attentional Bias in Moral Judgements

**Inputs**: `specs/001-influence-of-visual-salience/spec.md`, `plan.md`, `data-model.md`, `contracts/` (dataset.schema.yaml, output.schema.yaml, salience.schema.yaml)

## Phase 1: Setup and first end‑to‑end analysis  

- [ ] T001 [P] Establish project layout, generate `requirements.txt`, and provide a runnable entry point.  
  **Implementation**: `code/bootstrap.py` creates the standard directory tree (`code/`, `data/raw/`, `data/interim/`, `data/processed/`, `docs/`), writes a pinned `requirements.txt`, and adds a `quickstart.md` command `python -m code.main --stage smoke`.  
  **Verification**: Running `bootstrap.py` exits 0, prints the directory tree, and the generated `requirements.txt` matches the pinned list.  

- [ ] T002 [US1] Download the “Moral Foundations Eye‑Tracking Dataset” (OpenNeuro ds003123) with fail‑loud semantics and verify integrity.   <!-- FAILED-IN-EXECUTION: code/ingestion/download_data.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/ingestion/download_data.py exit=1 -->
  **Implementation**: `code/ingestion/download_data.py` uses the OpenNeuro CLI (`openneuro download ds003123 --out data/raw/`) or falls back to `datasets.load_dataset("openneuro/ds003123", streaming=True)`. After download it validates the expected `sub‑*` folders, computes SHA‑256 checksums stored in `data/raw/checksums.json`, and raises `RuntimeError("DATA_MISSING_001")` only if the dataset cannot be fetched. No synthetic data fallback is provided.  
  **Verification**: A test `test_download_success.py` asserts that the script exits 0 when the dataset is present and that `checksums.json` exists and matches the recorded hashes.  

- [ ] T003 [US1] Compute pixel‑wise salience maps for all 200 stimulus images using **DeepGaze II in CPU‑only mode**.   <!-- FAILED-IN-EXECUTION: code/salience/generate_maps.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/salience/generate_maps.py exit=1 -->
  **Implementation**: `code/salience/generate_maps.py` iterates over `data/raw/images/*.png`, loads the DeepGaze II model with `device="cpu"` (no GPU fallback), computes salience, writes `.npy` maps to `data/interim/salience_maps/`, and records metadata (`stimulus_id`, `map_path`, `resolution`, `generation_method="deepgaze_ii"`, `status="success"` or `"failed"` with reason) in `data/interim/salience_metadata.json`. Any failure for an image aborts the run with a logged error (no GBVS fallback).  
  **Verification**: After processing the first 5 images, the corresponding `.npy` files exist, their shapes match the source images, and `salience_metadata.json` validates against `contracts/salience.schema.yaml`.  

- [ ] T004 [US2] Generate semantic ROI masks for “faces” (YOLOv8) and “weapons” (Detectron2) when pre‑segmented masks are absent.  
  **Implementation**: `code/eye_tracking/segment_roi.py` checks `data/raw/masks/`. Missing masks trigger YOLOv8 inference (`ultralytics.YOLO`) for faces (confidence ≥ 0.85) and Detectron2 inference for weapons (confidence ≥ 0.85). Masks are saved as PNGs in `data/interim/masks/` named `<stimulus_id>_face.png` and `<stimulus_id>_weapon.png`. Images yielding empty or low‑confidence masks are logged to `data/interim/flagged_images.csv`.  
  **Verification**: Unit test `test_roi_segmentation.py` confirms that both mask types are produced for a sample image and that low‑confidence detections are excluded.  

- [ ] T005 [US2] Extract fixation metrics (first‑fixation probability, dwell time, fixation latency) per ROI and output a structured CSV.  
  **Implementation**: `code/eye_tracking/parse_fixations.py` reads raw eye‑tracking files from `data/raw/eye_tracking/`, identifies fixations within each ROI using the masks from T004, computes:  
  - `first_fixation_prob` (proportion of trials where the first fixation lands in the ROI)  
  - `dwell_time_ms` (total fixation duration within the ROI)  
  - `fixation_latency_ms` (time from stimulus onset to first fixation in the ROI)  
  Results are written to `data/interim/fixations.csv`. Trials with missing gaze data are excluded and logged with a warning.  
  **Verification**: Processing a single participant’s file yields a row containing all three metrics; `test_fixation_extraction.py` checks numeric ranges and that `fixation_latency_ms` is non‑negative.  

- [ ] T006 [US2] Compute low‑level visual features (luminance, contrast, edge density) for each stimulus image.  
  **Implementation**: `code/analysis/feature_gen.py` loads each image, calculates average luminance, RMS contrast, and edge density (Canny edge proportion), and appends these values to the metadata file `data/interim/low_level_features.json`.  
  **Verification**: A sanity‑check script verifies that every image has three numeric entries; `test_feature_computation.py` asserts that values fall within plausible ranges.  

- [ ] T007 [US2] Align salience scores, ROI masks, fixation metrics, and low‑level features into a single analysis dataset.  
  **Implementation**: `code/analysis/align_data.py` merges `salience_metadata.json`, `low_level_features.json`, and `fixations.csv` on `stimulus_id` and `trial_id`, producing `data/processed/aligned_data.csv`. The CSV includes all columns required by `contracts/dataset.schema.yaml` (including `fixation_latency_ms`). Trials flagged in `flagged_images.csv` or with missing data are marked `excluded=True`.  
  **Verification**: `test_alignment.py` confirms that every row satisfies the schema, that there are no ID mismatches, and that the proportion of excluded trials is recorded in `data/processed/alignment_stats.json`.  

- [ ] T008 [US3] Perform a simulation‑based power analysis for the planned mixed‑effects model and abort if power < 0.8.  
  **Implementation**: `code/analysis/power_analysis.py` simulates 500 datasets using the observed variance components, a moderate effect size (f = 0.15), and fits the full model (random intercepts + random slopes). It writes `data/interim/power_report.json` containing `estimated_power` and `power_status`. If `estimated_power` < 0.8 the script raises `RuntimeError("POWER_INSUFFICIENT")`, causing the pipeline to stop.  
  **Verification**: `test_power_analysis.py` checks that the JSON contains both fields and that the script aborts when power is insufficient.  

- [ ] T009 [US3] Compute variance‑inflation factors (VIF) for all fixed predictors and enforce a threshold of 5.  
  **Implementation**: `code/analysis/vif_calc.py` loads `aligned_data.csv`, fits a linear model with all predictors, calculates VIF per predictor, and writes `data/interim/vif_report.json`. If any VIF > 5 the script raises `RuntimeError("VIF_THRESHOLD_EXCEEDED")`, halting further analysis.  
  **Verification**: `test_vif.py` asserts that the JSON contains a VIF entry for each predictor, that values are numeric, and that the script fails when a threshold violation occurs.  

- [ ] T010 [US3] Fit Linear Mixed‑Effects Model A (random intercepts only) and Model B (random intercepts + random slopes for salience).  
  **Implementation**: `code/analysis/model_fit.py` uses `statsmodels.MixedLM` to fit:  
  - **Model A** → results saved as `data/interim/model_a_results.csv` (fixed‑effect estimate, standard error, p‑value, 95 % CI).  
  - **Model B** → results saved as `data/interim/model_b_results.csv` (same columns plus random‑slope variance).  
  Convergence warnings are captured in `data/interim/lmm_warnings.log`.  
  **Verification**: `test_model_fit.py` checks that both CSVs contain the required columns, that the models converged (no fatal warnings), and that the salience estimate differs between models.  

- [ ] T011 [US3] Apply Benjamini‑Hochberg FDR correction and inject the required disclaimer into all result artifacts.  
  **Implementation**: `code/analysis/robustness.py` reads `model_a_results.csv` and `model_b_results.csv`, applies BH correction to the p‑values, writes `model_a_results_fdr.csv` and `model_b_results_fdr.csv`, and adds a column `disclaimer` with the exact phrase **“correlational only”** for any row where the (raw or corrected) p‑value < 0.05. The same logic is applied to the final JSON results (see T012).  
  **Verification**: `test_fdr_disclaimer.py` confirms that the disclaimer column appears only where appropriate and that the corrected p‑values are ≤ 1.  

- [ ] T012 [US3] Assemble the final results JSON, embed power status, and ensure schema compliance.  
  **Implementation**: `code/main.py` orchestrates the pipeline, reads `model_b_results_fdr.csv` to extract the salience fixed‑effect estimate, confidence interval, raw and FDR‑corrected p‑values, incorporates the `power_status` from T008, adds the `"disclaimer": "correlational only"` field if any p‑value < 0.05, and writes `data/processed/results.json`. The file is validated against `contracts/output.schema.yaml` via `code/utils/final_validator.py`.  
  **Verification**: `test_final_results.py` validates the JSON against the schema and checks that `disclaimer` is present only when required and that `power_status` matches the power report.  

- [ ] T013 Document the full reproducible pipeline and handoff to the paper stage.  
  **Implementation**:  
  - `README.md` now lists installation steps, the exact `requirements.txt`, the data‑acquisition command, and the quick‑start command (`bash quickstart.sh`).  
  - `docs/pipeline.md` describes each stage (download, salience, ROI, fixation, alignment, feature computation, power, VIF, modeling, robustness, final results) with file‑path references.  
  - `research.md` provides a concise methods and results narrative, linking every reported number to its source artifact (e.g., “salience‑effect estimate = 0.42 (see `results.json` → `fixed_effect_estimate`)”).  
  **Verification**: A clean CI run on a fresh runner executes `bash quickstart.sh`, completes all tasks without errors, and the verifier confirms that every contract‑defined artifact exists and passes schema validation.  

- [ ] T014 [P] Verify dataset integrity after download.  
  **Implementation**: `code/ingestion/verify_data.py` reads `data/raw/checksums.json`, recomputes SHA‑256 hashes for all files in `data/raw/`, and asserts they match. It raises an error if any mismatch is found.  
  **Verification**: `test_verify_data.py` ensures the script fails when a file is corrupted and passes when all hashes match.  

- [ ] T015 [P] Compute and record the proportion of successfully generated salience maps (SC‑001).  
  **Implementation**: `code/salience/compute_success_rate.py` loads `salience_metadata.json`, calculates `success_rate = (# status=="success") / total_images`, and writes the metric to `data/interim/salience_success_rate.json`.  
  **Verification**: `test_salience_success_rate.py` checks that the JSON contains a `success_rate` field between 0 and 1 and that it matches the counts in the metadata.  

- [ ] T016 [P] Log and validate RAM/CPU usage against GitHub Actions free‑tier limits (SC‑002).  
  **Implementation**: `code/utils/resource_validator.py` wraps the execution of the salience generation step (T003) using `psutil` to record peak RAM and CPU time, writes `data/interim/resource_usage.json` with fields `peak_ram_gb`, `cpu_seconds`, and compares them to limits (7 GB, 6 h). If limits are exceeded, the script raises `RuntimeError("RESOURCE_LIMIT_EXCEEDED")`.  
  **Verification**: `test_resource_validator.py` simulates high usage and checks that the script aborts, and also verifies normal usage passes.  
