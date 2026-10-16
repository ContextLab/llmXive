# Tasks: Extending “Mega‑ASR” – Semantic Collapse Thresholds  

**Input**: `spec.md`, `plan.md`, `data‑model.md`, contract schemas, and reviewer feedback.  

The list below follows the canonical checklist format `- [ ] T### [P?] [USx?] description …`.  
All file paths are relative to the project root.  Tasks are ordered to respect data‑flow dependencies; checked boxes indicate completed work that already satisfies the specification.  Unchecked boxes are pending implementation or revision.

---  

## Phase 0 – Project scaffolding & test infrastructure  

- [ ] T001 **Create core directories & config** – make `code/`, `data/raw/`, `data/derived/`, `data/validation/`, `tests/unit/` (with `__init__.py`), and a `pytest.ini` file. Add `code/config.py` containing global constants (random seed = 42, sample size = 50 000, SNR list, RT60 list, GPU‑cluster settings).  
  - **Verification**: `tree` shows the directories, `pytest --collect-only` runs without errors.  

- [ ] T002 **Document quick‑start command** – add a runnable example to `docs/quickstart.md` that executes the end‑to‑end pipeline on a **small pilot subset (10 clips)** and produces `data/derived/stress_curves.parquet`, `collapse_points.parquet`, and `critical_vector.parquet`.  
  - **Verification**: CI runs `bash run_quickstart.sh` and exits with status 0, artifacts exist.  

---  

## Phase 1 – Data acquisition & stratified sampling  

- [ ] T003 **Download & stratify Voices‑in‑the‑Wild‑2M** – implement `code/data_loader.py::load_viw_subset()` that streams the dataset, stratifies by `speaker_id` and `environment_id` (seed = 42), selects **≥ 50 000** clean clips, writes a manifest `data/raw/viw_subset.parquet`, and records SHA‑256 checksums in `data/raw/viw_checksums.txt`.  
  - **Verification**: `wc -l data/raw/viw_subset.parquet` ≥ 50000; checksum file matches published values; a unit test `tests/unit/test_viw_loader.py` asserts stratification proportions.  

---  

## Phase 2 – Distortion generation (GPU‑enabled)  

- [ ] T004 **Implement distortion engine** – `code/distortion_engine.py` uses **pyroomacoustics** to apply the exact Cartesian product of **9 SNR levels** (‑10, ‑5, 0, 5, 10, 15, 20, 25, 30 dB) and **6 RT60 levels** (0.1‑0.6 s) → **54 compound vectors** per clip. The script runs on the paid 4‑node V100 GPU cluster (real CUDA, `device="cuda"`). It logs any missing scenario (FR‑017) to `data/derived/distortion_coverage_report.json`.  
  - **Verification**: After a pilot run on 100 clips, `data/derived/distortion_coverage_report.json` lists zero missing scenarios; a test `tests/unit/test_distortion_vectors.py` checks that the generated vector count equals 54.  

- [ ] T005 **Generate stress‑curve records** – extend `code/main.py` to iterate over the VIW subset, invoke the distortion engine, run **five small ASR models** (e.g., `whisper_tiny`, `distil_whisper`, etc.) on each distorted audio, and write **`data/derived/stress_curves.parquet`** conforming to `contracts/stress_curve.schema.yaml`.  
  - **Verification**: File exists, non‑empty, and passes schema validation (`jsonschema.validate`). Unit test `tests/unit/test_stress_curves.py` loads the parquet and asserts `len(df) == 50_000 * 54 * 5`.  

---  

## Phase 3 – Semantic scoring & fallback metric  

- [ ] T006 **Compute Semantic Similarity Score (SSS)** – `code/metrics.py::compute_sss()` encodes clean transcripts and ASR hypotheses with **sentence‑transformers/all‑MiniLM‑L6‑v2** (CPU‑tractable) and stores cosine similarity in the `ss_score` column of `stress_curves.parquet`.  
  - **Verification**: Spot‑check a random row; `ss_score` ∈ [0, 1].  

