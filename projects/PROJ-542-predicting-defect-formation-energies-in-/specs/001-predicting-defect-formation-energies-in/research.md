# Research: Predicting Defect Formation Energies in Perovskites with Machine Learning

## Dataset Strategy
| Need | Candidate | Access Method | Status |
|------|-----------|---------------|--------|
| Perovskite oxygen‑vacancy defect formation energies (target) | Materials Project “defect formation energy” entries (requires API key) | `requests` to Materials Project REST API; API key via `MP_API_KEY` env var | **No verified public URL** – the dataset is gated. The pipeline therefore **requires a pre‑downloaded CSV** (`data/raw/materials_defects.csv`) supplied by the user. |
| Atomic property tables for descriptor calculation | `pymatgen` built‑in periodic‑table data | Local library call | Open, no download needed |
| Open substitute with matching target | None found in verified dataset list | – | **Missing** – documented as a scope limitation (see below). |

### Scope Limitation
The core scientific question depends on DFT‑computed oxygen‑vacancy formation energies available only through the Materials Project API, which is gated behind an API key. Because the CI environment cannot provide proprietary credentials, the automatic download step will **fail gracefully** if the key is absent. Researchers must either (a) provide a locally stored CSV derived from a prior API dump, or (b) reformulate the question to use an openly available surrogate (e.g., bulk formation energies). This limitation is explicitly flagged to avoid hidden fabrication.

## Methodology Decision & Rationale
| Decision | Rationale | Compute Allocation |
|----------|-----------|--------------------|
| **CPU‑first baseline models** (Random Forest, Gradient Boosting) | Tree‑based models are lightweight, deterministic, and run comfortably on the free‑tier GitHub Actions runner. No GPU is required, satisfying SC‑004. | All training and evaluation run on the CPU runner. |
| **GroupKFold cross‑validation (group = full composition)** | Guarantees that identical compositions never appear in both training and validation folds, preventing data leakage. | CPU, negligible overhead. |
| **Bootstrap 10 000 resamples for RMSE CI** | Provides a robust confidence interval with low memory demand; can be streamed to stay within RAM limits. | CPU, < 1 GB RAM. |
| **Paired two‑sided t‑test** | Required by SC‑007 to assess bias; **not** used as a primary acceptance criterion. | CPU, negligible cost. |
| **Runtime budget measurement** | SC‑004 mandates total wall‑clock time ≤ 30 minutes on a CPU‑only runner. The pipeline records start/end timestamps and aborts if the budget is exceeded. | CPU, negligible overhead. |
| **Power analysis** | Removed because it did not directly support the primary hypothesis (RMSE ≤ 0.5 eV, R² ≥ 70 %). Dataset‑size checks remain. | — |
| **Stratified 80/20 train‑test split (by composition)** | Preserves composition distribution while ensuring no overlap with CV groups. | CPU, negligible overhead. |

## Statistical Rigor Checklist
- **Multiple comparisons**: Only two models are compared; family‑wise correction is unnecessary (family size = 2).  
- **Power justification**: Dataset‑size warning is logged; no explicit power calculation (see above).  
- **Causal inference**: Purely predictive/associational; no causal claims are made.  
- **Measurement validity**: Targets are DFT‑computed defect formation energies from the Materials Project, a widely accepted computational source.  
- **Collinearity**: Descriptors may be correlated (e.g., radius ↔ electronegativity). A Pearson correlation matrix will be logged; feature importance is interpreted descriptively, not as independent effects.  

## Execution Flow (ordered)
1. **Data acquisition** (`download.py`): attempt API fetch → fallback to local CSV → abort if neither available.  
2. **Checksum verification** (`checksum.py`) → `data/checksums/raw_defects.sha256`.  
3. **Feature engineering** (`featurize.py`) → `data/processed/features.csv` + `featurize.log` + `descriptor_gaps.log`.  
4. **Dataset validation** (`validate.py`) → `validation.log` (size check, ≥ 500 rows warning).  
5. **Stratified train‑test split** (`split.py`) → `train.csv`, `test.csv` + `split.log`.  
6. **5‑fold GroupKFold CV** (`train.py`) → `models/rf_cv.pkl`, `models/gb_cv.pkl`, `cv_metrics.json`.  
7. **Model selection** (lowest mean CV RMSE).  
8. **Held‑out evaluation** (`evaluate.py`) → `performance.json`, `figures/pred_vs_actual.png`, `figures/feature_importance.png`.  
9. **Runtime check**: total elapsed time is compared to the 30‑minute ceiling; pipeline aborts if exceeded.  
10. **Notebook orchestration** (`pipeline.ipynb`).  
11. **Contract validation** (`pytest`) – each artifact is checked against its JSON‑Schema contract (see `contracts/`).  

All steps are reproducible; random seeds are fixed (`np.random.seed(42)`, `random_state=42` in scikit‑learn).

---

