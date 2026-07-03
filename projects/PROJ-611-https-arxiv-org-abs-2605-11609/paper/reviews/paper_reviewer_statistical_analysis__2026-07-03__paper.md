---
action_items:
- id: dad77d7ca584
  severity: science
  text: Section 4.1 (Main results) and Table 1 report point estimates for accuracy
    and speedup but omit measures of statistical uncertainty (e.g., standard deviation,
    confidence intervals, or error bars) across the 32 rollouts or multiple seeds.
    Given the small margins in some benchmarks (e.g., Olmo3-7B-TK MinervaMath -0.6pp),
    statistical significance testing (e.g., paired t-test or bootstrap) is required
    to validate that AntiSD's gains are not due to variance.
- id: b5618422e9bc
  severity: science
  text: The entropy gate threshold (tau_down = 0.93 * H_warm) is auto-calibrated from
    5 warmup steps (Section 4 Setup). The paper does not report the variance of H_warm
    across the batch or models, nor does it provide a sensitivity analysis on the
    stability of this threshold. A statistical justification for the 0.93 multiplier
    or a confidence interval for the entropy collapse point is needed to ensure the
    gate is not overfitting to a specific batch realization.
- id: 8c8c36a078a5
  severity: science
  text: In Section 4.3 (Ablations), the 'No-gate' configuration shows model-dependent
    failure (collapse on Qwen, survival on Olmo). The paper attributes this to initial
    teacher entropy but does not provide statistical evidence (e.g., distributions
    of initial entropy values) to support this claim. Quantitative comparison of the
    entropy distributions between model families is required to substantiate the 'model-conditional'
    argument.
artifact_hash: 5a5c1b2fc5b93010078510a2719b14ae8df452ff19cefaab0b0cc9b505e14712
artifact_path: projects/PROJ-611-https-arxiv-org-abs-2605-11609/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T07:26:48.982407Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The statistical analysis in the paper is rigorous in its theoretical derivation of the per-token signal (PMI) and the bounded nature of the JSD ascent. However, the empirical validation of the proposed method's superiority lacks necessary statistical rigor regarding uncertainty quantification and significance testing.

First, the main results in Section 4.1 and Table 1 present accuracy metrics as single point estimates (e.g., "65.7" for Qwen3-8B AntiSD). While the evaluation uses `avg@32` (averaging over 32 rollouts per problem), the paper does not report the standard deviation of these averages across the test set, nor does it provide confidence intervals. Given that the performance gains on some benchmarks are marginal (e.g., the -0.6pp gap on MinervaMath for Olmo3-7B-TK), it is impossible to determine if the observed improvements are statistically significant or within the noise of the evaluation process. Standard practice for RL benchmarks requires reporting error bars or conducting significance tests (e.g., paired t-tests or bootstrap resampling) to validate claims of superiority.

Second, the entropy-triggered gate mechanism relies on a threshold $\tau_{\mathrm{down}} = 0.93 \cdot H_{\mathrm{warm}}$, calibrated from only 5 warmup steps (Section 4, Setup). The paper does not discuss the variance of $H_{\mathrm{warm}}$ across different batches or models. Without reporting the distribution of teacher entropy during warmup, it is unclear if the 0.93 multiplier is a robust statistical choice or a heuristic that might fail under different data distributions. A sensitivity analysis showing the stability of the gate's activation across different random seeds or batch realizations would strengthen the reproducibility of this component.

Finally, the ablation study in Section 4.3 attributes the model-dependent failure of the "No-gate" variant to differences in initial teacher entropy. While the text claims Qwen models start at $\approx 0.4$ nats and Olmo higher, it does not provide the statistical distribution (mean, variance, or range) of these initial entropy values across the training runs. Providing these statistics would substantiate the claim that the gate is "essential for Qwen and inert for Olmo" rather than a result of specific random seeds or batch effects.

To address these concerns, the authors should: (1) report standard deviations or confidence intervals for all accuracy metrics in Table 1; (2) perform and report statistical significance tests comparing AntiSD against GRPO and SD; (3) include a sensitivity analysis or variance report for the entropy gate calibration; and (4) provide descriptive statistics for the initial teacher entropy across model families.
