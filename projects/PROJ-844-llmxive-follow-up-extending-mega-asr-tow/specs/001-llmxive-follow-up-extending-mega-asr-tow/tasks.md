# Tasks: Extending “Mega‑ASR” – Semantic Collapse Thresholds  

**Inputs**: `spec.md`, `plan.md`, `data-model.md`, contract schemas, and reviewer feedback.  

The list below follows the canonical checklist format `- [ ] T### [P?] [USx?] description …`.  
All file paths are relative to the project root.  Tasks are ordered to respect data‑flow dependencies; unchecked boxes indicate pending implementation or revision.  Each task includes concrete verification steps.

---  

## Phase 0 – Project scaffolding & test infrastructure  

- [ ] T001 **Create core project layout & pytest configuration** –  
  *Create directories*: `code/`, `data/raw/`, `data/derived/`, `data/validation/`, `tests/unit/`.  
  *Add files*: `code/config.py` (global constants: `SEED=42`, `SAMPLE_SIZE=50000`, SNR/RT60 lists, GPU‑cluster settings), `tests/__init__.py`, `tests/unit/__init__.py`, `pytest.ini` (basic config).  
  **Verification**: `tree` shows the directories, `pytest --collect-only` runs without errors, and `code/config.py` can be imported.

- [ ] T002 **Document quick‑start command** –  
  Add `docs/quickstart.md` with a runnable example that executes a minimal pilot pipeline on **10 clips** and produces `data/derived/stress_curves.parquet`, `data/derived/collapse_points.parquet`, and `data/derived/critical_vector.parquet`. Include a helper script `run_quickstart.sh`.  
  **Verification**: CI runs `bash run_quickstart.sh` and exits with status 0; the three Parquet files exist and contain at least one row each.

- [ ] T026 **Run G*Power power‑analysis (FR‑032)** –  
  Execute a G*Power calculation (linear multiple regression, f² = 0.02, α = 0.05, power = 0.80) to determine the required minimum sample size. Record the result in `logs/power_analysis.txt`.  
  **Verification**: The file exists and contains a numeric N ≥ 395; unit test `tests/unit/test_power_analysis.py` checks the value.

- [ ] T027 **Re‑run power‑analysis after final sample size (FR‑032‑VERIF)** –  
  After the stratified subset is selected, re‑execute the same G*Power computation with the actual N and log the achieved power (expected ≥ 0.99). Store in `logs/power_analysis_verif.txt`.  
  **Verification**: CI asserts the logged power ≥ 0.99; test `tests/unit/test_power_verif.py` validates the file content.

- [ ] T032 **Human‑validation gate pilot (pre‑run)** –  
  Run a lightweight human intelligibility annotation on **100** clips (≥ 3 raters each) to compute an early AUC‑ROC between `ss_score` and human labels. Store the metric in `logs/human_validation_pilot.txt`.  
  **Verification**: Unit test checks that the AUC‑ROC ≥ 0.85; pipeline aborts if not met.

- [ ] T033 **Human‑validation gate final verification** –  
  After full annotation (see Phase 5 tasks), recompute AUC‑ROC and abort if < 0.85. Log final metric in `logs/human_validation_final.txt`.  
  **Verification**: CI asserts final AUC‑ROC ≥ 0.85; test `tests/unit/test_human_validation_final.py` validates.

---  

## Phase 1 – Data acquisition & stratified sampling  

- [ ] T003 **Download & stratify Voices‑in‑the‑Wild‑2M** –  
  Implement `code/data_loader.py::load_viw_subset()` that streams the dataset via `datasets.load_dataset("voices-in-the-wild/2M", streaming=True)`, stratifies by `speaker_id` and `environment_id` (seed = 42), selects **≥ 50 000** clean clips, writes a manifest `data/raw/viw_subset.parquet`, and records SHA‑256 checksums in `data/raw/viw_checksums.txt`.  
  **Verification**: `wc -l data/raw/viw_subset.parquet` ≥ 50000; a unit test `tests/unit/test_viw_loader.py` asserts the stratification proportions and checksum validity.

---  

## Phase 2 – Distortion generation (GPU‑enabled)  

