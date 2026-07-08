---
action_items:
- id: d393435f0edb
  severity: writing
  text: The paper presents a compelling method for cross-platform GUI agents, but
    the experimental design currently leaves open several alternative explanations
    for the reported gains. First, the stability of the results is unverified. Table
    2 reports a 5.6 percentage point improvement on MobileWorld (12.0% vs 6.4% for
    Mixed-SFT) and a 3.2 point gain on OSWorld. However, the paper reports these as
    single-point estimates without any indication of variance, standard deviation,
    or the number of random seed
artifact_hash: c439848c25362cb29ce1d9d26f8d9ad2ccefc577792fd895c77799b18522bbdd
artifact_path: projects/PROJ-1006-ui-mopd-multi-platform-on-policy-distill/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-08T02:55:50.635103Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The paper presents a compelling method for cross-platform GUI agents, but the experimental design currently leaves open several alternative explanations for the reported gains.

First, the stability of the results is unverified. Table 2 reports a 5.6 percentage point improvement on MobileWorld (12.0% vs 6.4% for Mixed-SFT) and a 3.2 point gain on OSWorld. However, the paper reports these as single-point estimates without any indication of variance, standard deviation, or the number of random seeds used. In reinforcement learning and agent benchmarks, performance can fluctuate significantly between seeds due to the stochastic nature of rollout generation and environment interaction. A gap of this magnitude could plausibly arise from a single lucky seed rather than a robust algorithmic improvement. To establish the claim that UI-MOPD is genuinely superior, the authors must report results averaged over at least 3-5 independent training runs with seeds, providing mean ± standard deviation.

Second, the attribution of the gain to the specific "multi-teacher" mechanism is not fully isolated. The paper claims the improvement comes from "platform-conditioned distillation" preventing behavioral mixing. However, the primary comparison in Table 2 is against "Mixed-SFT" and "Model Merge." It is possible that the improvement stems simply from the use of on-policy reinforcement learning (the DAPO/GRPO objective) rather than the specific multi-teacher routing. A critical control experiment is missing: a "Single-Teacher On-Policy Distillation" baseline where the student is trained with the same RL framework but distills from only one teacher (or a merged teacher) without platform-conditioned routing. Without this ablation, the reader cannot distinguish whether the benefit comes from the *multi-teacher* aspect or the *on-policy* aspect of the method.

Finally, there is a potential confusion in the interpretation of the teacher-student comparison in Section 4.3. The text states UI-MOPD "outperforms the 32B base model on MobileWorld," citing 12.0% vs 9.4%. However, Table 3 explicitly lists the "Mobile Teacher, 32B" achieving 16.2% on MobileWorld, which is higher than the student's 12.0%. The student underperforms the specialized teacher, which is expected, but the text's phrasing suggests a comparison against the 32B *base* (untrained) model or creates ambiguity about whether the student has surpassed the expert. Clarifying this comparison is essential to ensure the claim of "effective transfer" is not overstated.
