---
action_items:
- id: 668a23c8ae7a
  severity: writing
  text: The claim of '10% of optimization steps' (Abstract) conflates update count
    with compute. Since d-OPSD uses pass@8 sampling per step (Sec 3.3), total FLOPs
    may match RLVR. Clarify that efficiency is in updates, not total compute.
- id: 0706aee8b1fd
  severity: writing
  text: Describing AR-style OPSD as 'fundamentally conflicting' (Abstract) overstates
    the case. Table 4 shows it is less effective, not impossible. Soften to 'suboptimal'
    to avoid implying theoretical impossibility.
- id: 66b913a252f9
  severity: writing
  text: The 'first OPSD for dLLMs' claim (Abstract) relies on distinguishing on-policy
    vs. off-policy data sources. Explicitly define this distinction early to prevent
    ambiguity regarding prior self-distillation attempts in diffusion models.
artifact_hash: 5c8da21032033f700374cf269bb9ef61b58d8799f1e6049fc84e38c052b8b257
artifact_path: projects/PROJ-732-learning-from-the-self-future-on-policy/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T04:40:29.164167Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: minor_revision
---

The paper presents a compelling adaptation of On-Policy Self-Distillation (OPSD) for Diffusion Large Language Models (dLLMs), introducing a novel "self-future" conditioning mechanism. However, the manuscript occasionally overreaches in its claims regarding efficiency and the exclusivity of its approach.

First, the Abstract and Section 4.2 claim that d-OPSD requires "only around 10% of the optimization steps" compared to RLVR. While Table 3 supports this regarding the number of gradient updates, the text explicitly notes in Section 3.3 and 4.2 that d-OPSD employs a pass@k sampling strategy (k=8) to ensure correct trajectories, which shares the "same computation overhead as RLVR (group k rollouts) for each training step." Consequently, the total computational cost (FLOPs) or wall-clock time may not be 10% of the baseline, even if the number of updates is. The claim of "superior sample efficiency" is technically correct in terms of updates but risks misleading readers into assuming a 10x reduction in total compute. The text should clarify that the efficiency gain is specific to the number of optimization steps, not necessarily the total computational budget.

Second, the Introduction and Abstract characterize existing OPSD methods as "inherently autoregressive-centric" and "fundamentally conflicting" with dLLMs. This language is too absolute. The paper demonstrates that the proposed suffix-conditioning approach outperforms an AR-style prefix-conditioning baseline (Table 4), but it does not prove that the AR-style approach is theoretically impossible or universally ineffective for dLLMs. The conflict is empirical and performance-based, not fundamental. The authors should soften this to state that the AR-style approach is "suboptimal" or "less effective" rather than "fundamentally conflicting," which implies a theoretical impossibility that is not fully substantiated.

Finally, the claim of being the "first OPSD framework tailored for dLLMs" relies heavily on the distinction between using self-generated trajectories (on-policy) versus static ground-truth data (off-policy, as in d3LLM). While this distinction is valid, the manuscript would benefit from a more explicit definition of "on-policy" in the context of self-distillation early on to ensure the "first" claim is not misinterpreted as ignoring all prior self-distillation work in diffusion models. The current phrasing is slightly ambiguous regarding whether previous works attempted on-policy updates with different conditioning strategies.
