# Research: Predicting Glass Formation Tendency with Machine Learning on Public Data

## Overview

This research plan investigates the predictability of metallic glass formation using thermodynamic descriptors derived from chemical composition. The study leverages a **verified, static public dataset** (Matbench Glass Formation Benchmark) to train an XGBoost model, aiming to identify key descriptors (e.g., mixing enthalpy, atomic size mismatch) that align with Inoue's rules. The plan explicitly addresses data availability, statistical power, and the risk of tautological validation.

## Dataset Strategy

### Verified Datasets

The plan relies **exclusively** on the following verified datasets to ensure reproducibility and avoid runtime discovery failures:

- **Primary Dataset**: Matbench Glass Formation Benchmark
  - **Source URL**: `https://github.com/materialsvirtuallab/matbench` (or the specific Zenodo DOI for the glass dataset, e.g., `10.5281/zenodo.xxxxxx` if available)
  - **Target Variable**: Continuous critical casting thickness ($D_c$) or binary glass/crystal label.
  - **Access Method**: `matbench.load_dataset('glass_formation')` or direct CSV download.
  - **Status**: **Verified**. This dataset is known to contain experimental glass formation labels.

- **Fallback Dataset**: UCI Glass Identification
  - **Source URL**: `https://archive.ics.uci.edu/ml/datasets/glass+identification`
  - **Target Variable**: Binary (Glass vs. Crystal) or Type of Glass.
  - **Access Method**: `sklearn.datasets.fetch_openml(name="glass")` or direct CSV download.
  - **Status**: **Verified**. This dataset is known to contain binary glass labels, but lacks continuous $D_c$. If used, the research question is re-framed to "Binary Glass Formation Prediction".

**Fallback Strategy**: If the Matbench dataset is unreachable, the pipeline attempts to load the UCI Glass Identification dataset. If neither is available, the pipeline halts with a `DataValidationError`. No dynamic discovery of alternative sources (e.g., Zenodo, Materials Project) is permitted, as these often lack the specific target variable or require authentication, violating Principle II (Verified Accuracy).

**Dataset Table**:

| Dataset Name | Source Type | Target Variable | Access Method | Status |
| :--- | :--- | :--- | :--- | :--- |
| Matbench Glass Formation | Matbench / Zenodo | Continuous $D_c$ or Binary | `matbench.load_dataset('glass_formation')` | Verified |
| UCI Glass Identification | UCI | Binary | `sklearn.datasets.fetch_openml(name="glass")` | Verified (Fallback) |

### Data Availability & Feasibility

- **Feasibility**: The plan assumes the Matbench dataset contains ≥ 30 samples. If the dataset size is < 30, the pipeline halts.
- **Streaming**: If the dataset > 7GB (unlikely for this specific domain), the code will use `pandas.read_csv(..., chunksize=...)` to stream and aggregate statistics.
- **Data Hygiene**: Raw downloads are saved to `data/raw/` with SHA256 checksums recorded in `state/artifacts.yaml`. Processed data is also checksummed.

## Methodology

### Feature Engineering (Descriptors)

The core hypothesis is that thermodynamic properties derived from composition predict glass formation.
1.  **Atomic Size Mismatch ($\delta$)**: Calculated using atomic radii from `pymatgen`.
2.  **Mixing Enthalpy ($\Delta H_{mix}$)**: Calculated using `pymatgen`'s thermodynamic database.
3.  **Electronegativity ($\Delta \chi$)**: Calculated using Pauling electronegativities.
4.  **Entropy of Mixing ($\Delta S_{mix}$)**: Optional, if data supports.

*Validation*: `pymatgen` will be used to ensure all elements in the dataset have known properties. Unknown elements will be logged and samples excluded.

### Ground Truth Verification

**Critical Step**: Before training, the system must verify that the target variable (e.g., $D_c$ or binary label) is an **experimental observation** from literature, NOT a value calculated from the same descriptors (e.g., a rule-based "Glass" label derived from $\Delta H_{mix}$ thresholds). If the target is derived from the features, the model will simply recover the physical rule (tautology). The plan mandates checking the dataset's metadata for "experimental" or "measured" tags. If the target is found to be a derived proxy for the descriptors, the plan will flag this as a "Potential Tautology" and halt or proceed with a severe warning.

### Binary Task Validity Check

