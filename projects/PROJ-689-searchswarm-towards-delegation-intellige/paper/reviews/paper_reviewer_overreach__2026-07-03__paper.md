---
action_items:
- id: 8936a8b272c0
  severity: science
  text: The claim that SearchSwarm 'exceeds GPT-5.2-Thinking' (Section 3.2) is an
    overreach. Table 1 shows SearchSwarm (68.1) only exceeds GPT-5.2-Thinking (65.8)
    on BrowseComp, but GPT-5.2-Thinking scores 76.1 on BrowseComp-ZH, where SearchSwarm
    scores 73.3. The text implies a general superiority that the data does not support
    across all metrics.
- id: 38c7d19b0e2c
  severity: writing
  text: 'The statement that SearchSwarm ''remains competitive with models over 10x
    larger'' (Figure 1 caption) is an overgeneralization. While it beats GPT-5.2-Thinking
    on one metric, it trails significantly on others (e.g., GAIA: 82.5 vs. 76.4 for
    GPT-5, but GPT-5 is not 10x larger; the comparison to 10x larger models like DeepSeek
    V3.2 is mixed). The claim needs qualification to reflect specific benchmark performance
    rather than a blanket statement.'
- id: 74e371b38e28
  severity: science
  text: The conclusion states 'Delegation patterns generalize to single-agent and
    open-ended tasks' (Section 6). However, Section 3.5 shows a significant performance
    drop in the single-agent setting (52.0 vs 68.1 on BrowseComp). While it improves
    over the base model, claiming 'generalization' without acknowledging the substantial
    performance degradation in the absence of subagents overstates the robustness
    of the learned behavior.
artifact_hash: 23164a835e9fc14f10b36f04bd2aeba4213e5a3b759192c46a449dbfe25b61f3
artifact_path: projects/PROJ-689-searchswarm-towards-delegation-intellige/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T17:13:30.585546Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: minor_revision
---

The paper presents a compelling architecture for delegation intelligence, but several claims overreach the empirical evidence provided in the results tables and ablation studies.

First, the assertion in Section 3.2 that the model "exceeds GPT-5.2-Thinking" is misleading. While SearchSwarm achieves 68.1 on BrowseComp compared to GPT-5.2-Thinking's 65.8, the reverse is true on BrowseComp-ZH (73.3 vs. 76.1). The text presents this as a general victory, ignoring the metric where the larger model outperforms the proposed method. This selective framing exaggerates the model's relative standing against frontier closed-source systems.

Second, the caption for Figure 1 claims the model "remains competitive with models over 10x larger." This is an overgeneralization. While SearchSwarm outperforms GPT-5 on BrowseComp, it lags behind GPT-5 on BrowseComp-ZH and GAIA (76.4 vs. 82.5 is a win, but GPT-5 is not 10x larger in the same parameter count sense as the 671B DeepSeek V3.2). The comparison to DeepSeek V3.2 (671B) shows SearchSwarm trailing on BrowseComp-ZH (73.3 vs. 65.0 is a win, but DeepSeek V3.2 is 67.6 vs 68.1 on BrowseComp). The claim of being "competitive" with models 10x larger is only partially supported and requires nuance regarding which specific benchmarks and models are being compared.

Finally, the conclusion states that "Delegation patterns generalize to single-agent... tasks." Section 3.5 demonstrates that while the model improves over the base in a single-agent setting (52.0 vs 43.5), it suffers a massive performance drop compared to its multi-agent configuration (68.1). Describing this as "generalization" without qualifying the significant loss in efficacy when the delegation mechanism is disabled overstates the transferability of the learned skills. The model appears to rely heavily on the multi-agent architecture rather than having internalized a robust single-agent reasoning capability.
