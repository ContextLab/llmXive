# Tasks: Extending "Mega-ASR" – Semantic Collapse Thresholds

**Inputs**: `spec.md`, `plan.md`, `data-model.md`, contract schemas, and reviewer feedback.

The list below follows the canonical checklist format `- [ ] T### [P?] [USx?] description …`. All file paths are relative to the project root. Tasks are ordered to respect data‑flow dependencies; each task includes concrete verification steps. This revision consolidates the prior task list into the smallest complete study and reopens the requirements rejected by the independent verifier (missing test scaffolding, truncated orchestration, missing `collapse_points.parquet`).

---

## Phase 1: Setup and first end‑to‑end analysis

- [ ] T001 [P] **Establish project layout, test scaffolding, and quickstart command** –   <!-- FAILED-IN-EXECUTION: code/run_quickstart.py exit=1 -->
  Create `code/`, `data/raw/`, `data/derived/`, `data/validation/`, `tests/unit/` (with `tests/__init__.py` and `tests/unit/__init__.py`) and `pytest.ini` / `conftest.py`. Add `code/config.py` with pinned constants (FR‑023): `SEED=42`, `SAMPLE_SIZE=50000`, SNR levels (9 values, −10 dB … 30 dB), RT60 levels (6 values, 0.1 s … 0.6 s), CCM threshold 0.5, SSS absolute threshold 0.5, WER multiplier 2.0, FDR 0.05, R² target 0.6. Write `docs/quickstart.md` documenting a runnable pilot command on 10 real clips producing `data/derived/stress_curves.parquet`, `data/derived/collapse_points.parquet`, and `data/derived/critical_vector.parquet`.  
  **Verification**: `pytest --collect-only` exits 0; `python -c "import code.config"` succeeds; the documented quickstart command runs end‑to‑end on real inputs and all three Parquet files contain ≥ 1 row each.

- [ ] T002 [US1] **Download and stratify the Voices‑in‑the‑Wild‑2M subset (FR‑001)** –  
  Implement `code/data_loader.py::load_viw_subset()` that streams the dataset via `datasets.load_dataset("voices-in-the-wild/2M", split="train", streaming=True)`, stratifies by `speaker_id` and `environment_id` (seed 42), selects ≥ 50 000 clean clips, writes `data/raw/viw_subset.parquet` and records SHA‑256 checksums in `data/raw/viw_checksums.txt`. The loader MUST fail loudly (raise) on any fetch or checksum failure — no synthetic/mock fallback. Also record the exact streaming/sampling rule (split, chunk size, row count) in the manifest.  
  **Verification**: `data/raw/viw_subset.parquet` has ≥ 50 000 rows with required metadata columns; `tests/unit/test_viw_loader.py` asserts stratification proportions within ±0.02 tolerance and that a failed fetch raises.

- [ ] T012 [US1] **Compute SSS embeddings for subset (FR‑003)** –  
  Using `sentence-transformers/all-MiniLM-L6-v2`, compute semantic similarity scores for each clean clip and store in `data/derived/clean_sss.parquet`. This provides the `ss_score` needed for downstream human‑validation AUC‑ROC.  
  **Verification**: `tests/unit/test_sss_embeddings.py` checks that the file exists, contains a `clip_id` column, and that all scores lie in [0, 1].

- [ ] T013 [US1] **Power analysis and verification (FR‑011, FR‑016, FR‑023, FR‑032, FR‑032‑VERIF)** –  
  Implement `code/power_analysis.py` reproducing the G*Power calculation (linear multiple regression, f² = 0.02, α = 0.05, power = 0.80 → N ≈ 395) and write `logs/power_analysis.txt`. After the final subset size from T002 is fixed, re‑run with actual N and log achieved power (≥ 0.99) to `logs/power_analysis_verif.txt`.  
  **Verification**: `tests/unit/test_power_analysis.py` asserts that both log files exist and contain the expected numeric values.

- [ ] T014 [US1] **Create human‑validation annotation tool** –  
  Provide `code/annotation_tool.py` with a simple CLI that ingests a CSV of clip IDs, presents audio via a Streamlit web UI, collects binary intelligibility labels from ≥ 3 raters per clip, enforces ≥ 2/3 agreement, and writes `data/validation/human_annotations.parquet`.  
  **Verification**: `tests/unit/test_annotation_tool.py` checks that the script creates the Parquet file with required columns and that disagreement handling works as specified.

