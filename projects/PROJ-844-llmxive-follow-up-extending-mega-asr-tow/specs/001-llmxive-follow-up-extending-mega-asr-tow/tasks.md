# Tasks: Extending "Mega-ASR" – Semantic Collapse Thresholds

**Inputs**: `spec.md`, `plan.md`, `data-model.md`, contract schemas, and reviewer feedback.

The list below follows the canonical checklist format `- [ ] T### [P?] [USx?] description …`. All file paths are relative to the project root. Tasks are ordered to respect data-flow dependencies; each task includes concrete verification steps. This revision consolidates the prior task list into the smallest complete study and reopens the requirements rejected by the independent verifier (missing test scaffolding, truncated orchestration, missing `collapse_points.parquet`).

---

## Phase 1: Setup and first end-to-end analysis

- [ ] T001 [P] **Establish project layout, test scaffolding, and quickstart command** –
  Create `code/`, `data/raw/`, `data/derived/`, `data/validation/`, `tests/unit/` (with `tests/__init__.py` and `tests/unit/__init__.py` — previously missing per verifier) and `pytest.ini` / `conftest.py`. Add `code/config.py` with pinned constants (FR-023): `SEED=42`, `SAMPLE_SIZE=50000`, SNR levels (9 values, −10 dB … 30 dB), RT60 levels (6 values, 0.1 s … 0.6 s), CCM threshold 0.5, SSS absolute threshold 0.5, WER multiplier 2.0, FDR 0.05, R² target 0.6. Write `docs/quickstart.md` documenting a runnable pilot command on 10 real clips producing `data/derived/stress_curves.parquet`, `data/derived/collapse_points.parquet`, and `data/derived/critical_vector.parquet`.
  **Verification**: `pytest --collect-only` exits 0; `python -c "import code.config"` succeeds; the documented quickstart command runs end-to-end on real inputs and all three Parquet files contain ≥ 1 row each.

- [ ] T002 [US1] **Download and stratify the Voices-in-the-Wild-2M subset (FR-001)** –
  Implement `code/data_loader.py::load_viw_subset()` that streams the dataset via `datasets.load_dataset("voices-in-the-wild/2M", split=..., streaming=True)`, stratifies by `speaker_id` and `environment_id` (seed 42), selects ≥ 50 000 clean clips, writes `data/raw/viw_subset.parquet` and records SHA-256 checksums in `data/raw/viw_checksums.txt`. The loader MUST fail loudly (raise) on any fetch or checksum failure — no synthetic/mock fallback. Also record the exact streaming/sampling rule (split, chunk size, row count) in the manifest.
  **Verification**: `data/raw/viw_subset.parquet` has ≥ 50 000 rows with required metadata columns; `tests/unit/test_viw_loader.py` asserts stratification proportions and that a failed fetch raises.

- [ ] T003 [US1] **Power analysis and human-validation gate (FR-011, FR-016, FR-023, FR-032, FR-032-VERIF)** –
  Implement `code/power_analysis.py` reproducing the G*Power calculation (linear multiple regression, f² = 0.02, α = 0.05, power = 0.80 → N ≈ 395) in `logs/power_analysis.txt`; after the final subset size from T002 is fixed, re-run with actual N and log achieved power (≥ 0.99) in `logs/power_analysis_verif.txt`. Implement `code/annotation_tool.py` plus `code/human_validation.py` to collect binary intelligibility labels (≥ 3 raters per clip, ≥ 2/3 agreement) for ≥ 1 000 stratified clips into `data/validation/human_annotations.parquet`, compute AUC-ROC between `ss_score` and the binary label, and require AUC-ROC ≥ 0.85. If SSS fails for high-reverb clips (RT60 > 0.5 s, ≥ 500 clips stratified by speaker), switch to Montreal Forced Aligner phoneme-edit distance (FR-022) and require Pearson r ≥ 0.6; if both fail, abort with `RuntimeError` (FR-016).
  **Verification**: `tests/unit/test_power_analysis.py` and `tests/unit/test_human_validation.py` assert the logged values; a test asserts the abort path fires on a low-AUC fixture.