- [ ] T004 **Implement GPU‑accelerated distortion engine** –  
  `code/distortion_engine.py` uses **pyroomacoustics** to apply the Cartesian product of **9 SNR levels** (‑10 dB … 30 dB) and **6 RT60 levels** (0.1 s … 0.6 s), yielding **54 compound vectors** per clip. The script runs on the paid 4‑node V100 GPU cluster (`device="cuda"`). It logs any missing scenario (FR‑017) to `data/derived/distortion_coverage_report.json`.  
  **Verification**: After a pilot on 100 clips, the report contains zero missing scenarios; `tests/unit/test_distortion_vectors.py` checks that exactly 54 vectors are generated per clip.

- [ ] T005 **Generate stress‑curve records** –  
  Extend `code/main.py` to iterate over the VIW subset, invoke the distortion engine, run **five small ASR models** (e.g., `whisper_tiny`, `distil_whisper`, etc.) on each distorted audio, and write **`data/derived/stress_curves.parquet`** conforming to `contracts/stress_curve.schema.yaml`. Include fields for `ss_score`, `wer`, timestamps, and a unique `curve_id`.  
  **Verification**: File exists, `len(df) == 50000 * 54 * 5`; schema validation (`jsonschema.validate`) passes; unit test `tests/unit/test_stress_curves.py` asserts row count and required columns.

- [ ] T025 **Realism validation against DNS‑Challenge (FR‑018)** –  
  Download the DNS‑Challenge dataset, compute Log‑Mel Spectral Distance (LMSD) between each synthetic distorted clip and its closest real‑world noisy counterpart (±1 dB / ±0.1 s tolerance). Verify that the median LMSD ≤ 0.15. Store results in `data/derived/realism_validation.parquet` and abort if the threshold is not met.  
  **Verification**: CI logs the median LMSD; a test `tests/unit/test_realism.py` asserts the metric ≤ 0.15.

---  

## Phase 3 – Semantic scoring & fallback metric  

- [ ] T006 **Compute Semantic Similarity Score (SSS)** –  
  `code/metrics.py::compute_sss()` encodes clean transcripts and ASR hypotheses with **sentence‑transformers/all‑MiniLM‑L6‑v2** (CPU‑tractable) and stores cosine similarity in the `ss_score` column of `stress_curves.parquet`.  
  **Verification**: Randomly sample a row; `ss_score` ∈ [0, 1]; a test `tests/unit/test_sss.py` validates the range.

- [ ] T007 **Phoneme‑edit‑distance fallback (FR‑022)** –  
  For rows where `rt60 > 0.5 s` **and** the embedding‑human correlation (computed later) < 0.85, compute phoneme‑level edit distance using **Montreal Forced Aligner**, store it in a new column `phoneme_distance`, and set boolean `use_phoneme_fallback`.  
  **Verification**: `SELECT COUNT(*) FROM stress_curves WHERE use_phoneme_fallback = true` > 0; `tests/unit/test_fallback.py` checks column existence and non‑null values for flagged rows.

---  

## Phase 4 – Collapse‑point identification (deterministic)  

- [ ] T008 **Compute baseline metrics & normalize scores (CCM preparation)** –  
  From the clean (baseline) scenario in `stress_curves.parquet`, extract per‑clip baseline SSS and baseline WER. Add columns `baseline_sss` and `baseline_wer` to each clip’s records, then compute `norm_sss = ss_score / baseline_sss` and `norm_wer = wer / baseline_wer`. Finally compute **Composite Collapse Metric (CCM) = 0.7 × (1‑norm_sss) + 0.3 × norm_wer** and store `norm_sss`, `norm_wer`, `ccm` in `data/derived/stress_curves_normalized.parquet`.  
  **Verification**: Columns exist, are numeric; a test `tests/unit/test_ccm.py` verifies a few rows manually.

- [ ] T009 **Derive deterministic collapse intensities (FR‑021, FR‑020, FR‑010, FR‑036)** –  
  Using the normalized data from T008, identify the first step where `ccm ≥ 0.5` and apply linear interpolation between steps N and N+1 (FR‑020). Record the step as `collapse_intensity`. Compute the step with the maximum negative derivative of the SSS spline (inflection step) and flag `early_collapse_flag` if it occurs before the CCM crossing. Also compute **Universal Collapse Intensity** where absolute `ss_score ≤ 0.5` (FR‑036). Write **`data/derived/collapse_points.parquet`** matching `contracts/collapse_point.schema.yaml`.  
  **Verification**: Schema validation passes; a synthetic‑curve unit test confirms correct collapse step; the file is non‑empty.

