# Research: Predicting Molecular Halide Binding Affinities

## Executive Summary
This study evaluates whether standard machine‑learning models can predict halide binding affinities of host molecules from purely structural descriptors. Because no open source provides the exact experimental binding constants, the pipeline first attempts to scrape NIST Chemistry WebBook and PubChem (FR‑001) with fully defensive error handling. When the scrape yields fewer than 50 viable hosts, the pipeline **automatically switches** to a deterministic simulated‑data mode (FR‑011) using a publicly available SMILES dataset. Because the FR‑011 simulated target is a deterministic (plus noise) function of two model features, primary‑simulation performance metrics are **circular by construction** and are labeled as such; a **feature‑independent** secondary evaluation set (targets ~ N(0,1)) provides a non‑circular benchmark of genuine predictive ability.

The final report includes per‑halide R²/RMSE (when real data are present), bootstrap confidence intervals for performance differences, a ranked feature‑stability list, partial dependence plots for two key features, an explicit **associational** disclaimer (FR‑008), and an appended independent‑evaluation section. If only simulated single‑halide data are available, the report flags "Comparative analysis aborted" and provides model performance for that single halide only.

## Dataset Strategy

### Verified Datasets
Only the following URLs are used; they have been pre‑validated for accessibility and format.

| Source | Description | Verified URL |
|--------|-------------|--------------|
| **SMILES (parquet)** | Large collection of canonical SMILES strings for small molecules. Used as the host‑molecule source when experimental binding data are unavailable. | ` |
| **RDKit Descriptors (parquet)** | Pre‑computed RDKit descriptors for a subset of ChEMBL; optional for cross‑checking descriptor calculations. | ` |
| **WebBook (csv)** | Proxy WebBook metadata (does not contain halide binding constants). Included to satisfy the scraping attempt requirement. | ` |
| **PubChem (parquet)** | Canonicalized PubChem molecule records (no binding constants). Used for the initial scrape attempt. | ` |

### Variable Fit Assessment
| Required Variable | Present in Real Scrape? | Present after Fallback? |
|-------------------|------------------------|--------------------------|
| `host SMILES` | Yes (if scrape succeeds) | Yes – from SMILES dataset |
| `halide_identity` | Yes (if scrape succeeds) | **No** – simulated data generate a **single** halide (the most abundant in the scraped set, default `Cl-`) |
| `binding_constant` | Yes (if scrape succeeds) | Yes – primary simulated set follows the FR‑011 formula; independent evaluation set uses a feature‑independent N(0,1) draw |
| `solvent` | Yes (if scrape succeeds) | Simulated records assign a random allowed solvent (acetonitrile, chloroform, DCM) |

Because the real scrape does **not** provide the full set of required variables, the fallback path is activated, and the comparative research question (differences across halides) is **aborted** as mandated by FR‑011. The pipeline still produces a complete, verifiable ML workflow.

## Methodology

### 1. Data Ingestion & Preprocessing
1. **Scrape Attempt (defensive)** – `requests` with 2 s delay, exponential backoff (max 5 retries) to NIST and PubChem pages (FR‑001). All network and parsing exceptions are caught and logged; the (possibly empty) result is written to `data/raw/scrape_result.csv`. Scrape failure never causes a non‑zero exit.
2. **Fallback Path** – If <50 hosts with ≥3 halides: log the exact FR‑011 warning, identify the most abundant halide (default `Cl-`), load the SMILES parquet via `pandas.read_parquet` with an explicit column check, and randomly sample 200 molecules (seed 42).
3. **Primary Simulation** – For each host, generate a single‑halide binding constant dependent on descriptors as specified by FR‑011:  
   ```python
   logK = 0.5 * charge_density + 0.3 * cavity_volume + rng.normal(0, 0.2)
   ```  
   Note: this target is a deterministic function of two model features, so downstream metrics on this set are **circular by construction** and are labeled as such in the report.
4. **Independent Evaluation Set** – Generate 100 additional records where the binding constant is **independent** of any descriptor: `logK = rng.normal(0, 1)`. This set is used solely for evaluating whether the model can predict targets that are not trivially encoded in the features (addresses methodology‑f4c7012e and scientific_soundness‑f0482303).
5. **Filtering** – The ≥3‑halide retention rule and the solvent filter apply **only to real scraped data**. In Simulated mode each host carries exactly one halide measurement by construction, so the ≥3‑halide filter is not applicable and is skipped with a logged note. Records with invalid SMILES (RDKit parsing fails) are always excluded and logged (FR‑010).
6. **Output** – Write `halide_binding_data.csv` (primary) and `independent_eval.csv` (evaluation) and validate both against `contracts/dataset.schema.yaml` before use.

