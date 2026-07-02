---
action_items:
- id: 201f31a87144
  severity: science
  text: The paper exhibits a high density of unexplained acronyms and specialized
    jargon that hinders accessibility for non-specialist readers. The most critical
    issue is the introduction of the term "LongPT" (Long-Context Continued Pre-Training)
    in the Abstract and Introduction without explicitly defining the acronym at its
    first occurrence. It is subsequently used as a standalone noun (e.g., "practical
    LongPT recipes"), which assumes a level of familiarity not guaranteed in a general
    audience. In Sect
artifact_hash: 27eba2e5ea40297ff1b355e2383ef9ee011ad854079e699d6346f41869d2df3c
artifact_path: projects/PROJ-575-training-long-context-vision-language-mo/paper/specs/001-paper/tasks.md
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-01T20:44:23.899665Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_jargon_police
score: 0.0
verdict: full_revision
---

The paper exhibits a high density of unexplained acronyms and specialized jargon that hinders accessibility for non-specialist readers. The most critical issue is the introduction of the term "LongPT" (Long-Context Continued Pre-Training) in the Abstract and Introduction without explicitly defining the acronym at its first occurrence. It is subsequently used as a standalone noun (e.g., "practical LongPT recipes"), which assumes a level of familiarity not guaranteed in a general audience.

In Section 3, the term "mRoPE" is used to describe the positional encoding scaling method. While standard within the specific Qwen architecture community, it is not a universal term in the broader vision-language model literature and requires a brief definition or expansion (e.g., "multimodal Rotary Positional Embeddings") upon first use. Similarly, Section 4.1 introduces "DPI" (dots per inch) without expansion, and Section 4.2 uses "SFT" (Supervised Fine-Tuning) without defining it first, despite the paper's focus on training recipes.

Furthermore, the Appendix (Section 7) relies heavily on framework-specific jargon such as "FSDP" (Fully Sharded Data Parallel) and "VeOmni" without providing their full names or a brief description of their function. This creates a barrier for readers attempting to reproduce the work who may not be familiar with these specific internal tools or standard deep learning acronyms. The phrase "agentic workflows" in the Abstract is also slightly jargon-heavy; "agent-based workflows" or "tasks performed by autonomous agents" would be more accessible.

To meet the standards of clarity, every acronym (LongPT, SFT, mRoPE, FSDP, DPI) must be spelled out at its first appearance in the text. Additionally, specialized terms like "agentic" should be simplified to ensure the paper remains accessible to a broader scientific audience beyond the immediate sub-field of long-context training.