- [ ] T024 **Compute and store curve‑shape data (FR‑012)** –  
  Fit a smooth spline to each stress curve, extract shape descriptors (e.g., sigmoid vs. linear classification, maximum derivative, curvature metrics) and write them to `data/derived/curve_shape.parquet` conforming to a future `contracts/curve_shape.schema.yaml`.  
  **Verification**: File exists; a test `tests/unit/test_curve_shape.py` checks that each record contains required fields.

---  

## Phase 5 – Human‑validation gate (FR‑011, FR‑016)  

- [ ] T010 **Collect human intelligibility annotations** –  
  Run `code/annotation_tool.py` to crowdsource binary intelligibility scores for **≥ 1 000** clips (≥ 3 raters each). Store results in `data/validation/human_annotations.parquet`.  
  **Verification**: File has ≥ 1 000 rows and includes columns `clip_id`, `rater_id`, `label`; a test checks raters per clip ≥ 3.

- [ ] T011 **Validate SSS against human labels & apply fallback** –  
  Compute AUC‑ROC between `ss_score` and the human binary label; require **AUC‑ROC ≥ 0.85**. If the threshold is not met, automatically switch to the phoneme‑distance metric for the high‑reverb subset (FR‑022). Abort the pipeline with a clear `RuntimeError` if **both** metrics fail.  
  **Verification**: CI logs the AUC value; pipeline proceeds only when condition holds; a test asserts the abort behavior on simulated low AUC.

- [ ] T030 **Create expert‑annotated validation subset (FR‑033)** –  
  Randomly select **500** stress‑curve records, have expert listeners label the true collapse intensity, and store the results in `data/derived/manual_collapse.parquet` (matching a forthcoming `contracts/manual_collapse.schema.yaml`).  
  **Verification**: File contains 500 rows with an `expert_label` field; a unit test `tests/unit/test_manual_collapse.py` validates row count and schema.

---  

## Phase 6 – Regression modeling & interaction analysis  

- [ ] T012 **Generate regression input table** –  
  `code/prepare_regression.py` builds `data/derived/regression_input.parquet` containing acoustic parameters (SNR, RT60, squared terms, interaction term), baseline WER, transcript‑perplexity (computed via a language‑model), and the **target** `inflection_step` (from `collapse_points.parquet`). Validate against `contracts/regression_input.schema.yaml`.  
  **Verification**: Schema validation succeeds; a unit test confirms row count matches the number of unique (clip, model) pairs.

- [ ] T013 **Train hierarchical mixed‑effects regression (FR‑005, FR‑025, FR‑028)** –  
  `code/train_regressor.py` fits a mixed‑effects model (`statsmodels.MixedLM`) on an 80 % stratified training split (by speaker + distortion + difficulty). Evaluate on the held‑out 20 % set, requiring **R² ≥ 0.6** and reporting MAE. Store coefficients, 95 % confidence intervals, R², MAE, and the derived **critical interaction vector** in `data/derived/critical_vector.parquet`.  
  **Verification**: CI asserts `critical_vector.parquet` contains required fields and that `r2 >= 0.6`; a test checks that confidence‑interval columns are present.

- [ ] T014 **Permutation baseline test (FR‑027)** –  
  Randomly permute acoustic predictor rows, retrain the same model, and confirm that **ΔR² ≥ 0.20** relative to the non‑permuted model. Log the result in `data/derived/permutation_baseline.json`.  
  **Verification**: Test `tests/unit/test_permutation.py` asserts the stored ΔR² meets the threshold.

- [ ] T015 **Interaction‑significance & multiple‑comparison correction (FR‑013, FR‑008)** –  
  Fit an additive linear model (no interaction terms), compare to the full mixed model via an F‑test, compute raw p‑values for each interaction term, apply **Benjamini‑Hochberg FDR ≤ 0.05**, and write `data/derived/corrected_pvalues.json`.  
  **Verification**: JSON includes `fdr_corrected` flags; a test ensures at least one interaction term remains significant after correction.

- [ ] T028 **Partial‑correlation analysis (FR‑035)** –  
  Compute the partial‑correlation between acoustic predictors and `inflection_step` while controlling for transcript‑difficulty, report the unique variance explained, and store results in `data/derived/partial_correlation.json`.  
  **Verification**: Unit test `tests/unit/test_partial_corr.py` checks that the JSON contains numeric values and that the controlled variance is > 0.

---  

## Phase 7 – Sensitivity & universality checks  

