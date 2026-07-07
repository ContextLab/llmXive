---
action_items:
- id: 567fe7c9554f
  severity: writing
  text: Section 3.1 claims 3.9B samples/6.0T tokens, but the 83% token share for image-caption
    pairs isn't verified by the text breakdown. Please add a table or sentence confirming
    the 3.9B/6.0T totals sum correctly with the component counts to support the 83%
    claim.
- id: a10eadff3bae
  severity: writing
  text: Section 4.1 states 'English data carries almost all signal (0.6pp drop if
    removed)' based on Table 2 (All 49.1 vs Eng-only 48.5). However, the text also
    says 'Non-English tail alone is insufficient (-3.0pp)'. Clarify that the 0.6pp
    drop refers to removing non-English data, not English, to match the table comparison
    and avoid confusion.
- id: ccc5d125a95b
  severity: writing
  text: Section 5.1 claims 'only 0.29% of all training samples are removed' globally
    despite high rates in specific datasets (e.g., InfoVQA 100%). Confirm this 0.29%
    is the global average across the entire 3.9B pool, not just the subset in Figure
    3, to validate the 'cheap' decontamination claim.
- id: 98d42dbe646f
  severity: science
  text: Section 6.1 states the 'Instruction-heavy mix is the worst at 1Bx6.25B', but
    Figure 4 shows the red line (Instruction-heavy) as the highest (best) at that
    point. Verify the data in Figure 4 and correct the text or figure labels to resolve
    this direct contradiction.
- id: 6cbf98f77ac4
  severity: writing
  text: Section 6.2 claims Pearson r=0.99 between pre- and post-SFT scores for 27
    checkpoints. Clarify if this correlation is calculated on the 27 checkpoint averages
    (not 54 runs) and ensure the figure caption explicitly states the number of points
    used.
artifact_hash: d4a22931e6b886440cd41104bb215d7473154b2e0677ff1cb31fe0010e81d224
artifact_path: projects/PROJ-1001-datacomp-vlm-improved-open-datasets-for/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-07T10:40:50.843266Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_claim_accuracy
score: 0.0
verdict: minor_revision
---

The paper presents a comprehensive study on data curation for Vision-Language Models, with a strong focus on decontamination and data mixing. The claims regarding the decontamination pipeline (Section 5) are well-supported by the detailed methodology and the removal rate statistics provided in the text and figures. The claim that "filtering rarely helps" (Section 6) is supported by the extensive ablation studies in the appendices.

However, there are a few specific instances where the textual claims appear to contradict the visual data or require clarification to ensure the reader can trust the numbers:

1. Section 6.1 (Data Mixing): The text states, "the Instruction-heavy mix is the worst at 1Bx6.25B". However, visual inspection of Figure 4 (mixing-panels) for the 1B model at 6.25B tokens suggests the red line (Instruction-heavy) is actually the highest (best) or at least not the worst compared to the other lines. This is a direct contradiction between the text and the figure. The authors must verify the data plotted in Figure 4 and correct the text to accurately reflect the results.

2. Section 3.1 (Pool Composition): The text claims the pool has 3.9B samples and 6.0T tokens. The caption of Figure 1 states image-caption pairs are 83% of tokens. While the text lists the number of datasets, it does not explicitly break down the 3.9B/6.0T totals by data type to allow the reader to verify the 83% claim. A brief breakdown or a reference to a table with these specific totals would strengthen the claim.

3. Section 5.1 (Decontamination Rates): The text states that "only 0.29% of all training samples are removed" at the pool level, despite high removal rates in specific datasets like InfoVQA (100%) and ScienceQA (66.4%). Given the total pool size (3.9B), this 0.29% figure implies a very small absolute number of removed samples. The text should explicitly confirm that this 0.29% is the global average across the *entire* 3.9B sample pool to avoid confusion about the impact of the decontamination.

4. Section 6.2 (SFT Correlation): The claim of a Pearson correlation of 0.99 is extremely high. The text mentions 27 checkpoints and 54 SFT runs. It is crucial to clarify that the correlation is calculated on the 27 pretraining scores vs. the 27 corresponding post-SFT scores (likely averaged), not on the 54 individual runs. The figure caption should also explicitly state the number of points used for the correlation calculation.

These issues are primarily about ensuring the text and figures are perfectly aligned and that the reader can verify the specific numbers. They do not invalidate the core findings but require correction for accuracy.
