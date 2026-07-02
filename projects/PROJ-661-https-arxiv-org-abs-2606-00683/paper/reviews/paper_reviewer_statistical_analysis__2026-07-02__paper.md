---
action_items:
- id: 1f01527ad7bc
  severity: science
  text: The evaluation section reports single-point accuracy metrics (In-Acc, F1,
    R-Acc) without confidence intervals or standard deviations. Given the stochastic
    nature of LLM inference and the finite size of test sets (e.g., 2,417 samples
    for MuSiQue), statistical significance testing (e.g., bootstrap CIs or paired
    t-tests) is required to substantiate claims of superiority over baselines.
- id: e3ea124a8f7d
  severity: science
  text: The Memorization Ratio (M_R) is defined as P_o / (P_o + P_c) but lacks an
    associated uncertainty estimate. With ConFiQA subsets varying in difficulty, the
    variance in M_R across the QA, MR, and MC subsets should be reported to assess
    the stability of the faithfulness claim.
- id: 9a40d58de6ee
  severity: science
  text: The paper claims OCC-RAG-0.6B 'exceeds' baselines on every benchmark. Without
    reported p-values or confidence intervals for the differences in accuracy (e.g.,
    the 9.5 point gap on ConFiQA), it is statistically premature to assert these improvements
    are not due to random variance in the evaluation samples.
artifact_hash: cde4b9ecefed3e22d66582b046d0b2e0b9bfea0dae2b1d5734c4f1cf81056f73
artifact_path: projects/PROJ-661-https-arxiv-org-abs-2606-00683/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T20:28:35.380275Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The statistical analysis in the evaluation section (Section 5) is insufficient to support the strong comparative claims made in the paper. The authors report point estimates for accuracy (In-Acc, F1, R-Acc) and the Memorization Ratio (M_R) across multiple benchmarks (HotpotQA, MuSiQue, ConFiQA, etc.) but fail to provide any measure of statistical uncertainty.

Specifically, the test sets have finite sizes (e.g., 7,405 for HotpotQA, 2,417 for MuSiQue). For a model achieving ~60% accuracy on a 2,400-sample set, the standard error is approximately 1%. While the reported gaps (e.g., 9.5 points on ConFiQA) appear large, the paper does not perform or report statistical significance tests (such as bootstrap confidence intervals, paired t-tests, or McNemar's test) to confirm that the observed differences between OCC-RAG and the baselines (like Qwen3-1.7B or Pleias-RAG) are statistically significant rather than artifacts of sampling variance.

Furthermore, the Memorization Ratio (M_R) is a derived metric calculated from the rates of original vs. counterfactual answers. The paper defines the formula but does not report the variance of this ratio across the three ConFiQA subsets (QA, MR, MC) or provide confidence intervals. Given that the paper's central claim relies on the model's "faithfulness" and "calibrated abstention," the lack of uncertainty quantification for these specific metrics weakens the empirical evidence. The authors should re-run the evaluation to compute 95% confidence intervals for all reported metrics and include significance testing for the key comparisons highlighted in the Results section.
