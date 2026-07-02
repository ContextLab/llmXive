---
action_items:
- id: c79cfaa45890
  severity: science
  text: 'The paper exhibits significant overreach in its comparative claims and efficiency
    metrics, particularly regarding latency and the superiority of the proposed method
    over existing baselines. First, the Abstract and Conclusion claim that the method
    reduces "first-frame latency by 50%." This is directly contradicted by the footnote
    in Table 1 (tab:performance-comparison), which states: "Because we adopt the ASD
    trick... the first-frame latency for 1-step, 2-step, and 4-step generation is
    identical.'
artifact_hash: bc6ea3b7abb50e6d2d0c61521fe88f76d18733e7f3e4d74c5eba9d5fe9acb8e6
artifact_path: projects/PROJ-580-https-arxiv-org-abs-2605-15141/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-01T21:02:51.839579Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: full_revision
---

The paper exhibits significant overreach in its comparative claims and efficiency metrics, particularly regarding latency and the superiority of the proposed method over existing baselines.

First, the Abstract and Conclusion claim that the method reduces "first-frame latency by 50%." This is directly contradicted by the footnote in Table 1 (`tab:performance-comparison`), which states: "Because we adopt the ASD trick... the first-frame latency for 1-step, 2-step, and 4-step generation is identical." The latency reduction applies only to the *subsequent* frames in the autoregressive rollout, not the initial frame. In an interactive setting, the first-frame latency is the critical metric for user perception. Claiming a 50% reduction in "first-frame latency" is factually incorrect based on the paper's own experimental setup and misleads the reader about the real-time capabilities.

Second, the claim that Causal Forcing++ "surpasses the SOTA 4-step chunk-wise Causal Forcing" (Abstract) is an overgeneralization. Table 1 shows that while the 2-step frame-wise model achieves a slightly higher Total score (84.14 vs 84.04), it underperforms the 4-step Causal Forcing baseline in Dynamic Degree (64 vs 68) and Semantic score (81.13 vs 81.84). The paper frames the result as a blanket "surpassing" without acknowledging that the 4-step chunk-wise baseline still outperforms in specific, critical dimensions like dynamics and semantic alignment. The comparison conflates architectural changes (frame-wise vs. chunk-wise) with methodological improvements, making it difficult to attribute the gains solely to Causal Forcing++.

Third, the assertion that causal CD "surpasses" causal ODE initialization (Abstract, Sec 3.2) is not uniformly supported. In the 4-step ablation (Table 1), causal ODE achieves a higher Dynamic Degree (75) than causal CD (71). The paper selectively highlights metrics where CD wins (Total, Quality) while downplaying where ODE wins, presenting a skewed view of the trade-off. The claim of "surpassing" should be qualified to reflect that CD is a more *efficient* alternative that matches or exceeds ODE in *most* but not *all* metrics.

Finally, the claim of "no extra storage" (Abstract) is technically accurate regarding the *trajectories* but omits the storage requirements for the AR teacher model itself, which is a prerequisite for the method. While less severe, the phrasing creates an impression of zero-overhead that ignores the full pipeline's resource footprint.

These issues require a revision of the abstract and conclusion to accurately reflect the specific conditions of the latency reduction and to provide a more balanced comparison of the performance metrics.
