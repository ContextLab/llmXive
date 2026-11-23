# Research: Predicting the Glass Forming Region of Alloy Systems with Machine Learning

## Objective
The objective is to determine if the critical cooling rate (CCR) of ternary alloys can be predicted using three fundamental thermodynamic descriptors derived from elemental properties in the Open Quantum Materials Database (OQMD).

## Dataset Strategy
| Role | Source | Access Method | Variables | Notes |
|------|--------|---------------|-----------|-------|
| **Elemental Properties** | OQMD | `datasets.load_dataset("materials-toolkits/oqmd", streaming=True)` | Atomic radius, Electronegativity, Formation enthalpy | Verified URLs provided in block. |
| **Alloy CCR** | Experimental Dataset | Programmatic download (URL pending verification) | Composition, measured CCR | **CRITICAL**: No verified URL provided in "Verified Datasets" block. Implementation requires a verified open source to proceed. |

## Feature Engineering
The pipeline computes three descriptors for each ternary alloy $(A, B, C)$ with fractions $(x_A, x_B, x_C)$:

1. **Mixing Enthalpy ($\Delta H_{mix}$)**: Calculated as the weighted sum of elemental formation enthalpies from OQMD.
2. **Atomic Size Difference ($\delta$)**: 
   $$\delta = 100 \sqrt{\sum_{i=1}^{n} x_i \left(1 - \frac{r_i}{\bar{r}}\right)^2}$$
   where $\bar{r}$ is the average atomic radius.
3. **Electronegativity Variance ($\sigma_{\chi}$)**:
   $$\sigma_{\chi} = \sqrt{\sum_{i=1}^{n} x_i (\chi_i - \bar{\chi})^2}$$
   where $\bar{\chi}$ is the average Pauling electronegativity.

**Verification**: Results will be compared against reference calculations for standard alloys (e.g., Zr-Cu-Al) within a tolerance of $\pm 0.01$ for $\delta$ and $\pm 0.005$ for $\sigma_{\chi}$.

## Modeling & Statistical Rigor
- **Algorithm**: Random Forest Regressor. Chosen due to the expected non-linear relationship between thermodynamic descriptors and CCR.
- **Validation**: 80/20 train-test split. 5-fold cross-validation on the training set to estimate generalization error.
- **Baseline**: A dummy regressor (predicting the mean CCR) serves as the null model. A paired permutation test on per-fold RMSE differences (10,000 permutations) will determine if the RF model is statistically superior ($p < 0.05$) to the dummy regressor.
- **Causal Inference**: As the dataset is observational, all findings are framed as **associational**.
- **Power**: With $N \ge 500$, the study is powered to detect moderate effect sizes (Cohen's $d \approx 0.5$) at $\alpha = 0.05$.

## Evaluation Rigor
- **Permutation Importance**: To avoid the bias of "impurity-based" importance in RF, `sklearn.inspection.permutation_importance` will be used with $n=1000$ permutations. A feature is considered significant if its importance is higher than the shuffled baseline with $p < 0.05$.
- **Sensitivity Analysis**: The model's performance will be evaluated as a classifier across thresholds $[50, 100, 150]$ K/s.
- **Multiple Comparison Correction**: A Bonferroni correction ($\alpha_{adj} = 0.05 / 3 \approx 0.0167$) will be applied to the three threshold tests to control the family-wise error rate.

## Compute Feasibility
- **CPU-First**: RF training on $N \approx 1000$ samples with 3 features is computationally trivial.
- **Memory**: OQMD data will be streamed. Total RAM usage is expected to be $< 2$ GB, well within the 7 GB CI limit.
- **Disk**: Artifacts are small CSVs/JSONs, fitting within the 14 GB limit.

## Limitations (FR-007)
The model uses only three thermodynamic descriptors. It omits:
- **Electronic Structure**: Density of states, valence electron concentration.
- **Processing History**: Cooling method, purity of precursors.
- **Structural Data**: Short-range order, coordination numbers.
These omissions may introduce bias and are documented in the final report.