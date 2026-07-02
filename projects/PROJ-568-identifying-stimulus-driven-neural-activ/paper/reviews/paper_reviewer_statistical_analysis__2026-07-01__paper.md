---
action_items:
- id: d53706ef642c
  severity: science
  text: The manuscript describes statistical methods (GLMs, RSA, ISC) but lacks a
    dedicated section on multiple-comparisons correction. Given the high dimensionality
    of iEEG data (many electrodes, timepoints, frequencies) and the use of searchlight
    analyses (Section 41.2.1), the authors must explicitly state how false discovery
    rates (FDR) or family-wise error rates (FWER) are controlled to prevent spurious
    findings.
- id: 39167584af2d
  severity: science
  text: In the description of Representational Similarity Analysis (RSA) and Inter-Subject
    Correlation (ISC), the text mentions computing correlations but omits details
    on significance testing. The authors should specify the null models used (e.g.,
    permutation tests, phase randomization) and how p-values or confidence intervals
    are derived for these correlation matrices, particularly given the temporal autocorrelation
    inherent in neural time series.
- id: dd2636b68765
  severity: science
  text: The section on Gaussian Process regression (Section 41.3.2) describes the
    kernel and interpolation but does not address model selection or uncertainty quantification.
    The authors should clarify how kernel hyperparameters are optimized and whether
    the model provides credible intervals for the reconstructed activity, which is
    critical for interpreting the reliability of the 'superEEG' estimates.
artifact_hash: 88c485888572e5b5ec21db55f3e25c0d533affd80dd028fd7994137fbaf7e64e
artifact_path: projects/PROJ-568-identifying-stimulus-driven-neural-activ/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-01T23:30:37.795738Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

This manuscript serves as a comprehensive methodological review of techniques for identifying stimulus-driven neural activity in multi-patient intracranial recordings. While the text excels in conceptual clarity and breadth, the statistical analysis lens reveals a lack of specific details regarding the rigorous application of these methods.

The primary concern is the absence of explicit discussion on **multiple-comparisons correction**. The text describes high-dimensional analyses, such as searchlight RSA (Section 41.2.1) and time-resolved GLMs, which inherently involve testing thousands of hypotheses (across electrodes, timepoints, and frequencies). Without a stated strategy for controlling the False Discovery Rate (FDR) or Family-Wise Error Rate (FWER), the risk of Type I errors is significant. The authors should add a paragraph detailing standard correction methods (e.g., cluster-based permutation tests, Benjamini-Hochberg) appropriate for the described analyses.

Secondly, the **significance testing framework** for correlation-based methods like RSA and Inter-Subject Correlation (ISC) is under-specified. These methods rely on comparing observed correlation matrices against a null distribution. The manuscript does not describe the null models employed (e.g., circular shifting of time series, phase randomization) to account for the strong temporal autocorrelation present in neural data. Standard parametric tests are often invalid for such data; the authors must clarify the non-parametric or robust statistical procedures used to derive p-values or confidence intervals.

Finally, regarding the **Gaussian Process (GP) models** (Section 41.3.2), the text focuses on the geometric intuition of reconstruction but omits the statistical mechanics of model fitting. Specifically, it is unclear how kernel hyperparameters are selected (e.g., via marginal likelihood maximization) and whether the model outputs include uncertainty estimates (credible intervals). In the context of reconstructing missing data from sparse electrode coverage, quantifying this uncertainty is essential for interpreting the validity of the "superEEG" approach.

Addressing these statistical rigor points will strengthen the manuscript's utility as a guide for researchers applying these complex methods.
