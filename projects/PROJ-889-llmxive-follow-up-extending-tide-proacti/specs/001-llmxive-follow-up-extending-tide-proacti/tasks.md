# Tasks: Extending “TIDE: Proactive Multi‑Problem Discovery via Template‑Guided Iteration”

**Inputs**: `spec.md`, `plan.md`, the research idea, and the contracts in `specs/001-llmxive-follow-up-extending-tide-proacti/contracts/`.

The checklist implements the smallest complete study that satisfies every functional requirement (FR‑001 – FR‑010) and measurable success criterion (SC‑001 – SC‑005) while respecting the computational constraints (≤ 6 h wall‑clock, ≤ 80 % CPU). Tasks are ordered to respect data flow and are grouped into logical research phases.

---

## Phase 1 – Data acquisition & early sanity check  

- [ ] T001 [US‑1] Download the official TIDE evaluation dataset from the verified URL and generate a deterministic synthetic edge‑case corpus.  
  **Path**: `src/data/acquire_real.py` (real download) and `src/data/generate_synthetic.py` (synthetic generation).  
  **Verification**:  
  • Running `python -m src.data.acquire_real` loads the dataset via the verified HTTP URL `[UNRESOLVED-CLAIM: https://huggingface.co/datasets/deeplearning-tide/actresses/resolve/main/data/test-00000-of-00001-9189dc62872204f7.parquet` — HTTP 404], checks the SHA‑256 checksum (`data/raw/tide.sha256`), and writes `data/raw/tide_eval.csv` with ≥ 200 rows.  
  • Running `python -m src.data.generate_synthetic --seed 42` creates ≥ 200 `.py` files under `data/synthetic/` and a metadata CSV `data/raw/synthetic_meta.csv` where `dependency_depth` ∈ {1,…,5}. Depth values > 5 are capped to 5 and a warning is logged (see T002).  
  • A checksum file `data/raw/checksums.txt` is produced; any mismatch aborts the script.  

- [ ] T002 [US‑1] Enforce FR‑009 caps on intrinsic property values and log warnings when caps are applied.  
  **Path**: `src/data/cap_properties.py` (invoked by the synthetic generator).  
  **Verification**:  
  • Log file `data/logs/cap_warnings.log` contains a line for each instance where `dependency_depth` > 5 or `semantic_scope` exceeds the model’s context window.  
  • The final `synthetic_meta.csv` respects `dependency_depth ≤ 5` for every row.  

- [ ] T003 [US‑1] Extract quantitative structural features for every code instance and produce a unified feature matrix.  
  **Path**: `src/features/extract.py`.  
  **Verification**:  
  • `python -m src.features.extract` writes `data/interim/features.csv` with header  
    `instance_id,origin,dependency_depth,semantic_scope,syntactic_complexity,ast_depth,import_count,cyclomatic_complexity,sha256`.  
  • Row count ≥ 400 (real + synthetic) and each row validates against the subset of `contracts/detection_results.schema.yaml` that applies to feature records (type checks, non‑null values).  

---

## Phase 2 – Pipeline execution (static & generative)  

- [ ] T004 [US‑2] Implement the deterministic static heuristic “TIDE‑Lite”.  
  **Path**: `src/pipelines/tide_lite.py`.  
  **Verification**:  
  • Unit test `src/tests/test_tide_lite.py` asserts that a known simple instance yields `prediction=True`.  
  • Running `python -m src.pipelines.tide_lite --input data/interim/features.csv --output data/results/tide_lite_enriched.csv` produces a CSV that passes full schema validation (`contracts/detection_results.schema.yaml`).  
  • All latency values are > 0 ms.  

- [ ] T005 [US‑2] Implement the generative “TIDE‑Original” pipeline using a CPU‑quantized small language model.  
  **Path**: `src/pipelines/tide_original.py`.  
  **Verification**:  
  • Uses `transformers` with an 8‑bit quantized `distilgpt2` model (`device="cpu"`).  
  • Deterministic decoding (`temperature=0.0`, `top_k=1`).  
  • Unit test `src/tests/test_tide_original.py` checks that the same known instance yields the expected `prediction`.  
  • Running `python -m src.pipelines.tide_original --input data/interim/features.csv --output data/results/tide_original_enriched.csv` creates a schema‑compliant CSV.  

- [ ] T006 [US‑2] Perform a sanity‑run on a small sample (first 10 rows) and produce a tiny merged file.  
  **Path**: `src/run_all.py --sample 10`.  
  **Verification**:  
  • File `data/tmp/sanity_merged.csv` exists, contains 10 rows with columns from both pipelines, and no exceptions were raised.  

- [ ] T007 [US‑2] Consolidate feature records and both pipeline results into the single source‑of‑truth `data/processed/merged_results.csv`.  
  **Path**: `src/analysis/merge.py`.  
  **Verification**:  
  • Row count equals the number of instances in `features.csv`.  
  • Each `instance_id` appears **once** with columns `static_prediction`, `static_latency_ms`, `generative_prediction`, `generative_latency_ms` alongside all feature columns.  
  • The merged CSV validates against the full `contracts/detection_results.schema.yaml`.  

