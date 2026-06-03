---
action_items:
- id: 585f9f54c36a
  severity: writing
  text: Strengthen the Introduction to explicitly contrast Parallel Box Decoding (PBD)
    against structure-agnostic Multi-Token Prediction (MTP) methods, clarifying why
    box-alignment is necessary for geometric coherence.
- id: c22c05a96b42
  severity: writing
  text: Define 'high-quality' grounding in the Abstract and Introduction using specific
    metrics (e.g., IoU thresholds, F1-mIoU) rather than qualitative claims to align
    with the title's promise.
- id: 4351b2492daf
  severity: writing
  text: Ensure the Supplementary Materials include the exact data mixing weights and
    hyperparameters for the Stage-3 and Stage-4 SFT to guarantee full reproducibility.
artifact_hash: fd5c6b9375343e0bf1127bc6f967de79045e8b07b55446fb41fe382f0df7e34c
artifact_path: projects/PROJ-636-locateanything-fast-and-high-quality-vis/paper/metadata.json
backend: dartmouth
feedback: Strong empirical results and novel PBD architecture warrant publication
  pending clarification of motivation and metric definitions.
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-03T13:37:20.071891Z'
reviewer_kind: llm
reviewer_name: paper_reviewer
score: 0.0
verdict: minor_revision
---

# Free-form review body

## Strengths
- **Novel Decoding Paradigm:** The proposed Parallel Box Decoding (PBD) is a well-motivated architectural change that directly addresses the latency bottleneck of token-by-token coordinate generation in VLM-based grounding.
- **Comprehensive Evaluation:** The paper evaluates across a wide range of benchmarks (COCO, LVIS, Dense200, VisDrone, GUI, OCR), demonstrating consistent SOTA performance in both accuracy and throughput.
- **Practical Inference Design:** The Hybrid Mode, which dynamically falls back to NTP for unreliable blocks, is a pragmatic engineering solution that balances the trade-off between speed and robustness effectively.
- **Large-Scale Data:** The curation of a 138M-query dataset (LocateAnything-Data) with a detailed data engine description adds significant value to the community.

## Concerns
- **Motivation Clarity:** As noted in prior reviews, the Introduction could better articulate why general MTP methods fail for this specific task. While the paper mentions "structure-agnostic" issues, a more concrete example or theoretical argument regarding the distribution mismatch would strengthen the claim.
- **Terminology Precision:** The title and Abstract use the term "High-Quality" without a rigorous definition. Given the quantitative nature of the work, this should be explicitly tied to the F1@IoU metrics reported in the tables.
- **Reproducibility:** While the Supplementary Materials are extensive, the exact data mixing ratios for the 138M queries (beyond the high-level percentages) would benefit from a detailed breakdown table to ensure the training recipe can be replicated.

## Recommendation
This paper presents a significant contribution to the field of vision-language grounding with a clear technical novelty (PBD) and strong empirical validation. The concerns raised are primarily related to framing and documentation clarity rather than fundamental scientific flaws. I recommend **minor_revision**. The authors should revise the Introduction to sharpen the motivation for PBD against existing MTP baselines and explicitly define the "high-quality" metric in the abstract. Once these clarifications are made, the manuscript will be publication-ready.
