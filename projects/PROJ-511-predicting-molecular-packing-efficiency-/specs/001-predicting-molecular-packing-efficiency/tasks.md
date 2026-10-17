# Tasks: Predicting Molecular Packing Efficiency in Crystals from SMILES Representations

**Inputs**: Active `spec.md`, `plan.md`, `data-model.md`, `contracts/`, existing artifacts.  
**Target variable**: `pc_raw` (Packing Coefficient, FR‑003/FR‑010).  
**Data source**: Crystallography Open Database (COD), `[UNRESOLVED-CLAIM: https://www.crystallography.net/cod/` — HTTP 404]. Individual CIFs are fetched deterministically as `https://www.crystallography.net/cod/<cod_id>.cif` after selecting organic entries via the COD search interface (`https://www.crystallography.net/cod/result?format=ids&a=el1=C&strictmin=1&strictmax=50`). The loader must fail loudly on fetch errors; no synthetic fallback is permitted.

## Phase 1: Data acquisition & preprocessing

- [ ] T001 [US1] Download CIF files for organic crystal entries (≤ 50 non‑hydrogen atoms) from the verified COD base URL. Continue downloading until **at least 500** valid SMILES/pc_raw pairs are obtained (SC‑001). Store raw files unchanged under `data/raw_cif/`, log download statistics, and write `data/source_verification.json` containing the COD base URL, retrieval date, version identifier, and SHA‑256 hashes of each downloaded file (FR‑001, FR‑011). **Verification**: `data/raw_cif/` contains real CIF files, `source_verification.json` validates, and a log confirms ≥ 500 successful entries.

- [ ] T002 [US1] Parse each downloaded CIF, **extract** a canonical SMILES from CIF metadata when present; otherwise **generate** a SMILES using RDKit from the 3‑D geometry. Record the source flag (`extracted` or `generated`) in the `smiles_source` column. Compute the **Packing Coefficient** per the spec (PC = Σ V_vdW / unit‑cell volume) using Bondi radii, and extract 3‑D descriptors (radius of gyration, asphericity, principal moments) and confounder metadata (lattice system, temperature_K, has_solvent). Produce `data/dataset_raw.csv` with all required columns **including** `pc_raw` and `smiles_source` (FR‑002, FR‑003, FR‑009). **Verification**: CSV contains the full set of columns, SMILES are canonical, and PC values lie in (0, 1).

- [ ] T003 [US1] Filter `data/dataset_raw.csv`:
    * Drop rows with missing or empty SMILES.
    * Drop rows where `pc_raw` ≤ 0 or ≥ 10 (aligning with data‑model bounds).
    * Drop rows with `atom_count` > 50 or other sanity violations (unit‑cell volume out of plausible range).
    * Log counts and reasons for each exclusion.
  Write the cleaned dataset to `data/dataset_filtered.csv`. Abort with a clear error if fewer than 500 rows remain (SC‑001). **Verification**: log shows ≥ 500 rows; file exists.

- [ ] T004 [US1] Perform **pre‑encoding** validation of `data/dataset_filtered.csv`:
    * Ensure presence and non‑nullness of all columns required **except** `fingerprint_vector`.
    * Verify data types, ranges, and that `smiles` strings are valid canonical SMILES.
    * **Additional spec‑range enforcement**: drop any rows where `pc_raw` is not strictly between 0 and 1, logging the removals and rewriting `data/dataset_filtered.csv` to contain only spec‑compliant records.
    * Log success or detailed failure messages.
  **Verification**: script exits 0 only when all pre‑encoding checks pass and the dataset conforms to the (0, 1) PC range.

- [ ] T005 [US2] Encode each SMILES using the frozen pre‑trained `seyonec/ChemBERTa-zinc-base-v1` transformer on CPU (`device="cpu"`). Use mean‑pooling to obtain a fixed‑length fingerprint vector. Process SMILES in streaming batches of 64, automatically reducing batch size (64 → 32 → 16) on memory pressure to stay within the 6 GB RAM limit. Write `data/processed/full_feature_matrix.csv` that includes **all** columns from `dataset_filtered.csv` plus the new `fingerprint_vector` column (FR‑004). **Verification**: output CSV validates against `contracts/dataset.schema.yaml` (full schema) and all fingerprint values are finite.

- [ ] T006 [US2] Validate `data/processed/full_feature_matrix.csv` against the full `contracts/dataset.schema.yaml`. **Verification**: script exits 0 only on full schema compliance.

## Phase 2: Modeling, evaluation & diagnostics