---

## Phase 3 – Statistical modelling & validation  

- [ ] T008 [US‑3] Split the merged dataset into training and hold‑out validation sets (seed = 42).  
  **Path**: `src/analysis/split.py`.  
  **Verification**:  
  • Files `data/processed/train_indices.npy` and `data/processed/val_indices.npy` are written.  
  • Split ratio is 80 % / 20 % and there is no overlap of `instance_id`s between sets.  

- [ ] T009 [US‑3] Fit logistic regression on the training split with 5‑fold cross‑validation and report average AUC.  
  **Path**: `src/analysis/logistic.py`.  
  **Verification**:  
  • Outputs `analysis/logistic_summary.json` containing `coefficients`, `p_values`, and `mean_auc`.  
  • For each fold the script records the 0.5‑probability threshold for the primary predictor; the summary reports the mean and variance of these thresholds (FR‑010).  
  • A warning is logged if `mean_auc < 0.6`.  

- [ ] T010 [US‑3] Estimate the 0.5‑probability threshold on the hold‑out set using a **binary search with tolerance 0.01** and compute a 95 % bootstrap confidence interval (1 000 resamples).  
  **Path**: `src/analysis/threshold_estimation.py`.  
  **Verification**:  
  • `analysis/logistic_summary.json` is updated with a `thresholds` dictionary (feature → value) and a `threshold_ci` dictionary (95 % CI).  
  • The script prints “Binary search tolerance: 0.01” and asserts that the search stopped when the probability difference fell below 0.01.  
  • The bootstrap completes (1000 samples) and reports the CI; exit status 0.  

- [ ] T011 [US‑3] Conduct stratified McNemar’s tests across **three complexity bins** (low, medium, high) as defined by tertiles of a combined intrinsic‑complexity score (e.g., weighted sum of `syntactic_complexity` and `dependency_depth`). Apply Holm‑Bonferroni correction to the three p‑values.  
  **Path**: `src/analysis/mcnemar.py`.  
  **Verification**:  
  • Generates `analysis/mcnemar_results.csv` with columns `complexity_bin,static_tp,static_fp,generative_tp,generative_fp,p_value,p_value_corrected`.  
  • All raw p‑values are numeric (≤ 1.0); corrected p‑values are computed via `statsmodels.stats.multitest.multipletests` (method=“holm”).  
  • No requirement that any corrected p‑value be < 0.05; task passes once the CSV validates.  

- [ ] T012 [US‑3] Perform sensitivity analysis over probability cut‑offs `{0.01, 0.05, 0.10}` and compute variance of false‑positive/false‑negative rates.  
  **Path**: `src/analysis/sensitivity.py`.  
  **Verification**:  
  • Outputs `analysis/sensitivity_summary.csv` with columns `cutoff,fp_rate,fn_rate,variance`.  
  • If `variance > 0.05` a warning is written to `analysis/logs/sensitivity.log`.  

- [ ] T013 [US‑3] Summarise execution efficiency (total wall‑clock time, average CPU utilisation, limits check).  
  **Path**: `src/analysis/efficiency.py`.  
  **Verification**:  
  • Produces `analysis/efficiency_report.json` containing `total_seconds`, `avg_cpu_percent`, and `within_limits` (true only if total ≤ 6 h and CPU ≤ 80 %).  
  • CI test asserts `within_limits == true`.  

---

## Phase 4 – Visualisation, tables & reproducible handoff  

- [ ] T014 [US‑3] Generate required figures directly from `merged_results.csv` **and** write the methods‑and‑results handoff document linking every artifact.  
  **Path**: `src/visualization/plot_all.py` (figures) and `paper/methods_results.md` (hand‑off).  
  **Verification**:  
  • Figures saved under `outputs/figures/` include `roc_static_vs_generative.png`, `pdp_complexity.png`, and `mcnemar_bar.png`; each file is non‑empty and listed in `outputs/manifest.txt`.  
  • `paper/methods_results.md` contains explicit relative references to all CSV/JSON/PNG files produced in earlier tasks, a reproducibility checklist (seed values, software versions from `requirements.txt`, exact command `python -m src.run_all`), and passes the `pytest -m handoff` validation test.  

---

### Dependency Summary (for reference)

| Requirement | Satisfying Task(s) |
|-------------|-------------------|
| FR‑001, FR‑009 | T001, T002, T003 |
| FR‑002, FR‑004 | T004 |
| FR‑003, FR‑004 | T005 |
| FR‑005, FR‑010 | T008, T009, T010 |
| FR‑006, FR‑008 | T011 |
| FR‑007 | T012 |
| FR‑010 (cross‑validation) | T009 |
| SC‑001 | T010 |
| SC‑002 | T011 |
| SC‑003 | T012 |
| SC‑004 | T013 |
| SC‑005 | T001, T003 |

All tasks are currently unchecked; executing them in the order presented will yield a complete, reproducible study that meets the specification without violating any constraints.  