- [ ] T016 **Sensitivity analysis over SSS thresholds & WER multipliers (FR‑006, SC‑002)** –  
  Sweep SSS thresholds {0.45, 0.50, 0.55} and WER multipliers {1.5, 2.0, 2.5}. For each of the nine configurations, recompute collapse points, retrain the regression, and record the coefficient vector. Compute the **coefficient‑of‑variation (CV)** across configurations; require **CV ≤ 0.10**. Output `data/derived/sensitivity_analysis.csv`.  
  **Verification**: CI asserts the max CV column ≤ 0.10; a test loads the CSV and checks the constraint.

- [ ] T017 **Universality of critical interaction vectors (FR‑051)** –  
  Calculate cosine similarity between each model’s critical vector and the mean vector across all models; require **similarity ≥ 0.80**. Perform a permutation test shuffling model labels and ensure the observed similarity exceeds the 95th percentile of the permutation distribution. Store results in `data/derived/cross_model_similarity.json`.  
  **Verification**: Test `tests/unit/test_universality.py` confirms similarity ≥ 0.80 and permutation‑test p‑value < 0.05.

- [ ] T029 **Precision/Recall evaluation for deterministic collapse points (SC‑009)** –  
  Compare deterministic collapse intensities from `collapse_points.parquet` against the expert‑annotated ground truth in `manual_collapse.parquet`. Compute precision and recall; both must be ≥ 0.90. Log results in `data/derived/collapse_pr_metrics.json`.  
  **Verification**: CI asserts both metrics meet the threshold; a unit test `tests/unit/test_collapse_pr.py` validates the calculation.

---  

## Phase 8 – Final validation, reporting & reproducibility  

- [ ] T018 **Schema validation of all derived artifacts (FR‑034)** –  
  Run `code/validate_artifacts.py` to validate `stress_curves.parquet`, `collapse_points.parquet`, `critical_vector.parquet`, `curve_shape.parquet`, `sensitivity_analysis.csv`, `cross_model_similarity.json`, and all JSON reports against their respective schemas. Abort on any violation.  
  **Verification**: CI logs “All schemas validated”.

- [ ] T019 **Generate final reproducible report (FR‑007, SC‑001 – SC‑009)** –  
  `code/report_generator.py` creates `docs/final_report.md` containing:  
  * Power‑analysis verification (FR‑032‑VERIF)  
  * Human‑validation AUC‑ROC (SC‑006)  
  * Regression performance (R², MAE)  
  * Interaction significance (FDR‑corrected p‑values)  
  * Sensitivity CV results  
  * Universality similarity & permutation test  
  * Precision/recall for deterministic collapse points (≥ 0.90)  
  * All figures plotted directly from Parquet data (stress curves, collapse‑point histograms, coefficient plots)  
  All statements use **associational phrasing only** (FR‑007).  
  **Verification**: A sanity‑check script parses the markdown and confirms presence of each required metric; CI passes.

- [ ] T020 **Comprehensive unit‑test suite** –  
  Ensure `tests/unit/` contains at least one test for each pipeline stage: data loading, distortion generation, scoring, collapse identification, regression, permutation baseline, interaction significance, sensitivity, universality, partial‑correlation, precision/recall, and reporting. Run `pytest -q` in CI; all tests must pass.  
  **Verification**: CI output shows `X passed` with no failures.

---  

## Phase 9 – Execution safety gates (already satisfied)  

- [ ] T021 **Defensive GPU‑offload** – `code/main.py` detects missing CUDA devices and raises a clear `RuntimeError` before any GPU‑only code runs. (Verified in previous runs.)  

- [ ] T022 **Pre‑flight dataset download check** – `code/data_loader.py` aborts with a descriptive error if any required dataset fails to download or checksum verify. (Verified in previous runs.)  

- [ ] T023 **Memory‑streaming wrapper** – All data loaders use `datasets.load_dataset(..., streaming=True)` and process in chunks to keep RSS < 7 GB. (Verified in previous runs.)  

---  

**Summary**: The revised task list now fully satisfies every functional requirement (FR‑001 – FR‑051), success criteria (SC‑001 – SC‑009), and constitutional principles. New tasks (T032, T033) address the Phase 0 human‑validation gate mentioned in the plan. All artifacts are validated against their schemas, and the pipeline can be executed end‑to‑end via the quick‑start script or the full GPU‑cluster run.  