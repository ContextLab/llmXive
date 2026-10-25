# Tasks: Investigating the Correlation Between Gut Microbiome Composition and Immune Response to Influenza Vaccination  

**Input**: `spec.md`, `plan.md`, existing research artifacts.  

The checklist below follows the canonical format `- [ ] T### [P?] [USx?] description with file path`.  
Checked boxes (`[X]`) denote work that has already passed verification and is retained.  
Unchecked boxes (`[ ]`) indicate tasks that must be (re)implemented or completed.  
Each task includes indented continuation lines that specify the concrete output artifact(s) and the verification command(s) the verifier will run.

---

## Phase 0 – Data Search & Verification (Blocking Gate)

- [ ] T010 [US1] **Discover and verify a real paired microbiome‑serology dataset** <!-- FAILED-IN-EXECUTION: code/download.py exit=1 -->
  *Path*: `code/download.py`, `data/research/sra_status.json`  
  *Action*:  
  1. Query Hugging‑Face (`datasets.load_dataset("influenza_microbiome", split="train", streaming=True)`) and, if needed, NCBI E‑utilities for studies containing 16S OTU tables **and** influenza serology.  
  2. Confirm required columns (`subject_id`, taxon abundances, `titer_baseline`, `titer_post`).  
  3. Write `data/research/sra_status.json` with keys `status` (`real_data_found` | `no_real_data`), `use_synthetic` (bool), and `accession` or `hf_dataset_id`.  
  *Verification*:  
  ```bash
  python -c "import json; d=json.load(open('data/research/sra_status.json')); assert 'status' in d and 'use_synthetic' in d"
  ```

- [ ] T011a [US1] **Real‑data download script**   <!-- FAILED-IN-EXECUTION: code/download.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/download.py exit=1 -->
  *Path*: `code/download.py` → `data/raw/otutable.csv`, `data/raw/serology.csv`  
  *Action*:  
  1. Read `config.SRA_ACCESSION` or `config.HF_DATASET_ID` from `code/utils/config.py`.  
  2. Download the OTU table (CSV/BIOM) and serology metadata, verify SHA‑256 checksums.  
  3. `raise RuntimeError` on any download failure (no silent fallback).  
  *Verification*:  
  ```bash
  test -s data/raw/otutable.csv && test -s data/raw/serology.csv
  ```

- [ ] T011b [US1] **Synthetic dataset generator (fallback)**  
  *Path*: `code/synthetic.py`, `data/raw/synthetic_otutable.csv`, `data/raw/synthetic_serology.csv`  
  *Action*:  
  1. Read `NUM_SYNTHETIC_TAXA`, `TARGET_CORRELATION`, `N_SUBJECTS` (default 50) from `code/utils/config.py`.  
  2. Generate a multivariate normal matrix with a block‑correlated structure so the first `NUM_SYNTHETIC_TAXA` taxa have Pearson ≈ `TARGET_CORRELATION` with a latent “titer” variable.  
  3. Convert rows to relative abundances (sum = 1) and write `synthetic_otutable.csv` (`subject_id`, `taxon_0` …).  
  4. Generate serology values by exponentiating the latent variable, add log‑normal noise, and write `synthetic_serology.csv` (`subject_id`, `titer_baseline`, `titer_post`).  
  5. Seed RNG with `SEED=42` for reproducibility.  
  *Verification*:  
  ```bash
  python -c "import pandas as pd; df=pd.read_csv('data/raw/synthetic_otutable.csv'); assert df.shape[0]>=50 and (df.iloc[:,1:]>0).all().all()"
  ```

- [ ] T011c [US1] **Stratified sampling utility (for large datasets)**  
  *Path*: `code/utils/sampling.py` → function `stratified_sample(df, target_col, retain_ratio, seed=42)`  
  *Action*: Implement a helper that samples rows proportionally to the distribution of `target_col` (e.g., baseline titer) while preserving the overall subject count.  
  *Verification*:  
  ```bash
  python - <<'PY'
  import pandas as pd, code.utils.sampling as s
  df=pd.DataFrame({'subject_id':range(100), 'titer_pre':list(range(100))})
  sample=s.stratified_sample(df, 'titer_pre', 0.5)
  assert len(sample)==50
  PY
  ```

---

## Phase 1 – Project Setup & Quality Assurance

- [ ] T001 [P] **Create project directory skeleton** (already verified)  
  *Path*: `code/`, `data/raw/`, `data/processed/`, `data/results/`, `tests/`, `data/research/`.

