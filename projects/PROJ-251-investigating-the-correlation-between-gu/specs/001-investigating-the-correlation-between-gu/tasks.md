# Tasks: Investigating the Correlation Between Gut Microbiome Composition and Immune Response to Influenza Vaccination  

**Input**: `spec.md`, `plan.md`, existing research artifacts.  

**Goal**: Build a reproducible end‑to‑end analysis pipeline that (1) obtains a real or synthetic gut‑microbiome + serology dataset, (2) preprocesses it (filtering, normalization, CLR, diversity, log‑transformation), (3) performs Spearman correlation with Benjamini‑Hochberg correction, (4) trains a Random‑Forest classifier with nested 5‑fold cross‑validation while keeping feature‑selection inside each training fold, (5) checks all success criteria, and (6) produces a final report.  

All tasks are written in the canonical checklist format. Checked boxes (`[X]`) indicate work that has already passed verification and is retained; unchecked boxes (`[ ]`) are tasks that must be (re)implemented because the verifier rejected the previous attempt.

---

## Phase 0 – Data Search & Verification (Blocking Gate)

- [ ] **T010** [US1] **NCBI SRA / Hugging‑Face dataset search & verification**  
  *Path*: `code/download.py`, `data/research/sra_status.json`  
  *Action*:  
  1. Query the Hugging‑Face hub for a dataset containing paired 16S OTU tables and influenza serology (e.g., `datasets.load_dataset("influenza_microbiome", split="train", streaming=True)`).  
  2. If not found, fall back to NCBI E‑utilities with the query `"16S rRNA AND (influenza OR flu) AND (serology OR antibody OR titer) AND human"` and retrieve the first study that provides both data types.  
  3. Verify the presence of required columns (`subject_id`, taxon abundances, `titer_baseline`, `titer_post`).  
  4. Write `data/research/sra_status.json` with keys `status` (`real_data_found` | `no_real_data`), `use_synthetic` (bool), and `accession` or `hf_dataset_id`.  
  *Verification*: `python -c "import json; d=json.load(open('data/research/sra_status.json')); assert ('use_synthetic' in d) and ('status' in d)"`.

- [ ] **T011a** [US1] **Real‑data download script**  
  *Path*: `code/download.py` → `data/raw/otutable.csv`, `data/raw/serology.csv`  
  *Action*:  
  1. Read `config.SRA_ACCESSION` (or `config.HF_DATASET_ID`) from `code/utils/config.py`.  
  2. Download the OTU table (CSV/BIOM) and serology metadata, verifying checksums (SHA‑256).  
  3. Fail loudly (`raise RuntimeError`) if any download fails.  
  *Verification*: Existence of both CSV files and matching row counts on `subject_id`.

- [ ] **T011b** [US1] **Synthetic dataset generator (fallback)**  
  *Path*: `code/synthetic.py`, `data/raw/synthetic_otutable.csv`, `data/raw/synthetic_serology.csv`  
  *Action*:  
  1. Read configuration values `NUM_SYNTHETIC_TAXA`, `TARGET_CORRELATION`, `N_SUBJECTS` (default 50) from `code/utils/config.py`.  
  2. Generate a multivariate normal matrix with a block‑correlated structure so the first `NUM_SYNTHETIC_TAXA` taxa have Pearson ≈ `TARGET_CORRELATION` with a latent “titer” variable.  
  3. Convert to relative abundances (row‑wise sum = 1) and write `synthetic_otutable.csv` with columns `subject_id`, `taxon_0` … `taxon_{NUM_SYNTHETIC_TAXA‑1}`.  
  4. Generate serology values (`titer_baseline`, `titer_post`) by exponentiating the latent variable and adding log‑normal noise; write `synthetic_serology.csv`.  
  5. Seed the RNG with a fixed integer (`SEED=42`) for reproducibility.  
  *Verification*: Load both CSVs, assert shape `(N_SUBJECTS, NUM_SYNTHETIC_TAXA+1)` and non‑negative abundances that sum to 1 per row.

---

## Phase 1 – Project Setup & Quality Assurance

- [ ] **T001** [P] **Create project directory skeleton** (already verified).  
  *Path*: `code/`, `data/raw/`, `data/processed/`, `data/results/`, `tests/`, `data/research/`.

