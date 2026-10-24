# Research: Predicting Molecular Halide Binding Affinities

## Executive Summary
The goal is to assess whether standard ML models can predict halide binding affinities from molecular structure. **No open‑source dataset provides the required experimental halide‑binding constants (host‑SMILES + halide_identity + binding_constant)**; therefore the pipeline first **defensively scrapes** NIST Chemistry WebBook and PubChem (FR‑001). If the scrape yields fewer than 50 host molecules with ≥3 halide measurements, the pipeline **automatically switches** to a deterministic simulated dataset (FR‑011) and **marks the comparative analysis as aborted** (the primary research question cannot be answered with simulated data). The simulated target is deliberately simple and is **not used to claim success** against SC‑001; it serves only to exercise the workflow.

The final report contains per‑halide R²/RMSE **when real data are available**, bootstrap confidence intervals for performance differences, a ranked feature‑stability list, partial‑dependence plots for two key features, and an explicit associational disclaimer. If only simulated single‑halide data are available, the report flags “Comparative analysis aborted” and provides model performance for that single halide only. **SC‑001 (R² > 0.5) is therefore not applicable in simulated‑data mode** and is omitted from the success‑criterion evaluation.

## Dataset Strategy

### Verified Datasets
Only the following URLs are used; they have been pre‑validated for accessibility and format.

| Source | Description | Verified URL |
|--------|-------------|--------------|
| **SMILES (parquet)** | Canonical SMILES strings for small molecules (fallback host source). | `https://huggingface.co/datasets/maykcaldas/smiles-transformers/resolve/main/data/test-00000-of-00015-27ed436361d9186e.parquet` |
| **WebBook (csv)** | Proxy WebBook metadata (does not contain halide binding constants). | `https://huggingface.co/datasets/Raziel1234/WebBooks-1/resolve/main/books_dataset.txt` |
| **PubChem (parquet)** | Canonicalized PubChem molecule records (no binding constants). | `https://huggingface.co/datasets/sagawa/pubchem-10m-canonicalized/resolve/main/data/train-00000-of-00001-e9b227f8c7259c8b.parquet` |
| **RDKit (parquet)** | Pre‑computed RDKit descriptors for a subset of ChEMBL (used for independent evaluation). | `https://huggingface.co/datasets/nglebm19/rdkit_chemical/resolve/main/data/train-00000-of-00001.parquet` |

### Variable Fit Assessment
| Required Variable | Present after Real Scrape? | Present after Fallback? |
|-------------------|---------------------------|--------------------------|
| `host SMILES` | Yes (if scrape succeeds) | Yes – from SMILES parquet |
| `halide_identity` | Yes (if scrape succeeds) | **No** – simulated data generate a **single** halide (default `Cl-`) |
| `binding_constant` | Yes (if scrape succeeds) | Yes – simulated via FR‑011 formula (primary) and `N(0,1)` (independent set) |
| `solvent` | Yes (if scrape succeeds) | Simulated records receive a random allowed solvent (acetonitrile, chloroform, dichloromethane) |

Because the real scrape does **not** provide the full set of required variables, the fallback path is **triggered**, and the comparative analysis across halides is **explicitly aborted** as mandated by FR‑011. The pipeline still produces a complete, verifiable ML workflow.

## Methodology

### 1. Data Ingestion & Preprocessing
1. **Scrape Attempt** – `requests` with 2 s delay, exponential backoff (max 5 retries) to NIST and PubChem pages (FR‑001). All network/parse errors are caught, logged, and the script exits with status 0. Results are written to `data/raw/scrape_result.csv`.  
2. **Fallback Detection** – If `<50` hosts with ≥3 halides, log the FR‑011 warning, identify the most abundant halide (default `Cl-`), and load the SMILES parquet via `pandas.read_parquet`. Sample a representative set of molecules (seed 42).  
3. **Primary Simulation** – For each sampled host compute:  
   ```python
   logK = 0.5 * charge_density + 0.3 * sqrt(cavity_volume) + 0.2 * charge_density * cavity_volume + rng.normal(0, 0.3)
   ```  
   where `charge_density` = sum of Gasteiger charges, `cavity_volume` = RDKit molecular volume (Å³).  
4. **Independent Evaluation Set** – Load the RDKit parquet (`logP` values) and use `logP` as an **external target** unrelated to the halide descriptors. This provides a genuine out‑of‑distribution benchmark.  
5. **Filtering** – The ≥3‑halide rule and solvent filter apply **only** to real scraped data. In simulated mode each host has exactly one halide measurement; the rule is skipped with a logged note.  
6. **Output & Validation** – Write `halide_binding_data.csv` (primary) and `independent_eval_logp.csv` (evaluation) and validate both against `contracts/dataset.schema.yaml`.  

