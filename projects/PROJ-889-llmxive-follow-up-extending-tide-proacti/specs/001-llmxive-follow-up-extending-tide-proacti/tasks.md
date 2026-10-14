# Tasks: Extending “TIDE: Proactive Multi‑Problem Discovery via Template‑Guided Iteration”

**Inputs**: `spec.md`, `plan.md`, the research idea, and the contracts in `specs/001-llmxive-follow-up-extending-tide-proacti/contracts/`.

The following checklist implements the smallest complete study that satisfies every functional requirement (FR‑001 – FR‑010) and measurable success criterion (SC‑001 – SC‑005) while respecting the computational constraints (≤ 6 h wall‑clock, ≤ 80 % CPU). Tasks are ordered to respect data flow and are grouped into logical research phases.

---

## Phase 1 – Data acquisition & early end‑to‑end sanity check

- [ ] T001 [US‑1] Download the real CodeXGLUE defect‑detection dataset and generate the synthetic edge‑case corpus.   <!-- FAILED-IN-EXECUTION: code/data/download_real.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/data/download_real.py exit=1 --> <!-- FAILED-IN-EXECUTION: src/data/acquire.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/data/download_real.py exit=1 -->
  **Path**: `code/data/download_real.py` (real download) and `code/data/generate_synthetic.py` (synthetic generation).  
  **Verification**:  
  • `datasets.load_dataset("code_x_glue", "defect_detection")` runs without error and returns ≥ 200 instances.  
  • Synthetic script uses a pinned random seed (`seed=42`) and creates ≥ 200 `.py` files with `dependency_depth` ∈ {1…5}.  
  • A SHA‑256 checksum file `data/raw/checksums.txt` is written; mismatches cause the script to abort.

- [ ] T002 [US‑1] Cap intrinsic property values per FR‑009 and record any capping warnings.  
  **Path**: `code/data/cap_properties.py` (called by the generation script).  
  **Verification**:  
  • Log file `data/logs/cap_warnings.log` contains only lines for instances where `dependency_depth` > 5 or `semantic_scope` exceeds the model context window.  
  • All rows in the final raw CSV respect `dependency_depth ≤ 5`.

- [ ] T003 [US‑1] Produce a unified feature matrix `data/interim/features.csv`.  
  **Path**: `code/features/extract_features.py`.  
  **Verification**:  
  • CSV header includes `instance_id,origin,dependency_depth,semantic_scope,syntactic_complexity,ast_depth,import_count,cyclomatic_complexity,sha256`.  
  • Row count ≥ 400 (real + synthetic).  
  • Validate each row against the subset of `detection_results.schema.yaml` that applies to feature records (type checks, non‑null values).

---

## Phase 2 – Full pipeline execution (static & generative)

- [ ] T005 [US‑2] Implement the deterministic static heuristic “TIDE‑Lite”.  
  **Path**: `code/pipelines/tide_lite.py`.  
  **Verification**:  
  • Unit test `code/tests/test_tide_lite.py` asserts that a known simple instance yields `prediction=True`.  
  • When run on the full dataset (`code/run_all.py --pipeline tide_lite`), produces `data/results/tide_lite_enriched.csv` that conforms to `contracts/detection_results.schema.yaml` (schema validation script `code/validation/validate_schema.py` must pass).

- [ ] T006 [US‑2] Implement the generative “TIDE‑Original” pipeline using a CPU‑quantized LLM.  
  **Path**: `code/pipelines/tide_original.py`.  
  **Verification**:  
  • Uses `transformers` with `bitsandbytes` 8‑bit quantization of `gpt2` (or comparable ≤ 1 B‑param model).  
  • Deterministic decoding (`temperature=0.0`, `top_k=1`).  
  • Unit test `code/tests/test_tide_original.py` checks that the same known instance yields the expected `prediction`.  
  • Full run (`code/run_all.py --pipeline tide_original`) creates `data/results/tide_original_enriched.csv` that passes schema validation.

- [ ] T004 [US‑2] End‑to‑end sanity run: feed the first 10 rows of `features.csv` through both pipelines and produce a tiny merged file `data/tmp/sanity_merged.csv`.  
  **Path**: `code/run_all.py --sample 10`.  
  **Verification**:  
  • File exists and contains 10 rows with columns from both pipelines.  
  • No runtime exception; latency > 0 for every entry.

- [ ] T007 [US‑2] Consolidate static, generative, and feature records into the single source‑of‑truth `data/processed/merged_results.csv`.  
  **Path**: `code/analysis/merge_results.py`.  
  **Verification**:  
  • Row count equals the number of instances in `features.csv`.  
  • Each `instance_id` appears twice (once per pipeline) with identical feature columns.  
  • The merged file validates against the full `detection_results.schema.yaml` (including `pipeline`, `prediction`, `latency_ms`, and all feature fields).

---

## Phase 3 – Statistical modelling & validation

