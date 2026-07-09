# Research: Pipeline Validation - Investigating the Impact of Network Topology on Neural Entrainment (Simulated Data)

## Executive Summary

This research phase validates the feasibility of correlating HCP resting‑state fMRI network topology with external entrainment metrics. **Key Finding**: No verified public dataset contains both HCP fMRI connectivity matrices **and** rhythmic entrainment strength (Phase‑Locking Values) for the same subjects. Consequently, the study is defined as a **pipeline validation** using **synthetic entrainment data** generated to match the structure of the HCP dataset. The analysis therefore validates the computational workflow, not the biological hypothesis.

## Dataset Strategy

### Primary Data Sources

| Data Type | Source Name | Verified URL | Access Method | Notes |
| :--- | :--- | :--- | :--- | :--- |
| **HCP fMRI (Parquet)** | HCP‑flat | `https://huggingface.co/datasets/jonxuxu/HCP-flat/resolve/main/data/train-00000-of-00001-ecc38ed386fa0d8c.parquet` | `pandas.read_parquet` | **Verified**: Contains connectivity matrices for resting‑state fMRI. |
| **Entrainment Metric** | Synthetic Generation | N/A | `numpy.random` | **Fallback**: No verified dataset provides rhythmic entrainment (PLV) aligned with HCP subjects. Synthetic entrainment values are generated with a fixed seed and a modest correlation (`r≈0.3`) to the primary topology metric for validation purposes. |

### Dataset Fit Analysis & Risks

1. **HCP Connectivity Data**: Verified to contain subject‑wise connectivity matrices. If the expected columns are missing, the pipeline halts with `Error: HCP data lacks required connectivity matrices`.
2. **Entrainment Metrics**: The only candidate external datasets (e.g., `neurofusion/eeg‑restingstate`) are generic resting‑state collections **without** rhythmic stimulation or PLV columns. **Therefore** the pipeline **will not** attempt to ingest them for the primary analysis. Instead, synthetic entrainment data are generated (see Phase 0 in the implementation plan). All downstream results are tagged `data_source: "synthetic"` and the final report includes a clear disclaimer that the analysis validates the code pipeline, not the scientific hypothesis.
3. **Subject Alignment**: The HCP and any external EEG datasets have disjoint subject IDs. The pipeline performs an **inner join** on `subject_id`. If the resulting `N` is below 30, a `Power Warning: N < 30 (Exploratory)` flag is added, but execution **continues** using the synthetic data fallback to ensure the pipeline is validated.

## Statistical Methodology

* **Graph Metrics**: Weighted clustering coefficient and characteristic path length (see plan.md).  
* **Correlation**: Spearman rank correlation between each topology metric and synthetic entrainment strength.  
* **Unique Effects**: **Partial Correlation** is used to test the unique contribution of each metric (CC vs Entrainment controlling for CPL, and vice versa), addressing the mathematical coupling of these metrics.  
* **Multiple‑Comparison**: Bonferroni correction for the two tests (N = 2) on the partial correlations.  
* **Collinearity**: VIF computed as a diagnostic. If VIF > 5, it confirms coupling, but the analysis proceeds with Partial Correlation rather than suppressing significance.  
* **Robustness**: Re‑run analysis for AAL and Power264 atlases; generate a single bar chart showing absolute differences in effect size (|r|) versus Schaefer (see SC‑002).  

## Compute Feasibility

* **Runtime**: < 30 min on GitHub Actions (2 CPU, 7 GB RAM).  
* **Memory**: < 4 GB.  
* **GPU**: Not required.

## Decision Log

| Decision | Rationale |
| :--- | :--- |
| **Use Synthetic Entrainment** | No verified matched dataset exists; synthetic data enable end‑to‑end pipeline validation while preserving reproducibility. |
| **Spearman Correlation** | Robust to non‑normality typical of neuroimaging metrics. |
| **Partial Correlation** | Required to test unique effects of CC and CPL, which are mathematically coupled. Univariate tests are insufficient. |
| **Bonferroni (N = 2)** | Explicitly required by FR‑004. |
| **Inner Join** | Guarantees only subjects with both topology and entrainment data are analyzed; avoids imputation bias. |
| **Explicit Disclaimer** | Clarifies that findings are methodological, not biological, satisfying scientific soundness concerns. |
| **Bar Chart Labeling** | Y‑axis set to "Absolute Difference in Effect Size (|r|)" to meet SC‑002. |
| **Mandatory Synthetic Fallback** | Ensures the pipeline runs even when real data is missing, preventing the research question from being unanswerable due to data gaps. |