- [ ] T015 [US1] **Human validation & AUC‑ROC computation (FR‑016, FR‑022)** –  
  Run `code/human_validation.py` to compute AUC‑ROC between `ss_score` (from T012) and the binary intelligibility label. Require AUC‑ROC ≥ 0.85; if fails for high‑reverb clips (RT60 > 0.5 s, ≥ 500 clips), switch to Montreal Forced Aligner phoneme‑edit distance and require Pearson r ≥ 0.6. Abort with `RuntimeError` if both fail.  
  **Verification**: `tests/unit/test_human_validation.py` asserts the AUC‑ROC threshold and the fallback path.

- [ ] T016 [US1] **Distortion engine implementation (FR‑002, FR‑024)** –  
  Implement `code/distortion_engine.py` using **pyroomacoustics** to apply the Cartesian product of 9 SNR × 6 RT60 levels (54 compound vectors) per clip. No in‑task scaling discretion; the task must process the full ≥ 50 k subset. If resources are insufficient, the task will abort and trigger amendment task T019.  
  **Verification**: `tests/unit/test_distortion_vectors.py` asserts exactly 54 vectors per clip; a log `logs/distortion_engine.log` records start/end timestamps.

- [ ] T017 [US1] **ASR inference & stress‑curve generation (FR‑003, FR‑017, FR‑026)** –  
  Run ASR inference on five small models (`whisper_tiny`, `whisper_base`, `distil_whisper`, `wav2vec2_small`, `whisper_medium`) with `device="cuda"` (auto‑offloaded to Kaggle GPU). Compute SSS via the embeddings from T012 and WER, log all provenance, and write `data/derived/stress_curves.parquet` conforming to `contracts/stress_curves.schema.yaml`. Also produce `data/derived/distortion_coverage_report.json`.  
  **Verification**: `tests/unit/test_stress_curves.py` validates schema, column ranges, and that each clip has entries for all 5 models × 54 vectors.

- [ ] T018 [P] **Validate stress‑curve artifact schema (FR‑034)** –  
  Execute `code/validate_artifacts.py` to validate `stress_curves.parquet` against `contracts/stress_curves.schema.yaml`; abort on any violation.  
  **Verification**: CI logs “Stress‑curve schema validation passed”.

- [ ] T019 [P] **Spec amendment request for resource constraints** –  
  If T016 aborts due to GPU budget, automatically open a PR proposing a formal spec amendment to relax FR‑001/FR‑002 or to allocate additional GPU resources.  
  **Verification**: Presence of a PR comment log `logs/spec_amendment_request.txt`.

- [ ] T020 [US1] **Baseline normalization, CCM, and deterministic collapse points (FR‑010, FR‑012, FR‑020, FR‑021, FR‑036)** –  
  Implement `code/collapse.py`: extract per‑clip baseline SSS/WER from the clean scenario; compute `norm_sss`, `norm_wer`, and `CCM = 0.7 × (1 − norm_sss) + 0.3 × norm_wer` into `data/derived/stress_curves_normalized.parquet`; apply deterministic algorithm (first step where CCM ≥ 0.5, linear interpolation per FR‑020, “None”/“Max Tested” when never crossed, early‑collapse flag from spline’s maximum negative derivative); compute the **Universal Collapse Intensity** at absolute SSS ≤ 0.5 (FR‑036); fit splines and store curve‑shape descriptors in `data/derived/curve_shape.parquet`. Write `data/derived/collapse_points.parquet` conforming to `contracts/collapse_points.schema.yaml`.  
  **Verification**: `tests/unit/test_collapse.py` checks collapse identification including edge cases; schema validation passes.

- [ ] T021 [US1] **Prepare regression input (FR‑005, regression_input.schema.yaml)** –  
  Build `data/derived/regression_input.parquet` containing `clip_id`, `model_name`, `snr`, `rt60`, `snr_sq`, `rt60_sq`, `snr_rt60`, `baseline_wer`, `transcript_perplexity`, and **`universal_collapse_intensity`** (the Universal Collapse Intensity from T020) as the target variable.  
  **Verification**: Schema validation against `contracts/regression_input.schema.yaml` (field `universal_collapse_intensity` added via task T033) and `tests/unit/test_regression_input.py`.