- [ ] T004 [US1] **Distortion engine, ASR inference, and stress-curve generation (FR-002, FR-017, FR-024, FR-026)** –
  Implement `code/distortion_engine.py` using **pyroomacoustics** to apply the Cartesian product of 9 SNR × 6 RT60 levels (54 compound vectors) per clip, and complete the full orchestration in `code/main.py` (previously truncated per verifier) with CLI arguments for subset size, shard index, and output paths. ASR inference over five small models (e.g., `whisper_tiny`, `distil_whisper`) is real GPU work: run with `device="cuda"` on the GPU runner (Kaggle/offload); scale to a few-hundred-clip pilot on the free GPU budget if the full 50 k × 54 × 5 run exceeds it, stating the sample size honestly. Compute SSS via `sentence-transformers/all-MiniLM-L6-v2` (FR-003) and WER, log all metric provenance (FR-026), log missing scenarios (FR-017) to `data/derived/distortion_coverage_report.json`, and write `data/derived/stress_curves.parquet` conforming to `contracts/stress_curve.schema.yaml`.
  **Verification**: Pilot run produces real rows; `tests/unit/test_distortion_vectors.py` asserts exactly 54 vectors per clip; schema validation passes; `tests/unit/test_stress_curves.py` asserts required columns and `ss_score ∈ [0, 1]`.