- [ ] **T002** [P] **Initialize Python 3.11 environment & pin dependencies** (already verified).  
  *Path*: `requirements.txt`.

- [ ] **T001a** [P] **Dataset schema definition**  
  *Path*: `specs/001-investigating-the-correlation-between-gu/contracts/dataset.schema.yaml`  
  *Content*: YAML schema requiring `subject_id` (string), `titer_baseline`, `titer_post` (numbers), `shannon_diversity`, `log_titer_pre`, `log_titer_post` (numbers), and allowing any number of additional numeric taxon columns via `additionalProperties`.  
  *Verification*: `python -c "import yaml, jsonschema; schema=yaml.safe_load(open('specs/001-investigating-the-correlation-between-gu/contracts/dataset.schema.yaml')); jsonschema.Draft7Validator(schema)"` succeeds.

- [ ] **T008a** [P] **`.env` template creation**  
  *Path*: `.env` (at repo root)  
  *Content*:  
  ```
  SRA_TOKEN=YOUR_TOKEN_HERE
  DATA_SOURCE_URL=YOUR_DATA_SOURCE_URL_HERE
  ```  
  *Verification*: `grep -q 'SRA_TOKEN' .env && grep -q 'DATA_SOURCE_URL' .env`.

- [ ] **T008b** [P] **Load `.env` into config module** (already verified).  
  *Path*: `code/utils/config.py`.

- [ ] **T039** [P] **Run linting & auto‑formatting, capture report**  
  *Path*: `data/results/lint_report.txt`  
  *Action*: Execute `ruff check code/ --output-format=full` and `black --check --diff code/`; redirect full stdout/stderr to the report file.  
  *Verification*: The report contains the line `Exit code: 0`; any non‑zero code fails the task.

---

## Phase 2 – Ingestion & Pre‑processing (Immutable Derivation Chain)

> Each step writes a **new** CSV file so that downstream tasks never modify a predecessor.

- [ ] **T011c** [P] **Sampling utility (stratified by baseline titer)**  
  *Path*: `code/utils/sampling.py`  
  *Function*: `stratified_sample(df: pd.DataFrame, target_col: str, retain_ratio: float, seed: int = 42) -> pd.DataFrame`.  
  *Verification*: Import the function and run a quick sanity check in a unit test (`tests/test_sampling.py`).

- [ ] **T011d** [US1] **Merge OTU & serology, filter for complete records**  
  *Input*: `data/raw/otutable.csv` | `data/raw/serology.csv` **or** synthetic equivalents.  
  *Output*: `data/processed/cleared.csv`  
  *Action*:  
  1. Load both CSVs, inner‑join on `subject_id`.  
  2. Drop any rows where `titer_baseline` or `titer_post` is missing (`NaN`).  
  3. Log the number of excluded subjects to `data/results/ingestion_log.txt`.  
  4. If the resulting `N < 50` **and** `config.USE_SYNTHETIC_DATA` is `False`, write `data/results/sampling_error.json` with an `"InsufficientSampleSize"` error and exit with status 1 (blocking further tasks).  
  5. Otherwise write the filtered dataset to `cleared.csv`.  
  *Verification*: `python -c "import pandas as pd; df=pd.read_csv('data/processed/cleared.csv'); assert len(df)>=50 or open('data/results/sampling_error.json')"`.

- [ ] **T020b** [US1] **Row‑wise relative abundance normalization**  
  *Input*: `data/processed/cleared.csv`  
  *Output*: `data/processed/cleared_norm.csv`  
  *Action*: Divide each taxon column by the row sum (excluding non‑taxon columns).  
  *Verification*: For every row, `abs(df[taxon_cols].sum(axis=1) - 1.0) < 1e-6`.

- [ ] **T020c** [US1] **Shannon diversity calculation**  
  *Input*: `data/processed/cleared_norm.csv`  
  *Output*: `data/processed/cleared_shannon.csv` (adds column `shannon_diversity`).  
  *Verification*: Compute `-∑ p_i log(p_i)` per row and assert the column exists and contains non‑negative floats.