If the target is binary, the system must verify that the binary labels are derived from experimental observations (e.g., 'glass formed at cooling rate X') and not from the descriptors themselves. It also adds a requirement to report the 'class balance' and 'feature separability' (e.g., via t-SNE or PCA) to ensure the binary task is not trivial. If the task is trivial (e.g., perfect separation by a single descriptor), the plan halts with a "Trivial Task" warning.

### Confounding Check

Glass formation is sensitive to cooling rate. Public datasets often mix samples prepared at different rates. The plan requires:
- If the dataset lacks cooling rate metadata, the report must explicitly state: "Model trained on data with mixed processing conditions; results reflect associations under heterogeneous conditions."
- If cooling rate is available, the model will control for it (if continuous) or stratify by it (if categorical).

### Modeling Strategy

- **Algorithm**: XGBoost (Gradient Boosting).
- **Mode Selection**:
  - If $D_c$ (continuous) is present: **Regressor** (Target: $D_c$).
  - If only Binary Label (Glass/Crystal) is present: **Classifier**.
- **Constraints**:
  - **CPU-Only**: `tree_method='hist'` or `approx` for efficiency.
  - **Memory**: Batch processing if needed (though unlikely for < 1000 samples).
  - **Reproducibility**: `random_state=42` for all splits and model initialization.
  - **Cross-Validation**: **Group K-Fold** (grouped by chemical family, e.g., Zr-based, Cu-based) to prevent data leakage from similar compositions.

### Statistical Rigor

- **Power Analysis**: A power calculation will be performed to determine the Minimum Detectable Effect Size (MDES) given the sample size (N) and number of predictors (k). The formula for MDES in regression is:
  $MDES = \sqrt{\frac{F_{critical} \cdot (1 - R^2_{null})}{N - k - 1}}$
  where $F_{critical}$ is derived from the F-distribution at $\alpha=0.05$ and power=0.80. The plan mandates running this calculation at runtime using `statsmodels.stats.power.FTestPower` and logging the result. If N is insufficient for a medium effect size, the report will explicitly flag this as a limitation.
- **Multiple Comparisons**: Not applicable for a single primary model, but if multiple descriptor subsets are tested, Bonferroni correction will be applied to p-values.
- **Causal Framing**: All results will be framed as **associational**. No causal claims (e.g., "increasing $\Delta H_{mix}$ *causes* glass formation") will be made.
- **Collinearity**: Variance Inflation Factor (VIF) will be computed for top predictors. High VIF (> 5 or 10) will be reported as a limitation, acknowledging physical correlations between descriptors. The plan explicitly notes that high VIF may indicate the model is recovering known physical definitions rather than new patterns.

## Decision Rationale

| Decision | Rationale |
| :--- | :--- |
| **Matbench Glass Formation** | Verified, open, and contains the required target variable. Avoids the "dynamic discovery" failure mode. |
| **UCI Glass Identification (Fallback)** | Verified, open, and contains binary labels. Used if Matbench is unavailable, with a re-framed research question. |
| **XGBoost over Neural Nets** | XGBoost is robust on small tabular datasets, interpretable, and runs efficiently on CPU (meeting the 2-core constraint). |
| **CPU-Only Execution** | The dataset size (≤ 1000 samples) does not require GPU acceleration. This ensures the pipeline runs on standard CI runners. |
| **Group K-Fold CV** | Prevents data leakage from chemically similar samples, ensuring the model generalizes to novel chemical spaces. |
| **Associational Framing** | The data is observational (public repositories). Causal inference requires randomized experiments or specific instrumental variables not present here. |

## Risk Assessment

- **Data Scarcity**: If Matbench (or UCI) is unreachable or < 30 samples. *Mitigation*: Pipeline halts with `DataValidationError`.
- **Missing Descriptors**: If `pymatgen` lacks properties for rare earth elements in the dataset. *Mitigation*: Exclude samples with unknown elements and log the count.
- **Collinearity**: High correlation between descriptors (e.g., mixing enthalpy and size mismatch) may inflate VIF. *Mitigation*: Report VIF scores and interpret feature importance with caution.
- **Tautology**: If the target variable is derived from the same descriptors. *Mitigation*: Check metadata; flag in report if tautology is suspected.
- **Confounding**: Missing cooling rate data. *Mitigation*: Explicitly state limitation in the report.
- **Trivial Task**: If the binary classification task is trivial (perfect separation). *Mitigation*: Halt with a "Trivial Task" warning.