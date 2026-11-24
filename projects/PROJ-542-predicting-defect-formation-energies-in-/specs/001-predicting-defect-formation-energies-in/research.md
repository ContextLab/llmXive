# Research: Predicting Defect Formation Energies in Perovskites with Machine Learning

## Dataset Strategy
| Need | Candidate | Access Method | Status |
|------|-----------|---------------|--------|
| Perovskite oxygen‑vacancy defect formation energies (target) | Materials Project “defect formation energy” entries (requires API key) | `requests` to Materials Project REST API; API key via `MP_API_KEY` env var | **No verified public URL** – the dataset is gated. The pipeline therefore **requires a user‑provided CSV** (`data/raw/materials_defects.csv`) that conforms to the `raw_dataset.schema.yaml` contract. |
| Atomic property tables for descriptor calculation | `pymatgen` built‑in periodic‑table data | Local library call | Open, no download needed |
| Open substitute with matching target | None found in verified dataset list | – | **Missing** – documented as a scope limitation (see below). |

### Scope Limitation
The scientific question relies on DFT‑computed oxygen‑vacancy formation energies that are only accessible through the gated Materials Project API. Because the CI environment cannot supply proprietary credentials, the automatic download step will **fail gracefully** if `MP_API_KEY` is absent. Researchers must therefore provide a pre‑downloaded CSV that matches the required schema. This limitation is explicitly flagged to avoid hidden fabrication.

### Metadata & Confounder Capture
When the Materials Project API is used, `metadata.py` extracts any available **DFT functional**, **calculation settings**, **temperature**, and **pressure** fields from the response and writes them to `data/raw/metadata.json`. These variables are logged and may be incorporated as covariates in secondary analyses to control for systematic variation across calculations (addressing methodological concern [methodology-75811a55]).

## Methodology Decision & Rationale
| Decision | Rationale | Compute Allocation |
|----------|-----------|--------------------|
| **CPU‑first baseline models** (Random Forest, Gradient Boosting) | Tree‑based models are lightweight, deterministic, and run comfortably on the free‑tier GitHub Actions runner. No GPU is required, satisfying SC‑004. | All training and evaluation run on the CPU runner. |
| **GroupKFold cross‑validation (group = full composition)** | Guarantees that identical compositions never appear in both training and validation folds, preventing data leakage. | CPU, negligible overhead. |
| **Bootstrap 10 000 resamples for RMSE CI** | Provides a robust confidence interval with low memory demand; can be streamed to stay within RAM limits. | CPU, < 1 GB RAM. |
| **Paired two‑sided t‑test** | Required by SC‑007 to assess bias; the p‑value is reported for diagnostic purposes only, **not** as a success criterion. | CPU, negligible cost. |
| **Runtime budget measurement** | SC‑004 mandates total wall‑clock time ≤ 30 minutes on a CPU‑only runner. The pipeline records start/end timestamps and aborts if the budget is exceeded. | CPU, negligible overhead. |
| **Stratified 80/20 train‑test split (by composition) + [deferred] validation split** | Preserves composition distribution while ensuring no overlap with CV groups; the validation split is reserved for assessing fallback models. | CPU, negligible overhead. |
| **Metadata capture** | DFT functional, temperature, pressure, etc., are captured from Materials Project metadata (if present) to acknowledge potential confounding factors and enable downstream control. | CPU, negligible overhead. |
| **Power‑analysis justification** | With ≥ 500 samples (SC‑005) and the target RMSE of 0.5 eV, a two‑sample t‑test has > 80 % power at α = 0.05 to detect a mean difference of this magnitude, satisfying methodological rigor. | CPU, no additional cost. |
| **Confounder Integration (optional)** | When `metadata.json` contains numeric or categorical fields, they are merged as additional covariates during model training (Phase 7). This directly addresses the methodological concern about uncontrolled confounders. | CPU, negligible overhead. |

## Statistical Rigor Checklist
- **Multiple comparisons**: Only two models are compared; family‑wise error correction is unnecessary (SC‑ref).  
- **Power justification**: See **Power‑analysis justification** above; ≥ 500 samples give > 80 % power for the target effect size.  
- **Causal inference**: Purely predictive/associational; no causal claims are made (causal‑inference disclaimer).  
- **Measurement validity**: Targets are DFT‑computed defect formation energies from the Materials Project, a widely accepted computational source.  
- **Collinearity**: Descriptors may be correlated; a Pearson correlation matrix will be logged; feature importance is interpreted descriptively, not as independent effects.  

## Execution Flow (ordered)
1. **Data acquisition** (`download.py`): attempt API fetch → fallback to local CSV → abort if neither available (FR‑007).  
2. **Checksum verification** (`checksum.py`) → `data/checksums/raw_defects.sha256`.  
3. **Metadata extraction** (`metadata.py`) → `data/raw/metadata.json` (confounder log).  
4. **Feature engineering** (`featurize.py`) → `data/processed/features.csv` + `featurize.log` + `descriptor_gaps.log`.  
5. **Dataset validation** (`validate.py`): enforce **≥ 50** samples for any CV; if < 500, log a **power‑size warning** but continue (see Power‑analysis justification).  
6. **Stratified train‑test‑validation split** (`split.py`) → `train.csv`, `test.csv`, `validation.csv` + `split.log`.  
7. **5‑fold GroupKFold CV** (`train.py`) → `cv_metrics.json`, model pickles.  
8. **Model selection** (lowest mean CV RMSE).  
9. **Held‑out evaluation** (`evaluate.py`) → `performance.json`, `figures/pred_vs_actual.png`, `figures/feature_importance.png`.  
10. **Fallback (if needed)** (`fallback.py`): augment features with structural descriptors (if `structure_cif` present), retrain using **validation.csv** as the held‑out set, and regenerate performance artefacts.  
11. **Confounder Integration (optional)** (`confounder_integration.py`): merge selected metadata fields into the training matrix before steps 7–9; log which confounders were used.  
12. **Runtime check**: total elapsed time compared to the 30‑minute ceiling; abort if exceeded.  
13. **Notebook orchestration** (`pipeline.ipynb`).  
14. **Contract validation** (`pytest`) – each artifact is checked against its JSON‑Schema contract (`raw_dataset.schema.yaml`, `features.schema.yaml`, `model_performance.schema.yaml`).  

All steps are reproducible; random seeds are fixed (`np.random.seed(42)`, `random_state=42` in scikit‑learn).

---


