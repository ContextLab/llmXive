---
action_items:
- id: bb3fde40cb68
  severity: writing
  text: 'The paper presents a compelling method (TRB) for stabilizing early on-policy
    distillation, but the evidence supporting the claim that TRB is strictly superior
    to baselines relies on point estimates that lack reported variance. In Table 1,
    the headline result is that TRB achieves the highest average score in both model
    settings. However, the margins are narrow: a 0.9 point gain on the 1.7B setup
    and a 0.4 point gain on the 0.6B setup. The experimental setup section (Appendix
    A) details the hyperp'
artifact_hash: a0fcc4014c0149719a56a0fd8c9438fb07408db2050a8ea923c6bb42f703660e
artifact_path: projects/PROJ-649-trust-region-behavior-blending-for-on-po/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T23:50:45.861772Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The paper presents a compelling method (TRB) for stabilizing early on-policy distillation, but the evidence supporting the claim that TRB is strictly superior to baselines relies on point estimates that lack reported variance.

In Table 1, the headline result is that TRB achieves the highest average score in both model settings. However, the margins are narrow: a 0.9 point gain on the 1.7B setup and a 0.4 point gain on the 0.6B setup. The experimental setup section (Appendix A) details the hyperparameter sweeps and the protocol for selecting the "best" checkpoint, but it does not state how many random seeds were used to train each model configuration, nor does it report the standard deviation of the final scores across seeds. In LLM training, especially with small model sizes and complex objectives like OPD, performance can vary significantly between seeds. Without reporting mean ± standard deviation (or confidence intervals) over multiple independent runs, it is impossible to determine if the observed 0.4–0.9 point improvements are a robust effect of the method or simply the result of a lucky initialization or a single favorable run. The authors should re-run the main experiments (TRB and Vanilla OPD) with at least 3-5 seeds and report the variance to substantiate the claim of superiority.

Additionally, the comparison between TRB and the "Temperature warmup" baseline introduces a potential confound regarding computational effort. TRB involves online teacher decoding and a binary search for the blending coefficient during the warmup phase, which is computationally more intensive than simply lowering the student's sampling temperature. While the paper acknowledges the efficiency overhead in the Limitations section, the experimental design does not isolate whether the performance gain comes from the specific *mechanism* of trust-region blending or simply from the fact that the TRB warmup spends more compute/teacher interaction time on the early rollouts. A more rigorous comparison would either match the compute budget (e.g., by extending the temperature warmup duration or increasing its intensity to match TRB's cost) or include an ablation that isolates the contribution of the KL-constraint solver itself versus the mere act of adding teacher guidance. Without this, the claim that the *specific* TRB formulation is the driver of the gain remains slightly confounded by the "more effort" alternative explanation.