### 2. Feature Engineering (FR‑002)
- Compute ECFP4 (radius 2, 1024 bits) and a suite of RDKit descriptors (MolWt, LogP, TPSA, etc.).  
- **One‑hot encode `halide_identity`** (four binary columns) so that models can learn halide‑specific effects.  
- Standardize continuous descriptors (z‑score).  
- Unit test `tests/test_feature_engineering.py` (top‑level `tests/` directory) imports the module via `sys.path.append('code')` and verifies that all required descriptor columns are present and correctly typed.

### 3. Power Check per Halide (FR‑012)
- Count hosts per halide; if any halide has `<20` hosts, write `metadata.json` with `"underpowered": true`. This flag triggers “wide CI” warnings in the final report and **prevents** bootstrap CI generation for that pair. No formal power analysis is performed (per specification), but the report clearly marks results as under‑powered.

### 4. Model Training (FR‑004, FR‑005)
- **Algorithms**: `RandomForestRegressor` and `GradientBoostingRegressor` (default hyper‑parameters).  
- **Cross‑validation**: **RepeatedGroupKFold** (`n_splits=5`, `n_repeats=5`, groups=`host_id`) prevents host leakage and yields 25 validation folds, increasing effective sample size for downstream bootstrap (addresses concern scientific_soundness‑eb109c00).  
- Record per‑fold R² and RMSE; compute mean ± std and store in `model_runs.json` adhering to `contracts/model_output.schema.yaml`.  
- **Runtime Logging**: wall‑clock time and peak RAM are captured via `psutil` and written to `training_log.json` (SC‑003).

### 5. Feature Stability & Physical Plausibility (FR‑006, FR‑013)
- Bootstrap 1 000 resamples; compute permutation importance per resample.  
- Calculate coefficient of variation (CV) across resamples; flag features with CV ≥ 0.3 as unstable.  
- **Physical Plausibility Check**: verify that the sign of the coefficient for the top feature `charge_density` is positive (electrostatic attraction).  
  - In Real mode: report the check outcome.  
  - In Simulated mode: still execute the check and annotate the result as “trivially satisfied by construction (simulated data)”.  

### 6. Partial Dependence Plots (FR‑007)
- Generate PDPs for the two most stable features (`charge_density`, `cavity_volume`) using `sklearn.inspection.PartialDependenceDisplay`. Save PNGs in `figures/`.  

### 7. Statistical Reporting (FR‑008, FR‑009, FR‑012)
- **Bootstrap CI**: 10 000 resamples of per‑fold mean R²/RMSE differences for every halide pair **only if each halide has ≥20 hosts**; otherwise the CI step is aborted and a wide‑CI warning is written.  
- Report 95 % CI; if CI includes zero, label the difference “not statistically distinguishable”.  
- Include associational disclaimer and, when under‑powered, note “wide CI”.  

### 8. Independent Evaluation (methodology‑f4c7012e)
- After the statistical report is written, load `independent_eval_logp.csv`, predict with the trained models, compute R²/RMSE, and **append** a dedicated “Independent Evaluation (logP)” section to `report.md`. This demonstrates that the model does **not** achieve artificially high performance on a target unrelated to the halide descriptors.  

### 9. Verification Steps
- **Schema Validation** (`T009`): `python -m jsonschema -i data/processed/model_runs.json contracts/model_output.schema.yaml`.  
- **Output Summary Validation** (`T014`): `python -m jsonschema -i data/processed/output_summary.json contracts/output.schema.yaml`.  
- **Citation Verification** (`T010`): Reference‑Validator Agent checks all URLs listed in this `research.md`; CI blocks on failure.  

## Decision Rationale: Compute & Data
- **Compute**: All modeling steps (≤ 200 samples in simulated mode, ≤ 5 × 5 = 25 CV folds) are trivially CPU‑tractable and comfortably fit the 7 GB RAM budget and ≤ 6 h runtime on the GitHub Actions free tier. No GPU escape hatch is needed.  
- **Data**: No open source provides the required experimental halide‑binding constants. The SMILES parquet is the only verified source containing valid molecular structures, satisfying the fallback requirement (FR‑011). All ingestion steps are defensive: expected failures are logged, never cause a non‑zero exit.  

## Risk Assessment
| Risk | Impact | Mitigation |
|------|--------|------------|
| No real binding data | High – primary comparative question unanswerable | FR‑011 fallback; clear flag in report; independent evaluation set to avoid circularity. |
| Ingestion script failure on CI | High – unverifiable artifacts | Defensive try/except, guaranteed exit 0, unit test `test_data_ingestion.py` ensures script runs without error. |
| Data leakage | High – inflated metrics | Enforced `RepeatedGroupKFold` by `host_id`; unit test `test_model_split.py` validates grouping before training. |
| Small per‑halide sample size | Medium – wide CIs | Bootstrap CI only when ≥20 hosts per halide; under‑power flag; no significance claims. |
| Descriptor collinearity | Medium – unstable importance | CV‑based stability; flag unstable features; report VIF diagnostics. |
| Trivial physical plausibility (simulated) | Low – check always runs | Annotate result as “trivially satisfied by construction (simulated data)”. |

---  

