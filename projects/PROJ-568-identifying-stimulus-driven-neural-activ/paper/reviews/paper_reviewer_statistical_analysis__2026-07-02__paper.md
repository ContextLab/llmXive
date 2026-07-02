---
action_items:
- id: 912c785dc035
  severity: science
  text: The manuscript describes statistical methods (GLMs, RSA, ISC) but lacks a
    dedicated section on multiple-comparisons correction. Given the high dimensionality
    of intracranial data (thousands of electrodes/timepoints) and the use of searchlight
    analyses, the authors must explicitly state how false discovery rates (FDR) or
    family-wise error rates (FWER) are controlled to prevent spurious findings.
- id: b512f3ad3108
  severity: science
  text: In the description of Representational Similarity Analysis (RSA) and Inter-Subject
    Correlation (ISC), the text mentions computing correlations between matrices or
    time series but omits details on significance testing. The authors should specify
    the permutation strategies or null models used to generate p-values and confidence
    intervals for these correlation coefficients.
- id: 50d4fe2a1dd0
  severity: science
  text: The section on Gaussian Process regression (SuperEEG) describes the kernel
    and interpolation but does not address model validation. The authors should clarify
    how hyperparameters (e.g., length scales) are selected and whether cross-validation
    or out-of-sample testing was used to prevent overfitting when reconstructing full-brain
    activity from sparse electrodes.
artifact_hash: 88c485888572e5b5ec21db55f3e25c0d533affd80dd028fd7994137fbaf7e64e
artifact_path: projects/PROJ-568-identifying-stimulus-driven-neural-activ/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T01:25:38.517836Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

This manuscript serves as a methodological survey rather than an empirical study reporting new statistical results. Consequently, there are no specific p-values, confidence intervals, or effect sizes to audit directly. However, the statistical rigor of the *described* methodologies requires clarification to ensure readers can apply these techniques correctly without inflating Type I error rates.

The primary concern is the absence of a discussion on **multiple-comparisons correction**. The text details high-dimensional analyses, such as searchlight RSA (Section 41.3.1.3) and whole-brain ISC (Section 41.3.2.2), which inherently involve testing thousands of hypotheses simultaneously. Without explicit mention of False Discovery Rate (FDR) or Family-Wise Error Rate (FWER) control methods (e.g., Bonferroni, cluster-based permutation tests), the described workflows risk generating spurious "significant" findings. The authors should add a paragraph in the relevant sections or a general "Statistical Considerations" subsection outlining standard correction practices for these specific modalities.

Secondly, the **significance testing procedures** for correlation-based metrics are underspecified. For RSA (Section 41.3.1.3) and ISC/ISFC (Section 41.3.2.2), the text explains how correlation matrices are computed but does not describe how statistical significance is determined. In naturalistic stimulus paradigms, standard parametric assumptions (e.g., independence of timepoints) are often violated due to temporal autocorrelation. The authors should specify the recommended null models (e.g., phase-randomized surrogates, trial-shuffling) and permutation strategies required to generate valid p-values and confidence intervals for these statistics.

Finally, regarding the **Gaussian Process (GP) models** (Section 41.3.2.3), the text describes the interpolation of activity from sparse electrodes to a full-brain grid. It is critical to address **model validation and overfitting**. The authors should clarify how kernel hyperparameters (e.g., length scales, noise variance) are optimized (e.g., via marginal likelihood maximization) and whether cross-validation is employed to ensure the reconstructed "SuperEEG" signals generalize beyond the training data. Without this, the reliability of the reconstructed full-brain maps remains theoretically unverified.

Addressing these points will ensure the survey provides a statistically sound roadmap for researchers applying these complex methods to intracranial data.
