---
action_items:
- id: 642baa4944fb
  severity: science
  text: Report confidence intervals or standard errors for all aggregate metrics (e.g.,
    mean PR, HR, T3 accuracy) in Table 1 and Section 5.1. Point estimates alone do
    not convey the stability of the 'Prejudice Gap' claim across the 27 models.
- id: 11d0ea143437
  severity: science
  text: Clarify the statistical test used to validate the 'Closed vs. Open' gap (Section
    5.1). A simple difference of means (14.5% vs 47.0%) is insufficient; provide a
    p-value or effect size (e.g., Cohen's d) from a t-test or non-parametric equivalent
    to support the claim of a 'significant' gap.
- id: ba736bf7230d
  severity: science
  text: "In Section 5.2 and Appendix A.10, the correlation between positional bias\
    \ and T3 accuracy is reported as r \u2248 -0.68. Specify if this is Pearson or\
    \ Spearman correlation and provide the associated p-value to confirm statistical\
    \ significance."
- id: 258e59b4e14b
  severity: science
  text: "The AI-as-Judge robustness analysis (Appendix A.9) reports Spearman correlations\
    \ (\u03C1=0.94, 0.92) but lacks confidence intervals for these correlation coefficients.\
    \ Given the small sample size (n=200 for the subset), CIs are necessary to assess\
    \ the precision of the rank stability claim."
artifact_hash: 46c2ca87e5752401742be8e75f855167112497e54e4e0af681d19e8bf31d8374
artifact_path: projects/PROJ-620-perception-or-prejudice-can-mllms-go-bey/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T19:36:38.140578Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The statistical analysis in the manuscript is generally sound in its design of metrics (PR, HR, RGM) but lacks necessary inferential statistics to support the strength of its central claims.

**1. Lack of Uncertainty Quantification:**
The paper relies heavily on point estimates for aggregate metrics. For instance, Section 5.1 states the mean Prejudice Rate is 51.3% and the mean HR is 10.4%. Without confidence intervals (CIs) or standard errors, it is impossible to determine if the observed "Prejudice Gap" is statistically robust or if it could be an artifact of the specific 27 models sampled. Similarly, the "Closed vs. Open" gap (14.5% vs 47.0%) is presented as a definitive finding. A formal hypothesis test (e.g., independent samples t-test or Mann-Whitney U test) with a reported p-value is required to validate that this difference is not due to random variation.

**2. Correlation Reporting:**
In Appendix A.10 (Positional Bias), the authors report a correlation of $r \approx -0.68$ between positional bias and T3 accuracy. The manuscript does not specify whether this is Pearson or Spearman correlation, nor does it provide a p-value. Given the non-linear nature of model performance and the potential for outliers, a non-parametric test (Spearman) is likely more appropriate, but the significance level must be explicitly stated to support the claim that "every model with $\sigma > 10$ ranks in the bottom third."

**3. AI-as-Judge Robustness:**
The cross-judge robustness analysis in Appendix A.9 uses a subset of 200 videos to calculate Spearman rank correlations ($\rho = 0.94$ and $0.92$). While the high correlation is promising, the sample size is relatively small for establishing generalizability. The authors should report the 95% confidence intervals for these correlation coefficients. Without CIs, the precision of the estimate is unclear, and the claim that the ranking is "not an artifact" is statistically weaker than it could be.

**4. Multiple Comparisons:**
The paper evaluates 27 models across multiple tasks and metrics (T1, T2, T3, HR, PR, CR, IR, RGM). While the primary focus is on the "Prejudice Gap," the extensive reporting of per-category accuracies (Appendix A.7) and per-trait difficulties (Appendix A.6) invites multiple comparison issues. The authors should acknowledge this and, if any specific pairwise comparisons between models or categories are highlighted as "significant," they should ideally be corrected (e.g., Bonferroni or Benjamini-Hochberg) or at least discussed in the context of Type I error inflation.

**Recommendation:**
The authors should re-run their analysis to include confidence intervals for all mean metrics and p-values for all comparative claims (Closed vs. Open, Correlation tests). This will significantly strengthen the statistical validity of the "Prejudice Gap" conclusion.
