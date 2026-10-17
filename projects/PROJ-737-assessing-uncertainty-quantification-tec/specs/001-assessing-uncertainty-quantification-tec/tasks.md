# Tasks: Assessing Uncertainty Quantification Techniques for Materials Property Predictions

**Inputs**: `specs/001-assessing-uncertainty-quantification-tec/spec.md`, `plan.md`, `data-model.md`, `contracts/`

The checklist below implements the smallest complete, reproducible study that satisfies all functional, non‑functional, and success‑criteria requirements.  Tasks are ordered to respect data flow and to address the reviewer‑identified gaps (explicit naming of the four UQ methods, correct dataset sources, pipeline stability, versioning discipline, and baseline alignment for sensitivity analysis).

---

## Phase 1 – Setup and first end‑to‑end analysis  

**Goal**: Verify that the pipeline runs on a tiny real‑data subset before scaling up.

- [ ] T001 [US1] **Document runnable command and verify per‑sample schema**  
  *Create* `specs/001-assessing-uncertainty-quantification-tec/quickstart.md` containing the command `python -m code.main --thin`.  The document must describe the four UQ methods (GPR, MC‑Dropout, Deep Ensemble, Split‑Conformal), the 2000‑sample training cap, the deterministic “first‑N rows, seed 42” sampling rule, the paired Wilcoxon test rationale, and the Formation‑Energy proxy note.  
  *Verify* that `specs/001-assessing-uncertainty-quantification-tec/contracts/per_sample_errors.schema.yaml` lists exactly the columns `sample_id, dataset, method, prediction, lower_bound, upper_bound, ground_truth, abs_error`.  
  *Path*: `specs/001-assessing-uncertainty-quantification-tec/quickstart.md`, `specs/001-assessing-uncertainty-quantification-tec/contracts/per_sample_errors.schema.yaml`  
  *Check*: a tiny test script loads the schema YAML, asserts the column set, and exits 0.

- [ ] T002 [US1] **Download three real materials datasets via verified URLs**  
  *Implement* `code/download.py` that uses the HuggingFace `datasets` library (or `urllib`) to fetch the exact CSVs:  

  1. **Band Gap** – OQMD CSV from `https://huggingface.co/datasets/oqmd/band_gap/resolve/main/band_gap.csv` → `data/raw/band_gap.csv`  
  2. **Formation Energy** – OQMD CSV from `https://huggingface.co/datasets/oqmd/formation_energy/resolve/main/formation_energy.csv` → `data/raw/formation_energy.csv`  
  3. **Thermal Conductivity** – AFLOW CSV from `https://huggingface.co/datasets/aflow/thermal_conductivity/resolve/main/thermal_conductivity.csv` → `data/raw/thermal_conductivity.csv`  

  *Requirements*: no `try/except` fallback; any fetch error must raise and abort the run. After each download compute a SHA‑256 checksum and write `data/raw/<dataset_id>_metadata.json` containing `dataset_id`, `source_url`, `property_name`, `n_samples_original`, `n_samples_used`, `checksum`.  
  *Cap* each raw file at **5 000 rows** deterministically (`seed=42`, `itertools.islice`).  
  *Verification*: `code/tests/test_download.py` loads each metadata JSON, asserts the CSV exists, checksum matches, `n_samples_used ≤ 5000`, the `source_url` matches the verified URL above, and that the CSV contains a `composition` column and a numeric target with ≥ 100 non‑null rows.  
  *Path*: `code/download.py`, `data/raw/*.csv`, `data/raw/*_metadata.json`, `code/tests/test_download.py`

