---
action_items:
- id: 75800142aec6
  severity: science
  text: Clarify sample sizes for t-tests in Table 1; reported degrees of freedom (e.g.,
    df=11.27 for Twain) are inconsistent with pooling all 7 other authors' seeds (n=70)
    and suggest averaging per seed (n=10), but the text implies pooling.
- id: b4fd6f78c17e
  severity: writing
  text: Address multiple comparisons correction for the 8 author tests and ablation
    comparisons. While p-values are small, methodological rigor requires acknowledging
    family-wise error rate control.
- id: 38b97b1ac3c4
  severity: writing
  text: Report effect sizes (e.g., Cohen's d) alongside p-values for key t-tests to
    quantify the magnitude of stylometric separation beyond statistical significance.
artifact_hash: 148021f63314c6cbe2b6159eaaaecc4e6c793ec5541ddbe74681664a10cdde19
artifact_path: projects/PROJ-562-a-stylometric-application-of-large-langu/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-11T16:35:49.405958Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The statistical methodology demonstrates robustness through the use of 10 random seeds, bootstrap confidence intervals (Figure 1), and Welch’s t-tests (non-integer degrees of freedom in Table 1). However, several statistical reporting details require clarification to ensure full reproducibility and rigor.

First, the sample composition for the t-tests in Table 1 is ambiguous. The text states losses are compared against "held-out texts from all other authors." If this implies pooling 7 authors × 10 seeds ($n=70$) against the target author ($n=10$), the resulting degrees of freedom should generally be higher than the reported values (e.g., Twain $df=11.27$). These lower df values suggest the "other" group was averaged per seed ($n=10$), but the text does not specify this aggregation. Clarifying the $N$ for each group is essential for interpreting the test statistics.

Second, multiple comparisons are not addressed. The study performs 8 primary t-tests (one per author) and multiple ablation comparisons (Section 3.3). While the reported p-values are extremely small (e.g., $10^{-12}$ to $10^{-43}$), standard practice requires acknowledging corrections (e.g., Bonferroni or FDR) to control the family-wise error rate, particularly for the ablation results where some p-values are marginal (e.g., $p=0.0529$ for Melville function words).

Finally, statistical significance is reported without effect sizes. Given the goal is to measure "stylometric distance," reporting Cohen’s $d$ or similar metrics would better contextualize the practical magnitude of the loss differences beyond mere significance. These adjustments will strengthen the statistical validity of the claims.
