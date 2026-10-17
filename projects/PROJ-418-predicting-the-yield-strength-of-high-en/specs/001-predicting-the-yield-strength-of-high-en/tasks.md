---
# Tasks: Predicting the Yield Strength of High‑Entropy Alloys

**Inputs**: `spec.md`, `plan.md`, existing code and data artifacts, JSON‑schema contracts in `contracts/`.  
**Goal**: End‑to‑end, reproducible pipeline that downloads real HEA data, computes composition‑only descriptors, trains a composition‑only predictor, validates it against an independent test set, and produces a fully provenance‑tracked markdown report satisfying all functional requirements (FR‑001‑FR‑024) and success criteria (SC‑001‑SC‑011).

---

## Phase 0 – Project scaffolding (already completed)

- [ ] **T001a** Create directory structure: `code/`, `data/raw/`, `data/processed/`, `output/`, `tests/`, `output/plots/`.  
- [ ] **T001b** Add `__init__.py` files to all `code/` and `tests/` sub‑directories.  
- [ ] **T001c** Create `requirements.txt` (pinned versions) and top‑level `README.md`.  
- [ ] **T004** Setup deterministic logging and random‑seed management in `code/utils/logging.py`.  

---

## Phase 1 – Data acquisition (primary HEA dataset)

- [ ] **T008** [FR-001] Download the curated HEA yield‑strength dataset from the Zenodo archive (URL specified in the spec).  
  - **Implementation**: `code/data/download.py` uses `requests` to fetch the CSV/JSON and writes `data/raw/heas_raw.csv`.  
  - **Verification**:  
    - `data/raw/heas_raw.csv` exists.  
    - Validate against `contracts/dataset.schema.yaml`; on failure raise a `ValidationError`.  

- [ ] **T060** Compute SHA‑256 checksum of `data/raw/heas_raw.csv` and record it in the provenance manifest (`output/manifest.json`).  
  - **Implementation**: `code/utils/checksum.py`.  
  - **Verification**:  
    - `output/manifest.json.checksums["heas_raw.csv"]` matches the computed hash.  
    - If mismatch → abort with informative error (distinguish missing vs corrupted file).  

---

## Phase 2 – Elemental property loading & descriptor engineering

- [ ] **T005** Create schema‑validation utilities in `code/data/__init__.py` for all contracts.  
- [ ] **T006** Implement `normalize_to_mpa` in `code/utils/unit_utils.py` (handles GPa→MPa, missing/invalid units).  
- [ ] **T007** Add `code/utils/config.py` containing `DATASET_URLS` with the verified Zenodo URLs (no fallback).  
- [ ] **T011** Load elemental property table from the verified Hugging Face dataset `MaterialsProject/elemental_properties`. Validate against `contracts/elemental_properties.schema.yaml`.  
- [ ] **T012** Implement descriptor calculator (`mixing_entropy`, `atomic_size_mismatch`, `electronegativity_variance`, `vec`, `tm_variance`) in `code/data/descriptors.py`.  
- [ ] **T200** Generate the processed descriptor matrix (composition + six descriptors) and write `data/processed/hea_descriptors.csv`.  
  - **Implementation**:  
    1. Load `data/raw/heas_raw.csv` → preprocess (filter single‑phase, room‑temp, missing fields → abort per FR‑009).  
    2. Compute descriptors via `code/data/descriptors.py`.  
    3. Save final descriptor table (`composition`, six descriptors) as CSV.  
  - **Verification**:  
    - File exists and validates against `contracts/descriptor.schema.yaml`.  

- [ ] **T022** [FR-016] After the train‑test split (see T016), compute Variance Inflation Factor (VIF) on the *training* descriptor matrix, drop any descriptor with VIF > 5, and write the cleaned training matrix `data/processed/train_clean.parquet`. Record VIF values and removals in `output/vif_summary.json`.  
  - **Verification**:  
    - `output/vif_summary.json` exists and conforms to a simple VIF schema.  
    - Cleaned training file `data/processed/train_clean.parquet` exists.  

---

## Phase 3 – Statistical power analysis

- [ ] **T145** Perform power analysis (target power ≥ 0.80, α = 0.05, effect size derived from R² ≥ 0.6) using `statsmodels.stats.power.FTestPower`. Record required N and achieved power in `output/power_analysis.json`. Abort if actual N < required N.  

---

## Phase 4 – Train‑test split, VIF filtering, and model training

- [ ] **T016** Create deterministic train‑test split (80 % train, 20 % held‑out test, `random_state=42`).  
  - **Outputs**: `data/processed/train.parquet`, `data/processed/test.parquet`.  
  - **Verification**:  
    - Both parquet files exist and schemas match `contracts/processed_data.schema.yaml`.  

- **T022** (see Phase 2) handles VIF after this split.

- [ ] **T018** Train a Random Forest regressor (`n_estimators=500`, `max_features='sqrt'`, `random_state=42`, `n_jobs=2`) on the cleaned training data (`data/processed/train_clean.parquet`). Perform 5‑fold CV for hyper‑parameter selection (grid over `max_features` and `min_samples_leaf`). Save model artifact `output/model_rf.joblib`.  
  - **Verification**:  
    - `output/model_rf.joblib` exists.  
    - Validate against `contracts/model_output.schema.yaml` (or a simple model schema).  

- [ ] **T019** Run 5‑fold cross‑validation on the training set to obtain out‑of‑fold performance estimates (store in `output/cv_metrics.json`).  
  - **Verification**:  
    - `output/cv_metrics.json` exists and matches `contracts/metrics_schema.schema.yaml`.  

---

## Phase 5 – Evaluation on held‑out test set