- [ ] T005 [US2] **Baseline normalization, CCM, and deterministic collapse points (FR-010, FR-012, FR-020, FR-021, FR-036)** –
  Implement `code/collapse.py`: extract per-clip baseline SSS/WER from the clean scenario; compute `norm_sss`, `norm_wer`, and `CCM = 0.7 × (1 − norm_sss) + 0.3 × norm_wer` into `data/derived/stress_curves_normalized.parquet`; apply the deterministic algorithm (first step where CCM ≥ 0.5, linear interpolation per FR-020, "None"/"Max Tested" when never crossed, early-collapse flag from the spline's maximum negative derivative); compute the **Universal Collapse Intensity** at absolute SSS ≤ 0.5 (FR-036); fit splines and store curve-shape descriptors in `data/derived/curve_shape.parquet` (FR-012). Write the previously missing **`data/derived/collapse_points.parquet`** conforming to `contracts/collapse_point.schema.yaml`. Handle edge cases: smoothing/hysteresis for oscillating SSS; empty ASR hypotheses map to collapse at lowest tested intensity.
  **Verification**: `data/derived/collapse_points.parquet` exists, is non-empty, and validates against the schema (verifier rejection resolved); `tests/unit/test_collapse.py` verifies collapse identification on a synthetic monotone curve including the "never crossed" case; `tests/unit/test_ccm.py` verifies CCM arithmetic on hand-computed rows.

## Phase 2: Complete the study and validate its evidence

- [ ] T006 [US3] **Expert-annotated validation subset and precision/recall (FR-033, SC-009)** –
  Randomly select 500 representative stress curves, obtain expert-labeled true collapse intensities, and store them in `data/derived/manual_collapse.parquet` (schema mirroring `collapse_points.parquet` plus `expert_label`). Compare deterministic collapse intensities against these labels; compute precision and recall (both ≥ 0.90) into `data/derived/collapse_pr_metrics.json`.
  **Verification**: File contains 500 rows with `expert_label`; `tests/unit/test_collapse_pr.py` validates the metric computation.

- [ ] T007 [US3] **Hierarchical regression, permutation baseline, and interaction significance (FR-005, FR-008, FR-013, FR-025, FR-027, FR-028, FR-029)** –
  Implement `code/prepare_regression.py` building `data/derived/regression_input.parquet` (SNR, RT60, SNR², RT60², SNR×RT60, baseline WER, transcript perplexity; target `inflection_step`), validated against `contracts/regression_input.schema.yaml`. Implement `code/train_regressor.py`: mixed-effects regression (`statsmodels.MixedLM`), 80/20 stratified split by speaker + distortion + difficulty, 5-fold CV, held-out R² ≥ 0.6 with MAE reported; permutation baseline requiring ΔR² ≥ 0.20 (FR-027) into `data/derived/permutation_baseline.json`; additive-vs-interaction model comparison with Benjamini-Hochberg FDR ≤ 0.05 (FR-013, FR-008) into `data/derived/corrected_pvalues.json`; partial-correlation controlling for transcript difficulty (FR-035) into `data/derived/partial_correlation.json`. Write `data/derived/critical_vector.parquet` conforming to `contracts/critical_vector.schema.yaml` with coefficients, 95% CIs, R², MAE.
  **Verification**: Schema validation passes; `tests/unit/test_permutation.py` asserts ΔR² ≥ 0.20; `tests/unit/test_partial_corr.py` asserts numeric unique-variance values; CI asserts `r2 >= 0.6` and CI columns present.

- [ ] T008 [US3] **Sensitivity analysis and universality assessment (FR-006, SC-002, FR-051)** –
  Sweep SSS thresholds {0.45, 0.50, 0.55} × WER multipliers {1.5, 2.0, 2.5}; for each of the nine settings recompute collapse points and refit the regression; record coefficient vectors and their coefficient of variation (CV ≤ 0.10) in `data/derived/sensitivity_analysis.csv`. Assess universality: cosine similarity between each model's critical interaction vector (derived from the Universal Collapse Intensity, FR-036) and the cross-model mean, requiring ≥ 0.80, plus a model-label permutation test where observed similarity must exceed the 95th percentile; store in `data/derived/cross_model_similarity.json`.
  **Verification**: `tests/unit/test_sensitivity.py` asserts max CV ≤ 0.10; `tests/unit/test_universality.py` asserts similarity ≥ 0.80 and permutation p < 0.05.

- [ ] T009 [P] **Realism validation, limited proxy (FR-018 as amended by plan)** –
  Because DNS-Challenge is not a verified source, implement the documented proxy: select ≥ 50 high-RT60 real clips from Voices-in-the-Wild-2M, compute Log-Mel Spectral Distance (window 25 ms, hop 10 ms, 128 bins) between synthetic distortions and matched real clips (±1 dB / ±0.1 s), record results in `data/derived/realism_validation.parquet`, and explicitly document the FR-018 limitation in the final report.
  **Verification**: `tests/unit/test_realism.py` asserts the file exists with numeric LMSD values and the limitation note is recorded.

- [ ] T010 **Full-run execution and artifact schema validation (FR-030, FR-031, FR-034)** –
  Run the complete pipeline end-to-end on the full stratified subset (GPU-offloaded for distortion/ASR; CPU for all statistics), then run `code/validate_artifacts.py` validating `stress_curves.parquet`, `collapse_points.parquet`, `critical_vector.parquet`, `curve_shape.parquet`, and all JSON reports against their schemas; abort on any violation.
  **Verification**: CI logs "All schemas validated"; all derived artifacts are non-empty and trace to logged computation steps (FR-026).

## Phase 3: Reproducible results and paper handoff

- [ ] T011 **Final report and reproducibility check (FR-007, SC-001–SC-009)** –
  `code/report_generator.py` creates `docs/final_report.md` with figures and tables plotted directly from the Parquet artifacts (stress curves, collapse-point histograms, coefficient plots), reporting: power-analysis verification, human-validation AUC-ROC, regression R²/MAE, FDR-corrected interaction p-values, sensitivity CV, universality similarity and permutation test, precision/recall, and the FR-018 limitation. Every result statement must use associational phrasing ("is associated with") and must not contain "causes"/"leads to"/"drives" (FR-007), with a recorded compliance sign-off. Re-run the documented workflow from `quickstart.md` inputs, confirm `pytest -q` passes in full, and document the paper-stage handoff (layout, PDF compilation, publication belong to the paper pipeline).
  **Verification**: A check script parses the markdown for each required metric and forbidden causal verbs; CI runs the full test suite with zero failures.

---

## Dependencies and requirement coverage

| Requirement | Task(s) | Order |
|---|---|---|
| FR-001, FR-023, FR-026 | T002, T001 | T001 → T002 |
| FR-011, FR-016, FR-022, FR-032, FR-032-VERIF | T003 | after T002 |
| FR-002, FR-003, FR-017, FR-024 | T004 | after T002 |
| FR-010, FR-012, FR-020, FR-021, FR-036 | T005 | after T004 |
| FR-033, SC-009 | T006 | after T005 |
| FR-005, FR-008, FR-013, FR-025, FR-027, FR-028, FR-029, FR-035 | T007 | after T005 |
| FR-006, FR-051, SC-002, SC-005 | T008 | after T007 |
| FR-018 (proxy) | T009 | after T004 (parallel) |
| FR-030, FR-031, FR-034 | T010 | after T005–T009 |
| FR-007, SC-001–SC-009 | T011 | after T010 |

## Revision behavior

- Reopened requirements from verifier rejections: test scaffolding (prior T008 → now T001), full orchestration + `stress_curves.parquet` (prior T015 → now T004), `collapse_points.parquet` (prior T022 → now T005).
- Consolidated the prior 33-task list into 11 substantive tasks by grouping related pipeline stages; every functional requirement and success criterion is preserved in the mapping above.
- Preserved constraints: no synthetic data fallbacks (loaders fail loudly), real GPU work for ASR/distortion with honest scaling, CPU-first statistics, associational framing, and schema-validated artifacts.
