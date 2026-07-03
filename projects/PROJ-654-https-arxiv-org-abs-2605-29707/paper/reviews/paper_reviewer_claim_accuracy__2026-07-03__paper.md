---
action_items:
- id: 9930f56eb707
  severity: writing
  text: In the Introduction (lines 105-108), the text claims EAGLE-3 achieves an acceptance
    length of 4.86 and speedup of 3.28x, while DFlash achieves 4.03 and 3.42x. However,
    Table 1 (main_result.tex) reports EAGLE-3 (16) on Qwen3-8B with an acceptance
    length of 3.27 and speedup of 2.21x, and DFlash with 6.59 and 5.21x. The values
    in the text do not match the primary results table, suggesting the text may be
    citing a different configuration or contains a factual error.
- id: 333d2f76683b
  severity: writing
  text: 'The Introduction (lines 128-130) states Domino improves average acceptance
    length by 16.6% and speedup by 12.3% over DFlash. Calculating from Table 1 (Qwen3-8B,
    T=0): Acceptance length increases from 6.06 to 7.17 (~18.3%), and speedup from
    4.66 to 5.49 (~17.8%). The specific percentages cited in the text do not align
    with the reported table data.'
- id: 20568f4c39e8
  severity: writing
  text: The Abstract claims 'up to 5.8x throughput speedup under SGLang serving'.
    Table 2 (high_concurrency.tex) shows the maximum speedup for Domino on Qwen3-8B
    (GSM8K) at concurrency 2 is 5.1x. The 5.8x figure is not supported by the provided
    table data, which lists a maximum of 5.1x for Qwen3-8B and 4.3x for Qwen3-4B.
artifact_hash: ac9b2293924c2f0c1f04178796bb698ee01d07baef5d80d5250c3c91d8a5b9a5
artifact_path: projects/PROJ-654-https-arxiv-org-abs-2605-29707/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T15:20:57.846299Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_claim_accuracy
score: 0.0
verdict: minor_revision
---

The review focuses on the alignment between factual claims in the text and the supporting evidence provided in the tables and figures. Several discrepancies were identified where the narrative text cites specific performance metrics that do not match the data presented in the primary results tables.

First, in the Introduction (lines 105-108), the authors describe a trade-off using specific numbers for EAGLE-3 and DFlash (EAGLE-3: 4.86 acceptance, 3.28x speedup; DFlash: 4.03 acceptance, 3.42x speedup). These figures are inconsistent with Table 1 (`latex/table/main_result.tex`), which reports significantly different values for the Qwen3-8B model under the same conditions (EAGLE-3: 3.27 acceptance, 2.21x speedup; DFlash: 6.59 acceptance, 5.21x speedup). It is unclear if the text refers to a different model size, a different benchmark subset, or if the numbers are simply erroneous. This mismatch undermines the credibility of the trade-off argument presented in the introduction.

Second, the Introduction (lines 128-130) quantifies the improvement of Domino over DFlash as a 16.6% increase in acceptance length and a 12.3% increase in speedup. A direct calculation from Table 1 (Qwen3-8B, T=0) shows the acceptance length rising from 6.06 to 7.17 (an 18.3% increase) and speedup from 4.66 to 5.49 (a 17.8% increase). The cited percentages are inaccurate relative to the provided data.

Third, the Abstract claims a throughput speedup of "up to 5.8x" under SGLang. However, Table 2 (`latex/table/high_concurrency.tex`), which details the SGLang results, shows the highest speedup for Domino on Qwen3-8B is 5.1x (at concurrency 2 on GSM8K). The 5.8x figure is not present in the provided data tables.

These issues are classified as writing errors because they involve incorrect reporting of the paper's own experimental results. The authors must reconcile the text with the tables, either by correcting the numbers in the text to match the tables or by clarifying the specific conditions under which the text's numbers were derived.
