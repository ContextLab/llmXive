---
action_items:
- id: ade7cbff830b
  severity: science
  text: The user study (Sec. 6) reports a Spearman rank correlation of 0.90 between
    MLLM and human rankings but provides no confidence interval or p-value. With only
    100 samples and 6 raters, the statistical significance of this correlation is
    unknown. Please report the 95% CI and p-value for the SRCC.
- id: 2c8b8af02b84
  severity: science
  text: The MLLM-Score metric relies on a single judge (Gemini-3.0-Pro) without reporting
    inter-rater reliability or variance estimates. For the subject-side task, where
    multiple poses are plausible, a single deterministic score may be unstable. Please
    report the standard deviation of scores across multiple judge runs or multiple
    judges.
- id: 62b6f8219b80
  severity: science
  text: In the ablation study (Table 4), performance differences between variants
    (e.g., IoU 74.30 vs 74.10) are small. The paper does not state whether these differences
    are statistically significant or if they fall within the margin of error of the
    benchmark evaluation. Please add significance testing (e.g., paired t-test or
    bootstrap) for ablation comparisons.
artifact_hash: c05d947baccac31badb983e4672bc18e6d1ae08f6b2511780ab5cbcde805c567
artifact_path: projects/PROJ-789-shuttermuse-capture-time-photography-gui/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T03:16:49.870104Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The statistical analysis in this paper is generally sound in its design of metrics (IoU, BDE, success rates) but lacks rigorous reporting of uncertainty and significance testing, which is critical for claims of "best overall performance" and "high consistency" with human judgment.

**1. Lack of Uncertainty Quantification in User Study:**
In Section 6 ("User Study"), the authors claim that the MLLM-based ranking is "highly consistent" with human preferences, citing a Spearman rank correlation coefficient (SRCC) of 0.90. However, the manuscript fails to report the statistical significance of this correlation (p-value) or a confidence interval. With a sample size of 100 examples and only 6 human participants, the variance of the SRCC estimate is non-negligible. Without a p-value or 95% confidence interval, it is impossible to determine if the observed correlation is statistically distinguishable from random chance or if the "high consistency" claim is robust. The authors should compute and report the 95% CI for the SRCC (e.g., via bootstrapping) and the associated p-value.

**2. Single-Judge Reliability for MLLM-Score:**
The primary evaluation metric, MLLM-Score, relies on a single instance of Gemini-3.0-Pro as a judge. In Section 5.2, the authors state that each sample is assigned a score of {0, 0.5, 1}. There is no mention of inter-rater reliability (e.g., Krippendorff's alpha) or intra-rater stability (e.g., running the judge multiple times with different seeds). Given that LLM judges can exhibit stochasticity, especially in subjective tasks like "aesthetics" or "plausibility," reporting a single point estimate without error bars or variance is insufficient. The authors should report the standard deviation of the MLLM-Score across multiple independent judge runs or use an ensemble of judges to provide a more robust estimate of the metric's reliability.

**3. Statistical Significance of Ablation Results:**
Table 4 presents an ablation study comparing ShutterMuse-RL (Ours) against variants (e.g., w/o $R_{dec}$, w/o $R_{mask}$). The differences in metrics are often marginal (e.g., IoU 74.30% vs. 74.10%; RSR 82.76% vs. 79.31%). The text claims these components "contribute to the final performance," but it does not provide statistical evidence that these improvements are significant rather than noise. Given the fixed benchmark size (421 photographer-side samples), the authors should perform paired statistical tests (e.g., paired t-test or Wilcoxon signed-rank test) or bootstrap resampling to determine if the performance gains from the full model are statistically significant compared to the ablated versions.

**4. Multiple Comparisons in Baseline Evaluation:**
In Table 1, the authors compare ShutterMuse against a large number of baselines (over 15 models). While the paper highlights ShutterMuse as the "best," it does not address the issue of multiple comparisons. If the authors are making claims about ShutterMuse being significantly better than *all* baselines, a correction for multiple testing (e.g., Bonferroni or False Discovery Rate) should be considered, or at least a discussion on the risk of Type I errors in selecting the "best" model from a large pool.

In summary, while the experimental design is appropriate, the statistical reporting is incomplete. The paper requires the addition of confidence intervals, p-values, and significance tests to substantiate its claims of superiority and consistency.
