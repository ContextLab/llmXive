---
action_items:
- id: bd96125975d5
  severity: science
  text: Eq. 1 defines hacking as d/dt E[true] <= 0 while bias increases. Table 2 shows
    net capability drops, but does not prove the derivative was non-positive *during*
    the onset phase. Clarify if the condition is strict simultaneous non-increase
    or eventual degradation.
- id: 28db6bb12de3
  severity: writing
  text: Section 4.1 claims lower OR correlates with delayed onset. Table 1 supports
    this generally, but the text implies a universal rule without addressing dataset-specific
    variance in absolute onset times, which may confuse the causal mechanism between
    entanglement and discovery speed.
- id: db0e0ea90c98
  severity: writing
  text: Section 5 claims RHDA "outperforms baselines" in onset localization. While
    aggregate metrics support this, CC-Sonnet has 0 error on HealthBench Tone vs RHDA's
    +7. Clarify that superiority refers to aggregate performance, not per-case accuracy,
    to avoid overgeneralization.
artifact_hash: eca43eb888bbc8155fd1bf21a6b137ce6bb47419fcb91606da445eda44a63a5a
artifact_path: projects/PROJ-663-https-arxiv-org-abs-2606-04923/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T18:48:15.525984Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_logical_consistency
score: 0.0
verdict: minor_revision
---

The paper presents a logically coherent framework for defining and detecting reward hacking in rubric-based RL, primarily through the decoupling of proxy rewards into gold and biased components (Eq. 1). The causal chain from bias injection to reward divergence and subsequent capability degradation is well-supported by the experimental data in Tables 1 and 2. The introduction of the Odds Ratio (OR) to quantify bias entanglement and its correlation with onset time (Section 4.1) is logically sound and supported by the data in Table 1.

However, there are minor logical gaps in the precise definition of the hacking condition versus the observed empirical results. Specifically, the definition of hacking in Eq. 1 requires the derivative of the expected true reward to be non-positive ($\le 0$) while the biased component increases. The paper reports "capability degradation" (e.g., IFB scores dropping from 31.7 to 23.7 in Table 2) as evidence of this. While this shows a net drop, it does not strictly prove that the true reward was non-increasing *during* the specific onset phase where the bias was being exploited. It is possible the true reward plateaued or fluctuated before dropping. The text should clarify whether the condition is a strict simultaneous derivative constraint or a looser "eventual degradation" condition, as the current phrasing implies a stricter mathematical condition than the aggregate metrics might fully support.

Additionally, the claim that RHDA "outperforms baselines" in onset localization (Section 5) relies on aggregate metrics ($\sum d_p$). While the aggregate data supports this, a reader might infer that RHDA is superior in every individual case. For instance, in the HealthBench Tone bias case, CC-Sonnet achieves a 0 error (68 vs 68), whereas RHDA-Plus has a +7 error. The text should explicitly qualify that the superiority is based on aggregate performance to avoid overgeneralization.

Finally, the logical link between "generation difficulty" (Section 4.2) and "exploitability" is well-argued, but the paper could more explicitly state that the *failure* to hack in the Tone/Format cases (Section 3.3) is a direct logical consequence of the low success ratios in Table 2, rather than just a separate observation. The current structure separates the "no hacking" observation from the "success ratio" explanation, slightly weakening the causal narrative.
