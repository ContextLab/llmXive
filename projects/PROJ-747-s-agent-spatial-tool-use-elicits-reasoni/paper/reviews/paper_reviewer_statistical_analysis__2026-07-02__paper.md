---
action_items:
- id: a8d2b42595fd
  severity: science
  text: In Section 4.3 (Ablation Studies) and Table 2 (tab_ablation_config), the performance
    gains of individual components (e.g., +2.5% for Scene Memory) are reported as
    single point estimates. Given the iterative nature of the agent and potential
    variance in tool execution, please report confidence intervals or standard deviations
    (e.g., via 3-5 random seeds) to establish statistical significance of these marginal
    gains.
- id: d1b9fde85058
  severity: science
  text: In Section 4.2 (Zero-Shot Performance) and Tables 1-3, the paper claims 'best
    overall' or 'surpasses' baselines based on point-estimate accuracy differences
    (e.g., 46.4% vs 45.2%). Without reported variance or significance testing (e.g.,
    paired t-tests or bootstrap confidence intervals), it is unclear if these small
    margins (1.2%) are statistically significant or within the noise of the evaluation
    protocol.
- id: 2a74caeb827e
  severity: science
  text: In Appendix A.2 (Details of S-300K), the trajectory filtering criteria for
    numeric questions uses a fixed threshold of Mean Relative Accuracy (MRA) >= 0.6.
    The paper does not justify this threshold statistically or discuss its sensitivity.
    Please provide a sensitivity analysis or justification for this cutoff to ensure
    it does not introduce selection bias in the training data.
artifact_hash: daf6f96ab0f7dc8b7f7a6cf5f7a9c2a699ed007819d222e3f1594a2f92961a95
artifact_path: projects/PROJ-747-s-agent-spatial-tool-use-elicits-reasoni/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T19:59:09.544800Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The manuscript presents a compelling framework for spatial reasoning, but the statistical rigor of the experimental evaluation requires strengthening to support the strong claims of superiority over baselines.

First, the ablation studies in Section 4.3 and Table 2 (tab_ablation_config) report performance improvements for individual modules (e.g., adding Scene Memory yields +1.5% over the spatial-only baseline) as single point estimates. Given the stochastic nature of LLM planning and potential variance in tool outputs (e.g., depth estimation noise), these marginal gains could be within the noise floor of the evaluation. The authors should report results over multiple random seeds (e.g., 3-5) to calculate standard deviations or 95% confidence intervals. Without this, it is impossible to determine if the observed improvements are statistically significant or merely artifacts of a specific random seed or evaluation split.

Second, the main results in Tables 1, 2, and 3 claim that S-Agent "surpasses" or is the "best" based on small accuracy differences (e.g., 46.4% vs 45.2% on MMSI-Bench, a 1.2% gap). In benchmark evaluations, especially with complex agent loops, variance can be substantial. The paper lacks any form of statistical significance testing (e.g., paired t-tests, Wilcoxon signed-rank tests, or bootstrap confidence intervals) to validate these claims. A difference of 1.2% is often not statistically significant in NLP/CV benchmarks without rigorous error analysis. The authors must provide variance metrics or significance tests to substantiate that their method is genuinely superior rather than just slightly better on a specific run.

Finally, regarding the data construction in Appendix A.2, the filtering of numeric trajectories relies on a hard threshold of Mean Relative Accuracy (MRA) >= 0.6. The choice of this specific threshold appears arbitrary without statistical justification. A sensitivity analysis showing how the final model performance varies with different MRA thresholds (e.g., 0.5, 0.6, 0.7) would strengthen the reproducibility and robustness of the data generation pipeline. Currently, the lack of variance reporting and significance testing limits the confidence in the reported state-of-the-art claims.
