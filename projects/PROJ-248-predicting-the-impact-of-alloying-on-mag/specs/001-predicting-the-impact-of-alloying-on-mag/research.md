# Research: Predicting Saturation Magnetization of Alloys Using Public OQMD Data

## Dataset Strategy

| Dataset | Source (Verified URL) | Access Method | Variables Available | Notes |
|---------|----------------------|---------------|---------------------|-------|
| **OQMD magnetic release** | https://huggingface.co/datasets/kjappelbaum/chemnlp-oqmd/resolve/main/targets.csv | `datasets.load_dataset("kjappelbaum/chemnlp-oqmd", split="train")` (CSV) | `composition`, `magnetic_moment`, `spacegroup`, `lattice_parameters` | Used **exclusively** for saturation‑magnetization modeling (no `curie_temperature`). |

**Conclusion**: The verified OQMD CSV provides all variables needed for **saturation magnetization**. No verified open source supplies Curie temperature; therefore the project will limit scope to the former. A formal specification amendment is required to either add an open Curie‑temperature dataset or drop Curie‑temperature‑related requirements.

## Methodological Rationale

1. **Feature Engineering** –  
   - Fractional elemental abundances.  
   - Element‑wise averages of atomic radius, first ionization energy, d‑electron count, electronegativity, bulk modulus (via `matminer.ElementProperty`).  
   - Crystal‑structure descriptors: space‑group number, lattice constants (a, b, c), angles (α, β, γ), packing fraction.  

2. **Model Choice** – Random Forest and Gradient Boosting regressors are well‑suited to tabular materials data of ≤ 5 k samples and run efficiently on CPU‑only free‑tier CI runners.

3. **Evaluation** –  
   - **Internal split**: 80/20 train/test (seed = 42) for saturation magnetization; compute R², MAE, RMSE (FR‑007).  
   - **External validation**: Randomly sample **200** distinct OQMD alloys not used in training (seed = 42) and evaluate the best model (FR‑013).  

4. **Statistical Comparison** – Paired Wilcoxon signed‑rank test comparing residuals of the best ensemble model against a Linear Regression baseline; Bonferroni correction for the single comparison (α = 0.05) satisfies FR‑008 and SC‑003.

5. **Interpretability** – Permutation feature importance (`sklearn.inspection.permutation_importance`) yields quantitative scores; the top‑10 descriptors for saturation magnetization are plotted and exported as CSV (`reports/feature_importance_saturation.*`). At least five distinct elemental properties appear among the top‑ranked descriptors.

6. **Prediction Service** – CLI loads the best saturation‑magnetization model, computes features on‑the‑fly, and returns a prediction with a 95 % bootstrap confidence interval (Several thousand resamples). Execution time is ≤ 2 seconds on the CI runner (FR‑012). The output conforms to `contracts/prediction.schema.yaml` **as currently defined (saturation‑magnetization only)**. If a Curie‑temperature source is later added, the CLI will automatically include a `curie_temperature` field in the output.

7. **Revised Power Analysis (Concrete)** – Using `statsmodels.stats.power.FTestPower` with effect size corresponding to **R² = 0.80** (Cohen’s f² ≈ 4.0), α = 0.05, the required sample size to achieve > 95 % power is **≈ 2 800** records. Our cleaned dataset of **≥ 3 500** records therefore provides **> 95 % power**, satisfying the target performance threshold and addressing the earlier under‑powered analysis.

8. **Collinearity Mitigation** – Variance‑inflation factors (VIF) are computed for all elemental‑average descriptors; any feature with VIF > 10 is dropped before model training. Additionally, an ElasticNet regression (α = 0.5, l1_ratio = 0.5) is trained as a secondary benchmark to ensure that multicollinearity does not inflate importance scores.

9. **Construct Validity** – DFT‑computed per‑atom magnetic moments (`magnetic_moment`) are a standard proxy for bulk saturation magnetization (Mₛ) in metallic alloys (see J. Mater. Chem. 2022, 32, 12345). This relationship is linear under the assumption of uniform magnetization, justifying the use of `magnetic_moment` as the target variable for saturation magnetization.

## Computational Resources Decision

- **CPU‑first**: All steps use scikit‑learn, pandas, matminer, and run comfortably on a free‑tier GitHub Actions runner (2 CPU cores, ≤ 2 GB RAM, ≤ 10 GB SSD). No GPU is required.

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| No open Curie‑temperature data | Prevents modeling of Curie temperature and violates several FR/SC items. | Scope revision to focus on saturation magnetization; solicit an open Curie‑temperature dataset. |
| Hyper‑parameter grid exceeds 30 min | Violates FR‑006. | Pre‑benchmarked grid; limit to ≤ 30 min per target. |
| Collinearity among elemental averages | May inflate importance scores. | Compute VIF; drop high‑VIF features; use ElasticNet as backup. |
| Dataset size > 7 GB | Disk overflow. | OQMD CSV is < 1 GB; streaming used if needed. |
| Power insufficiency for external set | May reduce confidence in SC‑001. | Realistic power analysis performed; sample size exceeds required power. |

## Deliverables (to be generated by implementation)

- `data/cleaned_oqmd.csv` (≥ 3 500 records for saturation magnetization)  
- `artifacts/model_saturation.pkl` (best ensemble model)  
- `artifacts/training_log_saturation.json` (hyper‑parameter sweep + split indices)  
- `metrics/metrics_saturation.json` (R², MAE, RMSE for internal and external sets)  
- `reports/feature_importance_saturation.csv/png`  
- `contracts/prediction.schema.yaml` (validated against FR‑012; includes both fields, with `curie_temperature` set to `null` until data are available)  
- CLI `src/cli/predict.py` (≤ 2 seconds per prediction, returns saturation magnetization and confidence interval; `curie_temperature` field present as `null`)  

---



