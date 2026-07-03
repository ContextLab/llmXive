---
action_items:
- id: c2c1c01b910f
  severity: writing
  text: "Table 1 (math_reasoning_results) reports standard deviations (e.g., 60.0\
    \ \xB1 1.1) but does not specify the number of independent runs (N) used to calculate\
    \ them. The text mentions 'Avg@3' in the appendix, but this must be explicitly\
    \ stated in the main results tables or caption to allow for proper statistical\
    \ interpretation of the variance."
- id: 4edad4d49c6e
  severity: science
  text: The claim that KVarN 'outperforms' KIVI on AIME24 (60.0% vs 55.5%) relies
    on a difference of 4.5%. Without a reported p-value or confidence interval for
    this difference, it is unclear if this improvement is statistically significant
    or within the noise of the evaluation (given the reported std dev of 6.9% for
    KIVI). Please add significance testing (e.g., paired t-test or bootstrap CI) for
    key comparisons.
- id: bc22a39f1dc2
  severity: science
  text: The 'pseudo-decode' evaluation method (Sec 3.2) is a novel proxy for error
    accumulation. The statistical validity of this proxy relies on the assumption
    that block-wise quantization error accumulation linearly approximates autoregressive
    decoding error. The paper lacks a statistical validation (e.g., correlation analysis)
    between the pseudo-decode metric and actual end-to-end performance degradation
    to justify this methodological choice.
artifact_hash: 41b8c942a61f2cf7279ecdca15cbc48d6d8be293f3b82fe8c5a5b6e8c4e01484
artifact_path: projects/PROJ-657-https-arxiv-org-abs-2606-03458/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T01:19:42.090307Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The statistical analysis in the manuscript is generally sound in its presentation of mean performance and standard deviations across multiple benchmarks. However, several critical statistical details are missing or insufficiently justified to fully support the claims of "substantial improvement" and "error mitigation."

First, regarding **reproducibility and variance estimation**, Table 1 (Section 4.1) presents results as Mean ± Standard Deviation (e.g., 60.0 ± 1.1 for KVarN on AIME24). While the Appendix mentions "Avg@3" for MATH500 and AIME24, this crucial parameter (N=3) is not explicitly linked to the standard deviation calculations in the main text or table captions. For N=3, the standard deviation is a highly unstable estimator of population variance. The authors should explicitly state the number of runs for every reported metric and consider reporting the Standard Error of the Mean (SEM) or 95% Confidence Intervals (CIs) instead of, or in addition to, the standard deviation, especially given the small sample size.

Second, the **statistical significance of improvements** is not addressed. The paper claims KVarN achieves "best performance" and "substantial improvement" over SOTA (KIVI). For instance, on AIME24 with Qwen3-4B, KVarN scores 60.0% while KIVI scores 55.5%. However, the standard deviation for KIVI is reported as 6.9%. The difference (4.5%) is smaller than the standard deviation of the baseline. Without a formal hypothesis test (e.g., a paired t-test or a non-parametric equivalent like the Wilcoxon signed-rank test) or a reported p-value, it is statistically premature to claim a definitive improvement. The observed gain could easily be due to random variation in the prompt sampling or model initialization. The authors must perform and report significance tests for the primary comparisons in Tables 1, 2, and 3.

Third, the **methodological validity of the "pseudo-decode" setting** (Section 3.2) requires statistical justification. The authors introduce this as an efficient proxy for error accumulation in autoregressive decoding. The core assumption is that the error accumulation observed in the block-wise pseudo-decode setting correlates strongly with the actual performance degradation in full autoregressive generation. The paper presents qualitative plots (Fig. 4) showing error trends but lacks a quantitative statistical analysis (e.g., Pearson/Spearman correlation coefficient) demonstrating that the pseudo-decode metric is a reliable predictor of end-to-end accuracy. Without this validation, the use of this proxy to claim "mitigation of error accumulation" is methodologically weak.

Finally, the **decomposition of error** (Eq. 2, Section 3.1) is presented as a deterministic algebraic identity, which is correct. However, the interpretation of Figure 1a (showing magnitude errors dominate) relies on the distribution of these errors across the dataset. The authors should clarify if the "top 5% errors" are defined globally across the entire dataset or per-sample, and whether the statistical significance of the dominance of magnitude errors over directional errors was tested.

In summary, while the experimental design is robust in terms of benchmark selection, the statistical reporting lacks the rigor required to confirm that the observed improvements are not due to chance. The addition of significance testing, clearer reporting of sample sizes for variance estimates, and validation of the pseudo-decode proxy is necessary.
