---
action_items:
- id: 9f25ac31ada1
  severity: writing
  text: The manuscript relies heavily on domain-specific acronyms and hardware jargon
    that are not defined at their first occurrence, creating barriers for non-specialist
    readers. In Section 1, the term "MoE" is used to describe the model architecture
    without defining it as "Mixture of Experts." Similarly, Section 2.1 introduces
    "GQA" (Grouped-Query Attention) and "KV heads" without expanding the "KV" acronym,
    assuming prior knowledge of Transformer internals. In the kernel design section
    (Section 5), t
artifact_hash: f00725508246b024cf4aa3c534e6f6afc166e2aa03bee30b44dd04e950f05991
artifact_path: projects/PROJ-701-minimax-sparse-attention/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T09:49:31.453207Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_jargon_police
score: 0.0
verdict: minor_revision
---

The manuscript relies heavily on domain-specific acronyms and hardware jargon that are not defined at their first occurrence, creating barriers for non-specialist readers. In Section 1, the term "MoE" is used to describe the model architecture without defining it as "Mixture of Experts." Similarly, Section 2.1 introduces "GQA" (Grouped-Query Attention) and "KV heads" without expanding the "KV" acronym, assuming prior knowledge of Transformer internals.

In the kernel design section (Section 5), the text becomes particularly dense with hardware-specific terminology. Section 5.2 mentions handling "hot tiles without atomics" without defining "atomics" as atomic memory operations, and later refers to "128x128 MMAs" without explaining that MMA stands for Matrix Multiply-Accumulate. Section 5.3 introduces "LSE computation" (Log-Sum-Exp) without expansion. While these terms are standard for systems researchers, the paper's claim of a "minimal, scalable" approach suggests it should be accessible to a broader ML audience. The authors should ensure every acronym is spelled out upon first use and consider replacing highly specific hardware jargon (like "MMA" or "atomics") with more descriptive plain English where possible to improve clarity.
