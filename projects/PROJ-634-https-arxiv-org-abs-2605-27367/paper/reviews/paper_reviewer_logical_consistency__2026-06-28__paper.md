---
action_items:
- id: ac2cf3de7126
  severity: science
  text: Clarify model naming consistency (VGGT vs VGGT-Long vs VGGT-Omega) across
    tables to support the 'Overall Ranking' claim.
- id: 4df0641b9841
  severity: science
  text: Align baseline model name in Introduction ('DA3-Giant') with tables ('DA3-Streaming')
    to validate performance gain claims.
- id: 780f6dfccc47
  severity: science
  text: Provide ablation or clarification to support 'Data quality outweighs volume'
    claim, isolating architecture from data effects.
artifact_hash: 306c5e78aff3c136de96c4c6956084c3af89239f10c2fba4682734d1809d3475
artifact_path: projects/PROJ-634-https-arxiv-org-abs-2605-27367/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-28T10:23:20.361815Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_logical_consistency
score: 0.0
verdict: minor_revision
---

The paper presents a coherent benchmark framework, but several logical links between evidence and conclusions require clarification to ensure rigorous support.

1. **Model Naming Consistency:** Tables `tab:main_leaderboard_filtered` (e004), `tab:sub_sparse` (e005), and `tab:sub_medium` (e004) use varying names for similar models (e.g., "VGGT", "VGGT-Long", "VGGT-Omega"). Specifically, `tab:main_leaderboard_filtered` lists "VGGT" (1256.54M params) while `tab:sub_sparse` lists "VGGT-Omega" (1143.81M params). Without explicit mapping, the "Overall Ranking" claim (Introduction) lacks rigorous support, as it is unclear if these are distinct variants or the same model under different names. This ambiguity weakens the logical chain connecting specific model performance to the general conclusion that "No single model dominates."

2. **Baseline Definition:** The Introduction claims Depth-Anything-Next achieves gains "over DA3-Giant". However, Tables `tab:sub_sparse` and `tab:sub_medium` list the baseline as "DA3-Streaming" (1355.67M params). Appendix `appendix:dan` states initialization from "da3-giant-1.1". If "DA3-Streaming" and "DA3-Giant" differ in architecture or training, the causal claim of improvement is not strictly supported by the provided tables. The logic requires the baseline to be identical across text and data to validate the percentage gains.

3. **Causal Attribution:** The claim "Data quality outweighs volume" (Introduction) relies on Fig `geobench_training_coverage`. However, the comparison mixes models with different architectures (e.g., DA3 vs DUSt3R). Without an ablation isolating data quality from architectural differences, the conclusion that data quality *alone* outweighs volume is not fully logically derived from the premises. The observed performance gap could be attributed to the backbone architecture rather than data curation alone.

These issues are fixable with text clarifications and consistent labeling, ensuring the conclusions follow directly from the presented evidence.
