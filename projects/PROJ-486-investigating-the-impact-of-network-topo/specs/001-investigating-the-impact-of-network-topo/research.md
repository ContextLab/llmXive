# Research: Investigating the Impact of Network Topology on Neural Entrainment to Rhythmic Stimuli

## Executive Summary

This research investigates the association between structural network topology (Clustering Coefficient, Path Length) and neural entrainment. Given the absence of a real-world dataset containing matched HCP fMRI connectivity and rhythmic entrainment metrics for the same subjects (Assumption in Spec), the primary execution path utilizes a **Simulated Data Fallback** (FR-009).

**Methodological Framing**: The simulation generates data with a known ground-truth correlation (r=0.5) strictly for **Pipeline Validation** (verifying the code detects the injected signal). The study explicitly acknowledges that it cannot test the biological hypothesis with current data availability. Success is defined by the pipeline's robustness, correct application of statistical corrections, and the generation of a power analysis for future real-data collection.

The analysis applies a deterministic statistical strategy (MLR or Univariate fallback based on VIF) with Holm-Bonferroni correction and evaluates robustness across Schaefer, AAL, and Power 264 parcellations.

## Dataset Strategy

### Primary Data Source: Simulation (FR-009)
Since no verified dataset exists for the specific combination of HCP resting-state topology and rhythmic entrainment, the system defaults to simulation.
- **Source**: `code/simulation.py`
- **Mechanism**: Generates synthetic `subject_id`, `clustering_coefficient`, `path_length`, and `entrainment_metric`.
- **Parameters**: Target correlation `r=0.5`, noise `= 0.2`.
- **Label**: All outputs will be tagged with `source: "Simulated"`.
- **Validation Role**: This data validates the *software* (does the pipeline detect r=0.5?). It does *not* validate the *hypothesis*.

### Verified Datasets (Reference Only)
The following datasets are listed in the project's verified sources but **cannot** be used for the primary matched analysis due to missing entrainment metrics:
- **HCP (Parquet)**: `
- **HCP (CSV)**: `
- **HCP (Parquet)**: `

*Note*: These datasets may be used for *simulating* realistic connectivity matrices if required, but the entrainment metric must be synthetic. The pipeline will attempt an inner join on `subject_id` if a user provides an external CSV; if the join yields N < 30, the simulation fallback is triggered immediately (FR-003).

## Statistical Methodology

### Deterministic Collinearity Decision Tree
To ensure the research question remains answerable and avoid unstable MLR coefficients, the following single decision tree is applied:
1. **Calculate VIF** for `clustering_coefficient` and `characteristic_path_length`.
2. **If VIF <= 5**:
 - Run **Multiple Linear Regression (MLR)**.
 - Report standardized coefficients, p-values, and joint R-squared.
 - Apply **Holm-Bonferroni** correction to the two predictor p-values.
3. **If VIF > 5** (or if the raw correlation between predictors > 0.7, which predicts high VIF):
 - **Do NOT run MLR** (coefficients would be unstable).
 - Run **Separate Univariate Analyses** (Spearman/Pearson) for each predictor against the outcome.
 - Apply **Holm-Bonferroni** correction to the two univariate p-values.
 - Report individual effect sizes and corrected p-values.
 - Flag `collinearity_warning` as `true`.
 - *Rationale*: This ensures the study can still determine if *either* metric is associated with entrainment, even if they cannot be disentangled in a joint model.

### Multiple Comparisons Correction
- **Method**: Holm-Bonferroni correction.
- **Scope**: Applied to the two tests (whether in MLR or Univariate mode).
- **Threshold**: Adjusted `p < 0.05` (FR-004, SC-003).

### Sensitivity Analysis
- **Atlases**: Schaefer (Primary), AAL, Power 264.
- **Metric**: Absolute difference in effect size (R-squared or Beta) compared to the Schaefer baseline.
- **Output**: Single comparative bar chart (FR-010).

## Power & Sample Size Considerations

### Simulation Power (Validated)
- **Target N**: 50 subjects.
- **Effect Size**: r=0.5 (injected).
- **Result**: N=50 is sufficient (>80% power) to detect r=0.5 at alpha=0.05. This validates the pipeline's ability to detect strong signals.

### Real-World Power (Exploratory)
- **Limitation**: If real data were available, typical neuroimaging effect sizes are often smaller (e.g., r=0.2).
- **Impact**: N=50 would be severely underpowered (power < 30%) to detect r=0.2.
- **Protocol**:
 - If real data yields N < 30, the system triggers the simulation fallback and flags `Power Warning: N < 30 (Exploratory)` (FR-002).
 - If real data yields N >= 30 but effect size is small, the report will explicitly state "Low Power for small effects" and frame results as exploratory.
- **Justification**: The study is explicitly framed as a **Pipeline Validation & Power Analysis**. The primary output is the *methodological framework* and the *demonstration of power limitations*, not a definitive biological claim.

## Decision Rationale (Compute Feasibility)
- **CPU-Only**: The pipeline uses `networkx` for graph metrics and `scikit-learn`/`scipy` for statistics. No GPU is required.
- **Memory**: N=50 with 200x200 matrices fits comfortably within 7GB RAM.
- **Runtime**: NetworkX graph metrics on 50 small graphs are computationally trivial (< 5 minutes). The MLR/Univariate and plotting steps are negligible. Total runtime is well under the -hour limit.