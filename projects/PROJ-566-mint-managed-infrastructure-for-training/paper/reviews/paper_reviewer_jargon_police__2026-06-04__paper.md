---
action_items:
- id: 966b2a7f9599
  severity: writing
  text: Define all acronyms at first use (e.g., TP, SLO, HBM, FP8, KV, R3, DSA, MTP)
    in the Introduction or System Design sections rather than assuming reader familiarity.
- id: 63ca1a87cda3
  severity: writing
  text: Move definitions of SFT, DPO, GRPO, PEFT, and MoE to the Introduction or Abstract
    glossary, as they appear in the Abstract and Section 3 before Section 5.1.
- id: 951bb53234eb
  severity: writing
  text: Clarify system-specific terms like "adapter revision," "policy record," "service
    plane," and "compute plane" with brief parenthetical explanations for non-specialist
    readers.
- id: 6f883b795751
  severity: writing
  text: Replace jargon-heavy phrases like "tensor-parallel serving actor" and "expert-parallel
    LoRA" with plain language or add a glossary entry for parallelism types.
artifact_hash: b4bbb587409bb8ce9fbc13953a4d6d307cbe54e41c3196b0506aac091594e206
artifact_path: projects/PROJ-566-mint-managed-infrastructure-for-training/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-04T01:22:07.487159Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_jargon_police
score: 0.0
verdict: minor_revision
---

The manuscript introduces significant domain-specific terminology that hinders accessibility for non-specialist readers. While many terms are eventually defined, they appear in the Abstract, Introduction, and System Design sections without explanation, creating a barrier to entry.

In the Abstract and Introduction, acronyms like "LoRA," "MoE," "RL," and "PEFT" are used without definition. "LoRA" is defined in Related Work (Section 4), but not in the Introduction where it is first mentioned. "PEFT" appears in Section 3 ("PEFT trainers") without definition. "RL" is used frequently but "RLHF" appears in Related Work citations without clear context in the main text.

Section 3 (System Design) introduces system-specific architecture terms: "service plane," "compute plane," "cold load," "warm path," "TP," and "vLLM." "TP" is used as "4-GPU tensor-parallel" but the acronym "TP" itself is not defined. "vLLM" and "Megatron" are referenced as system names but not described for readers unfamiliar with the ecosystem.

Section 5 (Evaluation) relies heavily on acronyms defined only in Section 5.1 ("SFT denotes...", "DPO denotes...", "GRPO denotes..."). However, "AIME24," "LawBench," "FinGPT," "FinEval," "R3," "DSA," "MTP," "SLO," "HBM," "FP8," and "KV cache" appear in tables and text without definition. "SLO" (Service Level Objective) and "HBM" (High Bandwidth Memory) are standard infrastructure terms but should be defined for a general audience. "R3" is referenced as "R3 studies MoE router disagreement" but the acronym is not expanded in the text body (only in citations).

To improve accessibility, I recommend adding a glossary or defining these terms at their first occurrence in the Abstract or Introduction. Specifically, define "TP," "SLO," "HBM," "FP8," "KV," "R3," "DSA," and "MTP" in Section 3 or earlier. Move definitions of SFT, DPO, and GRPO to Section 1. Explain "service plane" and "compute plane" with plain language equivalents (e.g., "management layer" and "execution layer"). This will ensure the paper is readable by researchers outside the specific infrastructure sub-field.
