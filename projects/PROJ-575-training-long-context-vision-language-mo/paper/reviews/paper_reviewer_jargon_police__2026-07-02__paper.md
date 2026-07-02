---
action_items:
- id: 68516ef90f1d
  severity: science
  text: The manuscript relies heavily on domain-specific acronyms and custom shorthand
    that hinder accessibility for a broader audience. In the Abstract and Introduction,
    the term "LVLM" is used repeatedly without being spelled out as "large vision-language
    model" at the very first instance. Similarly, "LongPT" is introduced as a concept
    but the acronym is not explicitly defined until later or assumed, which breaks
    the flow for non-specialist readers. In Section 3, technical terms like "mRoPE,"
    "FSDP,"
artifact_hash: 27eba2e5ea40297ff1b355e2383ef9ee011ad854079e699d6346f41869d2df3c
artifact_path: projects/PROJ-575-training-long-context-vision-language-mo/paper/specs/001-paper/tasks.md
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T01:46:37.980074Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_jargon_police
score: 0.0
verdict: full_revision
---

The manuscript relies heavily on domain-specific acronyms and custom shorthand that hinder accessibility for a broader audience. In the Abstract and Introduction, the term "LVLM" is used repeatedly without being spelled out as "large vision-language model" at the very first instance. Similarly, "LongPT" is introduced as a concept but the acronym is not explicitly defined until later or assumed, which breaks the flow for non-specialist readers.

In Section 3, technical terms like "mRoPE," "FSDP," and the framework name "VeOmni" appear without definition. While these are standard in specific sub-fields, a general paper should define them upon first use. Furthermore, the paper introduces custom LaTeX macros (e.g., `\extractsingle`, `\extractmulti`) that render as code-like text in the final PDF. These should be replaced with plain English descriptions in the narrative text to avoid visual clutter and confusion.

Section 5 introduces the term "pool-native" to describe a data distribution. While the context explains it, the term itself is jargon. A more descriptive phrase like "naturally sampled distribution" would be clearer. Finally, "SFT" is used in Section 4 without a prior definition in the main text, forcing the reader to guess or search the appendix. A systematic pass to define all acronyms and replace code-like macros with natural language is required.
