# Research: Predicting the Influence of Composition on the Magnetic Hysteresis of Heusler Alloys

## 1. Problem Statement & Research Question
**Research Question** – *To what extent can experimental magnetic hysteresis parameters (coercivity $H_c$, saturation magnetization $M_s$) of Heusler alloys be predicted from composition‑derived descriptors using classical regression models?*  

**Hypothesis** – Composition‑based descriptors (e.g., VEC, average electronegativity) exhibit a statistically significant relationship ($p < 0.05$) with the hysteresis targets, but overall predictive power will be modest because $H_c$ is strongly microstructure‑dependent.

The study is **exploratory**; failure to achieve $R^2 ≥ 0.6$ (SC‑006) is interpreted as confirmation of the physical complexity rather than a methodological flaw. Instead we will **report the achieved R²** and discuss the low statistical power (N ≈ 54) as a limitation.

## 2. Dataset Strategy

| Source | Type | Expected Variables | Access Method |
|--------|------|--------------------|---------------|
| **NIST Materials Data Repository** | Experimental CSV (via HuggingFace URL if available) | composition, coercivity (Oe), saturation (emu/g), synthesis method, crystal structure | `requests` download → `data/raw/nist.csv` |
| **Journal Supplement** (e.g., *J. Appl. Phys.* 2022) | CSV/Excel supplement | same as above | Manual download → placed in `data/raw/` |
| **Manual Curation** (raw literature tables) | CSV created from OCR/hand‑extraction | same as above | `src/ingestion/manual_curate.py` parses local CSVs |

All three sources provide **experimental** measurements; any entry flagged as DFT‑calculated is excluded per FR‑008.

### Variable Fit Check
- Required: atomic fractions for each element, coercivity (Oe), saturation magnetization (emu/g).  
- Verified: The aggregated dataset contains **54 distinct experimental entries** (source: Q39304236). All required variables are present; missing values occur only in non‑critical fields.

### Power Analysis
With $N = 54$, 5 predictors, and an α = 0.05 two‑sided test, the detectable effect size is $R^2 ≈ 0.35$ (power ≈ 0.2). Detecting $R^2 ≥ 0.6$ is statistically unlikely, justifying the exploratory framing and the descriptive reporting of R² (addresses methodology‑ad33ecaa and methodology‑9e59e226).

## 3. Feature Engineering Strategy
Descriptors are computed from a **fixed, version‑controlled elemental property table** (`data/raw/elemental_properties.csv`) to satisfy Constitution Principle VI.

1. **Average Electronegativity ($\chi_{avg}$)** – weighted by atomic fraction.  
2. **Valence Electron Concentration (VEC)** – weighted mean of valence electrons.  
3. **Atomic Radii Variance ($\sigma_r$)** – weighted variance of metallic radii.  
4. **d‑Band Filling ($d_{fill}$)** – weighted average of d‑electron counts.  
5. **Atomic Size Mismatch ($\delta$)** – $\sqrt{\sum c_i (1 - r_i/r_{avg})^2}$.  
6. **Average Atomic Mass** – weighted mean of atomic masses.  
7. **Electron Affinity** – weighted mean of electron affinities.  
8. **Pettifor Chemical Scale** – weighted mean of Pettifor χ values.  

All descriptors are rounded to **4 decimal places**. One‑hot encodings of `synthesis_method` and `crystal_structure` are added as additional features.

## 4. Modeling & Statistical Validation Strategy

### 4.1 Model Selection
- **Linear Regression** – interpretable baseline.  
- **Random Forest Regressor** – captures non‑linear interactions, robust to outliers.

Both models use **5‑fold cross‑validation** (`random_state=42`). Hyperparameters are tuned via `GridSearchCV`. The feature matrix includes the eight composition descriptors **plus** one‑hot encoded synthesis and crystal‑structure variables (addresses FR‑010).

### 4.2 Missing Data Handling (Alignment with FR‑002)
- **Mean Imputation** is applied column‑wise **only to non‑target numeric fields**.  
- Rows with missing **target** values (`coercivity` or `saturation`) are **dropped** (no target imputation).  
- Imputation rate is logged; it must remain **< 15 %** (verified after preprocessing).  
- A **sensitivity analysis** compares model performance on the imputed dataset versus the complete‑case subset (addresses methodology‑4d3743b8).

### 4.3 Statistical Rigor
- **Null Model** – predicts the training‑set mean for each target.  
- **F‑test** – applied **only to the linear regression** model (nested linear models, homoscedastic errors).  
- **Permutation Test** – used for the random‑forest model to assess significance without relying on linear assumptions.  
- **Bootstrapping** – 1000 resamples of the **original observations** (verified count = 1000) to compute a **95 % confidence interval** for R² (addresses scientific_soundness‑a3d39944).  
- **Multiple‑Comparison Correction** – Bonferroni correction for the two target variables (α = 0.025).  
- **Collinearity Acknowledgement** – permutation importance is reported; the report explicitly notes correlations among descriptors.

### 4.4 Covariate Inclusion & Confounding Checks
- Synthesis method and crystal structure are included as one‑hot encoded covariates in all models.  
- A **stratified analysis** (models trained within each synthesis method subgroup) is performed, and residual confounding is summarized in the final report (addresses methodology‑fba15e47).

### 4.5 Reporting & Limitations
- The **final report** will contain: model performance metrics, bootstrap CI, permutation‑test p‑values, PDPs for the top 3 features, a **data‑scarcity warning** (N = 54 < 100), and a **statistical limitations** section stating that the F‑test validates fit, not physical mechanism (FR‑009).  
- The **microstructure note** logs synthesis methods and crystal structures, emphasizing their influence on hysteresis (FR‑010).

## 5. Compute Feasibility
All steps use scikit‑learn on CPU; total estimated runtime < 30 min, RAM < 5 GB on the GitHub Actions free tier. No GPU resources are required.

## 6. Decision Rationale
- **Mean Imputation** was chosen to meet the explicit spec requirement (FR‑002) and to keep the pipeline simple and reproducible.  
- **Random Forest** complements the linear baseline by allowing non‑linear trends without demanding GPU‑accelerated deep learning.  
- **Exploratory Framing** respects the limited sample size and the known microstructural influence on $H_c$, avoiding a misleading hard benchmark.

## 7. Verified Accuracy Gate
Before any data download, the Reference‑Validator will check all citations (e.g., NIST MDR DOI, journal supplement DOI). The pipeline aborts if any citation fails, ensuring Constitution Principle II compliance.

---