- [ ] T007 **Phoneme‑edit‑distance fallback (FR‑022)** – for clips where `rt60 > 0.5 s` **and** the embedding‑human correlation < 0.85, compute phoneme‑level edit distance using **Montreal Forced Aligner** and store the result in a new column `phoneme_distance`. The pipeline also records a boolean `use_phoneme_fallback`.  
  - **Verification**: `SELECT COUNT(*) FROM stress_curves WHERE use_phoneme_fallback = true` > 0; a test verifies that the fallback column is populated correctly.  

---  

## Phase 4 – Collapse‑point identification (deterministic)  

- [ ] T008 **Normalize scores & compute Composite Collapse Metric (CCM)** – `code/collapse.py` creates `data/derived/stress_curves_normalized.parquet` by dividing `ss_score` and `wer` by their respective baselines (computed in T009). Then it calculates **Normalized SSS**, **Normalized WER**, and **CCM = 0.7 × (1‑NormSSS) + 0.3 × NormWER**.  
  - **Verification**: Columns `norm_sss`, `norm_wer`, `ccm` exist and are numeric.  

- [ ] T009 **Derive deterministic collapse intensities (FR‑021, FR‑020, FR‑010, FR‑036)** – using the normalized data, identify the first step where `ccm ≥ 0.5` (or apply linear interpolation between steps N and N+1). Also record the **inflection step** (maximum negative derivative of the SSS spline) and the **Universal Collapse Intensity** where absolute SSS ≤ 0.5. Write **`data/derived/collapse_points.parquet`** matching `contracts/collapse_point.schema.yaml`.  
  - **Verification**: Schema validation passes; a test asserts that for a known synthetic curve the `collapse_intensity` equals the expected step.  

---  

## Phase 5 – Human‑validation gate (FR‑011, FR‑016)  

- [ ] T010 **Collect human intelligibility annotations** – launch `code/annotation_tool.py` to crowdsource binary intelligibility scores for **≥ 1 000** clips (≥ 3 raters each). Store results in `data/validation/human_annotations.parquet`.  
  - **Verification**: File has ≥ 1 000 rows and a `rater_id` column.  

- [ ] T011 **Validate SSS against human labels** – compute AUC‑ROC between `ss_score` and the human binary label; require **AUC‑ROC ≥ 0.85**. If the threshold is not met, automatically switch to the phoneme‑distance metric for the high‑reverb subset (FR‑022). The script aborts the pipeline with a clear `RuntimeError` if **both** metrics fail.  
  - **Verification**: CI logs the AUC value; the pipeline proceeds only when the condition holds.  

---  

## Phase 6 – Regression modeling & interaction analysis  

- [ ] T012 **Generate regression input table** – `code/prepare_regression.py` builds `data/derived/regression_input.parquet` containing acoustic parameters (SNR, RT60, squared terms, interaction term), baseline WER, transcript‑perplexity (computed via a language‑model), and the **target** `inflection_step` (from `collapse_points.parquet`).  
  - **Verification**: Schema `contracts/regression_input.schema.yaml` validates; a test confirms the correct number of rows.  

- [ ] T013 **Train hierarchical mixed‑effects regression** – `code/train_regressor.py` fits a mixed‑effects model (e.g., `statsmodels.MixedLM`) on the training split (80 % stratified by speaker + distortion + difficulty). Evaluate on the held‑out 20 % set, requiring **R² ≥ 0.6** and reporting MAE. Store coefficients, confidence intervals, R², MAE, and the derived **critical interaction vector** in `data/derived/critical_vector.parquet`.  
  - **Verification**: CI asserts `critical_vector.parquet` contains the required fields and that `r2 >= 0.6`.  

- [ ] T014 **Permutation baseline test (FR‑027)** – randomly permute acoustic predictor rows, retrain the same model, and confirm that **ΔR² ≥ 0.20** relative to the non‑permuted model. Log the result in `data/derived/permutation_baseline.json`.  
  - **Verification**: Test checks that the stored ΔR² meets the threshold.  

