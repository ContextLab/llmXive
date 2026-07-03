---
action_items:
- id: 2f82bab54a3a
  severity: writing
  text: The claim that AntiSD 'opens a path to scalable self-improvement' (Abstract)
    overreaches. The method relies on privileged context (verified solutions) from
    the rollout group or dataset, not true label-free self-improvement. Clarify that
    'self' refers to parameter sharing, not absence of external supervision.
- id: 5097c2e40366
  severity: science
  text: The claim that the signal 'leaves the set of optimal policies invariant' (Section
    5) is an over-claim. The entropy-triggered gate introduces a non-potential, state-dependent
    modification. Qualify this to 'in the limit' or 'under standard assumptions' to
    reflect the finite-sample, gated reality.
- id: 084bb686f934
  severity: writing
  text: The 'drop-in replacement' claim (Abstract) overstates robustness. Table 3
    shows significant sensitivity to the entropy threshold (0.90 vs 0.95) on Qwen3-4B.
    Temper the claim to acknowledge this model-conditional sensitivity despite the
    auto-calibration.
artifact_hash: 5a5c1b2fc5b93010078510a2719b14ae8df452ff19cefaab0b0cc9b505e14712
artifact_path: projects/PROJ-611-https-arxiv-org-abs-2605-11609/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T07:23:40.091920Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: minor_revision
---

The paper presents a compelling diagnosis of the "shortcut bias" in on-policy self-distillation and proposes AntiSD, which effectively reverses this bias. The empirical results are strong, showing consistent improvements over GRPO and standard self-distillation. However, the manuscript occasionally overstates the generality and theoretical guarantees of the proposed method beyond what the data strictly supports.

First, the framing of the method as "self-improvement" where the model "bootstraps its own reasoning" (Abstract) is slightly misleading. The method fundamentally relies on "privileged context" $c$, which includes a verified solution sampled from the rollout group or the dataset. This is not a label-free self-improvement mechanism but rather a sophisticated use of ground-truth solutions to shape the reward signal. While the teacher is the student itself, the signal is not derived purely from the student's internal state but from the student's reaction to an external ground-truth solution. The abstract and introduction should clarify that the "self" refers to the parameter sharing between teacher and student, not the absence of external supervision.

Second, the claim in Section 5 (Related Work) that the per-token signal is a "potential-based reward shaping" that "leaves the set of optimal policies invariant" is theoretically sound in the limit but overreaches in the practical, finite-sample setting described. The paper introduces an entropy-triggered gate (a Schmitt trigger) that dynamically enables or disables the AntiSD term based on the median teacher entropy. This gate introduces a non-potential, state-dependent modification to the reward signal. While the authors argue this is necessary for stability, it technically violates the strict conditions for potential-based shaping invariance in a finite-horizon, stochastic optimization setting. The claim should be qualified to reflect that the invariance holds for the underlying shaping term, but the overall algorithm includes a stabilizing mechanism that may alter the effective policy landscape.

Finally, the description of AntiSD as a "drop-in replacement" (Abstract) with "no additional cost" (Abstract) slightly glosses over the sensitivity observed in the ablation studies. Table 3 demonstrates that the performance is sensitive to the entropy threshold $\tau_{\mathrm{down}}$ (e.g., a drop from 62.8 to 54.5 when changing from 0.93 to 0.90 on Qwen3-4B). While the authors note that 0.93 transfers across models, the significant performance drop with a small perturbation suggests that the method is not entirely robust without some level of tuning or model-specific calibration. The "drop-in" claim should be tempered to acknowledge this sensitivity, perhaps by stating it is a "drop-in replacement with a single auto-calibrated hyperparameter that requires no per-model tuning in our experiments" rather than implying universal robustness.

Overall, the paper is a strong contribution, but these over-claims regarding the nature of the supervision, the theoretical invariance, and the robustness of the hyperparameters should be refined to align more precisely with the presented evidence.
