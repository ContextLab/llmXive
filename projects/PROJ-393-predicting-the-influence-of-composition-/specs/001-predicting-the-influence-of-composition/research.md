# Research: Predicting the Influence of Composition on the Magnetic Hysteresis of Heusler Alloys

## 1. Problem Statement & Research Question
**Research Question**: To what extent can the magnetic hysteresis parameters (coercivity $H_c$, saturation magnetization $M_s$) of Heusler alloys be predicted solely from their elemental composition using classical regression models?

**Hypothesis**: Composition-derived descriptors (VEC, electronegativity variance) have a statistically significant ($p < 0.05$) relationship with hysteresis parameters. However, given that $H_c$ is a microstructure-dependent property, we hypothesize that the global predictive power ($R^2$) will be limited, and any observed correlation is likely a first-order approximation or confounded by synthesis methods.

**Study Nature**: **Exploratory**. This study is not designed to confirm a causal mechanism but to investigate whether composition provides *any* predictive signal in the absence of microstructural data.

## 2. Dataset Strategy

### 2.1 Verified Sources & Availability
**Critical Finding**: The "Verified datasets" block provided in the project context contains URLs for NIST *security standards* (800-53), LLM benchmarks, and unrelated music/banking datasets. **None** of these contain Heusler alloy magnetic data.

**Action Plan**: As per **FR-001** and the project's **Assumptions**, the system will **not** use the irrelevant URLs provided in the prompt. Instead, the ingestion pipeline will be designed to fetch from the *actual* scientific repositories required by the spec:
1.  **NIST Materials Data Repository (MDR)**: The primary source for experimental magnetic data.
2.  **Journal Supplements**: Data extracted from supplements of key papers (e.g., *Journal of Applied Physics*, *Acta Materialia*) covering Heusler alloys.
3.  **Manual Curation**: A script to parse raw text/tables from literature where API access is unavailable.

**Dataset Fit Analysis**:
-   **Required Variables**: Composition (atomic %), $H_c$ (Oe), $M_s$ (emu/g), Synthesis Method, Crystal Structure.
-   **Potential Mismatch**: Many public datasets report *calculated* (DFT) magnetic moments rather than *experimental* hysteresis loops.
-   **Mitigation**: The `preprocessing` module will strictly filter out any entry where the source metadata indicates "DFT", "Calculated", or "Simulation" for the target variables, as mandated by **FR-008**. Only entries with explicit "Experimental" or "Measured" flags will be retained for training.

### 2.2 Data Volume & Power Analysis
-   **Target**: ≥50 experimental data points (Spec Assumption).
- **Power Analysis**: With $N \approx 50$ and 5 predictors, a linear model has [deferred] power to detect an $R^2$ of ~0.3 at $\alpha=0.05$.
-   **Critical Limitation**: Detecting an effect size corresponding to $R^2 \ge 0.6$ (SC-006) with $N=50$ is statistically **improbable** unless the effect is extremely strong. Given the physical reality that $H_c$ is microstructure-dependent, a global $R^2 \ge 0.6$ is physically unrealistic.
-   **Conclusion**: The study is framed as **Exploratory**. Failure to meet $R^2 \ge 0.6$ is not considered a "failure" of the model but a confirmation of the physical complexity of the system.

## 3. Feature Engineering Strategy

To satisfy **FR-003**, the following descriptors will be computed for every alloy entry:
1.  **Average Electronegativity ($\chi_{avg}$)**: Weighted mean of constituent elements' Pauling electronegativity.
2.  **Valence Electron Concentration (VEC)**: Weighted mean of valence electrons per atom.
3.  **Atomic Radii Variance ($\sigma_r$)**: Standard deviation of atomic radii, weighted by composition.
4.  **Average d-Electron Count ($d_{avg}$)**: Weighted mean of d-electrons (crucial for magnetic properties).
5.  **Atomic Size Mismatch ($\delta$)**: $\sqrt{\sum c_i (1 - r_i/r_{avg})^2}$.

**Data Source for Descriptors**: A **local, pinned CSV** of elemental properties (electronegativity, radius, valence) will be used to ensure **Constitution Principle VI** (Computational Descriptor Consistency). No dynamic libraries (e.g., `mendeleev`) will be used to prevent drift.

## 4. Modeling & Statistical Validation Strategy

### 4.1 Model Selection
-   **Baseline**: Linear Regression (interpretable, low computational cost).
-   **Primary**: Random Forest Regressor (captures non-linear interactions, robust to outliers).
-   **Validation**: 5-fold Cross-Validation (fixed split).
-   **Hyperparameter Tuning**: Grid search over `n_estimators`, `max_depth` (for RF) and `alpha` (for Linear).

### 4.2 Statistical Rigor & Confounder Control
-   **Null Hypothesis**: The model performs no better than predicting the mean target value.
-   **F-Test**: Comparison of residual sum of squares (RSS) between the fitted model and the null model. $p < 0.05$ required for significance (**SC-001**).
-   **Confidence Intervals**: 1000-resample bootstrapping to determine 95% CI for $R^2$ (**SC-002**).
-   **Stratified Analysis**: To address the **microstructure confounder** (Methodology Concern), the analysis will be stratified by `synthesis_method` (e.g., Arc-melted vs. Sputtered) where metadata exists. This isolates composition effects within homogeneous processing groups.
-   **Interpretability**: Partial Dependence Plots (PDP) for the top 3 features (**SC-003**).

### 4.3 Limitations & Confounders (Explicit Acknowledgement)
-   **Microstructure**: Hysteresis is heavily influenced by grain size, defects, and phase purity. The model will **only** capture *composition* effects.
-   **Causal Validity**: **FR-009** and **FR-010** mandate that the report explicitly states the F-test validates *fit*, not *mechanism*. The model cannot distinguish composition effects from processing effects without microstructural features.
-   **Collinearity**: Descriptors like VEC and $d_{avg}$ may be correlated. Permutation importance will be used to rank features, acknowledging potential collinearity.
-   **Small Sample Size**: With N < 50, the F-test is sensitive to outliers. Sensitivity analysis will be performed.

## 5. Compute Feasibility
-   **Hardware**: GitHub Actions (2 CPU, 7GB RAM).
-   **Method**: No deep learning; only `scikit-learn` models.
-   **Data Size**: Expected dataset < 1000 rows. Fits easily in RAM.
-   **Runtime**: Ingestion + Feature Engineering + Training + Validation estimated at < 30 minutes. Well within the 6-hour limit.

## 6. Decision Rationale
-   **Why Random Forest?** Heusler alloy properties often exhibit non-linear thresholds (e.g., phase transitions at specific VEC values). RF handles this better than Linear Regression without the overhead of neural networks.
-   **Why Exclude DFT?** DFT data often uses idealized structures and lacks the defect physics that drive hysteresis. Mixing DFT and experimental data would introduce systematic bias.
-   **Why Manual Curation?** No single API provides a unified, clean dataset of Heusler hysteresis. Aggregation is the only viable path to reach the $N \ge 50$ target.
-   **Why Exploratory?** The combination of small N and high confounding (microstructure) makes confirmatory claims scientifically unsound. The study aims to generate hypotheses for future work with larger, more controlled datasets.

## 7. Verified Accuracy Gate
Before data ingestion, the Reference-Validator Agent will verify all citations in this document against primary sources. If any citation fails validation, the pipeline will halt, ensuring **Constitution Principle II** is enforced.