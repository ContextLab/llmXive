# Specification: Quantifying the Impact of Dataset Size on ML Accuracy for Material Properties

## 1. Introduction
This project investigates how the size of training datasets affects the accuracy of machine learning models predicting material properties. We focus on composition-only descriptors (Magpie vectors) to predict properties without requiring crystal structure data.

## 2. Objectives
- Download standardized material property datasets.
- Compute Magpie composition descriptors.
- Generate learning curves for multiple properties.
- Fit power-law scaling models ($Error = a \cdot N^{-b}$).
- Analyze correlations between physical characteristics and scaling exponents.
- Perform statistical validation between property classes.

## 3. Data Sources
- **HuggingFace Datasets**: Materials Project and AFLOW subsets.
- **Descriptors**: Magpie (composition-only) vectors.
- **Properties**: Formation Energy, Band Gap, and other available properties (N=2-3).

## 4. Methodology

### 4.1 Data Acquisition
- Fetch data from HuggingFace with exponential backoff.
- Compute Magpie descriptors for all entries.
- Consolidate into `data/processed/materials_master.parquet`.

### 4.2 Learning Curve Construction
- Generate 5 training subsets per property: `[1000, 5000, 10000, 20000, 40000]`.
- Train Random Forest regressors with **1 random seed** per subset (Amendment 001).
- Evaluate on a fixed test set.

### 4.3 Scaling Analysis
- Fit power-law model: $Error = a \cdot N^{-b}$.
- Classify as "non-power-law" if $R^2 < 0.9$.
- Output `data/processed/scaling_results.csv`.

### 4.4 Statistical Validation
- Compute physical metrics: "spatial locality" and "symmetry sensitivity".
- **Statistical Test**: Perform a **Permutation Test** to compare scaling exponents between electronic and mechanical classes (Amendment 003).
- **Note**: Due to the small number of available properties (N=2-3), standard tests (Kruskal-Wallis/ANOVA) are invalid. The Permutation Test is the mandated method.

## 5. Success Criteria (Amended)

### SC-001: Data Coverage and Analysis
- **Original**: Analyze 15 properties.
- **Amended**: Analyze **all available properties** (N=2-3) as identified by the data validation step.
- **Success**:
 1. Learning curves generated for all available properties.
 2. Power-law fits computed (or flagged as non-power-law).
 3. Permutation Test executed on the available classes.
 4. Final report includes exact p-values and scaling exponents.

### SC-002: Statistical Rigor
- **Original**: Achieve p < 0.05 using Kruskal-Wallis/ANOVA.
- **Amended**: Execute a valid **Permutation Test** for N < 5. Report the exact p-value.
- **Success**: The p-value is calculated correctly based on the permutation distribution. The result is interpreted in the context of the small sample size (N=2-3), acknowledging the limited power.

## 6. Deliverables
- `data/processed/materials_master.parquet`: Consolidated dataset.
- `data/processed/scaling_results.csv`: Exponents, intercepts, R², fit status.
- `data/processed/final_analysis.csv`: Correlation results and permutation test p-values.
- `figures/`: Learning curve plots, heatmaps.
- `state/amendments.md`: Formal record of protocol deviations.

## 7. Constraints & Assumptions
- **Compute**: Peak RAM < 7GB.
- **Data**: Only composition-only descriptors are used.
- **Sample Size**: The number of available properties is limited to N=2-3.
- **Statistical Method**: Permutation Test is used for N < 5.

## 8. Revision History
- **v1.0**: Initial draft.
- **v1.1**: Updated to reflect Amendment 001 (5x1 sampling), Amendment 002 (N=2-3 data), Amendment 003 (Permutation Test), and Amendment 004 (SC-001 modification).