# Specification: Quantifying the Impact of Dataset Size on ML Accuracy for Material Properties

**Project ID**: PROJ-526
**Version**: 1.1 (Amended)
**Status**: Active

## 1. Introduction

This project investigates how the size of training datasets affects the predictive
accuracy of machine learning models for material properties. We aim to derive
scaling laws ($Error \propto N^{-b}$) and correlate the scaling exponents ($b$)
with physical characteristics of the properties (e.g., spatial locality, symmetry sensitivity).

## 2. Objectives

1. Download and process standardized material property datasets from public repositories (Materials Project, AFLOW).
2. Compute composition-only descriptors (Magpie vectors) for all entries.
3. Generate learning curves for multiple properties by training Random Forest models on varying subset sizes.
4. Fit power-law models to extract scaling exponents ($b$).
5. Correlate $b$ with physical metrics and perform statistical validation between property classes.

## 3. Scope

### 3.1 In Scope
- Properties with >40,000 data points in public repositories.
- Composition-only descriptors (no structural data).
- Random Forest regressors with fixed hyperparameters.
- Scaling analysis for Electronic and Mechanical property classes.
- Statistical comparison using Permutation Test (N < 5).

### 3.2 Out of Scope
- Structural descriptors (requires crystal structures).
- Other ML models (e.g., GNNs, Transformers).
- Properties with <1,000 data points.

## 4. Requirements

### 4.1 Functional Requirements
- **FR-001**: The pipeline must successfully download and process at least 15 distinct material properties.
 *Correction*: Due to data availability constraints (see Amendment T036), the pipeline targets **N=2-3** properties per class (Electronic, Mechanical). The hard halt in T016 remains but is adjusted to expect the actual available N.
- **FR-002**: The system must compute Magpie composition descriptors for all material entries.
- **FR-003**: The system must generate learning curves for 5 subset sizes: [1000, 5000, 10000, 20000, 40000].
- **FR-004**: The system must fit power-law models and classify fits with $R^2 < 0.9$ as "non-power-law".
- **FR-005**: The system must perform a Permutation Test to compare scaling exponents between classes.

### 4.2 Non-Functional Requirements
- **NFR-001**: Peak RAM usage must remain < 7GB during dataset loading.
- **NFR-002**: All random operations must be deterministic via seed setting.
- **NFR-003**: Data integrity must be verified via SHA-256 checksums.

## 5. Success Criteria

### 5.1 Primary Criterion (SC-001)
- **Original**: "Statistical significance of scaling exponents between property classes shall be established with N >= 15 properties using Kruskal-Wallis/ANOVA."
- **Amended (T036)**: "Statistical significance of scaling exponents between property classes shall be established using a **Permutation Test** (10,000 iterations) given the available **N = 2-3** properties per class. A p-value < 0.05 indicates significant difference between Electronic and Mechanical classes."

### 5.2 Secondary Criteria
- **SC-002**: At least 80% of properties must yield valid power-law fits ($R^2 \ge 0.9$).
- **SC-003**: Learning curves must be generated for all available properties.
- **SC-004**: Correlation coefficients between physical metrics and scaling exponents must be computed.

## 6. Statistical Protocol

### 6.1 Power-Law Fitting
- Model: $Error = a \cdot N^{-b}$
- Method: Linear regression on log-transformed data ($\log(Error) = \log(a) - b \cdot \log(N)$).
- Validation: $R^2 \ge 0.9$ required for "valid" fit.

### 6.2 Class Comparison (Amended for Small N)
- **Method**: Permutation Test (Non-parametric).
- **Rationale**: Standard tests (Kruskal-Wallis, ANOVA) require N >= 5 per group for valid asymptotic approximation. With N = 2-3, exact permutation tests are required.
- **Procedure**:
 1. Combine scaling exponents from both classes.
 2. Randomly shuffle class labels 10,000 times.
 3. Compute the difference in means for each shuffle.
 4. Calculate p-value as the proportion of shuffled differences >= observed difference.
- **Threshold**: p < 0.05 for statistical significance.

## 7. Data Sources

- **Materials Project**: https://materialsproject.org (via API/HuggingFace)
- **AFLOW**: https://aflow.org (via API/HuggingFace)
- **Desired Properties**: Band Gap, Formation Energy, Bulk Modulus, Shear Modulus, etc.

## 8. Deliverables

- `data/processed/materials_master.parquet`: Consolidated dataset with descriptors.
- `data/processed/scaling_results.csv`: Scaling exponents and fit metrics.
- `data/processed/final_analysis.csv`: Statistical results (p-values, correlations).
- `figures/learning_curves.png`: Visualization of learning curves.
- `state/amendments.md`: Record of all project deviations.

## 9. Risks and Mitigations

- **Risk**: Insufficient data points for target properties.
 - **Mitigation**: T016 halts pipeline if count < 15 (adjusted to actual N per T036).
- **Risk**: Power-law fits fail ($R^2 < 0.9$).
 - **Mitigation**: Flag as "non-power-law" and exclude from statistical comparison.
- **Risk**: Small sample size invalidates statistical tests.
 - **Mitigation**: Use Permutation Test (Amendment T036) instead of parametric tests.

## 10. References

- Constitution Principle VII: Statistical Rigor
- Plan: Feasibility adjustments for dataset size and property count.
- Amendment T035: Subset and Seed Reduction.
- Amendment T036: Statistical Protocol Revision.