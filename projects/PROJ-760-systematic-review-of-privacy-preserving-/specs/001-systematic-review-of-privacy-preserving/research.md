# Research: Systematic Review of Privacy-Preserving Federated Learning Protocols

## Problem Statement

Federated learning (FL) enables collaborative model training without sharing raw data, but privacy-preserving mechanisms (Differential Privacy, Secure Aggregation, Homomorphic Encryption) introduce performance overheads. This review systematically quantifies the trade-offs between privacy and performance (communication, convergence, accuracy, computation) across recent literature.

## Dataset Strategy

| Dataset Name | Verified URL | Loader/Access Method | Notes |
|--------------|--------------|----------------------|-------|
| arXiv | https://arxiv.org | `arxiv` Python library | Query API for metadata and PDF URLs |
| Semantic Scholar | https://www.semanticscholar.org | `semanticscholar` Python library | Query API for metadata and PDF URLs |
| UCI Machine Learning Repository (not used) | N/A | N/A | Not applicable; no UCI dataset contains FL performance metrics |

**Note**: The spec assumes arXiv and Semantic Scholar provide sufficient access to PDFs and metadata. If a PDF is behind a paywall or broken, the system logs the DOI and skips (Edge Case 1). No other datasets are used; all data is extracted from the literature.

## Methodology

### 1. Literature Retrieval
- **Search Strings**: 
  - "federated learning" AND "differential privacy"
  - "federated learning" AND "secure aggregation"
  - "federated learning" AND "homomorphic encryption"
  - "federated learning" AND "privacy"
- **Filters**: Publication date -2024, English language.
- **APIs**: arXiv (via `arxiv` library), Semantic Scholar (via `semanticscholar` library).
- **Rate Limiting**: Retry up to 3 times on timeout/rate limit; log failures.

### 2. PDF Extraction
- **Tools**: `pdfplumber` for table extraction; `tabula-py` as fallback.
- **Metrics**: Communication overhead (KB/MB), convergence rounds, accuracy drop (%), computational cost (seconds/FLOPs).
- **Normalization**: 
  - Communication → bytes
  - Convergence → rounds (integer)
  - Computational cost → relative overhead ratio (Private Baseline / Non-Private Baseline) if baseline available; else exclude from meta-analysis (FR-008).
- **Categorization**: 
  - **Single Mechanism**: Assign to DP, SecureAgg, or FHE if only one is used.
  - **Hybrid Mechanism**: If multiple mechanisms are used (e.g., DP + SecureAgg), assign to "Hybrid" and **exclude** from single-mechanism groups to prevent confounding.

### 3. Meta-Analysis (Methodological Override)
- **Control Group Definition**: For each study, the "control" mean and variance are extracted from the **non-private baseline** reported in the *same* paper. If a study reports only absolute overhead without a baseline, it is excluded from effect-size calculations.
- **Effect Size**: Hedges' g is computed **only** for studies where both treatment and control means and variances are available. Studies lacking variance are excluded from the effect-size calculation but may contribute to raw metric summaries.
- **Primary Statistical Test**: **Random-Effects Meta-Regression** on the **raw normalized metrics** (e.g., log-communication-overhead) with mechanism type as the predictor. This accounts for between-study heterogeneity and hierarchical data structure.
- **Multiple Comparisons**: Benjamini-Hochberg correction applied to the p-values of the mechanism coefficients in the regression.
- **Missing Variance Handling**: 
  - **Imputation Sensitivity**: If <50% of studies in a group lack variance, impute missing variance using the median SD from similar studies in the same mechanism group for sensitivity analysis.
  - **Descriptive Review**: If >50% of studies in a group lack variance, **skip** the effect size calculation and meta-regression. Instead, perform a **Descriptive Review** (median, IQR) and flag as "Descriptive Review". **Fixed-effects models are not used** as they assume homogeneity likely violated in this context.
- **Visualization**: Forest plots (for valid effect sizes), bar charts (for mean/median overhead), and scatter plots.

## Statistical Rigor

- **Multiple Comparisons**: Benjamini-Hochberg applied to regression coefficients (Methodological Override of FR-006).
- **Sample Size**: If N < 5 per category, output "Descriptive Review" (SC-001); no power justification needed.
- **Causal Inference**: Observational; claims framed as associational.
- **Measurement Validity**: Metrics extracted from published studies; validation via ground-truth subset of papers (SC-002).
- **Collinearity**: Not applicable; mechanisms are mutually exclusive due to Hybrid exclusion rule.
- **Variance Handling**: No fixed-effects fallback; strict descriptive review for high-missing-variance scenarios to avoid misleading CIs.

## Assumptions and Limitations

- **API Access**: arXiv and Semantic Scholar provide sufficient PDF access; paywalled PDFs are skipped.
- **Extraction Accuracy**: `pdfplumber` extracts ≥80% of tables; remaining flagged for manual review.
- **Metric Comparability**: Computational cost reported in comparable units; non-comparable studies excluded (FR-008).
- **Sample Size**: Search strings yield N ≥ 5 per category; if not, descriptive review is valid (SC-001).
- **Control Group**: Assumes papers report a non-private baseline for comparison. If not, the study is excluded from effect-size calculations.

## Decision Rationale

- **CPU-Only**: All methods (PDF parsing, meta-regression) are CPU-tractable; no GPU required.
- **Lightweight Libraries**: `pdfplumber`, `pandas`, `statsmodels` are lightweight and fit within 7 GB RAM.
- **Reproducibility**: Pinned dependencies, random seeds, and canonical API sources ensure reproducibility.
- **Methodological Override**: The plan deviates from FR-004 and FR-006 in the spec to ensure scientific validity (avoiding fixed-effects with missing variance and ANOVA on effect sizes). This is documented as a necessary correction.
- **Data Integrity**: All results are derived from real extracted data; no simulated or hardcoded values are used.
