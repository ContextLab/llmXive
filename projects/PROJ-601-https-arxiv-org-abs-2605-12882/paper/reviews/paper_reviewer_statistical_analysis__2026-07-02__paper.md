---
action_items:
- id: 0a705d3eb2bd
  severity: science
  text: The statistical analysis presented in the CiteVQA paper is currently insufficient
    to support the strong claims regarding model performance gaps and the validity
    of the proposed metrics. First, the validation of the automated evaluation pipeline
    (Appendix, Table tab:model-eval) relies exclusively on the Friedman test to compare
    LLM judges against human experts. The authors report p-values > 0.05 and conclude
    there is "no statistically significant deviation." This is a fundamental statistical
    erro
artifact_hash: 567bb319ad9aec08be02c875d29027d6ab5aa636652eb3a41f2a0b1e3b7ef794
artifact_path: projects/PROJ-601-https-arxiv-org-abs-2605-12882/paper/specs/001-paper/tasks.md
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T02:16:59.537966Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: full_revision
---

The statistical analysis presented in the CiteVQA paper is currently insufficient to support the strong claims regarding model performance gaps and the validity of the proposed metrics.

First, the validation of the automated evaluation pipeline (Appendix, Table `tab:model-eval`) relies exclusively on the Friedman test to compare LLM judges against human experts. The authors report p-values > 0.05 and conclude there is "no statistically significant deviation." This is a fundamental statistical error: failing to reject the null hypothesis does not prove the null hypothesis (equivalence). To validate the judges, the authors must demonstrate *agreement*, not just a lack of difference. A Bland-Altman plot to assess bias and limits of agreement, or the calculation of the Intraclass Correlation Coefficient (ICC) and Cohen's kappa, is mandatory to quantify the reliability of the LLM judges. Without this, the primary metrics (SAA, Rel, Ans) are built on an unverified foundation.

Second, the definition of the primary metric, Strict Attributed Accuracy (SAA), is statistically opaque. The formula $\text{SAA} = \mathbf{1}_{(\text{Ans.} \ge 4 \land (\text{Rel.} \ge 4 \lor \text{Rec.} \ge 0.6))}$ combines a continuous relevance score with a binary recall threshold using a logical OR. This creates a non-monotonic and discontinuous surface where a model could theoretically improve its relevance score but fail the metric if recall drops slightly below 0.6, or vice versa. The threshold of 0.6 for IoU-based recall is arbitrary and lacks justification. A sensitivity analysis showing how SAA varies with different recall thresholds (e.g., 0.5, 0.6, 0.7) is required to ensure the metric is robust.

Third, the comparative results in Table `tab:main_results` lack any measure of statistical uncertainty. The paper ranks 20 models based on point estimates (e.g., 76.0 vs 69.3). With a dataset size of 1,897, the standard error for these proportions is likely small, but the authors do not report confidence intervals or perform pairwise statistical tests (e.g., McNemar's test or paired t-tests on the binary SAA outcomes) to determine if the observed differences are statistically significant. Without this, the claim that "Gemini-3.1-Pro-Preview leads" is merely descriptive, not inferential.

Finally, the ground truth generation relies on an ablation-based procedure to identify "Crucial Evidence" (Section 3.3). The statistical stability of this process is unreported. If the set of "crucial" elements changes significantly when the ablation model is re-run with different seeds, the ground truth is noisy. The authors should report the inter-rater reliability (e.g., Cohen's kappa) of the crucial evidence identification process, perhaps by running the ablation pipeline multiple times or using a second model to verify the crucial elements.

In summary, the paper requires a full revision to include rigorous statistical validation of the judges, a sensitivity analysis of the SAA metric, and proper statistical testing for model comparisons.
