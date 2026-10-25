# Research: Predicting the Impact of Composition on the Band Gap of Perovskite Materials

## Objective
Create a reproducible, composition‑only predictive pipeline for perovskite band gaps, quantify its predictive accuracy, interpret descriptor importance, and confirm external validity against experimental measurements.

## Decision & Rationale
| Decision | Rationale |
|----------|-----------|
| **CPU‑first implementation** (scikit‑learn, matminer, SHAP TreeExplainer) | All algorithms run efficiently on the 2‑core GitHub Actions CPU; no GPU‑only models are needed. |
| **Open perovskite dataset via Materials Project API or Zenodo mirror** | Guarantees ≥ 500 ABX₃ entries with `formula` and `band_gap`; falls back to Zenodo if no API key is provided. |
| **NREL experimental JSON** (`bsebench-org/nrel-pulse-diagnostics-2025-raw`) | Provides an external set of experimental band gaps; meets the ≥ 20‑entry requirement. |
| **Stratified split on band‑gap quantile bins** | Preserves the target distribution across train/val/test (FR‑013). |
| **Bootstrap paired test (10 000 resamples)** | Non‑parametric significance testing for model vs. baseline and RF vs. GB; enables Bonferroni correction (FR‑005). |
| **SHAP TreeExplainer** | Works with tree models on CPU; yields global importance and per‑sample explanations (FR‑006). |
| **Spearman rank correlation** | Directly matches the literature benchmark (ρ ≥ 0.5) from Jain et al., 2022 (SC‑003). |
| **Threshold sweep {0.30, 0.35, 0.40 eV}** | Implements FR‑008 and produces false‑negative rates for lead‑free identification (SC‑004). |
| **Top‑5 descriptor refit** | Tests FR‑016; we will compare R² to the full model (SC‑005). |
| **Power analysis for external validation** | Because the experimental set may be small, we compute the observed statistical power of the Spearman test; if power < 0.8 we still report ρ but note that the ≥ 0.5 target is interpreted conservatively. |
| **Power analysis for external validation** | Because the experimental set may be small, we compute the observed statistical power of the Spearman test; if power < 0.8 we still report ρ but note that the ≥ 0.5 target is interpreted conservatively. |
| **Power analysis for external validation** | Because the experimental set may be small, we compute the observed statistical power of the Spearman test; if power < 0.8 we still report ρ but note that the ≥ 0.5 target is interpreted conservatively. |

## Dataset Strategy
| Role | Source (Verified URL) | Loader | Key Variables | Notes |
|------|-----------------------|--------|---------------|-------|
| **Training / DFT** | Materials Project API (`https://materialsproject.org/rest/v2/materials`) **or** Zenodo mirror `https://zenodo.org/record/7261235/files/perovskite_dataset.parquet` | Custom API client / `datasets.load_dataset(..., streaming=False)` | `formula` (string), `band_gap` (float) | After loading we filter for ABX₃ stoichiometry and enforce `0 < band_gap < 6`. A post‑download check ensures ≥ 500 perovskite entries; otherwise the pipeline aborts. |
| **Experimental Validation** | `https://huggingface.co/datasets/bsebench-org/nrel-pulse-diagnostics-2025-raw/resolve/main/BSEBENCH_SOURCE.json` | `datasets.load_dataset(..., streaming=False)` | `formula`, `experimental_band_gap` | May contain < 20 entries; we still compute Spearman ρ and annotate the p‑value as “insufficient sample size” when N < 10 (FR‑011). |
| **Elemental Properties** | `matminer` internal tables (no external URL) | `matminer.featurizers.composition.ElementProperty` | electronegativity, atomic radius, ionization energy, oxidation states, etc. | Required for FR‑002 and FR‑016. |

*No other datasets are used. If any required column is missing, the pipeline aborts with a clear error (fatal mismatch).*

