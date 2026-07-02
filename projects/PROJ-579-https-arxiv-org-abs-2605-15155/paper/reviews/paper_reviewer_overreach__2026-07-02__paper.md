---
action_items:
- id: 5cf0d6369a65
  severity: writing
  text: 'The claim ''consistently outperforms hybrid baselines across all model scales''
    overstates the margin. Table 1 shows SDAR often ties or leads by small margins
    (e.g., Qwen2.5-7B Search-QA: 49.0 vs 47.0). Temper ''substantial'' to ''consistent''
    when comparing to hybrids, reserving ''substantial'' for the GRPO baseline comparison.'
- id: f0407f2fc094
  severity: science
  text: Attributing Random Retrieval gains 'primarily' to gating is an overreach.
    Random skills may still provide regularization or generic context. Clarify that
    the method is robust to retrieval quality, rather than claiming the gains stem
    solely from the gating mechanism without a no-context control.
- id: e269b73877e0
  severity: writing
  text: The argument that Reverse KL is the key design choice aligning with 'weak
    teacher signals' overreaches. The gating mechanism already handles negative gaps;
    the divergence choice appears secondary. Tone down the claim that Reverse KL 'perfectly
    aligns' with the rationale, acknowledging the gating is the primary driver.
artifact_hash: a2fe5096ad1b93f50db064c40f59b84672b255d5a406d9c082d97d449a5f037d
artifact_path: projects/PROJ-579-https-arxiv-org-abs-2605-15155/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T01:52:31.813178Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: minor_revision
---

The paper presents a compelling method for stabilizing On-Policy Self-Distillation (OPSD) in multi-turn agents via a token-level sigmoid gate. However, several claims in the abstract and discussion slightly overreach the empirical evidence provided.

First, the abstract states that the method "consistently outperforms hybrid RL–OPSD baselines across all model scales" and achieves "substantial improvements." While Table 1 confirms that SDAR generally outperforms baselines like GRPO+OPSD, the margins are often marginal rather than substantial when compared to these specific hybrids. For instance, on Qwen2.5-7B for Search-QA, SDAR achieves 49.0% versus 47.0% for GRPO+OPSD. The term "substantial" is accurate when comparing SDAR to vanilla GRPO (e.g., +9.4% on ALFWorld), but applying it to the comparison with hybrid baselines risks overstating the magnitude of the improvement. The claim of "consistent" outperformance is technically supported, but the phrasing implies a more dominant advantage than the data suggests in several settings.

Second, the robustness analysis claims that the performance uplift "stems primarily from gated distillation rather than retrieval fidelity" because even Random Retrieval yields gains. While the method is clearly robust, the conclusion that the gains are *primarily* due to the gating mechanism is not fully isolated. The "Random Retrieval" condition still introduces an auxiliary signal (albeit noisy), which could act as a regularizer or provide generic context. Without a control condition where the auxiliary loss is applied with no context or a null context, it is difficult to rule out that the mere presence of the auxiliary term contributes to the gain. The claim should be tempered to state that the method is robust to retrieval quality, rather than attributing the gains solely to the gating logic.

Finally, the discussion on the choice of Reverse KL divergence over Forward KL or JSD overstates its theoretical necessity. The paper argues that Reverse KL is "inherently mode-seeking" and thus essential for handling "weak teacher signals." However, the gating mechanism already attenuates negative teacher signals, which is the primary defense against weak teachers. The ablation study (Figure 4) shows Reverse KL performs best, but the difference is not explained as a critical dependency. The claim that this choice "aligns perfectly" with the design rationale implies a stronger theoretical link than the empirical evidence supports, as the gating mechanism is likely the dominant factor in stability.

These issues are primarily matters of phrasing and attribution. The core contribution—the gated distillation mechanism—is well-supported, but the surrounding claims should be refined to more accurately reflect the nuanced reality of the results.
