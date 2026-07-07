---
action_items:
- id: c253951a2f14
  severity: writing
  text: The paper presents a compelling theoretical argument for objective misalignment
    in LLM RL and proposes MIPU to address it. However, the empirical evidence supporting
    the central claims of performance improvement and stability is currently insufficient
    to rule out sample noise or lucky seeds. The primary concern lies in the lack
    of variance reporting. Table 1 presents headline accuracy numbers (e.g., 66.71%
    vs 65.66% for Qwen3-4B) derived from what appears to be single runs. In reinforcement
    lear
artifact_hash: 532a85457b6c71e1e8174b90594afc6d1be5ab1b35a438039d06e81d212f0a7d
artifact_path: projects/PROJ-994-the-mirage-of-optimizing-training-polici/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-07T03:26:38.314814Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The paper presents a compelling theoretical argument for objective misalignment in LLM RL and proposes MIPU to address it. However, the empirical evidence supporting the central claims of performance improvement and stability is currently insufficient to rule out sample noise or lucky seeds.

The primary concern lies in the lack of variance reporting. Table 1 presents headline accuracy numbers (e.g., 66.71% vs 65.66% for Qwen3-4B) derived from what appears to be single runs. In reinforcement learning, especially with small training sets (1,491 examples for Qwen3-4B) and high-mismatch settings, performance variance across seeds is often substantial. A 1.05% average gain is well within the plausible range of sampling noise for a single run. Without reporting results across multiple seeds (e.g., 3-5) with standard deviations or confidence intervals, the reader cannot distinguish a genuine algorithmic improvement from a lucky initialization or a specific random seed trajectory. The claim of "improved average reasoning performance" is statistically unsupported in its current form.

Similarly, the claim of "training stability" relies heavily on the visual inspection of a single training curve (Figure 1) and a binary "Stable" flag in Table 1. While the curve shows MIPU avoiding a sharp drop seen in baselines, this observation is anecdotal without statistical backing. Does the baseline *always* collapse, or did it just collapse in this specific run? To substantiate the stability claim, the authors should either report the variance of the final performance across seeds (showing MIPU has lower variance) or define a quantitative metric for stability (e.g., maximum performance drop during training) and show it is significantly better for MIPU across multiple runs.

Finally, the ablation study in Table 2 has a subtle confound in the "Step 2 only" condition. The text implies this variant uses the standard GRPO update as its proposal, meaning the "Step 2 only" result is a combination of a potentially poor proposal (GRPO) and the Step 2 filter. This makes it difficult to isolate the specific contribution of the Step 2 acceptance mechanism. A more rigorous ablation would compare the full MIPU against a variant that uses the *same* Step 1 proposal (TIS) but replaces the inference-gap-aware acceptance with a random or fixed-threshold acceptance rule. This would better isolate whether the gain comes from the *specific* inference-gap signal or simply from the act of rejecting updates more frequently.

Addressing these points by adding multi-seed runs and refining the ablation design is necessary to transform the current suggestive results into robust scientific evidence.