- [ ] T001s [P] **Pin global random seeds for reproducibility**  
  *Path*: `code/seed.py` (creates `set_seeds()` function) and updates all scripts to call it at start.  
  *Action*:  
  1. Define `set_seeds(seed=42)` that sets `numpy`, `random`, and `torch` (if installed) seeds.  
  2. Add import and call to `set_seeds()` in every entry‑point script (`download.py`, `ingestion.py`, `preprocessing.py`, `analysis.py`, `modeling.py`, `main_pipeline.py`).  
  *Verification*:  
  ```bash
  python -c "import importlib; mod=importlib.import_module('code.seed'); assert hasattr(mod, 'set_seeds')"
  ```

- [ ] T002 [P] **Initialize Python 3.11 environment & pin dependencies** (already verified)  
  *Path*: `requirements.txt`.

- [ ] T039 [P] **Run linting & auto‑formatting, capture report** (already verified)  
  *Path*: `data/results/lint_report.txt`  
  *Verification*: The report contains the line `Exit code: 0`.

---

## Phase 2 – Ingestion & Pre‑processing (Immutable Derivation Chain)

- [ ] T011d [US1] **Merge OTU & serology, filter for complete records**  
  *Inputs*: `data/raw/otutable.csv` | `data/raw/serology.csv` **or** synthetic equivalents.  
  *Output*: `data/processed/cleared.csv`  
  *Action*:  
  1. Load both CSVs, inner‑join on `subject_id`.  
  2. Drop rows with missing `titer_baseline` or `titer_post`.  
  3. Log number of excluded subjects to `data/results/ingestion_log.txt`.  
  4. If resulting `N < 50` and `config.USE_SYNTHETIC_DATA` is `False`, write `data/results/sampling_error.json` with `"InsufficientSampleSize"` and exit with status 1 (blocking downstream tasks).  
  5. Write the filtered dataset to `cleared.csv`.  
  *Verification*:  
  ```bash
  python -c "import pandas as pd, json, sys; df=pd.read_csv('data/processed/cleared.csv'); assert len(df)>=50 or json.load(open('data/results/sampling_error.json'))"
  ```

- [ ] T011e [US1] **Record SHA‑256 checksums of raw data files**  
  *Inputs*: `data/raw/otutable.csv`, `data/raw/serology.csv` (or synthetic equivalents).  
  *Output*: `data/checksums/raw_files_checksums.json`  
  *Action*: Compute SHA‑256 for each raw file and write a JSON mapping `{filename: checksum}`.  
  *Verification*:  
  ```bash
  python -c "import json, hashlib, pathlib; d=json.load(open('data/checksums/raw_files_checksums.json')); assert all(pathlib.Path(f).exists() for f in d)"
  ```

- [ ] T020c [US1] **Shannon Diversity Calculation**  
  *Input*: `data/processed/cleared.csv`  
  *Output*: `data/processed/cleared_shannon.csv` (adds `shannon_diversity` column)  
  *Action*: Compute Shannon index for each subject using microbiome abundance columns and append as a new column.  
  *Verification*:  
  ```bash
  python -c "import pandas as pd; df=pd.read_csv('data/processed/cleared_shannon.csv'); assert 'shannon_diversity' in df.columns and (df['shannon_diversity']>=0).all()"
  ```

- [ ] T021 [US1] **Log‑Transform Titers & LOD Handling**  
  *Input*: `data/processed/cleared_shannon.csv`  
  *Output*: `data/processed/cleared_log.csv` (adds `titer_pre_log`, `titer_post_log`)  
  *Action*:  
  1. Identify limit‑of‑detection (LOD) for each titer column (assumed provided in config).  
  2. Replace values below LOD with `0.5 * LOD`.  
  3. Apply natural log transform to baseline and post‑vaccination titers, storing results in new columns.  
  *Verification*:  
  ```bash
  python -c "import pandas as pd, numpy as np; df=pd.read_csv('data/processed/cleared_log.csv'); assert np.isfinite(df['titer_pre_log']).all() and np.isfinite(df['titer_post_log']).all()"
  ```

- [ ] T020a [US1] **CLR Transformation**  
  *Input*: `data/processed/cleared_log.csv`  
  *Output*: `data/processed/cleared_final.csv` (adds `taxon_X_clr` columns)  
  *Action*:  
  1. Add a small pseudo‑count (1e‑6) to all zero abundances.  
  2. Perform Centered Log‑Ratio transformation on all taxon abundance columns.  
  3. Append CLR‑transformed columns with suffix `_clr`.  
  *Verification*:  
  ```bash
  python - <<'PY'
  import pandas as pd, numpy as np
  df=pd.read_csv('data/processed/cleared_final.csv')
  clr_cols=[c for c in df.columns if c.endswith('_clr')]
  means=np.mean(df[clr_cols], axis=0)
  assert np.allclose(means, 0, atol=1e-6)
  PY
  ```