- [ ] T007 [US2] Train the Primary 2‑layer MLP regression model (64 → 32 hidden units, ReLU, dropout = 0.1, ≤ 100 k trainable parameters) on an 80/20 split of the fingerprint matrix to predict `pc_raw`. Use Adam optimizer, learning rate 1e‑3, batch size 32, seed 42. Save the checkpoint as `data/artifacts/model_primary.pt` and a side‑car JSON metadata file that validates against `contracts/model.schema.yaml` (FR‑005). **Verification**: parameter count asserted ≤ 100 k; files exist and validate.

- [ ] T008 [US2] Evaluate the trained model on the held‑out 20 %:
    * Compute **MAE** and log a boolean `mae_pass` indicating whether MAE ≤ 0.05 (SC‑002 requirement).
    * Compute **Spearman ρ**.
    * Perform **Shapiro‑Wilk** test on residuals; record statistic and p‑value.
    * Compute **Pearson r** *conditionally*: if Shapiro‑Wilk p ≥ 0.05 (normal residuals) record the numeric value; otherwise record `NaN` (numeric placeholder) to satisfy the required schema while respecting FR‑006.
    * Run a **two‑sided permutation test** with **10 000** shuffles (seed = 42, parallelized via joblib). Record `n_shuffles`, `p_value`, and `actual_shuffles` (must be 10 000). Enforce SC‑003: if Spearman ρ < 0.2 then `p_value` ≥ 0.05, logging the outcome.
    * Compute **VIF diagnostics** on a PCA‑reduced fingerprint (≤ 20 components) and record flagged features and max VIF.
    * Compute **residual‑composition correlation** (correlation between residuals and one‑hot atom‑type counts) and record the value.
    * Assess target‑distribution normality (Shapiro‑Wilk) and record `is_normal`.
  Write all results to `data/artifacts/validation_report.json` conforming to `contracts/validation_report.schema.yaml` (FR‑006, FR‑007, FR‑013, SC‑002, SC‑003). **Verification**: JSON validates; `actual_shuffles` = 10 000; `mae_pass` logged.

- [ ] T009 [US2] Generate a **markdown** summary of the permutation test in `results/validation_report.md`. The markdown must list:
    * Total shuffles performed (10 000, exceeding the constitutional minimum of 1 000).
    * Observed two‑sided p‑value.
    * Brief interpretation of significance at α = 0.05.
  This satisfies Constitution Principle VII while preserving the detailed JSON artifact. **Verification**: file exists and contains the required fields.

- [ ] T010 [US2] Perform **sensitivity analysis** sweeping high‑packing thresholds {0.5, 0.6, 0.7}:
    * For each threshold, recompute validation metrics (MAE, Spearman ρ, permutation‑test p‑value).
    * Apply **Bonferroni correction** (α_adj = 0.05 / 3 ≈ 0.0167) and record `is_significant`.
    * Write `data/artifacts/sensitivity_sweep.csv` and augment `validation_report.json` with `sensitivity_analysis` and `bonferroni_correction` blocks (as required by the schema). **Verification**: three rows present; JSON re‑validated after augmentation.

## Phase 3: Reproducible reporting & handoff

- [ ] T011 [US2] Generate a **reproducible HTML report** `data/artifacts/report.html` using Jinja2. The report must include:
    * Dataset provenance (COD URL, version, SHA‑256 hashes).
    * Preprocessing steps, model architecture, hyper‑parameters.
    * All evaluation metrics (MAE, `mae_pass`, Spearman ρ, Pearson r/NaN, permutation‑test p‑value, Shapiro‑Wilk results, VIF diagnostics, residual‑composition correlation, sensitivity analysis).
    * Figures generated programmatically (predicted vs. observed scatter, residual histogram, PC distribution).
    * Full source‑code git commit hash.
  Validate that the report contains no hand‑typed numbers; every value is sourced from the JSON/CSV artifacts (FR‑008, SC‑002, SC‑003). **Verification**: HTML renders without errors; all numeric values match those in `validation_report.json`.

- [ ] T012 [US1, US2] Execute the **full end‑to‑end workflow** (T001 → T011) on a fresh GitHub Actions free‑tier runner. Record wall‑clock runtimes for each stage and the total runtime. Fail explicitly if the total exceeds **6 hours** (SC‑005). **Verification**: a log file `data/artifacts/runtime_log.txt` exists, showing total ≤ 6 h.

- [ ] T013 [US2] Write a concise **methods & results summary** `data/results/summary.md` that:
    * Links to `data/dataset_filtered.csv`, `data/artifacts/model_primary.pt`, `data/artifacts/validation_report.json`, and `data/artifacts/report.html`.
    * Restates the measured MAE, `mae_pass` status, Spearman ρ, permutation‑test p‑value, and SC‑003 outcome.
    * Honest discussion of limitations (SMILES captures only connectivity, atom‑count filter, possible residual confounding).
  **Verification**: file exists, all referenced artifacts are present, and numeric values exactly match those in `validation_report.json`.

