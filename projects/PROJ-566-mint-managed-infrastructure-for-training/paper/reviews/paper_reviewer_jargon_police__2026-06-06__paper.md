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
- id: ad2bb682b189
  severity: writing
  text: Define "IcePop" upon first use in Section 5.1, as it introduces new specialized
    terminology not covered in prior action items.
artifact_hash: b4bbb587409bb8ce9fbc13953a4d6d307cbe54e41c3196b0506aac091594e206
artifact_path: projects/PROJ-566-mint-managed-infrastructure-for-training/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-06T13:06:47.377447Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_jargon_police
score: 0.0
verdict: minor_revision
---

The revision does not adequately address the prior jargon concerns. While terms like "adapter revision" and "policy record" are defined in Section 2, they remain absent from the Introduction or Abstract glossary as requested (ID 63ca1a87cda3, 951bb53234eb). Acronyms such as TP, EP, SFT, DPO, and GRPO are still introduced in Section 5 without prior definition in the Introduction (ID 966b2a7f9599). System-specific phrases like "tensor-parallel serving actor" persist in Figure captions (e001) without plain-language alternatives or glossary entries (ID 6f883b795751).

Specifically, in Section 5.1, "tensor-parallel (TP)" and "expert-parallel (EP)" are defined late, after appearing in the title and earlier sections. "SFT, DPO, GRPO" appear in Table 3 (Section 5) without introductory context. The Introduction uses "LoRA" and "RL" without expanding them, assuming reader familiarity. Section 3 defines "service plane" and "compute plane", but this is too late for non-specialist onboarding. Additionally, the term "IcePop" appears in Section 5.1 without definition, introducing new specialized jargon. To meet accessibility standards, all acronyms and system-specific terms must be defined at first use in the Introduction or an Abstract glossary. These omissions exclude readers unfamiliar with distributed training infrastructure.
