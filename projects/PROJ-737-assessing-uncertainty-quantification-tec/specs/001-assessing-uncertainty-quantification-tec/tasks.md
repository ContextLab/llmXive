# Tasks: Assessing Uncertainty Quantification Techniques for Materials Property Predictions

**Inputs**: `specs/001-assessing-uncertainty-quantification-tec/spec.md`, `plan.md`, `data-model.md`, `contracts/`

This checklist implements the smallest complete, reproducible study satisfying all functional, non‑functional, and success‑criteria requirements. The four UQ methods are named explicitly (GPR, MC‑Dropout, Deep Ensemble, Split‑Conformal). Formation Energy is used as the proxy for Elastic Modulus, and the construct‑validity caveat is carried throughout.

---

## Phase 1 — Setup and first end‑to‑end analysis  

**Goal**: Verify that the pipeline runs on a tiny real‑data subset before scaling up.

- [ ] T001 [US1] **Document runnable command and verify per‑sample schema**  
  *Create* `specs/001-assessing-uncertainty-quantification-tec/quickstart.md` with the command `python -m code.main --thin`. Include a short description of the four UQ methods, the 2000‑sample training cap, the deterministic sampling rule (seed 42, first‑N rows), the paired Wilcoxon test rationale, and the Formation Energy proxy note.  
  *Verify* that `specs/001-assessing-uncertainty-quantification-tec/contracts/per_sample_errors.schema.yaml` lists exactly the columns `sample_id, dataset, method, prediction, lower_bound, upper_bound, ground_truth, abs_error`.  
  *Path*: `specs/001-assessing-uncertainty-quantification-tec/quickstart.md`, `specs/001-assessing-uncertainty-quantification-tec/contracts/per_sample_errors.schema.yaml`  
  *Check*: a tiny test script loads the schema YAML, asserts the column set, and exits 0.

- [ ] T002 [US1] **Download three real materials datasets via direct URLs**  
  *Implement* `code/download.py` that uses `datasets` (or `urllib`) to fetch the exact raw CSVs:  
  1. **Band Gap** – OQMD CSV from `https://huggingface.co/datasets/oqmd/band_gap/resolve/main/band_gap.csv` → `data/raw/band_gap.csv`  
  2. **Formation Energy** – OQMD CSV from `https://huggingface.co/datasets/oqmd/formation_energy/resolve/main/formation_energy.csv` → `data/raw/formation_energy.csv`  
  3. **Thermal Conductivity** – AFLOW CSV from `[UNRESOLVED-CLAIM: https://aflow.org/AFLOWLIB_DATA/thermal_conductivity.csv` — HTTP 404] → `data/raw/thermal_conductivity.csv`  
  *Requirements*: no `try/except` fallback; any fetch error must raise and abort. After each download compute a SHA‑256 checksum and write `data/raw/<dataset_id>_metadata.json` containing `dataset_id`, `source_url` (the verified URL), `property_name`, `n_samples_original`, `n_samples_used`, `checksum`. Cap each dataset at 5 000 rows deterministically (seed 42, `itertools.islice`).  
  *Verification*: `code/tests/test_download.py` loads each metadata JSON, asserts the CSV exists, checksum matches, `n_samples_used ≤ 5000`, the source URL points to the correct OQMD/AFLOW dataset, and the CSV contains a composition column and a numeric target with ≥ 100 non‑null rows.  
  *Path*: `code/download.py`, `data/raw/*.csv`, `data/raw/*_metadata.json`, `code/tests/test_download.py`