- [ ] **T021** [US1] **Log‑transform titers & LOD handling**  
  *Input*: `data/processed/cleared_norm.csv`  
  *Output*: `data/processed/cleared_log.csv` (adds `log_titer_baseline`, `log_titer_post`).  
  *Action*:  
  1. Load `config.LOD_VALUE` from `.env`. If `None`, raise `ConfigurationError`.  
  2. Replace any titer ≤ `LOD_VALUE` with `0.5 * LOD_VALUE`.  
  3. Apply natural log (`np.log`) to the cleaned titers.  
  *Verification*: All values in the new columns are finite (`np.isfinite`) and no entry equals the raw LOD.

- [ ] **T020a-1** [US1] **Merge normalized, diversity, and log‑transformed tables**  
  *Inputs*: `cleared_norm.csv`, `cleared_shannon.csv`, `cleared_log.csv`  
  *Output*: `data/processed/cleared_merged.csv` (single table containing taxon relative abundances, `shannon_diversity`, and log‑titer columns).  
  *Verification*: Row count identical across inputs; a single CSV file exists.

- [ ] **T061** [V] **Record SHA‑256 hash for `cleared_merged.csv`**  
  *Input*: `data/processed/cleared_merged.csv`  
  *Output*: `data/results/manifest.json` (adds entry `"cleared_merged.csv": "<sha256>"`).  
  *Verification*: The manifest file contains a 64‑character hex string for the key.

- [ ] **T020a-2** [US1] **Zero‑replacement before CLR**  
  *Input*: `cleared_merged.csv`  
  *Output*: `data/processed/cleared_zero_replaced.csv` (adds a tiny pseudo‑count `1e-6` to any zero taxon abundance).  
  *Verification*: No taxon column contains a literal zero.

- [ ] **T062** [V] **Record SHA‑256 hash for `cleared_zero_replaced.csv`**  
  *Input*: `data/processed/cleared_zero_replaced.csv`  
  *Output*: `data/results/manifest.json` (adds entry `"cleared_zero_replaced.csv": "<sha256>"`).  
  *Verification*: Manifest updated with a valid hash.

- [ ] **T020a-3** [US1] **Centered Log‑Ratio (CLR) transformation**  
  *Input*: `cleared_zero_replaced.csv`  
  *Output*: `data/processed/cleared_final.csv` (adds CLR columns `taxon_{i}_clr`).  
  *Verification*: For each subject, the geometric mean of CLR‑transformed taxa is ≈ 0 (within `1e-6`).

- [ ] **T063** [V] **Record SHA‑256 hash for `cleared_final.csv`**  
  *Input*: `data/processed/cleared_final.csv`  
  *Output*: `data/results/manifest.json` (adds entry `"cleared_final.csv": "<sha256>"`).  
  *Verification*: Manifest contains a valid hash entry.

- [ ] **T013** [US1] **Validate final processed table against schema**  
  *Input*: `cleared_final.csv`, `contracts/dataset.schema.yaml`  
  *Output*: `data/results/schema_validation_report.json` (JSON report from `jsonschema.validate`).  
  *Verification*: The report contains `"valid": true`.

---

## Phase 3 – Correlation Analysis & Feature Selection

- [ ] **T032a** [US2] **Global variance filter (remove zero‑variance taxa)**  
  *Input*: `cleared_final.csv`  
  *Output*: `data/results/variance_filtered_taxa.json` (list of retained taxon names).  
  *Action*: Compute variance across subjects for each CLR taxon; drop those with variance < 1e‑9. If none remain, raise `NoFeaturesError`.  
  *Verification*: The JSON list is non‑empty.

- [ ] **T032** [US2] **Spearman correlation + Benjamini‑Hochberg correction**  
  *Inputs*: `cleared_final.csv`, `variance_filtered_taxa.json`  
  *Output*: `data/results/correlation_results.json` and `data/results/correlation_results.csv`.  
  *Action*:  
  1. For each retained taxon, compute Spearman ρ with `log_titer_post`.  
  2. Collect raw p‑values, apply BH correction (`statsmodels.stats.multitest.multipletests`).  
  3. Store `taxon`, `spearman_rho`, `p_raw`, `p_adj` in JSON and CSV.  
  *Verification*: CSV contains a header row and at least one taxon entry; p‑values are between 0 and 1.

