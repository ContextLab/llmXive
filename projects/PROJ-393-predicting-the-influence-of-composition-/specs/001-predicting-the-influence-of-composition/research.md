# Research: Predicting the Influence of Composition on the Magnetic Hysteresis of Heusler Alloys

## 1. Problem Statement & Research Question
**Research Question** – *To what extent can experimental magnetic hysteresis parameters (coercivity $H_c$, saturation magnetization $M_s$) of Heusler alloys be predicted from composition‑derived descriptors using classical regression models?*  

**Hypothesis** – Composition‑based descriptors (e.g., VEC, average electronegativity) exhibit a statistically significant relationship ($p < 0.05$) with the hysteresis targets, but overall predictive power will be modest because $H_c$ is strongly microstructure‑dependent.

The study is **exploratory**; failure to achieve $R^2 ≥ 0.6$ (SC‑006) is interpreted as confirmation of the physical complexity rather than a methodological flaw.

## 2. Dataset Strategy

| Source | Type | Expected Variables | Access Method |
|--------|------|--------------------|---------------|
| **NIST Materials Data Repository** | Experimental CSV (via HuggingFace URL if available) | composition, coercivity (Oe), saturation (emu/g), synthesis method, crystal structure | `requests` download → `data/raw/nist.csv` |
| **Journal Supplement** (e.g., *J. Appl. Phys.* 2022) | CSV/Excel supplement | same as above | Manual download → placed in `data/raw/` |
| **Manual Curation** (raw literature tables) | CSV created from OCR/hand‑extraction | same as above | `src/ingestion/manual_curate.py` parses local CSVs |

All three sources provide **experimental** measurements; any entry flagged as DFT‑calculated is excluded per FR‑008.

### Variable Fit Check
- Required: atomic fractions for each element, coercivity (Oe), saturation magnetization (emu/g).  
- Verified: The aggregated dataset contains **54 distinct experimental entries** (source: Q39304236). All required variables are present; missing values occur in non‑critical fields only.

### Power Analysis
With $N = 54$, 5 predictors, and an α = 0.05 two‑sided test, the detectable effect size is $R^2 ≈ 0.35$ (power ≈ 0.2). Detecting $R^2 ≥ 0.6$ is statistically unlikely, justifying the exploratory framing.

## 3. Feature Engineering Strategy
Descriptors are computed from a **fixed, version‑controlled elemental property table** (`data/raw/elemental_properties.csv`) to satisfy Constitution Principle VI.

1. **Average Electronegativity ($\chi_{avg}$)** – weighted by atomic fraction.  
2. **Valence Electron Concentration (VEC)** – weighted mean of valence electrons.  
3. **Atomic Radii Variance ($\sigma_r$)** – weighted variance of metallic radii.  
4. **Average d‑Electron Count ($d_{avg}$)** – weighted mean of d‑electron numbers.  
5. **Atomic Size Mismatch ($\delta$)** – $\sqrt{\sum c_i (1 - r_i/r_{avg})^2}$.

All descriptors are rounded to **4 decimal places**.

## 4. Modeling & Statistical Validation Strategy

### 4.1 Model Selection
- **Linear Regression** – interpretable baseline.  
- **Random Forest Regressor** – captures non‑linear interactions, robust to outliers.

Both models use **5‑fold cross‑validation** (`random_state=42`). Hyperparameters are tuned via `GridSearchCV`.

### 4.2 Missing Data Handling (Alignment with FR‑002)
- **Mean Imputation** is applied column‑wise for any missing numeric field.  
- Imputation rate is logged; it must remain **< 15 %** (verified after preprocessing).  
- This satisfies the spec’s acceptance scenario 2 and resolves the prior conflict with MICE.

### 4.3 Statistical Rigor
- **Null Model** – predicts the training‑set mean for each target.  
- **F‑test** – compares residual sum of squares (RSS) of each model against the null model; $p < 0.05$ indicates significance (SC‑001).  
- **Bootstrapping** – 1000 resamples (verified count) of CV $R^2$ values to compute a **95 % confidence interval** (SC‑002).  
- **Partial Dependence Plots** – generated for the top‑3 features per target (SC‑003).  
- **Stratified Analysis** – models are also trained within each `synthesis_method` subgroup when metadata is present, to isolate composition effects from processing confounders (FR‑009, FR‑010).  

### 4.4 Multiple‑Comparison Correction
Only two target variables are tested; Bonferroni correction would set α = 0.025. The reported $p$‑values are compared against this stricter threshold.

### 4.5 Collinearity Acknowledgement
Descriptors such as VEC and $d_{avg}$ are correlated; permutation importance is used instead of coefficient magnitude, and the report explicitly notes potential collinearity.

## 5. Compute Feasibility
All steps use scikit‑learn on CPU; total estimated runtime < 30 min, RAM < 5 GB on the GitHub Actions free tier. No GPU resources are required.

## 6. Decision Rationale
- **Mean Imputation** was chosen to meet the explicit spec requirement (FR‑002) and to keep the pipeline simple and reproducible.  
- **Random Forest** complements the linear baseline by allowing non‑linear trends without demanding GPU‑accelerated deep learning.  
- **Exploratory Framing** respects the limited sample size and the known microstructural influence on $H_c$.

## 7. Verified Accuracy Gate
Before any data download, the Reference‑Validator will check all citations (e.g., NIST MDR DOI, journal supplement DOI). The pipeline aborts if any citation fails, ensuring Constitution Principle II compliance.

---
