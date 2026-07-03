---
action_items:
- id: d94b6dbe35a4
  severity: science
  text: The NeurIPS Checklist explicitly states 'No' for statistical significance
    (Item 7), claiming error bars are not required in the field. However, the ablation
    studies (Tables 4 & 5) show large performance swings (e.g., VisA dropping from
    76.8% to 55.5% without SFT). The authors must provide standard deviations or results
    from multiple random seeds to confirm these gains are not due to random initialization
    or data split variance.
- id: 34f6218b3424
  severity: science
  text: The reward function (Eq. 3) relies on ground-truth IoU ($R_{loc}$) and semantic
    distance ($R_{type}$) during training. The paper does not specify if the test
    set annotations used for these rewards are the same as those used for evaluation,
    or if a separate validation set was used for RL tuning. If the RL policy was optimized
    directly on the test set metrics, this constitutes data leakage and invalidates
    the SOTA claim.
- id: f7020d7bc2bc
  severity: science
  text: The 'Tool Usage Statistics' table (Appendix) reports a 99.1% success rate
    for tool calls. The definition of 'success' is ambiguous (e.g., API return 200
    vs. correct visual crop). Without a clear definition and error analysis of failed
    tool calls, the claim that the agent is 'cost-aware' and 'reliable' is not fully
    supported by the evidence.
artifact_hash: becd970ef8620fcce447156389fb0620d5149fe00a85e4d09a2c8efc9340b659
artifact_path: projects/PROJ-613-indusagent-reinforcing-open-vocabulary-i/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T18:22:33.340311Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The paper presents IndusAgent, an agentic framework for open-vocabulary industrial anomaly detection, claiming state-of-the-art performance across five benchmarks. While the reported average scores (83.4%) and recall improvements (+17.4% on MPDD) are substantial, the scientific evidence supporting the robustness of these claims is currently insufficient due to a lack of statistical rigor and potential methodological ambiguities in the reinforcement learning setup.

First, the manuscript explicitly opts out of reporting statistical significance in the NeurIPS Checklist (Item 7), citing field norms. However, the ablation studies (Section 4.3, Tables 4 and 5) demonstrate massive performance variances when components are removed (e.g., VisA performance drops from 76.8% to 55.5% without SFT). In deep learning, particularly with RL and LLMs, results can be highly sensitive to random seeds, hyperparameters, and data shuffling. Without reporting standard deviations over multiple runs (e.g., 3-5 seeds) or confidence intervals, it is impossible to determine if the observed gains are statistically significant or artifacts of a specific random initialization. The claim of "catastrophic collapse" without SFT is dramatic but requires statistical backing to be scientifically rigorous.

Second, the reward formulation in Section 3.2 (Eq. 3) introduces a potential source of data leakage. The reward components $R_{loc}$ (IoU) and $R_{type}$ (semantic distance) require ground-truth annotations. The paper does not clarify whether the RL training process utilized the test set annotations to compute these rewards. If the agent was optimized to maximize metrics calculated on the test set, the reported SOTA results are invalid. Even if a validation set was used, the authors must explicitly state the separation of data splits for SFT, RL training, and final evaluation to ensure the integrity of the benchmark results.

Finally, the "Tool Usage Statistics" in the Appendix report a >98% success rate for tool calls. The definition of "success" is not provided. Does this mean the tool executed without crashing, or that the tool returned a visually useful crop? If the metric is merely API availability, it does not support the claim of "reliable" diagnostic reasoning. The evidence for the agent's cost-awareness (penalizing redundant calls) is also weak without a breakdown of inference latency or computational cost per image compared to baselines.

To strengthen the scientific evidence, the authors must: (1) Report mean and standard deviation for all main results and ablation studies across multiple seeds; (2) Explicitly confirm that test set annotations were never used during the RL reward calculation; and (3) Define "tool success" and provide latency/cost metrics to substantiate the efficiency claims.