- [ ] T003 [US1] **Featurize, split, and run a thin end‑to‑end analysis on a 100‑sample subset**  
  *Implement* `code/featurize.py` to convert compositions to feature vectors with `matminer` featurizers; fallback to elemental‑fraction vectors via `pymatgen` if a featurizer fails. Write `data/processed/<dataset_id>.csv`.  
  *Perform* a stratified 70 %/15 %/15 % train/val/test split by target‑property range, saving split indices to `data/processed/<dataset_id>_split.json`.  
  *Implement* the four UQ methods in `code/models/`:  
  - `gpr.py` (sklearn GPR, ≤ 2000 training points)  
  - `mc_dropout.py` (torch MLP ≤ 2 M params, 50 stochastic passes, `device="cpu"`)  
  - `deep_ensemble.py` (ensemble of 3 MLPs, distinct seeds)  
  - `conformal.py` (XGBoost + split‑conformal calibration)  
  Each returns point predictions and lower/upper bounds on the test set.  
  *Run* the thin pipeline on the first 100 rows of each capped dataset (use `--thin` flag). Write per‑sample rows to `data/results/per_sample_errors.csv` (exact schema columns) and a pipeline log `data/results/pipeline_run.json` conforming to `contracts/pipeline.schema.yaml`.  
  *Verification*: `code/tests/test_thin_pipeline.py` validates `per_sample_errors.csv` against the per‑sample schema, validates `pipeline_run.json` against the pipeline schema, and asserts that all four methods produced rows for each dataset subset. The command `python -m code.main --thin` must exit 0.  
  *Path*: `code/featurize.py`, `code/models/*.py`, `data/processed/*.csv`, `data/results/per_sample_errors.csv`, `data/results/pipeline_run.json`, `code/tests/test_thin_pipeline.py`

---

## Phase 2 — Complete the study and validate its evidence  

**Goal**: Run the full pipeline on all capped datasets, compute metrics, perform statistical testing, and produce sensitivity analyses.

- [ ] T004 [US1] **Full‑scale pipeline on all three capped datasets (uniform 2000‑sample training cap)**  
  *Extend* `code/pipeline.py` to orchestrate: download → featurize → split → train all four UQ methods on each dataset (≤ 5000 rows total, ≤ 2000 training examples per method). Enforce ≥ 200 test samples per dataset (power‑analysis requirement).  
  *Persist* per‑sample predictions for every dataset × method in a single `data/results/per_sample_errors.csv` (schema‑compliant).  
  *Write* the UQMethod registry `data/results/uq_methods.csv` (`method_id, baseline_model, hyperparams, n_iterations, status, error_msg`).  
  *Write* the pipeline execution log `data/results/pipeline_log.csv` (conforms to `contracts/pipeline.schema.yaml`).  
  *Record* cost metrics in `data/results/cost_metrics.csv` (`dataset_id, method_id, train_time_s, inference_time_s, peak_ram_mb`).  
  *Handle* method‑level failures gracefully: record `status=failed` and `error_msg` in `uq_methods.csv`; continue with remaining methods (partial_success). Dataset‑level download failures abort loudly (per T002).  
  *Verification*: `code/tests/test_full_pipeline.py` validates all CSVs against their contracts, asserts every method‑dataset combination is present, and checks `n_test ≥ 200`. Exit 0.  
  *Path*: `code/pipeline.py`, `data/results/per_sample_errors.csv`, `data/results/uq_methods.csv`, `data/results/pipeline_log.csv`, `data/results/cost_metrics.csv`, `code/tests/test_full_pipeline.py`

- [ ] T005 [US2] **Compute calibration error, sharpness, and coverage metrics**  
  *Implement* `code/metrics/evaluation.py` that reads `data/results/per_sample_errors.csv` and, for each dataset‑method pair, calculates:  
  - Calibration Error (standard binned ECE over prediction intervals)  
  - Sharpness (mean interval width `U − L`)  
  - Coverage Error (`|empirical − nominal|`)  
  Write results to `data/results/metrics_raw.csv` conforming to `contracts/metrics.schema.yaml` (`dataset_id, method_id, metric_type, value, nominal_coverage, timestamp`).  
  *Verification*: `code/tests/test_metrics.py` checks schema compliance, ensures all four methods × three datasets are covered, and that timestamps parse as ISO‑8601. Exit 0.  
  *Path*: `code/metrics/evaluation.py`, `data/results/metrics_raw.csv`, `code/tests/test_metrics.py`

