---
action_items:
- id: 886e5382a876
  severity: science
  text: 'Reconcile dataset statistics: Abstract/Section 4 claim 2.6M items/302k hours,
    but Figure 3(c) table lists 2.34M items/66.7K hours.'
- id: 02df6a80c33c
  severity: science
  text: 'Correct latency claim: Section 3.4 states 4.5x reduction, but Table 5.4 shows
    2.12x (831ms vs 392ms).'
- id: 46c960d12aa9
  severity: writing
  text: 'Fix WER regression number: Section 1 claims 3-point regression, but Table
    ''tab:asr'' and Section 5.2 show 0.30 (3.17 vs 2.87).'
- id: 9dc995aeb595
  severity: writing
  text: 'Unify model naming: Title/Tables use ''Audio-Interaction'', but Section 4/5
    text uses ''Mini-Omni 3''.'
artifact_hash: d722b827ffcc42ef33cad3308518a181a01c5d135cbbac51efaf0289e64033d0
artifact_path: projects/PROJ-666-https-arxiv-org-abs-2606-05121/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-12T10:51:19.250117Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_claim_accuracy
score: 0.0
verdict: full_revision
---

This review identifies critical internal inconsistencies in factual claims and quantitative results that must be resolved before publication.

First, the **dataset statistics are contradictory**. The Abstract, Introduction, and Section 4 consistently state that `StreamAudio-2M` comprises **2.6M items** totaling **302k hours**. However, the table within **Figure 3(c)** explicitly reports **2.34M items** and **66.7K hours**. A discrepancy of this magnitude (e.g., 302k vs 66.7k hours) suggests a potential error in data counting, unit conversion, or figure labeling that invalidates the resource claim.

Second, **performance metrics in the text do not match the tables**. Section 1 Introduction claims a "**3-point WER regression**" on LibriSpeech. However, Table `tab:asr` shows the model's WER is 3.17 versus the base 2.87, a difference of **0.30 points**, not 3. Section 5.2 correctly notes "+0.30", indicating the Introduction text is erroneous. Similarly, Section 3.4 claims the FIFO inference scheme cuts first-frame latency by **4.5x**, but Table `tab:fifo_inference` in Section 5.4 demonstrates a reduction from 831ms to 392ms, which is only **2.12x**.

Third, there is a **naming inconsistency**. The model is titled and referred to as `Audio-Interaction` throughout the Abstract, Introduction, and Tables. However, the text in **Section 4 (Main Results)** and **Section 5 (Ablation)** repeatedly refers to the model as "**Mini-Omni 3**". This suggests copy-paste artifacts from a previous work that were not fully updated, casting doubt on the originality and accuracy of the reported results.

Finally, the **benchmark comparison** in the Introduction ("matches state-of-the-art... 58.15 vs 57.81") compares the proposed 3B model against a 3B baseline, while Table 1 shows 7B baselines (e.g., Qwen2.5-Omni 7B at 65.60) outperforming the proposed model. While not a factual error, the claim requires qualification to avoid misleading readers about the model's scale relative to SOTA.

Please align all numerical claims between the text and tables, correct the dataset statistics, and ensure consistent model naming throughout the manuscript.