- [ ] **T032b_model** [US3] **Feature‑selection function for inner loop**  
  *Path*: `code/modeling.py` → `select_features_inner_loop(train_X, train_y) -> List[str]`.  
  *Action*: Within the training fold, (a) drop zero‑variance taxa, (b) compute Spearman correlations with `train_y`, (c) BH‑adjust, (d) return taxa with `p_adj < 0.05`; if none pass, return **all** variance‑filtered taxa (ensuring a non‑empty list).  
  *Verification*: Unit test (`tests/test_modeling.py::test_inner_feature_selection_isolation`) asserts the returned list is non‑empty and that the function does not read global `correlation_results.json`.

- [ ] **T025** [US2] **Log count of significant taxa (SC‑004)**  
  *Input*: `correlation_results.json`  
  *Output*: `data/results/sc004_report.json`  
  *Action*:  
  1. Count taxa with `p_adj < 0.05`.  
  2. If `config.USE_SYNTHETIC_DATA` is `False` (real data) and count is outside the expected range [1, 9], write a warning entry; otherwise write a normal report.  
  *Verification*: The JSON contains keys `status`, `count`, and `within_range` (bool).

---

## Phase 4 – Predictive Modeling (Nested Cross‑Validation)

- [ ] **T030d** [US3] **Define responder status & generate label files**  
  *Input*: `cleared_final.csv`  
  *Outputs*: `data/processed/responder_labels.csv` (columns `subject_id`, `responder_status`), plus additional files for each threshold sweep (`responder_labels_thr_{i}.csv`).  
  *Action*:  
  1. Default responder = seroconversion (`titer_post >= 4 * titer_baseline`).  
  2. Also generate absolute‑titer responder (`titer_post >= 40`).  
  3. Perform a ±10 % sweep around each definition and write separate label files.  
  *Verification*: Each label file contains exactly the same `subject_id` set as `cleared_final.csv` and a binary `responder_status` column.

- [ ] **T034d-1** [US3] **Generate outer folds for each responder‑threshold**  
  *Inputs*: `responder_labels_thr_{i}.csv`  
  *Outputs*: `data/results/folds_thr_{i}.json` (list of 5 subject‑ID lists).  
  *Action*: Use `sklearn.model_selection.StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)` on the binary labels for each threshold file. Store folds per threshold.  
  *Verification*: Each JSON contains exactly 5 lists whose union equals the full subject set and are disjoint.

- [ ] **T034d-2** [US3] **Inner‑loop feature selection & logging**  
  *Inputs*: `cleared_final.csv`, `folds_thr_{i}.json`, `modeling.select_features_inner_loop`.  
  *Output*: `data/results/feature_selection_log_thr_{i}.json` (mapping `fold_index → selected_taxa`).  
  *Verification*: For each fold, the listed taxa are a subset of the variance‑filtered set and the file is valid JSON.

- [ ] **T034d-3** [US3] **Train & evaluate Random Forest per fold/threshold**  
  *Inputs*: `cleared_final.csv`, `responder_labels_thr_{i}.csv`, fold definitions, selected features.  
  *Output*: `data/results/predictions_thr_{i}.json` (per‑subject predicted probability and class).  
  *Action*:  
  1. For each outer fold, train `sklearn.ensemble.RandomForestClassifier(n_estimators=200, random_state=SEED)` on the training split using only the inner‑selected features.  
  2. Predict on the held‑out fold; store true and predicted labels.  
  *Verification*: Each prediction record contains `subject_id`, `true_label`, `pred_label`, `pred_proba`.

- [ ] **T034d-4** [US3] **Aggregate metrics across folds & thresholds**  
  *Input*: `predictions_thr_*.json`  
  *Output*: `data/results/model_metrics.json` (JSON with `mean_accuracy`, `std_accuracy`, `precision`, `recall`, `f1`, `thresholds_tested`, `meets_accuracy_target`).  
  *Verification*: The JSON includes numeric fields; `meets_accuracy_target` is set to `True` **iff** `mean_accuracy >= 0.60` (the spec threshold) and the evaluation was performed on real data (`config.USE_SYNTHETIC_DATA` is `False`).  

- [ ] **T036a** [US3] **Compute confusion matrices & per‑threshold detailed metrics**  
  *Input*: `predictions_thr_*.json`  
  *Output*: `data/results/confusion_matrices.json` (nested dict `threshold → {tp, fp, tn, fn, precision, recall, f1}`) and update `model_metrics.json` with the same values.  
  *Verification*: Each matrix sums to the number of subjects for that threshold.

