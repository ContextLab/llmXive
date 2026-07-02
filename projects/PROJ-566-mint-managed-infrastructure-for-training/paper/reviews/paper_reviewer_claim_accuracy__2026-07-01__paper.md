---
action_items:
- id: 7c6860c0af2c
  severity: writing
  text: Abstract and Section 4.2 claim a 18.3x handoff reduction on a 4B model, but
    Table 1 (e1_handoff_paths) shows a 71.82s vs 0.036s materialization time (approx
    1995x) and a 55.7s vs 4.1s total cold first sample (approx 13.5x). The 18.3x figure
    does not match the provided data for either metric. Clarify the specific metric
    used for this claim or correct the number.
- id: af18f83f7b5b
  severity: writing
  text: The abstract claims a 2.85x handoff reduction on a 30B MoE model. Table 1
    shows 402.245s (Merge) vs 46.455s (Adapter) for materialization (approx 8.6x)
    and 156.074s vs 117.304s for cold first sample (approx 1.33x). The 2.85x figure
    is unsupported by the table data. Reconcile the claim with the evidence.
- id: e14aa200ba3b
  severity: writing
  text: Section 4.2 states a rank-1 LoRA is 'roughly 0.10% of the bf16 base-weight
    floor' and supports the abstract's 'less than 1%' claim. However, the text calculates
    7.9 MiB for rank-1 vs 8.0 GB base, which is 0.098%. While mathematically correct,
    the phrasing 'less than 1%' is technically true but potentially misleading given
    the order of magnitude difference (0.1% vs 1%). Ensure the distinction between
    'compact rank-1' and general rank settings is clear to avoid overgeneralization.
- id: f77424f4c6a6
  severity: writing
  text: Section 5 claims the Kimi K2 1T run uses a '64 H800 deployment'. However,
    Table 2 (model_coverage) lists the Kimi-K2-Thinking training profile as '128 GPUs'.
    The text in Section 5 also mentions '128 GPU' in the table notes. The '64 H800'
    claim in the text (Section 2, Figure 3 caption) contradicts the table data. Verify
    the correct GPU count for the Kimi K2 deployment.
- id: c9e33a457902
  severity: writing
  text: The abstract claims 'thousand-adapter active waves at cluster scale'. Section
    5 and Appendix Table 4 (app_fleet_model) describe a '2300-distinct-adapter active-wave
    assumption' for fleet sizing. The term 'thousand-adapter' is vague and does not
    align with the specific 2300 figure used in the capacity model. Use the precise
    number or clarify the range.
artifact_hash: 9b74dd1f4b8f2d4815ea056f5e26899cdd80d0bb7bac2914c7ef2512791b5d74
artifact_path: projects/PROJ-566-mint-managed-infrastructure-for-training/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-01T20:01:45.153871Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_claim_accuracy
score: 0.0
verdict: minor_revision
---

The paper makes several specific quantitative claims in the abstract and Section 4 regarding performance improvements (handoff speedups) that are not directly supported by the data presented in the corresponding tables.

Specifically, the abstract claims an **18.3x** reduction in handoff time for a 4B model and a **2.85x** reduction for a 30B MoE model. However, **Table 1 (e1_handoff_paths)** presents data that contradicts these figures:
- For the 4B model, the "Materialization or load" time drops from 71.820s to 0.036s (a ~1995x improvement), and the "Cold first sample" drops from 55.704s to 4.114s (a ~13.5x improvement). Neither matches 18.3x.
- For the 30B model, the "Materialization or load" time drops from 402.245s to 46.455s (an ~8.6x improvement), and the "Cold first sample" drops from 156.074s to 117.304s (a ~1.33x improvement). Neither matches 2.85x.

The authors must clarify which specific metric (e.g., a specific subset of the pipeline, a different experimental run, or a specific definition of "handoff") yields the 18.3x and 2.85x figures, or correct the numbers in the abstract to match the provided table data.

Additionally, there is a discrepancy regarding the Kimi K2 deployment size. The text in **Section 2** and the caption of **Figure 3** mention a "64 H800 deployment," while **Table 2 (model_coverage)** and the text in **Section 5** explicitly state a "128 GPU" profile for the Kimi-K2-Thinking training. This inconsistency needs resolution.

Finally, the claim of "thousand-adapter active waves" in the abstract is imprecise compared to the "2300-distinct-adapter active-wave assumption" detailed in **Appendix Table 4**. The abstract should reflect the specific number used in the capacity model or clarify the range.
