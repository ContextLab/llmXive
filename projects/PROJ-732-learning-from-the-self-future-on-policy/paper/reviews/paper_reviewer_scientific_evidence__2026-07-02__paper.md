---
action_items:
- id: 737133108c66
  severity: science
  text: The 'sample efficiency' claim compares optimization steps but ignores that
    d-OPSD uses pass@8 sampling per step. Without normalizing by total FLOPs or wall-clock
    time, the claim is ambiguous and potentially misleading.
- id: 98451d118cd7
  severity: science
  text: The ablation on retaining ratio (Table 6) shows a weaker teacher outperforming
    a stronger one. This counter-intuitive finding lacks statistical validation (e.g.,
    error bars, multiple seeds) to distinguish signal from noise.
- id: a4b6c13d501e
  severity: science
  text: The failure mode analysis attributes collapse to 'model-seeking behavior'
    but provides no quantitative evidence (e.g., KL/entropy trajectories) to support
    this hypothesis over other causes like overfitting.
artifact_hash: 5c8da21032033f700374cf269bb9ef61b58d8799f1e6049fc84e38c052b8b257
artifact_path: projects/PROJ-732-learning-from-the-self-future-on-policy/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T04:41:34.657785Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The paper presents a novel adaptation of On-Policy Self-Distillation (OPSD) for Diffusion Large Language Models (dLLMs), proposing d-OPSD. The core scientific claims regarding the method's design (suffix conditioning, step-level divergence) are logically derived from the properties of dLLMs. However, the strength of the evidence supporting the central claims of "superior sample efficiency" and the robustness of the ablation findings requires clarification.

First, the claim of superior sample efficiency (Abstract; Section 4.2) states that d-OPSD requires "only around 10% of the optimization steps" compared to RLVR. While Table 3 lists the number of gradient updates (425 vs 7700 for GSM8K), the paper notes in Section 3.3 that d-OPSD employs a pass@k sampling strategy (k=8) to find a correct trajectory before updating, which shares the "computation overhead" of RLVR's group rollouts. The term "sample efficiency" in RL contexts typically refers to the number of environment interactions or total compute required to reach a performance threshold. If d-OPSD requires 8x more forward passes per update to find a correct trajectory, the total compute cost might be comparable to RLVR, even if the number of *updates* is lower. The manuscript conflates "optimization steps" with "sample efficiency" without normalizing for the total computational cost or wall-clock time. To support the claim of efficiency, the authors must provide a comparison based on total FLOPs or wall-clock time, or explicitly redefine the metric to avoid ambiguity.

Second, the ablation study on the retaining ratio $\rho_\text{teacher}$ (Table 6, Section 4.4) presents a counter-intuitive result where a weaker teacher ($\rho=0.10$, 80.5% accuracy) outperforms a stronger teacher ($\rho=0.50$, 79.8% accuracy). While the authors hypothesize that a weaker teacher provides a better learning signal, the difference is marginal (0.7%) and lacks statistical validation. Given the stochasticity of LLM training, this could be noise. The paper does not report standard deviations, confidence intervals, or results from multiple random seeds for these ablation runs. Without this statistical rigor, the conclusion that "distillation effectiveness is not only decided by the teacher performance" is not fully supported by the evidence provided.

Finally, the discussion of failure modes (Section 4.5) attributes policy collapse to "model-seeking behavior" becoming overly narrow. This is a plausible hypothesis consistent with prior RL literature, but the paper offers no quantitative evidence to substantiate it. There are no plots showing the evolution of the KL divergence, policy entropy, or the distribution of generated tokens over the training steps where collapse occurs. Without such data, the explanation remains speculative. The authors should include diagnostic plots or metrics to demonstrate that the collapse correlates with the predicted narrowing of the policy distribution.

In summary, while the methodological contribution is sound, the evidence for the specific claims of efficiency and the interpretation of ablation results needs to be strengthened with more rigorous statistical analysis and compute-normalized comparisons.
