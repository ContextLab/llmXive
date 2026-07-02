---
action_items:
- id: 9055d27effaa
  severity: science
  text: The abstract and Section 5.2 report a Pearson correlation of r=0.950 on n=150
    instances but omit 95% confidence intervals. Please report the CI for both Pearson's
    r and Spearman's rho in Table 3 to quantify the precision of these estimates.
- id: 3db7d21630d8
  severity: science
  text: In Section 5.4 (Degradation Analysis), pairwise comparisons (e.g., alpha=50
    vs alpha=75) are mentioned with Holm-Bonferroni correction, but the specific p-values
    and the exact test statistic (t-statistic) are not reported in the text or tables.
    Please add these values to ensure reproducibility.
- id: 7ca62b500e2c
  severity: science
  text: The ground-truth construction relies on the intersection of successful trajectories
    (Section 3.3). This introduces a selection bias where only solvable instances
    are included. Please explicitly quantify the size of the excluded set (instances
    with <2 successful trajectories) and discuss how this limits the generalizability
    of the 'missing context is dominant' conclusion to unsolvable or hard-to-solve
    issues.
artifact_hash: d01bf725e90093797f2151085112b0bd34f0dac442648b3b22aae07b0ee791b3
artifact_path: projects/PROJ-687-swe-explore-benchmarking-how-coding-agen/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T20:45:32.371320Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The statistical analysis in SWE-Explore is generally sound, particularly in the use of trajectory-grounded ground truth and the downstream validation protocol. However, several critical statistical details are missing or insufficiently reported, preventing a full assessment of the robustness of the claims.

First, regarding the correlation analysis in Section 5.2 and Table 3: The authors report a very high Pearson correlation ($r=0.950$) between Context Efficiency and downstream resolve rate based on a subset of $n=150$ instances. While the magnitude is impressive, the absence of 95% confidence intervals (CIs) for both Pearson's $r$ and Spearman's $\rho$ is a significant omission. Given the sample size, the precision of these estimates should be quantified. The abstract mentions that CIs are now reported, but they are not visible in the provided text or tables. Please ensure the final manuscript includes these intervals (e.g., via bootstrapping or Fisher's z-transformation) to demonstrate that the correlation is not an artifact of the specific subset chosen.

Second, the degradation analysis in Section 5.4 and Figure 3 involves multiple hypothesis tests (pairwise comparisons across different $\alpha$ levels). The authors state that Holm-Bonferroni correction was applied, which is appropriate for controlling the family-wise error rate. However, the specific p-values and the underlying test statistics (e.g., t-statistics for the two-sample t-tests) are not reported in the text or the figure captions. Without these values, it is impossible to verify the significance of the reported "threshold-like pattern" or the claim that the dip at $\alpha=25$ is a "caveat rather than the main effect." Please add a supplementary table or expand the text to include the exact p-values and test statistics for the key comparisons (e.g., $\alpha=50$ vs $\alpha=75$).

Third, the ground-truth annotation methodology (Section 3.3) introduces a potential selection bias. The benchmark only includes instances where at least two successful agent trajectories were observed. This inherently filters out difficult or unsolvable issues. While the authors acknowledge this as a "Selection Bias Limitation" in the abstract, they do not quantify the extent of this filtering. How many instances were excluded from the original source datasets (SWE-bench Verified, Pro, Multilingual) due to this criterion? A quantitative analysis of the excluded set (e.g., comparing the difficulty or characteristics of excluded vs. included instances) is necessary to properly contextualize the claim that "missing context is the dominant failure mode." If the excluded instances are those where context is irrelevant (because the issue is unsolvable regardless of context), the conclusion may be biased.

Finally, the use of $K=5$ regions is justified by the average number of core regions being 4.7. However, the distribution of core region counts is not provided. If the distribution is highly skewed, a fixed $K=5$ might be suboptimal for a significant portion of instances. A brief discussion or histogram of the core region count distribution would strengthen the justification for this hyperparameter choice.

In summary, while the experimental design is innovative, the statistical reporting requires enhancement to meet the rigor expected for a benchmark paper. Specifically, the addition of confidence intervals, full statistical test results, and a quantitative analysis of the selection bias is required.
