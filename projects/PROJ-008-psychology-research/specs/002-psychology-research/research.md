# Research: Mindfulness Components and Delivery Formats in ASD Social Skills

## Summary

This research plan defines the strategy for data acquisition, variable verification, and statistical analysis to answer the primary research question: *Which mindfulness components and delivery formats are most effective for improving social skills in children (6-12) with ASD?* The plan prioritizes dataset-variable fit verification before any statistical modeling to prevent fatal flaws.

## Dataset Strategy

The analysis relies on aggregated data from clinical trials and open science repositories. Per Constitution Principle II and the "Verified datasets" constraint, we only utilize sources explicitly verified for reachability and format.

| Dataset Source | Purpose | Verification Status | Access Method |
| :--- | :--- | :--- | :--- |
| ClinicalTrials.gov | Primary source for RCT metadata, inclusion criteria, and study identification (2015-2024). | Verified (API endpoint `/study/v2`). | `requests` library with rate limiting (10 req/s). |
| Open Science Framework (OSF) | Supplemental source for pre-registered protocols. | Verified (API v2). | `requests` library. |
| PubMed Central (PMC) | Primary source for full-text PDFs to extract numeric data (means/SDs). | Verified (PMC Open Access API). | `requests` (XML/Full-text). |
| DOAJ | Secondary source for open-access journal articles. | Verified (DOAJ API). | `requests`. |
| Semantic Scholar / OpenAlex | Metadata search only. **NOT** used for PDF retrieval. | Verified (Metadata API). | `requests` (Metadata only). |

**Dataset-Variable Fit Verification**:
Before calculating effect sizes, the `extractor.py` module will perform a strict schema check:
1.  **Required Variables**: `age_min`, `age_max`, `diagnosis` (ASD), `outcome_measure` (social skill), `pre_mean`, `pre_sd`, `post_mean`, `post_sd`, `n`, `study_design`.
2.  **Mismatch Handling**: If a study lacks a required variable (e.g., only reports p-values without means/SDs), the system will:
    *   Attempt reconstruction via full-text PDF extraction from PMC/DOAJ (FR-009).
    *   If reconstruction fails, log the exclusion reason (e.g., "Missing SD, reconstruction failed") to `excluded_studies.log` and remove the row from the analysis dataset.
    *   **Crucial**: Do not proceed with analysis on studies with missing required variables.

**Inclusion Filter: RCT Verification**:
To ensure causal validity, the inclusion criteria (FR-002) will strictly filter for **Randomized Controlled Trials (RCTs)** only. Studies with non-randomized, quasi-experimental, or observational designs will be excluded from the primary meta-analysis. If observational data is included in a secondary descriptive synthesis, claims will be explicitly framed as "associational."

## Coding Validation Protocol

To address measurement error risks in `delivery_format` and `intervention_component` tagging:
1.  **Manual Double-Coding**: The initial subset of studies extracted will be manually coded by two independent reviewers.
2.  **Reliability Check**: Inter-rater reliability (Cohen's Kappa) will be calculated.
3.  **Threshold**: If Kappa < 0.6, regex rules in `extractor.py` will be refined and re-tested before processing the full dataset.
4.  **Confidence Tag**: Each study will receive a `coding_confidence` tag (high/low) based on this validation.

## Statistical Methodology

### Effect Size Calculation (FR-004, FR-013)
*   **Metric**: Hedges' *g* (standardized mean difference) to handle varying scales.
*   **Formula**: $g = J \times \frac{\bar{X}_1 - \bar{X}_2}{S_{pooled}}$, where $J$ is the small-sample correction factor.
*   **Implementation**: `statsmodels.stats.meta_analysis` or custom implementation validated against `metafor` (R) reference logic.
*   **Precision**: Verified against synthetic data (SC-002).

### Meta-Analysis Model (FR-005)
*   **Model**: **Random-Effects Model** (DerSimonian-Laird or REML) is the **pre-specified default** due to expected heterogeneity in interventions and populations. The choice is not dependent on an I² threshold to avoid data-dredging bias.
*   **Heterogeneity**: Quantified via $Q$ (total), $I^2$, and $\tau^2$.
*   **Subgroup Analysis**:
    *   **Components**: Breath, Body Scan, Loving-Kindness, Combined.
    *   **Formats**: Caregiver-mediated, Child-led.
    *   **Domains**: Peer interaction, Emotional recognition, Reciprocal communication.
    *   **Test**: **Q-between (Qb)** statistic is used to compare effect sizes between independent subgroups (not Cochran's Q).
    *   **Condition**: Formal subgroup testing (Qb) and meta-regression are **only performed if N >= 20**.
    *   **Fallback**: If N < 20, the analysis will be purely descriptive/narrative. No formal hypothesis testing (including Q-tests) will be performed to avoid underpowered results.

### Publication Bias (FR-006, SC-004)
*   **Visual**: Funnel plot (asymmetry assessment).
*   **Statistical**: Egger's test.
*   **Condition**: Only performed if N >= 10. If N < 10, suppressed with a warning in the report.

### Bayesian Fallback Strategy (N < 20)
If N < 20, the project will utilize a Bayesian meta-analysis approach (using `bayesmeta` or equivalent Python implementation) with weakly informative priors to estimate the pooled effect size and uncertainty, providing a more robust inference than frequentist methods in small samples. If Bayesian analysis is not feasible due to tooling constraints, a purely narrative synthesis will be provided.

## Statistical Rigor & Assumptions

*   **Multiple Comparisons**: Not applicable. If N < 20, no formal tests are run. If N >= 20, a family-wise error correction (e.g., Bonferroni) will be applied to subgroup p-values.
*   **Power Limitation**: Acknowledged that N < 20 is a high probability. The plan explicitly triggers the "descriptive fallback" (FR-014) or Bayesian approach rather than forcing invalid frequentist subgrouping.
*   **Causal Claims**: Claims are restricted to **efficacy** for RCTs. Any observational data included in secondary synthesis is framed as **associational**.
*   **Collinearity**: If "breath awareness" and "body scan" are often combined, they will be tagged as "Combined" to avoid claiming independent effects for definitionally overlapping predictors.
*   **Measurement Validity**: Instruments (e.g., SRS-2) will be cited with validation evidence in `research.md` if used.

## Computational Feasibility

*   **Environment**: CPU-only (2 cores, 7 GB RAM).
*   **Methods**: All statistical methods (Hedges' g, REML, Qb, Bayesian inference) are computationally lightweight and CPU-tractable.
*   **Data Volume**: Expected dataset size < 100 rows. No GPU required.
*   **Runtime**: Estimated < 1 hour for full pipeline.

## Decision Rationale

*   **Why Random-Effects?**: Anticipated heterogeneity in intervention protocols and populations across different studies necessitates a random-effects model over fixed-effects, pre-specified to avoid data-dredging.
*   **Why N < 20 Fallback?**: Subgroup analysis and meta-regression with N < 20 are statistically underpowered and prone to false positives. The plan prioritizes validity (descriptive synthesis or Bayesian inference) over forcing a model that would yield unreliable confidence intervals.
*   **Why No LLM for Extraction?**: LLM inference is too heavy for the 6h/7GB constraint and introduces non-determinism. Regex and structured API parsing are used for reproducibility (Constitution Principle I), validated by manual double-coding.