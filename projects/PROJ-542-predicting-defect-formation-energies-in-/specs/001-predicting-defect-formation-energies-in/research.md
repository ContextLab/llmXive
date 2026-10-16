# Research: Predicting Defect Formation Energies in Perovskites with Machine Learning

## Dataset Strategy
| Need | Candidate | Access Method | Status |
|------|-----------|---------------|--------|
| Perovskite oxygen‑vacancy defect formation energies (target) | Materials Project “defect formation energy” entries (requires API key) | `requests` to Materials Project REST API; API key via `MP_API_KEY` env var | **Not openly downloadable** – no verified public URL. The pipeline therefore **requires a pre‑downloaded CSV** (`data/raw/materials_defects.csv`) supplied by the user. |
| Atomic properties for descriptor calculation | `pymatgen` built‑in periodic table data | Local library call | Open, no download needed |
| Optional open substitute | None with matching target variable (verified datasets list does not contain a suitable open source) | – | **Missing** – documented as a scope limitation (see below). |

### Scope Limitation
The core scientific question hinges on DFT‑computed defect formation energies that are only available via the Materials Project API, which is gated behind an API key. Because the CI environment cannot supply proprietary credentials, the automated download step will **fail gracefully** if the key is absent. Researchers must either (a) provide a locally stored CSV derived from a prior API dump, or (b) revise the research question to use an openly available surrogate dataset (e.g., formation energies of bulk perovskites without defects). This limitation is explicitly flagged to avoid hidden fabrication.

## Methodology Decision & Rationale
| Decision | Rationale | Compute Allocation |
|----------|-----------|--------------------|
| **CPU‑first baseline models** (Random Forest, Gradient Boosting) | Tree‑based models are lightweight, deterministic, and run comfortably on the free‑tier GitHub Actions runner. No GPU is required, satisfying SC‑004. | All training and evaluation run on the CPU runner. |
| **Optional GPU off‑load** – *none* | No deep‑learning or transformer models are needed; the baseline satisfies the parsimony principle (VI). | – |
| **Bootstrapped confidence intervals** (10 000 resamples) | Provides a robust estimate of RMSE variability without excessive compute; can be performed in a streamed fashion to keep memory low. | CPU, < 1 GB RAM. |
| **Paired two‑sided t‑test** | Required by SC‑003 to assess bias; straightforward implementation with `scipy.stats.ttest_rel`. | CPU, negligible cost. |
| **Stratified train‑test split** | To mitigate composition‑class imbalance (e.g., over‑representation of certain A‑site cations), the 80/20 split is performed stratified by A‑site element, preserving class distribution across folds. | CPU, negligible overhead. |
| **Class‑weight handling in training** | Scikit‑learn estimators receive `class_weight='balanced'` (or custom weights) to further reduce bias from imbalanced composition groups. | CPU, negligible overhead. |

## Statistical Rigor Checklist
- **Multiple comparisons**: Only two models are compared; we will report both but will not perform a formal correction (family size = 2, negligible).  
- **Power justification**: Assuming an expected RMSE improvement of a modest magnitude. and a standard deviation of a modest fraction of an eV, a sample of 500 gives > 80 % power at α = 0.05 (computed via a two‑sample t‑test approximation). If fewer rows are available, we will report the reduced power in the final results.  
- **Causal inference**: The study is purely predictive/associational; no causal claims are made.  
- **Measurement validity**: Target values are DFT‑computed defect formation energies from the Materials Project, a widely used computational source.  
- **Collinearity**: Descriptors may be correlated (e.g., atomic radius ↔ electronegativity). Feature‑importance will be reported, and a Pearson correlation matrix will be logged for transparency.  
- **Descriptor limitation**: The chosen twelve compositional descriptors capture bulk chemical trends but omit detailed structural/electronic information. An optional Goldschmidt tolerance factor is included when lattice data exist. If baseline performance fails to meet the RMSE target, future work may explore richer structural features, but this lies outside the current scope.

## Execution Flow (ordered)
1. **Data acquisition** (`download.py`): attempt API fetch → fallback to local CSV → abort if neither available.  
2. **Checksum verification** → `data/raw/materials_defects.csv.sha256`.  
3. **Feature engineering** (`featurize.py`) → `data/processed/features.csv`.  
4. **Dataset validation** (size, missing values).  
5. **Stratified train‑test split** (seeded, 80/20, stratified by A‑site element).  
6. **k‑fold stratified CV** (`train.py`) → JSON metrics (`cv_metrics.json`).  
7. **Model selection** (lowest mean RMSE).  
8. **Held‑out evaluation** (`evaluate.py`) → metrics, bootstrap CI, t‑test, plots.  
9. **Feature importance extraction** → bar chart PNG.  
10. **Notebook orchestration** (`pipeline.ipynb`).  
11. **Contract validation** (`pytest`) – performed as part of the notebook documentation phase.  

All steps are reproducible; random seeds are fixed (`np.random.seed(42)`, `random_state=42` in scikit‑learn).

---