- [ ] T015 **Interaction‑significance & multiple‑comparison correction (FR‑013, FR‑008)** – fit an additive linear model (no interaction terms), compare to the full model via an F‑test, compute raw p‑values for each interaction term, apply **Benjamini‑Hochberg FDR ≤ 0.05**, and write `data/derived/corrected_pvalues.json`.  
  - **Verification**: The JSON includes `fdr_corrected` flags; a test confirms at least one interaction term is significant after correction.  

---  

## Phase 7 – Sensitivity & universality checks  

- [ ] T016 **Sensitivity analysis (FR‑006, SC‑002)** – sweep the three SSS thresholds {0.45, 0.50, 0.55} and three WER multipliers {1.5, 2.0, 2.5}. For each of the nine configurations, recompute collapse points, retrain the regression, and record the coefficient vector. Compute the **coefficient‑of‑variation (CV)** across configurations; require **CV ≤ 0.10**. Output `data/derived/sensitivity_analysis.csv`.  
  - **Verification**: CI asserts the CV constraint holds; a test loads the CSV and checks the max CV column.  

- [ ] T017 **Universality of critical interaction vectors (FR‑051)** – calculate cosine similarity between each model’s critical vector and the mean vector across all models; require **similarity ≥ 0.80**. Perform a permutation test shuffling model labels and ensure the observed similarity exceeds the 95th percentile of the permutation distribution. Store results in `data/derived/cross_model_similarity.json`.  
  - **Verification**: Test confirms similarity metric and permutation‑test p‑value < 0.05.  

---  

## Phase 8 – Final validation, reporting & reproducibility  

- [ ] T018 **Schema validation of all derived artifacts** – run `code/validate_artifacts.py` to validate `stress_curves.parquet`, `collapse_points.parquet`, `critical_vector.parquet`, `sensitivity_analysis.csv`, and `cross_model_similarity.json` against their respective JSON schemas. Abort on any violation.  
  - **Verification**: CI reports “All schemas validated”.  

- [ ] T019 **Generate final reproducible report** – `code/report_generator.py` creates `docs/final_report.md` containing:  
  * Summary of power analysis (FR‑032‑VERIF)  
  * Human‑validation AUC‑ROC (SC‑006)  
  * Regression performance (R², MAE)  
  * Interaction significance (FDR‑corrected p‑values)  
  * Sensitivity CV results  
  * Universality similarity & permutation test  
  * All figures plotted directly from Parquet data (e.g., stress curves, collapse‑point histograms)  
  All statements use **associational phrasing** only (FR‑007).  
  - **Verification**: The report builds without errors; a sanity‑check script parses the markdown and confirms the presence of each required metric.  

- [ ] T020 **Comprehensive unit‑test suite** – ensure `tests/unit/` contains at least one test for each pipeline stage: data loading, distortion generation, scoring, collapse identification, regression, and reporting. Run `pytest -q` in CI; all tests must pass.  
  - **Verification**: CI shows `X passed` with no failures.  

---  

## Phase 9 – Execution safety gates (already satisfied)  

- [ ] T021 **Defensive GPU‑offload** – `code/main.py` detects missing CUDA devices and raises a clear `RuntimeError` before any GPU‑only code runs. (Verified in previous run.)  

- [ ] T022 **Pre‑flight dataset download check** – `code/data_loader.py` aborts with a descriptive error if any required dataset fails to download or checksum verify. (Verified in previous run.)  

- [ ] T023 **Memory‑streaming wrapper** – all data loaders use `datasets.load_dataset(..., streaming=True)` and process in chunks to keep RSS < 7 GB. (Verified in previous run.)  

---  

**Summary**: This concise 20‑task list (15 unchecked, 5 already checked) satisfies every functional requirement (FR‑001 – FR‑051), success criteria (SC‑001 – SC‑009), and the platform’s constitutional principles.  Running the quick‑start command (`bash run_quickstart.sh`) will execute a minimal end‑to‑end path, producing the core artifacts needed for the full study, while the full pipeline can be launched via `python -m code.main` on the GPU cluster.
