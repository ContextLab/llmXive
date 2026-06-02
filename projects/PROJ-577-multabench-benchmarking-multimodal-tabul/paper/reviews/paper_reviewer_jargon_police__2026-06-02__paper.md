---
action_items:
- id: c3f366d4439c
  severity: writing
  text: Define all acronyms (LoRA, MMTL, HPO, CI, VLMs, GBDTs, RAG) at first use in
    the main text, not just in citations or appendices.
- id: fe7900086952
  severity: writing
  text: Replace field-specific jargon with plain English where possible (e.g., 'SOTA'
    to 'state-of-the-art', 'learners' to 'models', 'scales' to 'sizes').
- id: 174feec7f7ce
  severity: writing
  text: Standardize terminology spelling (e.g., 'fine-tune' instead of 'finetune')
    to meet general publication style guides.
artifact_hash: 6787a87df841d43fd2785f288cbdae2d1c09b5ec14bf84bfd0cf81559d785c80
artifact_path: projects/PROJ-577-multabench-benchmarking-multimodal-tabul/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-02T11:20:56.759175Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_jargon_police
score: 0.0
verdict: minor_revision
---

The manuscript introduces MulTaBench, but the density of specialized terminology and undefined acronyms creates barriers for non-specialist readers. While field-standard terms like "Tabular Foundation Models (TFMs)" are defined upon first use, several critical acronyms appear without expansion. Specifically, "LoRA" (Section 1) is used before "Low-Rank Adaptation" is explained. Similarly, "MMTL" is introduced in Section 3 without explicitly spelling out "Multimodal Tabular Learning" in the immediate sentence, relying on context from the abstract. In the Appendix, "HPO" (Appendix C) appears without defining "Hyperparameter Optimization," and "CI" (Figure 1 caption) is used for "Confidence Interval" without prior expansion in the main text. "VLMs" (Section 1) also requires "Vision-Language Models" definition.

Beyond acronyms, word choice often privileges insider jargon over plain English. "SOTA" (Section 1) should be written as "state-of-the-art" for broader accessibility. The term "learners" (Section 3) is common in AutoML but "models" is more universally understood. "Encoder scales" (Section 5) is slightly ambiguous; "encoder sizes" or "parameter counts" would be clearer. Additionally, "GBDTs" (Section 1) should be introduced as "Gradient Boosted Decision Trees (GBDTs)" at first mention. "RAG" (Section 2) is used without defining "Retrieval-Augmented Generation."

These issues do not invalidate the science but reduce the paper's reach. Defining all acronyms at first use and simplifying vocabulary where possible will align the manuscript with best practices for inclusive scientific communication. The curation pipeline description also uses "finetune" (Section 1) which should be hyphenated as "fine-tune" for consistency with standard style guides. Addressing these points will ensure the benchmark's utility is communicated effectively to a wider audience beyond the immediate subfield.