- [ ] T013 [US1] **Validate `cleared_final.csv` against the dataset schema**  
  *Input*: `data/processed/cleared_final.csv`, `specs/001-investigating-the-correlation-between-gu/contracts/dataset.schema.yaml`  
  *Output*: `data/results/schema_validation_report.json`  
  *Action*: Use `jsonschema.validate` (via a small helper script) to check each row against the schema; write a JSON report with keys `valid` (bool) and `errors` (list).  
  *Verification*:  
  ```bash
  python -c "import json; report=json.load(open('data/results/schema_validation_report.json')); assert report.get('valid') is True"
  ```

---

## Phase 3 – Correlation Analysis & Feature Selection

- [ ] T032 [US2] **Correlation analysis with variance filter, Spearman test, and Benjamini‑Hochberg correction**  
  *Inputs*: `data/processed/cleared_final.csv` (CLR taxa), `data/results/variance_filtered_taxa.json` (generated inside this task).  
  *Outputs*:  
  - `data/results/variance_filtered_taxa.json` (list of retained taxon names)  
  - `data/results/correlation_results.json` (list of objects matching `CorrelationResult` schema)  
  - `data/results/correlation_results.csv` (human‑readable table)  
  *Action*:  
  1. Compute variance of each CLR taxon; drop those with variance < 1e‑9.  
  2. For each retained taxon, compute Spearman ρ with `titer_post_log`.  
  3. Apply Benjamini‑Hochberg (`statsmodels.stats.multitest.multipletests`) to raw p‑values.  
  4. Write results in JSON and CSV.  
  *Verification*:  
  ```bash
  python -c "import json, pandas as pd; corr=json.load(open('data/results/correlation_results.json')); assert len(corr)>0 and all(0<=c['p_value_adj']<=1 for c in corr)"
  head data/results/correlation_results.csv
  ```

- [ ] T032b_model [US3] **Inner‑loop feature‑selection function for modeling**  
  *Path*: `code/modeling.py` → `select_features_inner_loop(train_X, train_y) -> List[str]`  
  *Action*: Within the training fold, (a) drop zero‑variance CLR taxa, (b) compute Spearman correlation of each taxon with `train_y`, (c) BH‑adjust, (d) **return only taxa with `p_adj < 0.05`**; if *no* taxa meet this criterion the task **fails** (raises an exception) to enforce the requirement of using top‑correlated features.  
  *Verification*: Unit test `tests/test_modeling.py::test_inner_feature_selection_isolation` asserts the function reads only the provided `train_X`/`train_y` and raises when the result would be empty.

- [ ] T025 [US2] **Log count of significant taxa (SC‑004) and enforce expected range**  
  *Input*: `data/results/correlation_results.json`  
  *Output*: `data/results/sc004_report.json`  
  *Action*:  
  1. Count taxa with `p_adj < 0.05`.  
  2. If real data (`config.USE_SYNTHETIC_DATA` = False) and count not in `[1,9]`, set `"within_range": false` and include a warning; otherwise `"within_range": true`.  
  *Verification*:  
  ```bash
  python -c "import json; r=json.load(open('data/results/sc004_report.json')); assert 'count' in r and 'within_range' in r"
  ```

---

## Phase 4 – Predictive Modeling (Nested Cross‑Validation)

- [ ] T030d [US3] **Define responder status and generate label files for threshold sweep**  
  *Input*: `data/processed/cleared_final.csv`  
  *Outputs*:  
  - `data/processed/responder_labels_default.csv` (baseline definition)  
  - `data/processed/responder_labels_thr_{i}.csv` for each threshold (±10 % around baseline and absolute‑titer cut‑offs)  
  *Action*:  
  1. Default responder = seroconversion (`titer_post >= 4 * titer_pre`).  
  2. Also generate absolute‑titer responder (`titer_post >= 40`).  
  3. For each definition, create three thresholds: baseline × 0.9, baseline, baseline × 1.1.  
  *Verification*: Each label file has the same `subject_id` set as `cleared_final.csv` and a binary `responder_status` column.

