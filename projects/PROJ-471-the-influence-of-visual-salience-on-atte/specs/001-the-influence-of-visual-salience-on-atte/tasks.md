# Tasks: The Influence of Visual Salience on Attentional Bias in Moral Judgements

**Inputs**: `specs/001-influence-of-visual-salience/spec.md`, `plan.md`, `data-model.md`, `contracts/` (dataset.schema.yaml, output.schema.yaml, salience.schema.yaml)

## Phase 1: Setup and first end‑to‑end analysis  

| Goal | Run an executable analysis on a small real subset early, proving that the pipeline can ingest data, generate salience maps, create ROI masks, extract fixation metrics, and produce a minimal aligned dataset. |

- [ ] **T001** [US1] Implement `code/bootstrap.py` so that it *accepts a `--root <dir>` argument* and correctly patches `llmxive_toolkit.paths.root` for the duration of the run. The script **must** create the standard directory tree under the supplied root (`code/`, `data/raw/`, `data/interim/`, `data/processed/`, `logs/`), write a pinned `requirements.txt`, and generate a `quickstart.md` that documents the command `python -m code.main --stage smoke`.  
  *Verification*: `tests/test_bootstrap.py` runs the script with a temporary `tmp_path` root, asserts that all directories and files exist **inside** `tmp_path`, and checks that `requirements.txt` matches the expected pinned list. The test must now pass (exit 0).

- [ ] **T002** [US1] Implement `code/ingestion/verify_data.py` to (1) confirm that `data/raw/ds003123/` exists, (2) require at least one `sub‑*/` participant folder containing eye‑tracking logs, (3) compute SHA‑256 checksums for **all** files under `stimuli/` **and** every eye‑tracking file, (4) write a non‑empty `data/raw/checksums.json` with the structure `{ "files": { "<relative_path>": "<hex_sha256>", … } }`. If any requirement is unmet, raise `RuntimeError("DATA_MISSING_001: ds003123 incomplete")`.  
  *Verification*: `tests/test_verify_data.py` validates that the script exits 0 when the full dataset is present, that `checksums.json` contains an entry for every file, and that the exact error message appears when the directory is missing or participant folders are absent.

- [ ] **T003** [FR‑001][US1] Write `code/salience/generate_maps.py` to (a) iterate over every image in `data/raw/ds003123/stimuli/`, (b) load the DeepGaze II weights **in CPU‑only mode**, (c) run inference on a **224 × 224** down‑sampled version of each image, (d) upscale the resulting salience map back to the original resolution and save it as `<stimulus_id>.npy` in `data/interim/salience_maps/`, and (e) append a record to `data/interim/salience_metadata.json` conforming to `contracts/salience.schema.yaml` with `generation_method="deepgaze_ii"` and `status="success"`. **If DeepGaze II fails for any image, the task aborts with a clear error**; no heuristic fallback is permitted, ensuring FR‑001 is satisfied.   <!-- FAILED-IN-EXECUTION: code/salience/generate_maps.py exit=1 -->
  *Verification*: `tests/test_salience_generation.py` runs the script on a 5‑image subset, checks that each `.npy` file matches the source image resolution, validates the JSON metadata against the schema, and asserts that `generation_method` equals `deepgaze_ii` for **all** records (no fallback entries).

- [ ] **T004** [FR‑008][US2] Implement `code/eye_tracking/segment_roi.py` with **lazy imports** for `detectron2`. The script must (1) look for existing masks in `data/raw/ds003123/masks/`; if found, copy them to `data/interim/masks/` and record provenance, (2) otherwise load YOLOv8 (`ultralytics.YOLO("yolov8n.pt")`) for **faces** **and** Detectron2 for **weapons** (both imported lazily inside the function). Both detectors must be successfully imported; if Detectron2 is unavailable the task aborts with a descriptive error rather than falling back to YOLOv8‑only. (3) generate binary PNG masks named `<stimulus_id>_face.png` and `<stimulus_id>_weapon.png` in `data/interim/masks/`, (4) log any image with no detections or low‑confidence detections to `data/interim/flagged_images.csv` and `data/interim/detection_metadata.json`, including a `detector_used` flag for each ROI type.  
  *Verification*: `tests/test_roi_segmentation.py` confirms that both mask types are produced for a sample image, that dimensions equal the source image, and that `detection_metadata.json` records `detector_used="detectron2"` for weapons when available. The test fails if Detectron2 is not used.

- [ ] **T005** [FR‑002][US2] Write `code/eye_tracking/parse_fixations.py` to (a) read raw eye‑tracking files from `data/raw/ds003123/eye_tracking/`, (b) use the ROI masks from T004 to assign each fixation to “face”, “weapon”, or “background”, (c) compute per‑trial metrics: `first_fixation_prob`, `dwell_time_ms`, `fixation_latency_ms`, (d) output `data/interim/fixations.csv` with columns `trial_id, participant_id, stimulus_id, roi_type, dwell_time_ms, first_fixation_prob, fixation_latency_ms`, and (e) write a warning entry to `logs/fixation_warnings.log` for any trial with missing or malformed gaze data (these trials are excluded from downstream analysis). The parser now includes robust CSV handling, skips malformed rows with warnings, and guarantees that the script exits cleanly even when some trials are incomplete.  
  *Verification*: `tests/test_fixation_extraction.py` processes a single participant’s file, checks that each `(trial_id, roi_type)` appears exactly once, that numeric fields are within plausible ranges, and that excluded trials are listed in the warning log without causing a crash.