- [ ] T022 [US1] **Train hierarchical regression model (FR‑005, FR‑025)** –  
  Use `statsmodels.MixedLM` on the input from T021, 80/20 stratified split, 5‑fold CV, achieve out‑of‑sample R² ≥ 0.6 and MAE reported.  
  **Verification**: `tests/unit/test_regression_fit.py` asserts metrics meet thresholds.

- [ ] T023 [US1] **Permutation baseline & interaction significance (FR‑027, FR‑028)** –  
  Generate a permutation baseline by shuffling the target `universal_collapse_intensity`; require ΔR² ≥ 0.20. Compute interaction term significance, apply Benjamini‑Hochberg FDR ≤ 0.05, output `data/derived/permutation_baseline.json` and `data/derived/corrected_pvalues.json`.  
  **Verification**: `tests/unit/test_permutation.py` asserts ΔR² ≥ 0.20; `tests/unit/test_fdr_correction.py` checks FDR threshold.

- [ ] T024 [US1] **Partial‑correlation controlling for transcript difficulty (FR‑035)** –  
  Compute partial‑correlation between acoustic predictors and `universal_collapse_intensity` while controlling for transcript perplexity; store results in `data/derived/partial_correlation.json`.  
  **Verification**: `tests/unit/test_partial_corr.py` validates numeric output and that transcript difficulty is the control variable.

- [ ] T025 [US1] **Export critical interaction vector & out‑of‑sample R² (FR‑005, FR‑033, FR‑051)** –  
  From the fitted model, export `critical_vector.parquet` matching `contracts/critical_vector.schema.yaml` (coefficients, CIs, R², MAE, universal vector, similarity to others). Additionally, compute out‑of‑sample R² against the 500‑expert‑labeled collapse intensities (FR‑033) and store in `data/derived/expert_r2.json`.  
  **Verification**: `tests/unit/test_critical_vector.py` checks schema; `tests/unit/test_expert_r2.py` asserts R² is computed and recorded.

- [ ] T026 [P] **Update data‑model.md and designate canonical schemas (FR‑039)** –  
  Edit `data-model.md` to reference the **plural** schema files (`contracts/stress_curves.schema.yaml`, `contracts/collapse_points.schema.yaml`, `contracts/critical_vector.schema.yaml`) and to point the module layout to `code/` (`distortion_engine.py`, `collapse.py`, `train_regressor.py`). Commit the updated file.  
  **Verification**: `git diff --quiet data-model.md` passes; CI lints the file for consistency.

- [ ] T027 [P] **Revise dependency table to include all SC‑001 – SC‑009** –  
  Add missing rows for SC‑003 (FDR‑corrected interaction p‑values) and SC‑005 (sensitivity analysis CV) and ensure each task tags the corresponding SC IDs.  
  **Verification**: Table now contains a row for every SC‑001…SC‑009; CI checks the table format.

- [ ] T028 [US3] **Model‑agnostic SHAP analysis of interaction (US‑3)** –  
  Run SHAP on the final regression model to quantify feature importance and visualize the interaction effect between SNR and RT60. Store plots in `figures/shap_interaction.png` and summary JSON `data/derived/shap_summary.json`.  
  **Verification**: `tests/unit/test_shap.py` asserts files exist and that SHAP values for the interaction term are non‑zero.

- [ ] T029 [US1] **Realism validation against DNS‑Challenge (FR‑018)** –  
  Fetch the DNS‑Challenge dataset, compute Log‑Mel Spectral Distance (LMSD) between synthetic distortions and matched real clips (±1 dB / ±0.1 s), record results in `data/derived/realism_validation.parquet`, and require mean LMSD ≤ 0.15. Document the validation procedure and limitation note in the final report.  
  **Verification**: `tests/unit/test_realism_dns.py` checks the parquet file exists, LMSD values are numeric, and mean ≤ 0.15.

- [ ] T030 [P] **Record wall‑time for pilot and full runs (SC‑004)** –  
  Instrument the pipeline (T016‑T025) to log start/end timestamps to `logs/run_timing.json`. Verify pilot run ≤ 48 h and full run ≤ 72 h on the GPU cluster. Abort if limits exceeded.  
  **Verification**: `tests/unit/test_timing.py` parses the JSON and asserts the limits.