- [ ] T003 [US1] **Featurize, split, and run a thin end‑to‑end analysis on a 100‑sample subset**   <!-- FAILED-IN-EXECUTION: code/main.py exit=2 --> <!-- FAILED-IN-EXECUTION: code/main.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/main.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/main.py exit=1 -->
  *Implement* `code/featurize.py` to convert the `composition` column to feature vectors with `matminer` (fallback to elemental‑fraction vectors via `pymatgen` if any featurizer fails).  Write the processed files to `data/processed/<dataset_id>.csv`.  
  *Perform* a stratified 70 %/15 %/15 % train/val/test split by target‑property range; save split indices to `data/processed/<dataset_id>_split.json`.  
  *Implement* the four UQ method modules in `code/models/`:  

  - `gpr.py` – scikit‑learn Gaussian Process Regression (≤ 2000 training points)  
  - `mc_dropout.py` – PyTorch MLP ≤ 2 M parameters, 50 stochastic forward passes, `device="cpu"`  
  - `deep_ensemble.py` – ensemble of **3** MLPs (distinct seeds)  
  - `conformal.py` – XGBoost regressor + split‑conformal calibration  

  Each module must expose a `run(train_data, test_data) → DataFrame` with columns `prediction, lower_bound, upper_bound`.  
  *Run* the thin pipeline on the first 100 rows of each capped dataset (use the `--thin` flag).  Write per‑sample rows to `data/results/per_sample_errors.csv` (exact schema) and a pipeline log `data/results/pipeline_run.json` conforming to `contracts/pipeline.schema.yaml`.  
  *Verification*: `code/tests/test_thin_pipeline.py` validates `per_sample_errors.csv` against the per‑sample schema, validates `pipeline_run.json` against the pipeline schema, and asserts that all four methods produced rows for every dataset subset.  The command `python -m code.main --thin` must exit 0.  
  *Path*: `code/featurize.py`, `code/models/*.py`, `data/processed/*.csv`, `data/results/per_sample_errors.csv`, `data/results/pipeline_run.json`, `code/tests/test_thin_pipeline.py`

---

## Phase 2 – Complete the study and validate its evidence  

**Goal**: Run the full pipeline on all capped datasets, compute metrics, perform statistical testing, and produce sensitivity analyses.

- [ ] T004 [US1] **Full‑scale pipeline on all three capped datasets (uniform 2000‑sample training cap)**  
  *Extend* `code/pipeline.py` to orchestrate: download → featurize → split → train all four UQ methods on each dataset (≤ 5000 rows total, ≤ 2000 training examples per method).  Enforce **≥ 200 test samples** per dataset (power‑analysis requirement).  
  *Persist* per‑sample predictions for every dataset × method in a single `data/results/per_sample_errors.csv` (schema‑compliant).  
  *Write* the UQMethod registry `data/results/uq_methods.csv` (`method_id, baseline_model, hyperparams, n_iterations, status, error_msg`).  
  *Write* the pipeline execution log `data/results/pipeline_log.csv` (conforms to `contracts/pipeline.schema.yaml`).  
  *Record* computational cost metrics in `data/results/cost_metrics.csv` (`dataset_id, method_id, train_time_s, inference_time_s, peak_ram_mb`).  
  *Handle* method‑level failures gracefully: record `status=failed` and `error_msg` in `uq_methods.csv`; continue with remaining methods (pipeline status = `partial_success`).  Dataset‑level download failures abort loudly (as enforced in T002).  
  *Verification*: `code/tests/test_full_pipeline.py` validates all CSVs against their contracts, asserts every method‑dataset combination is present, and checks `n_test ≥ 200`.  Exit 0.  
  *Path*: `code/pipeline.py`, `data/results/per_sample_errors.csv`, `data/results/uq_methods.csv`, `data/results/pipeline_log.csv`, `data/results/cost_metrics.csv`, `code/tests/test_full_pipeline.py`

- [ ] T005 [US2] **Compute calibration error, sharpness, and coverage metrics**   <!-- FAILED-IN-EXECUTION: code/metrics/generate_metrics_raw.py exit=1; code/main.py exit=1 -->
  *Implement* `code/metrics/evaluation.py` that reads `data/results/per_sample_errors.csv` and, for each dataset‑method pair, calculates:  

  1. **Calibration Error (ECE)** – standard equal‑probability binning over prediction‑interval confidence.  
  2. **Sharpness** – mean interval width `U − L`.  
  3. **Coverage Error** – `|empirical_coverage − nominal_coverage|`.  

  Write the results to `data/results/metrics_raw.csv` conforming to `contracts/metrics.schema.yaml` (`dataset_id, method_id, metric_type, value, nominal_coverage, timestamp`).  
  *Verification*: `code/tests/test_metrics.py` checks schema compliance, ensures all four methods × three datasets are covered, and validates ISO‑8601 timestamps.  Exit 0.  
  *Path*: `code/metrics/evaluation.py`, `data/results/metrics_raw.csv`, `code/tests/test_metrics.py`

