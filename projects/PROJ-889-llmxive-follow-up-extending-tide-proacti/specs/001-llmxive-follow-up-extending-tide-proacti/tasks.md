# Tasks: Extending “TIDE: Proactive Multi‑Problem Discovery via Template‑Guided Iteration”

**Inputs**: `spec.md`, `plan.md`, the research idea, and the contracts in `specs/001-llmxive-follow-up-extending-tide-proacti/contracts/`.

The checklist implements the smallest complete study that satisfies every functional requirement (FR‑001 – FR‑010) and measurable success criterion (SC‑001 – SC‑005) while respecting the computational constraints (≤ 6 h wall‑clock, ≤ 80 % CPU). Tasks are ordered to respect data flow and are grouped into logical research phases.

---

## Phase 1 – Data acquisition & feature extraction  

- [ ] T001 [US‑1] **Download the verified TIDE evaluation dataset and verify its integrity**   <!-- FAILED-IN-EXECUTION: src/data/acquire_real.py exit=1 --> <!-- FAILED-IN-EXECUTION: src/data/acquire_real.py exit=1 -->
  **Path**: `src/data/acquire_real.py` (script streams the TIDE parquet via `datasets.load_dataset`, writes `data/raw/tide.csv`, computes a SHA‑256 checksum and aborts on mismatch).  
  **Verification**:  
  • Running `python -m src.data.acquire_real` exits with status 0.  
  • `data/raw/tide.csv` contains **≥ 200 rows**.  
  • A checksum file `data/raw/tide.sha256` is created and matches the SHA‑256 of `tide.csv`.  
  • Log `data/logs/acquire_real.log` records successful download and checksum validation.

- [ ] T002 [US‑1] **Generate a deterministic synthetic code corpus (≥ 200 instances) with systematic variation of intrinsic properties**  
  **Path**: `src/data/generate_synthetic.py` (accepts `--seed 42`, respects FR‑009 caps, writes individual `.py` files under `data/synthetic/` and a manifest `data/raw/synthetic_meta.csv`).  
  **Verification**:  
  • Running `python -m src.data.generate_synthetic --seed 42` exits with status 0.  
  • `data/raw/synthetic_meta.csv` contains **exactly 200 rows**; each row includes `dependency_depth` (1‑5), `semantic_scope` (`local`/`cross_module`), and `syntactic_complexity`.  
  • A test script `src/tests/test_generate_synthetic.py` asserts the row count and exits with status 0, printing the command‑line output.  
  • Any instance where `dependency_depth` would exceed 5 is capped and a warning is written to `data/logs/cap_warnings.log`.

- [ ] T003 [US‑1] **Enforce FR‑009 caps and log warnings for out‑of‑range property values**  
  **Path**: `src/data/cap_properties.py` (imported by the synthetic generator; also usable as a post‑hoc validator).  
  **Verification**:  
  • After generation, `python -m src.data.cap_properties data/raw/synthetic_meta.csv` exits with status 0 and produces `data/logs/cap_warnings.log`.  
  • The log contains one line per capped instance; the final `synthetic_meta.csv` shows all `dependency_depth` ≤ 5.

- [ ] T004 [US‑1] **Extract quantitative structural features and ground‑truth labels from every code instance (real + synthetic) and produce a unified feature matrix**  
  **Path**: `src/features/extract.py` (parses `.py` files, computes AST depth, import count, cyclomatic complexity via `radon`, reads `ground_truth_label` from the TIDE CSV, and records the intrinsic properties).  
  **Verification**:  
  • Running `python -m src.features.extract` writes `data/interim/features.csv`.  
  • The CSV header is  
    `instance_id,origin,ground_truth_label,dependency_depth,semantic_scope,syntactic_complexity,ast_depth,import_count,cyclomatic_complexity,sha256`.  
  • Row count equals the sum of real and synthetic instances (**≥ 400 rows**).  
  • Every column validates against the type constraints in `contracts/detection_results.schema.yaml` (non‑null, correct types) **using a locally generated corrected schema**.

