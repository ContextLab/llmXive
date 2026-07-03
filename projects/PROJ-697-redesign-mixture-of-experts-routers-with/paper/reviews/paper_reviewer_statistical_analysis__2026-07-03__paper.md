---
action_items:
- id: b87ce580bea0
  severity: science
  text: The paper reports downstream performance improvements (e.g., Table 1, Table
    3) and loss reductions (e.g., Figure 1, Table 2) as deterministic facts without
    reporting statistical significance. Given the stochastic nature of deep learning
    training, the authors must report standard deviations or confidence intervals
    across multiple random seeds (e.g., 3-5 runs) to confirm that the observed gains
    are not due to random variance.
- id: e7f7aec31b5a
  severity: science
  text: In Section 5.1 (Ablation Studies), the claim that 10 power iterations 'provides
    no further convergence advantage' is based on a single run comparison (0.002-0.003
    loss increase). Without error bars or variance estimates, it is impossible to
    distinguish a genuine performance drop from noise. The authors should re-run these
    ablations with multiple seeds to validate the stability of the single-iteration
    choice.
- id: 141928149aea
  severity: science
  text: The sensitivity analysis of hyperparameter C' (Table 4) presents a single
    validation perplexity value for each setting. To support the claim of 'insensitivity,'
    the authors should report the variance of these metrics across different random
    seeds or data shuffles, as small fluctuations in PPL could otherwise be misinterpreted
    as robustness.
artifact_hash: 34fabb025335fc2fcf0855d53316dbb275a62eee03c0f1ad1b72c49ea11b1392
artifact_path: projects/PROJ-697-redesign-mixture-of-experts-routers-with/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T10:00:51.330298Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The manuscript presents a novel router design for Mixture-of-Experts (MoE) models, but the statistical rigor of the empirical evaluation is insufficient to support the strong claims of superiority. The primary concern is the complete absence of measures of statistical uncertainty. Throughout the "Experiment" section (Sections 4 and 5), performance metrics such as downstream accuracy (Table 1, Table 3), perplexity (Table 2), and convergence rates (Figures 1-3) are reported as single point estimates derived from what appears to be a single training run per configuration.

In deep learning research, training dynamics are inherently stochastic due to random weight initialization, data shuffling, and optimizer noise. Reporting a single run without standard deviations, confidence intervals, or p-values makes it impossible to determine if the observed improvements (e.g., the 0.013 loss reduction in Figure 1 or the 2.33% accuracy gain in Table 3) are statistically significant or merely artifacts of a favorable random seed. For instance, the claim in Section 5.1 that increasing power iterations to 10 results in a "downstream drop of 1.39 percentage points" is presented as a definitive finding, yet without variance estimates, this difference could easily fall within the noise floor of the training process.

Furthermore, the sensitivity analysis of the hyperparameter $C'$ (Table 4) relies on single-point validation perplexity values. To robustly claim that the method is "relatively insensitive" to this parameter, the authors must demonstrate that the performance variance across seeds is small relative to the differences between $C'$ settings. The current presentation lacks the necessary statistical evidence to distinguish between genuine robustness and random fluctuation.

To address these issues, the authors should re-run their key experiments (main comparisons, ablation studies, and sensitivity analyses) with at least three independent random seeds. They must then report the mean and standard deviation (or 95% confidence intervals) for all quantitative results in tables and figures. Additionally, for the main performance claims, a statistical significance test (e.g., a paired t-test or Wilcoxon signed-rank test) should be performed to confirm that the improvements over the vanilla MoE baseline are not due to chance. Without these additions, the empirical evidence remains anecdotal rather than statistically sound.
