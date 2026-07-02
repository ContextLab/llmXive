---
action_items:
- id: dfca5df5c684
  severity: writing
  text: The manuscript relies heavily on field-specific acronyms and jargon that are
    not consistently defined at their first point of use, creating barriers for non-specialist
    readers. First, the Abstract introduces "MLLMs" without the full expansion "Multimodal
    Large Language Models," which only appears in the Introduction. Similarly, "SOTA"
    is used in the Abstract without being spelled out as "state-of-the-art." The term
    "alignment tax" is used in the Abstract and Section 3.3 without a plain-language
artifact_hash: e83058c54d1a49095166f0ef2ff7177a4db8d52f3626563ad7ae59fa949315e9
artifact_path: projects/PROJ-610-https-arxiv-org-abs-2605-16403/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T19:17:25.853878Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_jargon_police
score: 0.0
verdict: minor_revision
---

The manuscript relies heavily on field-specific acronyms and jargon that are not consistently defined at their first point of use, creating barriers for non-specialist readers. 

First, the Abstract introduces "MLLMs" without the full expansion "Multimodal Large Language Models," which only appears in the Introduction. Similarly, "SOTA" is used in the Abstract without being spelled out as "state-of-the-art." The term "alignment tax" is used in the Abstract and Section 3.3 without a plain-language definition, assuming the reader knows this specific phenomenon of performance degradation.

In the methodology and experiments, acronyms like "DPO" (Direct Preference Optimization), "SFT" (Supervised Fine-Tuning), "CTP" (Counterfactual Temporal Preferences), and "FV-D" (FineVideo-derived general video data) are introduced without immediate expansion. While "DPO" and "SFT" are common in the field, their first usage in the main text (Section 3.3) lacks the full name, and "CTP" and "FV-D" are particularly opaque without definition. The custom operators \shift, \mute, and \swap are defined in the LaTeX preamble but are used as conceptual terms in the Abstract and Introduction before their specific meanings (temporal synchronization, sound existence, consistency) are explicitly linked to the names in the text.

Finally, the Appendix uses technical shorthand like "LoRA" (Low-Rank Adaptation), "bf16" (bfloat16), and "H200" (NVIDIA H200 GPUs) without expansion. To improve accessibility, every acronym should be spelled out at first use, and jargon like "alignment tax" should be briefly explained in plain English.