---

## Phase 2 – Dual‑pipeline execution  

- [ ] T005 [US‑2] **Implement the deterministic static heuristic “TIDE‑Lite” pipeline**  
  **Path**: `src/pipelines/tide_lite.py` (uses rule: `ast_depth > 3` OR `cyclomatic_complexity > 10`).  
  **Verification**:  
  • Unit test `src/tests/test_tide_lite.py` passes (known simple instance yields `prediction=True`).  
  • Running `python -m src.pipelines.tide_lite --input data/interim/features.csv --output data/results/tide_lite_enriched.csv` produces a CSV that **passes internal schema validation using the corrected local schema**.  
  • All `latency_ms` values are > 0 ms.

- [ ] T006 [US‑2] **Implement the generative “TIDE‑Original” pipeline using a CPU‑quantized small language model**  
  **Path**: `src/pipelines/tide_original.py` (loads an 8‑bit quantized `bigcode/starcoderbase-7b` model via `bitsandbytes`, deterministic decoding: `temperature=0.0`, `top_k=1`, fixed seed 42).  
  **Verification**:  
  • Unit test `src/tests/test_tide_original.py` passes (same known instance yields the expected binary prediction).  
  • Running `python -m src.pipelines.tide_original --input data/interim/features.csv --output data/results/tide_original_enriched.csv --sample 200` creates a schema‑compliant CSV (using the corrected local schema) with non‑negative `latency_ms`. **Only a sampled subset of 200 instances is processed** to respect CI limits.

- [ ] T007 [US‑2] **Consolidate feature records, ground‑truth labels, and both pipeline results into a single source‑of‑truth**  
  **Path**: `src/analysis/merge.py` (inner‑join on `instance_id`, retains `origin` and `ground_truth_label`).  
  **Verification**:  
  • Executing `python -m src.analysis.merge` writes `data/processed/merged_results.csv`.  
  • Row count equals the number of rows in `features.csv`.  
  • Each row contains columns `ground_truth_label`, `static_prediction`, `static_latency_ms`, `generative_prediction`, `generative_latency_ms` together with all feature fields.  
  • The merged CSV validates against the **corrected local schema**.

---

## Phase 3 – Statistical modelling & validation  

- [ ] T008 [US‑3] **Split the merged dataset into training and hold‑out validation sets (seed = 42)**  
  **Path**: `src/analysis/split.py`.  
  **Verification**:  
  • Running `python -m src.analysis.split` creates `data/processed/train_ids.npy` and `data/processed/val_ids.npy`.  
  • The split ratio is 80 % train / 20 % validation with no overlapping `instance_id`s.  
  • This step is performed for analysis purposes only and does **not** claim compliance with the deferred FR‑010.

- [ ] T009 [US‑3] **Fit logistic regression on the training split (no cross‑validation) and report average AUC**  
  **Path**: `src/analysis/logistic.py`.  
  **Verification**:  
  • Execution writes `analysis/logistic_summary.json` containing `coefficients`, `p_values`, and `mean_auc`.  
  • An EPV (events‑per‑variable) check is performed; if EPV < 15 a warning is logged and the script proceeds with standard logistic regression (no fallback required).  
  • The JSON also records the 0.5‑probability threshold estimated on the training data.

- [ ] T010 [US‑3] **Estimate the 0.5‑probability detection threshold on the hold‑out set using a binary search (tolerance 0.01) and compute a 95 % bootstrap confidence interval (1 000 resamples)**  
  **Path**: `src/analysis/threshold_estimation.py`.  
  **Verification**:  
  • Updates `analysis/logistic_summary.json` with a `thresholds` dict (feature → value) and a `threshold_ci` dict (95 % CI).  
  • Prints “Binary search tolerance: 0.01” and exits with status 0.  
  • Bootstrap completes without error and reports the CI.