- [ ] T006 [US3] **Paired Wilcoxon signed‑rank significance testing with Bonferroni correction**  
  *Implement* `code/stats/significance.py` to generate the 6 unique method pairs for each dataset, run paired Wilcoxon signed‑rank tests on the **per‑sample calibration error** and **sharpness** vectors (same test set), and apply Bonferroni correction across the 18 tests (α ≈ 0.00278).  Compute rank‑biserial effect sizes with 95 % bootstrap confidence intervals.  
  *Write* `data/results/statistical_report.csv` conforming to `contracts/stats.schema.yaml` (`dataset_id, method_a, method_b, metric_type, p_value, test_type, significant, alpha, correction`).  
  *Verification*: `code/tests/test_statistics.py` validates the CSV against the schema, asserts `test_type` is `wilcoxon_signed_rank`, and checks that the `significant` flag respects the Bonferroni‑adjusted α.  Exit 0.  
  *Path*: `code/stats/significance.py`, `data/results/statistical_report.csv`, `code/tests/test_statistics.py`

- [ ] T007 [US3] **Conformal coverage sensitivity sweep and trade‑off figure**  
  *Sweep* nominal coverage from **0.95** to **0.99** in steps of **0.01** for the Split‑Conformal method (and, where applicable, analogous interval‑producing variants of the other methods).  Implement in `code/sensitivity_sweep.py`.  For each level compute empirical coverage and average interval width.  
  *Write* `data/results/sensitivity_report.csv` (`dataset_id, method_id, nominal_coverage, empirical_coverage, avg_interval_width`).  
  *Generate* `figures/sensitivity_tradeoff.png` (coverage vs. interval width, faceted by method and dataset) using `matplotlib`.  
  *Verification*: `code/tests/test_sensitivity.py` asserts the set of `nominal_coverage` values is exactly `{0.95,…,0.99}`, validates numeric ranges, and confirms the PNG can be opened.  Exit 0.  
  *Path*: `code/sensitivity_sweep.py`, `data/results/sensitivity_report.csv`, `figures/sensitivity_tradeoff.png`, `code/tests/test_sensitivity.py`

- [ ] T008 [US1] **Model‑constraint enforcement, performance monitoring, and reproducibility smoke test**  
  *Wrap* the full pipeline with a `psutil` monitor in `code/monitor.py` that records total wall‑clock time and peak RAM.  Assert `total_duration_seconds < 3600` and `memory_peak_mb ≤ 2000` (NFR‑001).  
  *Enforce* model limits: Deep Ensemble ≤ 3 sub‑models, MC‑Dropout ≤ 200 stochastic passes, all torch models on `device="cpu"`, no 8‑bit quantization (FR‑002).  Violations are logged to `data/results/model_constraints.log` and abort the run.  
  *Guarantee* fixed seeds (`numpy`, `torch`, and split seeds) for full reproducibility (NFR‑003).  
  *Add* `code/tests/smoke_test.py` that re‑runs the thin pipeline and asserts all metric values in `data/results/metrics_raw.csv` match a stored reference `code/tests/reference/metrics_raw_ref.csv` within `1e-8`.  Any mismatch raises `AssertionError`.  
  *Validate* every generated CSV against its contract; on violation write details to `data/results/schema_validation.log` and abort.  
  *Verification*: `code/tests/test_all_validations.py` runs the above checks end‑to‑end and exits 0.  
  *Path*: `code/monitor.py`, `data/results/model_constraints.log`, `data/results/schema_validation.log`, `code/tests/smoke_test.py`, `code/tests/test_all_validations.py`

- [ ] T012 **Record artifact hashes for versioning discipline**  
  *Implement* `code/state/update_hashes.py` that, after successful schema validation, computes SHA‑256 hashes of all generated CSV/PNG artifacts in `data/results/` and `figures/`, then writes a mapping `artifact_hashes` into `state/projects/PROJ-737-assessing-uncertainty-quantification-tec.yaml`.  Also updates the `updated_at` timestamp.  
  *Verification*: `code/tests/test_state_hashes.py` recomputes hashes and checks they match the entries in the state file; exits 0.  
  *Path*: `code/state/update_hashes.py`, `state/projects/PROJ-737-assessing-uncertainty-quantification-tec.yaml`, `code/tests/test_state_hashes.py`

