# Research: Predicting Defect Formation Energies in Perovskites with Machine Learning

## Dataset Strategy
| Need | Candidate | Access Method | Status |
|------|-----------|---------------|--------|
| Perovskite oxygen‑vacancy defect formation energies (target) | Materials Project “defect formation energy” entries (requires API key) | `requests` to Materials Project REST API; API key via `MP_API_KEY` env var | **No verified public URL** – the dataset is gated. The pipeline therefore **requires a pre‑downloaded CSV** (`data/raw/materials_defects.csv`) supplied by the user. |
| Atomic property tables for descriptor calculation | `pymatgen` built‑in periodic‑table data | Local library call | Open, no download needed |
| Open substitute with matching target | None found in verified dataset list | – | **Missing** – documented as a scope limitation (see below). |

### Scope Limitation
The central scientific question relies on DFT‑computed oxygen‑vacancy formation energies that are only available through the Materials Project API, which is gated behind an API key. Because the CI environment cannot provide proprietary credentials, the automatic download step will **fail gracefully** if the key is absent. Researchers must either (a) provide a locally stored CSV derived from a prior API dump, or (b) reformulate the question to use an openly available surrogate (e.g., bulk formation energies without defects). This limitation is explicitly flagged to avoid hidden fabrication.

## Methodology Decision & Rationale
| Decision | Rationale | Compute Allocation |
|----------|-----------|--------------------|
| **CPU‑first baseline models** (Random Forest, Gradient Boosting) | Tree‑based models are lightweight, deterministic, and run comfortably on the free‑tier GitHub Actions runner. No GPU is required, satisfying SC‑004. | All training and evaluation run on the CPU runner. |
| **GroupKFold cross‑validation (group = full composition)** | Guarantees that identical compositions never appear in both training and validation folds, preventing data leakage inherent in StratifiedKFold for regression. | CPU, negligible overhead. |
| **Bootstrap 10 000 resamples for RMSE CI** | Provides a robust confidence interval with low memory demand; can be streamed to stay within RAM limits. | CPU, < 1 GB RAM. |
| **Paired two‑sided t‑test** | Required by SC‑003 to assess bias between predictions and DFT values. | CPU, negligible cost. |
| **Power analysis using statsmodels** | Computes required sample size for detecting a 0.1 eV RMSE improvement with 80 % power (α = 0.05) based on σ estimated from a pilot subset; logs achieved power. | CPU, trivial. |
| **Stratified 80/20 train‑test split (by composition)** | Preserves composition distribution while ensuring no overlap with CV groups. | CPU, negligible overhead. |

## Statistical Rigor Checklist
- **Multiple comparisons**: Only two models are compared; family‑wise correction is unnecessary (family size = 2).  
- **Power justification**: Using `statsmodels.stats.power.tt_ind_solve_power` with effect size = 0.1 eV / σ (σ estimated from pilot), we compute required N; if actual N ≥ required, we report > 80 % power, otherwise we note the limitation.  
- **Causal inference**: Purely predictive/associational; no causal claims are made.  
- **Measurement validity**: Targets are DFT‑computed defect formation energies from the Materials Project, a widely accepted computational source.  
- **Collinearity**: Descriptors may be correlated (e.g., radius ↔ electronegativity). A Pearson correlation matrix will be logged; feature importance is interpreted descriptively, not as independent effects.  

## Execution Flow (ordered)
1. **Data acquisition** (`download.py`): attempt API fetch → fallback to local CSV → abort if neither available.  
2. **Checksum verification** → `data/raw/materials_defects.csv.sha256`.  
3. **Feature engineering** (`featurize.py`) → `data/processed/features.csv`.  
4. **Dataset validation** (size, missing values, power analysis).  
5. **Stratified train‑test split** (seeded, 80/20, composition stratification).  
6. **k‑fold GroupKFold CV** (`train.py`) → JSON metrics (`cv_metrics.json`).  
7. **Model selection** (lowest mean CV RMSE).  
8. **Held‑out evaluation** (`evaluate.py`) → metrics, bootstrap CI, paired t‑test, plots.  
9. **Feature importance extraction** → bar chart PNG.  
10. **Notebook orchestration** (`pipeline.ipynb`).  
11. **Contract validation** (`pytest`) – performed within the notebook and as a separate test suite.  

All steps are reproducible; random seeds are fixed (`np.random.seed(42)`, `random_state=42` in scikit‑learn).

---

