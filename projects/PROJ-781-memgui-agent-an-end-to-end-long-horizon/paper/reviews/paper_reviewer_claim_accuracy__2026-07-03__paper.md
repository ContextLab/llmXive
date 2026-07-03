---
action_items:
- id: d0224f45ec55
  severity: science
  text: Section 1 claims GUI-Owl-1.5-8B scores 71.6% on AndroidWorld but cites no
    source. Verify this baseline or cite the specific evaluation.
- id: 328d76042244
  severity: writing
  text: Section 3 mentions '75.7% reasonable steps' without defining the metric or
    linking it to Figure 2. Clarify the definition and source.
- id: afe27c8fef81
  severity: writing
  text: Section 4.1 compares against 'same backbone' but does not explicitly specify
    the 'Thinking' variant, risking confusion with the 'Instruct' row in Table 1.
artifact_hash: 7ba9201f0f49d9384a35f3eca07d4fd8d448c0da222a8a4e9472044b7e857c18
artifact_path: projects/PROJ-781-memgui-agent-an-end-to-end-long-horizon/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T18:52:18.444672Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_claim_accuracy
score: 0.0
verdict: minor_revision
---

The paper presents a compelling narrative on long-horizon mobile GUI agents, but several factual claims require tighter alignment with evidence and citations.

In the Introduction, the claim that "GUI-Owl-1.5-8B" achieves 71.6% on AndroidWorld is unsupported by the provided text or citations. While the 11.7% figure on MemGUI-Bench is present in Table 1, the 71.6% baseline lacks a direct citation (e.g., to `xu2026mobile` or `rawles2025androidworld`). Without this citation, the magnitude of the "dramatic drop" is an unverified assertion. The authors must either cite the specific source for the AndroidWorld score or clarify if this is a new evaluation performed by the authors.

In Section 3, the dataset construction description mentions a filtering step resulting in "75.7% reasonable steps." This specific percentage is not explicitly defined or cross-referenced with the statistics in Figure 2 (dataset-stats). The figure details folding granularity (23.8%) and trajectory containment (88.7%), but the "reasonable steps" metric appears isolated. The text should clarify whether this 75.7% refers to the ratio of steps retained after filtering or the quality of the initial generation, and ensure this metric is visually represented or explicitly defined in the figure caption.

Finally, in Section 4.1, the comparison of MemGUI-Agent-235B against the "same backbone" cites improvements of +13.3 Pass@1 and +16.8 IRR. While the arithmetic holds against the "Qwen3-VL-235B-Thinking" row in Table 1, the text does not explicitly distinguish this from the "Qwen3-VL-235B-Instruct" variant listed immediately above it. Given the significant performance gap between the "Thinking" and "Instruct" variants in the table, the claim of improvement over the "same backbone" is technically accurate but potentially misleading without explicitly specifying that the baseline is the "Thinking" variant. Precision here is critical to avoid overstating the method's contribution over the base model's inherent capabilities.