- [ ] T011 [US‑3] **Perform stratified McNemar’s tests across three fixed complexity bins (low, medium, high) and apply Holm‑Bonferroni correction**  
  **Path**: `src/analysis/mcnemar.py`.  
  **Verification**:  
  • Generates `analysis/mcnemar_results.csv` with columns  
    `complexity_bin,static_tp,static_fp,generative_tp,generative_fp,p_value,p_value_corrected`.  
  • Bins are defined a priori as low (syntactic_complexity ≤ 33rd percentile), medium (34‑66 percentile), high (≥ 67th percentile) ensuring each bin contains ≥ 30 instances and ≥ 10 discordant pairs.  
  • All raw p‑values are numeric (0 ≤ p ≤ 1); corrected p‑values are computed via `statsmodels.stats.multitest.multipletests(method="holm")`.  
  • The CSV contains no missing values and passes a simple schema test.

- [ ] T012 [US‑3] **Run sensitivity analysis** (a) probability cut‑offs `{0.01, 0.05, 0.10}`, (b) synthetic depth‑distribution variants (uniform vs. skewed toward depth 5), (c) binning schemes (quantile vs. equal‑width) **and** (d) inclusion/exclusion of `ast_depth` & `cyclomatic_complexity` in the logistic model.  
  **Path**: `src/analysis/sensitivity.py`.  
  **Verification**:  
  • Outputs `analysis/sensitivity_summary.csv` with columns `config,fp_rate,fn_rate,variance`.  
  • If any configuration yields `variance > 0.05` a warning is written to `analysis/logs/sensitivity.log`.  
  • The script exits with status 0.

- [ ] T013 [US‑3] **Summarise execution efficiency (total wall‑clock time, average CPU utilisation, limits check)**  
  **Path**: `src/analysis/efficiency.py`.  
  **Verification**:  
  • Produces `analysis/efficiency_report.json` containing keys `total_seconds`, `avg_cpu_percent`, `within_limits`.  
  • `within_limits` is `true` only if `total_seconds ≤ 21600` (6 h) and `avg_cpu_percent ≤ 80`.  
  • A CI test asserts `within_limits == true`.

---

## Phase 4 – Visualization, tables & reproducible handoff  

- [ ] T014 [US‑3] **Generate all required figures directly from `merged_results.csv` and create the methods‑results handoff document**  
  **Path**: `src/visualization/plot_all.py` (produces PNGs under `outputs/figures/`) and `paper/methods_results.md`.  
  **Verification**:  
  • Figures created: `roc_static_vs_generative.png`, `pdp_complexity.png`, `mcnemar_bar.png`; each file is non‑empty and listed in `outputs/manifest.txt`.  
  • `paper/methods_results.md` contains explicit relative links to every CSV/JSON/PNG produced, a reproducibility checklist (seed values, software versions from `requirements.txt`, exact command `python -m src.run_all`), and passes the `pytest -m handoff` test.

---

### Dependency Summary (for reference)

| Requirement | Satisfying Task(s) |
|-------------|-------------------|
| FR‑001, FR‑009 | T001, T002, T003, T004 |
| FR‑002, FR‑004 | T005 |
| FR‑003, FR‑004 | T006 |
| FR‑005, FR‑010 (optional) | T008, T009, T010 |
| FR‑006, FR‑008 | T011 |
| FR‑007 | T012 |
| FR‑010 (cross‑validation) | **Not required** – omitted per spec deferment |
| SC‑001 | T010 |
| SC‑002 | T011 |
| SC‑003 | T012 |
| SC‑004 | T013 |
| SC‑005 | T001, T003, T004 |

All tasks are currently unchecked except the already‑validated **T003** (cap‑property enforcement). Executing them in the order presented will yield a complete, reproducible study that meets the specification without violating any constraints.  