- [ ] T006 [US3] **Paired Wilcoxon signed‑rank significance testing with Bonferroni correction**  
  *Implement* `code/stats/significance.py` to generate all 6 unique method pairs for each dataset, run paired Wilcoxon signed‑rank tests on per‑sample errors (same test set), and apply Bonferroni correction across the 18 tests (α ≈ 0.00278). Compute rank‑biserial effect sizes with bootstrap 95 % confidence intervals.  
  *Write* `data/results/statistical_report.csv` conforming to `contracts/stats.schema.yaml` (`dataset_id, method_a, method_b, metric_type, p_value, test_type, significant, alpha, correction`).  
  *Verification*: `code/tests/test_statistics.py` validates the CSV against the schema, asserts `test_type` is only `wilcoxon_signed_rank`, and that the `significant` flag respects the Bonferroni‑adjusted α. Exit 0.  
  *Path*: `code/stats/significance.py`, `data/results/statistical_report.csv`, `code/tests/test_statistics.py`

- [ ] T007 [US3] **Conformal coverage sensitivity sweep and trade‑off figure**  
  *Sweep* nominal coverage from 0.90 to 0.99 in steps of 0.01 for the split‑conformal method (and analogous interval‑producing variants for the other methods where applicable). Implement in `code/sensitivity_sweep.py`. For each level compute empirical coverage and average interval width.  
  *Write* `data/results/sensitivity_report.csv` (`dataset_id, method_id, nominal_coverage, empirical_coverage, avg_interval_width`).  
  *Generate* `figures/sensitivity_tradeoff.png` (coverage vs. interval width, faceted by method and dataset) using `matplotlib`.  
  *Verification*: `code/tests/test_sensitivity.py` asserts the set of `nominal_coverage` values is exactly `{0.90, 0.91, …, 0.99}`, validates numeric ranges, and confirms the PNG can be opened. Exit 0.  
  *Path*: `code/sensitivity_sweep.py`, `data/results/sensitivity_report.csv`, `figures/sensitivity_tradeoff.png`, `code/tests/test_sensitivity.py`

- [ ] T008 [US1] **Model‑constraint enforcement, performance monitoring, and reproducibility smoke test**  
  *Wrap* the full pipeline with a `psutil` monitor recording total wall‑clock time and peak memory; implement in `code/monitor.py`. Assert `total_duration_seconds < 3600` and `memory_peak_mb ≤ 2000` (NFR‑001).  
  *Enforce* model limits: Deep Ensemble ≤ 3 sub‑models, MC‑Dropout ≤ 200 passes, all torch models on `device="cpu"`, no quantization (FR‑002). Violations are logged to `data/results/model_constraints.log` and abort the run.  
  *Guarantee* fixed seeds (`np.random.seed`, `torch.manual_seed`, seeded splits) for reproducibility (NFR‑003).  
  *Add* `code/tests/smoke_test.py` that re‑runs the thin pipeline and asserts all metric values in `data/results/metrics_raw.csv` match a stored reference `code/tests/reference/metrics_raw_ref.csv` within `1e-8`. Any mismatch raises `AssertionError`.  
  *Validate* every generated CSV against its contract; on violation write details to `data/results/schema_validation.log` and abort.  
  *Verification*: `code/tests/test_all_validations.py` runs the above checks end‑to‑end and exits 0.  
  *Path*: `code/monitor.py`, `data/results/model_constraints.log`, `data/results/schema_validation.log`, `code/tests/smoke_test.py`, `code/tests/test_all_validations.py`

- [ ] T009 [US1] **Summary tables and reliability diagrams**  
  *Implement* `code/visualize_summary.py` to aggregate calibration error, sharpness, and cost metrics into `data/results/summary.csv` (`dataset_id, method_id, calibration_error, sharpness, train_time_s, inference_time_s, peak_ram_mb`).  
  *Implement* `code/visualize_reliability.py` to produce `figures/reliability_diagrams.png` (one panel per dataset, all four methods overlaid, showing observed vs. nominal coverage).  
  *Verification*: `code/tests/test_visualization.py` validates `summary.csv` column names/types, asserts both PNG files exist and are readable. Exit 0.  
  *Path*: `code/visualize_summary.py`, `code/visualize_reliability.py`, `data/results/summary.csv`, `figures/reliability_diagrams.png`, `code/tests/test_visualization.py`

