---
action_items:
- id: f23d54164128
  severity: science
  text: The standard error for success rates (n=20) is ~0.11. The paper claims significant
    superiority of PICA over baselines at high damping (e.g., 0.56 vs 0.27) without
    reporting confidence intervals or statistical significance tests (e.g., t-tests
    or bootstrap CIs). Given the high variance in RL, these differences may not be
    statistically significant. Please add 95% CIs to Table 1 and Figure 2.
- id: f83a6fc42f77
  severity: science
  text: The ablation study (Table 3) compares 'w/o PICA' and 'w/o GLA' but does not
    report variance or perform pairwise statistical tests between the full model and
    ablations. The claim that components are 'complementary' relies on point estimates
    that fall within the margin of error for n=20. Provide statistical validation
    for the ablation conclusions.
- id: 7e1296447445
  severity: science
  text: The training-length study (Table 2) shows a collapse in robustness from 0.55
    to 0.10. While the trend is clear, the lack of error bars or multiple seeds makes
    it difficult to distinguish between a systematic failure mode and stochastic variance.
    Please clarify if these results are averaged over multiple random seeds or single
    runs.
artifact_hash: aac12eff083d8d7168328cdeef9fdab897d5808d01d31c99a8c36453db9b88d3
artifact_path: projects/PROJ-750-dragmesh-2-physically-plausible-dexterou/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-30T13:51:09.219687Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The statistical analysis in DragMesh-2 is rigorous in its design of the evaluation protocol (damping randomization, OOD testing) but lacks necessary statistical reporting to support the magnitude of the claimed improvements.

**1. Lack of Confidence Intervals and Significance Testing**
The primary results in Table 1 (Main Comparison) and Figure 2 rely on point estimates derived from 20 episodes per cell. For a binary success metric with $n=20$, the standard error is approximately $\sqrt{p(1-p)/20} \approx 0.11$ (at $p=0.5$). The paper claims PICA achieves 0.56 success at $\times4$ damping versus 0.27 for State-only PPO. While the absolute difference is large, without 95% confidence intervals or a statistical test (e.g., two-proportion z-test or bootstrap), it is impossible to determine if this difference is statistically significant or within the noise floor of the evaluation. The text states PICA "attains the best mean" but does not quantify the uncertainty. I recommend adding error bars to Figure 2 and reporting 95% CIs in Table 1.

**2. Insufficient Statistical Validation of Ablations**
Table 3 (Ablation) isolates the PICA and GLA components. The authors claim the components are "complementary" because the full model outperforms the ablations by at least 0.13 at $\times4$ damping. However, given the sample size ($n=20$), a difference of 0.13 is barely outside the standard error. The paper does not report whether these differences are statistically significant. Without pairwise statistical comparisons (e.g., McNemar's test for paired binary outcomes if the same seeds were used, or independent t-tests), the claim of complementarity is weak.

**3. Training-Length Study Variance**
Table 2 presents a critical finding: longer training leads to robustness collapse (0.55 $\to$ 0.10). This is a strong qualitative claim. However, the table does not indicate if these values are averages over multiple random seeds or single runs. In RL, single-run results can be highly volatile. If these are single runs, the "collapse" might be an artifact of a specific seed rather than a systematic overfitting phenomenon. The authors must clarify the number of seeds used for these diagnostic experiments and provide variance metrics.

**4. Reproducibility of Metrics**
The definition of `clip099` and `detach_proxy` is clear, but the statistical aggregation method for these continuous/diagnostic metrics is not fully specified. Are the means reported in the text (e.g., "clip099 climbs toward 1.0") accompanied by standard deviations? The text mentions "standard error of a success estimate is approximately 0.10" in the Limitations section (Appendix), which is a good acknowledgment, but this uncertainty is not propagated into the main results tables or the interpretation of the "significant" gains.

To strengthen the paper, the authors should re-run the main comparison and ablation studies with multiple random seeds (at least 3-5) to compute standard deviations, add confidence intervals to all quantitative tables and figures, and perform statistical significance tests to validate the superiority of PICA over baselines.