- [ ] T031 [P] **Create report compliance check script (FR‑007)** –  
  Implement `code/check_report_compliance.py` that parses `docs/final_report.md`, ensures every required metric is present, and flags any prohibited causal verbs (“causes”, “leads to”, “drives”).  
  **Verification**: `tests/unit/test_report_compliance.py` runs the script on a sample report and expects zero violations.

- [ ] T032 [P] **Canonicalize schema references and SSoT (FR‑038, FR‑039)** –  
  Remove singular schema files (`contracts/stress_curve.schema.yaml`, `contracts/collapse_point.schema.yaml`) from the repository; ensure only plural versions remain. Update all task descriptions, validation scripts, and data‑model.md to reference the plural schemas. Add a short note in `data-model.md` that the source‑of‑truth for schema definitions is now the plural files and that the pipeline code resides under `code/`.  
  **Verification**: CI checks that singular schema files are absent, that all import paths point to plural schemas, and that `data-model.md` contains the updated SSoT statement.

- [ ] T033 [US1] **Align regression target to Universal Collapse Intensity (FR‑005)** –  
  Modify `code/prepare_regression_input.py` to set `target = universal_collapse_intensity` (from T020) instead of `inflection_step`. Update `contracts/regression_input.schema.yaml` to replace `inflection_step` with `universal_collapse_intensity` (type string, same format as in `collapse_point.schema.yaml`). Adjust downstream tasks (T022‑T025) to consume the new target field.  
  **Verification**: `tests/unit/test_regression_input.py` validates the new field; schema validation passes; regression training scripts reference the correct column name.

- [ ] T034 [US1] **Implement robust annotation UI and import contract** –  
  Build `code/annotation_ui.py` using Streamlit that loads a CSV of clip IDs, streams audio from `data/raw/viw_subset.parquet`, records binary intelligibility labels, and writes `data/validation/human_annotations.parquet` following the contract `contracts/human_annotations.schema.yaml` (new contract to be added). Provide a CLI wrapper `code/run_annotation.sh` for batch execution.  
  **Verification**: `tests/unit/test_annotation_ui.py` checks that the UI script produces a Parquet file adhering to the contract and that missing input raises an error.

- [ ] T035 [US1] **Stratification tolerance verification (FR‑001)** –  
  Extend `tests/unit/test_viw_loader.py` to compute the proportion of each `speaker_id` and `environment_id` stratum in the sampled subset and assert that the absolute deviation from the source distribution is ≤ 0.02 for both dimensions.  
  **Verification**: Test passes only when the tolerance condition holds.

- [ ] T011 **Final report and reproducibility check (FR‑007, SC‑001–SC‑009)** –  
  `code/report_generator.py` creates `docs/final_report.md` with figures and tables plotted directly from the Parquet artifacts (stress curves, collapse‑point histograms, coefficient plots, SHAP visualisation, timing summary, realism validation, etc.). Every result statement uses associational phrasing only (FR‑007). Re‑run the documented workflow from `quickstart.md` inputs, confirm `pytest -q` passes in full, and document the paper‑stage handoff.  
  **Verification**: A CI step runs `code/check_report_compliance.py` (produced by T031); all checks pass; the report includes all required metrics.

## Dependency Table

| Requirement | Task(s) | Order |
|---|---|---|
| FR‑001, FR‑023, FR‑026 | T001 → T002 | T001 → T002 |
| FR‑011, FR‑016, FR‑022, FR‑032, FR‑032‑VERIF | T013 | after T002 |
| FR‑002, FR‑003, FR‑017, FR‑024 | T016 → T017 | after T002 |
| FR‑010, FR‑012, FR‑020, FR‑021, FR‑036 | T020 | after T004/T017 |
| FR‑033, SC‑009 | T025 | after T023 |
| FR‑005, FR‑008, FR‑013, FR‑025, FR‑027, FR‑028, FR‑029, FR‑035 | T022 → T023 → T024 → T025 | after T020 |
| FR‑006, FR‑051, SC‑002, SC‑005 | T028 | after T025 |
| FR‑018 (real DNS‑Challenge) | T029 | after T004 |
| SC‑004 (pilot/full timing) | T030 | after T025 |
| SC‑001, SC‑003, SC‑006, SC‑007, SC‑008 | T031, T025, etc. | throughout |
| FR‑007, SC‑001–SC‑009 | T011 | after T025 |