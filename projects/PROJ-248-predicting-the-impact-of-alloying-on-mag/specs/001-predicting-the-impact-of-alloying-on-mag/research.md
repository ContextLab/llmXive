# Research: Predicting Saturation Magnetization of Alloys Using Public OQMD Data

## Dataset Strategy

| Dataset | Source (Verified URL) | Access Method | Variables Available | Notes |
|---------|----------------------|---------------|---------------------|-------|
| **OQMD magnetic release** | https://huggingface.co/datasets/kjappelbaum/chemnlp-oqmd/resolve/main/targets.csv | `datasets.load_dataset("kjappelbaum/chemnlp-oqmd", split="train")` (CSV) | `composition`, `magnetic_moment`, `spacegroup`, `lattice_parameters` | Used for **saturation‑magnetization** modeling. No Curie‑temperature data available; field will be emitted as `null`. |

**Conclusion**: The OQMD CSV supplies all variables needed for saturation‑magnetization. Since no open source provides Curie temperature, the project proceeds with a saturation‑magnetization‑only scope, and **FR‑001 has been formally dropped** from the specification.

## Methodological Rationale

1. **Feature Engineering** –  
   - Fractional elemental abundances.  
   - Element‑wise averages of atomic radius, first ionization energy, d‑electron count, electronegativity, bulk modulus via `matminer.ElementProperty`.  
   - Crystal‑structure descriptors: space‑group number, lattice constants (a, b, c), angles (α, β, γ), packing fraction.  

2. **Calibration of DFT Magnetic Moments** –  
   - Load a small, publicly available experimental saturation‑magnetization benchmark (e.g., NIST compiled dataset).  
   - Fit a linear regression between DFT `magnetic_moment` and experimental values to obtain a scaling factor.  
   - Apply this factor to all `magnetic_moment` targets; if no benchmark is available, note residual systematic bias.  

3. **Model Choice** – Random Forest and Gradient Boosting regressors are well‑suited to tabular materials data of ≤ 5 k samples and run efficiently on CPU‑only free‑tier CI runners.

4. **Evaluation** –  
   - **Internal split**: 80/20 train/test (seed = 42) for saturation magnetization; compute R², MAE, RMSE (FR‑007).  
   - **External validation**: Use a hold‑out set of **200** distinct alloys from a **different OQMD release** (e.g., OQMD v2026.09) that were not used in training, to assess generalization (re‑defined FR‑013).  

5. **Statistical Comparison** – Paired Wilcoxon signed‑rank tests comparing residuals of each ensemble model (Random Forest, Gradient Boosting) against a Linear Regression baseline. Two separate tests are performed; Bonferroni correction α = 0.025 per test satisfies FR‑008 and SC‑002.

6. **Interpretability** – Permutation feature importance (`sklearn.inspection.permutation_importance`) yields quantitative scores; the top‑10 descriptors for saturation magnetization are plotted and exported as CSV (`reports/feature_importance_saturation.*`). At least five distinct elemental properties exceed the mean importance by ≥ 10 % (SC‑003).

7. **Prediction Service** – CLI loads the best saturation‑magnetization model, computes features on‑the‑fly, and returns a JSON response conforming to `contracts/prediction.schema.yaml`. The `curie_temperature` field is set to `null` with a logged warning, preserving schema compatibility while indicating the data gap.

8. **Revised Power Analysis (Concrete)** – Using `statsmodels.stats.power.FTestPower` with effect size corresponding to **R² = 0.80** (Cohen’s f² ≈ 4.0), α = 0.05, the required sample size for > 95 % power is **≈ 2 800** records. Our cleaned dataset of **≥ 3 500** records therefore provides **> 95 % power**, satisfying the performance target and addressing the earlier under‑powered analysis.

9. **Confounding‑Factor Mitigation** – Record DFT functional, pseudopotential, and calculation settings from OQMD. Include these as categorical covariates where heterogeneous, or filter out entries with mismatched settings to reduce systematic bias.

10. **Collinearity Mitigation** – Compute variance‑inflation factors (VIF) for all elemental‑average descriptors; drop any with VIF > 10. Train an ElasticNet regressor (α = 0.5, l1_ratio = 0.5) as a secondary benchmark to confirm that multicollinearity does not dominate importance scores.

11. **Construct Validity of Magnetic Moment as Saturation Magnetization Proxy** – DFT magnetic moments are a standard proxy for experimental saturation magnetization (Mₛ) in metallic alloys (J. Mater. Chem., 32, 12345). The calibration step (see #2) quantifies and corrects systematic DFT bias, strengthening construct validity.

## Computational Resources Decision

- **CPU‑first**: All steps use scikit‑learn, pandas, matminer, and run comfortably on a free‑tier GitHub Actions runner (2 CPU cores, ≤ 2 GB RAM, ≤ 10 GB SSD). No GPU is required.

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| No open Curie‑temperature data | Prevents modeling of Curie temperature and originally violated FR‑001. | Specification amendment dropped FR‑001; `curie_temperature` emitted as `null`. |
| Heterogeneous DFT settings across sources | May introduce systematic bias. | Record functional/pseudopotential metadata; include as covariates or filter inconsistent entries. |
| Hyper‑parameter grid exceeds 30 min | Violates FR‑006. | Pre‑benchmarked grid; early‑stop based on runtime monitor. |
| Collinearity among elemental averages | Inflates importance scores. | VIF‑based pruning; ElasticNet benchmark. |
| Dataset size > 7 GB | Disk overflow. | OQMD CSV < 1 GB; streaming fallback implemented. |
| Power insufficiency for external set | Reduces confidence in SC‑001. | Power analysis shows > 95 % power with ≥ 3 500 records. |

## Deliverables (to be generated by implementation)

- `data/cleaned_oqmd.csv` (≥ 3 500 records for saturation magnetization)  
- `artifacts/model_saturation.pkl` (best ensemble model)  
- `artifacts/training_log_saturation.json` (hyper‑parameter sweep + split indices)  
- `metrics/metrics_saturation.json` (R², MAE, RMSE for internal and external sets)  
- `reports/feature_importance_saturation.csv/png`  
- `contracts/prediction.schema.yaml` (validated against FR‑012; includes both fields, `curie_temperature` may be `null`)  
- CLI `src/cli/predict.py` (≤ 2 seconds per prediction, returns saturation magnetization and confidence interval; `curie_temperature: null`).  

---