---

## Phase 3 — Reproducible results and paper handoff  

**Goal**: Produce a concise methods/results narrative and expose all artifacts for downstream paper generation.

- [ ] T010 [US1] **Methods/results account and paper‑stage handoff**  
  *Write* a concise narrative in `specs/001-assessing-uncertainty-quantification-tec/results_overview.md` that:  
  - Links each UQ method (GPR, MC‑Dropout, Deep Ensemble, Split‑Conformal) to its performance (lowest calibration error, sharpest intervals) per dataset.  
  - Summarizes statistical significance outcomes after Bonferroni correction.  
  - Explicitly notes the construct‑validity limitation (Formation Energy as proxy for Elastic Modulus) and the resulting narrowed physical‑diversity claim.  
  - Documents the exact commands for reproducing the full pipeline (`python -m code.main`) and the thin run (`python -m code.main --thin`).  
  - Lists locations of all CSVs and figures required for the manuscript, and points to the pinned `requirements.txt`.  
  *Verification*: `code/tests/test_handoff.py` asserts every artifact path referenced exists and that the documented commands parse without error. Exit 0.  
  *Path*: `specs/001-assessing-uncertainty-quantification-tec/results_overview.md`, `code/tests/test_handoff.py`

- [ ] T011 [US1] **Final end‑to‑end verification**  
  *Execute* the full pipeline (`python -m code.main`) from its declared inputs, then run `code/tests/test_all_validations.py` and `code/tests/test_full_pipeline.py`. Confirm that:  
  - All required CSVs and figures exist and pass schema validation.  
  - Model‑constraint and performance limits hold.  
  - The reproducibility smoke test passes.  
  *The command sequence must exit with status 0 and print `READY`.**  
  *Verification*: The CI runner checks the exit code and output; no additional script needed.  
  *Path*: `code/main.py` (entry point), `code/tests/test_all_validations.py`, `code/tests/test_full_pipeline.py`

---

## Dependencies and requirement coverage  

| Spec / Success Criterion | Covered by Task(s) |
|--------------------------|--------------------|
| **FR‑001** (real datasets) | T002 (direct OQMD/AFLOW URLs) |
| **FR‑002** (CPU‑only, model caps) | T003, T004, T008 (model‑constraint enforcement) |
| **FR‑003** (featurization, caps, stratified split) | T003, T004 |
| **FR‑004** (paired Wilcoxon) | T006 (only paired Wilcoxon used) |
| **FR‑005** (CSV schemas) | T003–T009 (all CSV outputs) |
| **SC‑001** (pipeline execution) | T001, T003, T004, T011 |
| **SC‑002** (metric calculation) | T005 |
| **SC‑003** (statistical significance) | T006 |
| **SC‑004** (sensitivity sweep) | T007 |
| **SC‑005** (process three datasets) | T002, T004 |
| **NFR‑001** (time & memory) | T008 |
| **NFR‑002** (graceful partial results) | T004 (status = failed recorded) |
| **NFR‑003** (fixed seeds, pinned deps) | T008, T010 |
| **US‑1** (single orchestrated script) | T001, T003, T004, T011 |
| **US‑2** (Calibration & Sharpness) | T005 |
| **US‑3** (Statistical & sensitivity analysis) | T006, T007 |

**Execution order**:  

1. T001 → 2. T002 → 3. T003 (thin run) → 4. T004 → 5. T005 → 6. T006 → 7. T007 → 8. T008 → 9. T009 → 10. T010 → 11. T011  

All tasks respect data flow: each verification step runs only after its prerequisite artifacts are produced. No task creates or modifies platform‑owned state outside the project’s `data/`, `results/`, `figures/`, or `code/` directories.