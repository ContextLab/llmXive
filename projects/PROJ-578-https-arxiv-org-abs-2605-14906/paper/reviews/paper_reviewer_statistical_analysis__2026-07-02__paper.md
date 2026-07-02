---
action_items:
- id: 70d1ff8ec78e
  severity: science
  text: Report confidence intervals or standard errors for all reported accuracy metrics
    (e.g., Table 1, Table 2, Appendix Tables). With n=789, point estimates lack precision
    context.
- id: 6d9d78cb573d
  severity: science
  text: Clarify the statistical test used for the model size vs. retention correlation
    (rho=0.62, p=0.002). Specify if the p-value is from a permutation test or standard
    parametric test given the small sample of models (n=22).
- id: 2868bc8fdeb2
  severity: science
  text: Justify the use of Cohen's kappa for judge agreement on a 0/1 task with highly
    imbalanced classes (e.g., 96.40% agreement). Report prevalence-adjusted bias-adjusted
    kappa (PABAK) or Gwet's AC1 to avoid kappa paradox artifacts.
- id: ccb2b7629162
  severity: science
  text: Define the bootstrap methodology for the 195-question subset analysis (e.g.,
    stratified vs. simple random, number of iterations). Ensure the 1000 iterations
    mentioned are sufficient for stable CI estimation on small subgroups.
artifact_hash: 894b3a058a7c60576126fae0e86fbf0afb5e6919dad970b01a23558253a18ccf
artifact_path: projects/PROJ-578-https-arxiv-org-abs-2605-14906/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T01:52:42.500928Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The statistical analysis in the paper is generally rigorous, particularly in the design of the benchmark and the ablation studies. However, several key statistical reporting standards are missing or require clarification to fully support the claims.

First, the paper reports numerous point estimates for accuracy (e.g., 93.13% in Table 1, 54.10% in Table 2) without accompanying measures of uncertainty. Given the fixed test set size (n=789), the standard error for a proportion near 50% is approximately 1.8%. For smaller subgroups (e.g., the 22-question AR subset), the error bars are significantly larger (~10%). Reporting 95% confidence intervals (e.g., Wilson score intervals) for all accuracy metrics in tables and figures is essential to determine if observed differences between models (e.g., the 1-2% gaps in Table 1) are statistically significant or within noise.

Second, the correlation analysis in Appendix e002 (Section "Context-Length Analysis") reports a Spearman correlation of $\rho = 0.62$ with $p = 0.002$ between model size and retention. With only 22 data points (models), the power of this test is limited. The authors should specify the exact statistical test used to derive the p-value (e.g., permutation test vs. asymptotic approximation) and consider reporting the confidence interval for the correlation coefficient.

Third, the validation of the LLM-as-Judge relies heavily on Cohen's $\kappa$ (0.93 and 0.86). While high, Cohen's kappa can be misleading when the prevalence of the positive class (correct answers) is very high or very low, leading to the "kappa paradox." Given the high accuracy of top models, the agreement might be driven by the majority class. The authors should supplement $\kappa$ with prevalence-adjusted metrics like Gwet's AC1 or PABAK to ensure the agreement metric is robust to class imbalance.

Finally, the bootstrap analysis for the 195-question subset (Appendix e002) mentions 1000 iterations. While standard, the text does not explicitly state whether the resampling was stratified by question type to preserve the distribution of the 5 abilities. If simple random sampling was used, the resulting confidence intervals for specific ability scores (like MSR with only 35 items) may be unstable. Clarifying the resampling strategy is necessary for reproducibility.