- [ ] T007_split [US‑3] Perform a random‑seeded (seed=42) split of the dataset into training and hold‑out validation sets.  
  **Path**: `code/analysis/split_data.py`.  
  **Verification**:  
  • Persists `data/processed/train_indices.npy` and `data/processed/val_indices.npy`.  
  • Validates that the split ratio is consistent (e.g., 80/20) and that no `instance_id` overlaps between sets.

- [ ] T008 [US‑3] Fit logistic regression on the training split and perform 5‑fold cross‑validation.  
  **Path**: `code/analysis/logistic.py`.  
  **Verification**:  
  • Outputs `analysis/logistic_summary.json` containing `coefficients`, `p_values`, `mean_auc`.  
  • For each fold, calculates the 0.5‑probability threshold for the primary predictor and reports the stability (mean and variance) of this threshold across folds per FR‑010.  
  • Mean AUC ≥ 0.6 (otherwise a warning is logged).

- [ ] T009 [US‑3] Estimate the 0.5‑probability threshold for each predictor (binary search tolerance 0.01) on the hold‑out validation set and bootstrap 1 000 resamples for confidence intervals.  
  **Path**: `code/analysis/threshold_estimation.py`.  
  **Verification**:  
  • `analysis/logistic_summary.json` now includes a `thresholds` dictionary (feature → value) and `threshold_ci` (95 % CI).  
  • Explicitly identifies a single "primary complexity threshold" (the value of the most significant predictor where prob=0.5) to satisfy SC‑001.  
  • The script prints the number of bootstrap samples completed; any failure aborts with a non‑zero exit code.

- [ ] T010 [US‑3] Conduct stratified McNemar’s tests across low/medium/high complexity bins.  
  **Path**: `code/analysis/mcnemar.py`.  
  **Verification**:  
  • Generates `analysis/mcnemar_results.csv` with columns `complexity_bin,static_tp,static_fp,generative_tp,generative_fp,p_value`.  
  • All three p‑values are non‑null and ≤ 1.0.

- [ ] T011 [US‑3] Apply Holm‑Bonferroni correction to the three McNemar p‑values and record corrected values in the same CSV.  
  **Path**: `code/analysis/correct_pvalues.py` (called by `mcnemar.py`).  
  **Verification**:  
  • CSV now contains `p_value_corrected`.  
  • At least one corrected p‑value < 0.05 triggers a “significant difference” flag in the log `analysis/logs/mcnemar.log`.

- [ ] T012 [US‑3] Perform sensitivity analysis over probability cut‑offs `{0.01, 0.05, 0.10}` and compute variance of FP/FN rates.  
  **Path**: `code/analysis/sensitivity.py`.  
  **Verification**:  
  • Outputs `analysis/sensitivity_summary.csv` with columns `cutoff,fp_rate,fn_rate,variance`.  
  • `variance` is reported; a value > 0.05 is logged as “high sensitivity variance”.

- [ ] T013 [US‑3] Summarize execution efficiency.  
  **Path**: `code/analysis/efficiency.py`.  
  **Verification**:  
  • Produces `analysis/efficiency_report.json` containing total wall‑clock time (seconds), `avg_cpu_percent`, and a boolean `within_limits` that is true only if wall‑clock ≤ 6 h and CPU ≤ 80 %.  
  • The CI test suite asserts `within_limits == true`.

---

## Phase 4 – Figures, tables & reproducible handoff

- [ ] T014 Generate all required visualisations directly from `merged_results.csv`.  
  **Path**: `code/visualization/plot_all.py`.  
  **Outputs** (saved under `outputs/figures/`):  
  • ROC curve for static vs. generative.  
  • Heat‑map of logistic‑predicted probability across the three intrinsic features.  
  • Bar plot of corrected McNemar p‑values per complexity bin.  
  **Verification**:  
  • Each PNG file is non‑empty and its filename appears in `outputs/manifest.txt`.  
  • A headless test (`pytest -m visualization`) confirms that the script runs without error on the full dataset.

- [ ] T015 Write the methods‑and‑results handoff document linking every artifact.  
  **Path**: `paper/methods_results.md`.  
  **Verification**:  
  • Contains explicit references to all CSV/JSON/PNG files generated above.  
  • Includes a reproducibility checklist (seed values, software versions from `requirements.txt`, and the exact command `python -m code.run_all`).  
  • The CI step `pytest -m handoff` parses the markdown and verifies that each referenced file exists.

---

### Dependency Summary

| Requirement | Satisfying Task(s) |
|-------------|-------------------|
| FR‑001, FR‑009 | T001, T002, T003 |
| FR‑002, FR‑004 | T005 |
| FR‑003, FR‑004 | T006 |
| FR‑005, FR‑010 | T007_split, T008, T009 |
| FR‑006, FR‑008 | T010, T011 |
| FR‑007 | T012 |
| SC‑001 | T009 |
| SC‑002 | T010, T011 |
| SC‑003 | T012 |
| SC‑004 | T013 |
| SC‑005 | T001, T003 |

All tasks are unchecked and ready to be executed in the order presented. Running `python -m code.run_all` will sequentially invoke the data‑download, feature‑extraction, both pipelines, and merging steps, after which the analysis scripts can be run independently or via the convenience script `code/run_all.py --full`.