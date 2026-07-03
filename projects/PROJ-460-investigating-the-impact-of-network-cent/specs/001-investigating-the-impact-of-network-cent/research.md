# Research: Investigating Network Centrality in ASD Resting-State fMRI

## 1. Dataset Strategy

### Verified Sources
The project relies on the ABIDE (Autism Brain Imaging Data Exchange) dataset. Per the "# Verified datasets" block, the following sources are available and verified. Note: The provided URLs point to specific parquet files related to LLM leaderboards or generic ASD JSON files, which **do not** contain the raw fMRI time-series data required for this study (resting-state BOLD signals).

* **ABIDE (Parquet)**: `
 * *Status*: **UNSUITABLE**. This file contains LLM evaluation metrics, not fMRI data.
* **ABIDE (Parquet)**: `
 * *Status*: **UNSUITABLE**. LLM evaluation metrics.
* **ASD (JSON)**: `
 * *Status*: **UNSUITABLE**. Generic JSON, likely not structured fMRI data.

**Critical Gap Identified**: The verified dataset block **does not contain a source for raw resting-state fMRI data** (NIfTI files) or preprocessed time-series data required for FR-001 (Download) and FR-002 (Preprocessing). The spec assumes access to ABIDE raw data, but the verified list only provides LLM leaderboard details and generic JSONs.

**Resolution Strategy**:
1. **Immediate Action**: The plan **cannot** proceed with downloading raw fMRI data from the provided URLs as they do not contain the necessary neuroimaging data.
2. **Pipeline Halt**: The scientific analysis pipeline is **HALTED** at the Data Acquisition phase. **No synthetic data will be generated or used to simulate results.**
3. **Requirement for Progress**: To proceed, the `# Verified datasets` block must be updated with a valid source for raw ABIDE fMRI data (e.g., a verified HuggingFace dataset containing NIfTI files, or a direct link to the ABIDE repository).
4. **No Synthetic Fallback**: Synthetic data is strictly prohibited for scientific results. It may only be used in unit tests to verify code logic, not to answer the research question.

### Variable Fit Check
* **Required**: Raw fMRI NIfTI, Diagnosis (ASD/Control), Age, Sex, Motion Parameters.
* **Available (Verified)**: None of the verified URLs contain these variables.
* **Action**: The pipeline cannot proceed until a verified source containing these variables is identified and added to the dataset list.

### Scientific Validity
* **Hypothesis**: ASD group will exhibit altered network centrality (degree, betweenness, eigenvector) compared to controls in specific brain regions.
* **Data Requirement**: This hypothesis can **only** be tested with real biological data. Synthetic data, by definition, cannot validate this biological hypothesis.
* **Result Validity**: Any results generated from synthetic data are **illustrative only** and do not constitute scientific findings. The project will not generate or report any scientific results until real data is acquired.

## 2. Methodological Rigor

### Statistical Approach
* **Hypothesis**: ASD group will exhibit altered network centrality (degree, betweenness, eigenvector) compared to controls in specific brain regions.
* **Test**: Two-sample t-tests for each node and metric.
* **Correction**: False Discovery Rate (FDR) correction (Benjamini-Hochberg) applied across all tests (3 metrics × 400 nodes = 1200 tests).
* **Causal Framing**: Observational study. Claims will be restricted to "associational differences." No causal inference will be made.
* **Collinearity**: Degree, betweenness, and eigenvector centrality are mathematically correlated. The plan will **not** run a multivariate regression claiming independent effects. Instead, it will report pairwise correlations and descriptive statistics, framing findings as "jointly altered network topology."

### Power & Sample Size
* **Assumption**: Spec requires ≥100 participants per group.
* **Reality**: Power analysis is contingent on the actual number of participants available from the verified ABIDE source.
* **Limitation**: Acknowledged that power depends on effect size, which is [deferred] until real data is acquired.

### Sensitivity Analysis (FR-009)
* **Method**: Sweep correlation threshold at varying percentages of edge weights.
* **Metrics**: Count of significant nodes at each threshold; Jaccard similarity of significant node sets across thresholds.
* **Rationale**: Ensures findings are not artifacts of a single arbitrary threshold.
* **Constraint**: This analysis is **BLOCKED** until real connectivity matrices are derived from real fMRI data. **Synthetic data cannot be used to validate threshold sensitivity for biological findings.**

### Collinearity Diagnostics (FR-010)
* **Method**: Report pairwise correlations between degree, betweenness, and eigenvector centrality.
* **Rationale**: Centrality metrics are mathematically related; claiming independent effects is invalid.
* **Constraint**: This analysis is **BLOCKED** until real centrality metrics are computed from real fMRI data. **Synthetic data cannot be used to validate collinearity structure for real-world application.**

## 3. Compute Feasibility

* **Hardware**: GitHub Actions Free Tier (multi-core CPU, ample RAM).
* **Bottlenecks**: fMRIPrep is memory intensive.
* **Mitigation**:
 * **Real Data Only**: The pipeline will only attempt to run fMRIPrep on real data if a valid source is provided.
 * **Batch Processing**: If memory constraints are encountered, the pipeline will process subjects in batches.
 * **Subset Strategy**: If full sample processing is infeasible, a representative subset will be processed, with power limitations explicitly noted.
 * **No Synthetic Data**: Synthetic data is not a solution to compute constraints for this research question.
* **Conclusion**: The pipeline is feasible on CPU-only runners **only if** a valid real data source is provided and memory constraints are managed via batching or subset selection. Without real data, the pipeline cannot run.

## 4. Risks & Mitigations

| Risk | Impact | Mitigation |
|:--- |:--- |:--- |
| **Missing Real fMRI Data** | Pipeline cannot run on real data. | **Pipeline Halt**. No scientific results will be generated. Action required: Update verified datasets block. |
| **fMRIPrep Memory Overflow** | Crash on 7GB RAM. | Process subjects in batches; reduce sample size if necessary; acknowledge power limitations. |
| **Collinearity Misinterpretation** | Invalid scientific claims. | Enforce descriptive reporting; no multivariate regression on centrality metrics. |
| **FDR Correction Over-correction** | No significant findings. | Report uncorrected p-values and effect sizes alongside FDR; discuss power. |
| **Unverified Data Source** | Invalid results. | Strictly use only sources listed in the `# Verified datasets` block. |
| **Synthetic Data Temptation** | Invalid scientific results. | **Strict Prohibition**: No synthetic data for scientific results. Unit tests only. |