### 2. Feature Engineering (FR‑002)
- Compute ECFP4 (radius 2, 1024 bits) and a suite of RDKit descriptors (MolWt, LogP, TPSA, etc.).  
- Standardize continuous descriptors (z‑score).  
- Append columns to a new CSV file.

### 3. Power Check per Halide (FR‑012)
- Count hosts per halide; if any halide has <10 hosts, set `underpowered: true` in `metadata.json` and flag wide CIs in the final report.

### 4. Model Training (FR‑004, FR‑005)
- **Algorithm**: `RandomForestRegressor` and `GradientBoostingRegressor` with default hyper‑parameters.  
- **Cross‑validation**: `GroupKFold(n_splits=5, groups=host_id)` ensures no host leakage (Principle VII).  
- Record per‑fold R² and RMSE; compute **mean ± std** and store in `model_runs.json` following `contracts/model_output.schema.yaml` (`metrics` object with `r2_mean`, `r2_std`, `rmse_mean`, `rmse_std`, plus `fold_metrics`).

### 5. Feature Stability & Physical Plausibility Check (FR‑006, FR‑013)
- Perform 1000 bootstrap resamples of the training data; compute permutation importance for each feature per resample.  
- Calculate coefficient of variation (CV) across resamples; flag features with CV ≥ 0.3 as "unstable".  
- **Physical Plausibility Check (always executed)**: verify that the sign of the coefficient for the top feature `charge_density` is positive (electrostatic attraction). In Real mode, report the check outcome as an informative validation. In Simulated mode, the check is still executed and its result recorded, annotated "trivially satisfied by construction (simulated data)" — the check is never skipped, but the annotation prevents it from being read as independent evidence.

### 6. Partial Dependence Plots (FR‑007)
- Using `sklearn.inspection.PartialDependenceDisplay`, generate PDPs for the two most stable features (e.g., `charge_density` and `cavity_volume`).  
- Save PNGs to `data/processed/figures/` and reference them in the report.

### 7. Statistical Reporting (FR‑008, FR‑009, FR‑012)
- **Bootstrap CI**: 10 000 resamples of per‑fold mean R²/RMSE differences for every halide pair (only if ≥2 halides present and not underpowered).  
- Report 95 % CI; if CI includes zero, label the difference "not statistically distinguishable".  
- Include an associational disclaimer and, when underpowered, note "wide CI".  
- If simulated single‑halide mode is active, set `comparative_analysis_aborted: true` and omit pairwise CI tables.  
- Generates `report.md`.

### 8. Independent Evaluation on Hold‑Out Set (methodology‑f4c7012e)
- Runs **after** statistical reporting; loads `independent_eval.csv`, predicts using the trained models, computes R²/RMSE, and **appends** a dedicated section to the existing `report.md` (it does not regenerate the report).  
- This demonstrates that the model does **not** achieve artificially high performance when the target is unrelated to the features, and contrasts it with the (circular) primary‑simulation metrics.

### 9. Verification Steps
- **Schema Validation**: `python -m jsonschema -i data/processed/model_runs.json contracts/model_output.schema.yaml` (Task T009).  
- **Citation Verification**: The Reference‑Validator Agent automatically checks all URLs listed in this `research.md` (Task T010); CI blocks on failure.

## Decision Rationale: Compute & Data

- **Compute**: Random Forest / Gradient Boosting on ≤ 200 hosts (single halide in simulated mode) plus the independent evaluation set is trivially CPU‑tractable; fits within the 7 GB RAM budget and ≤ 6 h runtime. No GPU escape hatch needed.  
- **Data**: No open source provides the exact experimental binding constants. The SMILES dataset is the only verified source containing valid molecular structures. Using a deterministic, seeded simulation satisfies FR‑011 while the independent evaluation set provides a non‑circular benchmark. All ingestion steps are defensive: expected scrape/download failures are logged and handled, never fatal.

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| No real binding data | High – primary comparative question unanswerable | FR‑011 fallback; clear flagging in report; independent evaluation set to avoid circularity. |
| Ingestion script failure on CI | High – unverifiable artifacts | Defensive try/except around all network and parse steps; deterministic seeded fallback; schema validation before write. |
| Data leakage | High – inflated metrics | Enforced `GroupKFold` by `host_id`; unit test verifies grouping. |
| Small sample per halide | Medium – wide CIs | Bootstrap CI; underpowered flag; avoid significance claims. |
| Collinearity among descriptors | Medium – unstable importance | CV‑based stability; flag unstable features; report VIF diagnostics. |
| Trivial physical plausibility (simulated) | Low – check always runs | Check executed with "trivially satisfied by construction (simulated data)" annotation; never skipped. |