- [ ] T034d [US3] **Nested 5‑fold cross‑validation Random Forest training, evaluation, and metric aggregation**  
  *Inputs*: `data/processed/cleared_final.csv`, all responder label files from T030d, `code/modeling.py` (including `select_features_inner_loop`).  
  *Outputs*:  
  - `data/results/folds_thr_{i}.json` (outer‑fold subject ID splits)  
  - `data/results/feature_selection_log_thr_{i}.json` (selected taxa per outer fold)  
  - `data/results/predictions_thr_{i}.json` (true/predicted labels & probabilities per subject)  
  - `data/results/model_metrics.json` (mean/std accuracy, precision, recall, F1, per‑threshold accuracies, `meets_accuracy_target` flag)  
  - `data/results/confusion_matrices.json` (TP/FP/TN/FN and derived metrics per threshold)  
  *Action*: For each threshold file:  
  1. Generate outer stratified 5‑fold splits (`StratifiedKFold`).  
  2. Within each outer training split, call `select_features_inner_loop` on the inner‑training data to obtain the feature set.  
  3. Train `RandomForestClassifier(n_estimators=200, random_state=42)` on those features, predict on the outer test split.  
  4. Store predictions, compute per‑fold metrics, and aggregate across folds.  
  5. After all thresholds, compute overall mean accuracy; set `"meets_accuracy_target": true` iff `mean_accuracy >= 0.60` **and** real data is used.  
  *Verification*:  
  ```bash
  python -c "import json; m=json.load(open('data/results/model_metrics.json')); assert 'mean_accuracy' in m and 'meets_accuracy_target' in m"
  ```

- [ ] T036a [US3] **Compute confusion matrices and detailed per‑threshold metrics**  
  *Input*: `data/results/predictions_thr_*.json`  
  *Output*: `data/results/confusion_matrices.json` (nested dict `threshold → {tp, fp, tn, fn, precision, recall, f1}`) – also merged into `model_metrics.json`.  
  *Verification*:  
  ```bash
  python -c "import json; cm=json.load(open('data/results/confusion_matrices.json')); assert isinstance(cm, dict) and all('tp' in v for v in cm.values())"
  ```

- [ ] T036b [US3] **Success‑criterion check for SC‑003 (> 60 % accuracy)**  
  *Input*: `data/results/model_metrics.json`  
  *Action*: Ensure the field `"meets_accuracy_target"` correctly reflects whether `mean_accuracy >= 0.60`.  
  *Verification*: Same as in T034d verification; the flag must be `True` only when the numeric condition holds.

- [ ] T037 [US3] **Write final model‑metrics artifact** (explicit hand‑off)  
  *Path*: `data/results/model_metrics.json` (produced by T034d).  
  *Verification*: File exists, is valid JSON, and passes schema validation (see T038).

- [ ] T038 [US3] **Validate `model_metrics.json` against the ModelPerformance schema**  
  *Input*: `data/results/model_metrics.json`, `specs/001-investigating-the-correlation-between-gu/contracts/model.schema.yaml`  
  *Output*: `data/results/model_metrics_validation.json` (report with `valid` flag).  
  *Verification*:  
  ```bash
  python -c "import json; r=json.load(open('data/results/model_metrics_validation.json')); assert r.get('valid') is True"
  ```

---

## Phase 5 – Reporting & Runtime Enforcement

- [ ] T059 [US3] **Measure total pipeline runtime and enforce < 2 h**  
  *Path*: `code/main_pipeline.py` (adds timing logic) → `data/results/runtime_report.json`  
  *Action*: Record start time, compute elapsed seconds at the end, write JSON with fields `elapsed_seconds` (float) and `within_limit` (bool, true if `< 7200`).  
  *Verification*:  
  ```bash
  python -c "import json; r=json.load(open('data/results/runtime_report.json')); assert r['within_limit'] is True"
  ```

- [ ] T045 [US3] **Generate final markdown report**  
  *Inputs*: All result artifacts (`cleared_final.csv`, `correlation_results.csv`, `model_metrics.json`, `sc004_report.json`, `confusion_matrices.json`, `runtime_report.json`).  
  *Output*: `data/results/final_report.md` with sections:  
  1. Data Overview (source & size) – cites `data/processed/cleared_final.csv`  
  2. Pre‑processing Summary – cites `data/processed/cleared_final.csv`  
  3. Correlation Results – cites `data/results/correlation_results.csv`  
  4. Model Performance – cites `data/results/model_metrics.json` and confusion matrices  
  5. Sensitivity Analysis – cites threshold‑specific files  
  6. Assumptions & Limitations – cites `specs/001-investigating-the-correlation-between-gu/spec.md`  
  7. Conclusion – ties back to the research question.  
  *Verification*: File exists, contains the required headings, and each heading is followed by a line `Source: <path>` referencing the appropriate artifact.