- [ ] **T006** [FR‑009] Implement `code/analysis/feature_gen.py` to compute low‑level visual covariates for every stimulus image: (a) mean luminance (0‑255), (b) RMS contrast, (c) edge density via Canny (threshold = 100), and (d) scene complexity as the count of objects detected by Detectron2 panoptic segmentation. Store results in `data/interim/low_level_features.json` keyed by `stimulus_id`.  
  *Verification*: `tests/test_feature_computation.py` asserts that every stimulus has an entry, that luminance ∈ [0,255], contrast ≥ 0, edge_density ∈ [0,1], and scene_complexity is a non‑negative integer; the JSON must be parseable.

- [ ] **T007** [FR‑003][US2] Write `code/analysis/align_data.py` to merge (i) salience ROI means (averaged over the corresponding mask), (ii) low‑level features from T006, (iii) fixation metrics from T005, (iv) semantic covariates (if any), into `data/processed/aligned_data.csv` conforming to `contracts/dataset.schema.yaml`. Rows with any missing component are flagged `excluded=True`. Also generate `data/processed/alignment_stats.json` summarising total rows, excluded rows, and reason breakdown.  
  *Verification*: `tests/test_alignment.py` validates schema compliance, checks that ID fields match across sources, confirms correct exclusion flags, and that the stats JSON accurately reflects counts.

- [ ] **T008** [FR‑004][FR‑005][FR‑006] Implement `code/analysis/collinearity_and_modeling.py` to (1) load `aligned_data.csv` (excluding rows where `excluded=True`), (2) compute Variance Inflation Factors for fixed predictors (`salience_score`, `luminance`, `contrast`, `edge_density`, `scene_complexity`) using `pingouin.vif()`, (3) if any VIF > 5, apply PCA to the three low‑level covariates, retain components explaining ≥ 95 % variance, and store post‑orthogonalization VIFs, (4) fit **Model A** (random intercepts for participant and stimulus) and **Model B** (adds random slopes for `salience_score` per participant) with `statsmodels.MixedLM` on the dependent variable `dwell_time_ms`, (5) extract fixed‑effect estimates, standard errors, raw p‑values, and 95 % confidence intervals, (6) apply Benjamini‑Hochberg FDR correction to all fixed‑effect p‑values, (7) compute the stability metric `|β_A − β_B|` for the salience predictor, and (8) write `data/interim/model_a_results.csv` and `data/interim/model_b_results.csv` plus `logs/vif_pre.json`, `logs/vif_post.json`, and `logs/lmm_convergence.log`.  
  *Verification*: `tests/test_collinearity_and_modeling.py` checks that VIFs are numeric, that post‑orthogonalization VIF ≤ 5 (if orthogonalization occurred), that both model CSVs contain required columns, that FDR‑corrected p‑values are ≤ 1 and not larger than raw p‑values, that confidence intervals are ordered, and that the stability metric is non‑negative. Model fitting must complete without fatal errors.

- [ ] **T009** [SC‑003] Implement `code/analysis/power_analysis.py` to perform a simulation‑based power check: using the observed sample size, an assumed moderate effect size (Cohen’s f = 0.15), ICC ≈ 0.1, and α = 0.05, run 500 simulated datasets, fit Model B to each, and compute the proportion of simulations yielding a significant salience predictor after FDR correction. Write `power_estimate` and `power_status` (`"valid"` if ≥ 0.8, else `"invalid"`) into `data/processed/power.json`.  
  *Verification*: `tests/test_power_analysis.py` ensures the JSON contains both fields, that `power_estimate` ∈ [0,1], and that `power_status` matches the threshold rule.

- [ ] **T010** [FR‑007][SC‑004] Write `code/analysis/final_results.py` to assemble `data/processed/results.json` with all fields required by `contracts/output.schema.yaml`: model identifiers, fixed‑effect estimate, raw and FDR‑corrected p‑values, confidence interval, `sensitivity_analysis` (including Model A & B estimates and stability metric), `collinearity_report` (pre‑ and post‑VIF dicts), `power_status`, `power_estimate`, and the mandatory `"disclaimer": "correlational only"` **only if** any p‑value < 0.05 (otherwise still set to `"correlational only"` as per spec). The script must validate the JSON against the schema via `code/utils/final_validator.py` and raise `RuntimeError("SCHEMA_VALIDATION_FAILED")` on mismatch.  
  *Verification*: `tests/test_final_results.py` confirms schema compliance, correct insertion of the disclaimer, accurate propagation of power information, and that a checksum of the JSON is written to `logs/results_checksum.log`.

