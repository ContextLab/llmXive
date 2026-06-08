---
action_items:
- id: d63d7603e2cd
  severity: science
  text: Report standard deviations over multiple training seeds in Table 1 (main_table.tex)
    to quantify variance in accuracy estimates.
- id: aabf9c3baeb4
  severity: science
  text: Perform statistical significance tests (e.g., bootstrap or paired t-tests)
    for the main accuracy comparisons between AntiSD and GRPO in Section 4.1.
- id: 6ff1d4c5781d
  severity: writing
  text: Clarify the number of evaluation seeds used for avg@32 metrics and ensure
    benchmark variance (AIME size) is acknowledged as a limitation.
artifact_hash: 5a5c1b2fc5b93010078510a2719b14ae8df452ff19cefaab0b0cc9b505e14712
artifact_path: projects/PROJ-611-https-arxiv-org-abs-2605-11609/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-08T14:45:27.426593Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The statistical reporting in Section 4 (Experiments) and Table 1 (main_table.tex) lacks necessary rigor for a NeurIPS submission. While the reported effect sizes (e.g., +11.5 points average accuracy, Abstract) are large, the absence of uncertainty quantification makes it difficult to distinguish robust improvements from stochastic variance inherent in RL training.

**1. Variance Reporting:** Table 1 presents single point estimates for accuracy across five models and five benchmarks. In reinforcement learning, training runs exhibit high variance due to initialization and sampling noise. Standard practice requires reporting mean ± standard deviation (or confidence intervals) aggregated over multiple independent training seeds (e.g., 3-5 seeds). Currently, the table implies a single run per configuration (Section 4 Setup states "We train five language models... for 200 on-policy steps" without mentioning seeds). Without error bars, claims like "AntiSD's final mean accuracy exceeds GRPO's on every model" (Section 4.1) are descriptive rather than inferential.

**2. Significance Testing:** The paper asserts strong comparative claims (e.g., "2 to 10x fewer training steps," Abstract) without statistical tests. Given the small size of evaluation benchmarks (AIME 2024/2025/2026 typically contain ~30 problems each), accuracy estimates have non-negligible binomial variance. I recommend adding bootstrap confidence intervals or paired t-tests comparing AntiSD vs. GRPO performance across seeds to validate that the observed gains are statistically significant.

**3. Benchmark Variance:** The evaluation aggregates AIME 2024, 2025, and 2026. While this increases sample size, the difficulty distribution may vary year-to-year. The current averaging hides potential instability on specific subsets. I suggest reporting per-benchmark variance or ensuring the aggregation method is robust to outliers.

**4. Gate Calibration:** Section 4.1 describes calibrating the entropy gate threshold ($\tau_{\mathrm{down}}$) from the first 5 steps. While efficient, this introduces a hyperparameter dependency on early training dynamics. Sensitivity analysis in Table 3 (ablation_q4_table.tex) shows threshold impacts, but without variance across seeds, it is unclear if the "0.93" multiplier is universally robust or model-specific.

Addressing these points will strengthen the empirical claims and ensure reproducibility.
