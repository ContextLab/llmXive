---
action_items:
- id: 666447f8acfa
  severity: science
  text: The claim of 50% first-frame latency reduction contradicts the footnote stating
    first-frame latency is determined by 4-step generation for all methods. Clarify
    the metric or correct the claim.
- id: c1511b80e6f7
  severity: science
  text: Table 1 compares 1/2-step Causal CD against a 4-step Causal ODE baseline.
    Re-run Causal ODE initialization for 1-step and 2-step settings to ensure a fair
    ablation comparison.
- id: 0da61e01cb74
  severity: science
  text: Report standard deviations for the Stage 2 training time (11,600 vs 2,900
    GPU hours) to validate the robustness of the 4x efficiency claim.
artifact_hash: bc6ea3b7abb50e6d2d0c61521fe88f76d18733e7f3e4d74c5eba9d5fe9acb8e6
artifact_path: projects/PROJ-580-https-arxiv-org-abs-2605-15141/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T01:56:58.490688Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The paper presents a compelling methodological argument for replacing causal ODE distillation with causal consistency distillation (CD) to improve efficiency in few-step autoregressive video generation. However, the scientific evidence supporting the central claims regarding latency reduction and the fairness of the ablation studies requires clarification.

First, the claim of a 50% reduction in first-frame latency (Abstract; Table 2) appears inconsistent with the provided experimental setup. The footnote in Table 2 explicitly states that due to the ASD trick, "the first-frame latency for 1-step, 2-step, and 4-step generation is identical, and is determined by the 4-step generation of the first frame." Since the baseline methods (CausVid, Self Forcing, Causal Forcing) are also 4-step models, and the proposed method's first frame is also generated in 4 steps, the critical path latency should theoretically be identical, not reduced by 50%. The evidence suggests the latency reduction might apply to *subsequent* frames or total video generation time, but the claim of "first-frame latency" reduction is not supported by the described mechanism. This requires a correction in the text or a re-evaluation of the metric.

Second, the ablation study in Table 1 compares Causal CD against Causal ODE initialization. The text notes that "causal ODE is trained under the 4-step setting." It is unclear if the Causal ODE baseline was re-initialized and trained specifically for the 1-step and 2-step settings to match the Causal CD evaluations. If the 1-step and 2-step Causal CD results are compared against a 4-step Causal ODE initialization, the comparison is confounded, as the initialization quality for fewer steps may differ significantly. To robustly support the claim that Causal CD is a superior substitute across all step counts, the authors must provide Causal ODE baselines specifically trained for the 1-step and 2-step regimes.

Finally, the efficiency claims (4x speedup, 11,600 vs 2,900 GPU hours) are presented as point estimates. Given the stochasticity of deep learning training, reporting the variance (e.g., standard deviation over multiple runs or seeds) for these training time metrics would strengthen the evidence for the claimed efficiency gains. Without this, the robustness of the 4x improvement claim remains uncertain.