- [ ] **T012** [SC‑001][SC‑002] Implement `code/utils/resource_validator.py` to monitor RAM and CPU usage during the most intensive step (salience generation, T003) using `psutil`. It must log per‑image usage to `logs/resource.log` (JSON entries with `stimulus_id`, `ram_mb`, `cpu_seconds`). If peak RAM > 7 GB or cumulative CPU > 6 h, raise `RuntimeError("RESOURCE_LIMIT_EXCEEDED: ...")`. The script aborts; the platform will then retry on a GPU if available.  
  *Verification*: `tests/test_resource_validator.py` simulates normal usage (below limits) and a breach scenario, asserting that the appropriate exception and message are raised and logged.

- [ ] **T011** [SC‑001][SC‑002] Implement `code/utils/success_metrics.py` to (a) read `salience_metadata.json` and compute `salience_success_rate = (#status=="success") / total_images`, (b) parse `logs/resource.log` for peak RAM usage and total CPU seconds, (c) read `alignment_stats.json` for `exclusion_rate` and reason breakdown, (d) write these metrics to `data/interim/success_metrics.json` and append a human‑readable summary to `logs/metrics_summary.log` (e.g., “Salience maps generated: 195/200 (97.5 %); peak RAM: 6.3 GB; exclusion rate: 8.2 %”).  
  *Verification*: `tests/test_success_metrics.py` checks that numeric values lie in expected ranges, that the summary log contains the expected strings, and that the JSON is well‑formed.

- [ ] **T013** Implement `code/utils/final_validator.py` to validate three key artifacts against their schemas: `data/processed/aligned_data.csv` vs. `dataset.schema.yaml`, `data/processed/results.json` vs. `output.schema.yaml`, and `data/interim/salience_metadata.json` vs. `salience.schema.yaml`. Errors are written to `logs/validation_errors.log` and cause a `RuntimeError("VALIDATION_FAILED")`; on success, write a concise pass summary to `logs/validation_summary.log`. Additionally, generate `docs/pipeline.md` describing each stage, its inputs, outputs, and the exact command to run it in isolation.  
  *Verification*: `tests/test_final_validator.py` supplies both valid and deliberately corrupted artifacts, verifies that the validator accepts good files, rejects bad ones with informative messages, and that `pipeline.md` contains the expected sections and command snippets.

- [ ] **T014** Write `docs/research.md` (≤ 2000 words) containing a **methods** section that cites exact artifact locations (e.g., “salience computation: `data/interim/salience_metadata.json`”), a **results** section that reports all numeric findings directly from `results.json` (fixed‑effect estimate, CIs, p‑values, stability metric, VIFs, power estimate), a **limitations & null‑findings** subsection referencing the exclusion statistics and power status, and a **conclusion** that reiterates the mandatory `"correlational only"` disclaimer.  
  *Verification*: Added `tests/test_research_doc.py` which parses the generated `docs/research.md`, extracts every numeric claim, and cross‑checks it against the corresponding fields in `results.json` and `aligned_data.csv`. The test fails if any mismatch is found.

- [ ] **T015** Create `quickstart.sh` (documented in `quickstart.md`) that (1) verifies the presence of `data/raw/ds003123/` and aborts with clear instructions if missing, (2) runs `python -m code.main --stage all` to execute tasks T002–T013 in the correct order, (3) invokes `python -m code.utils.final_validator --all` to re‑validate all outputs, and (4) prints a concise summary of produced artifacts (e.g., “Aligned data: 10 k rows; results.json schema valid; salience maps: 195/200”).  
  *Verification*: A clean CI run on a fresh GitHub Actions free‑tier runner (2 CPU cores, ≤ 7 GB RAM, ≤ 6 h) executes `bash quickstart.sh` without errors, produces all expected files, and the final validation passes. The CI logs must show the summary report.

---  

### Dependency mapping (spec → tasks)

| Spec Requirement | Satisfied by Task(s) |
|------------------|----------------------|
| FR‑001 | T003 |
| FR‑002 | T005 |
| FR‑003 | T007 |
| FR‑004 | T008 |
| FR‑005 | T008 |
| FR‑006 | T008 |
| FR‑007 | T010 |
| FR‑008 | T004 |
| FR‑009 | T006 |
| SC‑001 | T011 |
| SC‑002 | T001, T012 |
| SC‑003 | T009 |
| SC‑004 | T008 |
| SC‑005 | T007 |
| SC‑006 | T008 |
| US‑1 | T001, T002, T003 |
| US‑2 | T004, T005, T006, T007 |
| US‑3 | T008, T009, T010 |

---  

**Note**: All tasks are unchecked (`- [ ]`) until their implementation and associated test suite pass. The ordering respects data flow: verification → salience generation → ROI creation → fixation extraction → feature computation → alignment → diagnostics → modeling → power → final results → metrics → validation → documentation → full workflow execution.  