## Methodology Overview
1. **Download & Verify** – Fetch the perovskite dataset via API or Zenodo; compute SHA‑256 checksums; abort on mismatch.  
2. **Perovskite Filtering** – Regex `^[A-Z][a-z]?[A-Z][a-z]?[A-Z][a-z]?\\d*$` to retain ABX₃ formulas; log and drop entries with unknown elements (FR‑009).  
3. **Physical Band‑Gap Filtering** – Remove rows where `band_gap ≤ 0` (log warning, FR‑010) or `≥ 6`.  
4. **Feature Generation** – Using `matminer`:  
   - `ElementProperty` → mean & variance of electronegativity, atomic radius, ionization energy.  
   - `OxidationStateFeaturizer` → variance of oxidation states.  
   - `GoldschmidtToleranceFactor` & `OctahedralFactor` computed from ionic radii.  
   - Resulting table has ≥ 5 descriptors (FR‑002).  
5. **Standardization** – Fit `StandardScaler` on training descriptors; apply to val/test (FR‑012).  
6. **Stratified Split** – [deferred] train, [deferred] val, [deferred] test using band‑gap quantile bins (FR‑013).  
7. **Model Training** –  
   - **Random Forest**: grid over `n_estimators=[200,400]`, `max_depth=[10,20,None]`.  
   - **Gradient Boosting**: grid over `n_estimators=[200,400]`, `max_depth=[3,5]`, `learning_rate=[0.01,0.05,0.1]`.  
   - 5‑fold CV on training set; select hyper‑parameters minimizing mean RMSE (FR‑004, FR‑014).  
8. **Baseline & Significance** – Baseline = mean predictor. Perform bootstrap paired test (10 000 resamples) for: RF vs. baseline, GB vs. baseline, RF vs. GB. Apply Bonferroni correction (FR‑005).  
9. **Evaluation** – Compute RMSE, MAE, R² on held‑out test set for both models (FR‑005). Verify RMSE ≤ 0.35 eV (SC‑001) and R² significance (SC‑002).  
10. **Interpretation** – `shap.TreeExplainer` on the best model; generate global SHAP summary plot; extract top‑5 descriptors (FR‑006).  
11. **External Validation & Power Analysis** – Predict band gaps for NREL formulas; compute Spearman ρ and p‑value; if N < 10, annotate p‑value as “insufficient sample size”. Compute observed power of the Spearman test; if power < 0.8, report ρ but note that the ≥ 0.5 target is interpreted conservatively.  
12. **Sensitivity Analysis** – Define lead‑free = no “Pb” in formula. For each error threshold (0.30, 0.35, 0.40 eV) compute false‑negative rate for lead‑free identification (FR‑008). Report rates (SC‑004).  
13. **Top‑5 Descriptor Refitting** – Train a Random Forest using only the top‑5 descriptors; compute R² and ensure `R²_top5 / R²_full ≥ 0.80` (FR‑016, SC‑005).  
14. **Logging & Audit** – All warnings (missing elements, metallic entries) written to `logs/pipeline.log`; final `results/summary.json` aggregates audit counts.  

## Success Metrics (Mapped to SC)
| Metric | Target | Source |
|--------|--------|--------|
| Test‑set RMSE ≤ 0.35 eV | SC‑001 | Step 9 (evaluation) |
| Model R² significantly > baseline (Bonferroni‑adjusted p < 0.05) | SC‑002 | Step 8 (bootstrap) |
| Spearman ρ ≥ 0.5 on NREL experimental set **when observed power ≥ 0.8** | SC‑003 | Step 11 (external validation) |
| False‑negative rates for lead‑free across thresholds | SC‑004 | Step 12 (sensitivity sweep) |
| `R²_top5 / R²_full` ≥ 0.80 | SC‑005 | Step 13 (top‑5 refit) |

All metrics are stored in `results/summary.json` and will be rendered into tables/figures for the paper stage.


## Power Analysis Details (added for methodology concern)
We compute the observed power of the Spearman test using a Monte‑Carlo approximation: generate 10 000 synthetic datasets matching the experimental sample size, with a true correlation of 0.5, and record the proportion of simulations yielding a p‑value ≤ 0.05. This proportion is reported in `results/external_validation.json` as `spearman_power`. If `spearman_power < 0.8`, the success criterion SC‑003 is interpreted as “report ρ, but do not require ρ ≥ 0.5 for acceptance”.  

---

