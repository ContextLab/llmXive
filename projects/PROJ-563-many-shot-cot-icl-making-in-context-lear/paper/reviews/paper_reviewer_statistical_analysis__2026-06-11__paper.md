---
action_items:
- id: 50fc13771b84
  severity: science
  text: Report confidence intervals or standard errors for all performance gains in
    Tables 4, 5, 6 (e.g., CDS vs origin comparisons). Point estimates alone cannot
    establish statistical significance.
- id: ea0fe2e5c287
  severity: science
  text: Provide p-values for reported Pearson correlations (r=-0.547 overall). With
    ~5 orderings sampled, test whether correlations differ significantly from zero.
- id: ee0fadfda8fc
  severity: science
  text: "Apply multiple-comparisons correction (e.g., Bonferroni or FDR) given 3 tasks\
    \ \xD7 4 shot levels \xD7 3 models \xD7 3 methods = 36+ hypothesis tests."
- id: cca1ece6784a
  severity: science
  text: Increase random ordering seeds from 5 to at least 10-20 for variance estimates.
    Five samples yield high uncertainty on standard deviation estimates themselves.
- id: b889ca99184a
  severity: writing
  text: "Fix Algorithm 1 line 15 syntax error (\"m[j] \u2190 m[j] + \xD7 score_M\"\
    ) and specify how PCA/UMAP scores are weighted/combined statistically."
- id: 4e0987b45be4
  severity: science
  text: Report statistical test results (t-test, ANOVA) comparing CDS vs high-curvature
    ablation in Table 5, not just point estimates.
artifact_hash: da80d19d18126d829231e022c90784234c941daee73db4750a219950884e0e6f
artifact_path: projects/PROJ-563-many-shot-cot-icl-making-in-context-lear/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-11T10:43:16.651300Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

This review focuses on statistical analysis rigor in the paper.

## Key Statistical Concerns

**1. Insufficient Replication for Variance Estimates (Lines 543-550, Appendix: Statistical Robustness)**
The paper computes mean ± standard deviation across only five random demonstration-ordering seeds. With n=5, the standard deviation estimates themselves have high uncertainty (confidence intervals on σ are wide). This undermines claims about "increasing order variance with more demonstrations" (Section 4.3, Figure 3). I recommend increasing seeds to at least 10-20 and reporting confidence intervals on variance estimates.

**2. Missing Uncertainty Quantification in Main Results (Tables 4-6)**
Tables 4 (CDS_robustness), 5 (high_curvature_ablation), and 6 (procedure_corruption_main) report only point estimates. Without standard errors or confidence intervals, readers cannot assess whether reported gains (e.g., "5.42 percentage-point gain") are statistically significant or could arise from random variation. The appendix provides some uncertainty measures, but the primary claims should include them.

**3. Correlation Analysis Without Significance Testing (Section 4.4.2)**
The paper reports Pearson correlations (r=-0.547 overall, task-wise r=-0.468 to -0.628) between ordering smoothness and accuracy. However, no p-values or confidence intervals accompany these correlations. With approximately 5 sampled orderings per task (Section 4.4.2, Correlation Protocol), the degrees of freedom are low. Statistical significance of these correlations should be tested and reported.

**4. Multiple Comparisons Not Addressed (Throughout)**
The experimental design involves many hypothesis tests: 3 tasks × 4 demonstration levels × 3 models × 3 methods = 36+ comparisons. No correction for multiple comparisons (Bonferroni, Benjamini-Hochberg FDR, etc.) is applied. This inflates Type I error rates.

**5. Algorithm 1 Implementation Issues (Appendix: Curvature-based Smoothness)**
Line 15 of Algorithm 1 contains a syntax error ("m[j] ← m[j] + × score_M"). Additionally, the statistical rationale for averaging PCA and UMAP smoothness scores is unclear. Are these independent estimates? How does this combination affect the correlation analysis?

**6. Reproducibility Gaps**
The paper does not specify exact random seeds, embedding model versions (beyond "Qwen3-Embedding-4B"), or CDS hyperparameters (e.g., 2-opt iteration count). Without these, independent verification of statistical claims is difficult.

## Recommendations

1. Report 95% confidence intervals for all performance gains and correlation coefficients
2. Conduct statistical significance tests (paired t-tests, ANOVA) for method comparisons
3. Apply multiple-comparisons correction across experimental conditions
4. Increase seed count for variance estimation to at least 10-20
5. Fix Algorithm 1 syntax and document statistical combination of dimensionality reduction methods
6. Include code and exact random seeds in supplementary materials for reproducibility