- [ ] T009 [US1] **Summary tables and reliability diagrams**  
  *Implement* `code/visualize_summary.py` to aggregate calibration error, sharpness, and cost metrics into `data/results/summary.csv` (`dataset_id, method_id, calibration_error, sharpness, train_time_s, inference_time_s, peak_ram_mb`).  
  *Implement* `code/visualize_reliability.py` to produce `figures/reliability_diagrams.png` (one panel per dataset, all four methods overlaid, showing observed vs. nominal coverage).  
  *Verification*: `code/tests/test_visualization.py` validates `summary.csv` column names/types, asserts both PNG files exist and are readable.  Exit 0.  
  *Path*: `code/visualize_summary.py`, `code/visualize_reliability.py`, `data/results/summary.csv`, `figures/reliability_diagrams.png`, `code/tests/test_visualization.py`

---

## Phase 3 – Reproducible results and paper handoff  

**Goal**: Produce a concise methods/results narrative and expose all artifacts for downstream paper generation.

- [ ] T010 [US1] **Methods/results account and paper‑stage handoff**  
  *Write* a narrative in `specs/001-assessing-uncertainty-quantification-tec/results_overview.md` that:  

  1. Links each UQ method (GPR, MC‑Dropout, Deep Ensemble, Split‑Conformal) to its observed performance (lowest calibration error, sharpest intervals) per dataset.  
  2. Summarizes statistical significance outcomes after Bonferroni correction.  
  3. Explicitly notes the construct‑validity limitation (Formation Energy used as a proxy for Elastic Modulus) and qualifies any physical‑property conclusions accordingly.  
  4. Documents the exact commands for reproducing the full pipeline (`python -m code.main`) and the thin run (`python -m code.main --thin`).  
  5. Lists locations of all CSVs and figures required for the manuscript and points to the pinned `requirements.txt`.  
  6. **References Constitution compliance**, stating that reproducibility (Principle I), data hygiene (III), versioning discipline (V) and computational‑budget discipline (VI) have been verified by the corresponding tasks and logs.  
  *Verification*: `code/tests/test_handoff.py` asserts every artifact path referenced in the markdown exists and that the documented commands parse without error.  Exit 0.  
  *Path*: `specs/001-assessing-uncertainty-quantification-tec/results_overview.md`, `code/tests/test_handoff.py`

- [ ] T011 [US1] **Final end‑to‑end verification**  
  *Execute* the full pipeline (`python -m code.main`) from its declared inputs, then run `code/tests/test_all_validations.py` and `code/tests/test_full_pipeline.py`.  Confirm that:  

  1. All required CSVs and figures exist and pass schema validation.  
  2. Model‑constraint and performance limits hold.  
  3. The reproducibility smoke test passes.  

  The command sequence must exit with status 0 and print `READY`.  
  *Verification*: CI runner checks the exit code and output; no additional script is needed.  
  *Path*: `code/main.py` (entry point), `code/tests/test_all_validations.py`, `code/tests/test_full_pipeline.py`

---

## Dependencies and requirement coverage  

| Spec / Success Criterion | Covered by Task(s) |
|--------------------------|--------------------|
| **FR‑001** (real datasets) | T002 |
| **FR‑002** (CPU‑only, model caps) | T003, T004, T008 |
| **FR‑003** (featurization, caps, stratified split) | T003, T004 |
| **FR‑004** (paired Wilcoxon) | T006 |
| **FR‑005** (CSV schemas) | T003–T009 |
| **SC‑001** (pipeline execution) | T001, T003, T004, T011 |
| **SC‑002** (metric calculation) | T005 |
| **SC‑003** (statistical significance) | T006 |
| **SC‑004** (sensitivity sweep) | T007 |
| **SC‑05** (process three datasets) | T002, T004 |
| **NFR‑001** (time & memory) | T008 |
| **NFR‑002** (graceful partial results) | T004 (status = failed recorded) |
| **NFR‑003** (fixed seeds, pinned deps) | T008, T010 |
| **US‑1** (single orchestrated script) | T001, T003, T004, T011 |
| **US‑2** (Calibration & Sharpness) | T005 |
| **US‑3** (Statistical & sensitivity analysis) | T006, T007 |

**Execution order**:  

1. T001 → 2. T002 → 3. T003 → 4. T004 → 5. T005 → 6. T006 → 7. T007 → 8. T008 → 9. T012 → 10. T009 → 11. T010 → 12. T011  

All tasks respect the required data flow; no verification runs before its prerequisite artifacts are produced.  