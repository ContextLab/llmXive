---
action_items:
- id: 3b4ebab61696
  severity: science
  text: Add statistical significance tests (e.g., paired t-tests) for model comparisons
    in Table 1 to validate bolded scores.
- id: 55322ded1953
  severity: science
  text: Report 95% confidence intervals instead of standard deviations of the mean,
    given only 3 runs per task.
- id: e7d8a496f229
  severity: science
  text: Apply multiple comparisons correction (e.g., Bonferroni) for the 9 models
    x 18 task types analysis.
artifact_hash: 446593595ed3db0a3ea306b2f1debae06a4efb5d82e58c3ca6afc0ab4d9515cf
artifact_path: projects/PROJ-618-bench-evaluating-proactive-personal-assi/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-11T08:38:00.269063Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The statistical analysis in Section 4 lacks rigor for the comparative claims made. In Section 4.1 (`1-main/4-experiments.tex`), the paper states experiments are run "three times." With n=3, standard deviations in Table 1 (`0.1-table/overall`) are unstable estimates of population variance. The authors should report 95% confidence intervals for means rather than just standard deviations. Currently, Table 1 bolds the highest mean scores (e.g., GPT-5.4 Proc 67.0) without significance testing. A paired t-test or Wilcoxon signed-rank test across the 3 seeds is required to validate that differences between models are statistically significant and not due to random seed variation.

Furthermore, the analysis involves extensive multiple comparisons: 9 models evaluated across 2 metrics (Proc/Comp), 5 user domains, and 18 task types. No correction (e.g., Bonferroni or Benjamini-Hochberg) is applied, which inflates Type I error rates for the claims regarding "Model trends" and "Domain trends." The ablation study in Section 4.3 claims a "9.5 points" decrease in Proactivity upon removing history but provides no p-value or confidence interval to support this magnitude of change. Similarly, Figure 5 (`0.0-figure/turn_proactivity.pdf`) depicts a "negative association" between turn count and Proactivity but omits the correlation coefficient (r) and p-value. Finally, Appendix E002 (`2-appendix/experiments.tex`) reports disagreement rates for evaluation (2.66%) but does not compute inter-rater reliability metrics like Cohen's Kappa or Fleiss' Kappa. To ensure reproducibility and validity, statistical tests must be added to all comparative claims, and the limitations of the n=3 sample size should be explicitly acknowledged in the text.
