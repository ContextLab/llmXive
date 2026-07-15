---
action_items:
- id: 4382e7c6d83b
  severity: writing
  text: The paper presents a compelling method for weak-to-strong generalization,
    but the experimental design has gaps that prevent the reported results from definitively
    establishing the claimed mechanisms. First, the primary evidence for the method's
    efficacy relies on single-run results reported in Table 1 and Figure 2. For instance,
    the claim that Direct-OPD boosts Qwen3-1.7B from 48.3% to 58.3% on AIME 2024 is
    presented as a definitive improvement. However, Reinforcement Learning with Verifiable
    Re
artifact_hash: fe03c20c23e17e66c41241fcf88a5ad32b5f8c89483ca27ec649ff3d3b355988
artifact_path: projects/PROJ-1059-weak-to-strong-generalization-via-direct/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-15T02:39:31.914921Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The paper presents a compelling method for weak-to-strong generalization, but the experimental design has gaps that prevent the reported results from definitively establishing the claimed mechanisms.

First, the primary evidence for the method's efficacy relies on single-run results reported in Table 1 and Figure 2. For instance, the claim that Direct-OPD boosts Qwen3-1.7B from 48.3% to 58.3% on AIME 2024 is presented as a definitive improvement. However, Reinforcement Learning with Verifiable Rewards (RLVR) is notoriously stochastic; performance can vary significantly across different random seeds due to the high variance in rollout generation and reward signals. Without reporting results across multiple seeds (e.g., 3-5) with standard deviations or confidence intervals, it is impossible to distinguish a genuine methodological improvement from a lucky seed or sampling noise. A 10% point gain is substantial, but if the standard deviation across seeds is 5-8%, the result is not statistically robust. The authors must report variance to validate that the effect is reproducible.

Second, the efficiency claim in Section 4.2 ("Weak-to-strong generalization beats RL") compares wall-clock time but fails to control for total compute or data exposure. The authors compare a 1.5B model trained for 1500 steps (plus a short transfer) against a 7B model trained for a matched number of steps. However, the 1.5B model likely consumes significantly fewer FLOPs per step. If the 7B model were allowed to run for a compute budget equivalent to the 1.5B model's training plus the transfer cost, it might achieve similar or better performance. The current design confounds the "weak-to-strong" mechanism with the possibility that the small model simply had a more favorable training trajectory or data exposure per unit of compute. A compute-matched ablation is required to isolate the benefit of the transfer mechanism itself.

Finally, the sequential composition experiment (Section 4.3) lacks a negative control. The authors show that applying Shift A then Shift B improves performance. However, they do not demonstrate that applying Shift A then Shift A (or a random shift) does not yield similar gains. Without this control, the improvement could be attributed to the simple fact of additional training steps (more optimization) rather than the specific composition of distinct policy shifts. A control run applying the same shift twice would help rule out the "more training" alternative explanation.
