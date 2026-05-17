---
artifact_hash: 88c485888572e5b5ec21db55f3e25c0d533affd80dd028fd7994137fbaf7e64e
artifact_path: projects/PROJ-568-identifying-stimulus-driven-neural-activ/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.0.0
reviewed_at: '2026-05-17T14:49:54.324337Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

This manuscript is a methodological survey chapter rather than an empirical study, which fundamentally limits the applicability of a statistical analysis review lens. No original statistical analyses with primary data are presented; all figures (e.g., Figures 1–9) appear to be conceptual or illustrative rather than empirical results.

**Statistical methods coverage (Section 2, lines 400–1200):** The paper describes multiple statistical approaches (GLMs, MVPA, RSA, Gaussian processes, hierarchical matrix factorization, ISC/ISFC) but does so at a conceptual level. For each method, there is no discussion of:
- Model assumptions (e.g., independence, stationarity, normality)
- Validation procedures (e.g., cross-validation folds, holdout sets)
- Multiple-comparisons corrections (critical for RSA searchlight analyses, ISC/ISFC across many electrode pairs)
- Confidence intervals or effect sizes for any reported associations

**Missing statistical rigor (Section 2.1–2.2, lines 450–850):** For within-participant approaches like GLMs and MVPA, the paper should specify:
- How regularization is applied to prevent overfitting given the typically small number of trials in iEEG
- Whether temporal autocorrelation in neural timeseries is accounted for
- What statistical significance thresholds are used for decoding accuracy

**Across-participant modeling (Section 2.2, lines 850–1200):** Hierarchical models (HTFA, Gaussian processes, hyperalignment) require careful specification of:
- Prior distributions and hyperparameter selection procedures
- How electrode location uncertainty is propagated through the models
- Whether inter-subject correlations account for within-subject temporal dependence

**Recommendations for minor revision:**
1. Add a subsection explicitly addressing statistical assumptions and validation requirements for each method class (lines 400–1200)
2. Include discussion of multiple-comparisons correction strategies for searchlight RSA and ISC/ISFC analyses (currently absent)
3. Specify reproducibility considerations: code availability, random seed control, and data preprocessing pipelines
4. If empirical examples are included in the final chapter, ensure all statistical tests report confidence intervals and effect sizes, not just point estimates

Without these additions, readers cannot assess the reliability or reproducibility of the described methods when applied to their own data.