- [ ] **T036b** [US3] **Success‑criterion check (SC‑003 > 60 % accuracy)**  
  *Input*: `model_metrics.json`  
  *Action*: Set `meets_accuracy_target` to `True` if `mean_accuracy >= 0.60`; otherwise `False`.  
  *Verification*: The flag in the JSON matches the numeric comparison (already enforced in T034d-4).

- [ ] **T037** [US3] **Write final model‑metrics artifact** (already covered by T034d‑4 but retained for explicit hand‑off).  
  *Path*: `data/results/model_metrics.json` (validated in previous step).

- [ ] **T038** [US3] **Validate model‑metrics against schema**  
  *Path*: `specs/001-investigating-the-correlation-between-gu/contracts/model_metrics.schema.yaml` → `data/results/model_metrics_validation.json`.  
  *Action*: Use `jsonschema.validate`; write a validation report.  
  *Verification*: Report contains `"valid": true`.

---

## Phase 5 – Validation, Reporting & Cross‑Cutting Concerns

- [ ] **T045** [US3] **Generate final report**  
  *Inputs*: All result files (`cleared_final.csv`, `correlation_results.csv`, `model_metrics.json`, `assumptions.md`, `sc004_report.json`).  
  *Output*: `data/results/final_report.md`.  
  *Structure*: Sections “Data Overview”, “Pre‑processing Summary”, “Correlation Results”, “Model Performance”, “Sensitivity Analysis”, “Assumptions & Limitations”, and “Conclusion”. **Each section explicitly cites the file path of the underlying artifact** (e.g., “see `data/processed/cleared_final.csv`”).  
  *Verification*: The markdown file exists, contains the required headings, and every section includes a line of the form `Source: <path>` referencing the relevant artifact.

- [ ] **T040a** [P] **Unit test – zero‑variance taxa exclusion** (`tests/test_preprocess.py::test_zero_variance_taxa_exclusion`).  
- [ ] **T040b** [P] **Unit test – LOD handling logic** (`tests/test_ingest.py::test_lod_handling`).  
- [ ] **T040c** [P] **Unit test – CLR pseudo‑count edge cases** (`tests/test_correlation.py::test_clr_pseudocount_extremes`).  
- [ ] **T041** [P] **Validate quickstart documentation** (`quickstart.md` points to the command `python -m code.main_pipeline`).  
- [ ] **T042a** [P] **Pre‑planned stratified sampling for large datasets** (optional, runs before the main pipeline if `data/processed/cleared.csv` exceeds 5 GB). Produces `data/processed/cleared_sampled.csv`.  
- [ ] **T042** [P] **Resource‑usage monitoring** (integrated into `code/main_pipeline.py`; writes `data/results/resource_usage.json`).  
- [ ] **T056** [US3] **Document sampling strategy & limitations** (`data/results/sampling_report.md`).  
- [ ] **T057** [US3] **Test that feature‑selection is isolated per fold** (`tests/test_modeling.py::test_feature_selection_isolation_in_nested_cv`).  
- [ ] **T058** [US3] **Test that threshold sweep correctly regenerates folds** (`tests/test_modeling.py::test_threshold_sweep_folds`).

---

## Phase 6 – Runtime & Versioning Enforcement

- [ ] **T059** [SC‑005] **Measure total pipeline runtime and enforce < 2 h**  
  *Action*: At the start of `code/main_pipeline.py` record `time.time()`. At the end, compute elapsed seconds, write `data/results/runtime_report.json` with fields `elapsed_seconds` and `within_limit` (boolean true if `< 7200`).  
  *Verification*: The JSON `within_limit` must be `true`; CI fails otherwise.

- [ ] **T060** **Generate data‑model documentation**  
  *Path*: `specs/001-investigating-the-correlation-between-gu/data-model.md`  
  *Action*: Auto‑generate a markdown summary of the processed data schema (columns, types, derived fields) from `dataset.schema.yaml`.  
  *Verification*: File exists and contains a table listing every column defined in the schema.

- [ ] **T061‑T063** (see above) **Content‑hash manifest generation** – already checked.
