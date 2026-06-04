---
action_items:
- id: 28a68b6585cd
  severity: writing
  text: Section 2.1.2 (RSA) omits discussion of multiple-comparisons correction for
    searchlight analyses. Without FWE or FDR control, reported spatial patterns may
    reflect false positives.
- id: 5b59ba34b623
  severity: writing
  text: Section 2.1.1 (GLMs) describes the model form but lacks details on link function
    selection, error distribution assumptions, or residual diagnostics required for
    valid inference.
- id: c202c8d04032
  severity: writing
  text: Section 2.2.2 (Gaussian processes) mentions spatial blurring but does not
    address kernel selection, hyperparameter optimization, or cross-validation procedures
    essential for reproducibility.
- id: 47b1bd8f2681
  severity: writing
  text: Section 2.2.3 (ISC/ISFC) describes correlation computation but does not specify
    null models or permutation testing procedures to establish statistical significance
    against noise.
artifact_hash: 88c485888572e5b5ec21db55f3e25c0d533affd80dd028fd7994137fbaf7e64e
artifact_path: projects/PROJ-568-identifying-stimulus-driven-neural-activ/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-04T13:26:05.308106Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

This manuscript is a methodological survey chapter rather than an empirical study, which limits the direct application of statistical tests. However, the statistical rigor of the *described* methods must be accurately conveyed to ensure readers understand the limitations and requirements of each approach.

In **Section 2.1.2 (Representational similarity analysis)**, the text describes conducting RSA across "searchlights" but fails to mention the necessity of correcting for multiple comparisons across the thousands of searchlight spheres. In neuroimaging, failing to apply family-wise error (FWE) or false discovery rate (FDR) correction to searchlight results renders spatial inferences statistically invalid. This omission risks misleading readers about the robustness of RSA findings.

In **Section 2.1.1 (Generalized linear models)**, the GLM formulation is presented generally ($y_t = f(x_t, \beta)$) without specifying link functions, error distributions, or assumptions regarding independence of observations. For iEEG data, temporal autocorrelation is a major violation of standard GLM assumptions. The text should clarify how time-series dependencies are handled (e.g., ARIMA errors, robust standard errors) to prevent misuse of the models.

In **Section 2.2.2 (Gaussian process models)**, the text mentions using radial basis function kernels for spatial interpolation but does not discuss kernel selection or hyperparameter tuning. The choice of kernel and length-scale parameters significantly impacts the estimated correlation structure and downstream inferences. Reproducibility requires specifying how these parameters were optimized (e.g., via marginal likelihood maximization).

In **Section 2.2.3 (ISC/ISFC)**, the procedure for computing inter-subject correlations is outlined, but the text does not specify the null hypothesis or the permutation testing framework used to assess significance. ISC values can be inflated by shared noise or stimulus artifacts; without a clear statistical test (e.g., phase randomization), the reported correlations lack inferential value.

These additions are necessary to ensure the survey accurately reflects the statistical standards required for rigorous application of these methods in intracranial research.