- [ ] **T020** Evaluate the trained model on the held‑out test set: compute R², Pearson r, two‑tailed p‑value (bootstrap = 1000 resamples), MAE, RMSE, and 95 % bootstrap confidence intervals. Save `output/metrics.json` conforming to `contracts/metrics.schema.yaml`.  

- [ ] **T021** Record provenance (random seeds, hyper‑parameters, package versions, timestamps) in `output/pipeline_log.json` (FR‑010).  

- [ ] **T044** Compute permutation importance on the held‑out test set with **≥ 1000 permutations per feature**. Store raw scores in `output/permutation_raw.json`.  

- [ ] **T211** Perform a non‑parametric permutation test for each feature’s importance, apply Holm‑Bonferroni correction (α = 0.05), and write `output/permutation_results.json` validated against `contracts/importance.schema.yaml`.  

- [ ] **T136** Calculate descriptor‑target Pearson correlations (training data only) and write `output/descriptor_correlation.json`. Verify that at least two descriptors satisfy |r| > 0.5 and p < 0.01 (SC‑007).  

---

## Phase 6 – External validation

- [ ] **T141** Download the independent external validation dataset from the Zenodo DOI specified in the spec. Validate against `contracts/dataset.schema.yaml` and store as `data/external/validation.csv`.  

- [ ] **T131** Run inference of the trained Random Forest on the external validation set; compute R², Pearson r, and two‑tailed p‑value; write `output/external_metrics.json` (schema `contracts/metrics.schema.yaml`).  

- [ ] **T132** Abort the pipeline if external‑validation metrics fail to meet SC‑001, SC‑002, or SC‑003 (R² ≥ 0.6, |r| ≥ 0.5, p < 0.05).  

---

## Phase 7 – Stability assessment (three independent runs)

- [ ] **T144** Execute the full training‑evaluation pipeline three times with distinct seeds `[111, 222, 333]`. Record the top‑5 feature rankings for each run in `output/stability_rankings.json`. Compute the maximum rank difference; abort if > 1 (SC‑006).  

---

## Phase 8 – Reporting & provenance linking

- [ ] **T028** Generate `output/report.md` containing:  
  1. Dataset statistics (size, power analysis).  
  2. VIF summary and descriptor filtering.  
  3. Model performance (R², Pearson r, p‑values, confidence intervals).  
  4. Descriptor‑target correlation table.  
  5. Permutation‑importance results with Holm‑Bonferroni‑corrected p‑values.  
  6. Stability assessment summary.  
  7. External‑validation metrics.  
  8. Measurement‑protocol documentation for primary and external datasets (FR‑024).  
  9. Provenance log excerpt.  
  - **Verification**:  
    - `output/report.md` exists.  
    - Contains all nine required sections (checked via simple regex).  
    - Its SHA‑256 checksum is recorded in `output/manifest.json`.  

- [ ] **T2005b** Create `output/provenance_linking.json` mapping each numeric entry in `report.md` to its source data row and code block.  
  - **Verification**:  
    - File exists.  
    - Validates against a lightweight provenance schema (e.g., keys: entry_id, source_file, line_number).  

---

## Phase 9 – End‑to‑end verification & handoff

- [ ] **T117** Run the complete pipeline end‑to‑end using the primary CSV (`data/raw/heas_raw.csv`). Ensure all artifacts (`manifest.json`, `report.md`, `metrics.json`, `stability_rankings.json`, `external_metrics.json`) are produced.  

- [ ] **T2008** Execute `scripts/verify_success_criteria.py` which parses all output artifacts and produces `output/verification_report.json` indicating pass/fail for each SC‑001 – SC‑011.  

- [ ] **T118** Verify that `output/report.md` includes every required section (dataset stats, VIF, performance, permutation importance, bootstrap CI, disclaimer).  

- [ ] **T119b** Confirm that `output/stability_rankings.json` shows a maximum rank difference ≤ 1 for the top‑5 features across the three runs.  

- [ ] **T120** Check `output/pipeline_runtime.json` reports total wall‑clock time ≤ 7200 s and status = “pass”.  

---

## Phase 10 – Documentation updates

- [ ] **T031a** Update `README.md` with installation steps, data‑source URLs, and usage instructions.  
  - **Verification**:  
    - `README.md` exists and contains sections: Installation, Data Sources, Usage, License.  

- [ ] **T031b** Update `quickstart.md` with a step‑by‑step walkthrough matching the current pipeline commands.  
  - **Verification**:  
    - `quickstart.md` exists and includes the headings: Prerequisites, Quick Start, Expected Output.  

- [ ] **T2001** Synchronize `README.md` and `quickstart.md` with any newly added tasks or changed file paths.  

---

## Phase 11 – Contract‑validation sanity checks (cross‑cutting)

- [ ] **T200_schema_validation** After each artifact creation, run `jsonschema` validation against its contract. Abort on any failure.  

- [ ] **T091** Automated check that every FR‑001 – FR‑024 and SC‑001 – SC‑011 appears in `spec.md` and is referenced by at least one implementation task.  

- [ ] **T2002** Ensure every functional requirement (FR‑001 – FR‑024) has at least one associated implementation task; abort otherwise.  

---

## Phase 12 – Final handoff to paper pipeline

- [ ] **T2007** Create `output/final_handoff.json` summarizing artifact locations, manifest SHA‑256 hashes, and a pointer to `output/report.md`. This file is consumed by the downstream paper‑generation stage.  

---

### Notes & Conventions
- All paths are **project‑relative** and reside under `code/`, `data/`, or `output/`.  
- No task writes to platform‑managed `state/` or `.github/` directories.  
- Every task that produces a file also records its SHA‑256 checksum in `output/manifest.json` (FR‑010).  
- Tasks marked **[X]** are already verified; pending tasks are unchecked and will be executed in the next run.  

--- 